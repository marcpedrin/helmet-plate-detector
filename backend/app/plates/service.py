"""Plate service: detector + OCR + voter factory behind ``PlateServiceProtocol``."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING

import cv2
import numpy as np

from app.core.geometry import clip, expand, ioa
from app.core.types import BBox, ModelState, PlateObservation, Rider
from app.plates.detector import PlateDetector
from app.plates.ocr import PlateOCR
from app.plates.voting import PlateVoter

if TYPE_CHECKING:
    from app.config import Settings

log = logging.getLogger(__name__)

# WHY: blurrier crops than this produce confident garbage from OCR.
MIN_SHARPNESS = 25.0


class PlateService:
    """Implements ``PlateServiceProtocol``.

    ``observe`` searches the rider's motorcycle box (expanded, mostly downwards: plates sit
    low on two-wheelers), picks the best detection not overlapping ``exclude``, and runs OCR
    on the crop only when ``run_ocr`` is True and the crop is big and sharp enough.

    Thread-safety: shared by all pipeline threads; detector and OCR serialise internally.
    """

    detector_state: ModelState
    ocr_state: ModelState

    def __init__(self, detector: PlateDetector, ocr: PlateOCR | None, min_width_px: int = 50) -> None:
        """Wrap an already-loaded detector and (optional) OCR engine."""
        self.detector = detector
        self.ocr = ocr
        self.min_width_px = min_width_px
        self.detector_state = detector.state
        self.ocr_state = ocr.state if ocr is not None else ModelState.NOT_LOADED

    @classmethod
    def from_settings(cls, settings: Settings) -> PlateService:
        """Build detector + OCR from settings.

        Raises:
            Exception: Detector load error (the factory converts it to state=ERROR). OCR load
                errors are tolerated: detection still works, ``ocr_state`` becomes ERROR.
        """
        detector = PlateDetector(
            settings.plate_detector_model,
            conf=settings.plate_detector_conf,
            min_width_px=settings.plate_min_width_px,
            device=settings.device,
        )
        ocr: PlateOCR | None = None
        if settings.ocr_engine != "none":
            try:
                ocr = PlateOCR(settings.ocr_engine)
            except Exception:
                log.exception("OCR failed to load; plates will be UNREADABLE")
        svc = cls(detector, ocr, settings.plate_min_width_px)
        if ocr is None and settings.ocr_engine != "none":
            svc.ocr_state = ModelState.ERROR
        return svc

    def observe(
        self, frame: np.ndarray, rider: Rider, run_ocr: bool = True, exclude: Sequence[BBox] = ()
    ) -> PlateObservation:
        """See ``PlateServiceProtocol.observe``. Never raises."""
        try:
            h, w = frame.shape[:2]
            moto = rider.motorcycle.bbox
            region = expand(moto, 0.15, 0.10, 0.25, w, h)
            dets = self.detector.detect(frame, region, exclude)
            if not dets:
                return PlateObservation(detection=None, read=None, crop=None)
            mcx = (moto[0] + moto[2]) / 2
            mw = max(moto[2] - moto[0], 1)

            def score(d):  # confidence x containment x horizontal centring
                cx = (d.bbox[0] + d.bbox[2]) / 2
                return d.confidence * max(ioa(d.bbox, region), 0.01) * max(1 - abs(cx - mcx) / mw, 0.05)

            best = max(dets, key=score)
            x1, y1, x2, y2 = clip(
                (best.bbox[0] - 4, best.bbox[1] - 4, best.bbox[2] + 4, best.bbox[3] + 4), w, h
            )
            crop = frame[y1:y2, x1:x2].copy()
            read = None
            if run_ocr and self.ocr is not None and crop.size and crop.shape[1] >= self.min_width_px:
                sharp = cv2.Laplacian(cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()
                if sharp >= MIN_SHARPNESS:
                    read = self.ocr.read(crop)
            return PlateObservation(detection=best, read=read, crop=crop)
        except Exception:
            log.exception("plate observe failed")
            return PlateObservation(detection=None, read=None, crop=None)

    def new_voter(self) -> PlateVoter:
        """Return a fresh ``PlateVoter``."""
        return PlateVoter()
