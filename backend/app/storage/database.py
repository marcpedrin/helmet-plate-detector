"""SQLite connection management and schema.

Owner: Marc (camera/storage stream). Signatures are final; bodies are pending.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_VERSION = 1
"""Bump when ``SCHEMA_SQL`` changes; ``init_db`` migrates forward."""

SCHEMA_SQL = """
-- Proposed schema (camera/storage stream finalises it).
CREATE TABLE IF NOT EXISTS violations (
    id               TEXT PRIMARY KEY,
    camera_id        TEXT NOT NULL,
    track_id         INTEGER NOT NULL,
    violation        TEXT NOT NULL,
    helmet_conf      REAL NOT NULL,
    plate            TEXT,
    plate_status     TEXT NOT NULL,
    plate_conf       REAL,
    timestamp        REAL NOT NULL,
    frame_index      INTEGER NOT NULL,
    video_pos_ms     REAL NOT NULL,
    rider_bbox       TEXT NOT NULL,
    full_frame_path  TEXT NOT NULL,
    rider_crop_path  TEXT NOT NULL,
    plate_crop_path  TEXT
);
CREATE INDEX IF NOT EXISTS ix_violations_camera_ts ON violations(camera_id, timestamp DESC);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    """Open (creating parent dirs) a SQLite connection usable from multiple threads.

    Implementation notes: ``check_same_thread=False``, WAL journal mode,
    ``row_factory = sqlite3.Row``; callers serialise writes with a lock.

    Args:
        db_path: Absolute path of the database file.

    Returns:
        An open connection.

    Raises:
        sqlite3.Error: If the database cannot be opened.
    """
    raise NotImplementedError("camera/storage stream: implement SQLite connect()")


def init_db(conn: sqlite3.Connection) -> None:
    """Create tables and indexes if missing and migrate to ``SCHEMA_VERSION``.

    Args:
        conn: Open connection.

    Raises:
        sqlite3.Error: On migration failure.
    """
    raise NotImplementedError("camera/storage stream: implement init_db()")
