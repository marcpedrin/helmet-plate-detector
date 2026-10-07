"""Mock-mode runner: fake tracks, fake violations and fake plates, no ML at all.

Owner: Marc. Lets the API, WebSocket and frontend be developed before any model exists.
Everything it produces is labelled "MOCK".
"""

from __future__ import annotations

import logging
import random
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field

import cv2
import numpy as np

from app.core import geometry
from app.core.interfaces import CameraManagerProtocol, EventPublisherProtocol, ViolationRepositoryProtocol
from app.core.schemas import CameraMetricsMsg, StatsOut, TrackOverlay
from app.core.types import (
    BBox,
    EvidenceBundle,
    HelmetStatus,
    ModelState,
    PipelineMetrics,
    PlateResult,
    PlateStatus,
    ViolationEvent,
)
from app.pipeline.overlay import OverlayRider, OverlayState

log = logging.getLogger(__name__)

MOCK_PLATES: tuple[str | None, ...] = ("KA01AB1234", "MH12DE1433", "DL3CAF0001", "TN09BC5678", None)
"""Plates assigned in rotation; ``None`` produces an UNREADABLE result."""


@dataclass
class _CameraSim:
    next_violation_at: float
    n_tracks: int = 1
    statuses: list[HelmetStatus] = field(default_factory=list)
    tracks: list[TrackOverlay] = field(default_factory=list)
    reshuffle_at: float = 0.0
    fps: float = 5.0


class MockRunner:
    """Simulates the pipeline for every camera from one background thread.

    * Every ``interval_s`` (random in range) per camera: builds a fake ``ViolationEvent``
      from the current frame, ``repository.create`` + publish ``violation_created``.
    * ``plate_delay_s`` later: ``repository.update_plate`` with the next mock plate +
      publish ``violation_updated``.
    * At 2 Hz: 1-3 fake moving tracks per camera -> overlay + ``camera_metrics``.
    * Every 5 s: publish ``stats``.

    Thread-safety: ``start``/``stop``/``metrics`` may be called from any thread.
    """

    detector_state = ModelState.MOCK

    def __init__(
        self,
        cameras: CameraManagerProtocol,
        repository: ViolationRepositoryProtocol,
        publisher: EventPublisherProtocol,
        stats_fn: Callable[[], StatsOut],
        interval_s: tuple[float, float] = (8.0, 15.0),
        plate_delay_s: float = 2.0,
        seed: int | None = None,
        overlay: OverlayState | None = None,
    ) -> None:
        """Create the runner (no thread yet).

        Args:
            cameras: Source of frames.
            repository: Where fake violations are stored.
            publisher: Event hub for WS messages.
            stats_fn: Returns the current ``StatsOut`` (provided by the container).
            interval_s: Min/max seconds between fake violations per camera.
            plate_delay_s: Delay between ``violation_created`` and ``violation_updated``.
            seed: Optional RNG seed for deterministic tests.
            overlay: Shared overlay state (registered with the camera manager by the container).
        """
        self.cameras = cameras
        self.repository = repository
        self.publisher = publisher
        self.stats_fn = stats_fn
        self.interval_s = interval_s
        self.plate_delay_s = plate_delay_s
        self.overlay = overlay or OverlayState()
        self._rng = random.Random(seed)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._metrics: dict[str, PipelineMetrics] = {}
        self._sims: dict[str, _CameraSim] = {}
        self._pending_plates: list[tuple[float, str, str]] = []  # (due, violation_id, camera_id)
        self._plate_idx = 0
        self._next_track_id = 1

    # ----------------------------------------------------------------- lifecycle
    def start(self) -> None:
        """Start the simulation thread."""
        now = time.monotonic()
        for cid in self.cameras.camera_ids():
            self._sims[cid] = _CameraSim(next_violation_at=now + self._rng.uniform(*self.interval_s))
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="mock-runner", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the simulation thread (idempotent)."""
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def metrics(self, camera_id: str) -> PipelineMetrics:
        """Return the latest fake metrics for ``camera_id``."""
        with self._lock:
            return self._metrics.get(camera_id, PipelineMetrics(camera_id))

    # ----------------------------------------------------------------- loop
    def _run(self) -> None:
        next_metrics = 0.0
        next_stats = time.monotonic() + 1.0
        while not self._stop.wait(0.1):
            now = time.monotonic()
            try:
                if now >= next_metrics:
                    next_metrics = now + 0.5
                    for cid in self._sims:
                        self._tick_tracks(cid, now)
                for cid, sim in self._sims.items():
                    if now >= sim.next_violation_at:
                        if self._emit_violation(cid, sim):
                            sim.next_violation_at = now + self._rng.uniform(*self.interval_s)
                self._flush_plates(now)
                if now >= next_stats:
                    next_stats = now + 5.0
                    self.publisher.publish("stats", self.stats_fn().model_dump(mode="json"))
            except Exception:  # the simulation must never die
                log.exception("mock runner tick failed")

    def _frame_size(self, cid: str) -> tuple[int, int]:
        rt = self.cameras.get_runtime(cid)
        return (rt.width or 1280, rt.height or 720)

    def _tick_tracks(self, cid: str, now: float) -> None:
        sim = self._sims[cid]
        if now >= sim.reshuffle_at:
            sim.reshuffle_at = now + self._rng.uniform(4.0, 8.0)
            sim.n_tracks = self._rng.randint(1, 3)
            sim.statuses = [
                self._rng.choice([HelmetStatus.HELMET, HelmetStatus.NO_HELMET, HelmetStatus.UNKNOWN])
                for _ in range(sim.n_tracks)
            ]
            self._next_track_id += sim.n_tracks
        w, h = self._frame_size(cid)
        bw, bh = int(w * 0.12), int(h * 0.38)
        tracks = []
        for i in range(sim.n_tracks):
            phase = (now * 0.05 + i * 0.33) % 1.0
            cx = int((0.15 + 0.7 * phase) * w)
            cy = int((0.50 + 0.08 * i) * h)
            box: BBox = geometry.clip((cx - bw // 2, cy - bh // 2, cx + bw // 2, cy + bh // 2), w, h)
            tracks.append(
                TrackOverlay(track_id=self._next_track_id + i, bbox=list(box), helmet=sim.statuses[i])
            )
        sim.tracks = tracks
        sim.fps = round(self._rng.uniform(4.5, 5.5), 2)
        self.overlay.update(
            cid,
            [OverlayRider(t.track_id, tuple(t.bbox), t.helmet, 0.8) for t in tracks],  # type: ignore[arg-type]
            sim.fps,
        )
        with self._lock:
            self._metrics[cid] = PipelineMetrics(cid, sim.fps, len(tracks), len(tracks) * 2)
        msg = CameraMetricsMsg(
            camera_id=cid, processing_fps=sim.fps, riders_in_view=len(tracks), tracks=tracks
        )
        self.publisher.publish("camera_metrics", msg.model_dump(mode="json"))

    # ----------------------------------------------------------------- violations
    def _emit_violation(self, cid: str, sim: _CameraSim) -> bool:
        packet = self.cameras.latest_frame(cid)
        if packet is None or not sim.tracks:
            return False
        track = next((t for t in sim.tracks if t.helmet == HelmetStatus.NO_HELMET), sim.tracks[0])
        bbox: BBox = tuple(track.bbox)  # type: ignore[assignment]
        clean = packet.image.copy()
        rider_crop = geometry.crop(clean, bbox)
        if rider_crop.size == 0:
            return False
        _label(rider_crop, "MOCK")
        full = clean.copy()
        cv2.rectangle(full, bbox[:2], bbox[2:], (40, 40, 230), 4)
        _label(full, "MOCK EVIDENCE - NO_HELMET")
        event = ViolationEvent(
            violation_id=uuid.uuid4().hex,
            camera_id=cid,
            track_id=track.track_id,
            violation_type="NO_HELMET",
            helmet_confidence=round(self._rng.uniform(0.6, 0.95), 3),
            rider_bbox=bbox,
            frame_index=packet.frame_index,
            video_pos_ms=packet.video_pos_ms,
            timestamp=time.time(),
            evidence=EvidenceBundle(full_frame=full, rider_crop=rider_crop),
        )
        out = self.repository.create(event)
        self.publisher.publish("violation_created", out.model_dump(mode="json"))
        with self._lock:
            self._pending_plates.append((time.monotonic() + self.plate_delay_s, out.id, cid))
        return True

    def _flush_plates(self, now: float) -> None:
        with self._lock:
            due = [p for p in self._pending_plates if p[0] <= now]
            self._pending_plates = [p for p in self._pending_plates if p[0] > now]
        for _, vid, _cid in due:
            text = MOCK_PLATES[self._plate_idx % len(MOCK_PLATES)]
            self._plate_idx += 1
            crop = _render_plate(text)
            if text is None:
                result = PlateResult(PlateStatus.UNREADABLE, None, 0.21, 3)
            else:
                result = PlateResult(PlateStatus.READ, text, round(self._rng.uniform(0.8, 0.97), 3), 5)
            out = self.repository.update_plate(vid, result, crop)
            self.publisher.publish("violation_updated", out.model_dump(mode="json"))


def _label(image: np.ndarray, text: str) -> None:
    h = image.shape[0]
    scale = max(0.5, h / 400)
    cv2.putText(
        image, text, (8, int(30 * scale)), cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 255), 2, cv2.LINE_AA
    )


def _render_plate(text: str | None) -> np.ndarray:
    img = np.full((80, 300, 3), 255, dtype=np.uint8)
    cv2.rectangle(img, (2, 2), (297, 77), (0, 0, 0), 3)
    shown = text or "KA??X?12?"
    cv2.putText(img, shown, (14, 55), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 3, cv2.LINE_AA)
    if text is None:
        img = cv2.GaussianBlur(img, (21, 21), 0)
    cv2.putText(img, "MOCK", (232, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1, cv2.LINE_AA)
    return img
