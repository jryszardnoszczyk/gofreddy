"""MarTech stack fingerprinting.

Regex over homepage HTML for vendor signatures + HEAD-probe convention
trust-page URLs. v1 detects the most common vendors per category;
Stage-2 Experience agent can extend if a prospect uses something exotic.
"""
from __future__ import annotations

import re
from typing import Any

import httpx


# Each entry: category → ((vendor, regex), ...). First match wins per category.
_FINGERPRINTS: dict[str, tuple[tuple[str, str], ...]] = {
    "cmp": (
        ("OneTrust",   r"\bonetrust\b|cookielaw"),
        ("Cookiebot",  r"\bcookiebot\b"),
        ("Iubenda",    r"\biubenda\b"),
        ("Osano",      r"\bosano\b"),
        ("CookieYes",  r"\bcookieyes\b"),
        ("TrustArc",   r"\btrustarc\b"),
    ),
    "tag_manager": (
        ("GTM",        r"googletagmanager\.com|gtm\.js"),
        ("Tealium",    r"\btealium\b|utag\.js"),
        ("Piwik",      r"\bpiwik\b|matomo"),
    ),
    "cdp": (
        ("Segment",     r"cdn\.segment\.com|analytics\.js"),
        ("RudderStack", r"rudderlabs\b|rudderanalytics"),
        ("Hightouch",   r"\bhightouch\b"),
    ),
    "product_analytics": (
        ("Amplitude", r"\bamplitude\b"),
        ("Mixpanel",  r"\bmixpanel\b"),
        ("PostHog",   r"\bposthog\b"),
        ("Heap",      r"\bheap(?:analytics)?\b"),
    ),
    "session_replay": (
        ("Hotjar",     r"\bhotjar\b|static\.hotjar"),
        ("FullStory",  r"\bfullstory\b"),
        ("Mouseflow",  r"\bmouseflow\b"),
        ("LogRocket",  r"\blogrocket\b"),
    ),
    "cro_tooling": (
        ("Optimizely",  r"\boptimizely\b"),
        ("VWO",         r"\bvisualwebsiteoptimizer\b|\bvwo\b"),
        ("Intellimize", r"\bintellimize\b"),
    ),
    "ab_testing": (
        ("GoogleOptimize", r"google-optimize|optimize\.google"),
        ("Convert",        r"\bconvert\.com\b"),
    ),
    "booking": (
        ("Calendly",        r"\bcalendly\b"),
        ("SavvyCal",        r"\bsavvycal\b"),
        ("HubSpotMeetings", r"meetings\.hubspot"),
        ("Chili Piper",     r"\bchilipiper\b"),
    ),
    "forms": (
        ("HubSpotForms", r"hsforms\.net|js\.hsforms"),
        ("Typeform",     r"\btypeform\b"),
        ("Tally",        r"\btally\.so\b"),
        ("Marketo",      r"\bmarketo\b"),
    ),
    "esp": (
        ("CustomerIO",   r"customer\.io|cdp\.customer\.io"),
        ("Klaviyo",      r"\bklaviyo\b"),
        ("Braze",        r"\bbraze\b"),
        ("Iterable",     r"\biterable\b"),
        ("Mailchimp",    r"\bmailchimp\b|chimpstatic"),
    ),
}


_TRUST_PAGE_PATHS: dict[str, str] = {
    "sub_processor_url":  "/sub-processors",
    "status_page_url":    "/status",
    "public_roadmap_url": "/roadmap",
    "ir_page_url":        "/investors",
    "press_kit_url":      "/press",
}


def _detect_category(html: str, patterns: tuple[tuple[str, str], ...]) -> dict[str, Any]:
    for vendor, pattern in patterns:
        m = re.search(pattern, html, flags=re.IGNORECASE)
        if m:
            return {"vendor": vendor, "evidence": m.group(0)}
    return {"vendor": None, "evidence": None}


async def _head_or_get_200(client: httpx.AsyncClient, url: str) -> bool:
    """Returns True if URL responds 200. HEAD first, fall back to GET."""
    try:
        resp = await client.head(url)
        if resp.status_code == 405:
            resp = await client.get(url)
        return resp.status_code == 200
    except httpx.HTTPError:
        return False


async def check(domain: str) -> dict:
    base = f"https://{domain.strip().rstrip('/')}"
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        try:
            resp = await client.get(base)
            html = resp.text if resp.status_code == 200 else ""
        except httpx.HTTPError:
            html = ""

        result: dict[str, Any] = {}
        for category, patterns in _FINGERPRINTS.items():
            result[category] = _detect_category(html, patterns)

        # Vendor sprawl — count >1 detection across analytics/cdps.
        analytics_signals = sum(
            1 for cat in ("product_analytics", "session_replay")
            if result[cat]["vendor"] is not None
        )
        cdp_signals = 1 if result["cdp"]["vendor"] is not None else 0
        chat_signals = 1 if re.search(r"\b(intercom|drift|zendesk|crisp)\b", html, flags=re.IGNORECASE) else 0
        result["vendor_sprawl_flags"] = {
            "analytics": analytics_signals,
            "cdps": cdp_signals,
            "chats": chat_signals,
        }

        # Trust-page URL convention probes
        trust_pages: dict[str, str | None] = {}
        for key, path in _TRUST_PAGE_PATHS.items():
            url = base + path
            trust_pages[key] = url if await _head_or_get_200(client, url) else None
        result["trust_pages"] = trust_pages

    return result
