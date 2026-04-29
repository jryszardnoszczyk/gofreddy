"""Tests for src/audit/preflight/checks/schema.py."""
from __future__ import annotations

import httpx
import pytest
import respx

from src.audit.preflight.checks.schema import check


_HOMEPAGE_HTML = """
<html><head>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {"@id": "#org", "@type": "Organization", "name": "Acme"},
    {"@id": "#site", "@type": "WebSite", "url": "https://acme.test",
     "potentialAction": {"@type": "SearchAction", "target": "https://acme.test/?q={query}"}}
  ]
}
</script>
</head><body>x</body></html>
"""


@pytest.mark.asyncio
@respx.mock
async def test_extracts_types_and_search_action():
    respx.get("https://acme.test/").mock(return_value=httpx.Response(200, text=_HOMEPAGE_HTML))
    respx.get("https://acme.test/about").mock(return_value=httpx.Response(404))
    respx.get("https://acme.test/pricing").mock(return_value=httpx.Response(404))

    result = await check("acme.test")
    assert "Organization" in result["types_present"]
    assert "WebSite" in result["types_present"]
    assert result["at_graph_composability"] is True
    assert result["search_action"] is True
    assert result["errors"] == []


@pytest.mark.asyncio
@respx.mock
async def test_malformed_jsonld_recorded_in_errors():
    bad_html = '<html><head><script type="application/ld+json">{not json</script></head></html>'
    respx.get("https://x.test/").mock(return_value=httpx.Response(200, text=bad_html))
    respx.get("https://x.test/about").mock(return_value=httpx.Response(404))
    respx.get("https://x.test/pricing").mock(return_value=httpx.Response(404))

    result = await check("x.test")
    assert result["types_present"] == []
    assert len(result["errors"]) == 1


@pytest.mark.asyncio
@respx.mock
async def test_breadcrumbs_detected_on_subpage():
    breadcrumb_html = """
<html><head>
<script type="application/ld+json">
{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": []}
</script>
</head></html>
"""
    respx.get("https://x.test/").mock(return_value=httpx.Response(200, text="<html></html>"))
    respx.get("https://x.test/about").mock(return_value=httpx.Response(200, text=breadcrumb_html))
    respx.get("https://x.test/pricing").mock(return_value=httpx.Response(404))

    result = await check("x.test")
    assert result["breadcrumbs"] is True
