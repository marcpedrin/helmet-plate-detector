"""``GET /api/violations`` and ``GET /api/violations/{id}``. Owner: Marc."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api import get_container
from app.container import Container
from app.core.schemas import ViolationOut, ViolationPage

router = APIRouter(prefix="/api/violations", tags=["violations"])


@router.get("", response_model=ViolationPage)
def list_violations(
    container: Annotated[Container, Depends(get_container)],
    camera_id: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ViolationPage:
    """Return violations newest-first, optionally filtered by ``camera_id``."""
    return container.repository.list(camera_id=camera_id, limit=limit, offset=offset)


@router.get("/{violation_id}", response_model=ViolationOut)
def get_violation(violation_id: str, container: Annotated[Container, Depends(get_container)]) -> ViolationOut:
    """Return one violation.

    Raises:
        HTTPException: 404 if it does not exist.
    """
    v = container.repository.get(violation_id)
    if v is None:
        raise HTTPException(status_code=404, detail="violation not found")
    return v
