"""`/.well-known/*` file probes.

Covers preflight lenses 02-08 (security.txt, agent-card.json, mcp-server,
apple-app-site-association, assetlinks.json, UCP manifest).

Expected signal shape:

    {
        "security_txt":               {"present": bool, "contact": str | None, "expires": str | None},
        "agent_card":                 {"present": bool, "@type": str | None, "endpoints": list[str]},
        "mcp_server":                 {"present": bool, "url": str | None},
        "apple_app_site_association": {"present": bool, "apps": list[str], "details": list[dict]},
        "assetlinks":                 {"present": bool, "targets": list[dict]},
        "ucp_manifest":               {"present": bool, "catalog_url": str | None},
    }

Implementation note (v1): httpx async client, single-try 5s timeout each,
follow redirects once. Probe `https://<domain>/.well-known/<file>` — 200+JSON
= present; 404 = absent; other = record the status but mark absent.
"""
from __future__ import annotations


async def check(domain: str) -> dict:
    # TODO(v1-step-C): implement via httpx async client.
    return {"implemented": False}
