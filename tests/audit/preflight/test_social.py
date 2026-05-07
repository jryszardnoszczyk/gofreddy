"""Tests for src/audit/preflight/checks/social.py."""
from __future__ import annotations

import httpx
import pytest
import respx

from src.audit.preflight.checks.social import check


_HOMEPAGE = """
<html><head>
<meta property="og:title" content="Acme">
<meta property="og:description" content="Doing things">
<meta property="og:image" content="https://acme.test/og.png">
<meta property="og:url" content="https://acme.test/">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://acme.test/tw.png">
<meta name="twitter:site" content="@acme">
</head></html>
"""


@pytest.mark.asyncio
@respx.mock
async def test_full_meta_score_high():
    respx.get("https://acme.test/").mock(return_value=httpx.Response(200, text=_HOMEPAGE))
    respx.get("https://acme.test/pricing").mock(return_value=httpx.Response(200, text=_HOMEPAGE))
    respx.get("https://acme.test/about").mock(return_value=httpx.Response(200, text=_HOMEPAGE))

    result = await check("acme.test")
    assert result["open_graph"]["og:title"]["present_on"] == 3
    assert result["open_graph"]["og:image"]["present_on"] == 3
    assert "https://acme.test/og.png" in result["open_graph"]["og:image"]["image_urls"]
    assert result["twitter_card"]["twitter:card"]["values"] == {"summary_large_image": 3}
    assert result["twitter_card"]["twitter:site"]["handle"] == "@acme"
    assert result["share_card_quality_score"] >= 90


@pytest.mark.asyncio
@respx.mock
async def test_no_meta_returns_empty():
    respx.get("https://x.test/").mock(return_value=httpx.Response(200, text="<html></html>"))
    respx.get("https://x.test/pricing").mock(return_value=httpx.Response(404))
    respx.get("https://x.test/about").mock(return_value=httpx.Response(404))

    result = await check("x.test")
    assert result["share_card_quality_score"] == 0
    assert result["twitter_card"]["twitter:site"]["handle"] is None
