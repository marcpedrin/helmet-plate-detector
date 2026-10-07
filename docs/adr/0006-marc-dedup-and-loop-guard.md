# 0006. Dedup strategy: per-track, ID-switch and video-loop guards

- Status: accepted
- Date: 2026-10-07
- Owner: Marc

## Context

The output contract is "exactly one violation per real violation". Three things break it: a track that stays in
view after its violation, ByteTrack ID switches after occlusion, and the prerecorded videos looping (the same
rider rides past again every 60-120 s, with fresh track ids because the tracker resets).

## Decision

Checked once, at confirmation; a match moves the track to SUPPRESSED and emits nothing:

1. **Per track**: one violation per `(track_id, loop_index)`, ever (records outlive the 30 s state GC).
2. **ID switch**: another violation on the same camera last seen ≤ `DEDUP_WINDOW_S` (5 s) ago whose last
   rider bbox has IoU ≥ `DEDUP_IOU` (0.3) with this rider.
3. **Loop guard**: a violation from an earlier `loop_index` confirmed within ±1500 ms of the same
   `video_pos_ms` with IoU ≥ 0.3.

Records are kept 10 minutes in memory.

## Alternatives considered

| Option | Why not |
|---|---|
| Plate-text dedup | plates are often unreadable, and arrive after confirmation |
| Appearance ReID | another model and CPU budget |
| Disable looping | the cameras must run indefinitely for the demo |
| Global "one violation per N seconds per camera" | suppresses genuine violations by different riders |

## Consequences

Two different riders confirmed at the same place within 5 s with overlapping boxes would be merged (rare, accepted).
Records are lost on restart, so a looping clip can re-fire once after a backend restart.
