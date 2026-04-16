"""Shared text sanitization for external/user-generated content.

Defends against indirect prompt injection (OWASP LLM01) when external
text flows back into Gemini via workspace/canvas/tool results.
"""

from __future__ import annotations

import re
import unicodedata

_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f-\x9f]")
_ZERO_WIDTH = re.compile(r"[\u200b\u200c\u200d\ufeff]")

# Indirect prompt injection defense (OWASP LLM01).
_INJECTION_PATTERN = re.compile(
    r"(ignore\s+(previous|above|all)\s+instructions"
    r"|you\s+are\s+now"
    r"|system\s*:\s*"
    r"|<\s*/?\s*system\s*>"
    r"|<\s*/?\s*\|system\|\s*>"
    r"|<<\s*SYS\s*>>"
    r"|\[INST\]"
    r"|<\|im_start\|>\s*system"
    r"|```\s*system"
    r"|(?:^|\n)\s*IMPORTANT\s*:"
    r"|(?:^|\n)\s*New\s+task\s*:"
    r"|Actually,?\s+do\s+this\s+instead"
    r"|<\s*/?\s*user_input\s*>)",
    re.IGNORECASE,
)


def sanitize_external(text: str | None, max_len: int = 200) -> str:
    """Strip injection patterns and truncate external text."""
    if not text:
        return ""
    cleaned = _CONTROL_CHARS.sub("", text)
    cleaned = unicodedata.normalize("NFKC", cleaned)
    cleaned = _ZERO_WIDTH.sub("", cleaned)
    cleaned = _INJECTION_PATTERN.sub("[FILTERED]", cleaned)
    if len(cleaned) > max_len:
        return cleaned[:max_len] + "..."
    return cleaned


def escape_braces(text: str) -> str:
    """Escape curly braces so str.format() treats them as literal characters.

    Must be applied to any user-controlled string *before* it is interpolated
    via ``TEMPLATE.format(...)``.  Without this, input like ``{bad_key}``
    raises ``KeyError`` and may leak user content into exception tracebacks.
    """
    return text.replace("{", "{{").replace("}", "}}")
