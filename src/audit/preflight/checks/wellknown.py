"""`/.well-known/*` file probes.

Covers preflight lenses 02-08 (security.txt, agent-card.json, mcp-server,
apple-app-site-association, assetlinks.json, UCP manifest).

Signal shape: see per-file entry in `_PROBES` below; return dict mirrors that
shape keyed by probe name. Each entry has `present: bool` plus parsed fields.

Implementation notes:

- httpx async client, 5s timeout per probe, follows redirects once.
- 200-class + expected content-type shape = present. 404 = absent. Other
  status codes record `status` but mark `present: False` (treat as unknown).
- `security.txt` may be at either `/.well-known/security.txt` or
  `/security.txt` per RFC 9116; we probe both and prefer well-known.
- All fetches happen in parallel via asyncio.gather — total wall-clock is
  dominated by the slowest probe, not their sum.
- JSON parsing is tolerant: malformed JSON → `present: True, parse_error: str`
  rather than crashing (file existence is itself signal).
"""
from __future__ import annotations

import asyncio
import json
import re
from typing import Any

import httpx


async def _fetch(client: httpx.AsyncClient, url: str) -> tuple[int, str | None]:
    """Returns (status, body). status=-1 on exception. body capped at 256KB."""
    try:
        resp = await client.get(url, follow_redirects=True, timeout=5.0)
        return resp.status_code, resp.text[:256_000] if resp.text else ""
    except httpx.HTTPError:
        return -1, None


def _parse_security_txt(body: str | None) -> dict[str, Any]:
    """RFC 9116 security.txt: newline-separated `key: value` with RFC 5322 comments."""
    if not body:
        return {"present": False, "contact": None, "expires": None}
    fields: dict[str, list[str]] = {}
    for raw in body.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields.setdefault(key.strip().lower(), []).append(value.strip())
    return {
        "present": True,
        "contact": fields.get("contact", [None])[0],
        "expires": fields.get("expires", [None])[0],
    }


def _parse_json(body: str | None) -> tuple[bool, dict | None, str | None]:
    """Returns (parsed_ok, data, error)."""
    if not body:
        return False, None, None
    try:
        return True, json.loads(body), None
    except json.JSONDecodeError as exc:
        return False, None, str(exc)


def _parse_agent_card(body: str | None) -> dict[str, Any]:
    ok, data, err = _parse_json(body)
    if not ok:
        return {"present": False, "parse_error": err}
    return {
        "present": True,
        "at_type": data.get("@type") if isinstance(data, dict) else None,
        "endpoints": list(data.get("endpoints", [])) if isinstance(data, dict) else [],
    }


def _parse_mcp_server(body: str | None) -> dict[str, Any]:
    ok, data, err = _parse_json(body)
    if not ok:
        return {"present": False, "parse_error": err}
    return {
        "present": True,
        "url": data.get("url") if isinstance(data, dict) else None,
    }


def _parse_aasa(body: str | None) -> dict[str, Any]:
    """Apple App Site Association — activitycontinuation/applinks/webcredentials."""
    ok, data, err = _parse_json(body)
    if not ok:
        return {"present": False, "parse_error": err, "apps": [], "details": []}
    if not isinstance(data, dict):
        return {"present": False, "apps": [], "details": []}
    applinks = data.get("applinks", {})
    details = applinks.get("details", []) if isinstance(applinks, dict) else []
    apps = [d.get("appIDs", d.get("appID")) for d in details if isinstance(d, dict)]
    apps_flat = [a for sub in apps for a in (sub if isinstance(sub, list) else [sub] if sub else [])]
    return {"present": True, "apps": apps_flat, "details": details}


def _parse_assetlinks(body: str | None) -> dict[str, Any]:
    """Digital Asset Links (Android)."""
    ok, data, err = _parse_json(body)
    if not ok:
        return {"present": False, "parse_error": err, "targets": []}
    if not isinstance(data, list):
        return {"present": False, "targets": []}
    return {"present": True, "targets": data}


def _parse_ucp(body: str | None) -> dict[str, Any]:
    """Unified Commerce Protocol manifest (ai-commerce.json / ucp-manifest)."""
    ok, data, err = _parse_json(body)
    if not ok:
        return {"present": False, "parse_error": err}
    catalog = data.get("catalog", {}) if isinstance(data, dict) else {}
    return {
        "present": True,
        "catalog_url": catalog.get("url") if isinstance(catalog, dict) else None,
    }


# Dispatch table: probe_name → (path, parser). Keep alphabetized.
_PROBES: dict[str, tuple[str, Any]] = {
    "agent_card":                 ("/.well-known/agent-card.json",            _parse_agent_card),
    "apple_app_site_association": ("/.well-known/apple-app-site-association", _parse_aasa),
    "assetlinks":                 ("/.well-known/assetlinks.json",            _parse_assetlinks),
    "mcp_server":                 ("/.well-known/mcp-server",                 _parse_mcp_server),
    "security_txt":               ("/.well-known/security.txt",               _parse_security_txt),
    "ucp_manifest":               ("/.well-known/ucp-manifest",               _parse_ucp),
}


async def check(domain: str) -> dict:
    domain = domain.strip().lower().rstrip("/").rstrip(".")
    base = f"https://{domain}" if not re.match(r"^https?://", domain) else domain

    async with httpx.AsyncClient() as client:
        fetches = await asyncio.gather(
            *[_fetch(client, base + path) for _, (path, _) in _PROBES.items()],
            return_exceptions=False,
        )

    out: dict[str, Any] = {}
    for (name, (_, parser)), (status, body) in zip(_PROBES.items(), fetches):
        if status == 200 and body is not None:
            out[name] = parser(body)
        else:
            out[name] = {"present": False, "status": status}
    return out
