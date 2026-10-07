# Demo guide

## Footage guidance (owner: Prajwal)

| Requirement | Target |
|---|---|
| Camera angle | Elevated (footbridge / first floor), looking down the road at 20-45°; riders approach the camera |
| Rider size | Riders ≥ 100 px tall in a 1280x720 frame |
| Plate size | Plates ≥ 80 px wide when the rider is closest (rear plates if filming from behind) |
| Light | Daylight, no strong backlight, no night clips |
| Length | 60-120 s per clip, several helmet and no-helmet riders each |
| Format | 1280x720, 25-30 fps, H.264, no audio (`scripts/prepare_videos.py`) |
| Files | `videos/camera_01.mp4` … `camera_04.mp4` (see [videos/README.md](../videos/README.md)) |

## Demo script (≈ 4 minutes)

1. **Dashboard** at `http://localhost:5173` (or `:8000` when the built frontend is served by FastAPI).
   Point at the status bar: 4 cameras ONLINE, models LOADED, mode `live`.
2. **Four feeds**: the 2×2 grid shows the four virtual cameras playing in real time.
3. **Boxes**: rider boxes appear, green = helmet, red = no helmet, grey = unknown.
4. **Violation**: a red rider is confirmed → a card appears in the alert feed (plate "pending").
5. **Plate fills in**: ~1-3 s later the same card updates with the plate text (or UNREADABLE).
6. **Click the incident**: evidence viewer shows the full frame, rider crop and plate crop, confidences,
   camera and time.
7. **Stats**: totals per camera, plates read vs unreadable.
8. Close with the privacy disclaimer ([PRIVACY.md](PRIVACY.md)).

## Fallback plan

1. **Backup screen recording** of a full successful run of the script above, made the day before, on the
   demo laptop and a USB stick. If anything misbehaves live, switch to the recording immediately.
2. **`APP_MODE=mock`** only as a clearly labelled **UI walkthrough** ("this is simulated data"): every mock
   image is stamped MOCK. Never present mock output as real detections.
3. Pre-demo checklist: [RUNBOOK.md](RUNBOOK.md#pre-demo-checklist).
