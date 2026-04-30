"""Brand-asset probes: logo, color, robots, sitemap.

Part of the LHR-design-doc 8-module taxonomy under `brand-assets`. Covers
the cross-surface-consistency signals Stage-2 Narrative agent needs.

Expected signal shape:

    {
        "logo": {
            "src_urls":        [str],
            "distinct_hashes": int,     # >1 = logo-version sprawl
            "formats":         [str],   # ["svg", "png", ...]
        },
        "brand_colors": {
            "primary":   str | None,    # extracted from CSS custom properties / logo
            "secondary": str | None,
            "css_source": str | None,   # which stylesheet declared it
        },
        "robots_txt": {
            "present":           bool,
            "disallow_count":    int,
            "sitemap_urls":      [str],
            "ai_bot_policies": {str: "allow"|"disallow"|"unspecified"},  # GPTBot, ClaudeBot, etc.
        },
        "sitemap": {
            "urls_discovered": int,     # caveat: capped — we don't crawl the full tree here
            "nested_sitemaps": int,
            "preflight_adversarial_flag": bool,  # True if urls > 500 — feeds plan-002 preflight_check
        },
    }

Implementation note (v1): `robots.txt` is a plain-text fetch. Sitemap parsing
via `lxml` (XML or gzipped XML). Logo extraction: fetch homepage, find
`<link rel="icon">` + `<img>` tags in header / footer / nav, hash via sha256.
Color extraction: regex `--brand|--primary|--color-primary` in CSS custom
property declarations. Cheap proxies — no image processing in v1.
"""
from __future__ import annotations


async def check(domain: str) -> dict:
    # TODO(v1-step-C): implement via httpx + lxml + hashlib + regex.
    return {"implemented": False}
