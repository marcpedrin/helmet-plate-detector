# 0007. Synthetic fallback only in mock mode

- Status: accepted
- Date: 2026-10-07
- Owner: Marc

## Context

Development should work without videos, but a live demo must visibly report a broken camera.

## Decision

Use a labelled synthetic source for missing files only when `APP_MODE=mock`; live sources transition to OFFLINE and retry.

## Alternatives considered

| Option | Pros | Cons | Why not |
|---|---|---|---|
| Always synthesize | Demo never blanks | Hides operational failures | Misleading in live mode |
| Fail process | Clear failure | Other cameras die too | Poor resilience |

## Consequences

Mock UI remains usable, while live camera tiles demonstrate isolated failure and recovery.
