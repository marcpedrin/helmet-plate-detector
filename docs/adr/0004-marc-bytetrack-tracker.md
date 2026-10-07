# 0004. Ultralytics built-in ByteTrack for rider tracking

- Status: accepted
- Date: 2026-10-07
- Owner: Marc

## Context

A violation is a temporal decision (several looks at the same rider), so every rider needs a stable id across
frames at only ~3-8 processed FPS, on CPU or GPU, with no extra install burden.

## Decision

Use `model.track(..., tracker=pipeline/bytetrack.yaml)` from Ultralytics 8.4 with YOLO26n, one model instance per
camera. Tuned for low FPS: `track_high_thresh 0.4`, `new_track_thresh 0.45`, `track_buffer 15` (≈ 3 s at 5 FPS),
`match_thresh 0.8`, `fuse_score true`. `persist=False` on the first frame of each new `loop_index`.

## Alternatives considered

| Option | Pros | Cons | Why not |
|---|---|---|---|
| BoT-SORT (Ultralytics) | camera-motion compensation, optional ReID | slower (GMC per frame), ReID needs another model | static cameras need no GMC; CPU budget too tight |
| DeepSORT / StrongSORT | appearance features | extra model + package, slower | same |
| OC-SORT / own IoU tracker | simple | another dependency or our own bugs | built-in ByteTrack is tested and free |
| Detection-only + IoU voting | no tracker | votes split across riders in traffic | temporal rule needs ids |

## Consequences

No extra dependency; tracker state lives in each model, hence one model per camera (≈ 6 MB weights, ~300 MB RAM each).
ID switches still happen under occlusion, which is why the engine has an ID-switch dedup guard ([0006](0006-marc-dedup-and-loop-guard.md)).
