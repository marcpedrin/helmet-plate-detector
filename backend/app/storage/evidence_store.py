"""Writes evidence JPEGs to ``EVIDENCE_DIR`` and maps them to ``/evidence/...`` URLs.

Owner: Marc (camera/storage stream). ``save`` and ``delete`` work minimally; the storage
stream adds atomic writes and the retention purge.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import cv2
import numpy as np

EvidenceKind = str
"""One of ``"full_frame"``, ``"rider_crop"``, ``"plate_crop"``."""


class EvidenceStore:
    """Stores evidence images at ``<root>/<camera_id>/<violation_id>/<kind>.jpg``.

    Thread-safety: safe for concurrent calls on *different* violations.
    """

    def __init__(self, root: Path, url_prefix: str = "/evidence", jpeg_quality: int = 90) -> None:
        """Create the store; ``root`` is created on first save.

        Args:
            root: Absolute evidence directory (``EVIDENCE_DIR``), mounted at ``url_prefix``.
            url_prefix: URL path where FastAPI serves ``root``.
            jpeg_quality: JPEG quality for saved evidence.
        """
        self.root = Path(root)
        self.url_prefix = url_prefix.rstrip("/")
        self.jpeg_quality = jpeg_quality

    def path_for(self, camera_id: str, violation_id: str, kind: EvidenceKind) -> Path:
        """Return the absolute file path for one evidence image (does not create it)."""
        return self.root / camera_id / violation_id / f"{kind}.jpg"

    def url_for(self, camera_id: str, violation_id: str, kind: EvidenceKind) -> str:
        """Return the public URL for one evidence image."""
        return f"{self.url_prefix}/{camera_id}/{violation_id}/{kind}.jpg"

    def save(self, camera_id: str, violation_id: str, kind: EvidenceKind, image: np.ndarray) -> str:
        """Encode ``image`` as JPEG, write it, and return its public URL.

        Raises:
            OSError: If the file cannot be written.
            ValueError: If the image cannot be encoded (e.g. empty crop).
        """
        path = self.path_for(camera_id, violation_id, kind)
        path.parent.mkdir(parents=True, exist_ok=True)
        ok, buf = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality])
        if not ok:
            raise ValueError(f"cannot encode evidence image {kind} for {violation_id}")
        path.write_bytes(buf.tobytes())
        return self.url_for(camera_id, violation_id, kind)

    def delete(self, camera_id: str, violation_id: str) -> None:
        """Delete all evidence of one violation (missing files are ignored)."""
        shutil.rmtree(self.root / camera_id / violation_id, ignore_errors=True)
