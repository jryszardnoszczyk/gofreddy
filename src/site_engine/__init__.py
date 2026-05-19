"""Site-engine primitives (R27-R34 / U15b).

Top-level package for the site_engine lane's substrate-level primitives:
- `sanitizer.py`     — nh3-backed allowlist HTML sanitizer
- `brand_tokens.py`  — Pydantic schema + loader for tokens.json

Per CLAUDE.md Rule 2: the TD-43 reviewer-feedback capture machinery
(reviewer_diff_capture.py + edit_category_clusterer.py) was deleted
on the CE-review cleanup pass — those modules were v1.3 scaffolding
with zero v1 consumers + an explicit ~6-month deferred trigger
condition. Restore when the trigger condition actually fires per
the v1.3 backlog.
"""
from src.site_engine.brand_tokens import (
    BrandTokens,
    BrandTokensNotFoundError,
    load_brand_tokens,
)
from src.site_engine.sanitizer import (
    SanitizerDelta,
    SanitizerResult,
    sanitize_section_html,
)

__all__ = [
    "BrandTokens",
    "BrandTokensNotFoundError",
    "SanitizerDelta",
    "SanitizerResult",
    "load_brand_tokens",
    "sanitize_section_html",
]
