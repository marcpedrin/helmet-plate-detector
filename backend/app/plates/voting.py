"""Multi-frame plate voting.

Policy: a wrong plate is worse than UNKNOWN, so READ needs a valid Indian format plus
either agreement across reads or one very confident read.
"""

from __future__ import annotations

from collections import Counter, defaultdict

import numpy as np

from app.core.types import PlateObservation, PlateRead, PlateResult, PlateStatus
from app.plates.indian_format import correct

# WHY: a single read must be this confident to stand alone without a second agreeing read.
SINGLE_READ_CONF = 0.90
INVALID_WEIGHT = 0.3


class PlateVoter:
    """Implements ``PlateVoterProtocol``: accumulates reads for one violation and votes.

    Contract:
      * ``result()`` is PENDING until ``add`` was called at least once.
      * READ when a valid-format text wins (confidence-weighted vote across reads).
      * UNREADABLE when plates were detected but no read is valid/agreed.
      * NOT_DETECTED when observations were added but none contained a detection.
      * ``ocr_count`` counts observations that contained a read.

    Thread-safety: one voter per violation, used from one pipeline thread.
    """

    ocr_count: int

    def __init__(self, min_votes: int = 2) -> None:
        """Create an empty voter.

        Args:
            min_votes: Minimum agreeing valid reads before the status becomes READ
                (unless a single read has confidence >= ``SINGLE_READ_CONF``).
        """
        self.min_votes = min_votes
        self.ocr_count = 0
        self._observations = 0
        self._detections = 0
        self._reads: list[tuple[PlateRead, np.ndarray | None]] = []
        self._best_det_crop: tuple[float, np.ndarray] | None = None

    def add(self, obs: PlateObservation) -> None:
        """Add one observation."""
        self._observations += 1
        if obs.detection is not None:
            self._detections += 1
            if obs.crop is not None:
                score = obs.detection.confidence * obs.crop.shape[1]
                if self._best_det_crop is None or score > self._best_det_crop[0]:
                    self._best_det_crop = (score, obs.crop)
        if obs.read is not None:
            self.ocr_count += 1
            if obs.read.text:
                self._reads.append((obs.read, obs.crop))

    def _vote(self) -> tuple[str, float, int] | None:
        weights: dict[str, float] = defaultdict(float)
        confs: dict[str, list[float]] = defaultdict(list)
        valid: dict[str, bool] = {}
        for r, _ in self._reads:
            weights[r.text] += r.confidence * (1.0 if r.valid_format else INVALID_WEIGHT)
            confs[r.text].append(r.confidence)
            valid[r.text] = r.valid_format
        if weights:
            winner = max(weights, key=weights.__getitem__)
            n = len(confs[winner])
            mean = sum(confs[winner]) / n
            if valid[winner] and (n >= self.min_votes or max(confs[winner]) >= SINGLE_READ_CONF):
                return winner, mean, n
        # Character-level vote across valid reads of the modal length.
        vr = [r for r, _ in self._reads if r.valid_format]
        if len(vr) >= self.min_votes:
            length = Counter(len(r.text) for r in vr).most_common(1)[0][0]
            same = [r for r in vr if len(r.text) == length]
            if len(same) >= self.min_votes:
                chars = []
                for i in range(length):
                    c: dict[str, float] = defaultdict(float)
                    for r in same:
                        c[r.text[i]] += r.confidence
                    chars.append(max(c, key=c.__getitem__))
                text, ok = correct("".join(chars))
                if ok:
                    return text, 0.9 * sum(r.confidence for r in same) / len(same), len(same)
        return None

    def result(self) -> PlateResult:
        """Return the current voted result."""
        if self._observations == 0:
            return PlateResult(PlateStatus.PENDING, None, 0.0, 0)
        voted = self._vote()
        if voted:
            text, conf, votes = voted
            return PlateResult(PlateStatus.READ, text, round(float(conf), 4), votes)
        if self._detections:
            return PlateResult(PlateStatus.UNREADABLE, None, 0.0, 0)
        return PlateResult(PlateStatus.NOT_DETECTED, None, 0.0, 0)

    def best_crop(self) -> np.ndarray | None:
        """Return the crop of the highest-confidence read supporting the winning text."""
        voted = self._vote()
        if voted:
            supporting = [(r.confidence, c) for r, c in self._reads if r.text == voted[0] and c is not None]
            if supporting:
                return max(supporting, key=lambda t: t[0])[1]
        return self._best_det_crop[1] if self._best_det_crop else None
