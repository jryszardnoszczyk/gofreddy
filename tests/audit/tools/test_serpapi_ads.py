"""Tests for src/audit/tools/serpapi_ads — Adyntel live fallback."""
from __future__ import annotations

import httpx
import pytest
import respx

from src.audit.tools.serpapi_ads import (
    SERPAPI_BASE_URL,
    SerpApiAdsClient,
)


@pytest.mark.asyncio
async def test_no_key_returns_degraded() -> None:
    c = SerpApiAdsClient(api_key="")
    r = await c.advertiser_lookup(advertiser_id="AR123")
    assert r["degraded"] is True
    assert "SERPAPI_KEY" in r["degraded_reason"]


@pytest.mark.asyncio
async def test_advertiser_lookup_2xx_full_payload() -> None:
    payload = {
        "advertisers": [{
            "advertiser_id": "AR123",
            "name": "ACME Corp",
            "domain": "acme.com",
            "verified": True,
            "region": "US",
            "link": "https://...",
        }],
        "ad_creatives": [
            {
                "creative_id": "C1",
                "ad_format": "image",
                "first_seen": "2026-01-15",
                "last_seen": "2026-04-30",
                "destination_url": "https://acme.com/landing",
                "preview_url": "https://serpapi.com/preview/C1",
                "advertiser_id": "AR123",
            },
            {
                "ad_id": "C2",
                "format": "video",
                "date_started": "2026-03-01",
                "domain": "acme.com",
            },
        ],
    }
    with respx.mock() as router:
        router.get(SERPAPI_BASE_URL).mock(
            return_value=httpx.Response(200, json=payload)
        )
        c = SerpApiAdsClient(api_key="key123")
        r = await c.advertiser_lookup(advertiser_id="AR123")

    assert r["degraded"] is False
    assert r["http_status"] == 200
    assert len(r["advertisers"]) == 1
    assert r["advertisers"][0]["domain"] == "acme.com"
    assert len(r["ad_creatives"]) == 2
    assert r["ad_creatives"][0]["creative_id"] == "C1"
    assert r["ad_creatives"][0]["format"] == "image"
    # Second creative uses the alt synonym keys.
    assert r["ad_creatives"][1]["creative_id"] == "C2"
    assert r["ad_creatives"][1]["format"] == "video"


@pytest.mark.asyncio
async def test_search_ads_by_domain_calls_correct_engine_param() -> None:
    with respx.mock() as router:
        route = router.get(SERPAPI_BASE_URL).mock(
            return_value=httpx.Response(200, json={"advertisers": []})
        )
        c = SerpApiAdsClient(api_key="k")
        await c.search_ads_by_domain("acme.com", region="GB")

    sent_params = route.calls.last.request.url.params
    assert sent_params["engine"] == "google_ads_transparency_center"
    assert sent_params["q"] == "acme.com"
    assert sent_params["region"] == "GB"
    assert sent_params["api_key"] == "k"


@pytest.mark.asyncio
async def test_serpapi_logical_error_on_2xx_returns_degraded() -> None:
    """SerpAPI returns ``{"error": "..."}`` even on HTTP 200 for some failures."""
    with respx.mock() as router:
        router.get(SERPAPI_BASE_URL).mock(
            return_value=httpx.Response(
                200,
                json={"error": "Your account has run out of searches."},
            )
        )
        c = SerpApiAdsClient(api_key="k")
        r = await c.advertiser_lookup(advertiser_id="X")
    assert r["degraded"] is True
    assert "run out" in r["degraded_reason"]


@pytest.mark.asyncio
async def test_4xx_returns_degraded() -> None:
    with respx.mock() as router:
        router.get(SERPAPI_BASE_URL).mock(
            return_value=httpx.Response(401, text="bad key")
        )
        c = SerpApiAdsClient(api_key="bad")
        r = await c.search_ads_by_domain("x.com")
    assert r["degraded"] is True
    assert "401" in r["degraded_reason"]


@pytest.mark.asyncio
async def test_network_error_returns_degraded() -> None:
    with respx.mock() as router:
        router.get(SERPAPI_BASE_URL).mock(
            side_effect=httpx.ConnectError("DNS")
        )
        c = SerpApiAdsClient(api_key="k")
        r = await c.search_ads_by_domain("x.com")
    assert r["degraded"] is True
    assert "ConnectError" in r["degraded_reason"]


@pytest.mark.asyncio
async def test_non_json_returns_degraded() -> None:
    with respx.mock() as router:
        router.get(SERPAPI_BASE_URL).mock(
            return_value=httpx.Response(200, text="HTML")
        )
        c = SerpApiAdsClient(api_key="k")
        r = await c.search_ads_by_domain("x.com")
    assert r["degraded"] is True
    assert "non-JSON" in r["degraded_reason"]
