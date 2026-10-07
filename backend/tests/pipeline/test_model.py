"""Real-model tests (``-m model``): need ultralytics + YOLO26n weights (auto-downloaded on first run)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import cv2
import pytest

from app.config import Settings
from app.core.types import FramePacket, ModelState
from app.pipeline.association import associate_riders
from app.pipeline.detector import ObjectTracker

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "pipeline" / "street.jpg"

pytestmark = [
    pytest.mark.model,
    pytest.mark.skipif(importlib.util.find_spec("ultralytics") is None, reason="ultralytics not installed"),
]


def test_yolo26n_tracks_people_on_street_frame():
    image = cv2.imread(str(FIXTURE))
    assert image is not None, f"missing fixture {FIXTURE}"
    tracker = ObjectTracker(Settings(_env_file=None), "TEST")
    assert tracker.state == ModelState.LOADED, tracker.error
    tracks = tracker.update(FramePacket("TEST", 0, 0, 0.0, 0.0, image))
    persons = [t for t in tracks if t.class_name == "person"]
    assert len(persons) >= 1
    assert all(isinstance(v, int) for t in tracks for v in t.bbox)
    # same frame again: ids persist within a loop
    again = tracker.update(FramePacket("TEST", 1, 0, 40.0, 0.04, image))
    assert {t.track_id for t in again} & {t.track_id for t in tracks}
    associate_riders(tracks, image.shape[1], image.shape[0])  # must not raise on real boxes
