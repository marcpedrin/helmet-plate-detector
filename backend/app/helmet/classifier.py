"""YOLO head-detector based helmet classifier.

Owner: Prajwal. Signatures are final; bodies are pending.
Do NOT import ultralytics/torch at module top level; import inside ``__init__``.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np

from app.core.types import HelmetResult, ModelState, Rider


class YoloHelmetClassifier:
    """Runs a YOLO helmet/head detector on each rider's upper-body crop.

    Contract (implements ``HelmetClassifierProtocol``):
      * Crop region per rider: union of person boxes (fallback: rider bbox), expanded
        with ``geometry.expand`` and clipped to the frame.
      * Batch all crops in one ``model.predict`` call at ``imgsz``; drop boxes below ``conf``.
      * Map each head box back to frame coordinates (``HeadDetection.bbox``).
      * Rider status: NO_HELMET if any head is NO_HELMET, else HELMET if any head is
        HELMET, else UNKNOWN. ``confidence`` = confidence of the deciding head (0.0 if UNKNOWN).
      * Never raise on empty/degenerate crops: return ``HelmetResult(UNKNOWN, 0.0)``.

    Thread-safety: may be shared by all pipeline threads; serialise ``predict`` with a lock.
    """

    state: ModelState

    def __init__(self, weights: Path, imgsz: int = 320, conf: float = 0.35, device: str = "auto") -> None:
        """Load the model (import ultralytics here, not at module level).

        Args:
            weights: Path to the ``.pt`` weights (``HELMET_WEIGHTS``).
            imgsz: Inference size (``HELMET_IMGSZ``).
            conf: Minimum box confidence (``HELMET_CONF``).
            device: ``auto`` | ``cpu`` | ``cuda`` | ``cuda:N``.

        Raises:
            NotImplementedError: Until Prajwal implements it.
            Exception: Any load error (the factory converts it to state=ERROR).
        """
        raise NotImplementedError("Prajwal: implement YoloHelmetClassifier")

    def classify_batch(self, frame: np.ndarray, riders: Sequence[Rider]) -> list[HelmetResult]:
        """Return one ``HelmetResult`` per rider, same order as ``riders``."""
        raise NotImplementedError
