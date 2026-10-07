"""Mock helmet classifiers for mock mode, fallbacks and tests.

Owner: Prajwal (may extend; keep existing behaviour stable, other tests depend on it).
"""

from __future__ import annotations

import itertools
from collections.abc import Sequence

import numpy as np

from app.core.types import HelmetResult, HelmetStatus, ModelState, Rider


class MockHelmetClassifier:
    """Always returns ``HelmetResult(UNKNOWN, 0.0)``; used as the not-loaded fallback.

    Thread-safety: stateless, safe everywhere.
    """

    def __init__(self, state: ModelState = ModelState.MOCK) -> None:
        """Create the mock reporting ``state`` (MOCK, NOT_LOADED or ERROR)."""
        self.state = state

    def classify_batch(self, frame: np.ndarray, riders: Sequence[Rider]) -> list[HelmetResult]:
        """Return UNKNOWN for every rider."""
        return [HelmetResult(HelmetStatus.UNKNOWN, 0.0) for _ in riders]


class ScriptedHelmetClassifier:
    """Replays a fixed sequence of statuses, one per rider per call (cycling); for tests.

    Example: ``ScriptedHelmetClassifier([NO_HELMET] * 6 + [HELMET])``.
    Thread-safety: not thread-safe (tests only).
    """

    def __init__(self, sequence: Sequence[HelmetStatus | HelmetResult], confidence: float = 0.9) -> None:
        """Create the scripted classifier.

        Args:
            sequence: Statuses (or full results) to replay in order, cycling at the end.
            confidence: Confidence used when ``sequence`` holds bare statuses.
        """
        if not sequence:
            raise ValueError("sequence must not be empty")
        self.state = ModelState.MOCK
        self._it = itertools.cycle(
            [s if isinstance(s, HelmetResult) else HelmetResult(s, confidence) for s in sequence]
        )

    def classify_batch(self, frame: np.ndarray, riders: Sequence[Rider]) -> list[HelmetResult]:
        """Return the next scripted result for each rider."""
        return [next(self._it) for _ in riders]
