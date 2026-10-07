# 0005. MJPEG shared encode cache

- Status: accepted
- Date: 2026-10-07
- Owner: Marc

## Context

Several dashboard tabs can request the same camera frame concurrently.

## Decision

Cache encoded JPEG bytes by camera manager, camera ID, and immutable frame index.

## Alternatives considered

| Option | Pros | Cons | Why not |
|---|---|---|---|
| Encode per client | Simple | CPU grows with tabs | Wasteful |
| WebRTC | Efficient | Signalling and operational complexity | Overkill for local demo |

## Consequences

MJPEG remains browser-native, with one encoding cost per camera frame and client polling of the latest frame.
