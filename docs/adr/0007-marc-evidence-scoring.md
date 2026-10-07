# 0007. Evidence frame scoring

- Status: accepted
- Date: 2026-10-07
- Owner: Marc

## Context

The confirming frame is often not the best picture: the rider may be small, blurred or half out of frame.
Reviewers need one clear image per violation, but we cannot keep every frame (memory, 4 cameras).

## Decision

For every NO_HELMET look while SUSPECTED/CONFIRMED compute
`score = conf × min(1, h/250) × min(1, LaplacianVar(gray crop)/300) × (0.5 if the box touches the border)` and keep
only the best frame per track (copied only when it wins). At confirmation the bundle is the annotated full frame
and `crop(expand(bbox, 0.1))`; the plate crop comes later from the voter.

## Alternatives considered

| Option | Why not |
|---|---|
| Confirming frame | often blurred / small |
| Highest helmet confidence only | ignores blur and size |
| Keep last N frames, pick at the end | N full frames per track × 4 cameras of memory |
| Learned image-quality model | extra model and latency |

## Consequences

Memory is bounded to one 1280×720 frame (~2.7 MB) per suspected track. Constants (250 px, 300 lapvar) are tuned on
720p footage and documented as `# WHY:` comments in `pipeline/evidence.py`.
