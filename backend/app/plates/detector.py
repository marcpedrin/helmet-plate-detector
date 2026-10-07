"""Plate detector (open-image-models ``yolo-v9-t-384-license-plate-end2end``, ONNX, MIT).

Import ``open_image_models`` inside ``__init__``, never at module top level.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Sequence

import numpy as np

from app.core.geometry import clip, iou
from app.core.types import BBox, ModelState, PlateDetection

log = logging.getLogger(__name__)


def resolve_providers(device: str) -> list[str]:
    """Pick ONNX Runtime providers: CUDA when requested/available, else CPU."""
    import onnxruntime as ort

    available = ort.get_available_providers()
    want_cuda = device == "auto" or device.startswith("cuda")
    if want_cuda and "CUDAExecutionProvider" in available:
        return ["CUDAExecutionProvider", "CPUExecutionProvider"]
    return ["CPUExecutionProvider"]


class PlateDetector:
    """Detects number plates inside a region (the rider's motorcycle box) of a frame.

    Thread-safety: may be shared by all pipeline threads; inference is serialised with a lock.
    """

    state: ModelState

    def __init__(
        self, model_name: str, conf: float = 0.40, min_width_px: int = 50, device: str = "auto"
    ) -> None:
        """Load the detector.

        Args:
            model_name: open-image-models model id (``PLATE_DETECTOR_MODEL``).
            conf: Minimum confidence (``PLATE_DETECTOR_CONF``).
            min_width_px: Plates narrower than this are still returned (for evidence) but
                the service skips OCR on them.
            device: ``auto`` | ``cpu`` | ``cuda``.

        Raises:
            Exception: If the model cannot be loaded (the factory converts it to state=ERROR).
        """
        from open_image_models import create_detector

        self.conf = conf
        self.min_width_px = min_width_px
        self.providers = resolve_providers(device)
        # WHY: a low raw threshold; ``conf`` is applied after aspect/size filtering.
        self._model = create_detector(model_name, conf_thresh=min(conf, 0.25), providers=self.providers)
        self._lock = threading.Lock()
        self.state = ModelState.LOADED
        log.info("Plate detector %s loaded (providers=%s)", model_name, self.providers)

    def detect(self, image: np.ndarray, region: BBox, exclude: Sequence[BBox] = ()) -> list[PlateDetection]:
        """Return plates inside ``region`` (frame coordinates), best first.

        Args:
            image: Full BGR frame.
            region: Search region in frame coordinates (expanded motorcycle box).
            exclude: Boxes to ignore (plates already assigned to other riders; IoU > 0.5).

        Returns:
            Detections in frame coordinates, sorted by confidence descending. Never raises.
        """
        try:
            h, w = image.shape[:2]
            x1, y1, x2, y2 = clip(region, w, h)
            if x2 - x1 < 16 or y2 - y1 < 16:
                return []
            crop = np.ascontiguousarray(image[y1:y2, x1:x2])
            with self._lock:
                raw = self._model.predict(crop)
            region_area = (x2 - x1) * (y2 - y1)
            out: list[PlateDetection] = []
            for det in raw:
                bb = det.bounding_box
                box = (int(bb.x1) + x1, int(bb.y1) + y1, int(bb.x2) + x1, int(bb.y2) + y1)
                bw, bh = box[2] - box[0], box[3] - box[1]
                if bw <= 0 or bh <= 0 or det.confidence < self.conf:
                    continue
                # WHY: two-line bike plates are ~1.3-2:1, single-line ~4-5:1; reject the rest.
                if not 0.8 <= bw / bh <= 6.5:
                    continue
                if bw * bh > 0.35 * region_area:
                    continue
                if any(iou(box, ex) > 0.5 for ex in exclude):
                    continue
                out.append(PlateDetection(bbox=box, confidence=float(det.confidence)))
            out.sort(key=lambda d: d.confidence, reverse=True)
            return out
        except Exception:
            log.exception("plate detection failed")
            return []
