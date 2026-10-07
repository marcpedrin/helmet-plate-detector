"""Best-evidence-frame selection for confirmed violations.

Owner: Marc. Signatures are final; bodies are pending.
"""

from __future__ import annotations

from app.core.types import EvidenceBundle, FramePacket, HelmetResult, Rider


class EvidenceSelector:
    """Keeps, per rider, the best frame seen so far while the rider is SUSPECTED/CONFIRMED.

    Score (to tune): NO_HELMET head confidence x rider-box sharpness (Laplacian variance)
    x size, preferring frames where the rider is fully inside the frame.

    Thread-safety: one instance per camera pipeline thread.
    """

    def __init__(self, max_riders: int = 64) -> None:
        """Create an empty selector holding at most ``max_riders`` candidates."""
        raise NotImplementedError("Marc: implement EvidenceSelector")

    def offer(self, packet: FramePacket, rider: Rider, helmet: HelmetResult) -> None:
        """Consider this frame as evidence for ``rider`` (copies the image only if it wins)."""
        raise NotImplementedError

    def build(self, rider_id: int) -> EvidenceBundle | None:
        """Return the evidence bundle (full frame annotated + rider crop) or None if unseen."""
        raise NotImplementedError

    def forget(self, rider_id: int) -> None:
        """Release the stored frame for ``rider_id``."""
        raise NotImplementedError
