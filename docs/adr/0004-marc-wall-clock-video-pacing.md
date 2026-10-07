# 0004. Wall-clock paced video decoding

- Status: accepted
- Date: 2026-10-07
- Owner: Marc

## Context

Virtual cameras must play prerecorded footage at real speed even when browser output FPS is lower than file FPS.

## Decision

Use monotonic wall-clock time to select the source frame index, `grab()` skipped frames, and retrieve only emitted frames.

## Alternatives considered

| Option | Pros | Cons | Why not |
|---|---|---|---|
| Sequential reads | Simple | Runs slow at low output FPS | Does not preserve speed |
| Per-frame sleep | Simple | Decode overhead drifts clock | Accumulates lag |

## Consequences

Output can skip frames by design, while positions and loops remain faithful to source time.
