"""REST details: pagination/order, 404s, stats, live-mode health, SPA fallback."""

from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from app.core.schemas import HealthOut, StatsOut, ViolationPage
from app.core.types import ModelState, PlateResult, PlateStatus
from app.main import create_app
from tests.conftest import make_event


class LoadedTracker:
    state = ModelState.LOADED
    device = "cpu"

    def update(self, packet):
        return []


@pytest.fixture
def quiet_client(settings):
    """Mock mode with the mock runner effectively silent, so tests control the data."""
    app = create_app(settings, mock_interval_s=(1e6, 1e6))
    with TestClient(app) as c:
        yield c


def test_violations_pagination_newest_first(quiet_client):
    repo = quiet_client.app.state.container.repository
    t0 = time.time()
    for i in range(5):
        repo.create(make_event(f"v{i}", "CAM_01" if i % 2 else "CAM_02", ts=t0 + i))
    page = ViolationPage.model_validate(quiet_client.get("/api/violations?limit=2&offset=1").json())
    assert page.total == 5 and [v.id for v in page.items] == ["v3", "v2"]
    cam = ViolationPage.model_validate(quiet_client.get("/api/violations?camera_id=CAM_01").json())
    assert [v.id for v in cam.items] == ["v3", "v1"]
    assert quiet_client.get("/api/violations?limit=0").status_code == 422
    assert quiet_client.get("/api/violations/nope").status_code == 404


def test_stats_counts(quiet_client):
    repo = quiet_client.app.state.container.repository
    repo.create(make_event("a", "CAM_01"))
    repo.create(make_event("b", "CAM_03"))
    repo.update_plate("a", PlateResult(PlateStatus.READ, "KA01AB1234", 0.9, 3), None)
    s = StatsOut.model_validate(quiet_client.get("/api/stats").json())
    assert s.total_violations == 2 and s.plates_read == 1 and s.plates_unreadable == 0
    assert s.violations_by_camera == {"CAM_01": 1, "CAM_02": 0, "CAM_03": 1, "CAM_04": 0}


def test_live_health_degraded_when_models_not_loaded(settings):
    settings.app_mode = "live"
    app = create_app(settings, tracker_factory=lambda cid: LoadedTracker())
    with TestClient(app) as c:
        h = HealthOut.model_validate(c.get("/api/health").json())
    assert h.mode == "live" and h.status == "degraded"
    assert h.models.detector == ModelState.LOADED
    assert h.models.helmet == ModelState.NOT_LOADED and h.models.plate_detector == ModelState.NOT_LOADED


def test_spa_fallback_serves_index_for_deep_links(settings, tmp_path):
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<html>spa</html>")
    (dist / "assets" / "app.js").write_text("console.log(1)")
    app = create_app(settings, frontend_dist=dist, mock_interval_s=(1e6, 1e6))
    with TestClient(app) as c:
        assert c.get("/").text == "<html>spa</html>"
        assert c.get("/violations/abc").text == "<html>spa</html>"
        assert c.get("/assets/app.js").status_code == 200
        assert c.get("/assets/missing.js").status_code == 404
        assert c.get("/api/does-not-exist").status_code == 404
        assert c.get("/api/health").json()["mode"] == "mock"
