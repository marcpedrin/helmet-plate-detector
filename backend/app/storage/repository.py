"""Violation repositories: the SQLite one (pending) and a working in-memory one.

Owner: Marc (camera/storage stream). Both implement ``ViolationRepositoryProtocol``;
``tests/storage`` runs the same contract tests against every implementation.
"""

from __future__ import annotations

import threading
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from app.core.schemas import EvidenceUrls, RepositoryCounts, ViolationOut, ViolationPage
from app.core.types import PlateResult, PlateStatus, ViolationEvent
from app.storage.evidence_store import EvidenceStore


def to_violation_out(event: ViolationEvent, evidence: EvidenceUrls) -> ViolationOut:
    """Convert a pipeline ``ViolationEvent`` plus saved evidence URLs into the wire schema."""
    plate = event.plate
    return ViolationOut(
        id=event.violation_id,
        camera_id=event.camera_id,
        track_id=event.track_id,
        violation=event.violation_type,
        plate=plate.text,
        plate_status=plate.status,
        plate_confidence=None if plate.status == PlateStatus.PENDING else plate.confidence,
        helmet_confidence=event.helmet_confidence,
        timestamp=datetime.fromtimestamp(event.timestamp, tz=UTC),
        frame_index=event.frame_index,
        rider_bbox=list(event.rider_bbox),
        evidence=evidence,
    )


class SqliteViolationRepository:
    """SQLite-backed ``ViolationRepositoryProtocol`` (camera/storage stream implements it).

    Thread-safety: one connection (``check_same_thread=False``) guarded by a lock.
    """

    def __init__(self, db_path: Path, evidence: EvidenceStore) -> None:
        """Open/create the database at ``db_path`` and run migrations.

        Raises:
            sqlite3.Error: If the database cannot be opened (the factory then falls back).
        """
        raise NotImplementedError("camera/storage stream: implement SqliteViolationRepository")

    def create(self, event: ViolationEvent) -> ViolationOut:
        """See ``ViolationRepositoryProtocol.create``."""
        raise NotImplementedError

    def update_plate(
        self, violation_id: str, plate: PlateResult, plate_crop: np.ndarray | None
    ) -> ViolationOut:
        """See ``ViolationRepositoryProtocol.update_plate``."""
        raise NotImplementedError

    def get(self, violation_id: str) -> ViolationOut | None:
        """See ``ViolationRepositoryProtocol.get``."""
        raise NotImplementedError

    def list(self, camera_id: str | None = None, limit: int = 50, offset: int = 0) -> ViolationPage:
        """See ``ViolationRepositoryProtocol.list``."""
        raise NotImplementedError

    def counts(self) -> RepositoryCounts:
        """See ``ViolationRepositoryProtocol.counts``."""
        raise NotImplementedError

    def purge_older_than(self, days: int) -> int:
        """See ``ViolationRepositoryProtocol.purge_older_than``."""
        raise NotImplementedError


class InMemoryRepository:
    """Working in-memory ``ViolationRepositoryProtocol``; evidence JPEGs still go to disk.

    Used in mock mode until the SQLite repository lands, and as its fallback.
    Thread-safety: all methods take an internal lock.
    """

    def __init__(self, evidence: EvidenceStore) -> None:
        """Create an empty repository writing evidence through ``evidence``."""
        self._evidence = evidence
        self._lock = threading.Lock()
        self._items: dict[str, ViolationOut] = {}
        self._created_at: dict[str, float] = {}

    def create(self, event: ViolationEvent) -> ViolationOut:
        """Save evidence images and store the violation; return the stored record."""
        ev = event.evidence
        save = self._evidence.save
        urls = EvidenceUrls(
            full_frame_url=save(event.camera_id, event.violation_id, "full_frame", ev.full_frame),
            rider_crop_url=save(event.camera_id, event.violation_id, "rider_crop", ev.rider_crop),
            plate_crop_url=(
                save(event.camera_id, event.violation_id, "plate_crop", ev.plate_crop)
                if ev.plate_crop is not None and ev.plate_crop.size
                else None
            ),
        )
        out = to_violation_out(event, urls)
        with self._lock:
            self._items[out.id] = out
            self._created_at[out.id] = event.timestamp
        return out

    def update_plate(
        self, violation_id: str, plate: PlateResult, plate_crop: np.ndarray | None
    ) -> ViolationOut:
        """Set the plate result; raises KeyError if ``violation_id`` is unknown."""
        with self._lock:
            current = self._items[violation_id]
        evidence = current.evidence
        if plate_crop is not None and plate_crop.size:
            url = self._evidence.save(current.camera_id, violation_id, "plate_crop", plate_crop)
            evidence = evidence.model_copy(update={"plate_crop_url": url})
        updated = current.model_copy(
            update={
                "plate": plate.text,
                "plate_status": plate.status,
                "plate_confidence": None if plate.status == PlateStatus.PENDING else plate.confidence,
                "evidence": evidence,
            }
        )
        with self._lock:
            self._items[violation_id] = updated
        return updated

    def get(self, violation_id: str) -> ViolationOut | None:
        """Return one violation or None."""
        with self._lock:
            return self._items.get(violation_id)

    def list(self, camera_id: str | None = None, limit: int = 50, offset: int = 0) -> ViolationPage:
        """Return violations newest-first, optionally filtered by camera."""
        with self._lock:
            items = [v for v in self._items.values() if camera_id is None or v.camera_id == camera_id]
        items.sort(key=lambda v: v.timestamp, reverse=True)
        return ViolationPage(
            items=items[offset : offset + limit], total=len(items), limit=limit, offset=offset
        )

    def counts(self) -> RepositoryCounts:
        """Return totals by camera and plate outcome."""
        with self._lock:
            items = list(self._items.values())
        by_camera: dict[str, int] = {}
        for v in items:
            by_camera[v.camera_id] = by_camera.get(v.camera_id, 0) + 1
        return RepositoryCounts(
            total=len(items),
            by_camera=by_camera,
            plates_read=sum(v.plate_status == PlateStatus.READ for v in items),
            plates_unreadable=sum(v.plate_status == PlateStatus.UNREADABLE for v in items),
        )

    def purge_older_than(self, days: int) -> int:
        """Drop violations (and their evidence) older than ``days``; return the count."""
        cutoff = time.time() - days * 86400
        with self._lock:
            old = [vid for vid, ts in self._created_at.items() if ts < cutoff]
            removed = [self._items.pop(vid) for vid in old]
            for vid in old:
                del self._created_at[vid]
        for v in removed:
            self._evidence.delete(v.camera_id, v.id)
        return len(removed)
