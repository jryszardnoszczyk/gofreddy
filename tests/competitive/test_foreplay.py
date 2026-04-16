"""Tests for ForeplayProvider."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx

from src.competitive.exceptions import ForeplayError, ProviderUnavailableError
from src.competitive.providers.foreplay import ForeplayProvider


@pytest.fixture
def mock_cost_recorder() -> AsyncMock:
    with patch("src.competitive.providers.foreplay._cost_recorder") as mock:
        mock.record = AsyncMock()
        yield mock


@pytest.mark.asyncio
class TestSearchAdsByDomain:
    async def test_happy_path(self, foreplay_provider: ForeplayProvider, mock_cost_recorder: AsyncMock) -> None:
        """Brand found → ads returned."""
        brand_response = [{"id": "brand-123", "name": "Nike", "domain": "nike.com"}]
        ads_response = [
            {
                "id": "ad-1",
                "headline": "Just Do It",
                "description": "Nike shoes ad",
                "cta_title": "Shop Now",
                "publisher_platform": "meta",
                "link_url": "https://nike.com",
                "image": "https://img.com/1.jpg",
                "video": None,
                "live": True,
                "started_running": "2026-01-01",
                "full_transcription": "Just do it transcript",
                "persona": "athlete",
                "emotional_drivers": "motivation",
            }
        ]

        with respx.mock:
            respx.get("https://public.api.foreplay.co/api/brand/getBrandsByDomain").mock(
                return_value=httpx.Response(200, json=brand_response)
            )
            respx.get("https://public.api.foreplay.co/api/brand/getAdsByBrandId").mock(
                return_value=httpx.Response(200, json=ads_response)
            )

            result = await foreplay_provider.search_ads_by_domain("nike.com")

        assert len(result) == 1
        assert result[0]["headline"] == "Just Do It"
        mock_cost_recorder.record.assert_awaited_once()

    async def test_brand_not_found_returns_empty(self, foreplay_provider: ForeplayProvider, mock_cost_recorder: AsyncMock) -> None:
        """No brand for domain → empty list, no error."""
        with respx.mock:
            respx.get("https://public.api.foreplay.co/api/brand/getBrandsByDomain").mock(
                return_value=httpx.Response(200, json=[])
            )

            result = await foreplay_provider.search_ads_by_domain("unknown-brand.com")

        assert result == []

    async def test_401_raises_permanent_error(self, foreplay_provider: ForeplayProvider, mock_cost_recorder: AsyncMock) -> None:
        """401 = invalid key, permanent error, no circuit breaker trip."""
        with respx.mock:
            respx.get("https://public.api.foreplay.co/api/brand/getBrandsByDomain").mock(
                return_value=httpx.Response(401, json={"error": "unauthorized"})
            )

            with pytest.raises(ForeplayError, match="Invalid API key"):
                await foreplay_provider.search_ads_by_domain("nike.com")

    async def test_402_raises_out_of_credits(self, foreplay_provider: ForeplayProvider, mock_cost_recorder: AsyncMock) -> None:
        """402 = out of credits, permanent error."""
        with respx.mock:
            respx.get("https://public.api.foreplay.co/api/brand/getBrandsByDomain").mock(
                return_value=httpx.Response(402, json={"error": "payment required"})
            )

            with pytest.raises(ForeplayError, match="Out of credits"):
                await foreplay_provider.search_ads_by_domain("nike.com")

    async def test_429_trips_circuit_breaker(self, foreplay_provider: ForeplayProvider, mock_cost_recorder: AsyncMock) -> None:
        """429 = rate limited, transient error, trips circuit breaker."""
        with respx.mock:
            respx.get("https://public.api.foreplay.co/api/brand/getBrandsByDomain").mock(
                return_value=httpx.Response(429, json={"error": "rate limited"})
            )

            with pytest.raises(ForeplayError, match="Rate limited"):
                await foreplay_provider.search_ads_by_domain("nike.com")

        # Circuit breaker should have recorded failure
        assert foreplay_provider._breaker._failure_count >= 1

    async def test_timeout_trips_circuit_breaker(self, foreplay_provider: ForeplayProvider, mock_cost_recorder: AsyncMock) -> None:
        """Timeout = transient error, trips circuit breaker."""
        with respx.mock:
            respx.get("https://public.api.foreplay.co/api/brand/getBrandsByDomain").mock(
                side_effect=httpx.ReadTimeout("timeout")
            )

            with pytest.raises(ForeplayError, match="Timeout"):
                await foreplay_provider.search_ads_by_domain("nike.com")

        assert foreplay_provider._breaker._failure_count >= 1

    async def test_circuit_breaker_open_raises(self, foreplay_provider: ForeplayProvider, mock_cost_recorder: AsyncMock) -> None:
        """Open circuit breaker raises ProviderUnavailableError."""
        # Trip the circuit breaker
        for _ in range(3):
            foreplay_provider._breaker.record_failure()

        with pytest.raises(ProviderUnavailableError, match="circuit open"):
            await foreplay_provider.search_ads_by_domain("nike.com")

    async def test_credit_tracking_from_headers(self, foreplay_provider: ForeplayProvider, mock_cost_recorder: AsyncMock) -> None:
        """Credit tracking reads X-Credits-Remaining header."""
        brand_response = [{"id": "brand-123", "domain": "nike.com"}]
        ads_response = [{"id": "ad-1"}]

        with respx.mock:
            respx.get("https://public.api.foreplay.co/api/brand/getBrandsByDomain").mock(
                return_value=httpx.Response(200, json=brand_response)
            )
            respx.get("https://public.api.foreplay.co/api/brand/getAdsByBrandId").mock(
                return_value=httpx.Response(
                    200,
                    json=ads_response,
                    headers={"X-Credits-Remaining": "100", "X-Credit-Cost": "1"},
                )
            )

            result = await foreplay_provider.search_ads_by_domain("nike.com")

        assert len(result) == 1


@pytest.mark.asyncio
class TestBrandDomainValidation:
    """Tests for brand-domain mismatch filtering (#11)."""

    async def test_substring_mismatch_returns_empty(
        self, foreplay_provider: ForeplayProvider, mock_cost_recorder: AsyncMock
    ) -> None:
        """Querying 'sketch.com' but Foreplay returns 'mangasketch.com' → empty."""
        brand_response = [
            {"id": "brand-999", "name": "MangaSketch", "domain": "mangasketch.com"},
        ]

        with respx.mock:
            respx.get("https://public.api.foreplay.co/api/brand/getBrandsByDomain").mock(
                return_value=httpx.Response(200, json=brand_response)
            )

            result = await foreplay_provider.search_ads_by_domain("sketch.com")

        assert result == []

    async def test_exact_match_with_www_prefix(
        self, foreplay_provider: ForeplayProvider, mock_cost_recorder: AsyncMock
    ) -> None:
        """Brand domain 'www.nike.com' matches queried 'nike.com'."""
        brand_response = [
            {"id": "brand-123", "name": "Nike", "domain": "www.nike.com"},
        ]
        ads_response = [{"id": "ad-1", "headline": "Just Do It"}]

        with respx.mock:
            respx.get("https://public.api.foreplay.co/api/brand/getBrandsByDomain").mock(
                return_value=httpx.Response(200, json=brand_response)
            )
            respx.get("https://public.api.foreplay.co/api/brand/getAdsByBrandId").mock(
                return_value=httpx.Response(200, json=ads_response)
            )

            result = await foreplay_provider.search_ads_by_domain("nike.com")

        assert len(result) == 1

    async def test_picks_matching_brand_from_list(
        self, foreplay_provider: ForeplayProvider, mock_cost_recorder: AsyncMock
    ) -> None:
        """When multiple brands returned, picks the one matching the queried domain."""
        brand_response = [
            {"id": "brand-wrong", "name": "MangaSketch", "domain": "mangasketch.com"},
            {"id": "brand-right", "name": "Sketch", "domain": "sketch.com"},
        ]
        ads_response = [{"id": "ad-1", "headline": "Sketch Ad"}]

        with respx.mock:
            respx.get("https://public.api.foreplay.co/api/brand/getBrandsByDomain").mock(
                return_value=httpx.Response(200, json=brand_response)
            )
            ads_mock = respx.get("https://public.api.foreplay.co/api/brand/getAdsByBrandId").mock(
                return_value=httpx.Response(200, json=ads_response)
            )

            result = await foreplay_provider.search_ads_by_domain("sketch.com")

        assert len(result) == 1
        # Verify we used the correct brand ID
        assert "brand-right" in str(ads_mock.calls[0].request.url)


@pytest.mark.asyncio
class TestClose:
    async def test_close_no_client(self, foreplay_provider: ForeplayProvider) -> None:
        """Close with no active client is a no-op."""
        await foreplay_provider.close()  # Should not raise
