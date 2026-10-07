"""``GET /api/stats``. Owner: Marc."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api import get_container
from app.container import Container
from app.core.schemas import StatsOut

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/stats", response_model=StatsOut)
def stats(container: Annotated[Container, Depends(get_container)]) -> StatsOut:
    """Return dashboard counters (same payload as the ``stats`` WS message)."""
    return container.stats()
