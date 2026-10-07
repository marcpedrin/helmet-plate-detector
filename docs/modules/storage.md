# Storage

Owner: Marc, Codex stream (@marcpedrin) - `feature/backend-camera`

<!-- doc-status: stub -->
<!-- Delete the marker above in your first feature PR; CI then enforces check_docs.py --strict. -->

## 1. Purpose & scope

<!-- What this module does and explicitly does NOT do.
One paragraph; link the ARCHITECTURE.md diagram node it implements. -->

Persists violations in SQLite and evidence JPEGs on disk; retention purge.
Does NOT decide what is a violation (pipeline).

## 2. Owner & files

<!-- Owner name + GitHub handle, branch, and every file/dir owned (paths).
List tests and fixtures too. -->

`backend/app/storage/{database,evidence_store,repository}.py`
Tests: `backend/tests/storage/` (contract tests every repository must pass).

## 3. Architecture

<!-- Internal structure: classes, threads, data flow. Prefer a Mermaid diagram.
Save screenshots/diagrams in docs/images/<module>/. -->

TBD

## 4. Public interface

<!-- Exact signatures callers rely on (copy from code), inputs/outputs, thread-safety.
Any change here needs a contracts/* PR. -->

```python
create_repository(settings) -> ViolationRepositoryProtocol
repo.create(event) -> ViolationOut; repo.update_plate(id, plate, crop) -> ViolationOut
repo.get(id); repo.list(camera_id, limit, offset) -> ViolationPage; repo.counts(); repo.purge_older_than(days) -> int
EvidenceStore(root).save(camera_id, violation_id, kind, image) -> url
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
