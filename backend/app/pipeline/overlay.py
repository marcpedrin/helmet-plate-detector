"""Overlay drawn on MJPEG frames: rider boxes coloured by helmet status + a top-left HUD.

Owner: Marc. ``OverlayState.draw`` is registered with ``camera_manager.set_overlay`` in ``container.py``;
the camera module calls it on the full-resolution frame copy before resizing for the stream.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Sequence
from dataclasses import dataclass

import cv2
import numpy as np

from app.core.schemas import TrackOverlay
from app.core.types import BBox, HelmetStatus

log = logging.getLogger(__name__)

GREEN = (60, 200, 60)
RED = (40, 40, 230)
AMBER = (0, 191, 255)
COLORS = {HelmetStatus.HELMET: GREEN, HelmetStatus.NO_HELMET: RED, HelmetStatus.UNKNOWN: AMBER}
"""BGR colour per helmet status (violations are always red)."""


@dataclass(frozen=True)
class OverlayRider:
    """One rider as shown on the stream."""

    track_id: int
    bbox: BBox
    helmet: HelmetStatus
    confidence: float = 0.0
    violation: bool = False
    plate: str | None = None


@dataclass
class _CameraOverlay:
    riders: tuple[OverlayRider, ...] = ()
    fps: float = 0.0


class OverlayState:
    """Latest overlay data per camera.

    Thread-safety: ``update`` is called from pipeline threads, ``draw`` from MJPEG encoder threads; both take
    a lock and ``draw`` works on a snapshot.
    """

    def __init__(self, camera_names: dict[str, str] | None = None) -> None:
        """Create an empty state; ``camera_names`` maps camera id -> display name for the HUD."""
        self._lock = threading.Lock()
        self._cams: dict[str, _CameraOverlay] = {}
        self._names = dict(camera_names or {})

    def update(self, camera_id: str, riders: Sequence[OverlayRider], fps: float = 0.0) -> None:
        """Replace what is drawn for ``camera_id``."""
        with self._lock:
            self._cams[camera_id] = _CameraOverlay(tuple(riders), fps)

    def riders(self, camera_id: str) -> list[OverlayRider]:
        """Return a copy of the riders currently drawn for ``camera_id``."""
        with self._lock:
            cam = self._cams.get(camera_id)
            return list(cam.riders) if cam else []

    def track_overlays(self, camera_id: str) -> list[TrackOverlay]:
        """Return the riders as wire ``TrackOverlay`` objects (for ``camera_metrics``)."""
        return [
            TrackOverlay(track_id=r.track_id, bbox=list(r.bbox), helmet=r.helmet)
            for r in self.riders(camera_id)
        ]

    def draw(self, camera_id: str, image: np.ndarray) -> np.ndarray:
        """Draw boxes, labels and the HUD onto ``image`` (an ``OverlayFn``).

        Never raises: on any error the input image is returned unchanged.

        Args:
            camera_id: Camera whose overlay to draw.
            image: Writable BGR image in original-frame coordinates.

        Returns:
            The annotated image.
        """
        try:
            with self._lock:
                cam = self._cams.get(camera_id) or _CameraOverlay()
                name = self._names.get(camera_id, camera_id)
            if image.ndim != 3 or image.shape[0] < 8 or image.shape[1] < 8:
                return image
            # WHY: scale strokes/text with resolution so 1080p and 480p streams look the same after resizing.
            scale = max(0.5, image.shape[0] / 720)
            thick = max(1, int(round(2 * scale)))
            for r in cam.riders:
                color = RED if r.violation else COLORS.get(r.helmet, AMBER)
                x1, y1, x2, y2 = (int(v) for v in r.bbox)
                cv2.rectangle(image, (x1, y1), (x2, y2), color, thick + (1 if r.violation else 0))
                label = f"#{r.track_id} {r.helmet.value} {r.confidence:.2f}"
                if r.plate:
                    label += f" {r.plate}"
                _label(image, label, x1, y1, color, 0.6 * scale, thick)
            hud = f"{name}  {time.strftime('%H:%M:%S')}  {cam.fps:.1f} fps  riders {len(cam.riders)}"
            _label(
                image, hud, 8, int(30 * scale), (30, 30, 30), 0.7 * scale, thick, text_color=(255, 255, 255)
            )
        except Exception:
            log.exception("overlay draw failed for %s", camera_id)
        return image


def _label(
    image: np.ndarray,
    text: str,
    x: int,
    y: int,
    bg: tuple[int, int, int],
    font_scale: float,
    thick: int,
    text_color: tuple[int, int, int] = (0, 0, 0),
) -> None:
    (tw, th), base = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thick)
    y = max(th + base + 2, y)
    cv2.rectangle(image, (x, y - th - base - 4), (x + tw + 6, y), bg, -1)
    cv2.putText(
        image,
        text,
        (x + 3, y - base - 1),
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        text_color,
        thick,
        cv2.LINE_AA,
    )
