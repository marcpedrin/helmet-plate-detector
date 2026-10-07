"""Pipeline smoke tests: geometry helpers, overlay, placeholders and the mock runner."""

from __future__ import annotations

import numpy as np
import pytest

from app.core import geometry
from app.core.schemas import TrackOverlay
from app.core.types import HelmetStatus, Track
from app.pipeline.association import associate_riders
from app.pipeline.overlay import OverlayState


# --------------------------------------------------------------------------- geometry
def test_area_and_center():
    assert geometry.area((0, 0, 10, 20)) == 200
    assert geometry.area((5, 5, 5, 10)) == 0
    assert geometry.area((10, 10, 0, 0)) == 0
    assert geometry.center((0, 0, 10, 20)) == (5.0, 10.0)


def test_iou():
    assert geometry.iou((0, 0, 10, 10), (0, 0, 10, 10)) == 1.0
    assert geometry.iou((0, 0, 10, 10), (20, 20, 30, 30)) == 0.0
    assert geometry.iou((0, 0, 10, 10), (5, 0, 15, 10)) == pytest.approx(50 / 150)
    assert geometry.iou((0, 0, 0, 0), (0, 0, 0, 0)) == 0.0


def test_ioa():
    assert geometry.ioa((2, 2, 4, 4), (0, 0, 10, 10)) == 1.0
    assert geometry.ioa((5, 0, 15, 10), (0, 0, 10, 10)) == 0.5
    assert geometry.ioa((0, 0, 0, 0), (0, 0, 10, 10)) == 0.0


def test_union():
    assert geometry.union((0, 0, 5, 5), (3, 4, 10, 8)) == (0, 0, 10, 8)
    assert geometry.union((1, 2, 3, 4)) == (1, 2, 3, 4)
    with pytest.raises(ValueError):
        geometry.union()


def test_clip_and_expand():
    assert geometry.clip((-5, -5, 50, 50), 40, 30) == (0, 0, 40, 30)
    assert geometry.expand((10, 10, 20, 20), 0.5, 1.0, 0.0, 100, 100) == (5, 0, 25, 20)
    assert geometry.expand((0, 0, 10, 10), 1.0, 1.0, 1.0, 15, 15) == (0, 0, 15, 15)


def test_crop_is_copy_and_empty_safe():
    img = np.arange(100 * 100 * 3, dtype=np.uint8).reshape(100, 100, 3)
    c = geometry.crop(img, (10, 10, 20, 30))
    assert c.shape == (20, 10, 3)
    c[:] = 0
    assert img[15, 15].any()  # original untouched
    assert geometry.crop(img, (200, 200, 300, 300)).size == 0
    assert geometry.crop(img, (50, 50, 50, 60)).shape[:2] == (0, 0)


# --------------------------------------------------------------------------- overlay / placeholders
def test_overlay_state_draws_boxes():
    state = OverlayState()
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    state.set("CAM_01", [TrackOverlay(track_id=1, bbox=[10, 10, 50, 50], helmet=HelmetStatus.NO_HELMET)])
    out = state("CAM_01", img)
    assert out.any()
    assert not state("CAM_02", np.zeros_like(img)).any()


def test_association_placeholder_returns_list():
    tracks = [Track(1, (0, 0, 10, 10), 0.9, "motorcycle")]
    assert associate_riders(tracks, 100, 100) == []
