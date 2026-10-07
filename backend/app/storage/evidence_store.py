"""Atomic JPEG evidence storage below date-partitioned directories."""

from __future__ import annotations

import os
import re
import shutil
import time
from datetime import UTC, datetime
from pathlib import Path

import cv2
import numpy as np

_SAFE_ID = re.compile(r"^[0-9a-fA-F]+$")


class EvidenceStore:
    """Store images at ``YYYY-MM-DD/<hex-id>/{full,rider,plate}.jpg``."""

    def __init__(self, root: Path, url_prefix: str = "/evidence", jpeg_quality: int = 90) -> None:
        """Create the store.

        Args:
            root: Directory mounted by FastAPI under ``url_prefix``.
            url_prefix: Browser URL prefix for evidence.
            jpeg_quality: JPEG encoder quality.
        """
        self.root, self.url_prefix, self.jpeg_quality = Path(root), url_prefix.rstrip("/"), jpeg_quality

    def _relative_dir(self, violation_id: str, timestamp: float) -> Path:
        if not _SAFE_ID.fullmatch(violation_id):
            raise ValueError("violation_id must be hexadecimal")
        return Path(datetime.fromtimestamp(timestamp, UTC).strftime("%Y-%m-%d")) / violation_id

    def _write(self, relative: Path, image: np.ndarray) -> str:
        if image.size == 0:
            raise ValueError("cannot write empty evidence image")
        ok, encoded = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality])
        if not ok:
            raise ValueError("cannot JPEG encode evidence image")
        destination = self.root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_bytes(encoded.tobytes())
        os.replace(temporary, destination)
        return relative.as_posix()

    def save_bundle(self, violation_id: str, timestamp: float, bundle: object) -> dict[str, str]:
        """Write full/rider/optional plate images and return relative paths."""
        directory = self._relative_dir(violation_id, timestamp)
        full = self._write(directory / "full.jpg", bundle.full_frame)  # type: ignore[attr-defined]
        rider = self._write(directory / "rider.jpg", bundle.rider_crop)  # type: ignore[attr-defined]
        paths = {"full": full, "rider": rider}
        crop = bundle.plate_crop  # type: ignore[attr-defined]
        if crop is not None and crop.size:
            paths["plate"] = self._write(directory / "plate.jpg", crop)
        return paths

    def save_plate(self, violation_id: str, timestamp: float, crop: np.ndarray | None) -> str | None:
        """Write an optional plate crop and return its relative path."""
        if crop is None or not crop.size:
            return None
        return self._write(self._relative_dir(violation_id, timestamp) / "plate.jpg", crop)

    def url_for(self, relative: str) -> str:
        """Map a relative storage path to a browser URL using forward slashes."""
        return f"{self.url_prefix}/{relative.replace('\\', '/')}"

    def delete(self, _camera_id: str, violation_id: str) -> None:
        """Delete every date-partitioned directory matching a violation ID."""
        if not _SAFE_ID.fullmatch(violation_id):
            raise ValueError("violation_id must be hexadecimal")
        for child in self.root.glob(f"*/{violation_id}"):
            shutil.rmtree(child, ignore_errors=True)

    def delete_dirs_older_than(self, days: int) -> int:
        """Remove whole date directories older than ``days`` and return their count."""
        cutoff = time.time() - days * 86400
        deleted = 0
        if not self.root.exists():
            return 0
        for child in self.root.iterdir():
            if child.is_dir() and child.stat().st_mtime < cutoff:
                shutil.rmtree(child, ignore_errors=True)
                deleted += 1
        return deleted
