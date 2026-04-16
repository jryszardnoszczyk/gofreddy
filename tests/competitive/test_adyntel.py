"""Tests for AdyntelProvider."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx

from src.competitive.exceptions import AdyntelError, ProviderUnavailableError
from src.competitive.providers.adyntel import AdyntelProvider


@pytest.fixture
def mock_cost_recorder() -> AsyncMock:
    with patch("src.competitive.providers.adyntel._cost_recorder") as mock:
        mock.record = AsyncMock()
        yield mock


@pytest.mark.asyncio
class TestSearchGoogleAds:
    async def test_happy_path(self, adyntel_provider: AdyntelProvider, mock_cost_recorder: AsyncMock) -> None:
        """Domain → Google ads returned."""
        ads_response = {
            "ads": [
                {
                    "advertiser_id": "adv-1",
                    "creative_id": "cr-1",
                    "original_url": "https://nike.com",
                    "advertiser_name": "Nike",
                    "variants": [{"content": "Just Do It", "height": 250, "width": 300}],
                    "start": "2026-01-01",
                    "last_seen": "2026-03-01",
                    "format": "image",
                }
            ],
            "continuation_token": None,
        }

        with respx.mock:
            respx.post("https://api.adyntel.com/google").mock(
                return_value=httpx.Response(200, json=ads_response)
            )

            result = await adyntel_provider.search_google_ads(domain="nike.com")

        assert len(result) == 1
        assert result[0]["advertiser_name"] == "Nike"
        mock_cost_recorder.record.assert_awaited_once()

    async def test_pagination_with_continuation_token(self, adyntel_provider: AdyntelProvider, mock_cost_recorder: AsyncMock) -> None:
        """Multiple pages via continuation_token."""
        page1 = {
            "ads": [{"advertiser_name": "Ad 1"}],
            "continuation_token": "next-page",
        }
        page2 = {
            "ads": [{"advertiser_name": "Ad 2"}],
            "continuation_token": None,
        }

        with respx.mock:
            route = respx.post("https://api.adyntel.com/google")
            route.side_effect = [
                httpx.Response(200, json=page1),
                httpx.Response(200, json=page2),
            ]

            result = await adyntel_provider.search_google_ads(domain="nike.com", max_pages=3)

        assert len(result) == 2
        # Cost recorded once for both pages
        mock_cost_recorder.record.assert_awaited_once()
        call_kwargs = mock_cost_recorder.record.call_args
        assert call_kwargs[1]["metadata"]["pages"] == 2

    async def test_max_pages_limit(self, adyntel_provider: AdyntelProvider, mock_cost_recorder: AsyncMock) -> None:
        """Stops after max_pages even with continuation_token."""
        page_data = {
            "ads": [{"advertiser_name": "Ad"}],
            "continuation_token": "more",
        }

        with respx.mock:
            respx.post("https://api.adyntel.com/google").mock(
                return_value=httpx.Response(200, json=page_data)
            )

            result = await adyntel_provider.search_google_ads(domain="nike.com", max_pages=1)

        assert len(result) == 1

    async def test_204_returns_empty_no_cost(self, adyntel_provider: AdyntelProvider, mock_cost_recorder: AsyncMock) -> None:
        """204 = no data found, no credits charged."""
        with respx.mock:
            respx.post("https://api.adyntel.com/google").mock(
                return_value=httpx.Response(204)
            )

            result = await adyntel_provider.search_google_ads(domain="unknown.com")

        assert result == []
        mock_cost_recorder.record.assert_not_awaited()

    async def test_401_raises_invalid_credentials(self, adyntel_provider: AdyntelProvider, mock_cost_recorder: AsyncMock) -> None:
        """401 = invalid credentials, permanent error."""
        with respx.mock:
            respx.post("https://api.adyntel.com/google").mock(
                return_value=httpx.Response(401, json={"error": "unauthorized"})
            )

            with pytest.raises(AdyntelError, match="Invalid credentials"):
                await adyntel_provider.search_google_ads(domain="nike.com")

    async def test_429_trips_circuit_breaker(self, adyntel_provider: AdyntelProvider, mock_cost_recorder: AsyncMock) -> None:
        """429 = rate limited, trips circuit breaker."""
        with respx.mock:
            respx.post("https://api.adyntel.com/google").mock(
                return_value=httpx.Response(429, json={"error": "rate limited"})
            )

            with pytest.raises(AdyntelError, match="Rate limited"):
                await adyntel_provider.search_google_ads(domain="nike.com")

        assert adyntel_provider._breaker._failure_count >= 1

    async def test_timeout_trips_circuit_breaker(self, adyntel_provider: AdyntelProvider, mock_cost_recorder: AsyncMock) -> None:
        """Timeout trips circuit breaker."""
        with respx.mock:
            respx.post("https://api.adyntel.com/google").mock(
                side_effect=httpx.ReadTimeout("timeout")
            )

            with pytest.raises(AdyntelError, match="Timeout"):
                await adyntel_provider.search_google_ads(domain="nike.com")

        assert adyntel_provider._breaker._failure_count >= 1

    async def test_circuit_breaker_open_raises(self, adyntel_provider: AdyntelProvider, mock_cost_recorder: AsyncMock) -> None:
        """Open circuit breaker raises ProviderUnavailableError."""
        for _ in range(3):
            adyntel_provider._breaker.record_failure()

        with pytest.raises(ProviderUnavailableError, match="circuit open"):
            await adyntel_provider.search_google_ads(domain="nike.com")

    async def test_company_domain_key_in_body(self, adyntel_provider: AdyntelProvider, mock_cost_recorder: AsyncMock) -> None:
        """Request body uses 'company_domain' key, not 'domain'."""
        with respx.mock:
            route = respx.post("https://api.adyntel.com/google").mock(
                return_value=httpx.Response(200, json={"ads": [], "continuation_token": None})
            )

            await adyntel_provider.search_google_ads(domain="nike.com")

        # Verify the request body
        request = route.calls[0].request
        import json
        body = json.loads(request.content)
        assert "company_domain" in body
        assert body["company_domain"] == "nike.com"
        assert "api_key" in body
        assert "email" in body


@pytest.mark.asyncio
class TestClose:
    async def test_close_no_client(self, adyntel_provider: AdyntelProvider) -> None:
        """Close with no active client is a no-op."""
        await adyntel_provider.close()
