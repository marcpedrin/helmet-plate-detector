"""Live-mode pipeline runner: one processing thread per camera plus one broadcast timer thread.

Owner: Marc. The runner owns all side effects; ``ViolationEngine`` stays pure.

Threads:
    pipeline-<cid> (x N): latest frame -> track -> associate -> helmet -> engine -> actions -> overlay/metrics
    pipeline-broadcast:   camera_metrics every 0.5 s per camera, stats every 5 s
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol

from app.core.interfaces import (
    CameraManagerProtocol,
    EventPublisherProtocol,
    HelmetClassifierProtocol,
    PlateServiceProtocol,
    ViolationRepositoryProtocol,
)
from app.core.schemas import CameraMetricsMsg, StatsOut
from app.core.types import (
    BBox,
    FramePacket,
    HelmetResult,
    HelmetStatus,
    ModelState,
    PipelineMetrics,
    Rider,
    Track,
)
from app.pipeline.association import associate_riders
from app.pipeline.overlay import OverlayRider, OverlayState
from app.pipeline.violation_engine import (
    Confirm,
    EngineAction,
    Finalize,
    NeedPlate,
    TrackPhase,
    ViolationEngine,
)

if TYPE_CHECKING:
    from app.config import Settings

log = logging.getLogger(__name__)

# WHY: camera_metrics at 2 Hz is smooth enough for the UI and keeps WS traffic tiny (contract: <= 2 Hz).
METRICS_PERIOD_S = 0.5
STATS_PERIOD_S = 5.0
# WHY: CPU inference of 5+ helmet crops per frame costs more than the detector; alternating frames halves it
# while every rider still gets ~2-3 looks per second at 5 FPS.
CPU_MAX_RIDERS_EVERY_FRAME = 4
# WHY: after 3 consecutive detector failures the camera's metrics are zeroed so the UI shows it as stalled.
DETECTOR_ERRORS_ZERO_METRICS = 3
# WHY: exponential moving average weight for processing FPS (~5-frame memory).
FPS_EMA = 0.2


class TrackerLike(Protocol):
    """What the runner needs from a tracker (``ObjectTracker`` or a test fake)."""

    state: ModelState
    device: str

    def update(self, packet: FramePacket) -> list[Track]:
        """Return tracks for one frame."""
        ...


@dataclass
class _CameraCtx:
    camera_id: str
    tracker: TrackerLike
    engine: ViolationEngine
    last_frame_index: int = -1
    processed: int = 0
    errors: int = 0
    detector_errors: int = 0
    fps: float = 0.0
    last_t: float | None = None
    last_helmet: dict[int, HelmetResult] = field(default_factory=dict)
    thread: threading.Thread | None = None


class PipelineRunner:
    """Runs detect -> track -> associate -> helmet -> engine -> evidence/plates per camera.

    Thread-safety: ``start``/``stop``/``metrics``/``detector_state`` may be called from any thread.

    Example:
        >>> runner = PipelineRunner(settings, cameras, helmet, plates, repo, hub, container.stats, overlay)
        >>> runner.start(); ...; runner.stop()
    """

    def __init__(
        self,
        settings: Settings,
        cameras: CameraManagerProtocol,
        helmet: HelmetClassifierProtocol,
        plates: PlateServiceProtocol,
        repository: ViolationRepositoryProtocol,
        publisher: EventPublisherProtocol,
        stats_fn: Callable[[], StatsOut],
        overlay: OverlayState | None = None,
        tracker_factory: Callable[[str], TrackerLike] | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        """Store collaborators; no threads start and no models load here.

        Args:
            settings: Application settings (``PIPELINE_FPS``, ``MIN_RIDER_HEIGHT_PX``, engine thresholds).
            cameras: Frame source.
            helmet: Helmet classifier (Prajwal).
            plates: Plate service (Malik).
            repository: Violation storage.
            publisher: Event hub.
            stats_fn: Returns current ``StatsOut`` (from the container).
            overlay: Shared overlay state registered with the camera manager.
            tracker_factory: ``camera_id -> tracker``; defaults to ``ObjectTracker`` (tests inject fakes).
            clock: Time source for the engine (seconds).
        """
        self.settings = settings
        self.cameras = cameras
        self.helmet = helmet
        self.plates = plates
        self.repository = repository
        self.publisher = publisher
        self.stats_fn = stats_fn
        self.overlay = overlay or OverlayState()
        self.clock = clock
        self._tracker_factory = tracker_factory
        self._ctx: dict[str, _CameraCtx] = {}
        self._metrics: dict[str, PipelineMetrics] = {}
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._timer: threading.Thread | None = None

    # ------------------------------------------------------------------ lifecycle
    @property
    def detector_state(self) -> ModelState:
        """Worst detector state across cameras (NOT_LOADED before ``start``)."""
        states = [c.tracker.state for c in self._ctx.values()]
        if not states:
            return ModelState.NOT_LOADED
        for bad in (ModelState.ERROR, ModelState.NOT_LOADED, ModelState.MOCK):
            if bad in states:
                return bad
        return ModelState.LOADED

    def start(self) -> None:
        """Create per-camera trackers/engines and start all threads."""
        factory = self._tracker_factory or self._default_tracker
        self._stop.clear()
        for cid in self.cameras.camera_ids():
            ctx = _CameraCtx(cid, factory(cid), ViolationEngine(self.settings, cid, self.plates.new_voter))
            ctx.thread = threading.Thread(target=self._loop, args=(ctx,), name=f"pipeline-{cid}", daemon=True)
            self._ctx[cid] = ctx
            ctx.thread.start()
        self._timer = threading.Thread(target=self._broadcast_loop, name="pipeline-broadcast", daemon=True)
        self._timer.start()

    def stop(self) -> None:
        """Signal all threads to stop and join them (2 s timeout each). Idempotent."""
        self._stop.set()
        for ctx in self._ctx.values():
            if ctx.thread is not None:
                ctx.thread.join(timeout=2.0)
                ctx.thread = None
        if self._timer is not None:
            self._timer.join(timeout=2.0)
            self._timer = None

    def metrics(self, camera_id: str) -> PipelineMetrics:
        """Return the latest metrics for ``camera_id`` (zeros before the first frame)."""
        with self._lock:
            return self._metrics.get(camera_id, PipelineMetrics(camera_id))

    def processed_frames(self, camera_id: str) -> int:
        """Number of frames processed for ``camera_id`` (diagnostics/tests)."""
        ctx = self._ctx.get(camera_id)
        return ctx.processed if ctx else 0

    def _default_tracker(self, camera_id: str) -> TrackerLike:
        from app.pipeline.detector import ObjectTracker

        return ObjectTracker(self.settings, camera_id)

    # ------------------------------------------------------------------ per-camera loop
    def _loop(self, ctx: _CameraCtx) -> None:
        period = 1.0 / max(self.settings.pipeline_fps, 0.1)
        while not self._stop.is_set():
            t0 = time.monotonic()
            try:
                self._process(ctx)
            except Exception:
                ctx.errors += 1
                # WHY: log the first error with a traceback, then every 50th, so a persistent fault does not
                # flood the log at 5 FPS x 4 cameras.
                if ctx.errors == 1 or ctx.errors % 50 == 0:
                    log.exception(
                        "%s: pipeline iteration failed (%d errors so far)", ctx.camera_id, ctx.errors
                    )
            self._stop.wait(max(0.0, period - (time.monotonic() - t0)))

    def _process(self, ctx: _CameraCtx) -> None:
        packet = self.cameras.latest_frame(ctx.camera_id)
        if packet is None or packet.frame_index == ctx.last_frame_index:
            return
        ctx.last_frame_index = packet.frame_index
        try:
            tracks = ctx.tracker.update(packet)
            ctx.detector_errors = 0
        except Exception:
            ctx.detector_errors += 1
            if ctx.detector_errors >= DETECTOR_ERRORS_ZERO_METRICS:
                with self._lock:
                    self._metrics[ctx.camera_id] = PipelineMetrics(ctx.camera_id)
            raise
        h, w = packet.image.shape[:2]
        riders = associate_riders(tracks, w, h)
        results = self._classify(ctx, packet, riders)
        actions = ctx.engine.update(ctx.camera_id, packet, riders, results, self.clock())
        self._execute(ctx, packet, actions)
        self._update_overlay(ctx, riders, results)
        self._update_metrics(ctx, riders, tracks)

    def _classify(
        self, ctx: _CameraCtx, packet: FramePacket, riders: Sequence[Rider]
    ) -> list[HelmetResult | None]:
        results: list[HelmetResult | None] = [None] * len(riders)
        min_h = self.settings.min_rider_height_px
        eligible = [i for i, r in enumerate(riders) if r.bbox[3] - r.bbox[1] >= min_h]
        if ctx.tracker.device == "cpu" and len(eligible) > CPU_MAX_RIDERS_EVERY_FRAME:
            eligible = [i for i in eligible if (ctx.processed + riders[i].rider_id) % 2 == 0]
        if not eligible:
            return results
        try:
            batch = self.helmet.classify_batch(packet.image, [riders[i] for i in eligible])
        except Exception:
            ctx.errors += 1
            log.exception("%s: helmet classify_batch failed", ctx.camera_id)
            return results
        if len(batch) != len(eligible):
            log.error(
                "%s: helmet returned %d results for %d riders", ctx.camera_id, len(batch), len(eligible)
            )
            return results
        for i, res in zip(eligible, batch, strict=True):
            results[i] = res
            ctx.last_helmet[riders[i].rider_id] = res
        return results

    def _execute(self, ctx: _CameraCtx, packet: FramePacket, actions: Sequence[EngineAction]) -> None:
        claimed: list[BBox] = []
        for action in actions:
            try:
                if isinstance(action, Confirm):
                    out = self.repository.create(action.event)
                    self.publisher.publish("violation_created", out.model_dump(mode="json"))
                    log.info("%s: violation %s (track %d)", ctx.camera_id, out.id, out.track_id)
                elif isinstance(action, NeedPlate):
                    obs = self.plates.observe(
                        packet.image, action.rider, run_ocr=action.run_ocr, exclude=tuple(claimed)
                    )
                    if obs.detection is not None:
                        claimed.append(obs.detection.bbox)
                    ctx.engine.record_plate(action.rider.rider_id, obs)
                elif isinstance(action, Finalize):
                    out = self.repository.update_plate(action.violation_id, action.plate, action.plate_crop)
                    self.publisher.publish("violation_updated", out.model_dump(mode="json"))
            except Exception:
                ctx.errors += 1
                log.exception("%s: failed to execute %s", ctx.camera_id, type(action).__name__)

    def _update_overlay(
        self, ctx: _CameraCtx, riders: Sequence[Rider], results: Sequence[HelmetResult | None]
    ) -> None:
        shown = []
        for r, res in zip(riders, results, strict=True):
            res = res or ctx.last_helmet.get(r.rider_id)
            phase = ctx.engine.phase(r.rider_id)
            shown.append(
                OverlayRider(
                    track_id=r.rider_id,
                    bbox=r.bbox,
                    helmet=res.status if res else HelmetStatus.UNKNOWN,
                    confidence=res.confidence if res else 0.0,
                    violation=phase in (TrackPhase.CONFIRMED, TrackPhase.FINALIZED),
                    plate=ctx.engine.plate_text(r.rider_id),
                )
            )
        live = {r.rider_id for r in riders}
        ctx.last_helmet = {k: v for k, v in ctx.last_helmet.items() if k in live}
        self.overlay.update(ctx.camera_id, shown, ctx.fps)

    def _update_metrics(self, ctx: _CameraCtx, riders: Sequence[Rider], tracks: Sequence[Track]) -> None:
        now = time.monotonic()
        if ctx.last_t is not None and now > ctx.last_t:
            inst = 1.0 / (now - ctx.last_t)
            ctx.fps = inst if ctx.fps == 0.0 else (1 - FPS_EMA) * ctx.fps + FPS_EMA * inst
        ctx.last_t = now
        ctx.processed += 1
        with self._lock:
            self._metrics[ctx.camera_id] = PipelineMetrics(
                ctx.camera_id, round(ctx.fps, 2), len(riders), len(tracks)
            )

    # ------------------------------------------------------------------ broadcasts
    def _broadcast_loop(self) -> None:
        next_stats = time.monotonic() + STATS_PERIOD_S
        while not self._stop.wait(METRICS_PERIOD_S):
            try:
                for cid in list(self._ctx):
                    m = self.metrics(cid)
                    msg = CameraMetricsMsg(
                        camera_id=cid,
                        processing_fps=m.processing_fps,
                        riders_in_view=m.riders_in_view,
                        tracks=self.overlay.track_overlays(cid),
                    )
                    self.publisher.publish("camera_metrics", msg.model_dump(mode="json"))
                if time.monotonic() >= next_stats:
                    next_stats = time.monotonic() + STATS_PERIOD_S
                    self.publisher.publish("stats", self.stats_fn().model_dump(mode="json"))
            except Exception:
                log.exception("broadcast tick failed")
