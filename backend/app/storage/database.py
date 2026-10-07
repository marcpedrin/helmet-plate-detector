"""SQLite connection management and idempotent violation schema."""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS violations (
 id TEXT PRIMARY KEY, camera_id TEXT NOT NULL, track_id INTEGER NOT NULL,
 violation TEXT NOT NULL, helmet_confidence REAL NOT NULL, plate TEXT,
 plate_status TEXT NOT NULL, plate_confidence REAL, plate_votes INTEGER NOT NULL DEFAULT 0,
 timestamp REAL NOT NULL, frame_index INTEGER NOT NULL, video_pos_ms REAL,
 rider_bbox TEXT NOT NULL, full_frame_path TEXT NOT NULL, rider_crop_path TEXT NOT NULL,
 plate_crop_path TEXT, created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_violations_cam_ts ON violations(camera_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_violations_ts ON violations(timestamp DESC);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    """Open a WAL SQLite connection suitable for externally serialized threads.

    Args:
        db_path: Database path, whose parents will be created.

    Returns:
        Connection with dictionary-like rows.
    """
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(Path(db_path), check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA synchronous=NORMAL")
    return connection


def init_db(conn: sqlite3.Connection) -> None:
    """Create the schema and indexes when they do not already exist."""
    conn.executescript(SCHEMA_SQL)
    conn.commit()


class Database:
    """A lock-serialized SQLite connection.

    Thread-safety: all methods serialize access, making ``check_same_thread=False`` safe.
    """

    def __init__(self, path: Path) -> None:
        """Open and initialize a database at ``path``."""
        self.lock = threading.Lock()
        self.conn = connect(path)
        init_db(self.conn)
