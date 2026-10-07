"""Camera smoke tests: config loading, synthetic source, manager fallback, JPEG encoding."""

from __future__ import annotations

from pathlib import Path

from app.camera.config_loader import load_cameras
from app.camera.manager import CameraManager
from app.camera.sources import SyntheticSource
from app.camera.streaming import encode_jpeg
from app.config import REPO_ROOT
from app.core.types import CameraConfig, CameraState
from tests.conftest import wait_for


def test_load_default_cameras_yaml():
    cams = load_cameras(REPO_ROOT / "backend" / "config" / "cameras.yaml")
    assert [c.camera_id for c in cams] == ["CAM_01", "CAM_02", "CAM_03", "CAM_04"]
    assert cams[0].name == "MG Road Junction"
    assert all(c.loop and c.target_fps == 15 for c in cams)


def test_synthetic_source_frame():
    src = SyntheticSource(CameraConfig("CAM_X", "Test", "synthetic"))
    ok, img, pos = src.read()
    assert ok and img.shape == (720, 1280, 3)
    assert pos == 0.0


def test_missing_video_falls_back_to_synthetic(tmp_path: Path):
    cfg = CameraConfig("CAM_X", "Test", "videos/does_not_exist.mp4", target_fps=30)
    mgr = CameraManager([cfg], repo_root=tmp_path)
    seen = []
    mgr.add_status_listener(seen.append)
    mgr.start()
    try:
        packet = wait_for(lambda: mgr.latest_frame("CAM_X"))
        assert packet.image.shape == (720, 1280, 3)
        assert not packet.image.flags.writeable
        rt = mgr.get_runtime("CAM_X")
        assert rt.state == CameraState.ONLINE
        assert rt.last_error and "synthetic" in rt.last_error
        assert mgr.rendered_frame("CAM_X").flags.writeable
    finally:
        mgr.stop()
    assert mgr.get_runtime("CAM_X").state == CameraState.STOPPED
    assert CameraState.ONLINE in {r.state for r in seen}


def test_encode_jpeg_resizes():
    src = SyntheticSource(CameraConfig("CAM_X", "Test", "synthetic"))
    _, img, _ = src.read()
    jpg = encode_jpeg(img, 640, 70)
    assert jpg[:2] == b"\xff\xd8"
