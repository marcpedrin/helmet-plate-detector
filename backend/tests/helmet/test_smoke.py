"""Helmet smoke tests (no weights needed). Model tests go behind ``@pytest.mark.model``."""

from __future__ import annotations

import numpy as np
import pytest

from app.config import resolve
from app.core.types import HelmetStatus, ModelState, Rider, Track
from app.helmet import load_helmet_classifier
from app.helmet.mock import MockHelmetClassifier, ScriptedHelmetClassifier

MOTO = Track(1, (100, 200, 200, 400), 0.9, "motorcycle")
RIDER = Rider(1, MOTO, (Track(2, (110, 100, 190, 350), 0.9, "person"),), (100, 100, 200, 400))
FRAME = np.zeros((720, 1280, 3), dtype=np.uint8)


def test_factory_missing_weights_returns_not_loaded(settings):
    settings.helmet_weights = "backend/models/helmet/definitely_missing.pt"
    clf = load_helmet_classifier(settings)  # must not raise
    assert clf.state == ModelState.NOT_LOADED
    assert clf.classify_batch(FRAME, [RIDER])[0].status == HelmetStatus.UNKNOWN


def test_mock_returns_unknown_per_rider():
    clf = MockHelmetClassifier()
    assert clf.state == ModelState.MOCK
    assert [r.status for r in clf.classify_batch(FRAME, [RIDER, RIDER])] == [HelmetStatus.UNKNOWN] * 2
    assert clf.classify_batch(FRAME, []) == []


def test_scripted_cycles():
    clf = ScriptedHelmetClassifier([HelmetStatus.NO_HELMET, HelmetStatus.HELMET])
    seq = [clf.classify_batch(FRAME, [RIDER])[0].status for _ in range(3)]
    assert seq == [HelmetStatus.NO_HELMET, HelmetStatus.HELMET, HelmetStatus.NO_HELMET]


@pytest.mark.model
def test_real_classifier_loads(settings):
    if not resolve(settings.helmet_weights).is_file():
        pytest.skip("helmet weights not downloaded")
    assert load_helmet_classifier(settings).state == ModelState.LOADED
