"""Tests for Trend Aggregator module (PR-015)."""

from contextlib import asynccontextmanager
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.common.enums import Platform
from src.trends.aggregator import (
    _aggregate_brand_mentions,
    _aggregate_hashtags,
    _find_emerging_creators,
    _get_sample_size,
    generate_trend_snapshot,
    run_daily_aggregation,
)
from src.trends.models import (
    TrendingHashtag,
    EmergingCreator,
    TrendSnapshot,
)


def create_mock_pool(mock_conn):
    """Create a mock asyncpg pool with proper async context manager support."""
    pool = MagicMock()

    @asynccontextmanager
    async def mock_acquire():
        yield mock_conn

    pool.acquire = mock_acquire
    return pool


@pytest.mark.mock_required
class TestHashtagAggregation:
    """Tests for hashtag aggregation."""

    @pytest.mark.asyncio
    async def test_aggregate_hashtags_success(self):
        """Test hashtag aggregation returns TrendingHashtag objects."""
        mock_rows = [
            {
                "hashtag": "#fitness",
                "today_count": 150,
                "yesterday_count": 100,
                "unique_creators": 45,
                "growth_rate": 0.5,
            },
            {
                "hashtag": "#workout",
                "today_count": 80,
                "yesterday_count": 60,
                "unique_creators": 30,
                "growth_rate": 0.33,
            },
        ]

        mock_conn = MagicMock()
        mock_conn.fetch = AsyncMock(return_value=mock_rows)
        mock_pool = create_mock_pool(mock_conn)

        result = await _aggregate_hashtags(mock_pool, Platform.TIKTOK)

        assert len(result) == 2
        assert result[0].hashtag == "#fitness"
        assert result[0].volume == 150
        assert result[0].growth_rate == 0.5
        assert result[0].unique_creators == 45
        assert isinstance(result[0], TrendingHashtag)

    @pytest.mark.asyncio
    async def test_aggregate_hashtags_empty(self):
        """Test hashtag aggregation with no results."""
        mock_conn = MagicMock()
        mock_conn.fetch = AsyncMock(return_value=[])
        mock_pool = create_mock_pool(mock_conn)

        result = await _aggregate_hashtags(mock_pool, Platform.INSTAGRAM)

        assert result == []


@pytest.mark.mock_required
class TestEmergingCreatorDetection:
    """Tests for emerging creator detection."""

    @pytest.mark.asyncio
    async def test_find_emerging_creators_success(self):
        """Test emerging creator detection returns EmergingCreator objects."""
        creator_id = uuid4()
        mock_rows = [
            {
                "creator_id": creator_id,
                "username": "fitnessjen",
                "platform": "tiktok",
                "follower_count": 150000,
                "follower_count_previous_month": 100000,
                "growth_rate": 0.5,
                "follower_delta": 50000,
            },
        ]

        mock_conn = MagicMock()
        mock_conn.fetch = AsyncMock(return_value=mock_rows)
        mock_pool = create_mock_pool(mock_conn)

        result = await _find_emerging_creators(mock_pool, Platform.TIKTOK)

        assert len(result) == 1
        assert result[0].creator_id == creator_id
        assert result[0].username == "fitnessjen"
        assert result[0].platform == Platform.TIKTOK
        assert result[0].growth_rate == 0.5
        assert result[0].follower_delta == 50000
        assert isinstance(result[0], EmergingCreator)


@pytest.mark.mock_required
class TestBrandMentionAggregation:
    """Tests for brand mention aggregation."""

    @pytest.mark.asyncio
    async def test_aggregate_brand_mentions_success(self):
        """Test brand mention aggregation returns dict of brand -> count."""
        mock_rows = [
            {"brand_name": "Nike", "mention_count": 150},
            {"brand_name": "Adidas", "mention_count": 100},
            {"brand_name": "Puma", "mention_count": 50},
        ]

        mock_conn = MagicMock()
        mock_conn.fetch = AsyncMock(return_value=mock_rows)
        mock_pool = create_mock_pool(mock_conn)

        result = await _aggregate_brand_mentions(mock_pool, Platform.TIKTOK)

        assert result == {"Nike": 150, "Adidas": 100, "Puma": 50}


@pytest.mark.mock_required
class TestSampleSize:
    """Tests for sample size calculation."""

    @pytest.mark.asyncio
    async def test_get_sample_size_success(self):
        """Test sample size query returns count."""
        mock_conn = MagicMock()
        mock_conn.fetchrow = AsyncMock(return_value={"sample_size": 150})
        mock_pool = create_mock_pool(mock_conn)

        result = await _get_sample_size(mock_pool, Platform.TIKTOK)

        assert result == 150

    @pytest.mark.asyncio
    async def test_get_sample_size_no_result(self):
        """Test sample size returns 0 when no row."""
        mock_conn = MagicMock()
        mock_conn.fetchrow = AsyncMock(return_value=None)
        mock_pool = create_mock_pool(mock_conn)

        result = await _get_sample_size(mock_pool, Platform.TIKTOK)

        assert result == 0


@pytest.mark.mock_required
class TestGenerateTrendSnapshot:
    """Tests for generating complete trend snapshots."""

    @pytest.fixture
    def mock_pool(self):
        """Create mock asyncpg pool."""
        pool = MagicMock()
        return pool

    @pytest.mark.asyncio
    async def test_generate_trend_snapshot_success(self, mock_pool):
        """Test full snapshot generation with all components."""
        creator_id = uuid4()

        with patch(
            "src.trends.aggregator._aggregate_hashtags"
        ) as mock_hashtags, patch(
            "src.trends.aggregator._find_emerging_creators"
        ) as mock_creators, patch(
            "src.trends.aggregator._aggregate_brand_mentions"
        ) as mock_brands, patch(
            "src.trends.aggregator._get_sample_size"
        ) as mock_sample:
            mock_hashtags.return_value = [
                TrendingHashtag(
                    hashtag="#fitness", volume=150, growth_rate=0.5, unique_creators=45
                )
            ]
            mock_creators.return_value = [
                EmergingCreator(
                    creator_id=creator_id,
                    username="fitnessjen",
                    platform=Platform.TIKTOK,
                    growth_rate=0.5,
                    follower_delta=50000,
                )
            ]
            mock_brands.return_value = {"Nike": 150, "Adidas": 100}
            mock_sample.return_value = 150

            result = await generate_trend_snapshot(
                mock_pool, Platform.TIKTOK, date(2026, 2, 5)
            )

            assert isinstance(result, TrendSnapshot)
            assert result.platform == Platform.TIKTOK
            assert result.snapshot_date == date(2026, 2, 5)
            assert len(result.trending_hashtags) == 1
            assert len(result.emerging_creators) == 1
            assert result.brand_mention_volumes == {"Nike": 150, "Adidas": 100}
            assert result.sample_size == 150
            assert result.confidence_level == "high"  # 150 >= 100

    @pytest.mark.asyncio
    async def test_generate_trend_snapshot_partial_failure(self, mock_pool):
        """Test snapshot generation with partial failures uses graceful degradation."""
        with patch(
            "src.trends.aggregator._aggregate_hashtags"
        ) as mock_hashtags, patch(
            "src.trends.aggregator._find_emerging_creators"
        ) as mock_creators, patch(
            "src.trends.aggregator._aggregate_brand_mentions"
        ) as mock_brands, patch(
            "src.trends.aggregator._get_sample_size"
        ) as mock_sample:
            # Simulate hashtag aggregation failure
            mock_hashtags.side_effect = Exception("Database error")
            mock_creators.return_value = []
            mock_brands.return_value = {}
            mock_sample.return_value = 50

            result = await generate_trend_snapshot(
                mock_pool, Platform.TIKTOK, date(2026, 2, 5)
            )

            # Should succeed with empty hashtags
            assert isinstance(result, TrendSnapshot)
            assert result.trending_hashtags == []
            assert result.sample_size == 50
            assert result.confidence_level == "medium"  # 50 >= 30 and < 100

    @pytest.mark.asyncio
    async def test_generate_trend_snapshot_low_confidence(self, mock_pool):
        """Test snapshot with low sample size has low confidence."""
        with patch(
            "src.trends.aggregator._aggregate_hashtags"
        ) as mock_hashtags, patch(
            "src.trends.aggregator._find_emerging_creators"
        ) as mock_creators, patch(
            "src.trends.aggregator._aggregate_brand_mentions"
        ) as mock_brands, patch(
            "src.trends.aggregator._get_sample_size"
        ) as mock_sample:
            mock_hashtags.return_value = []
            mock_creators.return_value = []
            mock_brands.return_value = {}
            mock_sample.return_value = 15  # Below 30 threshold

            result = await generate_trend_snapshot(
                mock_pool, Platform.INSTAGRAM, date(2026, 2, 5)
            )

            assert result.confidence_level == "low"


@pytest.mark.mock_required
class TestRunDailyAggregation:
    """Tests for daily aggregation job."""

    @pytest.fixture
    def mock_pool(self):
        """Create mock asyncpg pool."""
        pool = MagicMock()
        return pool

    @pytest.mark.asyncio
    async def test_run_daily_aggregation_all_platforms(self, mock_pool):
        """Test daily aggregation runs for all platforms."""
        with patch(
            "src.trends.aggregator.generate_trend_snapshot"
        ) as mock_generate, patch(
            "src.trends.aggregator.PostgresTrendRepository"
        ) as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.save = AsyncMock(return_value=True)
            mock_repo_class.return_value = mock_repo

            # Return different snapshots for each platform
            async def generate_snapshot(pool, platform, snapshot_date):
                return TrendSnapshot(
                    id=uuid4(),
                    snapshot_date=snapshot_date,
                    platform=platform,
                    trending_hashtags=[],
                    emerging_creators=[],
                    brand_mention_volumes={},
                    sample_size=100,
                    confidence_level="high",
                )

            mock_generate.side_effect = generate_snapshot

            result = await run_daily_aggregation(mock_pool)

            # Should have snapshots for all platforms
            assert len(result) == len(Platform)
            assert Platform.TIKTOK in result
            assert Platform.INSTAGRAM in result
            assert Platform.YOUTUBE in result

            # Verify save was called for each platform
            assert mock_repo.save.call_count == len(Platform)

    @pytest.mark.asyncio
    async def test_run_daily_aggregation_continues_on_error(self, mock_pool):
        """Test daily aggregation continues even if one platform fails."""
        with patch(
            "src.trends.aggregator.generate_trend_snapshot"
        ) as mock_generate, patch(
            "src.trends.aggregator.PostgresTrendRepository"
        ) as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.save = AsyncMock(return_value=True)
            mock_repo_class.return_value = mock_repo

            call_count = [0]

            async def generate_snapshot(pool, platform, snapshot_date):
                call_count[0] += 1
                if platform == Platform.INSTAGRAM:
                    raise Exception("Instagram API error")
                return TrendSnapshot(
                    id=uuid4(),
                    snapshot_date=snapshot_date,
                    platform=platform,
                    trending_hashtags=[],
                    emerging_creators=[],
                    brand_mention_volumes={},
                    sample_size=100,
                    confidence_level="high",
                )

            mock_generate.side_effect = generate_snapshot

            result = await run_daily_aggregation(mock_pool)

            # Should have snapshots for all platforms except Instagram (which failed)
            assert len(result) == len(Platform) - 1
            assert Platform.INSTAGRAM not in result
            # All platforms should have been attempted
            assert call_count[0] == len(Platform)
