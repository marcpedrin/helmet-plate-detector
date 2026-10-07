# Pipeline

Owner: Marc (@marcpedrin) - `feature/pipeline`

<!-- doc-status: stub -->
<!-- Delete the marker above in your first feature PR; CI then enforces check_docs.py --strict. -->

## 1. Purpose & scope

<!-- What this module does and explicitly does NOT do.
One paragraph; link the ARCHITECTURE.md diagram node it implements. -->

Per-camera processing: YOLO26n detect + ByteTrack, rider association, helmet classification, temporal violation engine, best evidence frame, plate collection, persistence and events. Mock mode uses `MockRunner`.
Does NOT decode video (camera), run helmet/plate models (helmet/plates) or serve HTTP (api).

## 2. Owner & files

<!-- Owner name + GitHub handle, branch, and every file/dir owned (paths).
List tests and fixtures too. -->

`backend/app/pipeline/{detector,association,violation_engine,evidence,overlay,runner,mock_runner}.py`
Tests: `backend/tests/pipeline/`; fixtures: `backend/tests/fixtures/pipeline/`.

## 3. Architecture

<!-- Internal structure: classes, threads, data flow. Prefer a Mermaid diagram.
Save screenshots/diagrams in docs/images/<module>/. -->

TBD

## 4. Public interface

<!-- Exact signatures callers rely on (copy from code), inputs/outputs, thread-safety.
Any change here needs a contracts/* PR. -->

```python
ObjectTracker(settings, camera_id).update(frame) -> list[Track]
associate_riders(tracks, frame_w, frame_h) -> list[Rider]
ViolationEngine(settings, camera_id).update(packet, riders, helmets) -> list[EngineDecision]
EvidenceSelector().offer(packet, rider, helmet); .build(rider_id) -> EvidenceBundle | None
PipelineRunner(settings, cameras, helmet, plates, repository, publisher, stats_fn).start() / stop() / metrics(cid)
MockRunner(cameras, repository, publisher, stats_fn, interval_s, plate_delay_s)
```

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
