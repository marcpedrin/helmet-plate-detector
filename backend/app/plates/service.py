"""Plate service: detector + OCR + voter factory behind ``PlateServiceProtocol``.

Owner: Malik. Signatures are final; bodies are pending.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

import numpy as np

from app.core.types import BBox, ModelState, PlateObservation, Rider
from app.plates.detector import PlateDetector
from app.plates.ocr import PlateOCR
from app.plates.voting import PlateVoter

if TYPE_CHECKING:
    from app.config import Settings


class PlateService:
    """Implements ``PlateServiceProtocol``.

    ``observe`` searches the rider's motorcycle box expanded downwards (plates sit low on
    two-wheelers), picks the best detection not overlapping ``exclude``, and runs OCR on
    the crop only when ``run_ocr`` is True.

    Thread-safety: shared by all pipeline threads; detector and OCR serialise internally.
    """

    detector_state: ModelState
    ocr_state: ModelState

    def __init__(self, detector: PlateDetector, ocr: PlateOCR) -> None:
        """Wrap an already-loaded detector and OCR engine."""
        raise NotImplementedError("Malik: implement PlateService")

    @classmethod
    def from_settings(cls, settings: Settings) -> PlateService:
        """Build detector + OCR from settings.

        Raises:
            NotImplementedError: Until Malik implements it.
            Exception: Any load error (the factory converts it to state=ERROR).
        """
        raise NotImplementedError("Malik: implement PlateService.from_settings")

    def observe(
        self, frame: np.ndarray, rider: Rider, run_ocr: bool = True, exclude: Sequence[BBox] = ()
    ) -> PlateObservation:
        """See ``PlateServiceProtocol.observe``."""
        raise NotImplementedError

    def new_voter(self) -> PlateVoter:
        """Return a fresh ``PlateVoter``."""
        raise NotImplementedError
