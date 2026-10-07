# CONTRACT — owner: Marc. Change only via a contracts/* PR.
"""Core domain types shared by every backend module.

These dataclasses are the in-process contract between camera, pipeline, helmet,
plates, storage and realtime. Field names are frozen: renaming or removing a field
is a breaking change and must go through a ``contracts/*`` PR (see CONTRIBUTING.md).

All bounding boxes are ``BBox = (x1, y1, x2, y2)`` in original-frame pixel
coordinates (integers, x2/y2 exclusive-ish, never normalised).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

import numpy as np

BBox = tuple[int, int, int, int]  # (x1, y1, x2, y2) original-frame pixels


class CameraState(str, Enum):
    """Lifecycle state of one virtual camera."""

    STARTING = "STARTING"
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    STOPPED = "STOPPED"


class HelmetStatus(str, Enum):
    """Per-head (or per-rider) helmet classification."""

    HELMET = "HELMET"
    NO_HELMET = "NO_HELMET"
    UNKNOWN = "UNKNOWN"


class PlateStatus(str, Enum):
    """Outcome of number-plate reading for one violation."""

    PENDING = "PENDING"
    READ = "READ"
    UNREADABLE = "UNREADABLE"
    NOT_DETECTED = "NOT_DETECTED"


class ModelState(str, Enum):
    """Load state of an ML model, reported by ``/api/health``."""

    LOADED = "LOADED"
    MOCK = "MOCK"
    NOT_LOADED = "NOT_LOADED"
    ERROR = "ERROR"


@dataclass(frozen=True)
class CameraConfig:
    """Static configuration of one virtual camera (from ``config/cameras.yaml``)."""

    camera_id: str
    name: str
    source: str
    location: str = ""
    loop: bool = True
    enabled: bool = True
    target_fps: float = 15.0


@dataclass(frozen=True)
class CameraRuntime:
    """Live runtime snapshot of one camera, produced by the camera manager."""

    camera_id: str
    state: CameraState
    source_fps: float
    frame_index: int
    loop_index: int
    width: int
    height: int
    last_error: str | None = None


@dataclass(frozen=True)
class FramePacket:
    """One decoded frame plus its provenance.

    ``image`` is a BGR ``uint8`` array marked read-only; consumers must copy before
    drawing on it. ``frame_index`` is monotonically increasing across loops;
    ``loop_index`` counts how many times a looping video has restarted.
    """

    camera_id: str
    frame_index: int
    loop_index: int
    video_pos_ms: float
    timestamp: float
    image: np.ndarray  # BGR, read-only


@dataclass(frozen=True)
class Track:
    """One tracked object (ByteTrack id) in one frame."""

    track_id: int
    bbox: BBox
    confidence: float
    class_name: Literal["person", "motorcycle"]


@dataclass(frozen=True)
class Rider:
    """A motorcycle track associated with the person tracks riding it.

    ``rider_id`` equals the motorcycle's ``track_id``; ``bbox`` is the union of the
    motorcycle and person boxes.
    """

    rider_id: int
    motorcycle: Track
    persons: tuple[Track, ...]
    bbox: BBox


@dataclass(frozen=True)
class HeadDetection:
    """One head found by the helmet head-detector inside a rider crop (frame coords)."""

    bbox: BBox
    status: HelmetStatus
    confidence: float


@dataclass(frozen=True)
class HelmetResult:
    """Aggregated helmet verdict for one rider in one frame."""

    status: HelmetStatus
    confidence: float
    heads: tuple[HeadDetection, ...] = ()


@dataclass(frozen=True)
class PlateDetection:
    """One number-plate box (frame coords) found inside a motorcycle region."""

    bbox: BBox
    confidence: float


@dataclass(frozen=True)
class PlateRead:
    """One OCR read of a plate crop, after Indian-format correction."""

    raw_text: str
    text: str
    confidence: float
    valid_format: bool


@dataclass(frozen=True)
class PlateObservation:
    """Plate detection + OCR result for one rider in one frame (any part may be None)."""

    detection: PlateDetection | None
    read: PlateRead | None
    crop: np.ndarray | None


@dataclass(frozen=True)
class PlateResult:
    """Final (voted) plate outcome for one violation."""

    status: PlateStatus
    text: str | None
    confidence: float
    votes: int


@dataclass(frozen=True)
class PipelineMetrics:
    """Per-camera processing metrics exposed via REST and ``camera_metrics`` WS messages."""

    camera_id: str
    processing_fps: float = 0.0
    riders_in_view: int = 0
    active_tracks: int = 0


@dataclass
class EvidenceBundle:
    """Images saved as evidence for one violation (BGR arrays)."""

    full_frame: np.ndarray
    rider_crop: np.ndarray
    plate_crop: np.ndarray | None = None


@dataclass
class ViolationEvent:
    """A confirmed violation, handed by the pipeline to the repository."""

    violation_id: str
    camera_id: str
    track_id: int
    violation_type: Literal["NO_HELMET"]
    helmet_confidence: float
    rider_bbox: BBox
    frame_index: int
    video_pos_ms: float
    timestamp: float
    evidence: EvidenceBundle
    plate: PlateResult = field(default_factory=lambda: PlateResult(PlateStatus.PENDING, None, 0.0, 0))
