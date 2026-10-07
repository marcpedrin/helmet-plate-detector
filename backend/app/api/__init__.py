"""REST + WebSocket routers. Thin: all logic lives in the container's services.

Owner: Marc (``cameras.py``: camera stream).
"""

from __future__ import annotations

from starlette.requests import HTTPConnection

from app.container import Container


def get_container(conn: HTTPConnection) -> Container:
    """FastAPI dependency returning the app's ``Container`` (works for HTTP and WebSocket)."""
    return conn.app.state.container
