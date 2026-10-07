"""Shared fixtures. Tests never need ML packages, weights or videos."""

from __future__ import annotations

import time
from collections.abc import Callable, Iterator

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.core.types import EvidenceBundle, PlateResult, PlateStatus, ViolationEvent
from app.main import create_app


@pytest.fixture
def settings(tmp_path) -> Settings:
    """Mock-mode settings writing evidence/db into a temp dir and ignoring any local .env."""
    return Settings(
        _env_file=None,
        app_mode="mock",
        evidence_dir=str(tmp_path / "evidence"),
        db_path=str(tmp_path / "violations.db"),
        log_level="WARNING",
    )


@pytest.fixture
def client(settings) -> Iterator[TestClient]:
    """Running app in mock mode with a fast mock runner (violation every ~0.3-0.6 s)."""
    app = create_app(settings, mock_interval_s=(0.3, 0.6), mock_plate_delay_s=0.3)
    with TestClient(app) as c:
        yield c


def wait_for(predicate: Callable[[], object], timeout: float = 8.0, interval: float = 0.1):
    """Poll ``predicate`` until it returns a truthy value or ``timeout`` elapses."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(interval)
    raise AssertionError("condition not met within timeout")


def make_event(
    violation_id: str = "v1", camera_id: str = "CAM_01", ts: float | None = None
) -> ViolationEvent:
    """Build a small valid ViolationEvent with synthetic images."""
    img = np.full((120, 160, 3), 128, dtype=np.uint8)
    return ViolationEvent(
        violation_id=violation_id,
        camera_id=camera_id,
        track_id=7,
        violation_type="NO_HELMET",
        helmet_confidence=0.8,
        rider_bbox=(10, 10, 60, 100),
        frame_index=42,
        video_pos_ms=1400.0,
        timestamp=ts if ts is not None else time.time(),
        evidence=EvidenceBundle(full_frame=img, rider_crop=img[10:100, 10:60].copy()),
        plate=PlateResult(PlateStatus.PENDING, None, 0.0, 0),
    )
