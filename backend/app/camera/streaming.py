"""JPEG encoding and the async MJPEG generator used by ``api/cameras.py``.

Owner: Marc (camera stream).
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import cv2
import numpy as np

from app.camera.manager import CameraManager

BOUNDARY = "frame"


def encode_jpeg(image: np.ndarray, width: int, quality: int) -> bytes:
    """Resize ``image`` to ``width`` (keeping aspect, never upscaling) and JPEG-encode it.

    Args:
        image: BGR image.
        width: Target width in pixels; 0 or larger than the image keeps the original size.
        quality: JPEG quality 1-100.

    Returns:
        JPEG bytes.

    Raises:
        ValueError: If OpenCV fails to encode the image.
    """
    h, w = image.shape[:2]
    if 0 < width < w:
        image = cv2.resize(image, (width, int(h * width / w)), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
    if not ok:
        raise ValueError("JPEG encoding failed")
    return buf.tobytes()


def placeholder_frame(text: str) -> np.ndarray:
    """Return a dark 640x360 BGR image showing ``text`` (used before the first frame arrives)."""
    img = np.zeros((360, 640, 3), dtype=np.uint8)
    cv2.putText(img, text, (20, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (200, 200, 200), 2, cv2.LINE_AA)
    return img


async def mjpeg_generator(
    manager: CameraManager, camera_id: str, fps: float, width: int, quality: int
) -> AsyncIterator[bytes]:
    """Yield ``multipart/x-mixed-replace`` parts for one camera until the client disconnects.

    Each part is the latest frame with the overlay applied. Encoding runs in a worker
    thread so the event loop is never blocked; Starlette cancels the generator when the
    client goes away.

    Args:
        manager: Camera manager to pull frames from.
        camera_id: Camera to stream.
        fps: Maximum frames per second sent to the client.
        width: Output width (see :func:`encode_jpeg`).
        quality: JPEG quality.

    Yields:
        One multipart chunk (headers + JPEG + CRLF) per frame.
    """
    period = 1.0 / max(fps, 1.0)
    while True:
        image = manager.rendered_frame(camera_id)
        if image is None:
            image = placeholder_frame(f"{camera_id}: waiting for frames")
        jpg = await asyncio.to_thread(encode_jpeg, image, width, quality)
        header = f"--{BOUNDARY}\r\nContent-Type: image/jpeg\r\nContent-Length: {len(jpg)}\r\n\r\n"
        yield header.encode() + jpg + b"\r\n"
        await asyncio.sleep(period)
