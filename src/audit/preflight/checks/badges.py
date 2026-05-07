"""Trust-mark badge detection + staleness flags.

Scans homepage + /security + /trust for badge alt-text + image src markers.
Norton/McAfee/TRUSTe-original mark stale: a real trust program would have
migrated to the current vendor brand (NortonLifeLock, McAfee→Trellix,
TRUSTe→TrustArc).
"""
from __future__ import annotations

import re
from typing import Any

import httpx
from bs4 import BeautifulSoup


_PAGES = ("", "/security", "/trust")

# (vendor, regex, stale_marker)
_BADGE_PATTERNS: tuple[tuple[str, str, bool], ...] = (
    ("soc2",                   r"\bsoc[\s\-]?2\b",                      False),
    ("iso_27001",              r"\biso[\s\-]?27001\b",                  False),
    ("bbb",                    r"\b(?:bbb|better[\s\-]business[\s\-]bureau)\b", False),
    ("dpf_privacy_shield",     r"\b(?:dpf|privacy[\s\-]shield)\b",      False),
    ("norton",                 r"\b(?:norton|symantec)\b",              True),
    ("mcafee",                 r"\bmcafee\b",                           True),
    ("truste_original",        r"\btruste\b(?!arc)",                    True),
)


async def _fetch(client: httpx.AsyncClient, url: str) -> str:
    try:
        resp = await client.get(url)
        if resp.status_code != 200:
            return ""
        return resp.text
    except httpx.HTTPError:
        return ""


def _scan_page(url: str, html: str) -> list[dict[str, Any]]:
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    # Concatenate alt-text + img src + a-href for low-cost text matching.
    haystack_parts: list[str] = []
    for img in soup.find_all("img"):
        for attr in ("alt", "src", "title"):
            v = img.get(attr)
            if isinstance(v, str):
                haystack_parts.append(v)
    for a in soup.find_all("a"):
        href = a.get("href")
        if isinstance(href, str):
            haystack_parts.append(href)
    haystack = " ".join(haystack_parts).lower()

    detected: list[dict[str, Any]] = []
    for vendor, pattern, stale in _BADGE_PATTERNS:
        if re.search(pattern, haystack, flags=re.IGNORECASE):
            entry: dict[str, Any] = {"vendor": vendor, "evidence_url": url}
            location = "footer" if "footer" in haystack else "page"
            entry["location"] = location
            if stale:
                entry["stale"] = True
            detected.append(entry)
    return detected


async def check(domain: str) -> dict:
    base = f"https://{domain.strip().rstrip('/')}"
    detected: list[dict[str, Any]] = []
    seen_vendors: set[str] = set()

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        for path in _PAGES:
            url = base + path
            html = await _fetch(client, url)
            for entry in _scan_page(url, html):
                if entry["vendor"] not in seen_vendors:
                    detected.append(entry)
                    seen_vendors.add(entry["vendor"])

    stale_vendors = sorted(
        {e["vendor"] for e in detected if e.get("stale")}
    )
    return {
        "detected": detected,
        "stale_vendors_present": stale_vendors,
    }
