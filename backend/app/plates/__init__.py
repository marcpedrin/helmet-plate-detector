"""Number-plate detection, OCR, Indian-format correction and multi-frame voting.

Owner: Malik (``feature/plate-ocr``).

Rules for this package (see CONTRIBUTING.md):
  * Never import open_image_models, rapidocr, onnxruntime, torch or ultralytics at
    module top level; import them inside loader functions/constructors.
  * :func:`load_plate_service` never raises. On any failure it returns a fallback whose
    ``detector_state`` / ``ocr_state`` is NOT_LOADED or ERROR and logs the reason.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.core.interfaces import PlateServiceProtocol
from app.core.types import ModelState

if TYPE_CHECKING:
    from app.config import Settings

log = logging.getLogger(__name__)


def load_plate_service(settings: Settings) -> PlateServiceProtocol:
    """Load the plate detector + OCR for live mode.

    Args:
        settings: Uses ``plate_detector_model``, ``plate_detector_conf``,
            ``plate_min_width_px``, ``ocr_engine``, ``device``.

    Returns:
        ``PlateService`` on success; otherwise ``MockPlateService`` with state
        NOT_LOADED (not implemented / models unavailable) or ERROR. Never raises.
    """
    from app.plates.mock import MockPlateService

    try:
        from app.plates.service import PlateService

        return PlateService.from_settings(settings)
    except NotImplementedError:
        log.warning("PlateService not implemented yet; plates will be NOT_DETECTED")
        return MockPlateService(state=ModelState.NOT_LOADED)
    except Exception:
        log.exception("Failed to load plate service")
        return MockPlateService(state=ModelState.ERROR)
