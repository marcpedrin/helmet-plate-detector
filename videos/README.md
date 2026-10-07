# videos/

Owner: **Prajwal** (demo footage). Videos are **never committed** (`*.mp4` is git-ignored).

The four virtual cameras read:

| Camera | File | Name |
|---|---|---|
| CAM_01 | `videos/camera_01.mp4` | MG Road Junction |
| CAM_02 | `videos/camera_02.mp4` | Ring Road Signal |
| CAM_03 | `videos/camera_03.mp4` | Market Street |
| CAM_04 | `videos/camera_04.mp4` | College Gate |

A missing file is not an error: that camera falls back to a synthetic test pattern and
reports `last_error` in `/api/cameras`.

## Getting the footage

* Shared team drive link: _TODO (Prajwal)_.
* Prepare clips with `python scripts/prepare_videos.py` (trim, resize to 1280x720, re-encode H.264, 60-120 s).
* Footage guidance (angle, sizes, lighting) and licensing: see [docs/DEMO.md](../docs/DEMO.md),
  [docs/PRIVACY.md](../docs/PRIVACY.md) and [docs/modules/footage.md](../docs/modules/footage.md).
