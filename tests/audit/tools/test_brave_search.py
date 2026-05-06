"""Tests for src/audit/tools/brave_search — lens #157 prerequisite."""
from __future__ import annotations

import json

import httpx
import pytest
import respx

from src.audit.tools.brave_search import (
    BRAVE_WEB_SEARCH_URL,
    BraveSearchClient,
)


@pytest.mark.asyncio
async def test_no_key_returns_degraded() -> None:
    c = BraveSearchClient(api_key="")
    r = await c.web_search("hello")
    assert r["degraded"] is True
    assert "BRAVE_API_KEY" in r["degraded_reason"]
    assert r["query"] == "hello"
    assert r["results"] == []


@pytest.mark.asyncio
async def test_2xx_payload_projects_correctly() -> None:
    payload = {
        "web": {
            "results": [
                {
                    "title": "Page One",
                    "url": "https://a.com",
                    "description": "First result.",
                    "age": "2 days ago",
                    "language": "en",
                    "page_age": "2026-05-04",
                    "profile": {"name": "A site"},
                },
                {
                    "title": "Page Two",
                    "url": "https://b.com",
                    "description": "Second result.",
                },
            ],
            "results_count": 12345,
        },
        "mixed": {"main": [{"type": "web", "index": 0}, {"type": "news", "index": 0}]},
    }

    with respx.mock(assert_all_called=True) as router:
        router.get(BRAVE_WEB_SEARCH_URL).mock(
            return_value=httpx.Response(200, json=payload)
        )
        c = BraveSearchClient(api_key="key123")
        r = await c.web_search("test", count=15)

    assert r["degraded"] is False
    assert r["http_status"] == 200
    assert r["query"] == "test"
    assert r["params"]["count"] == 15
    assert len(r["results"]) == 2
    assert r["results"][0]["title"] == "Page One"
    assert r["results"][0]["profile"] == "A site"
    assert r["total_estimated"] == 12345
    assert len(r["mixed_results"]) == 2


@pytest.mark.asyncio
async def test_http_error_returns_degraded() -> None:
    with respx.mock(assert_all_called=True) as router:
        router.get(BRAVE_WEB_SEARCH_URL).mock(
            return_value=httpx.Response(401, text="bad key")
        )
        c = BraveSearchClient(api_key="bad")
        r = await c.web_search("test")

    assert r["degraded"] is True
    assert "401" in r["degraded_reason"]
    assert r["http_status"] == 401


@pytest.mark.asyncio
async def test_429_rate_limit_returns_degraded() -> None:
    with respx.mock() as router:
        router.get(BRAVE_WEB_SEARCH_URL).mock(
            return_value=httpx.Response(429, text="slow down")
        )
        c = BraveSearchClient(api_key="k")
        r = await c.web_search("test")
    assert r["degraded"] is True
    assert r["http_status"] == 429


@pytest.mark.asyncio
async def test_network_error_returns_degraded() -> None:
    with respx.mock() as router:
        router.get(BRAVE_WEB_SEARCH_URL).mock(
            side_effect=httpx.ConnectError("DNS fail")
        )
        c = BraveSearchClient(api_key="k")
        r = await c.web_search("test")
    assert r["degraded"] is True
    assert "ConnectError" in r["degraded_reason"]


@pytest.mark.asyncio
async def test_non_json_response_returns_degraded() -> None:
    with respx.mock() as router:
        router.get(BRAVE_WEB_SEARCH_URL).mock(
            return_value=httpx.Response(200, text="not json {")
        )
        c = BraveSearchClient(api_key="k")
        r = await c.web_search("test")
    assert r["degraded"] is True
    assert "non-JSON" in r["degraded_reason"]


@pytest.mark.asyncio
async def test_count_clamped_to_brave_max() -> None:
    """Brave caps at 20 results per call; we clamp before sending."""
    with respx.mock() as router:
        route = router.get(BRAVE_WEB_SEARCH_URL).mock(
            return_value=httpx.Response(200, json={"web": {"results": []}})
        )
        c = BraveSearchClient(api_key="k")
        await c.web_search("q", count=999)
    assert route.calls.last.request.url.params["count"] == "20"


@pytest.mark.asyncio
async def test_subscription_token_header_sent() -> None:
    with respx.mock() as router:
        route = router.get(BRAVE_WEB_SEARCH_URL).mock(
            return_value=httpx.Response(200, json={"web": {"results": []}})
        )
        c = BraveSearchClient(api_key="MY-KEY")
        await c.web_search("q")
    sent_headers = route.calls.last.request.headers
    assert sent_headers["X-Subscription-Token"] == "MY-KEY"
    assert "GoFreddy-Audit" in sent_headers["User-Agent"]
