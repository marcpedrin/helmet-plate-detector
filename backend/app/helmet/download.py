"""Download helmet weights from Hugging Face.

Owner: Prajwal. See ``docs/MODELS.md`` / ``docs/modules/helmet.md`` for the source repo
(``nnsohamnn/helmet-detection-yolo11``, file ``yolov11s(80 epochs).pt``, saved as
``backend/models/helmet/helmet_yolo11s.pt``; fallback ``iam-tsr/yolov8n-helmet-detection``).
Import ``huggingface_hub`` inside the function, never at module level.
"""

from __future__ import annotations

from pathlib import Path


def download(dest_dir: Path) -> Path:
    """Download the helmet weights into ``dest_dir`` if missing.

    Args:
        dest_dir: Target directory (normally ``backend/models/helmet``).

    Returns:
        Path to the weights file (``dest_dir / "helmet_yolo11s.pt"``).

    Raises:
        NotImplementedError: Until Prajwal implements it.
        RuntimeError: If the download fails.
    """
    raise NotImplementedError("Prajwal: implement helmet weights download")
