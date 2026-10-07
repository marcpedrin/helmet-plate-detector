"""Load ``config/cameras.yaml`` into ``CameraConfig`` objects.

Owner: Marc (camera stream). Minimal parse only; the camera stream adds validation
(unique ids, positive fps, readable sources) with clear error messages.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from app.core.types import CameraConfig


def load_cameras(path: Path) -> list[CameraConfig]:
    """Parse the cameras YAML file.

    Args:
        path: Absolute path to a YAML file with a top-level ``cameras:`` list.

    Returns:
        Enabled and disabled cameras, in file order.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
        KeyError: If a camera entry lacks ``camera_id``, ``name`` or ``source``.
    """
    with Path(path).open(encoding="utf-8") as fh:
        doc = yaml.safe_load(fh) or {}
    cameras: list[CameraConfig] = []
    for entry in doc.get("cameras", []):
        cameras.append(
            CameraConfig(
                camera_id=str(entry["camera_id"]),
                name=str(entry["name"]),
                source=str(entry["source"]),
                location=str(entry.get("location", "")),
                loop=bool(entry.get("loop", True)),
                enabled=bool(entry.get("enabled", True)),
                target_fps=float(entry.get("target_fps", 15.0)),
            )
        )
    return cameras
