# Plates & OCR

Owner: Malik (@malikrehanmulla1048) - `feature/plate-ocr`

<!-- doc-status: stub -->
<!-- Delete the marker above in your first feature PR; CI then enforces check_docs.py --strict. -->

## 1. Purpose & scope

<!-- What this module does and explicitly does NOT do.
One paragraph; link the ARCHITECTURE.md diagram node it implements. -->

Detects the number plate inside a rider motorcycle region, reads it with RapidOCR, corrects to Indian formats and votes across frames.
Does NOT decide when to read plates (the pipeline schedules OCR within its budget).

## 2. Owner & files

<!-- Owner name + GitHub handle, branch, and every file/dir owned (paths).
List tests and fixtures too. -->

`backend/app/plates/{__init__,detector,ocr,indian_format,voting,service,mock,download}.py`, `backend/models/plates/`, `scripts/eval_plates.py`
Tests: `backend/tests/plates/`; fixtures: `backend/tests/fixtures/plates/`.

## 3. Architecture

<!-- Internal structure: classes, threads, data flow. Prefer a Mermaid diagram.
Save screenshots/diagrams in docs/images/<module>/. -->

TBD

## 4. Public interface

<!-- Exact signatures callers rely on (copy from code), inputs/outputs, thread-safety.
Any change here needs a contracts/* PR. -->

```python
load_plate_service(settings) -> PlateServiceProtocol   # never raises
service.observe(frame, rider, run_ocr=True, exclude=()) -> PlateObservation
service.new_voter() -> PlateVoterProtocol  (add / result / best_crop / ocr_count)
indian_format.normalize(text); correct(text) -> (text, valid); is_valid(text) -> bool
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
