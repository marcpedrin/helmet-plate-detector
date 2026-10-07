"""Thread-safe in-memory and SQLite violation repositories."""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from app.core.schemas import EvidenceUrls, RepositoryCounts, ViolationOut, ViolationPage
from app.core.types import PlateResult, PlateStatus, ViolationEvent
from app.storage.database import Database
from app.storage.evidence_store import EvidenceStore


def _out(event: ViolationEvent, paths: dict[str, str], store: EvidenceStore) -> ViolationOut:
    return ViolationOut(
        id=event.violation_id,
        camera_id=event.camera_id,
        track_id=event.track_id,
        violation=event.violation_type,
        plate=event.plate.text,
        plate_status=event.plate.status,
        plate_confidence=event.plate.confidence if event.plate.status == PlateStatus.READ else None,
        helmet_confidence=event.helmet_confidence,
        timestamp=datetime.fromtimestamp(event.timestamp, UTC),
        frame_index=event.frame_index,
        rider_bbox=list(event.rider_bbox),
        evidence=EvidenceUrls(
            full_frame_url=store.url_for(paths["full"]),
            rider_crop_url=store.url_for(paths["rider"]),
            plate_crop_url=store.url_for(paths["plate"]) if paths.get("plate") else None,
        ),
    )


class SqliteViolationRepository:
    """SQLite-backed repository with a lock around the shared connection.

    Thread-safety: every database operation uses ``Database.lock``.
    """

    def __init__(self, db_path: Path, evidence: EvidenceStore) -> None:
        """Open ``db_path`` and prepare storage.

        Raises:
            sqlite3.Error: If SQLite cannot initialize.
        """
        self._db, self._evidence = Database(db_path), evidence

    def create(self, event: ViolationEvent) -> ViolationOut:
        """Write evidence then insert a violation row."""
        paths = self._evidence.save_bundle(event.violation_id, event.timestamp, event.evidence)
        with self._db.lock:
            self._db.conn.execute(
                """INSERT INTO violations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    event.violation_id,
                    event.camera_id,
                    event.track_id,
                    event.violation_type,
                    event.helmet_confidence,
                    event.plate.text,
                    event.plate.status.value,
                    event.plate.confidence if event.plate.status == PlateStatus.READ else None,
                    event.plate.votes,
                    event.timestamp,
                    event.frame_index,
                    event.video_pos_ms,
                    json.dumps(event.rider_bbox),
                    paths["full"],
                    paths["rider"],
                    paths.get("plate"),
                    time.time(),
                ),
            )
            self._db.conn.commit()
        return _out(event, paths, self._evidence)

    def _row(self, row: object) -> ViolationOut:
        record = row
        evidence = EvidenceUrls(
            full_frame_url=self._evidence.url_for(record["full_frame_path"]),
            rider_crop_url=self._evidence.url_for(record["rider_crop_path"]),
            plate_crop_url=self._evidence.url_for(record["plate_crop_path"])
            if record["plate_crop_path"]
            else None,
        )
        return ViolationOut(
            id=record["id"],
            camera_id=record["camera_id"],
            track_id=record["track_id"],
            violation=record["violation"],
            plate=record["plate"],
            plate_status=PlateStatus(record["plate_status"]),
            plate_confidence=record["plate_confidence"],
            helmet_confidence=record["helmet_confidence"],
            timestamp=datetime.fromtimestamp(record["timestamp"], UTC),
            frame_index=record["frame_index"],
            rider_bbox=json.loads(record["rider_bbox"]),
            evidence=evidence,
        )

    def update_plate(
        self, violation_id: str, plate: PlateResult, plate_crop: np.ndarray | None
    ) -> ViolationOut:
        """Persist a plate result and optional JPEG crop.

        Raises:
            KeyError: If the violation does not exist.
        """
        with self._db.lock:
            row = self._db.conn.execute("SELECT * FROM violations WHERE id=?", (violation_id,)).fetchone()
            if row is None:
                raise KeyError(violation_id)
            path = (
                self._evidence.save_plate(violation_id, row["timestamp"], plate_crop)
                or row["plate_crop_path"]
            )
            self._db.conn.execute(
                "UPDATE violations SET plate=?, plate_status=?, plate_confidence=?, plate_votes=?, "
                "plate_crop_path=? WHERE id=?",
                (
                    plate.text,
                    plate.status.value,
                    plate.confidence if plate.status == PlateStatus.READ else None,
                    plate.votes,
                    path,
                    violation_id,
                ),
            )
            self._db.conn.commit()
            return self._row(
                self._db.conn.execute("SELECT * FROM violations WHERE id=?", (violation_id,)).fetchone()
            )

    def get(self, violation_id: str) -> ViolationOut | None:
        """Return a violation or ``None``."""
        with self._db.lock:
            row = self._db.conn.execute("SELECT * FROM violations WHERE id=?", (violation_id,)).fetchone()
        return self._row(row) if row else None

    def list(self, camera_id: str | None = None, limit: int = 50, offset: int = 0) -> ViolationPage:
        """Return newest-first, bounded to 200 rows per request."""
        limit, offset = max(0, min(limit, 200)), max(0, offset)
        clause, args = ("", ()) if camera_id is None else (" WHERE camera_id=?", (camera_id,))
        with self._db.lock:
            total = self._db.conn.execute("SELECT COUNT(*) FROM violations" + clause, args).fetchone()[0]
            rows = self._db.conn.execute(
                "SELECT * FROM violations" + clause + " ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                (*args, limit, offset),
            ).fetchall()
        return ViolationPage(items=[self._row(row) for row in rows], total=total, limit=limit, offset=offset)

    def counts(self) -> RepositoryCounts:
        """Return totals grouped by camera and plate terminal state."""
        with self._db.lock:
            rows = self._db.conn.execute(
                "SELECT camera_id, plate_status, COUNT(*) n FROM violations GROUP BY camera_id, plate_status"
            ).fetchall()
        cameras: dict[str, int] = {}
        read = unreadable = 0
        for row in rows:
            cameras[row["camera_id"]] = cameras.get(row["camera_id"], 0) + row["n"]
            read += row["n"] if row["plate_status"] == PlateStatus.READ.value else 0
            unreadable += row["n"] if row["plate_status"] == PlateStatus.UNREADABLE.value else 0
        return RepositoryCounts(
            total=sum(cameras.values()), by_camera=cameras, plates_read=read, plates_unreadable=unreadable
        )

    def purge_older_than(self, days: int) -> int:
        """Delete old rows and their evidence directories."""
        cutoff = time.time() - days * 86400
        with self._db.lock:
            rows = self._db.conn.execute(
                "SELECT id,camera_id FROM violations WHERE timestamp < ?", (cutoff,)
            ).fetchall()
            self._db.conn.execute("DELETE FROM violations WHERE timestamp < ?", (cutoff,))
            self._db.conn.commit()
        for row in rows:
            self._evidence.delete(row["camera_id"], row["id"])
        return len(rows)


class InMemoryRepository:
    """Small thread-safe fallback used when SQLite initialization fails."""

    def __init__(self, evidence: EvidenceStore) -> None:
        """Create an empty repository."""
        import threading

        self._evidence, self._items, self._timestamps, self._lock = evidence, {}, {}, threading.Lock()

    def create(self, event: ViolationEvent) -> ViolationOut:
        """Save evidence and retain the output in memory."""
        out = _out(
            event,
            self._evidence.save_bundle(event.violation_id, event.timestamp, event.evidence),
            self._evidence,
        )
        with self._lock:
            self._items[out.id], self._timestamps[out.id] = out, event.timestamp
        return out

    def update_plate(
        self, violation_id: str, plate: PlateResult, plate_crop: np.ndarray | None
    ) -> ViolationOut:
        """Update an item or raise ``KeyError``."""
        with self._lock:
            current = self._items[violation_id]
            path = self._evidence.save_plate(violation_id, self._timestamps[violation_id], plate_crop)
            evidence = current.evidence.model_copy(
                update={
                    "plate_crop_url": self._evidence.url_for(path)
                    if path
                    else current.evidence.plate_crop_url
                }
            )
            out = current.model_copy(
                update={
                    "plate": plate.text,
                    "plate_status": plate.status,
                    "plate_confidence": plate.confidence if plate.status == PlateStatus.READ else None,
                    "evidence": evidence,
                }
            )
            self._items[violation_id] = out
            return out

    def get(self, violation_id: str) -> ViolationOut | None:
        """Return one violation if present."""
        with self._lock:
            return self._items.get(violation_id)

    def list(self, camera_id: str | None = None, limit: int = 50, offset: int = 0) -> ViolationPage:
        """Return a newest-first page."""
        with self._lock:
            items = [
                item for item in self._items.values() if camera_id is None or item.camera_id == camera_id
            ]
        items.sort(key=lambda item: item.timestamp, reverse=True)
        return ViolationPage(
            items=items[offset : offset + min(limit, 200)],
            total=len(items),
            limit=min(limit, 200),
            offset=offset,
        )

    def counts(self) -> RepositoryCounts:
        """Return aggregate in-memory counts."""
        items = self.list(limit=200).items
        cameras = {
            camera: sum(item.camera_id == camera for item in items)
            for camera in {item.camera_id for item in items}
        }
        return RepositoryCounts(
            total=len(items),
            by_camera=cameras,
            plates_read=sum(item.plate_status == PlateStatus.READ for item in items),
            plates_unreadable=sum(item.plate_status == PlateStatus.UNREADABLE for item in items),
        )

    def purge_older_than(self, days: int) -> int:
        """Remove old in-memory entries and evidence."""
        cutoff = time.time() - days * 86400
        with self._lock:
            old = [key for key, timestamp in self._timestamps.items() if timestamp < cutoff]
        for key in old:
            item = self.get(key)
            with self._lock:
                self._items.pop(key, None)
                self._timestamps.pop(key, None)
            if item:
                self._evidence.delete(item.camera_id, key)
        return len(old)
