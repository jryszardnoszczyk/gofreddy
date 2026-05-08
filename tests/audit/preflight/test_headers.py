"""Tests for src/audit/preflight/checks/headers.py."""
from __future__ import annotations

import httpx
import pytest
import respx

from src.audit.preflight.checks.headers import check


@pytest.mark.asyncio
@respx.mock
async def test_strict_homepage_returns_full_signal():
    respx.head("https://example.test/").mock(
        return_value=httpx.Response(
            200,
            headers={
                "Strict-Transport-Security": "max-age=31536000; preload",
                "Content-Security-Policy": "default-src 'self'; img-src 'self' data:",
                "X-Frame-Options": "DENY",
                "Referrer-Policy": "no-referrer",
                "Permissions-Policy": "geolocation=(), camera=()",
                "Cross-Origin-Opener-Policy": "same-origin",
                "Cross-Origin-Embedder-Policy": "require-corp",
            },
        )
    )
    respx.head("https://example.test/pricing").mock(return_value=httpx.Response(200, headers={}))
    respx.head("https://example.test/about").mock(return_value=httpx.Response(200, headers={}))

    result = await check("example.test")
    assert result["strict_transport_security"]["present"] is True
    assert result["strict_transport_security"]["max_age"] == 31536000
    assert result["strict_transport_security"]["preload"] is True
    assert result["content_security_policy"]["present"] is True
    assert result["content_security_policy"]["report_only"] is False
    assert "default-src 'self'" in result["content_security_policy"]["directives"]
    assert result["x_frame_options"]["value"] == "DENY"
    assert result["referrer_policy"]["value"] == "no-referrer"
    assert "geolocation" in result["permissions_policy"]["features_restricted"]
    assert result["coop"]["value"] == "same-origin"


@pytest.mark.asyncio
@respx.mock
async def test_head_405_falls_back_to_get():
    respx.head("https://example.test/").mock(return_value=httpx.Response(405))
    respx.get("https://example.test/").mock(
        return_value=httpx.Response(200, headers={"X-Frame-Options": "SAMEORIGIN"}),
    )
    respx.head("https://example.test/pricing").mock(return_value=httpx.Response(404))
    respx.head("https://example.test/about").mock(return_value=httpx.Response(404))

    result = await check("example.test")
    assert result["x_frame_options"]["value"] == "SAMEORIGIN"


@pytest.mark.asyncio
@respx.mock
async def test_no_pages_reachable_returns_empty_signal():
    respx.head("https://example.test/").mock(side_effect=httpx.ConnectError("offline"))
    respx.head("https://example.test/pricing").mock(side_effect=httpx.ConnectError("offline"))
    respx.head("https://example.test/about").mock(side_effect=httpx.ConnectError("offline"))

    result = await check("example.test")
    assert result["pages_sampled"] == []
    assert result["strict_transport_security"]["present"] is False
    assert result["content_security_policy"]["present"] is False
