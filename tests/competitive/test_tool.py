"""Tests for competitor_ads tool registration and handler."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.competitive.config import CompetitiveSettings
from src.competitive.exceptions import AllProvidersUnavailableError
from src.competitive.service import CompetitiveAdService
from src.billing.tiers import Tier
from src.orchestrator.tools import build_default_registry


@pytest.fixture
def mock_ad_service() -> AsyncMock:
    service = AsyncMock(spec=CompetitiveAdService)
    service.search_ads = AsyncMock(return_value=[
        {
            "provider": "foreplay",
            "platform": "meta",
            "headline": "Test Ad",
            "body_text": "Body",
            "cta_text": "Shop",
            "link_url": "https://example.com",
            "image_url": None,
            "video_url": None,
            "is_active": True,
            "started_at": None,
            "transcription": None,
            "persona": None,
            "emotional_drivers": None,
        }
    ])
    return service


class TestToolRegistration:
    def test_registered_for_pro_tier(self, mock_ad_service: AsyncMock) -> None:
        """Tool registered when ad_service present and tier=PRO."""
        registry, restricted = build_default_registry(
            ad_service=mock_ad_service,
            tier=Tier.PRO,
        )
        assert registry.get("competitor_ads") is not None
        assert "competitor_ads" not in restricted

    def test_restricted_for_free_tier(self, mock_ad_service: AsyncMock) -> None:
        """Tool in restricted_tools when ad_service present but tier=FREE."""
        registry, restricted = build_default_registry(
            ad_service=mock_ad_service,
            tier=Tier.FREE,
        )
        assert registry.get("competitor_ads") is None
        assert "competitor_ads" in restricted

    def test_not_registered_without_service(self) -> None:
        """Tool not registered when ad_service=None."""
        registry, restricted = build_default_registry(
            ad_service=None,
            tier=Tier.PRO,
        )
        assert registry.get("competitor_ads") is None
        assert "competitor_ads" not in restricted


@pytest.mark.asyncio
class TestToolHandler:
    async def test_happy_path(self, mock_ad_service: AsyncMock) -> None:
        """Handler returns structured result."""
        registry, _ = build_default_registry(
            ad_service=mock_ad_service,
            tier=Tier.PRO,
        )
        tool = registry.get("competitor_ads")
        assert tool is not None

        result = await tool.handler(domain="nike.com")
        assert result["ad_count"] == 1
        assert len(result["ads"]) == 1
        assert "Found 1 ads" in result["summary"]
        assert "error" not in result

    async def test_providers_unavailable_error(self, mock_ad_service: AsyncMock) -> None:
        """AllProvidersUnavailableError returns structured error dict."""
        mock_ad_service.search_ads.side_effect = AllProvidersUnavailableError("All failed")
        registry, _ = build_default_registry(
            ad_service=mock_ad_service,
            tier=Tier.PRO,
        )
        tool = registry.get("competitor_ads")
        assert tool is not None

        result = await tool.handler(domain="nike.com")
        assert result["error"] == "providers_unavailable"
        assert result["ads"] == []
        assert result["ad_count"] == 0

    async def test_invalid_domain_error(self, mock_ad_service: AsyncMock) -> None:
        """ValueError from domain validation returns invalid_domain error."""
        mock_ad_service.search_ads.side_effect = ValueError("Invalid domain format: bad")
        registry, _ = build_default_registry(
            ad_service=mock_ad_service,
            tier=Tier.PRO,
        )
        tool = registry.get("competitor_ads")
        assert tool is not None

        result = await tool.handler(domain="bad")
        assert result["error"] == "invalid_domain"
        assert result["ads"] == []

    async def test_platform_note_all(self, mock_ad_service: AsyncMock) -> None:
        """Summary includes 'across all platforms' when platform=all."""
        registry, _ = build_default_registry(
            ad_service=mock_ad_service,
            tier=Tier.PRO,
        )
        tool = registry.get("competitor_ads")
        assert tool is not None

        result = await tool.handler(domain="nike.com", platform="all")
        assert "across all platforms" in result["summary"]

    async def test_platform_note_specific(self, mock_ad_service: AsyncMock) -> None:
        """Summary includes 'on meta' when platform=meta."""
        registry, _ = build_default_registry(
            ad_service=mock_ad_service,
            tier=Tier.PRO,
        )
        tool = registry.get("competitor_ads")
        assert tool is not None

        result = await tool.handler(domain="nike.com", platform="meta")
        assert "on meta" in result["summary"]
