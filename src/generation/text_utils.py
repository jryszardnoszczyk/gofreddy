"""Text utilities for video generation — filler word removal."""

import re

_FILLER_PATTERNS_EN = re.compile(
    r"\b(?:um|uh|erm|like,?\s|you know,?\s|basically,?\s|I mean,?\s|sort of,?\s|kind of,?\s|right,?\s|actually,?\s)\b",
    re.IGNORECASE,
)


def strip_fillers(text: str, language: str = "en") -> str:
    """Remove filler words from text. Only English supported initially."""
    if language != "en":
        return text
    cleaned = _FILLER_PATTERNS_EN.sub("", text)
    return re.sub(r" {2,}", " ", cleaned).strip()
