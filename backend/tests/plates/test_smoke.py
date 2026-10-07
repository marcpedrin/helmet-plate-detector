"""Plate smoke tests (no models needed). Model tests go behind ``@pytest.mark.model``."""

from __future__ import annotations

import importlib.util

import numpy as np
import pytest

from app.core.types import ModelState, PlateObservation, PlateStatus, Rider, Track
from app.plates import load_plate_service
from app.plates.mock import MockPlateService

MOTO = Track(1, (100, 200, 200, 400), 0.9, "motorcycle")
RIDER = Rider(1, MOTO, (), (100, 200, 200, 400))
FRAME = np.zeros((720, 1280, 3), dtype=np.uint8)


@pytest.mark.skipif(importlib.util.find_spec("open_image_models") is not None, reason="ML packages installed")
def test_factory_without_models_returns_not_loaded(settings):
    svc = load_plate_service(settings)  # must not raise
    assert svc.detector_state == ModelState.NOT_LOADED
    assert svc.ocr_state == ModelState.NOT_LOADED
    assert svc.observe(FRAME, RIDER).detection is None


def test_mock_service_and_voter():
    svc = MockPlateService()
    obs = svc.observe(FRAME, RIDER)
    assert obs == PlateObservation(None, None, None)
    voter = svc.new_voter()
    assert voter.result().status == PlateStatus.PENDING
    voter.add(obs)
    assert voter.result().status == PlateStatus.NOT_DETECTED
    assert voter.best_crop() is None and voter.ocr_count == 0


@pytest.mark.model
def test_real_plate_service_loads(settings):
    if importlib.util.find_spec("open_image_models") is None:
        pytest.skip("ML packages not installed")
    assert load_plate_service(settings).detector_state == ModelState.LOADED
