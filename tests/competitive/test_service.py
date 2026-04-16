"""Tests for CompetitiveAdService."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from src.competitive.config import CompetitiveSettings
from src.competitive.exceptions import (
    AllProvidersUnavailableError,
    ForeplayError,
    AdyntelError,
)
from src.competitive.providers.foreplay import ForeplayProvider
from src.competitive.providers.adyntel import AdyntelProvider
from src.competitive.service import CompetitiveAdService


@pytest.fixture
def mock_foreplay() -> AsyncMock:
    provider = AsyncMock(spec=ForeplayProvider)
    provider.search_ads_by_domain = AsyncMock(return_value=[
        {
            "id": "ad-1",
            "headline": "Meta Ad",
            "description": "Body text",
            "cta_title": "Shop",
            "publisher_platform": "meta",
            "link_url": "https://nike.com",
            "image": "https://img.com/1.jpg",
            "video": None,
            "live": True,
            "started_running": "2026-01-01",
            "full_transcription": "Transcript",
            "persona": "athlete",
            "emotional_drivers": "motivation",
        }
    ])
    return provider


@pytest.fixture
def mock_adyntel() -> AsyncMock:
    provider = AsyncMock(spec=AdyntelProvider)
    provider.search_google_ads = AsyncMock(return_value=[
        {
            "advertiser_name": "Nike",
            "original_url": "https://nike.com",
            "variants": [{"content": "Google Ad", "height": 250, "width": 300}],
            "start": "2026-01-01",
            "last_seen": "2026-03-01",
        }
    ])
    return provider


@pytest.fixture
def settings() -> CompetitiveSettings:
    return CompetitiveSettings(
        foreplay_api_key="test",
        adyntel_api_key="test",
        adyntel_email="test@test.com",
    )


@pytest.mark.asyncio
class TestSearchAds:
    async def test_platform_all_calls_both(
        self, mock_foreplay: AsyncMock, mock_adyntel: AsyncMock, settings: CompetitiveSettings,
    ) -> None:
        """platform=all calls both providers in parallel."""
        service = CompetitiveAdService(mock_foreplay, mock_adyntel, settings)
        result = await service.search_ads("nike.com", platform="all")

        assert len(result) == 2
        providers = {ad["provider"] for ad in result}
        assert providers == {"foreplay", "adyntel"}
        mock_foreplay.search_ads_by_domain.assert_awaited_once()
        mock_adyntel.search_google_ads.assert_awaited_once()

    async def test_platform_meta_calls_foreplay_only(
        self, mock_foreplay: AsyncMock, mock_adyntel: AsyncMock, settings: CompetitiveSettings,
    ) -> None:
        """platform=meta calls Foreplay only."""
        service = CompetitiveAdService(mock_foreplay, mock_adyntel, settings)
        result = await service.search_ads("nike.com", platform="meta")

        assert all(ad["provider"] == "foreplay" for ad in result)
        mock_foreplay.search_ads_by_domain.assert_awaited_once()
        mock_adyntel.search_google_ads.assert_not_awaited()

    async def test_platform_google_calls_adyntel_only(
        self, mock_foreplay: AsyncMock, mock_adyntel: AsyncMock, settings: CompetitiveSettings,
    ) -> None:
        """platform=google calls Adyntel only."""
        service = CompetitiveAdService(mock_foreplay, mock_adyntel, settings)
        result = await service.search_ads("nike.com", platform="google")

        assert all(ad["provider"] == "adyntel" for ad in result)
        mock_adyntel.search_google_ads.assert_awaited_once()
        mock_foreplay.search_ads_by_domain.assert_not_awaited()

    async def test_graceful_degradation_foreplay_fails(
        self, mock_foreplay: AsyncMock, mock_adyntel: AsyncMock, settings: CompetitiveSettings,
    ) -> None:
        """Foreplay fails → returns Adyntel results only."""
        mock_foreplay.search_ads_by_domain.side_effect = ForeplayError("Rate limited")
        service = CompetitiveAdService(mock_foreplay, mock_adyntel, settings)

        result = await service.search_ads("nike.com", platform="all")

        assert len(result) == 1
        assert result[0]["provider"] == "adyntel"

    async def test_graceful_degradation_adyntel_fails(
        self, mock_foreplay: AsyncMock, mock_adyntel: AsyncMock, settings: CompetitiveSettings,
    ) -> None:
        """Adyntel fails → returns Foreplay results only."""
        mock_adyntel.search_google_ads.side_effect = AdyntelError("Timeout")
        service = CompetitiveAdService(mock_foreplay, mock_adyntel, settings)

        result = await service.search_ads("nike.com", platform="all")

        assert len(result) == 1
        assert result[0]["provider"] == "foreplay"

    async def test_both_fail_raises(
        self, mock_foreplay: AsyncMock, mock_adyntel: AsyncMock, settings: CompetitiveSettings,
    ) -> None:
        """Both providers fail → AllProvidersUnavailableError."""
        mock_foreplay.search_ads_by_domain.side_effect = ForeplayError("Rate limited")
        mock_adyntel.search_google_ads.side_effect = AdyntelError("Timeout")
        service = CompetitiveAdService(mock_foreplay, mock_adyntel, settings)

        with pytest.raises(AllProvidersUnavailableError):
            await service.search_ads("nike.com", platform="all")

    async def test_no_providers_configured_raises(self, settings: CompetitiveSettings) -> None:
        """No providers → AllProvidersUnavailableError."""
        service = CompetitiveAdService(None, None, settings)

        with pytest.raises(AllProvidersUnavailableError, match="No ad providers"):
            await service.search_ads("nike.com")

    async def test_limit_cap_at_100(
        self, mock_foreplay: AsyncMock, mock_adyntel: AsyncMock, settings: CompetitiveSettings,
    ) -> None:
        """Limit capped at 100."""
        service = CompetitiveAdService(mock_foreplay, mock_adyntel, settings)
        await service.search_ads("nike.com", limit=500)

        # Foreplay called with min(500, 100) = 100
        call_kwargs = mock_foreplay.search_ads_by_domain.call_args
        assert call_kwargs[1]["limit"] == 100

    async def test_foreplay_none_google_platform(
        self, mock_adyntel: AsyncMock, settings: CompetitiveSettings,
    ) -> None:
        """Foreplay=None, platform=google → works with Adyntel only."""
        service = CompetitiveAdService(None, mock_adyntel, settings)
        result = await service.search_ads("nike.com", platform="google")

        assert len(result) == 1
        assert result[0]["provider"] == "adyntel"


@pytest.mark.asyncio
class TestNormalization:
    async def test_foreplay_normalization_shape(
        self, mock_foreplay: AsyncMock, settings: CompetitiveSettings,
    ) -> None:
        """Foreplay results normalized to unified shape."""
        service = CompetitiveAdService(mock_foreplay, None, settings)
        result = await service.search_ads("nike.com", platform="meta")

        ad = result[0]
        assert ad["provider"] == "foreplay"
        assert ad["platform"] == "meta"
        assert ad["headline"] == "Meta Ad"
        assert ad["body_text"] == "Body text"
        assert ad["cta_text"] == "Shop"
        assert ad["is_active"] is True
        assert ad["transcription"] == "Transcript"

    async def test_adyntel_normalization_shape(
        self, mock_adyntel: AsyncMock, settings: CompetitiveSettings,
    ) -> None:
        """Adyntel results normalized to unified shape."""
        service = CompetitiveAdService(None, mock_adyntel, settings)
        result = await service.search_ads("nike.com", platform="google")

        ad = result[0]
        assert ad["provider"] == "adyntel"
        assert ad["platform"] == "google"
        assert ad["headline"] == "Nike"
        assert ad["body_text"] == "Google Ad"
        assert ad["link_url"] == "https://nike.com"
        assert ad["transcription"] is None

    async def test_invalid_domain_raises_valueerror(self, settings: CompetitiveSettings) -> None:
        """Invalid domain raises ValueError."""
        service = CompetitiveAdService(None, None, settings)

        with pytest.raises(ValueError, match="Invalid domain format"):
            await service.search_ads("not a domain")


@pytest.mark.asyncio
class TestSearchAdsCache:
    async def test_cache_hit_skips_providers(
        self, mock_foreplay: AsyncMock, mock_adyntel: AsyncMock, settings: CompetitiveSettings,
    ) -> None:
        """Second call for same domain returns cached results, providers called once."""
        service = CompetitiveAdService(mock_foreplay, mock_adyntel, settings)

        result1 = await service.search_ads("nike.com", platform="all")
        result2 = await service.search_ads("nike.com", platform="all")

        assert result1 == result2
        mock_foreplay.search_ads_by_domain.assert_awaited_once()
        mock_adyntel.search_google_ads.assert_awaited_once()

    async def test_different_domains_no_cross_contamination(
        self, mock_foreplay: AsyncMock, mock_adyntel: AsyncMock, settings: CompetitiveSettings,
    ) -> None:
        """Different domains are cached separately."""
        service = CompetitiveAdService(mock_foreplay, mock_adyntel, settings)

        await service.search_ads("nike.com", platform="all")
        await service.search_ads("adidas.com", platform="all")

        assert mock_foreplay.search_ads_by_domain.await_count == 2
        assert mock_adyntel.search_google_ads.await_count == 2

    async def test_cache_slices_for_smaller_limit(
        self, mock_foreplay: AsyncMock, mock_adyntel: AsyncMock, settings: CompetitiveSettings,
    ) -> None:
        """First call with limit=100, second with limit=1 returns subset from cache."""
        service = CompetitiveAdService(mock_foreplay, mock_adyntel, settings)

        result_full = await service.search_ads("nike.com", platform="all", limit=100)
        result_small = await service.search_ads("nike.com", platform="all", limit=1)

        assert len(result_small) == 1
        assert result_small[0] == result_full[0]
        # Providers called only once
        mock_foreplay.search_ads_by_domain.assert_awaited_once()

    async def test_cache_upgrade_on_larger_limit(
        self, mock_foreplay: AsyncMock, mock_adyntel: AsyncMock, settings: CompetitiveSettings,
    ) -> None:
        """First call with limit=1, second with limit=100 re-fetches (cache too small)."""
        # First call: mock returns 1 ad each
        mock_foreplay.search_ads_by_domain.return_value = [
            {"id": "ad-1", "headline": "Ad", "description": "", "cta_title": "",
             "publisher_platform": "meta", "link_url": "https://nike.com",
             "image": None, "video": None, "live": True, "started_running": None,
             "full_transcription": None, "persona": None, "emotional_drivers": None}
        ]
        service = CompetitiveAdService(mock_foreplay, mock_adyntel, settings)

        result1 = await service.search_ads("nike.com", platform="all", limit=1)
        assert len(result1) == 1

        # Second call with larger limit — cache has 2 items (1 foreplay + 1 adyntel), need 100
        result2 = await service.search_ads("nike.com", platform="all", limit=100)

        # Providers called twice (upgrade)
        assert mock_foreplay.search_ads_by_domain.await_count == 2

    async def test_different_platforms_separate_cache(
        self, mock_foreplay: AsyncMock, mock_adyntel: AsyncMock, settings: CompetitiveSettings,
    ) -> None:
        """Different platforms for same domain are cached separately."""
        service = CompetitiveAdService(mock_foreplay, mock_adyntel, settings)

        await service.search_ads("nike.com", platform="meta")
        await service.search_ads("nike.com", platform="google")

        mock_foreplay.search_ads_by_domain.assert_awaited_once()
        mock_adyntel.search_google_ads.assert_awaited_once()

    async def test_provider_exception_not_cached(
        self, mock_foreplay: AsyncMock, mock_adyntel: AsyncMock, settings: CompetitiveSettings,
    ) -> None:
        """Both providers fail → not cached, next call retries."""
        mock_foreplay.search_ads_by_domain.side_effect = ForeplayError("fail")
        mock_adyntel.search_google_ads.side_effect = AdyntelError("fail")
        service = CompetitiveAdService(mock_foreplay, mock_adyntel, settings)

        with pytest.raises(AllProvidersUnavailableError):
            await service.search_ads("nike.com")

        # Reset mocks to succeed
        mock_foreplay.search_ads_by_domain.side_effect = None
        mock_foreplay.search_ads_by_domain.return_value = [
            {"id": "ad-1", "headline": "Ad", "description": "", "cta_title": "",
             "publisher_platform": "meta", "link_url": "https://nike.com",
             "image": None, "video": None, "live": True, "started_running": None,
             "full_transcription": None, "persona": None, "emotional_drivers": None}
        ]
        mock_adyntel.search_google_ads.side_effect = None
        mock_adyntel.search_google_ads.return_value = [
            {"advertiser_name": "Nike", "original_url": "https://nike.com",
             "variants": [{"content": "Ad"}], "start": "2026-01-01"}
        ]

        # Should retry providers (not return cached error)
        result = await service.search_ads("nike.com")
        assert len(result) >= 1


@pytest.mark.asyncio
class TestAdDomainFilter:
    """Tests for service-layer link_url domain filtering (#11)."""

    async def test_mismatched_link_url_filtered(
        self, mock_adyntel: AsyncMock, settings: CompetitiveSettings,
    ) -> None:
        """Ads with link_url pointing to wrong domain are filtered out."""
        mock_foreplay = AsyncMock(spec=ForeplayProvider)
        mock_foreplay.search_ads_by_domain = AsyncMock(return_value=[
            {
                "id": "ad-good", "headline": "Good Ad", "description": "",
                "cta_title": "", "publisher_platform": "meta",
                "link_url": "https://sketch.com/pricing",
                "image": None, "video": None, "live": True,
                "started_running": None, "full_transcription": None,
                "persona": None, "emotional_drivers": None,
            },
            {
                "id": "ad-bad", "headline": "Bad Ad", "description": "",
                "cta_title": "", "publisher_platform": "meta",
                "link_url": "https://mangasketch.com/shop",
                "image": None, "video": None, "live": True,
                "started_running": None, "full_transcription": None,
                "persona": None, "emotional_drivers": None,
            },
        ])
        service = CompetitiveAdService(mock_foreplay, None, settings)
        result = await service.search_ads("sketch.com", platform="meta")

        assert len(result) == 1
        assert result[0]["headline"] == "Good Ad"

    async def test_no_link_url_kept(
        self, mock_adyntel: AsyncMock, settings: CompetitiveSettings,
    ) -> None:
        """Ads with no link_url are kept (can't validate)."""
        mock_foreplay = AsyncMock(spec=ForeplayProvider)
        mock_foreplay.search_ads_by_domain = AsyncMock(return_value=[
            {
                "id": "ad-no-url", "headline": "No URL Ad", "description": "",
                "cta_title": "", "publisher_platform": "meta",
                "link_url": None,
                "image": None, "video": None, "live": True,
                "started_running": None, "full_transcription": None,
                "persona": None, "emotional_drivers": None,
            },
        ])
        service = CompetitiveAdService(mock_foreplay, None, settings)
        result = await service.search_ads("sketch.com", platform="meta")

        assert len(result) == 1
        assert result[0]["headline"] == "No URL Ad"

    async def test_www_prefix_link_url_matches(
        self, mock_adyntel: AsyncMock, settings: CompetitiveSettings,
    ) -> None:
        """link_url with www.domain.com matches queried domain.com."""
        mock_foreplay = AsyncMock(spec=ForeplayProvider)
        mock_foreplay.search_ads_by_domain = AsyncMock(return_value=[
            {
                "id": "ad-www", "headline": "WWW Ad", "description": "",
                "cta_title": "", "publisher_platform": "meta",
                "link_url": "https://www.nike.com/shoes",
                "image": None, "video": None, "live": True,
                "started_running": None, "full_transcription": None,
                "persona": None, "emotional_drivers": None,
            },
        ])
        service = CompetitiveAdService(mock_foreplay, None, settings)
        result = await service.search_ads("nike.com", platform="meta")

        assert len(result) == 1


@pytest.mark.asyncio
class TestAdyntelMaxPages:
    async def test_default_max_pages_is_1(
        self, mock_foreplay: AsyncMock, mock_adyntel: AsyncMock, settings: CompetitiveSettings,
    ) -> None:
        """Default adyntel_max_pages=1 is passed to provider."""
        service = CompetitiveAdService(mock_foreplay, mock_adyntel, settings)
        await service.search_ads("nike.com", platform="google")

        call_kwargs = mock_adyntel.search_google_ads.call_args
        assert call_kwargs[1]["max_pages"] == 1

    async def test_custom_max_pages(
        self, mock_foreplay: AsyncMock, mock_adyntel: AsyncMock,
    ) -> None:
        """Custom adyntel_max_pages=3 is passed to provider."""
        custom_settings = CompetitiveSettings(
            foreplay_api_key="test",
            adyntel_api_key="test",
            adyntel_email="test@test.com",
            adyntel_max_pages=3,
        )
        service = CompetitiveAdService(mock_foreplay, mock_adyntel, custom_settings)
        await service.search_ads("nike.com", platform="google")

        call_kwargs = mock_adyntel.search_google_ads.call_args
        assert call_kwargs[1]["max_pages"] == 3
