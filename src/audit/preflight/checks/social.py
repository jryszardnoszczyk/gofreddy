"""OpenGraph + Twitter Card meta validation.

Samples homepage + /pricing + /about. Counts presence of og:title,
og:description, og:image, og:type, og:url, twitter:card, twitter:image,
twitter:site across pages. Doesn't dimension-check OG images (would
require fetching each); ``dimensions_ok`` field is left at 0 in v1 with
Stage-2 free to extend.
"""
from __future__ import annotations

from typing import Any

import httpx
from bs4 import BeautifulSoup


_PAGES = ("", "/pricing", "/about")


async def _fetch_meta(client: httpx.AsyncClient, url: str) -> dict[str, str]:
    """Returns flat dict of meta-tag name/property → content for one page."""
    try:
        resp = await client.get(url)
        if resp.status_code != 200:
            return {}
    except httpx.HTTPError:
        return {}
    soup = BeautifulSoup(resp.text, "html.parser")
    out: dict[str, str] = {}
    for tag in soup.find_all("meta"):
        key = tag.get("property") or tag.get("name")
        content = tag.get("content")
        if key and content and isinstance(key, str) and isinstance(content, str):
            out.setdefault(key.lower(), content)
    return out


def _count_present(metas: list[dict[str, str]], key: str) -> tuple[int, int]:
    present = sum(1 for m in metas if key in m)
    return present, len(metas) - present


async def check(domain: str) -> dict:
    base = f"https://{domain.strip().rstrip('/')}"
    pages_sampled: list[str] = []
    metas: list[dict[str, str]] = []

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        for path in _PAGES:
            url = base + path
            meta = await _fetch_meta(client, url)
            if meta:
                pages_sampled.append(url)
                metas.append(meta)

    og_title_p, og_title_m = _count_present(metas, "og:title")
    og_desc_p, og_desc_m = _count_present(metas, "og:description")
    og_image_p, og_image_m = _count_present(metas, "og:image")
    og_image_urls = list({m["og:image"] for m in metas if "og:image" in m})

    og_type_values: dict[str, int] = {}
    for m in metas:
        v = m.get("og:type")
        if v:
            og_type_values[v] = og_type_values.get(v, 0) + 1

    og_url_self_ref = any(
        m.get("og:url", "").startswith(base) for m in metas
    )

    twitter_card_values: dict[str, int] = {}
    for m in metas:
        v = m.get("twitter:card")
        if v:
            twitter_card_values[v] = twitter_card_values.get(v, 0) + 1

    twitter_image_p, twitter_image_m = _count_present(metas, "twitter:image")
    twitter_image_urls = list({m["twitter:image"] for m in metas if "twitter:image" in m})
    twitter_site = next((m["twitter:site"] for m in metas if "twitter:site" in m), None)

    # Deterministic share-card-quality heuristic — 0-100 from observed signal.
    score = 0
    if og_title_p == len(metas) and metas:
        score += 25
    if og_desc_p == len(metas) and metas:
        score += 25
    if og_image_p == len(metas) and metas:
        score += 25
    if twitter_card_values:
        score += 15
    if og_url_self_ref:
        score += 10

    return {
        "pages_sampled": pages_sampled,
        "open_graph": {
            "og:title": {"present_on": og_title_p, "missing_on": og_title_m},
            "og:description": {"present_on": og_desc_p, "missing_on": og_desc_m},
            "og:image": {
                "present_on": og_image_p,
                "missing_on": og_image_m,
                "image_urls": og_image_urls,
                "dimensions_ok": 0,
            },
            "og:type": {"values": og_type_values},
            "og:url": {"self_reference_ok": og_url_self_ref},
        },
        "twitter_card": {
            "twitter:card": {"values": twitter_card_values},
            "twitter:image": {
                "present_on": twitter_image_p,
                "image_urls": twitter_image_urls,
            },
            "twitter:site": {"handle": twitter_site},
        },
        "share_card_quality_score": score,
    }
