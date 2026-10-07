"""Download the 4 demo clips (Pexels, free license) and transcode them into videos/camera_0N.mp4.

Videos are git-ignored, so run this once on every machine:
    python scripts/fetch_demo_videos.py [--force]

Sources (Pexels License: free to use, no attribution required):
    CAM_01 https://www.pexels.com/video/34394881/  riders approaching, several without helmets
    CAM_02 https://www.pexels.com/video/34394431/  rider from behind, no helmet, rear plate
    CAM_03 https://www.pexels.com/video/38617712/  underpass traffic
    CAM_04 https://www.pexels.com/video/15328413/  Ellis Bridge, Ahmedabad (mostly helmeted riders)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CLIPS = [("camera_01", 34394881, None), ("camera_02", 34394431, None), ("camera_03", 38617712, None),
         ("camera_04", 15328413, 30)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    raw_dir = REPO_ROOT / "data" / "raw_videos"
    raw_dir.mkdir(parents=True, exist_ok=True)
    for name, vid, duration in CLIPS:
        out = REPO_ROOT / "videos" / f"{name}.mp4"
        if out.exists() and not a.force:
            print(f"{out} exists (use --force)")
            continue
        raw = raw_dir / f"pexels_{vid}.mp4"
        if not raw.exists():
            print(f"downloading pexels {vid} ...")
            req = urllib.request.Request(f"https://www.pexels.com/download/video/{vid}/",
                                         headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req) as r, open(raw.with_suffix(".part"), "wb") as f:
                while chunk := r.read(1 << 20):
                    f.write(chunk)
            raw.with_suffix(".part").replace(raw)
        cmd = [sys.executable, str(REPO_ROOT / "scripts" / "prepare_videos.py"), str(raw), "--out", str(out), "--force"]
        if duration:
            cmd += ["--duration", str(duration)]
        subprocess.run(cmd, check=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
