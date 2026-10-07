# CONTRACT — owner: Marc. Change only via a contracts/* PR.
"""Protocols every module implements; ``container.py`` wires implementations to them.

Modules depend on these Protocols, never on each other's concrete classes. That is
what lets mock and real implementations be swapped without touching callers.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Protocol

import numpy as np

from app.core.schemas import RepositoryCounts, ViolationOut, ViolationPage
from app.core.types import (
    BBox,
    CameraConfig,
    CameraRuntime,
    FramePacket,
    HelmetResult,
    ModelState,
    PlateObservation,
    PlateResult,
    Rider,
    ViolationEvent,
)

OverlayFn = Callable[[str, np.ndarray], np.ndarray]
"""``(camera_id, bgr_image_copy) -> bgr_image`` drawn onto MJPEG frames."""


class CameraManagerProtocol(Protocol):
    """Owns the virtual cameras and their latest-frame buffers.

    Thread-safety: every method may be called from any thread.
    """

    def start(self) -> None:
        """Start one reader thread per enabled camera. Never raises on a bad source."""
        ...

    def stop(self) -> None:
        """Stop all reader threads and release sources. Idempotent."""
        ...

    def camera_ids(self) -> list[str]:
        """Return the ids of all configured (enabled) cameras, in config order."""
        ...

    def get_config(self, camera_id: str) -> CameraConfig:
        """Return the static config of a camera.

        Raises:
            KeyError: If ``camera_id`` is unknown.
        """
        ...

    def get_runtime(self, camera_id: str) -> CameraRuntime:
        """Return the current runtime snapshot of a camera.

        Raises:
            KeyError: If ``camera_id`` is unknown.
        """
        ...

    def latest_frame(self, camera_id: str) -> FramePacket | None:
        """Return the most recent frame, or None if no frame has been decoded yet."""
        ...

    def set_overlay(self, fn: OverlayFn) -> None:
        """Register the function used to draw overlays on streamed frames."""
        ...

    def add_status_listener(self, fn: Callable[[CameraRuntime], None]) -> None:
        """Register a callback invoked (from a camera thread) on every state change."""
        ...


class ViolationRepositoryProtocol(Protocol):
    """Persists violations and their evidence JPEGs.

    Thread-safety: every method may be called concurrently from pipeline threads and
    API handlers.
    """

    def create(self, event: ViolationEvent) -> ViolationOut:
        """Persist a new violation and its evidence images; return the stored record."""
        ...

    def update_plate(
        self, violation_id: str, plate: PlateResult, plate_crop: np.ndarray | None
    ) -> ViolationOut:
        """Set the final plate result (and optional crop) on an existing violation.

        Raises:
            KeyError: If ``violation_id`` is unknown.
        """
        ...

    def get(self, violation_id: str) -> ViolationOut | None:
        """Return one violation, or None if it does not exist."""
        ...

    def list(self, camera_id: str | None = None, limit: int = 50, offset: int = 0) -> ViolationPage:
        """Return violations newest-first, optionally filtered by camera."""
        ...

    def counts(self) -> RepositoryCounts:
        """Return aggregate counters over all stored violations."""
        ...

    def purge_older_than(self, days: int) -> int:
        """Delete violations (and evidence files) older than ``days``; return how many."""
        ...


class HelmetClassifierProtocol(Protocol):
    """Classifies helmet status for every rider in a frame.

    Thread-safety: called from a single pipeline thread per camera; implementations
    shared across cameras must be safe for concurrent calls.
    """

    state: ModelState

    def classify_batch(self, frame: np.ndarray, riders: Sequence[Rider]) -> list[HelmetResult]:
        """Return one ``HelmetResult`` per rider, in the same order. Never raises on bad crops."""
        ...


class PlateVoterProtocol(Protocol):
    """Accumulates plate observations for one violation and votes on the final text."""

    ocr_count: int

    def add(self, obs: PlateObservation) -> None:
        """Add one observation (detections without reads still count as evidence)."""
        ...

    def result(self) -> PlateResult:
        """Return the current voted result (PENDING until anything was observed)."""
        ...

    def best_crop(self) -> np.ndarray | None:
        """Return the crop that best supports the current result, if any."""
        ...


class PlateServiceProtocol(Protocol):
    """Detects and reads number plates inside a rider's motorcycle region."""

    detector_state: ModelState
    ocr_state: ModelState

    def observe(
        self, frame: np.ndarray, rider: Rider, run_ocr: bool = True, exclude: Sequence[BBox] = ()
    ) -> PlateObservation:
        """Detect (and optionally OCR) the plate of ``rider`` in ``frame``.

        Args:
            frame: Full BGR frame.
            rider: Rider whose motorcycle box bounds the search region.
            run_ocr: If False, only detection runs (cheap path between OCR budget slots).
            exclude: Plate boxes belonging to other riders, to avoid cross-assignment.

        Returns:
            A ``PlateObservation``; parts are None when nothing was found. Never raises.
        """
        ...

    def new_voter(self) -> PlateVoterProtocol:
        """Return a fresh voter for one violation."""
        ...


class EventPublisherProtocol(Protocol):
    """Publishes realtime events to WebSocket clients."""

    def publish(self, type: str, data: dict) -> None:
        """Publish one message. Callable from any thread; never blocks, never raises."""
        ...
