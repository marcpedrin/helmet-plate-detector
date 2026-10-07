"""Mock plate service + voter for mock mode, fallbacks and tests.

Owner: Malik (may extend; keep existing behaviour stable, other tests depend on it).
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from app.core.types import BBox, ModelState, PlateObservation, PlateResult, PlateStatus, Rider


class MockPlateVoter:
    """Voter that never sees a plate: PENDING until the first ``add``, then NOT_DETECTED."""

    def __init__(self) -> None:
        """Create an empty voter."""
        self.ocr_count = 0
        self._seen = 0

    def add(self, obs: PlateObservation) -> None:
        """Count the observation (contents ignored except for ``ocr_count``)."""
        self._seen += 1
        if obs.read is not None:
            self.ocr_count += 1

    def result(self) -> PlateResult:
        """Return PENDING before any observation, NOT_DETECTED after."""
        if self._seen == 0:
            return PlateResult(PlateStatus.PENDING, None, 0.0, 0)
        return PlateResult(PlateStatus.NOT_DETECTED, None, 0.0, 0)

    def best_crop(self) -> np.ndarray | None:
        """Return None (no crops)."""
        return None


class MockPlateService:
    """Plate service that never detects anything; used as the not-loaded fallback.

    Thread-safety: stateless, safe everywhere.
    """

    def __init__(self, state: ModelState = ModelState.MOCK) -> None:
        """Create the mock; both ``detector_state`` and ``ocr_state`` report ``state``."""
        self.detector_state = state
        self.ocr_state = state

    def observe(
        self, frame: np.ndarray, rider: Rider, run_ocr: bool = True, exclude: Sequence[BBox] = ()
    ) -> PlateObservation:
        """Return an empty observation."""
        return PlateObservation(detection=None, read=None, crop=None)

    def new_voter(self) -> MockPlateVoter:
        """Return a ``MockPlateVoter``."""
        return MockPlateVoter()
