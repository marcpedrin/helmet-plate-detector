"""Overlay drawing for MJPEG streams (rider boxes coloured by helmet status).

Owner: Marc. Implemented (tiny, shared by MockRunner and PipelineRunner).
"""

from __future__ import annotations

import threading
from collections.abc import Sequence

import cv2
import numpy as np

from app.core.schemas import TrackOverlay
from app.core.types import HelmetStatus

COLORS = {
    HelmetStatus.HELMET: (60, 200, 60),
    HelmetStatus.NO_HELMET: (40, 40, 230),
    HelmetStatus.UNKNOWN: (200, 200, 200),
}
"""BGR colour per helmet status."""


def draw_tracks(image: np.ndarray, tracks: Sequence[TrackOverlay]) -> np.ndarray:
    """Draw ``tracks`` onto ``image`` in place and return it.

    Args:
        image: Writable BGR image.
        tracks: Boxes to draw, in frame coordinates.

    Returns:
        The same ``image``.
    """
    for t in tracks:
        x1, y1, x2, y2 = (int(v) for v in t.bbox)
        color = COLORS.get(t.helmet, COLORS[HelmetStatus.UNKNOWN])
        cv2.rectangle(image, (x1, y1), (x2, y2), color, 3)
        label = f"#{t.track_id} {t.helmet.value}"
        cv2.putText(image, label, (x1, max(20, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2, cv2.LINE_AA)
    return image


class OverlayState:
    """Latest overlay tracks per camera; callable as an ``OverlayFn``.

    Thread-safety: ``set`` is called from pipeline threads, ``__call__`` from the MJPEG
    encoder threads; both take a lock.
    """

    def __init__(self) -> None:
        """Create an empty overlay state."""
        self._lock = threading.Lock()
        self._tracks: dict[str, list[TrackOverlay]] = {}

    def set(self, camera_id: str, tracks: Sequence[TrackOverlay]) -> None:
        """Replace the tracks drawn for ``camera_id``."""
        with self._lock:
            self._tracks[camera_id] = list(tracks)

    def get(self, camera_id: str) -> list[TrackOverlay]:
        """Return a copy of the tracks for ``camera_id``."""
        with self._lock:
            return list(self._tracks.get(camera_id, []))

    def __call__(self, camera_id: str, image: np.ndarray) -> np.ndarray:
        """Draw the current tracks of ``camera_id`` onto ``image`` (an ``OverlayFn``)."""
        return draw_tracks(image, self.get(camera_id))
