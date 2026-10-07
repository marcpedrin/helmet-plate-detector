"""Validate module docs in docs/modules/ against the 14-section template.

Usage:
    python scripts/check_docs.py            # headings present and in order
    python scripts/check_docs.py --strict   # + every section has >= 2 content lines and no TBD

Stub docs: a module doc containing the marker ``<!-- doc-status: stub -->`` is checked
for headings only, even with --strict (reported as STUB). Owners delete the marker in
their first feature PR; from then on the doc must pass strict mode.
Exit code 1 with a per-file report when any check fails.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULES_DIR = REPO_ROOT / "docs" / "modules"
STUB_MARKER = "<!-- doc-status: stub -->"

HEADINGS = [
    "1. Purpose & scope",
    "2. Owner & files",
    "3. Architecture",
    "4. Public interface",
    "5. Configuration",
    "6. Dependencies, models & licenses",
    "7. Algorithms & design decisions",
    "8. Failure modes & fallbacks",
    "9. Performance",
    "10. Testing",
    "11. Evaluation & verification results",
    "12. Troubleshooting / FAQ",
    "13. Known limitations & future work",
    "14. Changelog",
]


def _strip_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def check_file(path: Path, strict: bool) -> tuple[list[str], bool]:
    """Return (problems, is_stub) for one module doc."""
    text = path.read_text(encoding="utf-8")
    is_stub = STUB_MARKER in text
    problems: list[str] = []
    found = [m.group(1).strip() for m in re.finditer(r"^## +(.+?)\s*$", text, flags=re.MULTILINE)]
    numbered = [h for h in found if re.match(r"^\d+\. ", h)]
    missing = [h for h in HEADINGS if h not in numbered]
    if missing:
        problems.append(f"missing headings: {missing}")
    present = [h for h in numbered if h in HEADINGS]
    if present != [h for h in HEADINGS if h in present]:
        problems.append("headings out of order")
    if strict and not is_stub and not missing:
        sections = re.split(r"^## +.+$", text, flags=re.MULTILINE)
        titles = re.findall(r"^## +(.+?)\s*$", text, flags=re.MULTILINE)
        for title, body in zip(titles, sections[1:], strict=False):
            if title.strip() not in HEADINGS:
                continue
            content = [ln for ln in _strip_comments(body).splitlines() if ln.strip()]
            if len(content) < 2:
                problems.append(f"'{title}': needs >= 2 non-empty, non-comment lines (has {len(content)})")
            if re.search(r"\bTBD\b", "\n".join(content)):
                problems.append(f"'{title}': contains TBD")
    return problems, is_stub


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    files = sorted(p for p in MODULES_DIR.glob("*.md") if p.name != "_TEMPLATE.md")
    if not files:
        print(f"no module docs found in {MODULES_DIR}")
        return 1
    failed = 0
    for path in files:
        problems, is_stub = check_file(path, args.strict)
        rel = path.relative_to(REPO_ROOT).as_posix()
        if problems:
            failed += 1
            print(f"FAIL {rel}")
            for p in problems:
                print(f"     - {p}")
        else:
            tag = "STUB" if is_stub and args.strict else "OK  "
            print(f"{tag} {rel}")
    mode = "strict" if args.strict else "headings"
    print(f"\n{len(files) - failed}/{len(files)} module docs pass ({mode} mode)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
