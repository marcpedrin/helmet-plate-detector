# Contributing

## Branches

`main` is protected and always runs. Work on:

| Pattern | Use |
|---|---|
| `feature/<area>` | `feature/backend-camera`, `feature/helmet-detection`, `feature/plate-ocr`, `feature/frontend-dashboard`, `feature/pipeline`, `feature/integration` |
| `fix/<area>-<desc>` | bug fixes |
| `contracts/<desc>` | contract changes only (see below) |
| `docs/<desc>` | docs-only changes |

## Commits

[Conventional Commits](https://www.conventionalcommits.org): `type(scope): summary`

- types: `feat` `fix` `refactor` `test` `docs` `chore` `perf`
- scopes: `camera` `storage` `helmet` `plates` `pipeline` `api` `realtime` `frontend` `contracts` `docs` `ci`

Example: `feat(plates): add Indian-format correction for BH series`.

## Pull requests

- Open a **draft PR early**; mark it ready when its "open PR when" criterion in [OWNERSHIP.md](docs/OWNERSHIP.md) is met.
- Aim for ≤ ~600 changed lines; split otherwise.
- CI green; **touch only paths you own**; fill in the PR template checklist.
- ≥ 1 approval: Marc approves all PRs; Marc's PRs need any one teammate.
- **Squash merge**; delete the branch after merge.

## Keeping in sync

```bash
git fetch origin && git rebase origin/main      # at least twice a day, and before opening a PR
git push --force-with-lease                      # only on your own branch
```

## Conflicts

- **In a file you own**: resolve it.
- **In a file you don't own**: keep `main`'s version. During a rebase, `--ours` = main and `--theirs` = your commit:

  ```bash
  git checkout --ours <file> && git add <file>
  git diff origin/main -- <file>     # must print nothing
  git rebase --continue
  ```

  Then tell the owner what you needed. Never "fix" someone else's module in your PR.

## Contract changes

A separate `contracts/<desc>` PR that touches **only** `backend/app/core/*.py`, `frontend/src/types/contracts.ts`
and `docs/CONTRACTS.md`. Marc merges it; everyone rebases.

## Tests

- Backend: `cd backend && ruff check . && pytest -m "not model"` must pass (CI runs exactly this).
  Tests needing weights are marked `@pytest.mark.model` and skip when weights are missing.
- Frontend: `cd frontend && npm run lint && npm run typecheck && npm test && npm run build`.
- Mock mode must keep working: `APP_MODE=mock` + `python scripts/smoke_test.py`.

## Documentation (Definition of Done)

Every PR:

- updates the owner's `docs/modules/<module>.md`, including its **Changelog**;
- adds an ADR (`docs/adr/NNNN-<owner>-<kebab-title>.md`) for any non-trivial decision;
- keeps ruff `D` (docstrings) and eslint `jsdoc` (TSDoc) green;
- passes `python scripts/check_docs.py` (CI uses `--strict` for ready PRs and `main`; remove your doc's
  `doc-status: stub` marker in your first feature PR).

Reviewers reject PRs with stale docs. Docs are written alongside the code, not at the end. Standard:
[docs/DOCUMENTATION.md](docs/DOCUMENTATION.md).

## Hard rules

- **No ML imports at module top level.** Never import `torch`, `ultralytics`, `rapidocr`, `open_image_models` or
  `onnxruntime` at the top of a module; import inside loader functions/constructors. Mock mode and CI run without them.
- **Factories never raise.** They return a fallback with `state=NOT_LOADED|ERROR` and log the reason.
- **No generated files in feature branches**: `graphify-out/`, `frontend/dist/`, `evidence/`, `data/`.
  Only Marc regenerates `graphify-out/`, on `main`, after merges (generated files cause merge conflicts).
- **No weights, videos or evidence in git** (`*.pt`, `*.onnx`, `*.mp4`, `evidence/*`, `data/*`, `.env`).

## Merge order

1. `feature/backend-camera` (real videos + SQLite)
2. `feature/frontend-dashboard` (Harish)
3. `feature/helmet-detection` (Prajwal)
4. `feature/plate-ocr` (Malik)
5. `feature/pipeline` (Marc: real detection loop)
6. `feature/integration` (tuning on real footage, demo hardening)

Log each merge in [docs/INTEGRATION_LOG.md](docs/INTEGRATION_LOG.md).
