"""Prepare demo footage for the virtual cameras.

Resizes (keeping aspect; 16:9 output is letterboxed), trims, resamples fps and strips audio
using OpenCV only (no ffmpeg needed). 4K sources decode far too slowly for real-time
inference, so always run this on new footage.

Usage (repo root):
    python scripts/prepare_videos.py SRC.mp4 --out videos/camera_01.mp4 [--start 0] [--duration 60]
        [--width 1280] [--height 720] [--fps 25] [--force]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np


def letterbox(frame: np.ndarray, w: int, h: int) -> np.ndarray:
    """Scale ``frame`` to fit inside w x h and pad with black."""
    fh, fw = frame.shape[:2]
    s = min(w / fw, h / fh)
    nw, nh = int(round(fw * s)), int(round(fh * s))
    small = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_AREA)
    out = np.zeros((h, w, 3), np.uint8)
    y, x = (h - nh) // 2, (w - nw) // 2
    out[y : y + nh, x : x + nw] = small
    return out


def prepare(src: Path, out: Path, start: float, duration: float | None, w: int, h: int, fps: float) -> None:
    """Transcode one clip."""
    cap = cv2.VideoCapture(str(src))
    if not cap.isOpened():
        raise RuntimeError(f"cannot open {src}")
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = cap.get(cv2.CAP_PROP_FRAME_COUNT) / src_fps
    end = total if duration is None else min(total, start + duration)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp.mp4")
    writer = cv2.VideoWriter(str(tmp), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    t_out = start
    idx = 0
    written = 0
    cap.set(cv2.CAP_PROP_POS_MSEC, start * 1000)
    idx = int(start * src_fps)
    while t_out < end:
        target = int(t_out * src_fps)
        while idx < target:
            if not cap.grab():
                break
            idx += 1
        ok, frame = cap.read()
        idx += 1
        if not ok:
            break
        writer.write(letterbox(frame, w, h))
        written += 1
        t_out += 1.0 / fps
    writer.release()
    cap.release()
    tmp.replace(out)
    print(f"{src.name} -> {out}  {w}x{h} @{fps}fps  {written / fps:.1f}s ({written} frames)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--duration", type=float, default=None)
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    ap.add_argument("--fps", type=float, default=25.0)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    if a.out.exists() and not a.force:
        print(f"{a.out} exists; use --force to overwrite")
        return 1
    prepare(a.src, a.out, a.start, a.duration, a.width, a.height, a.fps)
    return 0


if __name__ == "__main__":
    sys.exit(main())
