"""Tests for src/audit/preflight/checks/assets.py."""
from __future__ import annotations

import httpx
import pytest
import respx

from src.audit.preflight.checks.assets import check


_ROBOTS = """
User-agent: *
Disallow: /admin
Disallow: /private

User-agent: GPTBot
Disallow: /

User-agent: ClaudeBot
Allow: /

Sitemap: https://acme.test/sitemap.xml
"""

_SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset>
  <url><loc>https://acme.test/</loc></url>
  <url><loc>https://acme.test/pricing</loc></url>
</urlset>
"""

_HOMEPAGE = """
<html><head>
<link rel="icon" href="/favicon.ico">
</head><body>
<header><img src="/logo.svg" alt="Acme"></header>
</body></html>
"""


@pytest.mark.asyncio
@respx.mock
async def test_extracts_robots_sitemap_logo():
    respx.get("https://acme.test/").mock(return_value=httpx.Response(200, text=_HOMEPAGE))
    respx.get("https://acme.test/robots.txt").mock(return_value=httpx.Response(200, text=_ROBOTS))
    respx.get("https://acme.test/sitemap.xml").mock(return_value=httpx.Response(200, text=_SITEMAP))
    # Logo fetches return small bytes
    respx.get("https://acme.test/favicon.ico").mock(return_value=httpx.Response(200, content=b"icon-bytes"))
    respx.get("https://acme.test/logo.svg").mock(return_value=httpx.Response(200, content=b"<svg/>"))

    result = await check("acme.test")
    assert result["robots_txt"]["present"] is True
    assert result["robots_txt"]["disallow_count"] == 3  # /admin, /private, /
    assert result["robots_txt"]["sitemap_urls"] == ["https://acme.test/sitemap.xml"]
    assert result["robots_txt"]["ai_bot_policies"]["GPTBot"] == "disallow"
    assert result["robots_txt"]["ai_bot_policies"]["ClaudeBot"] == "allow"
    assert result["robots_txt"]["ai_bot_policies"]["PerplexityBot"] == "unspecified"
    assert result["sitemap"]["urls_discovered"] == 2
    assert "/favicon.ico" in result["logo"]["src_urls"][0] or "/logo.svg" in result["logo"]["src_urls"][0]
    assert "svg" in result["logo"]["formats"] or "ico" in result["logo"]["formats"]


@pytest.mark.asyncio
@respx.mock
async def test_no_robots_no_sitemap_returns_empty_blocks():
    respx.get("https://x.test/").mock(return_value=httpx.Response(200, text="<html></html>"))
    respx.get("https://x.test/robots.txt").mock(return_value=httpx.Response(404))
    respx.get("https://x.test/sitemap.xml").mock(return_value=httpx.Response(404))

    result = await check("x.test")
    assert result["robots_txt"]["present"] is False
    assert result["robots_txt"]["disallow_count"] == 0
    assert result["sitemap"]["urls_discovered"] == 0
