"""FastAPI entry point: ``uvicorn app.main:app`` (run from ``backend/``).

Owner: Marc.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response
from starlette.types import Scope

from app import __version__
from app.api import cameras, health, stats, violations, ws
from app.config import REPO_ROOT, Settings, resolve
from app.container import Container


class SPAStaticFiles(StaticFiles):
    """Static files with single-page-app fallback: unknown extension-less paths serve ``index.html``.

    Deep links such as ``/violations/abc`` are client-side routes; without the fallback a browser refresh
    would 404. Missing assets (paths with a file extension) and ``api/``, ``ws/``, ``evidence/`` still 404.
    """

    async def get_response(self, path: str, scope: Scope) -> Response:
        """Serve ``path``, falling back to ``index.html`` for client-side routes."""
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            norm = path.replace("\\", "/")  # Starlette passes OS-normalised paths (backslashes on Windows)
            last = norm.rsplit("/", 1)[-1]
            if exc.status_code != 404 or "." in last or norm.startswith(("api/", "ws/", "evidence/")):
                raise
            return await super().get_response("index.html", scope)


def create_app(
    settings: Settings | None = None, *, frontend_dist: Path | None = None, **container_kwargs: Any
) -> FastAPI:
    """Build the FastAPI app.

    Args:
        settings: Settings to use (default: from env / ``.env``).
        frontend_dist: Built frontend to serve at ``/`` (default ``frontend/dist`` if it exists).
        **container_kwargs: Extra keyword arguments for :class:`Container` (tests use
            them to speed up the mock runner).

    Returns:
        The configured app; services start in the lifespan.
    """
    settings = settings or Settings()
    logging.basicConfig(
        level=settings.log_level.upper(), format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        container = Container(settings, **container_kwargs)
        container.hub.bind_loop(asyncio.get_running_loop())
        app.state.container = container
        container.start()
        try:
            yield
        finally:
            container.stop()

    app = FastAPI(title="Helmet & Plate Detector", version=__version__, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        # WHY: the dashboard can be hosted on Vercel and talk to this backend on the same laptop.
        allow_origin_regex=r"https://[a-z0-9-]+\.vercel\.app",
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def private_network_access(request, call_next):
        """Allow Chrome Private Network Access from a public (Vercel) page to this local server."""
        response = await call_next(request)
        if request.headers.get("access-control-request-private-network") == "true":
            response.headers["Access-Control-Allow-Private-Network"] = "true"
        return response
    for module in (cameras, violations, stats, health, ws):
        app.include_router(module.router)

    evidence_dir = resolve(settings.evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/evidence", StaticFiles(directory=evidence_dir), name="evidence")

    dist = frontend_dist or REPO_ROOT / "frontend" / "dist"
    if dist.is_dir():  # production-style single-port serving; mounted last so API routes win
        app.mount("/", SPAStaticFiles(directory=dist, html=True), name="frontend")
    return app


app = create_app()
