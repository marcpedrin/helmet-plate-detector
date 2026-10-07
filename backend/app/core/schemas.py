# CONTRACT — owner: Marc. Change only via a contracts/* PR.
"""Pydantic v2 wire schemas for REST responses and WebSocket messages.

Mirrored field-for-field in ``frontend/src/types/contracts.ts``. Any change here must
land in the same ``contracts/*`` PR as the TypeScript mirror and ``docs/CONTRACTS.md``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.core.types import CameraState, HelmetStatus, ModelState, PlateStatus


class EvidenceUrls(BaseModel):
    """URLs (served under ``/evidence``) of the evidence JPEGs for one violation."""

    full_frame_url: str
    rider_crop_url: str
    plate_crop_url: str | None = None


class ViolationOut(BaseModel):
    """One stored violation as returned by REST and ``violation_*`` WS messages."""

    id: str
    camera_id: str
    track_id: int
    violation: Literal["NO_HELMET"]
    plate: str | None = None
    plate_status: PlateStatus
    plate_confidence: float | None = None
    helmet_confidence: float
    timestamp: datetime  # UTC
    frame_index: int
    rider_bbox: list[int]
    evidence: EvidenceUrls


class ViolationPage(BaseModel):
    """A page of violations, newest first."""

    items: list[ViolationOut]
    total: int
    limit: int
    offset: int


class RepositoryCounts(BaseModel):
    """Aggregate counters computed by the repository."""

    total: int
    by_camera: dict[str, int]
    plates_read: int
    plates_unreadable: int


class CameraOut(BaseModel):
    """One camera with its runtime and pipeline metrics."""

    camera_id: str
    name: str
    location: str
    state: CameraState
    source_fps: float
    processing_fps: float
    frame_index: int
    riders_in_view: int
    stream_url: str
    snapshot_url: str
    last_error: str | None = None


class ModelsHealth(BaseModel):
    """Load state of each model family."""

    detector: ModelState
    helmet: ModelState
    plate_detector: ModelState
    ocr: ModelState


class HealthOut(BaseModel):
    """Response of ``GET /api/health``."""

    status: Literal["ok", "degraded"]
    mode: Literal["live", "mock"]
    models: ModelsHealth
    version: str


class StatsOut(BaseModel):
    """Response of ``GET /api/stats`` and payload of ``stats`` WS messages."""

    total_violations: int
    violations_by_camera: dict[str, int]
    plates_read: int
    plates_unreadable: int
    riders_in_view: int
    cameras_online: int
    cameras_total: int
    uptime_s: float


class TrackOverlay(BaseModel):
    """One tracked rider as drawn on the live stream overlay."""

    track_id: int
    bbox: list[int]
    helmet: HelmetStatus


class CameraMetricsMsg(BaseModel):
    """Payload of ``camera_metrics`` WS messages."""

    camera_id: str
    processing_fps: float
    riders_in_view: int
    tracks: list[TrackOverlay]


class WsEnvelope(BaseModel):
    """Envelope wrapping every message sent on ``/ws/events``."""

    type: Literal[
        "hello", "camera_status", "camera_metrics", "violation_created", "violation_updated", "stats"
    ]
    ts: datetime
    data: dict
