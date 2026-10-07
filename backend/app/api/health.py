"""``GET /api/health``. Owner: Marc."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api import get_container
from app.container import Container
from app.core.schemas import HealthOut

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthOut)
def health(container: Annotated[Container, Depends(get_container)]) -> HealthOut:
    """Return mode, model load states and overall status (``ok`` / ``degraded``)."""
    return container.health()
