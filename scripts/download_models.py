"""Download / pre-fetch all model weights so the demo machine can run offline.

Usage (repo root, venv with requirements-ml.txt):  python scripts/download_models.py
Owner: Marc (orchestration); each owner implements their module's ``download()``.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.config import get_settings  # noqa: E402


def main() -> int:
    settings = get_settings()
    failures = 0

    from app.helmet.download import download as download_helmet  # noqa: E402
    from app.plates.download import download as download_plates  # noqa: E402

    for label, owner, fn, dest in (
        ("helmet", "Prajwal", download_helmet, REPO_ROOT / "backend" / "models" / "helmet"),
        ("plates", "Malik", download_plates, REPO_ROOT / "backend" / "models" / "plates"),
    ):
        try:
            path = fn(dest)
            print(f"[ok]      {label}: {path}")
        except NotImplementedError:
            print(f"[pending] {label}: download not implemented yet (pending: {owner})")
        except Exception as exc:  # report and continue with the other models
            failures += 1
            print(f"[error]   {label}: {exc}")

    if importlib.util.find_spec("ultralytics") is None:
        print(f"[skip]    detector: ultralytics not installed (pip install -r backend/requirements-ml.txt) "
              f"-> {settings.detector_weights} not fetched")
    else:
        try:
            from ultralytics import YOLO

            YOLO(settings.detector_weights)
            print(f"[ok]      detector: {settings.detector_weights}")
        except Exception as exc:
            failures += 1
            print(f"[error]   detector: {exc}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
