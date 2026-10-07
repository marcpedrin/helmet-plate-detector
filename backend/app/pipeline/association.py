"""Associate person tracks with motorcycle tracks to form riders.

Owner: Marc. Pure geometry, no state; see docs/modules/pipeline.md §7 for the diagram.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.core import geometry
from app.core.types import BBox, Rider, Track

# WHY: riders sit above and slightly beside the bike; a 1.2x-height upward expansion covers a seated adult's
# head even when the bike box is only the lower body, while 0.2 width on each side tolerates leaning riders.
SEARCH_FX, SEARCH_FY_TOP, SEARCH_FY_BOTTOM = 0.2, 1.2, 0.1
# WHY: >= half the person must lie inside the bike's search region; lower values pull in pedestrians
# walking past.
MIN_IOA = 0.5
# WHY: with no person detected, the head region is still roughly 0.8 bike-heights above the bike, so
# the helmet classifier gets a useful crop instead of just the wheels.
NO_PERSON_FX, NO_PERSON_FY_TOP = 0.05, 0.8


def _is_candidate(person: BBox, moto: BBox, search: BBox) -> float:
    """Return the IoA score if ``person`` can ride ``moto`` (0.0 otherwise)."""
    mx1, my1, mx2, my2 = moto
    mh = my2 - my1
    score = geometry.ioa(person, search)
    if score < MIN_IOA:
        return 0.0
    # WHY: a rider's feet/legs end on the bike; a pedestrian behind the bike ends lower (closer to the
    # camera).
    if not (my1 <= person[3] <= my2 + 0.1 * mh):
        return 0.0
    # WHY: a rider's centre is above the bike's lower part; this rejects people crouching next to parked
    # bikes.
    if geometry.center(person)[1] >= geometry.center(moto)[1] + 0.25 * mh:
        return 0.0
    return score


def associate_riders(tracks: Sequence[Track], frame_w: int, frame_h: int) -> list[Rider]:
    """Group persons onto motorcycles (handles several bikes and pillion riders).

    Rules: a person P is a candidate for motorcycle M when
    ``ioa(P, expand(M, 0.2, 1.2, 0.1)) >= 0.5``, P's bottom edge lies in ``[M.y1, M.y2 + 0.1*M.h]`` and P's
    centre-y is above ``M.cy + 0.25*M.h``. Each person goes to the candidate bike with the highest IoA
    (greedy, one bike per person); unassigned persons are pedestrians and ignored.

    Args:
        tracks: All tracks in the frame.
        frame_w: Frame width (for clipping).
        frame_h: Frame height.

    Returns:
        One ``Rider`` per motorcycle, sorted by track id. ``bbox`` is the union of the bike and its
        persons, or the bike expanded upwards when nobody was assigned; always clipped to the frame.

    Example:
        >>> riders = associate_riders(tracker.update(packet), 1280, 720)
    """
    motos = [t for t in tracks if t.class_name == "motorcycle"]
    persons = [t for t in tracks if t.class_name == "person"]
    assigned: dict[int, list[Track]] = {m.track_id: [] for m in motos}
    searches = {
        m.track_id: geometry.expand(m.bbox, SEARCH_FX, SEARCH_FY_TOP, SEARCH_FY_BOTTOM, frame_w, frame_h)
        for m in motos
    }
    for p in persons:
        best_id, best_score = None, 0.0
        for m in motos:
            score = _is_candidate(p.bbox, m.bbox, searches[m.track_id])
            if score > best_score:
                best_id, best_score = m.track_id, score
        if best_id is not None:
            assigned[best_id].append(p)

    riders = []
    for m in sorted(motos, key=lambda t: t.track_id):
        ps = tuple(sorted(assigned[m.track_id], key=lambda t: t.track_id))
        if ps:
            box = geometry.clip(geometry.union(m.bbox, *(p.bbox for p in ps)), frame_w, frame_h)
        else:
            box = geometry.expand(m.bbox, NO_PERSON_FX, NO_PERSON_FY_TOP, 0.0, frame_w, frame_h)
        riders.append(Rider(m.track_id, m, ps, box))
    return riders
