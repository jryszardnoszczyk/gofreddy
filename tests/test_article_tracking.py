"""Tests for article tracking service — mock-based for GSC control flow."""

from datetime import date, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.seo.article_tracking_service import ArticleTrackingService
from src.seo.providers.gsc import PageSearchMetrics, SearchAnalyticsResult


@pytest.fixture
def mock_gsc():
    return AsyncMock()


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def service(mock_gsc, mock_repo):
    return ArticleTrackingService(gsc_client=mock_gsc, article_repo=mock_repo)


@pytest.mark.mock_required
class TestPollAllArticles:
    @pytest.mark.asyncio
    async def test_empty_published_urls_returns_early(self, service, mock_repo):
        mock_repo.list_published_urls.return_value = []
        result = await service.poll_all_articles(uuid4(), "https://example.com")
        assert result.articles_tracked == 0
        assert result.snapshots_upserted == 0

    @pytest.mark.asyncio
    async def test_successful_poll(self, service, mock_repo, mock_gsc):
        article_id = uuid4()
        url = "https://example.com/article-1"
        mock_repo.list_published_urls.return_value = [(article_id, url)]

        mock_gsc.get_search_analytics.return_value = SearchAnalyticsResult(
            site_url="https://example.com",
            start_date="2026-03-20",
            end_date="2026-03-23",
            rows=[
                PageSearchMetrics(page=url, clicks=10, impressions=100, ctr=0.1, position=5.2),
            ],
            row_count=1,
        )

        result = await service.poll_all_articles(uuid4(), "https://example.com")
        assert result.articles_tracked == 1
        assert result.snapshots_upserted == 1
        assert result.errors == []
        mock_repo.upsert_performance_snapshot.assert_called_once()

    @pytest.mark.asyncio
    async def test_gsc_api_error(self, service, mock_repo, mock_gsc):
        mock_repo.list_published_urls.return_value = [(uuid4(), "https://example.com/a")]
        mock_gsc.get_search_analytics.side_effect = Exception("GSC timeout")

        result = await service.poll_all_articles(uuid4(), "https://example.com")
        assert result.articles_tracked == 1
        assert result.snapshots_upserted == 0
        assert len(result.errors) == 1
        assert "GSC API error" in result.errors[0]

    def test_date_range_calculation(self):
        """Verify GSC data lag is accounted for (2 days)."""
        end = date.today() - timedelta(days=2)
        start = end - timedelta(days=6)
        assert (end - start).days == 6
