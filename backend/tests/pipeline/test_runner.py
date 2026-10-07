"""PipelineRunner end-to-end with real camera threads (synthetic source) and fakes for the models."""

from __future__ import annotations

import threading
import time

import pytest

from app.camera.manager import CameraManager
from app.config import Settings
from app.core.schemas import StatsOut
from app.core.types import CameraConfig, HelmetStatus, ModelState, Track
from app.helmet.mock import ScriptedHelmetClassifier
from app.pipeline.overlay import OverlayState
from app.pipeline.runner import PipelineRunner
from app.plates.mock import MockPlateService
from app.storage.evidence_store import EvidenceStore
from app.storage.repository import InMemoryRepository
from tests.conftest import wait_for


class FakeTracker:
    """Always sees one rider (bike + person) at a fixed place."""

    state = ModelState.LOADED
    device = "cpu"

    def update(self, packet):
        return [
            Track(1, (500, 400, 700, 650), 0.9, "motorcycle"),
            Track(2, (530, 180, 670, 560), 0.9, "person"),
        ]


class RecordingPublisher:
    def __init__(self):
        self.lock = threading.Lock()
        self.messages: list[tuple[str, dict]] = []

    def publish(self, type, data):
        with self.lock:
            self.messages.append((type, data))

    def types(self):
        with self.lock:
            return [t for t, _ in self.messages]


class FlakyHelmet:
    """Raises on every other call."""

    state = ModelState.LOADED

    def __init__(self):
        self.calls = 0

    def classify_batch(self, frame, riders):
        self.calls += 1
        if self.calls % 2:
            raise RuntimeError("injected helmet failure")
        return ScriptedHelmetClassifier([HelmetStatus.NO_HELMET]).classify_batch(frame, riders)


@pytest.fixture
def rig(tmp_path):
    settings = Settings(_env_file=None, PIPELINE_FPS=20, PLATE_WINDOW_S=0.5)
    cams = CameraManager([CameraConfig("CAM_T", "Test", "synthetic", target_fps=30)], repo_root=tmp_path)
    repo = InMemoryRepository(EvidenceStore(tmp_path / "evidence"))
    pub = RecordingPublisher()
    created = []
    yield settings, cams, repo, pub, created
    for r in created:
        r.stop()
    cams.stop()


def make_runner(rig, helmet):
    settings, cams, repo, pub, created = rig
    runner = PipelineRunner(
        settings,
        cams,
        helmet,
        MockPlateService(),
        repo,
        pub,
        lambda: StatsOut(
            total_violations=0,
            violations_by_camera={},
            plates_read=0,
            plates_unreadable=0,
            riders_in_view=0,
            cameras_online=1,
            cameras_total=1,
            uptime_s=0.0,
        ),
        OverlayState(),
        tracker_factory=lambda cid: FakeTracker(),
    )
    created.append(runner)
    cams.start()
    runner.start()
    return runner


def test_one_violation_created_and_updated(rig):
    _, _, repo, pub, _ = rig
    runner = make_runner(rig, ScriptedHelmetClassifier([HelmetStatus.NO_HELMET]))
    wait_for(lambda: "violation_updated" in pub.types(), timeout=10)
    time.sleep(1.0)  # keep running: the same rider must not produce a second violation
    assert pub.types().count("violation_created") == 1
    assert pub.types().count("violation_updated") == 1
    (v,) = repo.list().items
    assert v.plate_status == "NOT_DETECTED" and v.track_id == 1
    assert runner.metrics("CAM_T").riders_in_view == 1
    assert runner.detector_state == ModelState.LOADED
    drawn = runner.overlay.riders("CAM_T")
    assert drawn and drawn[0].violation


def test_helmet_exception_does_not_kill_thread(rig):
    _, _, _, pub, _ = rig
    helmet = FlakyHelmet()
    runner = make_runner(rig, helmet)
    wait_for(lambda: helmet.calls >= 12, timeout=10)
    first = runner.processed_frames("CAM_T")
    wait_for(lambda: runner.processed_frames("CAM_T") > first + 5, timeout=10)
    assert runner._ctx["CAM_T"].thread.is_alive()
    wait_for(lambda: "violation_created" in pub.types(), timeout=10)  # good frames still vote
