"""YOLO26n person+motorcycle detector with ByteTrack tracking.

Owner: Marc. Placeholder: ``update`` returns no tracks until implemented.
Import ultralytics inside ``__init__`` / a loader, never at module top level.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

from app.core.types import ModelState, Track

if TYPE_CHECKING:
    from app.config import Settings

log = logging.getLogger(__name__)


class ObjectTracker:
    """Detects persons and motorcycles and tracks them with ByteTrack, one per camera.

    Contract: ``model.track(frame, persist=True, classes=[person, motorcycle],
    imgsz=DETECTOR_IMGSZ, conf=DETECTOR_CONF, tracker="bytetrack.yaml")``; each camera
    owns its own instance so tracker state never mixes across cameras.

    Thread-safety: used by exactly one pipeline thread.
    """

    state: ModelState

    def __init__(self, settings: Settings, camera_id: str) -> None:
        """Create the tracker; never raises (sets ``state`` instead).

        Args:
            settings: Uses ``detector_weights``, ``detector_imgsz``, ``detector_conf``, ``device``.
            camera_id: Camera this tracker belongs to (for logs).
        """
        self.settings = settings
        self.camera_id = camera_id
        self.state = ModelState.NOT_LOADED  # TODO(Marc): load YOLO26n here

    def update(self, frame: np.ndarray) -> list[Track]:
        """Run detection + tracking on one frame.

        Args:
            frame: BGR frame (read-only).

        Returns:
            Tracks with stable ``track_id`` across frames. Placeholder: always ``[]``.
        """
        return []
