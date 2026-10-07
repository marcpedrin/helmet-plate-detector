"""Plate OCR (RapidOCR 3.9 / PP-OCR).

Owner: Malik. Signatures are final; bodies are pending.
Import ``rapidocr`` inside ``__init__``, never at module top level.
"""

from __future__ import annotations

import numpy as np

from app.core.types import ModelState, PlateRead


class PlateOCR:
    """Reads text from a plate crop and applies Indian-format correction.

    Thread-safety: may be shared; serialise engine calls with a lock.
    """

    state: ModelState

    def __init__(self, engine: str = "rapidocr") -> None:
        """Load the OCR engine (``OCR_ENGINE``).

        Raises:
            NotImplementedError: Until Malik implements it.
            ValueError: For an unknown engine name.
        """
        raise NotImplementedError("Malik: implement PlateOCR")

    def read(self, crop: np.ndarray) -> PlateRead | None:
        """OCR one plate crop.

        Two-line plates must be joined top-to-bottom. ``raw_text`` is the engine output,
        ``text`` the result of ``indian_format.correct``.

        Returns:
            A ``PlateRead``, or None if no text was found. Never raises on bad crops.
        """
        raise NotImplementedError
