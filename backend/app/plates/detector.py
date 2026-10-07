"""Plate detector (open-image-models ``yolo-v9-t-384-license-plate-end2end``).

Owner: Malik. Signatures are final; bodies are pending.
Import ``open_image_models`` inside ``__init__``, never at module top level.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from app.core.types import BBox, ModelState, PlateDetection


class PlateDetector:
    """Detects number plates inside a region (the rider's motorcycle box) of a frame.

    Thread-safety: may be shared by all pipeline threads; serialise inference with a lock.
    """

    state: ModelState

    def __init__(
        self, model_name: str, conf: float = 0.40, min_width_px: int = 50, device: str = "auto"
    ) -> None:
        """Load the detector.

        Args:
            model_name: open-image-models model id (``PLATE_DETECTOR_MODEL``).
            conf: Minimum confidence (``PLATE_DETECTOR_CONF``).
            min_width_px: Discard plates narrower than this (``PLATE_MIN_WIDTH_PX``).
            device: ``auto`` | ``cpu`` | ``cuda``.

        Raises:
            NotImplementedError: Until Malik implements it.
        """
        raise NotImplementedError("Malik: implement PlateDetector")

    def detect(self, image: np.ndarray, region: BBox, exclude: Sequence[BBox] = ()) -> list[PlateDetection]:
        """Return plates inside ``region`` (frame coordinates), best first.

        Args:
            image: Full BGR frame.
            region: Search region in frame coordinates (expanded motorcycle box).
            exclude: Boxes to ignore (plates already assigned to other riders; IoU > 0.5).

        Returns:
            Detections in frame coordinates, sorted by confidence descending. Never raises.
        """
        raise NotImplementedError
