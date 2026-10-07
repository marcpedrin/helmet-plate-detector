"""Frame sources: a synthetic test pattern and a looping video file.

Owner: Marc (camera stream). ``VideoFileSource`` is a minimal OpenCV loop; the camera
stream hardens it (real-time pacing / frame skipping, reopen on failure, error states).
"""

from __future__ import annotations

import time
from pathlib import Path

import cv2
import numpy as np

from app.core.types import CameraConfig


class SyntheticSource:
    """Generates 1280x720 test frames: camera name, wall clock and a moving rectangle.

    Used in mock mode and as the fallback whenever a video file is missing.
    Thread-safety: one instance per camera thread; not shared.
    """

    width = 1280
    height = 720

    def __init__(self, config: CameraConfig) -> None:
        """Create a synthetic source for ``config`` (no I/O)."""
        self.config = config
        self.fps = config.target_fps
        self.loop_index = 0
        self._n = 0
        self._tint = (sum(ord(c) for c in config.camera_id) * 37) % 60

    def open(self) -> bool:
        """Return True; a synthetic source cannot fail to open."""
        return True

    def read(self) -> tuple[bool, np.ndarray | None, float]:
        """Return ``(ok, bgr_frame, video_pos_ms)`` for the next synthetic frame."""
        w, h = self.width, self.height
        img = np.full((h, w, 3), 40, dtype=np.uint8)
        img[:, :, 0] = 50 + self._tint
        cv2.rectangle(img, (0, int(h * 0.55)), (w, h), (70, 70, 70), -1)  # "road"
        t = self._n / max(self.fps, 1.0)
        x = int((t * 160) % (w + 200)) - 200
        cv2.rectangle(img, (x, int(h * 0.45)), (x + 200, int(h * 0.75)), (0, 180, 255), -1)
        font = cv2.FONT_HERSHEY_SIMPLEX
        title = f"{self.config.camera_id}  {self.config.name}"
        cv2.putText(img, title, (30, 60), font, 1.4, (255, 255, 255), 3, cv2.LINE_AA)
        clock = time.strftime("%H:%M:%S") + f"  frame {self._n}"
        cv2.putText(img, clock, (30, 115), font, 1.0, (220, 220, 220), 2, cv2.LINE_AA)
        cv2.putText(img, "SYNTHETIC", (w - 300, 60), font, 1.2, (0, 0, 255), 3, cv2.LINE_AA)
        self._n += 1
        return True, img, t * 1000.0

    def close(self) -> None:
        """Release nothing (no resources held)."""


class VideoFileSource:
    """Reads a video file with OpenCV and loops it when ``config.loop`` is True.

    Thread-safety: one instance per camera thread; not shared.
    """

    def __init__(self, config: CameraConfig, repo_root: Path) -> None:
        """Prepare a source for ``config.source`` resolved against ``repo_root`` (no I/O yet)."""
        self.config = config
        src = Path(config.source)
        self.path = src if src.is_absolute() else repo_root / src
        self.fps = config.target_fps
        self.width = 0
        self.height = 0
        self.loop_index = 0
        self._cap: cv2.VideoCapture | None = None

    def open(self) -> bool:
        """Open the file; return False if it is missing or cannot be decoded."""
        if not self.path.is_file():
            return False
        cap = cv2.VideoCapture(str(self.path))
        if not cap.isOpened():
            return False
        self._cap = cap
        self.fps = cap.get(cv2.CAP_PROP_FPS) or self.config.target_fps
        self.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return True

    def read(self) -> tuple[bool, np.ndarray | None, float]:
        """Return ``(ok, bgr_frame, video_pos_ms)``; rewinds at end of file when looping."""
        if self._cap is None:
            return False, None, 0.0
        ok, frame = self._cap.read()
        if not ok and self.config.loop:
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.loop_index += 1
            ok, frame = self._cap.read()
        pos = float(self._cap.get(cv2.CAP_PROP_POS_MSEC) or 0.0)
        return ok, (frame if ok else None), pos

    def close(self) -> None:
        """Release the OpenCV capture."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
