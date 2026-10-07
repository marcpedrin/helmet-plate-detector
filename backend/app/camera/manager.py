"""Camera manager: one reader thread per camera feeding a latest-frame buffer.

Owner: Marc (camera stream). Minimal working version: the camera stream adds real-time
pacing, reconnect/backoff and OFFLINE handling.
"""

from __future__ import annotations

import dataclasses
import logging
import threading
import time
from collections.abc import Callable
from pathlib import Path

import numpy as np

from app.camera.sources import SyntheticSource, VideoFileSource
from app.core.interfaces import OverlayFn
from app.core.types import CameraConfig, CameraRuntime, CameraState, FramePacket

log = logging.getLogger(__name__)


class _CameraWorker:
    """Reader thread + latest-frame buffer for one camera (internal)."""

    def __init__(self, config: CameraConfig, repo_root: Path, on_status: Callable[[CameraRuntime], None]):
        self.config = config
        self.repo_root = repo_root
        self.on_status = on_status
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.latest: FramePacket | None = None
        self.runtime = CameraRuntime(config.camera_id, CameraState.STOPPED, 0.0, 0, 0, 0, 0)
        self.thread: threading.Thread | None = None

    def _update(self, notify: bool, **changes) -> None:
        with self.lock:
            old = self.runtime
            new = dataclasses.replace(old, **changes)
            self.runtime = new
        if notify and (new.state != old.state or new.last_error != old.last_error):
            try:
                self.on_status(new)
            except Exception:  # a listener must never kill a camera thread
                log.exception("camera status listener failed")

    def start(self) -> None:
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run, name=f"camera-{self.config.camera_id}", daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join(timeout=2.0)
            self.thread = None
        self._update(True, state=CameraState.STOPPED)

    def _open_source(self) -> tuple[SyntheticSource | VideoFileSource, str | None]:
        cfg = self.config
        if cfg.source.lower() == "synthetic":
            return SyntheticSource(cfg), None
        video = VideoFileSource(cfg, self.repo_root)
        if video.open():
            return video, None
        error = f"source not found or unreadable: {cfg.source}; using synthetic"
        log.warning("%s: %s", cfg.camera_id, error)
        return SyntheticSource(cfg), error

    def _run(self) -> None:
        cfg = self.config
        self._update(True, state=CameraState.STARTING, last_error=None)
        source, error = self._open_source()
        source.open()
        # WHY: minimal pacing at target_fps; the camera stream adds source-time pacing + frame skipping.
        period = 1.0 / max(cfg.target_fps, 1.0)
        frame_index = 0
        self._update(True, state=CameraState.ONLINE, source_fps=float(source.fps), last_error=error)
        try:
            while not self.stop_event.is_set():
                t0 = time.monotonic()
                ok, image, pos_ms = source.read()
                if not ok or image is None:
                    self._update(True, state=CameraState.OFFLINE, last_error="read failed / end of stream")
                    break
                image.setflags(write=False)
                packet = FramePacket(
                    cfg.camera_id, frame_index, source.loop_index, pos_ms, time.time(), image
                )
                with self.lock:
                    self.latest = packet
                self._update(
                    False,
                    frame_index=frame_index,
                    loop_index=source.loop_index,
                    width=image.shape[1],
                    height=image.shape[0],
                )
                frame_index += 1
                self.stop_event.wait(max(0.0, period - (time.monotonic() - t0)))
        finally:
            source.close()


class CameraManager:
    """Implements ``CameraManagerProtocol`` with one daemon thread per enabled camera.

    Thread-safety: all public methods are safe to call from any thread.
    """

    def __init__(self, configs: list[CameraConfig], repo_root: Path) -> None:
        """Create workers for every enabled camera in ``configs`` (threads start in ``start()``)."""
        self._configs = {c.camera_id: c for c in configs if c.enabled}
        self._listeners: list[Callable[[CameraRuntime], None]] = []
        self._overlay: OverlayFn | None = None
        self._workers = {cid: _CameraWorker(c, repo_root, self._emit) for cid, c in self._configs.items()}

    def _emit(self, runtime: CameraRuntime) -> None:
        for fn in list(self._listeners):
            fn(runtime)

    def start(self) -> None:
        """Start all camera threads."""
        for w in self._workers.values():
            w.start()

    def stop(self) -> None:
        """Stop all camera threads (idempotent)."""
        for w in self._workers.values():
            w.stop()

    def camera_ids(self) -> list[str]:
        """Return enabled camera ids in config order."""
        return list(self._configs)

    def get_config(self, camera_id: str) -> CameraConfig:
        """Return the config of ``camera_id`` (raises KeyError if unknown)."""
        return self._configs[camera_id]

    def get_runtime(self, camera_id: str) -> CameraRuntime:
        """Return the runtime snapshot of ``camera_id`` (raises KeyError if unknown)."""
        w = self._workers[camera_id]
        with w.lock:
            return w.runtime

    def latest_frame(self, camera_id: str) -> FramePacket | None:
        """Return the latest frame of ``camera_id`` or None (raises KeyError if unknown)."""
        w = self._workers[camera_id]
        with w.lock:
            return w.latest

    def set_overlay(self, fn: OverlayFn) -> None:
        """Register the overlay drawn by :meth:`rendered_frame`."""
        self._overlay = fn

    def add_status_listener(self, fn: Callable[[CameraRuntime], None]) -> None:
        """Register a callback for camera state changes."""
        self._listeners.append(fn)

    def rendered_frame(self, camera_id: str) -> np.ndarray | None:
        """Return a writable copy of the latest frame with the overlay applied, or None.

        Not part of the protocol; used by ``streaming`` for MJPEG and snapshots.
        Raises KeyError if ``camera_id`` is unknown.
        """
        packet = self.latest_frame(camera_id)
        if packet is None:
            return None
        image = packet.image.copy()
        overlay = self._overlay
        if overlay is not None:
            try:
                image = overlay(camera_id, image)
            except Exception:  # a broken overlay must not break the stream
                log.exception("overlay failed for %s", camera_id)
        return image
