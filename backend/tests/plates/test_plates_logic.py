"""Pure-logic tests for the plate module (no weights needed)."""

import numpy as np
import pytest

from app.core.types import PlateDetection, PlateObservation, PlateRead, PlateStatus
from app.plates.indian_format import correct, is_valid, normalize, pretty
from app.plates.ocr import assemble_lines
from app.plates.voting import PlateVoter


@pytest.mark.parametrize(
    "raw,expected,valid",
    [
        ("KA01AB1234", "KA01AB1234", True),
        ("KAO1AB1234", "KA01AB1234", True),
        ("ka-01 ab 1234", "KA01AB1234", True),
        ("INDKA01AB1234", "KA01AB1234", True),
        ("22BH1234AB", "22BH1234AB", True),
        ("DL3CAB1234", "DL3CAB1234", True),
        ("KA0lAB1234", "KA01AB1234", True),
        ("XX01AB1234", "XX01AB1234", False),
        ("KA01", "KA01", False),
    ],
)
def test_correct(raw, expected, valid):
    assert correct(raw) == (expected, valid)


def test_normalize_and_pretty():
    assert normalize(" mh 12-de 1433 ") == "MH12DE1433"
    assert is_valid("MH12DE1433")
    assert pretty("KA01AB1234") == "KA 01 AB 1234"
    assert pretty("22BH1234AB") == "22 BH 1234 AB"


def test_assemble_two_lines():
    boxes = [[[40, 70], [140, 70], [140, 110], [40, 110]], [[2, 15], [166, 15], [166, 57], [2, 57]]]
    text, conf = assemble_lines(boxes, ["1234", "KA01AB"], [1.0, 0.9])
    assert text == "KA01AB1234"
    assert 0.9 < conf <= 1.0


def _obs(text=None, conf=0.8, det=True):
    crop = np.zeros((20, 60, 3), np.uint8)
    read = None
    if text is not None:
        t, v = correct(text)
        read = PlateRead(text, t, conf, v)
    return PlateObservation(PlateDetection((0, 0, 60, 20), 0.9) if det else None, read, crop if det else None)


def test_voter_states():
    v = PlateVoter()
    assert v.result().status == PlateStatus.PENDING
    v.add(_obs(det=False))
    assert v.result().status == PlateStatus.NOT_DETECTED
    v.add(_obs())
    assert v.result().status == PlateStatus.UNREADABLE
    v.add(_obs("KA01AB1234"))
    v.add(_obs("KA01AB1234"))
    v.add(_obs("KA01AB1Z34", 0.5))
    r = v.result()
    assert (r.status, r.text, r.votes) == (PlateStatus.READ, "KA01AB1234", 3)  # 1Z34 is corrected to 1234
    assert v.ocr_count == 3
    assert v.best_crop() is not None


def test_voter_single_confident_read():
    v = PlateVoter()
    v.add(_obs("MH12DE1433", 0.95))
    assert v.result().status == PlateStatus.READ
    w = PlateVoter()
    w.add(_obs("MH12DE1433", 0.7))
    assert w.result().status == PlateStatus.UNREADABLE
