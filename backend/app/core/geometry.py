"""Bounding-box helpers shared by every module.

All boxes are ``BBox = (x1, y1, x2, y2)`` integer pixel coordinates. Functions are
pure and thread-safe. Degenerate boxes (x2 <= x1 or y2 <= y1) have area 0.
"""

from __future__ import annotations

import numpy as np

from app.core.types import BBox


def area(box: BBox) -> int:
    """Return the area of ``box`` in pixels (0 for degenerate boxes)."""
    x1, y1, x2, y2 = box
    return max(0, x2 - x1) * max(0, y2 - y1)


def center(box: BBox) -> tuple[float, float]:
    """Return the ``(cx, cy)`` centre of ``box``."""
    x1, y1, x2, y2 = box
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


def _intersection(a: BBox, b: BBox) -> int:
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[2], b[2]), min(a[3], b[3])
    return area((x1, y1, x2, y2))


def iou(a: BBox, b: BBox) -> float:
    """Return intersection-over-union of two boxes, in ``[0, 1]``."""
    inter = _intersection(a, b)
    union_area = area(a) + area(b) - inter
    return inter / union_area if union_area > 0 else 0.0


def ioa(inner: BBox, outer: BBox) -> float:
    """Return intersection over the area of ``inner`` (how much of ``inner`` lies in ``outer``)."""
    a = area(inner)
    return _intersection(inner, outer) / a if a > 0 else 0.0


def union(*boxes: BBox) -> BBox:
    """Return the smallest box enclosing all ``boxes``.

    Raises:
        ValueError: If no boxes are given.
    """
    if not boxes:
        raise ValueError("union() needs at least one box")
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


def clip(box: BBox, w: int, h: int) -> BBox:
    """Clip ``box`` to the frame ``[0, w] x [0, h]``."""
    x1, y1, x2, y2 = box
    return (
        int(min(max(x1, 0), w)),
        int(min(max(y1, 0), h)),
        int(min(max(x2, 0), w)),
        int(min(max(y2, 0), h)),
    )


def expand(box: BBox, fx: float, fy_top: float, fy_bottom: float, frame_w: int, frame_h: int) -> BBox:
    """Grow ``box`` by fractions of its own size, then clip to the frame.

    Args:
        box: Box to expand.
        fx: Fraction of the width added on *each* side horizontally.
        fy_top: Fraction of the height added above.
        fy_bottom: Fraction of the height added below.
        frame_w: Frame width used for clipping.
        frame_h: Frame height used for clipping.

    Returns:
        The expanded, clipped box.
    """
    x1, y1, x2, y2 = box
    w, h = x2 - x1, y2 - y1
    grown = (
        int(round(x1 - fx * w)),
        int(round(y1 - fy_top * h)),
        int(round(x2 + fx * w)),
        int(round(y2 + fy_bottom * h)),
    )
    return clip(grown, frame_w, frame_h)


def crop(image: np.ndarray, box: BBox) -> np.ndarray:
    """Return a *copy* of ``image`` inside ``box`` (clipped to the image).

    Returns an empty ``(0, 0, C)`` array if the clipped box is degenerate, so callers
    can check ``crop.size == 0`` instead of catching exceptions.
    """
    h, w = image.shape[:2]
    x1, y1, x2, y2 = clip(box, w, h)
    if x2 <= x1 or y2 <= y1:
        return np.zeros((0, 0, *image.shape[2:]), dtype=image.dtype)
    return image[y1:y2, x1:x2].copy()
