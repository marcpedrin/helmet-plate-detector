"""Application settings, loaded from environment variables and the repo-root ``.env``.

Owner: Marc. Every key here has a matching line in ``.env.example``; add both together.
Paths in settings are repo-relative strings; call :func:`resolve` to make them absolute.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


def resolve(path: str | Path) -> Path:
    """Return ``path`` as an absolute path, interpreting relative paths against ``REPO_ROOT``."""
    p = Path(path)
    return p if p.is_absolute() else (REPO_ROOT / p).resolve()


class Settings(BaseSettings):
    """All runtime configuration. Field names map to upper-case env vars (``APP_MODE`` ...)."""

    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", env_file_encoding="utf-8", extra="ignore")

    # General
    app_mode: Literal["mock", "live"] = "mock"
    log_level: str = "INFO"
    cameras_config: str = "backend/config/cameras.yaml"
    evidence_dir: str = "evidence"
    db_path: str = "data/violations.db"
    evidence_retention_days: int = 7
    cors_origins: str = "http://localhost:5173"
    device: str = "auto"

    # Object detector + tracker
    detector_weights: str = "yolo26n.pt"
    detector_imgsz: int = 640
    detector_conf: float = 0.30
    pipeline_fps: float = 5
    min_rider_height_px: int = 80

    # Helmet
    helmet_weights: str = "backend/models/helmet/helmet_yolo11s.pt"
    helmet_imgsz: int = 320
    helmet_conf: float = 0.35

    # Plates + OCR
    plate_detector_model: str = "yolo-v9-t-384-license-plate-end2end"
    plate_detector_conf: float = 0.40
    plate_min_width_px: int = 50
    ocr_engine: str = "rapidocr"

    # Violation engine
    violation_window: int = 10
    violation_min_hits: int = 6
    violation_min_conf: float = 0.50
    violation_max_helmet_hits: int = 2
    plate_window_s: float = 3.0
    plate_max_ocr_per_track: int = 8
    dedup_iou: float = 0.3
    dedup_window_s: float = 5.0

    # Streaming
    stream_fps: float = 15
    stream_width: int = 960
    stream_jpeg_quality: int = 70

    @property
    def cors_origin_list(self) -> list[str]:
        """Return ``CORS_ORIGINS`` split on commas, blanks removed."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings singleton."""
    return Settings()
