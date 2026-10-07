# 0005. Violation confirmation rule: 6 of the last 10 looks

- Status: accepted
- Date: 2026-10-07
- Owner: Marc

## Context

Per-frame helmet classification is noisy: heads turn, get occluded, blur, or are too small. Firing on a single
NO_HELMET frame would flood the demo with false violations, which is the worst failure in front of judges.

## Decision

Per track, keep a sliding window of the last `VIOLATION_WINDOW=10` classified looks. SUSPECTED at
⌈MIN_HITS/2⌉ = 3 NO_HELMET looks (plate collection starts early, while the bike is close). CONFIRMED when
NO_HELMET ≥ `VIOLATION_MIN_HITS=6`, mean NO_HELMET confidence ≥ `VIOLATION_MIN_CONF=0.5`, HELMET ≤
`VIOLATION_MAX_HELMET_HITS=2`, and the track has ≥ 5 looks. Riders below `MIN_RIDER_HEIGHT_PX` don't vote.
The engine is pure (actions out, injected clock) so every rule is unit-tested.

## Alternatives considered

| Option | Why not |
|---|---|
| Single frame above a confidence | too many false positives on noisy crops |
| Mean confidence over the whole track | slow to react, one long track dominates, no early plate collection |
| HMM / Bayesian filter | harder to explain and tune in a hackathon; marginal gain |
| N consecutive hits | one UNKNOWN frame resets the streak; the windowed count is more tolerant |

## Consequences

At 5 FPS a violation needs ≥ ~1.2 s of the rider in view; very fast passes may be missed (tune `PIPELINE_FPS`,
`VIOLATION_MIN_HITS`). All thresholds are `.env` keys; per-clip values are recorded in pipeline.md §11.
