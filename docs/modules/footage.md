# Demo footage

Owner: Prajwal (@prajwaltotad) - `feature/helmet-detection`

<!-- doc-status: stub -->
<!-- Delete the marker above in your first feature PR; CI then enforces check_docs.py --strict. -->

## 1. Purpose & scope

<!-- What this module does and explicitly does NOT do.
One paragraph; link the ARCHITECTURE.md diagram node it implements. -->

Sourcing, licensing and preparation of the four demo clips (`videos/camera_0N.mp4`).
Does NOT include the videos themselves (never committed).

## 2. Owner & files

<!-- Owner name + GitHub handle, branch, and every file/dir owned (paths).
List tests and fixtures too. -->

`videos/README.md`, `scripts/prepare_videos.py` (DEMO.md footage section changes go through Marc).
No automated tests; verification = clips play in all four cameras.

## 3. Architecture

<!-- Internal structure: classes, threads, data flow. Prefer a Mermaid diagram.
Save screenshots/diagrams in docs/images/<module>/. -->

TBD

## 4. Public interface

<!-- Exact signatures callers rely on (copy from code), inputs/outputs, thread-safety.
Any change here needs a contracts/* PR. -->

Output contract: four files `videos/camera_01.mp4` ... `camera_04.mp4`, 1280x720, 25-30 fps, H.264, 60-120 s, riders >= 100 px tall, plates >= 80 px wide.

## 5. Configuration

<!-- Every .env key this module reads: name, default, unit, effect, tuning advice. -->

TBD

## 6. Dependencies, models & licenses

<!-- Packages (with versions), model files, sources, licenses, download steps. -->

TBD

## 7. Algorithms & design decisions

<!-- How it works and WHY. Thresholds with rationale (mirror the # WHY: comments).
Link ADRs for non-trivial decisions. -->

TBD

## 8. Failure modes & fallbacks

<!-- What happens when weights/files/devices are missing or inputs are bad.
States reported to /api/health; never crash the app. -->

TBD

## 9. Performance

<!-- Measured latency/FPS on CPU and GPU (machine + numbers), memory, bottlenecks. -->

TBD

## 10. Testing

<!-- How to run the tests; what they cover; model tests (@pytest.mark.model) and fixtures. -->

TBD

## 11. Evaluation & verification results

<!-- Numbers on OUR footage (precision/recall, accuracy), dataset description, date, commit. -->

TBD

## 12. Troubleshooting / FAQ

<!-- Symptom -> cause -> fix entries learned during development. -->

TBD

## 13. Known limitations & future work

<!-- Honest list of what does not work and what you would do next. -->

TBD

## 14. Changelog

<!-- Date - PR - change. Newest first. Updated in every PR. -->

- 2026-10-07 - boilerplate - module doc created from the template (Marc).
