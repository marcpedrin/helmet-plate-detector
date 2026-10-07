"""Violation engine lifecycle (Prompt 2 §6.4). Pure logic: fake clock, fake voter, synthetic frames."""

from __future__ import annotations

import numpy as np
import pytest

from app.config import Settings
from app.core.types import (
    FramePacket,
    HelmetResult,
    HelmetStatus,
    PlateDetection,
    PlateObservation,
    PlateRead,
    PlateResult,
    PlateStatus,
    Rider,
    Track,
)
from app.pipeline.violation_engine import Confirm, Finalize, NeedPlate, TrackPhase, ViolationEngine

NH = HelmetResult(HelmetStatus.NO_HELMET, 0.9)
HE = HelmetResult(HelmetStatus.HELMET, 0.9)
UN = HelmetResult(HelmetStatus.UNKNOWN, 0.0)
FRAME = np.random.default_rng(0).integers(0, 255, (720, 1280, 3), dtype=np.uint8)
DT = 0.2  # 5 FPS


class FakeVoter:
    """Voter whose final result is set by the test."""

    def __init__(self, final: PlateResult | None = None):
        self.ocr_count = 0
        self.final = final
        self.added: list[PlateObservation] = []

    def add(self, obs):
        self.added.append(obs)
        if obs.read is not None:
            self.ocr_count += 1

    def result(self):
        if not self.added:
            return PlateResult(PlateStatus.PENDING, None, 0.0, 0)
        return self.final or PlateResult(PlateStatus.NOT_DETECTED, None, 0.0, 0)

    def best_crop(self):
        return (
            np.zeros((20, 60, 3), np.uint8) if self.final and self.final.status == PlateStatus.READ else None
        )


def rider(tid=1, box=(400, 200, 560, 600)):
    m = Track(tid, (box[0], box[1] + 200, box[2], box[3]), 0.9, "motorcycle")
    p = Track(100 + tid, (box[0] + 20, box[1], box[2] - 20, box[3] - 100), 0.9, "person")
    return Rider(tid, m, (p,), box)


class Harness:
    def __init__(self, voter_final: PlateResult | None = None, **overrides):
        self.settings = Settings(_env_file=None, **overrides)
        self.voters: list[FakeVoter] = []

        def factory():
            v = FakeVoter(voter_final)
            self.voters.append(v)
            return v

        self.engine = ViolationEngine(self.settings, "CAM_01", factory)
        self.now = 1000.0
        self.frame_index = 0
        self.loop_index = 0
        self.pos_ms = 0.0

    def step(self, riders, results, *, dt=DT):
        self.now += dt
        self.frame_index += 1
        self.pos_ms += dt * 1000
        packet = FramePacket("CAM_01", self.frame_index, self.loop_index, self.pos_ms, self.now, FRAME)
        return self.engine.update("CAM_01", packet, riders, results, self.now)

    def run(self, seq, r=None):
        r = r or rider()
        actions = []
        for res in seq:
            acts = self.step([r], [res])
            actions += acts
            for a in acts:  # emulate the runner feeding plate observations back
                if isinstance(a, NeedPlate):
                    self.engine.record_plate(a.rider.rider_id, PlateObservation(None, None, None))
        return actions


def confirms(actions):
    return [a for a in actions if isinstance(a, Confirm)]


def finalizes(actions):
    return [a for a in actions if isinstance(a, Finalize)]


def test_six_no_helmet_in_ten_confirms_exactly_once():
    h = Harness()
    acts = h.run([NH, UN, NH, NH, UN, NH, NH, UN, NH])
    (c,) = confirms(acts)
    ev = c.event
    assert ev.camera_id == "CAM_01" and ev.track_id == 1 and ev.violation_type == "NO_HELMET"
    assert ev.helmet_confidence == pytest.approx(0.9)
    assert ev.evidence.full_frame.shape == FRAME.shape and ev.evidence.rider_crop.size > 0
    assert h.engine.phase(1) == TrackPhase.CONFIRMED


def test_suspected_after_three_hits_and_plate_collection_starts():
    h = Harness()
    acts = h.run([NH, NH])
    assert not [a for a in acts if isinstance(a, NeedPlate)]
    acts = h.run([NH])
    assert h.engine.phase(1) == TrackPhase.SUSPECTED
    assert [a for a in acts if isinstance(a, NeedPlate)][0].run_ocr is True


def test_five_hits_do_not_confirm():
    h = Harness()
    assert confirms(h.run([NH] * 5 + [UN] * 5)) == []


def test_three_helmet_looks_block_confirmation():
    h = Harness()
    assert confirms(h.run([NH, NH, HE, NH, HE, NH, HE, NH, NH, NH])) == []


def test_low_mean_confidence_blocks_confirmation():
    h = Harness()
    weak = HelmetResult(HelmetStatus.NO_HELMET, 0.3)
    assert confirms(h.run([weak] * 10)) == []


def test_same_track_never_confirms_twice():
    h = Harness(PLATE_WINDOW_S=0.5)
    acts = h.run([NH] * 40)
    assert len(confirms(acts)) == 1
    assert len(finalizes(acts)) == 1


def test_id_switch_is_suppressed():
    h = Harness()
    assert len(confirms(h.run([NH] * 6, rider(1, (400, 200, 560, 600))))) == 1
    h.now += 2.0  # track 1 lost, a new id appears 2 s later at IoU ~0.6
    acts = h.run([NH] * 10, rider(2, (440, 220, 600, 620)))
    assert confirms(acts) == []
    assert h.engine.phase(2) == TrackPhase.SUPPRESSED


def test_different_rider_elsewhere_is_not_suppressed():
    h = Harness()
    h.run([NH] * 6, rider(1, (100, 200, 260, 600)))
    assert len(confirms(h.run([NH] * 6, rider(2, (900, 200, 1060, 600))))) == 1


def test_video_loop_is_suppressed():
    h = Harness()
    assert len(confirms(h.run([NH] * 6, rider(1, (400, 200, 560, 600))))) == 1
    # video restarts: tracker ids reset, same rider at the same position in the file
    h.loop_index, h.pos_ms = 1, 0.0
    h.now += 30.0
    acts = h.run([NH] * 6, rider(1, (420, 210, 580, 610)))
    assert confirms(acts) == []


@pytest.mark.parametrize(
    "final",
    [
        PlateResult(PlateStatus.READ, "KA01AB1234", 0.93, 4),
        PlateResult(PlateStatus.UNREADABLE, None, 0.2, 3),
        None,  # voter saw nothing -> NOT_DETECTED
    ],
)
def test_finalize_after_plate_window(final):
    h = Harness(voter_final=final, PLATE_WINDOW_S=1.0)
    acts = h.run([NH] * 6)
    c = confirms(acts)[0]
    assert finalizes(acts) == []
    acts = h.run([NH] * 4)  # 0.8 s: still collecting
    assert finalizes(acts) == []
    (f,) = finalizes(h.run([NH] * 2))  # passes confirmed_at + 1.0 s
    assert f.violation_id == c.event.violation_id
    expected = final.status if final else PlateStatus.NOT_DETECTED
    assert f.plate.status == expected
    assert (f.plate_crop is not None) == (expected == PlateStatus.READ)
    assert h.engine.phase(1) == TrackPhase.FINALIZED


def test_lost_confirmed_track_finalizes_early():
    h = Harness(PLATE_WINDOW_S=10.0)
    h.run([NH] * 6)
    assert finalizes(h.step([], [], dt=0.5)) == []
    (f,) = finalizes(h.step([], [], dt=0.6))  # lost 1.1 s > 1 s
    assert f.plate.status == PlateStatus.NOT_DETECTED


def test_unconfirmed_lost_track_is_dropped():
    h = Harness()
    h.run([NH, NH, NH])
    h.step([], [], dt=1.5)
    assert h.engine.phase(1) == TrackPhase.SUSPECTED
    h.step([], [], dt=1.0)  # lost 2.5 s
    assert h.engine.phase(1) is None


def test_ocr_budget_switches_to_detection_only():
    h = Harness(PLATE_MAX_OCR_PER_TRACK=2, PLATE_WINDOW_S=100.0)
    r = rider()
    flags = []
    for _ in range(8):
        for a in h.step([r], [NH]):
            if isinstance(a, NeedPlate):
                flags.append(a.run_ocr)
                read = PlateRead("KA01AB1234", "KA01AB1234", 0.9, True)
                h.engine.record_plate(1, PlateObservation(PlateDetection((0, 0, 10, 5), 0.9), read, None))
    assert flags[:2] == [True, True] and set(flags[2:]) == {False}


def test_none_results_are_not_votes_but_keep_track_alive():
    h = Harness()
    acts = h.run([NH, NH, None, None, None, NH, NH, None, NH, NH])
    assert len(confirms(acts)) == 1
