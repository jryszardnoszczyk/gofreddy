"""Tests for Trend Service — real PostgreSQL for service tests, pure logic for calculations.

Test isolation: each test runs inside a transaction that rolls back on teardown.
"""

import json
from datetime import date
from uuid import uuid4

import pytest

from src.common.enums import Platform
from src.trends.exceptions import NoTrendDataError
from src.trends.models import (
    TrendingHashtag,
    EmergingCreator,
    TrendResponse,
    TrendSnapshot,
    calculate_growth_rate,
    calculate_share_of_voice,
    get_confidence_level,
    is_emerging_creator,
)


# ── Pure Logic Tests (no DB needed) ─────────────────────────────────────────


class TestGrowthRateCalculation:
    def test_growth_rate_positive(self):
        result = calculate_growth_rate(150, 100)
        assert result == 0.5

    def test_growth_rate_negative(self):
        result = calculate_growth_rate(80, 100)
        assert result == -0.2

    def test_growth_rate_zero_previous(self):
        result = calculate_growth_rate(100, 0)
        assert result == 1.0

    def test_growth_rate_both_zero(self):
        result = calculate_growth_rate(0, 0)
        assert result == 0.0

    def test_growth_rate_no_change(self):
        result = calculate_growth_rate(100, 100)
        assert result == 0.0


class TestConfidenceLevel:
    def test_confidence_low(self):
        assert get_confidence_level(0) == "low"
        assert get_confidence_level(15) == "low"
        assert get_confidence_level(29) == "low"

    def test_confidence_medium(self):
        assert get_confidence_level(30) == "medium"
        assert get_confidence_level(50) == "medium"
        assert get_confidence_level(99) == "medium"

    def test_confidence_high(self):
        assert get_confidence_level(100) == "high"
        assert get_confidence_level(500) == "high"
        assert get_confidence_level(10000) == "high"


class TestShareOfVoice:
    def test_share_of_voice_basic(self):
        brands = {"Nike": 50, "Adidas": 30, "Puma": 20}
        result = calculate_share_of_voice(brands)
        assert result["Nike"] == 50.0
        assert result["Adidas"] == 30.0
        assert result["Puma"] == 20.0

    def test_share_of_voice_empty(self):
        result = calculate_share_of_voice({})
        assert result == {}

    def test_share_of_voice_single_brand(self):
        brands = {"Nike": 100}
        result = calculate_share_of_voice(brands)
        assert result["Nike"] == 100.0

    def test_share_of_voice_all_zero(self):
        brands = {"Nike": 0, "Adidas": 0}
        result = calculate_share_of_voice(brands)
        assert result == {}


class TestIsEmergingCreator:
    def test_is_emerging_true(self):
        assert is_emerging_creator(growth_rate=0.08, engagement_rate=0.05, sample_videos=5) is True

    def test_is_emerging_low_growth(self):
        assert is_emerging_creator(growth_rate=0.03, engagement_rate=0.05, sample_videos=5) is False

    def test_is_emerging_low_engagement(self):
        assert is_emerging_creator(growth_rate=0.08, engagement_rate=0.02, sample_videos=5) is False

    def test_is_emerging_insufficient_videos(self):
        assert is_emerging_creator(growth_rate=0.08, engagement_rate=0.05, sample_videos=2) is False


class TestTrendingHashtagModel:
    def test_valid_hashtag(self):
        hashtag = TrendingHashtag(hashtag="#fitness", volume=150, growth_rate=0.5, unique_creators=45)
        assert hashtag.hashtag == "#fitness"
        assert hashtag.volume == 150

    def test_negative_volume_rejected(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            TrendingHashtag(hashtag="#test", volume=-1, growth_rate=0.5, unique_creators=10)

    def test_negative_unique_creators_rejected(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            TrendingHashtag(hashtag="#test", volume=100, growth_rate=0.5, unique_creators=-1)


class TestEmergingCreatorModel:
    def test_valid_emerging_creator(self):
        creator_id = uuid4()
        creator = EmergingCreator(
            creator_id=creator_id, username="fitnessjen", platform=Platform.TIKTOK,
            growth_rate=0.12, follower_delta=85000,
        )
        assert creator.creator_id == creator_id


class TestTrendSnapshotModel:
    def test_valid_snapshot(self):
        snapshot_id = uuid4()
        snapshot = TrendSnapshot(
            id=snapshot_id, snapshot_date=date(2026, 2, 5), platform=Platform.TIKTOK,
            trending_hashtags=[], emerging_creators=[], brand_mention_volumes={},
            sample_size=100, confidence_level="high",
        )
        assert snapshot.id == snapshot_id

    def test_snapshot_default_values(self):
        snapshot = TrendSnapshot(id=uuid4(), snapshot_date=date(2026, 2, 5), platform=Platform.INSTAGRAM)
        assert snapshot.trending_hashtags == []
        assert snapshot.sample_size == 0
        assert snapshot.confidence_level == "low"


class TestTrendResponseModel:
    def test_valid_response(self):
        snapshot = TrendSnapshot(
            id=uuid4(), snapshot_date=date(2026, 2, 5), platform=Platform.TIKTOK,
            brand_mention_volumes={"Nike": 100, "Adidas": 50}, sample_size=150, confidence_level="high",
        )
        response = TrendResponse(snapshot=snapshot, share_of_voice={"Nike": 66.67, "Adidas": 33.33})
        assert "Nike" in response.share_of_voice


# ── TrendService Tests (real DB) ─────────────────────────────────────────────


async def _insert_trend_snapshot(conn, *, platform=Platform.TIKTOK, snapshot_date=None,
                                  hashtags=None, brands=None, sample_size=150):
    """Insert a trend snapshot row."""
    snapshot_id = uuid4()
    snapshot_date = snapshot_date or date(2026, 2, 5)
    hashtags_data = json.dumps(hashtags or [])
    brands_data = json.dumps(brands or {})
    creators_data = json.dumps([])

    await conn.execute(
        """INSERT INTO trend_snapshots
           (id, snapshot_date, platform, trending_hashtags, emerging_creators,
            brand_mention_volumes, sample_size, confidence_level)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
        snapshot_id, snapshot_date, platform.value,
        hashtags_data, creators_data, brands_data,
        sample_size, "high" if sample_size >= 100 else "medium",
    )
    return snapshot_id


@pytest.mark.db
class TestTrendService:
    @pytest.mark.asyncio
    async def test_get_trends_success(self, trend_service, db_conn):
        """Successful trend retrieval with share of voice calculation."""
        await _insert_trend_snapshot(
            db_conn, platform=Platform.TIKTOK,
            hashtags=[{"hashtag": "#fitness", "volume": 150, "growth_rate": 0.5, "unique_creators": 45}],
            brands={"Nike": 100, "Adidas": 50},
            sample_size=150,
        )

        result = await trend_service.get_trends(Platform.TIKTOK)

        assert isinstance(result, TrendResponse)
        assert result.share_of_voice["Nike"] == pytest.approx(66.67, rel=0.01)
        assert result.share_of_voice["Adidas"] == pytest.approx(33.33, rel=0.01)

    @pytest.mark.asyncio
    async def test_get_trends_no_data(self, trend_service):
        """Raises NoTrendDataError when no snapshot exists."""
        with pytest.raises(NoTrendDataError) as exc_info:
            await trend_service.get_trends(Platform.INSTAGRAM)
        assert exc_info.value.platform == "instagram"

    @pytest.mark.asyncio
    async def test_get_trends_empty_brands(self, trend_service, db_conn):
        """Trend response with empty brand mentions."""
        await _insert_trend_snapshot(
            db_conn, platform=Platform.YOUTUBE, brands={}, sample_size=50,
        )

        result = await trend_service.get_trends(Platform.YOUTUBE)

        assert result.share_of_voice == {}
