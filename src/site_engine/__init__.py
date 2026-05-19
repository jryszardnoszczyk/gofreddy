"""Site-engine primitives (R27-R34 / U15b).

Top-level package for the site_engine lane's substrate-level primitives:
- `sanitizer.py`           — nh3-backed allowlist HTML sanitizer
- `brand_tokens.py`        — Pydantic schema + loader for tokens.json
- `reviewer_diff_capture.py` — TD-43 reviewer-feedback edit-diff job stub
- `edit_category_clusterer.py` — TD-43 v1.3 placeholder (deferred)
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
