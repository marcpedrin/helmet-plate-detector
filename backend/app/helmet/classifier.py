"""YOLO head-detector based helmet classifier.

Owner: Prajwal. Signatures are final; bodies are pending.
Do NOT import ultralytics/torch at module top level; import inside ``__init__``.
"""

from __future__ import annotations

import logging
import re
import threading
from collections.abc import Sequence
from pathlib import Path

import numpy as np

from app.core.types import BBox, HeadDetection, HelmetResult, HelmetStatus, ModelState, Rider

log = logging.getLogger(__name__)


def _norm_label(value: str) -> str:
    """Normalise model class labels for matching against the helmet vocabulary."""
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def head_region(rider_bbox: BBox, frame_w: int, frame_h: int) -> BBox:
    """Return the crop region used for head detection around a rider's upper body."""
    if frame_w <= 0 or frame_h <= 0:
        return (0, 0, 0, 0)

    x1, y1, x2, y2 = rider_bbox
    if x2 < x1:
        x1, x2 = x2, x1
    if y2 < y1:
        y1, y2 = y2, y1

    width = max(0, x2 - x1)
    height = max(0, y2 - y1)
    pad_x = int(round(width * 0.10))
    y_start = max(0, y1 - int(round(height * 0.10)))
    y_end = min(frame_h, y1 + int(round(height * 0.60)))
    x_start = max(0, x1 - pad_x)
    x_end = min(frame_w, x2 + pad_x)
    return (int(x_start), int(y_start), int(x_end), int(y_end))


def decide(heads: Sequence[HeadDetection], threshold: float) -> HelmetResult:
    """Aggregate kept head detections into a rider verdict."""
    if not heads:
        return HelmetResult(HelmetStatus.UNKNOWN, 0.0, tuple())

    no_helmet_conf = max((h.confidence for h in heads if h.status == HelmetStatus.NO_HELMET), default=0.0)
    helmet_conf = max((h.confidence for h in heads if h.status == HelmetStatus.HELMET), default=0.0)

    if no_helmet_conf >= threshold:
        return HelmetResult(HelmetStatus.NO_HELMET, float(no_helmet_conf), tuple(heads))
    if helmet_conf >= threshold:
        return HelmetResult(HelmetStatus.HELMET, float(helmet_conf), tuple(heads))
    return HelmetResult(HelmetStatus.UNKNOWN, 0.0, tuple(heads))


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
        """Load the model (import ultralytics here, not at module level)."""
        self.weights = Path(weights)
        self.imgsz = int(imgsz)
        self.conf = float(conf)
        self.state = ModelState.ERROR
        self._lock = threading.Lock()

        try:
            import torch
            from ultralytics import YOLO
        except Exception:
            log.exception("Failed to import ultralytics dependencies for helmet classifier")
            raise

        if str(device).lower() == "auto":
            resolved_device = "cuda:0" if torch.cuda.is_available() else "cpu"
        else:
            resolved_device = str(device).lower()
            if resolved_device == "cuda":
                resolved_device = "cuda:0"
        self.device = resolved_device
        self._half = bool("cuda" in self.device and torch.cuda.is_available())

        self.model = YOLO(str(self.weights))
        self.model.to(self.device)
        self._class_map: dict[str, HelmetStatus] = {}
        names = getattr(self.model, "names", None) or {}
        for class_id, label in names.items():
            key = _norm_label(label)
            if key in {"withhelmet", "helmet"}:
                self._class_map[str(class_id)] = HelmetStatus.HELMET
            elif key in {"withouthelmet", "nohelmet", "withouthelmet", "nohelmet"}:
                self._class_map[str(class_id)] = HelmetStatus.NO_HELMET

        if not self._class_map:
            raise ValueError(f"No valid helmet classes found in model labels: {list(names.values())!r}")

        log.info("Helmet model class map: %s", {k: v.value for k, v in self._class_map.items()})

        warmup = np.zeros((64, 64, 3), dtype=np.uint8)
        with self._lock:
            self.model.predict(
                warmup,
                imgsz=self.imgsz,
                conf=0.20,
                agnostic_nms=True,
                verbose=False,
                device=self.device,
                half=self._half,
            )
        self.state = ModelState.LOADED

    def _head_detections_for_rider(
        self, frame: np.ndarray, rider: Rider, crop_bbox: BBox
    ) -> tuple[HeadDetection, ...]:
        x1, y1, x2, y2 = crop_bbox
        if x2 <= x1 or y2 <= y1:
            return ()

        frame_h, frame_w = frame.shape[:2]
        crop_x1 = max(0, x1)
        crop_y1 = max(0, y1)
        crop_x2 = min(frame_w, x2)
        crop_y2 = min(frame_h, y2)
        if crop_x2 <= crop_x1 or crop_y2 <= crop_y1:
            return ()

        crop = frame[crop_y1:crop_y2, crop_x1:crop_x2]
        if crop.size == 0 or crop.shape[0] < 32 or crop.shape[1] < 32:
            return ()

        try:
            with self._lock:
                predictions = self.model.predict(
                    crop,
                    imgsz=self.imgsz,
                    conf=0.20,
                    agnostic_nms=True,
                    verbose=False,
                    device=self.device,
                    half=self._half,
                )
        except Exception:
            log.exception("Helmet inference failed for rider %s", rider.rider_id)
            return ()

        if not predictions:
            return ()
        result = predictions[0]
        boxes = getattr(result, "boxes", None)
        if boxes is None or len(boxes) == 0:
            return ()

        crop_area = max(1, (crop.shape[1] * crop.shape[0]))
        rider_x1, rider_y1, rider_x2, rider_y2 = rider.bbox
        upper_y_limit = rider_y1 + 0.65 * (rider_y2 - rider_y1)

        detections: list[HeadDetection] = []
        xyxy = boxes.xyxy.cpu().numpy()
        confs = boxes.conf.cpu().numpy()
        cls_ids = boxes.cls.cpu().numpy()
        for idx, box in enumerate(xyxy):
            class_id = str(int(cls_ids[idx]))
            status = self._class_map.get(class_id)
            if status is None:
                continue

            conf = float(confs[idx])
            bx1, by1, bx2, by2 = [float(v) for v in box]
            if bx2 <= bx1 or by2 <= by1:
                continue

            full_x1 = crop_x1 + bx1
            full_y1 = crop_y1 + by1
            full_x2 = crop_x1 + bx2
            full_y2 = crop_y1 + by2
            cx = 0.5 * (full_x1 + full_x2)
            cy = 0.5 * (full_y1 + full_y2)
            if not (rider_x1 <= cx <= rider_x2 and rider_y1 <= cy <= upper_y_limit):
                continue

            head_area = (bx2 - bx1) * (by2 - by1)
            if head_area > 0.35 * crop_area:
                continue

            detections.append(
                HeadDetection(
                    bbox=(
                        int(max(0, round(full_x1))),
                        int(max(0, round(full_y1))),
                        int(min(frame.shape[1], round(full_x2))),
                        int(min(frame.shape[0], round(full_y2))),
                    ),
                    status=status,
                    confidence=conf,
                )
            )

        return tuple(detections)

    def classify_batch(self, frame: np.ndarray, riders: Sequence[Rider]) -> list[HelmetResult]:
        """Return one ``HelmetResult`` per rider, same order as ``riders``."""
        if not riders:
            return []

        frame = np.asarray(frame)
        results = [HelmetResult(HelmetStatus.UNKNOWN, 0.0, tuple()) for _ in riders]
        scheduled: list[tuple[int, Rider, BBox, np.ndarray]] = []

        for idx, rider in enumerate(riders):
            try:
                crop_bbox = head_region(rider.bbox, frame.shape[1], frame.shape[0])
            except Exception:
                log.exception("Failed to compute rider crop for rider %s", getattr(rider, "rider_id", None))
                continue

            if crop_bbox[2] <= crop_bbox[0] or crop_bbox[3] <= crop_bbox[1]:
                continue

            x1, y1, x2, y2 = crop_bbox
            crop = frame[max(0, y1):min(frame.shape[0], y2), max(0, x1):min(frame.shape[1], x2)]
            if crop.size == 0 or crop.shape[0] < 32 or crop.shape[1] < 32:
                continue
            scheduled.append((idx, rider, crop_bbox, crop))

        if not scheduled:
            return results

        try:
            with self._lock:
                predictions = self.model.predict(
                    [crop for _, _, _, crop in scheduled],
                    imgsz=self.imgsz,
                    conf=0.20,
                    agnostic_nms=True,
                    verbose=False,
                    device=self.device,
                    half=self._half,
                )
        except Exception:
            log.exception("Helmet inference batch failed; returning UNKNOWN for this batch")
            return [HelmetResult(HelmetStatus.UNKNOWN, 0.0, tuple()) for _ in riders]

        if len(predictions) != len(scheduled):
            log.warning(
                "Helmet prediction batch size mismatch: expected %s, got %s",
                len(scheduled),
                len(predictions),
            )
            return [HelmetResult(HelmetStatus.UNKNOWN, 0.0, tuple()) for _ in riders]

        for (idx, rider, crop_bbox, _), prediction in zip(scheduled, predictions):
            if not prediction or getattr(prediction, "boxes", None) is None:
                results[idx] = HelmetResult(HelmetStatus.UNKNOWN, 0.0, tuple())
                continue

            boxes = prediction.boxes
            if len(boxes) == 0:
                results[idx] = HelmetResult(HelmetStatus.UNKNOWN, 0.0, tuple())
                continue

            x_offset, y_offset = crop_bbox[0], crop_bbox[1]
            crop_w = max(1, crop_bbox[2] - crop_bbox[0])
            crop_h = max(1, crop_bbox[3] - crop_bbox[1])
            rider_x1, rider_y1, rider_x2, rider_y2 = rider.bbox
            upper_y_limit = rider_y1 + 0.65 * (rider_y2 - rider_y1)

            heads: list[HeadDetection] = []
            xyxy = boxes.xyxy.cpu().numpy()
            confs = boxes.conf.cpu().numpy()
            cls_ids = boxes.cls.cpu().numpy()
            for box, conf, cls_id in zip(xyxy, confs, cls_ids):
                status = self._class_map.get(str(int(cls_id)))
                if status is None:
                    continue

                bx1, by1, bx2, by2 = [float(v) for v in box]
                if bx2 <= bx1 or by2 <= by1:
                    continue

                full_x1 = x_offset + bx1
                full_y1 = y_offset + by1
                full_x2 = x_offset + bx2
                full_y2 = y_offset + by2
                cx = 0.5 * (full_x1 + full_x2)
                cy = 0.5 * (full_y1 + full_y2)
                if not (rider_x1 <= cx <= rider_x2 and rider_y1 <= cy <= upper_y_limit):
                    continue

                head_area = (bx2 - bx1) * (by2 - by1)
                if head_area > 0.35 * crop_w * crop_h:
                    continue

                heads.append(
                    HeadDetection(
                        bbox=(
                            int(max(0, round(full_x1))),
                            int(max(0, round(full_y1))),
                            int(min(frame.shape[1], round(full_x2))),
                            int(min(frame.shape[0], round(full_y2))),
                        ),
                        status=status,
                        confidence=float(conf),
                    )
                )

            results[idx] = decide(heads, self.conf)

        return results
