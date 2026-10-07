## Summary

<!-- What changed and why. Link the issue / ADR. -->

**Owner area:** camera | storage | helmet | plates | pipeline | api/realtime | frontend | contracts | docs | ci

## How I verified it

<!-- Commands run, outputs, eval numbers. -->

## Checklist

- [ ] Only paths I own are touched (see docs/OWNERSHIP.md)
- [ ] Tests added/updated and passing (`pytest -m "not model"` / `npm test`)
- [ ] `docs/modules/<module>.md` updated, **including its Changelog**
- [ ] ADR added in `docs/adr/` if a non-trivial decision was made
- [ ] Docstrings / TSDoc on all new public code (ruff `D`, eslint `jsdoc` green)
- [ ] `python scripts/check_docs.py` passes
- [ ] Mock mode still runs (`APP_MODE=mock` + `python scripts/smoke_test.py`)
- [ ] No weights, videos, evidence, data, `.env`, `graphify-out/` or `dist/` committed
- [ ] Contract unchanged **or** the `contracts/*` PR is linked: #
- [ ] Screenshots attached for UI changes
