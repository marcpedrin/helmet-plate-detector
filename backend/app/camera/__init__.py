"""Virtual cameras: config loading, frame sources, the camera manager and MJPEG streaming.

Owner: Marc (camera stream, built in a separate Codex session on ``feature/backend-camera``).
The boilerplate here works minimally; the camera stream hardens pacing, reopen and errors.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.config import REPO_ROOT, resolve
from app.core.interfaces import CameraManagerProtocol

if TYPE_CHECKING:
    from app.config import Settings

log = logging.getLogger(__name__)


def create_camera_manager(settings: Settings) -> CameraManagerProtocol:
    """Build the camera manager from ``settings.cameras_config``.

    Never raises: if the YAML is missing or invalid the manager starts with no cameras
    and the error is logged.

    Args:
        settings: Application settings.

    Returns:
        A ``CameraManager`` (not yet started).
    """
    from app.camera.config_loader import load_cameras
    from app.camera.manager import CameraManager

    try:
        configs = load_cameras(resolve(settings.cameras_config))
    except Exception:  # factories never raise
        log.exception("Failed to load camera config %s", settings.cameras_config)
        configs = []
    return CameraManager(configs, repo_root=REPO_ROOT, app_mode=settings.app_mode)
