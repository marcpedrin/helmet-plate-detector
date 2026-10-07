"""Evaluate the helmet classifier on our own footage.  Owner: Prajwal.

Must do (to implement):
  * Load a small labelled set (rider crops or frames + YOLO-format labels) from
    ``backend/tests/fixtures/helmet/`` or a ``--data`` folder.
  * Run ``app.helmet.load_helmet_classifier`` (live weights) via ``classify_batch``.
  * Report per-class precision / recall, confusion matrix (HELMET / NO_HELMET / UNKNOWN),
    mean latency per batch on CPU and GPU, and threshold sweep for ``HELMET_CONF``.
  * Write a markdown report to stdout (paste into docs/modules/helmet.md section 11).
"""

from __future__ import annotations

import sys


def main() -> int:
    print("eval_helmet.py: not implemented yet (owner: Prajwal). See the module docstring.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
