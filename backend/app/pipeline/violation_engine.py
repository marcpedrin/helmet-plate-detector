"""Temporal violation confirmation per rider track.

Owner: Marc. Signatures are final; bodies are pending. Rules (see docs/ARCHITECTURE.md,
"Violation lifecycle"):

* TRACKING -> SUSPECTED after >= 3 NO_HELMET observations; plate collection starts.
* SUSPECTED -> CONFIRMED when, within the last ``VIOLATION_WINDOW`` observations, there
  are >= ``VIOLATION_MIN_HITS`` NO_HELMET hits with mean confidence >=
  ``VIOLATION_MIN_CONF`` and <= ``VIOLATION_MAX_HELMET_HITS`` HELMET hits.
* CONFIRMED -> PLATE_PENDING -> FINALIZED once the plate voter returns READ /
  UNREADABLE / NOT_DETECTED or ``PLATE_WINDOW_S`` elapses.
* TRACKING/SUSPECTED -> DROPPED when the track is lost for > 2 s.
* CONFIRMED -> SUPPRESSED when it duplicates a violation on the same camera
  (IoU >= ``DEDUP_IOU`` within ``DEDUP_WINDOW_S``, or the same loop position +-1.5 s).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from app.core.types import FramePacket, HelmetResult, Rider

if TYPE_CHECKING:
    from app.config import Settings


class TrackPhase(str, Enum):
    """Lifecycle phase of one rider track inside the engine."""

    TRACKING = "TRACKING"
    SUSPECTED = "SUSPECTED"
    CONFIRMED = "CONFIRMED"
    PLATE_PENDING = "PLATE_PENDING"
    FINALIZED = "FINALIZED"
    DROPPED = "DROPPED"
    SUPPRESSED = "SUPPRESSED"


@dataclass(frozen=True)
class EngineDecision:
    """What the runner must do for one rider after an ``update``.

    Attributes:
        rider_id: Rider / motorcycle track id.
        phase: Phase after this update.
        newly_confirmed: True exactly once, on the update that confirmed the violation.
        collect_plate: True while plate observations should be gathered for this rider.
        helmet_confidence: Mean NO_HELMET confidence over the window.
    """

    rider_id: int
    phase: TrackPhase
    newly_confirmed: bool
    collect_plate: bool
    helmet_confidence: float


class ViolationEngine:
    """Per-camera state machine turning noisy per-frame helmet results into violations.

    Thread-safety: one instance per camera, used by that camera's pipeline thread only.
    """

    def __init__(self, settings: Settings, camera_id: str) -> None:
        """Create the engine with thresholds from settings (``VIOLATION_*``, ``DEDUP_*``)."""
        raise NotImplementedError("Marc: implement ViolationEngine")

    def update(
        self, packet: FramePacket, riders: Sequence[Rider], helmets: Sequence[HelmetResult]
    ) -> list[EngineDecision]:
        """Feed one frame's riders and their helmet results (same order).

        Returns:
            One decision per rider in ``riders``.
        """
        raise NotImplementedError

    def finalize(self, rider_id: int) -> None:
        """Mark a confirmed rider FINALIZED after its plate result was stored."""
        raise NotImplementedError

    def prune(self, now: float) -> list[int]:
        """Drop tracks lost for > 2 s; return the dropped rider ids."""
        raise NotImplementedError
