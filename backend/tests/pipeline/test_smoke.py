"""Pipeline smoke tests: geometry helpers, overlay, placeholders and the mock runner."""

from __future__ import annotations

import numpy as np
import pytest

from app.core import geometry
from app.core.types import HelmetStatus
from app.pipeline.overlay import OverlayRider, OverlayState


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


# --------------------------------------------------------------------------- overlay
def test_overlay_draws_boxes_and_hud():
    state = OverlayState({"CAM_01": "MG Road"})
    state.update(
        "CAM_01",
        [OverlayRider(1, (10, 20, 60, 90), HelmetStatus.NO_HELMET, 0.9, violation=True, plate="KA01AB1234")],
        5.0,
    )
    img = np.zeros((100, 120, 3), dtype=np.uint8)
    out = state.draw("CAM_01", img)
    assert out[20:90, 10].any()  # left edge of the box drawn
    assert state.track_overlays("CAM_01")[0].helmet == HelmetStatus.NO_HELMET


@pytest.mark.parametrize("shape", [(1, 1, 3), (7, 3000, 3), (50, 50), (2160, 3840, 3), (0, 0, 3)])
def test_overlay_never_raises_on_odd_images(shape):
    state = OverlayState()
    state.update("C", [OverlayRider(1, (-50, -50, 10**6, 10**6), HelmetStatus.UNKNOWN)], 1.0)
    img = np.zeros(shape, dtype=np.uint8)
    assert state.draw("C", img) is img
    assert OverlayState().draw("missing", np.zeros((10, 10, 3), np.uint8)).shape == (10, 10, 3)
