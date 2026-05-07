"""Tests for src/audit/preflight/checks/tooling.py."""
from __future__ import annotations

import httpx
import pytest
import respx

from src.audit.preflight.checks.tooling import check


_HOMEPAGE = """
<html><head>
<script src="https://www.googletagmanager.com/gtm.js?id=GTM-ABC"></script>
<script src="https://cdn.segment.com/analytics.js/v1/x/analytics.min.js"></script>
<script>amplitude.getInstance().init("KEY");</script>
<script src="https://static.hotjar.com/c/hotjar-12345.js"></script>
<link rel="stylesheet" href="//cdn.cookiebot.com/cb.css">
<script src="https://js.hsforms.net/forms/v2.js"></script>
</head><body>
<div id="intercom-container"></div>
</body></html>
"""


@pytest.mark.asyncio
@respx.mock
async def test_detects_common_martech():
    respx.get("https://acme.test").mock(return_value=httpx.Response(200, text=_HOMEPAGE))
    # Trust-page probes — return mixed
    respx.head("https://acme.test/sub-processors").mock(return_value=httpx.Response(200))
    respx.head("https://acme.test/status").mock(return_value=httpx.Response(404))
    respx.head("https://acme.test/roadmap").mock(return_value=httpx.Response(404))
    respx.head("https://acme.test/investors").mock(return_value=httpx.Response(404))
    respx.head("https://acme.test/press").mock(return_value=httpx.Response(404))

    result = await check("acme.test")
    assert result["tag_manager"]["vendor"] == "GTM"
    assert result["cdp"]["vendor"] == "Segment"
    assert result["product_analytics"]["vendor"] == "Amplitude"
    assert result["session_replay"]["vendor"] == "Hotjar"
    assert result["cmp"]["vendor"] == "Cookiebot"
    assert result["forms"]["vendor"] == "HubSpotForms"
    assert result["vendor_sprawl_flags"]["analytics"] >= 1
    assert result["vendor_sprawl_flags"]["chats"] == 1  # intercom-container in DOM
    assert result["trust_pages"]["sub_processor_url"] == "https://acme.test/sub-processors"
    assert result["trust_pages"]["status_page_url"] is None


@pytest.mark.asyncio
@respx.mock
async def test_no_tooling_returns_empty():
    respx.get("https://x.test").mock(return_value=httpx.Response(200, text="<html></html>"))
    for path in ("/sub-processors", "/status", "/roadmap", "/investors", "/press"):
        respx.head(f"https://x.test{path}").mock(return_value=httpx.Response(404))

    result = await check("x.test")
    assert result["tag_manager"]["vendor"] is None
    assert result["cdp"]["vendor"] is None
    assert result["vendor_sprawl_flags"]["chats"] == 0
    assert all(v is None for v in result["trust_pages"].values())
