# Documentation standard

Every owner documents their module **while** building it. No PR merges with stale docs.

## Four layers

1. **Code**: docstrings (Python, Google style, enforced by ruff `D`) and TSDoc (enforced by
   `eslint-plugin-jsdoc`) on everything public: what it does, Args/Returns/Raises, thread-safety.
   Put a `# WHY:` (or `# NOTE:`) comment on every threshold and heuristic. Graphify indexes these as rationale nodes.
2. **Module doc**: one per owner in [`docs/modules/`](modules/), built from [`_TEMPLATE.md`](modules/_TEMPLATE.md)
   (14 fixed sections, checked by `scripts/check_docs.py`).
3. **ADRs**: one file per non-trivial decision in [`docs/adr/`](adr/), named `NNNN-<owner>-<kebab-title>.md`, from
   [`0000-template.md`](adr/0000-template.md). Owners only *add* ADR files, so there are no conflicts.
4. **PR descriptions**: the [PR template](../.github/pull_request_template.md) (what, why, how verified, screenshots).

## How to write a good module doc (checklist)

- [ ] Section 4 matches the code exactly (copy signatures; don't paraphrase).
- [ ] Every `.env` key you read is in section 5 with default, unit and tuning advice.
- [ ] Every threshold has a reason (section 7) and a `# WHY:` comment in code.
- [ ] Section 8 says what `/api/health` shows when your module degrades.
- [ ] Section 9 and 11 contain **measured numbers** on **our** footage, with date and commit.
- [ ] Diagrams are Mermaid or images under `docs/images/<module>/`.
- [ ] The Changelog (section 14) has a line for this PR.
- [ ] No `TBD` left and the `doc-status: stub` marker removed (then `check_docs.py --strict` must pass).

## Definition of Done (every PR)

- Owner's `docs/modules/<module>.md` updated, including its Changelog.
- ADR added for any non-trivial decision.
- ruff `D` and eslint `jsdoc` green on new code.
- `python scripts/check_docs.py` passes (CI runs `--strict` on ready PRs and on `main`).
- Reviewers reject PRs whose docs are stale.
