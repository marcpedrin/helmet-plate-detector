"""Indian number-plate normalisation, OCR-confusion correction and validation.

Owner: Malik. Signatures are final; bodies are pending. Pure functions, no ML imports.

Formats to support (examples): ``KA01AB1234``, ``DL3CAF0001``, ``MH12DE1433``,
BH-series ``22BH1234AA``.
"""

from __future__ import annotations


def normalize(text: str) -> str:
    """Upper-case and strip everything except ``A-Z0-9`` (``"ka-01 ab 1234"`` -> ``"KA01AB1234"``)."""
    raise NotImplementedError("Malik: implement normalize")


def correct(text: str) -> tuple[str, bool]:
    """Fix position-dependent OCR confusions (``O<->0``, ``I<->1``, ``B<->8``, ``S<->5`` ...).

    Args:
        text: Raw OCR text.

    Returns:
        ``(corrected_text, valid_format)`` where ``valid_format`` is :func:`is_valid` of
        the corrected text.
    """
    raise NotImplementedError("Malik: implement correct")


def is_valid(text: str) -> bool:
    """Return True if ``text`` (already normalised) matches an Indian plate pattern."""
    raise NotImplementedError("Malik: implement is_valid")
