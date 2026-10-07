"""Pre-fetch plate detector / OCR models.

Owner: Malik. open-image-models and RapidOCR auto-download on first use; this function
warms their caches so the demo machine works offline. Import those packages inside the
function, never at module level.
"""

from __future__ import annotations

from pathlib import Path


def download(dest_dir: Path) -> Path:
    """Download (or warm the cache of) the plate detector and OCR models.

    Args:
        dest_dir: Directory for any explicitly downloaded files (``backend/models/plates``).

    Returns:
        ``dest_dir`` (or the cache directory actually used).

    Raises:
        NotImplementedError: Until Malik implements it.
        RuntimeError: If a download fails.
    """
    raise NotImplementedError("Malik: implement plate model download")
