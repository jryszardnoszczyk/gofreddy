"""HTTP security + privacy header inspection.

Samples homepage + /pricing + /about. HEAD-then-GET fallback (some sites 405
on HEAD). Captures HSTS, CSP, X-Frame-Options, Referrer-Policy,
Permissions-Policy, COOP, COEP. Doesn't grade strictness — Stage-2 agents
interpret. Failures return the documented shape with `present: False`
across the board so Stage-1a's aggregator never sees a missing key.
"""
from __future__ import annotations

import re
from typing import Any

import httpx


_PAGES = ("", "/pricing", "/about")


def _parse_hsts(value: str | None) -> dict[str, Any]:
    if not value:
        return {"present": False, "max_age": None, "preload": False}
    m = re.search(r"max-age\s*=\s*(\d+)", value, flags=re.IGNORECASE)
    return {
        "present": True,
        "max_age": int(m.group(1)) if m else None,
        "preload": "preload" in value.lower(),
    }


def _parse_csp(value: str | None, report_only: bool = False) -> dict[str, Any]:
    if not value:
        return {"present": False, "report_only": report_only, "directives": []}
    directives = [d.strip() for d in value.split(";") if d.strip()]
    return {"present": True, "report_only": report_only, "directives": directives}


def _parse_simple(value: str | None) -> dict[str, Any]:
    return {"present": bool(value), "value": value}


def _parse_permissions_policy(value: str | None) -> dict[str, Any]:
    if not value:
        return {"present": False, "features_restricted": []}
    # Permissions-Policy uses "feature=()" syntax for restrictions.
    restricted = re.findall(r"([a-z\-]+)\s*=\s*\(\s*\)", value, flags=re.IGNORECASE)
    return {"present": True, "features_restricted": restricted}


def _empty_signal(pages: list[str]) -> dict[str, Any]:
    return {
        "pages_sampled": pages,
        "strict_transport_security": {"present": False, "max_age": None, "preload": False},
        "content_security_policy": {"present": False, "report_only": False, "directives": []},
        "x_frame_options": {"present": False, "value": None},
        "referrer_policy": {"present": False, "value": None},
        "permissions_policy": {"present": False, "features_restricted": []},
        "coop": {"present": False, "value": None},
        "coep": {"present": False, "value": None},
    }


async def check(domain: str) -> dict:
    base = f"https://{domain.strip().rstrip('/')}"
    pages_sampled: list[str] = []
    headers_seen: dict[str, str] = {}

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        for path in _PAGES:
            url = base + path
            try:
                resp = await client.head(url)
                if resp.status_code == 405:
                    resp = await client.get(url)
            except httpx.HTTPError:
                continue
            pages_sampled.append(url)
            # First successful page wins for header capture (homepage usually
            # has the broadest CSP). Subsequent pages can be cross-checked
            # by Stage-2 if needed.
            for key, val in resp.headers.items():
                headers_seen.setdefault(key.lower(), val)

    if not pages_sampled:
        return _empty_signal([])

    csp_value = headers_seen.get("content-security-policy")
    csp_report_only_value = headers_seen.get("content-security-policy-report-only")

    return {
        "pages_sampled": pages_sampled,
        "strict_transport_security": _parse_hsts(headers_seen.get("strict-transport-security")),
        "content_security_policy": (
            _parse_csp(csp_value, report_only=False)
            if csp_value
            else _parse_csp(csp_report_only_value, report_only=True)
        ),
        "x_frame_options": _parse_simple(headers_seen.get("x-frame-options")),
        "referrer_policy": _parse_simple(headers_seen.get("referrer-policy")),
        "permissions_policy": _parse_permissions_policy(headers_seen.get("permissions-policy")),
        "coop": _parse_simple(headers_seen.get("cross-origin-opener-policy")),
        "coep": _parse_simple(headers_seen.get("cross-origin-embedder-policy")),
    }
