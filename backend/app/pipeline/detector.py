"""YOLO26n person+motorcycle detector with ByteTrack tracking, one instance per camera.

Owner: Marc. ultralytics/torch are imported inside ``__init__`` (never at module level), so mock mode and CI
run without ML packages.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from app.config import REPO_ROOT
from app.core.types import FramePacket, ModelState, Track

if TYPE_CHECKING:
    from app.config import Settings

log = logging.getLogger(__name__)

TRACKER_CFG = Path(__file__).with_name("bytetrack.yaml")
# COCO class ids used by YOLO26n.
COCO_CLASSES = {0: "person", 3: "motorcycle"}
MODELS_DIR = REPO_ROOT / "backend" / "models"


def resolve_device(device: str) -> str:
    """Resolve ``DEVICE``: ``auto`` -> ``cuda:0`` if CUDA is available else ``cpu``; others pass through."""
    if device != "auto":
        return device
    try:
        import torch

        return "cuda:0" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"


def resolve_weights(name: str) -> str:
    """Map a bare weights name (``yolo26n.pt``) to ``backend/models/<name>`` so downloads land there."""
    p = Path(name)
    if p.is_absolute() or len(p.parts) > 1:
        return str(p if p.is_absolute() else REPO_ROOT / p)
    return str(MODELS_DIR / p)


class ObjectTracker:
    """Detects persons and motorcycles and tracks them with ByteTrack.

    One instance per camera: Ultralytics keeps tracker state inside the model object, so sharing a model
    across cameras would mix their tracks.

    Thread-safety: used by exactly one pipeline thread.

    Example:
        >>> tracker = ObjectTracker(settings, "CAM_01")
        >>> tracks = tracker.update(packet) if tracker.state == ModelState.LOADED else []
    """

    def __init__(self, settings: Settings, camera_id: str) -> None:
        """Load YOLO and warm it up. Never raises: on failure ``state`` is NOT_LOADED or ERROR.

        Args:
            settings: Uses ``detector_weights``, ``detector_imgsz``, ``detector_conf``, ``device``.
            camera_id: Camera this tracker belongs to (for logs).
        """
        self.camera_id = camera_id
        self.imgsz = settings.detector_imgsz
        self.conf = settings.detector_conf
        self.state = ModelState.NOT_LOADED
        self.error: str | None = None
        self.device = "cpu"
        self.half = False
        self._model = None
        self._loop_index: int | None = None
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            self.error = f"ultralytics not installed ({exc}); pip install -r backend/requirements-ml.txt"
            log.warning("%s: detector NOT_LOADED: %s", camera_id, self.error)
            return
        try:
            self.device = resolve_device(settings.device)
            # WHY: FP16 halves GPU latency with negligible accuracy loss; CPU kernels have no FP16 speed-up.
            self.half = self.device.startswith("cuda")
            weights = resolve_weights(settings.detector_weights)
            Path(weights).parent.mkdir(parents=True, exist_ok=True)
            self._model = YOLO(weights)
            # WHY: the first inference allocates buffers / compiles kernels (~1-2 s); do it before going live.
            self._model.predict(
                np.zeros((640, 640, 3), np.uint8),
                imgsz=self.imgsz,
                device=self.device,
                half=self.half,
                verbose=False,
            )
            self.state = ModelState.LOADED
            log.info("%s: detector LOADED (%s on %s, half=%s)", camera_id, weights, self.device, self.half)
        except Exception as exc:
            self.state = ModelState.ERROR
            self.error = str(exc)
            log.exception("%s: detector failed to load", camera_id)

    def update(self, packet: FramePacket) -> list[Track]:
        """Run detection + tracking on one frame.

        The tracker is reset (``persist=False``) on the first frame of every new ``loop_index`` so a restarted
        video does not inherit tracks from the end of the previous loop.

        Args:
            packet: Frame to process (image is BGR, read-only).

        Returns:
            Person/motorcycle tracks with stable ids; ``[]`` when not LOADED or when nothing is tracked.

        Raises:
            Exception: Inference errors propagate; the runner counts them and keeps the thread alive.
        """
        if self._model is None or self.state != ModelState.LOADED:
            return []
        persist = self._loop_index == packet.loop_index
        self._loop_index = packet.loop_index
        result = self._model.track(
            packet.image,
            persist=persist,
            tracker=str(TRACKER_CFG),
            classes=list(COCO_CLASSES),
            conf=self.conf,
            imgsz=self.imgsz,
            device=self.device,
            half=self.half,
            verbose=False,
        )[0]
        boxes = result.boxes
        if boxes is None or boxes.id is None:
            return []
        xyxy = boxes.xyxy.cpu().numpy()
        ids = boxes.id.int().cpu().tolist()
        classes = boxes.cls.int().cpu().tolist()
        confs = boxes.conf.cpu().tolist()
        tracks = []
        for box, tid, cls, conf in zip(xyxy, ids, classes, confs, strict=True):
            name = COCO_CLASSES.get(cls)
            if name is None:
                continue
            x1, y1, x2, y2 = (int(round(float(v))) for v in box)
            tracks.append(Track(int(tid), (x1, y1, x2, y2), float(conf), name))  # type: ignore[arg-type]
        return tracks
