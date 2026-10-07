"""Violation persistence: SQLite repository + JPEG evidence store.

Owner: Marc (camera/storage stream, separate Codex session on ``feature/backend-camera``).
Until ``SqliteViolationRepository`` lands, :func:`create_repository` returns the working
``InMemoryRepository`` so the rest of the app runs end to end.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.config import resolve
from app.core.interfaces import ViolationRepositoryProtocol

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from app.config import Settings


def create_repository(settings: Settings) -> ViolationRepositoryProtocol:
    """Build the violation repository.

    Never raises. The camera/storage stream replaces the body with
    ``SqliteViolationRepository(resolve(settings.db_path), EvidenceStore(...))`` and keeps
    ``InMemoryRepository`` as the fallback when the database cannot be opened.

    Args:
        settings: Application settings (``evidence_dir``, ``db_path``).

    Returns:
        A repository implementing ``ViolationRepositoryProtocol``.
    """
    from app.storage.evidence_store import EvidenceStore
    from app.storage.repository import InMemoryRepository, SqliteViolationRepository

    evidence = EvidenceStore(resolve(settings.evidence_dir))
    try:
        return SqliteViolationRepository(resolve(settings.db_path), evidence)
    except Exception:
        log.exception("SQLite repository initialization failed; using in-memory fallback")
        return InMemoryRepository(evidence)
