"""Validated loading of virtual-camera configuration."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from app.core.types import CameraConfig

_CAMERA_ID = re.compile(r"^CAM_\d{2}$")


def load_cameras(path: Path) -> list[CameraConfig]:
    """Load camera definitions from a YAML document.

    Args:
        path: YAML file with a top-level ``cameras`` list.

    Returns:
        Camera definitions in their configured order.

    Raises:
        ValueError: If YAML is malformed or an entry violates the camera contract.
    """
    try:
        with Path(path).open(encoding="utf-8") as handle:
            document: Any = yaml.safe_load(handle) or {}
    except yaml.YAMLError as error:
        raise ValueError(f"invalid camera YAML: {error}") from error
    if not isinstance(document, dict) or not isinstance(document.get("cameras"), list):
        raise ValueError("camera YAML must contain a 'cameras' list")
    cameras: list[CameraConfig] = []
    seen: set[str] = set()
    for index, entry in enumerate(document["cameras"]):
        if not isinstance(entry, dict):
            raise ValueError(f"camera entry {index} must be a mapping")
        try:
            camera_id, name, source = (str(entry[key]) for key in ("camera_id", "name", "source"))
        except KeyError as error:
            raise ValueError(f"camera entry {index} missing {error.args[0]}") from error
        if not _CAMERA_ID.fullmatch(camera_id):
            raise ValueError(f"invalid camera_id {camera_id!r}; expected CAM_00")
        if camera_id in seen:
            raise ValueError(f"duplicate camera_id {camera_id}")
        if not name.strip() or not source.strip():
            raise ValueError(f"camera {camera_id} needs non-empty name and source")
        try:
            target_fps = float(entry.get("target_fps", 15.0))
        except (TypeError, ValueError) as error:
            raise ValueError(f"camera {camera_id} has invalid target_fps") from error
        if not 0 <= target_fps <= 60:
            raise ValueError(f"camera {camera_id} target_fps must be in [0, 60]")
        seen.add(camera_id)
        cameras.append(
            CameraConfig(
                camera_id,
                name.strip(),
                source,
                str(entry.get("location", "")),
                bool(entry.get("loop", True)),
                bool(entry.get("enabled", True)),
                target_fps,
            )
        )
    return cameras
