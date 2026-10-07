"""Evidence scoring (Prompt 2 §6.5)."""

from __future__ import annotations

import cv2
import numpy as np

from app.core.types import FramePacket
from app.pipeline.evidence import build_evidence, evidence_score, offer

RNG = np.random.default_rng(1)
SHARP = RNG.integers(0, 255, (720, 1280, 3), dtype=np.uint8)
BLURRY = cv2.GaussianBlur(SHARP, (31, 31), 0)


def test_sharper_frame_wins():
    box = (400, 100, 560, 400)
    assert evidence_score(SHARP, box, 0.9) > evidence_score(BLURRY, box, 0.9)


def test_larger_rider_wins():
    assert evidence_score(SHARP, (400, 100, 560, 400), 0.9) > evidence_score(SHARP, (400, 100, 460, 200), 0.9)


def test_border_touching_frame_is_penalised():
    inside = evidence_score(SHARP, (400, 100, 560, 400), 0.9)
    touching = evidence_score(SHARP, (0, 100, 160, 400), 0.9)
    assert touching == inside * 0.5


def test_offer_keeps_best_and_copies_frame():
    p1 = FramePacket("C", 1, 0, 0.0, 1.0, BLURRY)
    p2 = FramePacket("C", 2, 0, 200.0, 1.2, SHARP)
    best = offer(None, p1, (400, 100, 560, 400), 0.9)
    best = offer(best, p2, (400, 100, 560, 400), 0.9)
    assert best.frame_index == 2
    assert best.frame is not SHARP and np.array_equal(best.frame, SHARP)
    worse = offer(best, p1, (400, 100, 560, 400), 0.9)
    assert worse is best


def test_build_evidence_annotates_copy():
    best = offer(None, FramePacket("C", 1, 0, 0.0, 1.0, SHARP), (400, 100, 560, 400), 0.93)
    bundle = build_evidence(best, 37)
    assert bundle.full_frame.shape == SHARP.shape and not np.array_equal(bundle.full_frame, SHARP)
    assert bundle.rider_crop.shape[0] > 300 and bundle.plate_crop is None
