"""Run the pipeline on a video file without the server: annotated MP4 out + summary. Owner: Marc.

This is the tuning tool. It uses the real detector + tracker, rider association and violation engine, with
the real helmet/plate modules when available (``--helmet real --plates real``) or the mocks:

    python scripts/run_pipeline_offline.py --video videos/camera_01.mp4 --out out.mp4 --max-seconds 60
    python scripts/run_pipeline_offline.py --video clip.mp4 --out out.mp4 --helmet scripted   # every rider NO_HELMET

The engine clock is the *video* clock (``video_pos_ms``), so results are deterministic and independent of how
fast this machine is. Evidence JPEGs of confirmed violations go to ``<out>_evidence/``.
"""

from __future__ import annotations

import argparse
import sys
import time
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

import cv2  # noqa: E402

from app.config import Settings  # noqa: E402
from app.core.types import FramePacket, HelmetStatus, ModelState  # noqa: E402
from app.pipeline.association import associate_riders  # noqa: E402
from app.pipeline.detector import ObjectTracker  # noqa: E402
from app.pipeline.overlay import OverlayRider, OverlayState  # noqa: E402
from app.pipeline.violation_engine import (  # noqa: E402
    Confirm,
    Finalize,
    NeedPlate,
    TrackPhase,
    ViolationEngine,
)


def build_helmet(kind: str, settings: Settings):
    from app.helmet.mock import MockHelmetClassifier, ScriptedHelmetClassifier

    if kind == "scripted":
        return ScriptedHelmetClassifier([HelmetStatus.NO_HELMET], confidence=0.8)
    if kind == "unknown":
        return MockHelmetClassifier(ModelState.MOCK)
    from app.helmet import load_helmet_classifier

    return load_helmet_classifier(settings)


def build_plates(kind: str, settings: Settings):
    from app.plates.mock import MockPlateService

    if kind == "mock":
        return MockPlateService(ModelState.MOCK)
    from app.plates import load_plate_service

    return load_plate_service(settings)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--video", required=True)
    ap.add_argument("--out", required=True, help="annotated MP4 path")
    ap.add_argument("--max-seconds", type=float, default=0.0, help="0 = whole file")
    ap.add_argument("--fps", type=float, default=None, help="processing FPS (default PIPELINE_FPS)")
    ap.add_argument("--helmet", choices=["real", "scripted", "unknown"], default="real")
    ap.add_argument("--plates", choices=["real", "mock"], default="real")
    ap.add_argument("--imgsz", type=int, default=None)
    ap.add_argument("--conf", type=float, default=None)
    args = ap.parse_args()

    settings = Settings()
    if args.imgsz:
        settings.detector_imgsz = args.imgsz
    if args.conf:
        settings.detector_conf = args.conf
    fps = args.fps or settings.pipeline_fps

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        print(f"cannot open {args.video}")
        return 1
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    step = max(1, round(src_fps / fps))

    tracker = ObjectTracker(settings, "OFFLINE")
    if tracker.state != ModelState.LOADED:
        print(f"detector {tracker.state.value}: {tracker.error}")
        return 1
    helmet = build_helmet(args.helmet, settings)
    plates = build_plates(args.plates, settings)
    engine = ViolationEngine(settings, "OFFLINE", plates.new_voter)
    overlay = OverlayState({"OFFLINE": Path(args.video).name})
    print(f"detector {tracker.device} | helmet {helmet.state.value} | plates {plates.detector_state.value}")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ev_dir = out_path.with_name(out_path.stem + "_evidence")
    writer = None
    timings = Counter()
    tracks_seen: set[int] = set()
    phases: dict[int, set[TrackPhase]] = {}
    confirmed, finals = [], []
    n = idx = 0
    last_helmet: dict[int, object] = {}

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        idx += 1
        if (idx - 1) % step:
            continue
        pos_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
        if args.max_seconds and pos_ms / 1000 > args.max_seconds:
            break
        packet = FramePacket("OFFLINE", idx, 0, pos_ms, pos_ms / 1000, frame)
        t0 = time.perf_counter()
        tracks = tracker.update(packet)
        t1 = time.perf_counter()
        riders = associate_riders(tracks, frame.shape[1], frame.shape[0])
        eligible = [r for r in riders if r.bbox[3] - r.bbox[1] >= settings.min_rider_height_px]
        res_map = dict(zip([r.rider_id for r in eligible], helmet.classify_batch(frame, eligible), strict=True)) \
            if eligible else {}
        results = [res_map.get(r.rider_id) for r in riders]
        t2 = time.perf_counter()
        claimed = []
        for a in engine.update("OFFLINE", packet, riders, results, pos_ms / 1000):
            if isinstance(a, NeedPlate):
                obs = plates.observe(frame, a.rider, run_ocr=a.run_ocr, exclude=tuple(claimed))
                if obs.detection:
                    claimed.append(obs.detection.bbox)
                engine.record_plate(a.rider.rider_id, obs)
            elif isinstance(a, Confirm):
                confirmed.append(a.event)
                ev_dir.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(str(ev_dir / f"{a.event.violation_id[:8]}_full.jpg"), a.event.evidence.full_frame)
                cv2.imwrite(str(ev_dir / f"{a.event.violation_id[:8]}_rider.jpg"), a.event.evidence.rider_crop)
                print(f"  {pos_ms / 1000:7.1f}s CONFIRM track #{a.event.track_id} conf {a.event.helmet_confidence:.2f}")
            elif isinstance(a, Finalize):
                finals.append(a)
                if a.plate_crop is not None:
                    cv2.imwrite(str(ev_dir / f"{a.violation_id[:8]}_plate.jpg"), a.plate_crop)
                print(f"  {pos_ms / 1000:7.1f}s FINAL   track #{a.rider_id} plate {a.plate.status.value} {a.plate.text}")
        t3 = time.perf_counter()
        for r, res in zip(riders, results, strict=True):
            tracks_seen.add(r.rider_id)
            if res is not None:
                last_helmet[r.rider_id] = res
            ph = engine.phase(r.rider_id)
            if ph:
                phases.setdefault(r.rider_id, set()).add(ph)
        shown = []
        for r in riders:
            res = last_helmet.get(r.rider_id)
            ph = engine.phase(r.rider_id)
            shown.append(OverlayRider(r.rider_id, r.bbox, res.status if res else HelmetStatus.UNKNOWN,
                                      res.confidence if res else 0.0,
                                      ph in (TrackPhase.CONFIRMED, TrackPhase.FINALIZED), engine.plate_text(r.rider_id)))
        overlay.update("OFFLINE", shown, 1.0 / max(t3 - t0, 1e-6))
        annotated = overlay.draw("OFFLINE", frame.copy())
        if writer is None:
            h, w = annotated.shape[:2]
            writer = cv2.VideoWriter(str(out_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
        writer.write(annotated)
        timings["detect"] += t1 - t0
        timings["helmet"] += t2 - t1
        timings["engine+plates"] += t3 - t2
        n += 1

    # End of clip: finalize anything still CONFIRMED by advancing the clock past every timeout.
    if n:
        end = FramePacket("OFFLINE", idx + 1, 0, packet.video_pos_ms, packet.timestamp, packet.image)
        finals += [a for a in engine.update("OFFLINE", end, [], [], packet.timestamp + 60) if isinstance(a, Finalize)]
    if writer is not None:
        writer.release()
    cap.release()

    suspected = sum(1 for p in phases.values() if TrackPhase.SUSPECTED in p)
    plates_by = Counter(f.plate.status.value for f in finals)
    print("\nSUMMARY")
    print(f"  frames processed : {n} (every {step} of {src_fps:.1f} fps source -> {fps} fps)")
    print(f"  rider tracks     : {len(tracks_seen)}")
    print(f"  suspected        : {suspected}")
    print(f"  confirmed        : {len(confirmed)}  (suppressed: {sum(1 for p in phases.values() if TrackPhase.SUPPRESSED in p)})")
    print(f"  plates           : {dict(plates_by) or '-'}")
    if n:
        ms = {k: 1000 * v / n for k, v in timings.items()}
        total = sum(ms.values())
        print(f"  ms/frame         : " + ", ".join(f"{k} {v:.1f}" for k, v in ms.items()) + f"  (total {total:.1f} -> {1000 / total:.1f} FPS)")
    print(f"  output           : {out_path}" + (f", evidence in {ev_dir}" if confirmed else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
