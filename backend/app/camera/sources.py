"""Synthetic and wall-clock-paced OpenCV frame sources."""

from __future__ import annotations

import time
from pathlib import Path

import cv2
import numpy as np

from app.core.types import CameraConfig


class SourceError(RuntimeError):
    """A source could not be opened or recovered after decoding failures."""


class SyntheticSource:
    """Generate 1280x720 labelled test frames for mock mode.

    Thread-safety: instances are owned by a single camera thread.
    """

    width, height = 1280, 720

    def __init__(self, config: CameraConfig) -> None:
        """Create a source for ``config`` without performing I/O."""
        self.config, self.fps, self.loop_index, self._n = config, config.target_fps or 25.0, 0, 0
        self._tint = (sum(ord(char) for char in config.camera_id) * 37) % 60

    def open(self) -> bool:
        """Return true because a synthetic source needs no external resource."""
        return True

    def read(self) -> tuple[bool, np.ndarray | None, float]:
        """Return the next BGR frame and synthetic source position in milliseconds."""
        image = np.full((self.height, self.width, 3), 40, dtype=np.uint8)
        image[:, :, 0] = 50 + self._tint
        cv2.rectangle(image, (0, int(self.height * 0.55)), (self.width, self.height), (70, 70, 70), -1)
        elapsed = self._n / self.fps
        x = int((elapsed * 160) % (self.width + 200)) - 200
        cv2.rectangle(
            image, (x, int(self.height * 0.45)), (x + 200, int(self.height * 0.75)), (0, 180, 255), -1
        )
        cv2.putText(
            image, f"{self.config.camera_id}  {self.config.name}", (30, 60), 0, 1.4, (255, 255, 255), 3
        )
        cv2.putText(
            image, time.strftime("%H:%M:%S") + f"  frame {self._n}", (30, 115), 0, 1.0, (220, 220, 220), 2
        )
        cv2.putText(image, "SYNTHETIC", (self.width - 300, 60), 0, 1.2, (0, 0, 255), 3)
        self._n += 1
        return True, image, elapsed * 1000.0

    def close(self) -> None:
        """Release no resource (synthetic frames require none)."""


class VideoFileSource:
    """Read a video at source speed while emitting at the configured target rate.

    Thread-safety: instances are owned by one camera thread.
    """

    def __init__(self, config: CameraConfig, repo_root: Path) -> None:
        """Prepare a source path relative to ``repo_root``."""
        self.config = config
        source = Path(config.source)
        self.path = source if source.is_absolute() else repo_root / source
        self.fps, self.width, self.height, self.frame_count, self.loop_index = 25.0, 0, 0, 0, 0
        self._cap: cv2.VideoCapture | None = None
        self._started = self._emitted = 0.0
        self._last_source_index, self._failures = -1, 0

    def open(self) -> bool:
        """Open the configured file and read its native metadata."""
        self.close()
        if not self.path.is_file():
            return False
        cap = cv2.VideoCapture(str(self.path))
        if not cap.isOpened():
            cap.release()
            return False
        self._cap = cap
        self.fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)
        self.width, self.height = (
            int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        )
        self.frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        self._started, self._emitted, self._last_source_index, self._failures = time.monotonic(), 0, -1, 0
        return True

    def _rewind(self) -> bool:
        assert self._cap is not None
        if not self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0):
            return self.open()
        self.loop_index += 1
        self._started, self._emitted, self._last_source_index = time.monotonic(), 0, -1
        return True

    def read(self) -> tuple[bool, np.ndarray | None, float]:
        """Return a paced frame, skipping stale source frames with ``grab``.

        Raises:
            SourceError: If the source cannot be recovered after three failures.
        """
        if self._cap is None:
            raise SourceError("source is not open")
        emit_fps = self.config.target_fps or self.fps
        # WHY: monotonic deadlines retain true video speed when JPEG or clients are slow.
        delay = self._started + self._emitted / emit_fps - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        desired = int((time.monotonic() - self._started) * self.fps)
        if self.frame_count and desired >= self.frame_count:
            if not self.config.loop:
                return False, None, self.frame_count / self.fps * 1000.0
            if not self._rewind():
                raise SourceError(f"could not rewind {self.path}")
            desired = 0
        while self._last_source_index + 1 < desired:
            if not self._cap.grab():
                return False, None, 0.0
            self._last_source_index += 1
        ok, frame = self._cap.read()
        self._last_source_index += 1
        if not ok or frame is None:
            self._failures += 1
            if self._failures == 1 and self.open():
                return self.read()
            if self._failures >= 3:
                raise SourceError(f"decode failed repeatedly: {self.path}")
            return False, None, 0.0
        self._failures = 0
        self._emitted += 1
        position = float(self._cap.get(cv2.CAP_PROP_POS_MSEC) or self._last_source_index / self.fps * 1000.0)
        return True, frame, position

    def close(self) -> None:
        """Release the OpenCV capture if it is open."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
