"""API smoke tests against the running mock-mode app."""

from __future__ import annotations

import threading

from app.core.schemas import CameraOut, HealthOut, StatsOut, ViolationOut, ViolationPage, WsEnvelope
from tests.conftest import wait_for


def test_health_reports_mock_mode(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    health = HealthOut.model_validate(r.json())
    assert health.mode == "mock"
    assert health.status == "ok"
    assert set(health.models.model_dump().values()) == {"MOCK"}


def test_cameras_lists_four_valid_cameras(client):
    r = client.get("/api/cameras")
    assert r.status_code == 200
    cams = [CameraOut.model_validate(c) for c in r.json()]
    assert [c.camera_id for c in cams] == ["CAM_01", "CAM_02", "CAM_03", "CAM_04"]
    assert cams[0].stream_url == "/api/cameras/CAM_01/stream.mjpg"
    assert client.get("/api/cameras/CAM_02").status_code == 200
    assert client.get("/api/cameras/NOPE").status_code == 404


def test_snapshot_returns_jpeg(client):
    def fetch():
        r = client.get("/api/cameras/CAM_01/snapshot.jpg")
        return r if r.status_code == 200 else None

    r = wait_for(fetch)
    assert r.headers["content-type"] == "image/jpeg"
    assert r.content[:2] == b"\xff\xd8"  # JPEG SOI marker


def test_violations_schema_valid_after_mock_emits(client):
    page = wait_for(
        lambda: (p := ViolationPage.model_validate(client.get("/api/violations").json())).total and p
    )
    v = page.items[0]
    assert isinstance(v, ViolationOut)
    assert v.violation == "NO_HELMET"
    # evidence images are actually served
    assert client.get(v.evidence.full_frame_url).status_code == 200
    assert client.get(f"/api/violations/{v.id}").status_code == 200
    assert client.get("/api/violations/does-not-exist").status_code == 404
    # a plate update eventually arrives for some violation
    wait_for(
        lambda: any(
            i.plate_status != "PENDING"
            for i in ViolationPage.model_validate(client.get("/api/violations").json()).items
        )
    )


def test_stats_schema(client):
    stats = StatsOut.model_validate(client.get("/api/stats").json())
    assert stats.cameras_total == 4


def test_ws_sends_hello_then_camera_status(client):
    with client.websocket_connect("/ws/events") as ws:
        first = WsEnvelope.model_validate(ws.receive_json())
        assert first.type == "hello"
        assert first.data["mode"] == "mock"
        statuses = [WsEnvelope.model_validate(ws.receive_json()) for _ in range(4)]
        assert [s.type for s in statuses] == ["camera_status"] * 4
        assert {s.data["camera_id"] for s in statuses} == {"CAM_01", "CAM_02", "CAM_03", "CAM_04"}


def test_hub_publish_from_plain_thread_reaches_client(client):
    hub = client.app.state.container.hub
    with client.websocket_connect("/ws/events") as ws:
        for _ in range(5):  # hello + 4 camera_status
            ws.receive_json()
        t = threading.Thread(target=hub.publish, args=("stats", {"marker": "from-thread"}))
        t.start()
        t.join()
        for _ in range(200):
            msg = ws.receive_json()
            if msg["type"] == "stats" and msg["data"].get("marker") == "from-thread":
                break
        else:
            raise AssertionError("message published from a thread never arrived")


def test_ws_receives_violation_created(client):
    with client.websocket_connect("/ws/events") as ws:
        for _ in range(500):
            msg = ws.receive_json()
            if msg["type"] == "violation_created":
                ViolationOut.model_validate(msg["data"])
                break
        else:
            raise AssertionError("no violation_created received")
