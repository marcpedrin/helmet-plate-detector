"""Multi-frame plate voting.

Owner: Malik. Signatures are final; bodies are pending.
"""

from __future__ import annotations

import numpy as np

from app.core.types import PlateObservation, PlateResult


class PlateVoter:
    """Implements ``PlateVoterProtocol``: accumulates reads for one violation and votes.

    Contract:
      * ``result()`` is PENDING until ``add`` was called at least once.
      * READ when a valid-format text wins (confidence-weighted vote across reads).
      * UNREADABLE when plates were detected but no read is valid/agreed.
      * NOT_DETECTED when observations were added but none contained a detection.
      * ``ocr_count`` counts observations that contained a read (the pipeline caps OCR
        calls per track with ``PLATE_MAX_OCR_PER_TRACK``).

    Thread-safety: one voter per violation, used from one pipeline thread.
    """

    ocr_count: int

    def __init__(self, min_votes: int = 2) -> None:
        """Create an empty voter.

        Args:
            min_votes: Minimum agreeing valid reads before the status becomes READ.
        """
        raise NotImplementedError("Malik: implement PlateVoter")

    def add(self, obs: PlateObservation) -> None:
        """Add one observation."""
        raise NotImplementedError

    def result(self) -> PlateResult:
        """Return the current voted result."""
        raise NotImplementedError

    def best_crop(self) -> np.ndarray | None:
        """Return the crop of the highest-confidence read supporting the winning text."""
        raise NotImplementedError
