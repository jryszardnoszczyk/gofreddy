"""Tests for SEO service — service with mocked DataForSEO."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from src.seo.config import SeoSettings
from src.seo.exceptions import SeoAuditError
from src.seo.models import (
    KeywordAnalysisResult,
    KeywordData,
    PerformanceResult,
    TechnicalAuditResult,
)
from src.seo.service import SeoService


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def seo_settings():
    return SeoSettings(
        enable_seo=True,
        dataforseo_login="test",
        dataforseo_password="test",
        dataforseo_sandbox=True,
    )


@pytest.fixture
def seo_service(mock_repo, seo_settings):
    return SeoService(repository=mock_repo, settings=seo_settings)


class TestSeoServiceInit:
    def test_creates_provider_with_credentials(self, seo_settings, mock_repo):
        svc = SeoService(repository=mock_repo, settings=seo_settings)
        assert svc._provider is not None

    def test_no_provider_without_credentials(self, mock_repo):
        settings = SeoSettings(enable_seo=True, dataforseo_login="", dataforseo_password="")
        svc = SeoService(repository=mock_repo, settings=settings)
        assert svc._provider is None


class TestSeoServiceMethods:
    @pytest.mark.asyncio
    async def test_technical_audit_without_provider(self, mock_repo):
        settings = SeoSettings(enable_seo=True)
        svc = SeoService(repository=mock_repo, settings=settings)
        with pytest.raises(SeoAuditError, match="NO_PROVIDER"):
            await svc.technical_audit("https://example.com")

    @pytest.mark.asyncio
    async def test_technical_audit_delegates(self, seo_service):
        mock_result = TechnicalAuditResult(url="https://example.com", status_code=200)
        with patch.object(seo_service._provider, "technical_audit", return_value=mock_result):
            result = await seo_service.technical_audit("https://example.com")
            assert result["url"] == "https://example.com"
            assert result["status_code"] == 200

    @pytest.mark.asyncio
    async def test_keyword_analysis_delegates(self, seo_service):
        mock_result = KeywordAnalysisResult(
            keywords=(KeywordData(keyword="test", search_volume=1000),),
        )
        with patch.object(seo_service._provider, "keyword_analysis", return_value=mock_result):
            result = await seo_service.keyword_analysis(["test"])
            assert len(result["keywords"]) == 1
            assert result["keywords"][0]["keyword"] == "test"

    @pytest.mark.asyncio
    async def test_check_performance(self, seo_service):
        mock_result = PerformanceResult(url="https://example.com", performance_score=0.85)
        with patch("src.seo.service.check_performance", return_value=mock_result):
            result = await seo_service.check_performance("https://example.com")
            assert result["performance_score"] == 0.85

    @pytest.mark.asyncio
    async def test_backlink_without_provider(self, mock_repo):
        settings = SeoSettings(enable_seo=True)
        svc = SeoService(repository=mock_repo, settings=settings)
        with pytest.raises(SeoAuditError, match="NO_PROVIDER"):
            await svc.backlink_analysis("https://example.com")
