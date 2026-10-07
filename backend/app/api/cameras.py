"""Camera endpoints: list, detail, MJPEG stream and JPEG snapshot.

Owner: Marc (camera stream hardens this: client limits, 503 states, caching headers).
"""

from __future__ import annotations

import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse

from app.api import get_container
from app.camera.streaming import BOUNDARY, encode_jpeg, mjpeg_generator
from app.container import Container
from app.core.schemas import CameraOut

router = APIRouter(prefix="/api/cameras", tags=["cameras"])

ContainerDep = Annotated[Container, Depends(get_container)]


def _require(container: Container, camera_id: str) -> None:
    if camera_id not in container.cameras.camera_ids():
        raise HTTPException(status_code=404, detail=f"unknown camera {camera_id}")


@router.get("", response_model=list[CameraOut])
def list_cameras(container: ContainerDep) -> list[CameraOut]:
    """Return every enabled camera with runtime state and metrics."""
    return [container.camera_out(cid) for cid in container.cameras.camera_ids()]


@router.get("/{camera_id}", response_model=CameraOut)
def get_camera(camera_id: str, container: ContainerDep) -> CameraOut:
    """Return one camera (404 if unknown)."""
    _require(container, camera_id)
    return container.camera_out(camera_id)


@router.get("/{camera_id}/stream.mjpg")
def stream(camera_id: str, container: ContainerDep) -> StreamingResponse:
    """Stream the camera as MJPEG (``multipart/x-mixed-replace``) with the overlay drawn."""
    _require(container, camera_id)
    s = container.settings
    gen = mjpeg_generator(container.cameras, camera_id, s.stream_fps, s.stream_width, s.stream_jpeg_quality)
    return StreamingResponse(
        gen,
        media_type=f"multipart/x-mixed-replace; boundary={BOUNDARY}",
        headers={"Cache-Control": "no-store"},
    )


@router.get("/{camera_id}/snapshot.jpg")
async def snapshot(camera_id: str, container: ContainerDep) -> Response:
    """Return the latest frame (with overlay) as one JPEG; 503 before the first frame."""
    _require(container, camera_id)
    image = container.cameras.rendered_frame(camera_id)  # type: ignore[attr-defined]
    if image is None:
        raise HTTPException(status_code=503, detail="no frame yet")
    s = container.settings
    jpg = await asyncio.to_thread(encode_jpeg, image, s.stream_width, s.stream_jpeg_quality)
    return Response(content=jpg, media_type="image/jpeg", headers={"Cache-Control": "no-store"})
