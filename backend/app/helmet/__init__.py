"""Helmet classification on rider crops (head detector: HELMET / NO_HELMET per head).

Owner: Prajwal (``feature/helmet-detection``).

Rules for this package (see CONTRIBUTING.md):
  * Never import torch, ultralytics, onnxruntime or other ML packages at module top
    level; import them inside loader functions/constructors.
  * :func:`load_helmet_classifier` never raises. On any failure it returns a fallback
    whose ``state`` is NOT_LOADED or ERROR and logs the reason.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.config import resolve
from app.core.interfaces import HelmetClassifierProtocol
from app.core.types import ModelState

if TYPE_CHECKING:
    from app.config import Settings

log = logging.getLogger(__name__)


def load_helmet_classifier(settings: Settings) -> HelmetClassifierProtocol:
    """Load the helmet classifier for live mode.

    Args:
        settings: Uses ``helmet_weights``, ``helmet_imgsz``, ``helmet_conf``, ``device``.

    Returns:
        ``YoloHelmetClassifier`` with ``state=LOADED`` on success; otherwise a
        ``MockHelmetClassifier`` (always UNKNOWN) with ``state=NOT_LOADED`` (weights
        missing / not implemented yet) or ``state=ERROR`` (load failed). Never raises.
    """
    from app.helmet.mock import MockHelmetClassifier

    weights = resolve(settings.helmet_weights)
    if not weights.is_file():
        log.warning("Helmet weights not found at %s; helmet status will be UNKNOWN", weights)
        return MockHelmetClassifier(state=ModelState.NOT_LOADED)
    try:
        from app.helmet.classifier import YoloHelmetClassifier

        return YoloHelmetClassifier(
            weights=weights, imgsz=settings.helmet_imgsz, conf=settings.helmet_conf, device=settings.device
        )
    except NotImplementedError:
        log.warning("YoloHelmetClassifier not implemented yet; helmet status will be UNKNOWN")
        return MockHelmetClassifier(state=ModelState.NOT_LOADED)
    except Exception:
        log.exception("Failed to load helmet classifier from %s", weights)
        return MockHelmetClassifier(state=ModelState.ERROR)
