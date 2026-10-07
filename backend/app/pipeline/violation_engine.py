"""Temporal violation confirmation per rider track: pure logic, no I/O, injected clock.

Owner: Marc. The engine decides; ``PipelineRunner`` executes the resulting ``EngineAction``s (plate
observation, ``repository.create`` / ``update_plate``, WS publishing). Lifecycle, kept in sync with
docs/ARCHITECTURE.md §5 and docs/modules/pipeline.md §7:

* TRACKING -> SUSPECTED: NO_HELMET looks in the window >= ceil(VIOLATION_MIN_HITS / 2).
  Plate collection starts.
* SUSPECTED -> CONFIRMED: NO_HELMET >= VIOLATION_MIN_HITS within the last VIOLATION_WINDOW looks,
  mean NO_HELMET confidence >= VIOLATION_MIN_CONF, HELMET <= VIOLATION_MAX_HELMET_HITS and track age
  >= 5 looks. Emits ``Confirm`` unless a dedup guard matches (-> SUPPRESSED, nothing emitted).
* CONFIRMED -> FINALIZED: at confirmed_at + PLATE_WINDOW_S, or when the track is lost > 1 s.
  Emits ``Finalize``.
* TRACKING/SUSPECTED lost > 2 s -> dropped (state deleted). FINALIZED states are deleted 30 s after
  last seen; a compact dedup record is kept for 10 min.
* Video loop (``loop_index`` changes): tracker ids restart, so confirmed tracks are finalized and all
  others dropped.
"""

from __future__ import annotations

import math
import uuid
from collections import deque
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

import numpy as np

from app.core import geometry
from app.core.interfaces import PlateVoterProtocol
from app.core.types import (
    BBox,
    FramePacket,
    HelmetResult,
    HelmetStatus,
    PlateObservation,
    PlateResult,
    PlateStatus,
    Rider,
    ViolationEvent,
)
from app.pipeline import evidence

if TYPE_CHECKING:
    from app.config import Settings

# WHY: needing >= 5 looks (~1 s at 5 FPS) before confirming stops a brand-new track with a lucky
# streak from firing.
MIN_TRACK_AGE = 5
# WHY: ByteTrack keeps lost tracks ~3 s (track_buffer 15 @ 5 FPS); 1 s without the rider means the
# plate will not get better, so finalize early instead of waiting for PLATE_WINDOW_S.
LOST_FINALIZE_S = 1.0
# WHY: unconfirmed tracks are cheap to rebuild; 2 s covers short occlusions without leaking memory.
DROP_AFTER_S = 2.0
FINALIZED_GC_S = 30.0
# WHY: dedup records must outlive one loop of a 60-120 s demo clip (loop guard) but not grow forever.
RECORD_TTL_S = 600.0
# WHY: after a video restart the same rider reappears at the same file position; +-1.5 s absorbs the
# timing jitter of confirming at a slightly different frame, IoU 0.3 tolerates small box differences.
LOOP_POS_TOL_MS = 1500.0
LOOP_IOU = 0.3


class TrackPhase(str, Enum):
    """Lifecycle phase of one rider track inside the engine."""

    TRACKING = "TRACKING"
    SUSPECTED = "SUSPECTED"
    CONFIRMED = "CONFIRMED"
    FINALIZED = "FINALIZED"
    DROPPED = "DROPPED"
    SUPPRESSED = "SUPPRESSED"


@dataclass(frozen=True)
class NeedPlate:
    """Runner must call ``plates.observe(frame, rider, run_ocr, exclude)`` then ``engine.record_plate``."""

    rider: Rider
    run_ocr: bool


@dataclass(frozen=True)
class Confirm:
    """Runner must ``repository.create(event)`` and publish ``violation_created``."""

    event: ViolationEvent


@dataclass(frozen=True)
class Finalize:
    """Runner must ``repository.update_plate(...)`` and publish ``violation_updated``."""

    violation_id: str
    rider_id: int
    plate: PlateResult
    plate_crop: np.ndarray | None


EngineAction = NeedPlate | Confirm | Finalize


@dataclass
class TrackState:
    """Per-track engine state (internal, exposed for debugging/tests)."""

    rider_id: int
    first_seen: float
    last_seen: float
    rider_bbox: BBox
    observations: deque[tuple[HelmetStatus, float, float]]
    n_obs: int = 0
    phase: TrackPhase = TrackPhase.TRACKING
    violation_id: str | None = None
    voter: PlateVoterProtocol | None = None
    best_evidence: evidence.EvidenceCandidate | None = None
    confirmed_at: float | None = None
    plate_text: str | None = None


@dataclass
class _DedupRecord:
    violation_id: str
    track_id: int
    loop_index: int
    confirm_pos_ms: float
    confirm_bbox: BBox
    last_bbox: BBox
    last_seen: float
    created: float = field(default=0.0)


class ViolationEngine:
    """Per-camera state machine turning noisy per-frame helmet results into one violation per rider.

    Thread-safety: one instance per camera, used only by that camera's pipeline thread.

    Example:
        >>> engine = ViolationEngine(settings, "CAM_01", plates.new_voter)
        >>> for action in engine.update("CAM_01", packet, riders, helmet_results, time.time()):
        ...     runner.execute(action)
    """

    def __init__(
        self, settings: Settings, camera_id: str, voter_factory: Callable[[], PlateVoterProtocol]
    ) -> None:
        """Create the engine with thresholds from ``settings`` (``VIOLATION_*``, ``PLATE_*``, ``DEDUP_*``)."""
        self.camera_id = camera_id
        self.voter_factory = voter_factory
        self.window = settings.violation_window
        self.min_hits = settings.violation_min_hits
        self.suspect_hits = math.ceil(settings.violation_min_hits / 2)
        self.min_conf = settings.violation_min_conf
        self.max_helmet_hits = settings.violation_max_helmet_hits
        self.plate_window_s = settings.plate_window_s
        self.max_ocr = settings.plate_max_ocr_per_track
        self.dedup_iou = settings.dedup_iou
        self.dedup_window_s = settings.dedup_window_s
        self._states: dict[int, TrackState] = {}
        self._records: list[_DedupRecord] = []
        self._loop_index: int | None = None

    # ------------------------------------------------------------------ queries
    def phase(self, rider_id: int) -> TrackPhase | None:
        """Return the phase of a track, or None if the engine holds no state for it."""
        st = self._states.get(rider_id)
        return st.phase if st else None

    def plate_text(self, rider_id: int) -> str | None:
        """Return the final plate text of a finalized track (None otherwise)."""
        st = self._states.get(rider_id)
        return st.plate_text if st else None

    @property
    def active_tracks(self) -> int:
        """Number of tracks the engine currently holds state for."""
        return len(self._states)

    # ------------------------------------------------------------------ update
    def update(
        self,
        camera_id: str,
        packet: FramePacket,
        riders: Sequence[Rider],
        helmet_results: Sequence[HelmetResult | None],
        now: float,
    ) -> list[EngineAction]:
        """Feed one processed frame.

        Args:
            camera_id: Camera of this engine (sanity-checked).
            packet: The frame (used for evidence and loop/position bookkeeping).
            riders: Riders in the frame.
            helmet_results: One per rider, same order; ``None`` = not classified this frame (no vote, but the
                track stays alive).
            now: Clock value in seconds (``time.time()`` in production, a fake clock in tests).

        Returns:
            Actions for the runner, in execution order: confirmations, plate requests, then finalizations.

        Raises:
            ValueError: If ``riders`` and ``helmet_results`` differ in length or the camera id is wrong.
        """
        if len(riders) != len(helmet_results):
            raise ValueError("riders and helmet_results must have the same length")
        if camera_id != self.camera_id:
            raise ValueError(f"engine for {self.camera_id} got frame from {camera_id}")
        actions: list[EngineAction] = []
        if self._loop_index is not None and packet.loop_index != self._loop_index:
            actions += self._on_loop_restart()
        self._loop_index = packet.loop_index

        seen: set[int] = set()
        for rider, result in zip(riders, helmet_results, strict=True):
            seen.add(rider.rider_id)
            actions += self._observe(packet, rider, result, now)
        actions += self._housekeeping(seen, now)
        order = {Confirm: 0, NeedPlate: 1, Finalize: 2}
        actions.sort(key=lambda a: order[type(a)])
        return actions

    def record_plate(self, rider_id: int, obs: PlateObservation) -> None:
        """Feed a plate observation (requested via ``NeedPlate``) into the track's voter."""
        st = self._states.get(rider_id)
        if st and st.voter is not None and st.phase in (TrackPhase.SUSPECTED, TrackPhase.CONFIRMED):
            st.voter.add(obs)

    # ------------------------------------------------------------------ internals
    def _observe(
        self, packet: FramePacket, rider: Rider, result: HelmetResult | None, now: float
    ) -> list[EngineAction]:
        st = self._states.get(rider.rider_id)
        if st is None:
            st = TrackState(rider.rider_id, now, now, rider.bbox, deque(maxlen=self.window))
            self._states[rider.rider_id] = st
        st.last_seen = now
        st.rider_bbox = rider.bbox
        if st.violation_id is not None:
            for rec in self._records:
                if rec.violation_id == st.violation_id:
                    rec.last_bbox, rec.last_seen = rider.bbox, now

        actions: list[EngineAction] = []
        if result is not None:
            st.observations.append((result.status, result.confidence, now))
            st.n_obs += 1
        nh = [c for s, c, _ in st.observations if s == HelmetStatus.NO_HELMET]

        if st.phase == TrackPhase.TRACKING and len(nh) >= self.suspect_hits:
            st.phase = TrackPhase.SUSPECTED
            st.voter = self.voter_factory()

        if (
            result is not None
            and result.status == HelmetStatus.NO_HELMET
            and st.phase in (TrackPhase.SUSPECTED, TrackPhase.CONFIRMED)
        ):
            st.best_evidence = evidence.offer(st.best_evidence, packet, rider.bbox, result.confidence)

        if st.phase == TrackPhase.SUSPECTED and self._meets_rule(st, nh):
            if self._is_duplicate(st, packet, rider.bbox, now):
                st.phase = TrackPhase.SUPPRESSED
                st.voter = None
                st.best_evidence = None
            else:
                actions.append(self._confirm(st, packet, rider, nh, now))

        if st.phase in (TrackPhase.SUSPECTED, TrackPhase.CONFIRMED) and st.voter is not None:
            actions.append(NeedPlate(rider, run_ocr=st.voter.ocr_count < self.max_ocr))
        return actions

    def _meets_rule(self, st: TrackState, nh: list[float]) -> bool:
        helmet_hits = sum(1 for s, _, _ in st.observations if s == HelmetStatus.HELMET)
        return (
            len(nh) >= self.min_hits
            and sum(nh) / len(nh) >= self.min_conf
            and helmet_hits <= self.max_helmet_hits
            and st.n_obs >= MIN_TRACK_AGE
        )

    def _is_duplicate(self, st: TrackState, packet: FramePacket, bbox: BBox, now: float) -> bool:
        for rec in self._records:
            # (a) one violation per track, ever (track ids restart each loop, so key on loop too)
            if rec.track_id == st.rider_id and rec.loop_index == packet.loop_index:
                return True
            # (b) ID-switch guard: the same rider re-identified with a new id shortly after
            if (
                now - rec.last_seen <= self.dedup_window_s
                and geometry.iou(rec.last_bbox, bbox) >= self.dedup_iou
            ):
                return True
            # (c) loop guard: same place in the file, earlier loop of the prerecorded video
            if (
                rec.loop_index < packet.loop_index
                and abs(rec.confirm_pos_ms - packet.video_pos_ms) <= LOOP_POS_TOL_MS
                and geometry.iou(rec.confirm_bbox, bbox) >= LOOP_IOU
            ):
                return True
        return False

    def _confirm(
        self, st: TrackState, packet: FramePacket, rider: Rider, nh: list[float], now: float
    ) -> Confirm:
        best = st.best_evidence or evidence.offer(None, packet, rider.bbox, nh[-1] if nh else 0.0)
        assert best is not None
        st.phase = TrackPhase.CONFIRMED
        st.confirmed_at = now
        st.violation_id = uuid.uuid4().hex
        self._records.append(
            _DedupRecord(
                st.violation_id,
                st.rider_id,
                packet.loop_index,
                packet.video_pos_ms,
                rider.bbox,
                rider.bbox,
                now,
                now,
            )
        )
        event = ViolationEvent(
            violation_id=st.violation_id,
            camera_id=self.camera_id,
            track_id=st.rider_id,
            violation_type="NO_HELMET",
            helmet_confidence=round(sum(nh) / len(nh), 4),
            rider_bbox=best.bbox,
            frame_index=best.frame_index,
            video_pos_ms=best.video_pos_ms,
            timestamp=best.timestamp,
            evidence=evidence.build_evidence(best, st.rider_id),
        )
        st.best_evidence = None  # free the frame copy
        return Confirm(event)

    def _finalize(self, st: TrackState) -> Finalize:
        assert st.violation_id is not None
        result = st.voter.result() if st.voter is not None else None
        if result is None or result.status == PlateStatus.PENDING:
            result = PlateResult(PlateStatus.NOT_DETECTED, None, 0.0, 0)
        crop = st.voter.best_crop() if st.voter is not None else None
        st.phase = TrackPhase.FINALIZED
        st.plate_text = result.text
        st.voter = None
        return Finalize(st.violation_id, st.rider_id, result, crop)

    def _housekeeping(self, seen: set[int], now: float) -> list[EngineAction]:
        actions: list[EngineAction] = []
        for rid, st in list(self._states.items()):
            lost = now - st.last_seen if rid not in seen else 0.0
            if st.phase == TrackPhase.CONFIRMED:
                assert st.confirmed_at is not None
                if lost > LOST_FINALIZE_S or now >= st.confirmed_at + self.plate_window_s:
                    actions.append(self._finalize(st))
            elif st.phase in (TrackPhase.TRACKING, TrackPhase.SUSPECTED, TrackPhase.SUPPRESSED):
                if lost > DROP_AFTER_S:
                    del self._states[rid]
            elif st.phase == TrackPhase.FINALIZED and lost > FINALIZED_GC_S:
                del self._states[rid]
        self._records = [r for r in self._records if now - r.created <= RECORD_TTL_S]
        return actions

    def _on_loop_restart(self) -> list[EngineAction]:
        actions: list[EngineAction] = [
            self._finalize(st) for st in self._states.values() if st.phase == TrackPhase.CONFIRMED
        ]
        self._states.clear()
        return actions
