"""PageSpeed provider integration tests (mocked HTTP).

Closes the last Tier-1 P0 provider with no test coverage. Verifies
URL+param shaping, error swallowing, and JSON-response parsing
without hitting real Google APIs.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from src.seo.providers.pagespeed import PAGESPEED_URL, check_performance


def _mock_response(json_data: dict, status_code: int = 200):
    response = AsyncMock(spec=httpx.Response)
    response.json = lambda: json_data  # sync, not async
    response.raise_for_status = lambda: None
    response.status_code = status_code
    return response


@pytest.mark.asyncio
async def test_check_performance_returns_parsed_metrics():
    payload = {
        "lighthouseResult": {
            "categories": {"performance": {"score": 0.85}},
            "audits": {
                "first-contentful-paint": {"numericValue": 1234.5},
                "largest-contentful-paint": {"numericValue": 2500.0},
                "cumulative-layout-shift": {"numericValue": 0.05},
                "total-blocking-time": {"numericValue": 200.0},
                "speed-index": {"numericValue": 3000.0},
            },
        }
    }
    with patch("httpx.AsyncClient.get", AsyncMock(return_value=_mock_response(payload))):
        result = await check_performance("https://acme.example", api_key="test_key")

    assert result.url == "https://acme.example"
    assert result.performance_score == 0.85
    assert result.fcp_ms == 1234.5
    assert result.lcp_ms == 2500.0
    assert result.cls == 0.05
    assert result.tbt_ms == 200.0
    assert result.speed_index_ms == 3000.0
    assert result.strategy == "mobile"


@pytest.mark.asyncio
async def test_check_performance_passes_api_key_param():
    payload = {"lighthouseResult": {"categories": {}, "audits": {}}}
    with patch("httpx.AsyncClient.get", AsyncMock(return_value=_mock_response(payload))) as mock_get:
        await check_performance("https://x.example", api_key="my_secret_key")
    args, kwargs = mock_get.call_args
    assert args[0] == PAGESPEED_URL
    assert kwargs["params"]["key"] == "my_secret_key"
    assert kwargs["params"]["url"] == "https://x.example"
    assert kwargs["params"]["strategy"] == "mobile"


@pytest.mark.asyncio
async def test_check_performance_omits_key_when_empty():
    payload = {"lighthouseResult": {"categories": {}, "audits": {}}}
    with patch("httpx.AsyncClient.get", AsyncMock(return_value=_mock_response(payload))) as mock_get:
        await check_performance("https://x.example", api_key="")
    assert "key" not in mock_get.call_args.kwargs["params"]


@pytest.mark.asyncio
async def test_check_performance_honors_desktop_strategy():
    payload = {"lighthouseResult": {"categories": {}, "audits": {}}}
    with patch("httpx.AsyncClient.get", AsyncMock(return_value=_mock_response(payload))) as mock_get:
        result = await check_performance("https://x.example", strategy="desktop")
    assert mock_get.call_args.kwargs["params"]["strategy"] == "desktop"
    assert result.strategy == "desktop"


@pytest.mark.asyncio
async def test_check_performance_returns_empty_on_http_error():
    """Non-200 responses → graceful PerformanceResult with no metrics
    (audit pipeline tolerates this; lens gap_flags rather than crashes)."""
    err = httpx.HTTPError("upstream 500")
    with patch("httpx.AsyncClient.get", AsyncMock(side_effect=err)):
        result = await check_performance("https://x.example", api_key="k")
    assert result.url == "https://x.example"
    assert result.performance_score is None
    assert result.fcp_ms is None
    assert result.strategy == "mobile"


@pytest.mark.asyncio
async def test_check_performance_handles_partial_lighthouse_data():
    """Some pages return lighthouse without all audits — provider must
    fall back to None per metric without crashing."""
    payload = {
        "lighthouseResult": {
            "categories": {"performance": {"score": 0.5}},
            "audits": {"first-contentful-paint": {"numericValue": 1000.0}},
            # Missing LCP / CLS / TBT / speed-index
        }
    }
    with patch("httpx.AsyncClient.get", AsyncMock(return_value=_mock_response(payload))):
        result = await check_performance("https://x.example")
    assert result.performance_score == 0.5
    assert result.fcp_ms == 1000.0
    assert result.lcp_ms is None
    assert result.cls is None


@pytest.mark.asyncio
async def test_check_performance_handles_missing_lighthouse_result():
    """Quota-exceeded or 4xx responses sometimes return JSON with
    `error` only — no `lighthouseResult`. Must not crash."""
    payload = {"error": {"code": 429, "message": "quota exceeded"}}
    with patch("httpx.AsyncClient.get", AsyncMock(return_value=_mock_response(payload))):
        result = await check_performance("https://x.example")
    assert result.performance_score is None
