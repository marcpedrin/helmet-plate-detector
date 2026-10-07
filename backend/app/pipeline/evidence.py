"""Best-evidence-frame selection and evidence bundle building.

Owner: Marc. Pure functions (image maths only, no I/O). Memory is bounded: one candidate frame per
SUSPECTED/CONFIRMED track.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from app.core import geometry
from app.core.types import BBox, EvidenceBundle, FramePacket

# WHY: riders >= 250 px tall are already sharp enough for a human reviewer; bigger is not better beyond that.
FULL_SIZE_PX = 250.0
# WHY: Laplacian variance ~300 separates in-focus 720p rider crops from motion-blurred ones on typical
# street footage; normalising to 1.0 above that stops texture-rich backgrounds from dominating.
SHARP_LAPVAR = 300.0
# WHY: a box touching the frame edge (<= 4 px) is usually cut off (head or plate missing).
BORDER_PX = 4
BORDER_PENALTY = 0.5
RED = (40, 40, 230)


@dataclass(frozen=True)
class EvidenceCandidate:
    """The best frame seen so far for one track (``frame`` is a private copy)."""

    score: float
    frame: np.ndarray
    bbox: BBox
    helmet_conf: float
    frame_index: int
    video_pos_ms: float
    timestamp: float


def laplacian_var(gray: np.ndarray) -> float:
    """Return the variance of the Laplacian (a standard focus measure); 0.0 for empty images."""
    if gray.size == 0:
        return 0.0
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def evidence_score(image: np.ndarray, bbox: BBox, helmet_conf: float) -> float:
    """Score a frame as evidence for a rider.

    ``score = helmet_conf * min(1, rider_h / 250) * min(1, lapvar(rider_crop_gray) / 300) * border``
    where ``border`` is 0.5 if the box is within 4 px of the frame edge, else 1.0.

    Args:
        image: Full BGR frame.
        bbox: Rider box in frame coordinates.
        helmet_conf: NO_HELMET confidence of this observation.

    Returns:
        Score in ``[0, 1]``; higher is better.
    """
    h, w = image.shape[:2]
    x1, y1, x2, y2 = bbox
    crop = geometry.crop(image, bbox)
    if crop.size == 0:
        return 0.0
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if crop.ndim == 3 else crop
    size = min(1.0, (y2 - y1) / FULL_SIZE_PX)
    sharp = min(1.0, laplacian_var(gray) / SHARP_LAPVAR)
    touches = x1 <= BORDER_PX or y1 <= BORDER_PX or x2 >= w - BORDER_PX or y2 >= h - BORDER_PX
    return helmet_conf * size * sharp * (BORDER_PENALTY if touches else 1.0)


def offer(
    current: EvidenceCandidate | None, packet: FramePacket, bbox: BBox, helmet_conf: float
) -> EvidenceCandidate | None:
    """Return the better of ``current`` and this frame, copying the frame only when it wins.

    Args:
        current: Best candidate so far (or None).
        packet: Current frame.
        bbox: Rider box in this frame.
        helmet_conf: NO_HELMET confidence of this observation.

    Returns:
        The winning candidate (``current`` itself when it is still the best).
    """
    score = evidence_score(packet.image, bbox, helmet_conf)
    if current is not None and current.score >= score:
        return current
    return EvidenceCandidate(
        score,
        packet.image.copy(),
        bbox,
        helmet_conf,
        packet.frame_index,
        packet.video_pos_ms,
        packet.timestamp,
    )


def build_evidence(candidate: EvidenceCandidate, track_id: int) -> EvidenceBundle:
    """Build the evidence images for a confirmed violation.

    Args:
        candidate: Best frame of the track.
        track_id: Shown in the label.

    Returns:
        ``EvidenceBundle(full_frame=annotated copy, rider_crop=crop(expand(bbox, 0.1)), plate_crop=None)``;
        the plate crop is added later through ``repository.update_plate``.
    """
    h, w = candidate.frame.shape[:2]
    rider_crop = geometry.crop(candidate.frame, geometry.expand(candidate.bbox, 0.1, 0.1, 0.1, w, h))
    full = candidate.frame.copy()
    x1, y1, x2, y2 = candidate.bbox
    cv2.rectangle(full, (x1, y1), (x2, y2), RED, 3)
    label = f"NO HELMET {candidate.helmet_conf:.2f} | #{track_id}"
    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
    ty = max(th + 8, y1 - 6)
    cv2.rectangle(full, (x1, ty - th - 8), (x1 + tw + 8, ty + 4), RED, -1)
    cv2.putText(full, label, (x1 + 4, ty - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
    return EvidenceBundle(full_frame=full, rider_crop=rider_crop, plate_crop=None)
