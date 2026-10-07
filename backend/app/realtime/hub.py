"""Thread-safe event hub bridging pipeline threads to asyncio WebSocket clients.

Owner: Marc.

    pipeline / camera threads --publish()--> loop.call_soon_threadsafe --> per-client Queue
                                                                            |
                                                         /ws/events handler awaits queue.get()
"""

from __future__ import annotations

import asyncio
import logging
import threading
from datetime import UTC, datetime
from typing import Any

from app.core.schemas import WsEnvelope

log = logging.getLogger(__name__)


class EventHub:
    """Implements ``EventPublisherProtocol`` for the single ``/ws/events`` WebSocket.

    Every connected client gets its own bounded ``asyncio.Queue``. When a slow client's
    queue is full, the *oldest* message is dropped so live data stays fresh.

    Thread-safety: ``publish`` may be called from any thread (or the loop itself).
    ``connect``/``disconnect`` must be awaited on the event loop.
    """

    def __init__(self, queue_size: int = 100) -> None:
        """Create a hub with per-client queues of ``queue_size`` messages."""
        self.queue_size = queue_size
        self._loop: asyncio.AbstractEventLoop | None = None
        self._clients: dict[Any, asyncio.Queue[str]] = {}
        self._lock = threading.Lock()

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Bind the event loop that owns the client queues (called from the app lifespan)."""
        self._loop = loop

    @property
    def client_count(self) -> int:
        """Number of connected clients."""
        with self._lock:
            return len(self._clients)

    @staticmethod
    def encode(type: str, data: dict) -> str:
        """Serialise one message as a ``WsEnvelope`` JSON string (``ts`` = now, UTC)."""
        return WsEnvelope(type=type, ts=datetime.now(UTC), data=data).model_dump_json()  # type: ignore[arg-type]

    def publish(self, type: str, data: dict) -> None:
        """Queue a message for every connected client. Never blocks, never raises.

        Args:
            type: One of the ``WsEnvelope.type`` literals.
            data: JSON-serialisable payload (use ``model.model_dump(mode="json")``).
        """
        loop = self._loop
        if loop is None or loop.is_closed():
            return
        try:
            text = self.encode(type, data)
            loop.call_soon_threadsafe(self._fanout, text)
        except RuntimeError:
            pass  # loop shutting down
        except Exception:
            log.exception("failed to publish %s", type)

    def _fanout(self, text: str) -> None:
        with self._lock:
            queues = list(self._clients.values())
        for q in queues:
            if q.full():
                try:
                    q.get_nowait()  # drop oldest
                except asyncio.QueueEmpty:
                    pass
            q.put_nowait(text)

    async def connect(self, ws: Any) -> asyncio.Queue[str]:
        """Register ``ws`` and return its message queue (binds the loop if not yet bound)."""
        if self._loop is None:
            self._loop = asyncio.get_running_loop()
        q: asyncio.Queue[str] = asyncio.Queue(maxsize=self.queue_size)
        with self._lock:
            self._clients[ws] = q
        return q

    async def disconnect(self, ws: Any) -> None:
        """Unregister ``ws`` (no-op if unknown)."""
        with self._lock:
            self._clients.pop(ws, None)
