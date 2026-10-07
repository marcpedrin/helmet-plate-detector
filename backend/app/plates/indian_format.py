"""Indian number-plate normalisation, OCR-confusion correction and validation.

Pure functions, no ML imports.

Supported formats (examples): ``KA01AB1234``, ``KA01A1234``, ``DL3CAF0001``,
``DL01CAB1234``, ``MH12DE1433``, old ``MH121234``, BH-series ``22BH1234AA``.

Correction works by fitting the cleaned OCR string to letter/digit templates of the
same length and swapping commonly confused glyphs per position (``O<->0``, ``I<->1``,
``B<->8``, ``S<->5`` ...). The template that needs the fewest substitutions and yields
a valid state code wins.
"""

from __future__ import annotations

import re

STATE_CODES = frozenset(
    "AN AP AR AS BR CG CH DD DL DN GA GJ HP HR JH JK KA KL LA LD MH ML MN MP MZ NL OD OR PB PY "
    "RJ SK TN TR TS TG UK UA UP WB".split()
)

# WHY: ordered by how common the layout is; ties in substitution count go to the earlier one.
TEMPLATES: tuple[str, ...] = (
    "LLDDLLDDDD",  # KA01AB1234
    "LLDDLDDDD",  # KA01A1234
    "LLDDLLLDDDD",  # DL01CAB1234
    "LLDLLLDDDD",  # DL3CAB1234
    "LLDLLDDDD",  # DL3CA1234
    "LLDDDDDD",  # MH121234 (old, no series)
    "DDBHDDDDLL",  # 22BH1234AB
    "DDBHDDDDL",  # 22BH1234A
)

TO_DIGIT = {
    "O": "0", "Q": "0", "D": "0", "U": "0", "I": "1", "L": "1", "J": "1",
    "Z": "2", "S": "5", "B": "8", "G": "6", "T": "7", "A": "4",
}
TO_LETTER = {"0": "O", "1": "I", "2": "Z", "5": "S", "8": "B", "6": "G", "7": "T", "4": "A"}

MAX_SUBSTITUTIONS = 2

_STANDARD = re.compile(r"^[A-Z]{2}\d{1,2}[A-Z]{0,3}\d{4}$")
_BH = re.compile(r"^\d{2}BH\d{4}[A-Z]{1,2}$")


def normalize(text: str) -> str:
    """Upper-case and strip everything except ``A-Z0-9`` (``"ka-01 ab 1234"`` -> ``"KA01AB1234"``).

    Also drops the vertical ``IND`` mark printed on HSRP plates when OCR reads it as a prefix.
    """
    t = re.sub(r"[^A-Z0-9]", "", (text or "").upper())
    if t.startswith("IND") and len(t) - 3 >= 8:
        t = t[3:]
    return t


def is_valid(text: str) -> bool:
    """Return True if ``text`` (already normalised) matches an Indian plate pattern."""
    if _BH.match(text):
        return True
    if _STANDARD.match(text) and text[:2] in STATE_CODES:
        # WHY: only Delhi uses single-digit district codes (DL3CAB1234); elsewhere a
        # single digit there is an OCR error, so rejecting it forces the 2-digit reading.
        if text[3].isalpha() and text[:2] != "DL":
            return False
        return any(_fits(text, tpl) for tpl in TEMPLATES if tpl[0] == "L")
    return False


def _fits(text: str, template: str) -> bool:
    if len(text) != len(template):
        return False
    for ch, kind in zip(text, template, strict=True):
        if kind == "L" and not ch.isalpha():
            return False
        if kind == "D" and not ch.isdigit():
            return False
        if kind not in "LD" and ch != kind:
            return False
    return True


def _apply(text: str, template: str) -> tuple[str, int] | None:
    """Coerce ``text`` into ``template``; return (result, substitutions) or None if impossible."""
    out: list[str] = []
    subs = 0
    for ch, kind in zip(text, template, strict=True):
        if kind == "D":
            if ch.isdigit():
                out.append(ch)
            elif ch in TO_DIGIT:
                out.append(TO_DIGIT[ch])
                subs += 1
            else:
                return None
        elif kind == "L":
            if ch.isalpha():
                out.append(ch)
            elif ch in TO_LETTER:
                out.append(TO_LETTER[ch])
                subs += 1
            else:
                return None
        else:  # literal (e.g. the "BH" of BH-series)
            if ch == kind:
                out.append(ch)
            elif TO_LETTER.get(ch) == kind:
                out.append(kind)
                subs += 1
            else:
                return None
    return "".join(out), subs


def correct(text: str) -> tuple[str, bool]:
    """Fix position-dependent OCR confusions (``O<->0``, ``I<->1``, ``B<->8``, ``S<->5`` ...).

    Args:
        text: Raw OCR text.

    Returns:
        ``(corrected_text, valid_format)``. If no template fits within
        ``MAX_SUBSTITUTIONS`` the cleaned text is returned with ``valid_format=False``.
    """
    cleaned = normalize(text)
    candidates: list[tuple[int, int, str]] = []
    for prio, tpl in enumerate(TEMPLATES):
        if len(tpl) != len(cleaned):
            continue
        res = _apply(cleaned, tpl)
        if res is None:
            continue
        fixed, subs = res
        if subs <= MAX_SUBSTITUTIONS and is_valid(fixed):
            candidates.append((subs, prio, fixed))
    if not candidates:
        return cleaned, False
    candidates.sort()
    return candidates[0][2], True


def pretty(text: str) -> str:
    """Format a normalised plate with spaces (``KA01AB1234`` -> ``KA 01 AB 1234``)."""
    m = re.match(r"^(\d{2})(BH)(\d{4})([A-Z]{1,2})$", text)
    if m:
        return " ".join(m.groups())
    m = re.match(r"^([A-Z]{2})(\d{1,2})([A-Z]{0,3})(\d{4})$", text)
    if m:
        return " ".join(g for g in m.groups() if g)
    return text
