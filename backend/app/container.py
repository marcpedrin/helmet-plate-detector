"""Composition root: builds and wires every module. The ONLY file importing all modules.

Owner: Marc. Each owner's factory is already called here, so implementing the factory's
real path is all it takes to "plug in":

    settings
      -> camera.create_camera_manager      (camera stream)
      -> storage.create_repository         (camera/storage stream)
      -> realtime.hub.EventHub
      -> live: helmet.load_helmet_classifier (Prajwal), plates.load_plate_service (Malik),
               pipeline.runner.PipelineRunner (Marc)
         mock: pipeline.mock_runner.MockRunner
"""

from __future__ import annotations

import logging
import time
from typing import Protocol

from app import __version__
from app.camera import create_camera_manager
from app.config import Settings
from app.core.interfaces import HelmetClassifierProtocol, PlateServiceProtocol
from app.core.schemas import CameraOut, HealthOut, ModelsHealth, StatsOut
from app.core.types import CameraRuntime, CameraState, ModelState, PipelineMetrics
from app.helmet import load_helmet_classifier
from app.pipeline.mock_runner import MockRunner
from app.pipeline.runner import PipelineRunner
from app.plates import load_plate_service
from app.realtime.hub import EventHub
from app.storage import create_repository

log = logging.getLogger(__name__)


class RunnerProtocol(Protocol):
    """What the container needs from ``PipelineRunner`` and ``MockRunner``."""

    @property
    def detector_state(self) -> ModelState:
        """Load state of the object detector."""
        ...

    def start(self) -> None:
        """Start processing."""
        ...

    def stop(self) -> None:
        """Stop processing (idempotent)."""
        ...

    def metrics(self, camera_id: str) -> PipelineMetrics:
        """Latest metrics for one camera."""
        ...


class Container:
    """Holds every long-lived service for the app's lifetime.

    Thread-safety: built and started once from the lifespan; read-only afterwards.
    """

    def __init__(
        self,
        settings: Settings,
        *,
        mock_interval_s: tuple[float, float] = (8.0, 15.0),
        mock_plate_delay_s: float = 2.0,
    ) -> None:
        """Build all services (nothing starts until :meth:`start`).

        Args:
            settings: Application settings.
            mock_interval_s: Mock mode only: min/max seconds between fake violations per camera.
            mock_plate_delay_s: Mock mode only: delay before the fake plate update.
        """
        self.settings = settings
        self.started_at = time.time()
        self.cameras = create_camera_manager(settings)
        self.repository = create_repository(settings)
        self.hub = EventHub()
        self.helmet: HelmetClassifierProtocol | None = None
        self.plates: PlateServiceProtocol | None = None
        self.runner: RunnerProtocol
        if settings.app_mode == "live":
            self.helmet = load_helmet_classifier(settings)
            self.plates = load_plate_service(settings)
            self.runner = PipelineRunner(
                settings, self.cameras, self.helmet, self.plates, self.repository, self.hub, self.stats
            )
        else:
            self.runner = MockRunner(
                self.cameras,
                self.repository,
                self.hub,
                self.stats,
                interval_s=mock_interval_s,
                plate_delay_s=mock_plate_delay_s,
            )
        self.cameras.add_status_listener(self._on_camera_status)

    # ------------------------------------------------------------------ lifecycle
    def start(self) -> None:
        """Start cameras, then the runner."""
        log.info("Starting in %s mode with cameras %s", self.settings.app_mode, self.cameras.camera_ids())
        self.cameras.start()
        self.runner.start()

    def stop(self) -> None:
        """Stop the runner, then cameras (idempotent)."""
        self.runner.stop()
        self.cameras.stop()

    # ------------------------------------------------------------------ queries
    def models_health(self) -> ModelsHealth:
        """Return the load state of every model family."""
        if self.settings.app_mode == "mock":
            return ModelsHealth(
                detector=ModelState.MOCK,
                helmet=ModelState.MOCK,
                plate_detector=ModelState.MOCK,
                ocr=ModelState.MOCK,
            )
        assert self.helmet is not None and self.plates is not None
        return ModelsHealth(
            detector=self.runner.detector_state,
            helmet=self.helmet.state,
            plate_detector=self.plates.detector_state,
            ocr=self.plates.ocr_state,
        )

    def health(self) -> HealthOut:
        """Return overall health.

        ``degraded`` when any camera is OFFLINE, or in live mode when any model is not LOADED.
        """
        models = self.models_health()
        offline = any(
            self.cameras.get_runtime(c).state == CameraState.OFFLINE for c in self.cameras.camera_ids()
        )
        not_loaded = self.settings.app_mode == "live" and any(
            s != ModelState.LOADED for s in models.model_dump().values()
        )
        return HealthOut(
            status="degraded" if offline or not_loaded else "ok",
            mode=self.settings.app_mode,
            models=models,
            version=__version__,
        )

    def pipeline_metrics(self, camera_id: str) -> PipelineMetrics:
        """Return the runner's latest metrics for one camera."""
        return self.runner.metrics(camera_id)

    def camera_out(self, camera_id: str) -> CameraOut:
        """Return the wire representation of one camera (raises KeyError if unknown)."""
        cfg = self.cameras.get_config(camera_id)
        rt = self.cameras.get_runtime(camera_id)
        m = self.pipeline_metrics(camera_id)
        return CameraOut(
            camera_id=camera_id,
            name=cfg.name,
            location=cfg.location,
            state=rt.state,
            source_fps=rt.source_fps,
            processing_fps=m.processing_fps,
            frame_index=rt.frame_index,
            riders_in_view=m.riders_in_view,
            stream_url=f"/api/cameras/{camera_id}/stream.mjpg",
            snapshot_url=f"/api/cameras/{camera_id}/snapshot.jpg",
            last_error=rt.last_error,
        )

    def stats(self) -> StatsOut:
        """Return dashboard statistics (also published as ``stats`` WS messages)."""
        counts = self.repository.counts()
        ids = self.cameras.camera_ids()
        return StatsOut(
            total_violations=counts.total,
            violations_by_camera={cid: counts.by_camera.get(cid, 0) for cid in ids},
            plates_read=counts.plates_read,
            plates_unreadable=counts.plates_unreadable,
            riders_in_view=sum(self.pipeline_metrics(c).riders_in_view for c in ids),
            cameras_online=sum(self.cameras.get_runtime(c).state == CameraState.ONLINE for c in ids),
            cameras_total=len(ids),
            uptime_s=round(time.time() - self.started_at, 1),
        )

    # ------------------------------------------------------------------ events
    def _on_camera_status(self, runtime: CameraRuntime) -> None:
        self.hub.publish("camera_status", self.camera_out(runtime.camera_id).model_dump(mode="json"))
