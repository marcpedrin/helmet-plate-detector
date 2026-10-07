"""Prepare demo footage for the four virtual cameras.  Owner: Prajwal.

Must do (to implement):
  * Take source clips (path args or a folder) and write ``videos/camera_01.mp4`` ... ``camera_04.mp4``.
  * Trim to 60-120 s (``--start``/``--duration``), resize to 1280x720 keeping aspect (letterbox),
    re-encode H.264 at 25-30 fps with OpenCV (or ffmpeg if available), strip audio.
  * Print per-file resolution, fps, duration and a warning when riders/plates are likely too
    small (see docs/DEMO.md footage guidance).
  * Never overwrite an existing camera file without ``--force``.
"""

from __future__ import annotations

import sys


def main() -> int:
    print("prepare_videos.py: not implemented yet (owner: Prajwal). See the module docstring.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
