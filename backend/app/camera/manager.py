"""Threaded camera manager with retrying OFFLINE virtual cameras."""

from __future__ import annotations

import dataclasses
import logging
import threading
import time
from collections.abc import Callable
from pathlib import Path

import numpy as np

from app.camera.sources import SourceError, SyntheticSource, VideoFileSource
from app.core.interfaces import OverlayFn
from app.core.types import CameraConfig, CameraRuntime, CameraState, FramePacket

log = logging.getLogger(__name__)


class _CameraWorker:
    """Own one source, daemon thread, and lock-protected latest packet."""

    def __init__(
        self, config: CameraConfig, repo_root: Path, app_mode: str, notify: Callable[[CameraRuntime], None]
    ) -> None:
        self.config, self.repo_root, self.app_mode, self.notify = config, repo_root, app_mode, notify
        self.lock, self.stop_event = threading.Lock(), threading.Event()
        self.latest: FramePacket | None = None
        self.runtime = CameraRuntime(config.camera_id, CameraState.STOPPED, 0.0, 0, 0, 0, 0)
        self.thread: threading.Thread | None = None
        self._frame_index, self._last_emit, self._ema_fps = 0, None, 0.0

    def _update(self, **changes: object) -> None:
        with self.lock:
            old = self.runtime
            self.runtime = dataclasses.replace(old, **changes)
            new = self.runtime
        if new.state != old.state or new.last_error != old.last_error:
            try:
                self.notify(new)
            except Exception:
                log.exception("camera status listener failed")

    def start(self) -> None:
        """Start the worker once."""
        if self.thread is not None and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run, name=f"camera-{self.config.camera_id}", daemon=True)
        self.thread.start()

    def stop(self) -> None:
        """Request stop and join the worker for at most two seconds."""
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join(timeout=2.0)
            self.thread = None
        self._update(state=CameraState.STOPPED)

    def _source(self) -> SyntheticSource | VideoFileSource | None:
        if self.config.source.lower() == "synthetic":
            return SyntheticSource(self.config)
        source = VideoFileSource(self.config, self.repo_root)
        if source.open():
            return source
        if self.app_mode == "mock":
            return SyntheticSource(self.config)
        return None

    def _publish(self, source: SyntheticSource | VideoFileSource, image: np.ndarray, pos: float) -> None:
        image.setflags(write=False)
        now = time.monotonic()
        if self._last_emit is not None and now > self._last_emit:
            fps = 1.0 / (now - self._last_emit)
            # WHY: EMA hides transient decoder scheduling jitter in the dashboard metric.
            self._ema_fps = fps if not self._ema_fps else self._ema_fps * 0.8 + fps * 0.2
        self._last_emit = now
        packet = FramePacket(
            self.config.camera_id, self._frame_index, source.loop_index, pos, time.time(), image
        )
        with self.lock:
            self.latest = packet
        self._update(
            state=CameraState.ONLINE,
            source_fps=self._ema_fps or float(source.fps),
            frame_index=self._frame_index,
            loop_index=source.loop_index,
            width=image.shape[1],
            height=image.shape[0],
            last_error=(
                f"source not found or unreadable: {self.config.source}; using synthetic"
                if isinstance(source, SyntheticSource) and self.config.source.lower() != "synthetic"
                else None
            ),
        )
        self._frame_index += 1

    def _run(self) -> None:
        self._update(state=CameraState.STARTING, last_error=None)
        while not self.stop_event.is_set():
            source = self._source()
            if source is None:
                with self.lock:
                    self.latest = None
                self._update(
                    state=CameraState.OFFLINE,
                    last_error=f"source not found or unreadable: {self.config.source}",
                )
                # WHY: five seconds avoids a tight open loop but gives quick file restoration recovery.
                self.stop_event.wait(5.0)
                continue
            try:
                source.open()
                while not self.stop_event.is_set():
                    ok, image, pos = source.read()
                    if not ok or image is None:
                        if not self.config.loop and not isinstance(source, SyntheticSource):
                            self._update(state=CameraState.STOPPED, last_error=None)
                            return
                        raise SourceError("read failed")
                    self._publish(source, image, pos)
            except SourceError as error:
                with self.lock:
                    self.latest = None
                self._update(state=CameraState.OFFLINE, last_error=str(error))
                self.stop_event.wait(5.0)
            finally:
                source.close()


class CameraManager:
    """Implement ``CameraManagerProtocol`` using one daemon thread per camera.

    Thread-safety: all public methods are safe from any thread.
    """

    def __init__(self, configs: list[CameraConfig], repo_root: Path, app_mode: str = "mock") -> None:
        """Create workers without starting them."""
        self._configs = {config.camera_id: config for config in configs if config.enabled}
        self._listeners: list[Callable[[CameraRuntime], None]] = []
        self._overlay: OverlayFn = lambda _camera_id, image: image
        self._workers = {
            camera_id: _CameraWorker(config, repo_root, app_mode, self._emit)
            for camera_id, config in self._configs.items()
        }

    def _emit(self, runtime: CameraRuntime) -> None:
        for listener in list(self._listeners):
            try:
                listener(runtime)
            except Exception:
                log.exception("camera status listener failed")

    def start(self) -> None:
        """Idempotently start every configured camera."""
        for worker in self._workers.values():
            worker.start()

    def stop(self) -> None:
        """Stop all workers, allowing at most two seconds for each join."""
        for worker in self._workers.values():
            worker.stop()

    def camera_ids(self) -> list[str]:
        """Return enabled camera IDs in configuration order."""
        return list(self._configs)

    def get_config(self, camera_id: str) -> CameraConfig:
        """Return a configured camera or raise ``KeyError``."""
        return self._configs[camera_id]

    def get_runtime(self, camera_id: str) -> CameraRuntime:
        """Return a consistent runtime snapshot."""
        worker = self._workers[camera_id]
        with worker.lock:
            return worker.runtime

    def latest_frame(self, camera_id: str) -> FramePacket | None:
        """Return the immutable latest frame packet, if available."""
        worker = self._workers[camera_id]
        with worker.lock:
            return worker.latest

    def set_overlay(self, fn: OverlayFn) -> None:
        """Set the overlay applied to stream and snapshot copies."""
        self._overlay = fn

    def add_status_listener(self, fn: Callable[[CameraRuntime], None]) -> None:
        """Register a non-blocking state-change listener."""
        self._listeners.append(fn)

    def rendered_frame(self, camera_id: str) -> np.ndarray | None:
        """Return an annotated writable copy of the latest frame or ``None``."""
        packet = self.latest_frame(camera_id)
        if packet is None:
            return None
        image = packet.image.copy()
        try:
            return self._overlay(camera_id, image)
        except Exception:
            log.exception("overlay failed for %s", camera_id)
            return image
