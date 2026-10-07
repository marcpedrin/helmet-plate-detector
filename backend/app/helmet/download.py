"""Download helmet weights from Hugging Face.

Owner: Prajwal. See ``docs/MODELS.md`` / ``docs/modules/helmet.md`` for the source repo
(``nnsohamnn/helmet-detection-yolo11``, file ``yolov11s(80 epochs).pt``, saved as
``backend/models/helmet/helmet_yolo11s.pt``; fallback ``iam-tsr/yolov8n-helmet-detection``).
Import ``huggingface_hub`` inside the function, never at module level.
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path


def _sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def download(dest_dir: Path) -> Path:
    """Download the helmet weights into ``dest_dir`` if missing.

    Args:
        dest_dir: Target directory (normally ``backend/models/helmet``).

    Returns:
        Path to the weights file (``dest_dir / "helmet_yolo11s.pt"``).

    Raises:
        RuntimeError: If the download fails.
    """
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    attempts = [
        (
            "nnsohamnn/helmet-detection-yolo11",
            "yolov11s(80 epochs).pt",
            dest_dir / "helmet_yolo11s.pt",
        ),
        (
            "iam-tsr/yolov8n-helmet-detection",
            "best.pt",
            dest_dir / "helmet_yolov8n.pt",
        ),
    ]

    from huggingface_hub import hf_hub_download

    last_error: Exception | None = None
    for repo_id, filename, target_path in attempts:
        if target_path.exists():
            print(f"Using existing weights at {target_path} sha256={_sha256_of(target_path)}")
            return target_path

        try:
            downloaded = hf_hub_download(repo_id=repo_id, filename=filename)
            source_path = Path(downloaded)
            if source_path != target_path:
                shutil.copy2(source_path, target_path)
            print(f"Downloaded {repo_id}:{filename} -> {target_path} sha256={_sha256_of(target_path)}")
            return target_path
        except Exception as exc:  # pragma: no cover - defensive fallback path
            last_error = exc
            continue

    raise RuntimeError(
        "Failed to download helmet model from Hugging Face: "
        + "; ".join(f"{repo}:{filename}" for repo, filename, _ in attempts)
    ) from last_error
