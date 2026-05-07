"""Tests for src/audit/preflight/checks/badges.py."""
from __future__ import annotations

import httpx
import pytest
import respx

from src.audit.preflight.checks.badges import check


@pytest.mark.asyncio
@respx.mock
async def test_detects_soc2_iso_and_stale_norton():
    html = """
<html><body>
<footer>
  <img alt="SOC 2 Type II Certified" src="/badges/soc2.png">
  <img alt="ISO 27001" src="/badges/iso.png">
  <a href="/security?norton-secured=true">Norton Secured</a>
</footer>
</body></html>
"""
    respx.get("https://acme.test/").mock(return_value=httpx.Response(200, text=html))
    respx.get("https://acme.test/security").mock(return_value=httpx.Response(404))
    respx.get("https://acme.test/trust").mock(return_value=httpx.Response(404))

    result = await check("acme.test")
    vendors = {entry["vendor"] for entry in result["detected"]}
    assert "soc2" in vendors
    assert "iso_27001" in vendors
    assert "norton" in vendors
    assert "norton" in result["stale_vendors_present"]
    assert "soc2" not in result["stale_vendors_present"]


@pytest.mark.asyncio
@respx.mock
async def test_no_badges_returns_empty():
    respx.get("https://x.test/").mock(return_value=httpx.Response(200, text="<html></html>"))
    respx.get("https://x.test/security").mock(return_value=httpx.Response(404))
    respx.get("https://x.test/trust").mock(return_value=httpx.Response(404))

    result = await check("x.test")
    assert result["detected"] == []
    assert result["stale_vendors_present"] == []
