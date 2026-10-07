"""Repository contract tests. Every ViolationRepositoryProtocol implementation must pass.

The camera/storage stream adds ``SqliteViolationRepository`` to ``REPOSITORIES``.
"""

from __future__ import annotations

import time

import numpy as np
import pytest

from app.core.types import PlateResult, PlateStatus
from app.storage.evidence_store import EvidenceStore
from app.storage.repository import InMemoryRepository
from tests.conftest import make_event

REPOSITORIES = [
    pytest.param(lambda store, tmp: InMemoryRepository(store), id="memory"),
    # pytest.param(lambda store, tmp: SqliteViolationRepository(tmp / "v.db", store), id="sqlite"),
]


@pytest.fixture(params=REPOSITORIES)
def repo(request, tmp_path):
    store = EvidenceStore(tmp_path / "evidence")
    return request.param(store, tmp_path)


def test_create_get_list(repo, tmp_path):
    out = repo.create(make_event("a", "CAM_01"))
    assert out.id == "a" and out.plate_status == PlateStatus.PENDING and out.plate_confidence is None
    assert (tmp_path / "evidence" / "CAM_01" / "a" / "full_frame.jpg").is_file()
    assert out.evidence.full_frame_url == "/evidence/CAM_01/a/full_frame.jpg"
    repo.create(make_event("b", "CAM_02", ts=time.time() + 1))
    page = repo.list()
    assert page.total == 2 and [v.id for v in page.items] == ["b", "a"]
    assert repo.list(camera_id="CAM_01").total == 1
    assert repo.list(limit=1, offset=1).items[0].id == "a"
    assert repo.get("a").id == "a"
    assert repo.get("zzz") is None


def test_update_plate_and_counts(repo):
    repo.create(make_event("a"))
    repo.create(make_event("b"))
    crop = np.full((40, 120, 3), 255, dtype=np.uint8)
    out = repo.update_plate("a", PlateResult(PlateStatus.READ, "KA01AB1234", 0.9, 4), crop)
    assert out.plate == "KA01AB1234" and out.plate_status == PlateStatus.READ
    assert out.evidence.plate_crop_url is not None
    repo.update_plate("b", PlateResult(PlateStatus.UNREADABLE, None, 0.2, 2), None)
    c = repo.counts()
    assert (c.total, c.plates_read, c.plates_unreadable) == (2, 1, 1)
    assert c.by_camera == {"CAM_01": 2}
    with pytest.raises(KeyError):
        repo.update_plate("missing", PlateResult(PlateStatus.READ, "X", 1.0, 1), None)


def test_purge_older_than(repo):
    repo.create(make_event("old", ts=time.time() - 10 * 86400))
    repo.create(make_event("new"))
    assert repo.purge_older_than(7) == 1
    assert repo.get("old") is None and repo.get("new") is not None
