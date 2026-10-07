"""``/ws/events``: the single realtime WebSocket. Owner: Marc.

On connect the server sends ``hello``, then one ``camera_status`` per camera, then
streams every hub message. Clients never need to send anything.
"""

from __future__ import annotations

import asyncio
import contextlib

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app import __version__
from app.api import get_container

router = APIRouter(tags=["realtime"])


@router.websocket("/ws/events")
async def events(ws: WebSocket) -> None:
    """Serve one WebSocket client until it disconnects."""
    container = get_container(ws)
    hub = container.hub
    await ws.accept()
    queue = await hub.connect(ws)
    try:
        ids = container.cameras.camera_ids()
        hello = {"mode": container.settings.app_mode, "version": __version__, "cameras": ids}
        await ws.send_text(hub.encode("hello", hello))
        for cid in ids:
            await ws.send_text(hub.encode("camera_status", container.camera_out(cid).model_dump(mode="json")))

        async def pump() -> None:
            while True:
                await ws.send_text(await queue.get())

        async def drain() -> None:
            while True:  # returns via WebSocketDisconnect when the client goes away
                await ws.receive_text()

        tasks = [asyncio.create_task(pump()), asyncio.create_task(drain())]
        _, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for t in pending:
            t.cancel()
            with contextlib.suppress(asyncio.CancelledError, WebSocketDisconnect):
                await t
    except WebSocketDisconnect:
        pass
    finally:
        await hub.disconnect(ws)
