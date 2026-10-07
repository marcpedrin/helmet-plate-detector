"""Pre-fetch plate detector / OCR models.

open-image-models and RapidOCR auto-download on first use; this warms their caches so the
demo machine works offline. ML packages are imported inside the function.
"""

from __future__ import annotations

from pathlib import Path


def download(dest_dir: Path) -> Path:
    """Download (or warm the cache of) the plate detector and OCR models.

    Args:
        dest_dir: Directory for any explicitly downloaded files (``backend/models/plates``).

    Returns:
        ``dest_dir``.

    Raises:
        RuntimeError: If a download fails.
    """
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    try:
        import numpy as np
        from open_image_models import create_detector
        from rapidocr import RapidOCR

        create_detector("yolo-v9-t-384-license-plate-end2end", providers=["CPUExecutionProvider"])
        RapidOCR()(np.full((48, 160, 3), 255, np.uint8))
    except Exception as exc:
        raise RuntimeError(f"plate model download failed: {exc}") from exc
    return dest_dir
