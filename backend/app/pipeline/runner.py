"""Live-mode pipeline runner: one processing thread per camera.

Owner: Marc. Signatures are final; the processing loop is pending. Until implemented,
``start`` only registers the overlay and logs that live detection is not available, so
live mode still serves raw camera feeds without crashing.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from typing import TYPE_CHECKING

from app.core.interfaces import (
    CameraManagerProtocol,
    EventPublisherProtocol,
    HelmetClassifierProtocol,
    PlateServiceProtocol,
    ViolationRepositoryProtocol,
)
from app.core.schemas import StatsOut
from app.core.types import ModelState, PipelineMetrics
from app.pipeline.detector import ObjectTracker
from app.pipeline.overlay import OverlayState

if TYPE_CHECKING:
    from app.config import Settings

log = logging.getLogger(__name__)


class PipelineRunner:
    """Runs detect -> track -> associate -> helmet -> engine -> evidence -> plate per camera.

    Per-camera loop (to implement), paced at ``PIPELINE_FPS``:

    1. ``packet = cameras.latest_frame(cid)``; skip if unchanged ``frame_index``.
    2. ``tracks = tracker.update(packet.image)``; ``riders = associate_riders(...)``.
    3. ``helmets = helmet.classify_batch(packet.image, riders)``.
    4. ``decisions = engine.update(packet, riders, helmets)``; feed ``EvidenceSelector``.
    5. For ``collect_plate`` riders: ``plates.observe(...)`` into that rider's voter,
       OCR at most ``PLATE_MAX_OCR_PER_TRACK`` times.
    6. On ``newly_confirmed``: ``repository.create(event)`` then publish
       ``violation_created``; when the voter is final (or ``PLATE_WINDOW_S`` elapsed):
       ``repository.update_plate(...)`` then publish ``violation_updated``.
    7. Update overlay + metrics; publish ``camera_metrics`` at ~2 Hz and ``stats`` every 5 s.

    Thread-safety: ``start``/``stop``/``metrics`` may be called from any thread.
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
    ) -> None:
        """Store collaborators; no threads start and no models load here."""
        self.settings = settings
        self.cameras = cameras
        self.helmet = helmet
        self.plates = plates
        self.repository = repository
        self.publisher = publisher
        self.stats_fn = stats_fn
        self.overlay = OverlayState()
        self._trackers: dict[str, ObjectTracker] = {}
        self._metrics: dict[str, PipelineMetrics] = {}
        self._lock = threading.Lock()

    @property
    def detector_state(self) -> ModelState:
        """Worst state across per-camera trackers (NOT_LOADED before ``start``)."""
        states = [t.state for t in self._trackers.values()]
        if not states:
            return ModelState.NOT_LOADED
        for bad in (ModelState.ERROR, ModelState.NOT_LOADED, ModelState.MOCK):
            if bad in states:
                return bad
        return ModelState.LOADED

    def start(self) -> None:
        """Create per-camera trackers, register the overlay and start processing threads."""
        self.cameras.set_overlay(self.overlay)
        for cid in self.cameras.camera_ids():
            self._trackers[cid] = ObjectTracker(self.settings, cid)
        # TODO(Marc): start one daemon processing thread per camera (see class docstring).
        log.warning("PipelineRunner processing loop not implemented yet: live mode streams raw feeds only")

    def stop(self) -> None:
        """Signal processing threads to stop and join them (idempotent)."""

    def metrics(self, camera_id: str) -> PipelineMetrics:
        """Return the latest metrics for ``camera_id`` (zeros before the first frame)."""
        with self._lock:
            return self._metrics.get(camera_id, PipelineMetrics(camera_id))
