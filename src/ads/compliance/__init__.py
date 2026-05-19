"""Ad-engine compliance primitives (U15 / TD-42)."""
from pathlib import Path

import yaml

from src.ads.compliance.anti_patterns import (
    AntiPatternHit,
    cap_score_from_hits,
    find_anti_pattern_hits,
)


_BANNED_TERMS_PATH = Path(__file__).resolve().parent / "banned_terms.yaml"


def load_banned_terms() -> dict:
    """Load banned_terms.yaml from disk."""
    return yaml.safe_load(_BANNED_TERMS_PATH.read_text(encoding="utf-8"))


def text_violates_meta_health(text: str) -> list[str]:
    """Return list of banned Meta health-vertical words in `text`."""
    import re
    banned = load_banned_terms()
    words = banned.get("meta_health_vertical", {}).get("banned_words", [])
    hits: list[str] = []
    for word in words:
        if re.search(rf"\b{re.escape(word)}\b", text, re.IGNORECASE):
            hits.append(word)
    return hits


def text_violates_linkedin_aggressive(text: str) -> list[str]:
    """Return list of banned LinkedIn aggressive-promotional phrases in `text`."""
    banned = load_banned_terms()
    phrases = banned.get("linkedin_aggressive_promotional", {}).get("banned_phrases", [])
    hits: list[str] = []
    text_lower = text.lower()
    for phrase in phrases:
        if phrase.lower() in text_lower:
            hits.append(phrase)
    return hits


def text_violates_guaranteed_results(text: str) -> bool:
    """True if `text` matches any 'guaranteed N% results' regex."""
    import re
    banned = load_banned_terms()
    patterns = banned.get("guaranteed_n_pct_results", {}).get("regex_patterns", [])
    for pattern in patterns:
        try:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        except re.error:
            continue
    return False


__all__ = [
    "AntiPatternHit",
    "cap_score_from_hits",
    "find_anti_pattern_hits",
    "load_banned_terms",
    "text_violates_guaranteed_results",
    "text_violates_linkedin_aggressive",
    "text_violates_meta_health",
]
