"""Non-blocking cached JPEG encoding and multipart MJPEG generation."""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator
from typing import Any

import cv2
import numpy as np

from app.camera.manager import CameraManager
from app.core.types import CameraState

BOUNDARY = "frame"
_CACHE: dict[tuple[int, str], tuple[int, bytes]] = {}


def encode_jpeg(image: np.ndarray, width: int, quality: int) -> bytes:
    """Resize an image only when needed and return a JPEG.

    Args:
        image: BGR pixels.
        width: Maximum output width; never causes upscaling.
        quality: OpenCV JPEG quality.

    Returns:
        Encoded JPEG bytes.
    """
    height, source_width = image.shape[:2]
    if 0 < width < source_width:
        image = cv2.resize(image, (width, int(height * width / source_width)), interpolation=cv2.INTER_AREA)
    ok, data = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
    if not ok:
        raise ValueError("JPEG encoding failed")
    return data.tobytes()


def placeholder_frame(text: str) -> np.ndarray:
    """Create a dark offline/connecting JPEG source frame."""
    image = np.zeros((360, 640, 3), dtype=np.uint8)
    cv2.putText(image, text, (20, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (200, 200, 200), 2, cv2.LINE_AA)
    return image


async def mjpeg_generator(
    manager: CameraManager,
    camera_id: str,
    fps: float,
    width: int,
    quality: int,
    request: Any | None = None,
) -> AsyncIterator[bytes]:
    """Yield changed frames as multipart MJPEG without blocking the event loop.

    Args:
        manager: Camera manager supplying immutable packets.
        camera_id: Camera to stream.
        fps: Maximum client output rate.
        width: Stream JPEG width.
        quality: Stream JPEG quality.
        request: Optional Starlette request, used to detect disconnection.

    Yields:
        Complete ``--frame`` MIME parts.
    """
    period, previous, placeholder_at = 1.0 / max(fps, 1.0), -1, 0.0
    while True:
        if request is not None and await request.is_disconnected():
            return
        packet = manager.latest_frame(camera_id)
        if packet is None:
            now = time.monotonic()
            if now - placeholder_at >= 1.0:
                runtime, config = manager.get_runtime(camera_id), manager.get_config(camera_id)
                label = "CAMERA OFFLINE" if runtime.state == CameraState.OFFLINE else "CONNECTING…"
                jpg = await asyncio.to_thread(
                    encode_jpeg, placeholder_frame(f"{label}: {config.name}"), width, quality
                )
                placeholder_at = now
                yield _part(jpg)
            await asyncio.sleep(period)
            continue
        if packet.frame_index != previous:
            key = (id(manager), camera_id)
            cached = _CACHE.get(key)
            if cached is not None and cached[0] == packet.frame_index:
                jpg = cached[1]
            else:
                image = await asyncio.to_thread(manager.rendered_frame, camera_id)
                if image is None:
                    await asyncio.sleep(period)
                    continue
                jpg = await asyncio.to_thread(encode_jpeg, image, width, quality)
                _CACHE[key] = (packet.frame_index, jpg)
            previous = packet.frame_index
            yield _part(jpg)
        await asyncio.sleep(period)


def _part(jpeg: bytes) -> bytes:
    """Wrap JPEG payload in the exact multipart wire framing."""
    return (
        f"--{BOUNDARY}\r\nContent-Type: image/jpeg\r\nContent-Length: {len(jpeg)}\r\n\r\n".encode()
        + jpeg
        + b"\r\n"
    )
