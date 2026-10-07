"""Associate person tracks with motorcycle tracks to form riders.

Owner: Marc. Placeholder: returns no riders until implemented.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.core.types import Rider, Track


def associate_riders(tracks: Sequence[Track], frame_w: int, frame_h: int) -> list[Rider]:
    """Group persons onto motorcycles.

    Contract: a person belongs to a motorcycle when ``geometry.ioa(person, expanded_moto)``
    is high and the person's bottom-centre lies within the motorcycle's horizontal span;
    each person is assigned to at most one motorcycle (greedy by score); at most 3
    persons per motorcycle. ``Rider.bbox = geometry.union(moto, *persons)``. Riders whose
    bbox height is below ``MIN_RIDER_HEIGHT_PX`` are dropped by the caller.

    Args:
        tracks: All tracks in the frame.
        frame_w: Frame width (for clipping expanded boxes).
        frame_h: Frame height.

    Returns:
        Riders, one per motorcycle with at least one person. Placeholder: always ``[]``.
    """
    return []
