"""Evaluate plate detection + OCR on our own footage.  Owner: Malik.

Must do (to implement):
  * Load labelled frames/crops with ground-truth plate text from
    ``backend/tests/fixtures/plates/`` or a ``--data`` folder.
  * Run ``app.plates.load_plate_service`` (live models): detection recall, OCR exact-match
    and character accuracy before/after ``indian_format.correct``, and voting accuracy over
    N frames per plate.
  * Report latency per detection/OCR call and a threshold sweep for ``PLATE_DETECTOR_CONF``.
  * Write a markdown report to stdout (paste into docs/modules/plates.md section 11).
"""

from __future__ import annotations

import sys


def main() -> int:
    print("eval_plates.py: not implemented yet (owner: Malik). See the module docstring.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
