"""Plate OCR (RapidOCR 3.x = PaddleOCR PP-OCR models on ONNX Runtime, Apache-2.0).

Import ``rapidocr`` inside ``__init__``, never at module top level.

WHY RapidOCR: fast-plate-ocr's global models were not trained on Indian plates, and
Indian motorcycle plates are often two lines; PP-OCR text detection handles that.
"""

from __future__ import annotations

import logging
import threading

import cv2
import numpy as np

from app.core.types import ModelState, PlateRead
from app.plates.indian_format import correct

log = logging.getLogger(__name__)


def _preprocess(crop: np.ndarray) -> np.ndarray:
    """Pad, upscale and contrast-normalise a plate crop for OCR."""
    img = cv2.copyMakeBorder(crop, 6, 6, 6, 6, cv2.BORDER_REPLICATE)
    h = img.shape[0]
    # WHY: PP-OCR rec works best with ~48px text lines; two-line plates need ~2x that.
    target_h = 110
    if h < target_h:
        scale = target_h / max(h, 1)
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4)).apply(gray)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)


def assemble_lines(boxes: list, txts: list[str], scores: list[float]) -> tuple[str, float]:
    """Join OCR fragments into one plate string: lines top-to-bottom, left-to-right in a line.

    Returns:
        ``(text, confidence)`` where confidence is the character-weighted mean score.
    """
    items = []
    for box, txt, sc in zip(boxes, txts, scores, strict=False):
        pts = np.asarray(box, dtype=float).reshape(-1, 2)
        ys, xs = pts[:, 1], pts[:, 0]
        items.append((float(ys.mean()), float(xs.min()), float(ys.max() - ys.min()), txt, float(sc)))
    if not items:
        return "", 0.0
    items.sort(key=lambda it: it[0])
    med_h = float(np.median([it[2] for it in items])) or 1.0
    lines: list[list[tuple]] = []
    for it in items:
        if lines and abs(it[0] - lines[-1][0][0]) < 0.5 * med_h:
            lines[-1].append(it)
        else:
            lines.append([it])
    parts = []
    for line in lines:
        line.sort(key=lambda it: it[1])
        parts.extend(line)
    text = "".join(p[3] for p in parts)
    n = sum(len(p[3]) for p in parts) or 1
    conf = sum(len(p[3]) * p[4] for p in parts) / n
    return text, conf


class PlateOCR:
    """Reads text from a plate crop and applies Indian-format correction.

    Thread-safety: may be shared; engine calls are serialised with a lock.
    """

    state: ModelState

    def __init__(self, engine: str = "rapidocr") -> None:
        """Load the OCR engine (``OCR_ENGINE``).

        Raises:
            ValueError: For an unknown engine name.
        """
        if engine != "rapidocr":
            raise ValueError(f"Unknown OCR engine {engine!r} (supported: rapidocr)")
        from rapidocr import RapidOCR

        self._engine = RapidOCR()
        self._lock = threading.Lock()
        self.state = ModelState.LOADED
        log.info("RapidOCR loaded")

    def _run(self, img: np.ndarray) -> tuple[str, float]:
        with self._lock:
            out = self._engine(img)
        txts = list(out.txts or ())
        if not txts:
            return "", 0.0
        boxes = out.boxes.tolist() if out.boxes is not None else [[[0, i], [1, i]] for i in range(len(txts))]
        return assemble_lines(boxes, txts, list(out.scores or [0.0] * len(txts)))

    def read(self, crop: np.ndarray) -> PlateRead | None:
        """OCR one plate crop.

        Two-line plates are joined top-to-bottom. ``raw_text`` is the engine output,
        ``text`` the result of ``indian_format.correct``.

        Returns:
            A ``PlateRead`` (empty text + confidence 0 when OCR ran but found nothing), or
            None for an unusable crop. Never raises.
        """
        try:
            if crop is None or crop.size == 0 or min(crop.shape[:2]) < 8:
                return None
            raw, conf = self._run(_preprocess(crop))
            if not raw:
                raw, conf = self._run(crop)
            if not raw:
                return PlateRead(raw_text="", text="", confidence=0.0, valid_format=False)
            text, valid = correct(raw)
            return PlateRead(raw_text=raw, text=text, confidence=float(conf), valid_format=valid)
        except Exception:
            log.exception("OCR failed")
            return None
