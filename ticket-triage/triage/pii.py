"""Redact obvious PII before ticket text is sent to any external model."""
from __future__ import annotations


import re

_PATTERNS = [
    ("CARD", re.compile(r"\b(?:\d[ -]?){13,16}\b")),
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    ("PHONE", re.compile(r"(?<!\w)\+?\d{1,3}[\s.-]?\(?\d{2,4}\)?[\s.-]?\d{3}[\s.-]?\d{3,4}(?!\w)")),
]


def redact(text: str) -> tuple[str, list[str]]:
    """Return (redacted_text, list_of_pii_types_found)."""
    found: list[str] = []
    for name, pattern in _PATTERNS:
        if pattern.search(text):
            found.append(name)
            text = pattern.sub(f"[{name}]", text)
    return text, found
