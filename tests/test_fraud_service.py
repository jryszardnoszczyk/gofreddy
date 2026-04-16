"""Tests for FraudDetectionService — real PostgreSQL for DB tests, pure logic for calculations.

Test isolation: each test runs inside a transaction that rolls back on teardown.
Uses fraud_service, fraud_repo, db_conn fixtures from conftest.py.
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from src.common.enums import Platform
from src.fetcher.models import CommentData, CreatorStats, FollowerProfile
from src.fraud.models import (
    AQSGrade,
    AQSResult,
    BotCommentAnalysis,
    FraudAnalysisRecord,
    FraudRiskLevel,
)


# ── Pure Logic Tests (no DB needed) ─────────────────────────────────────────


class TestAQSResult:
    """Tests for AQS calculation."""

    def test_excellent_grade(self):
        """Test excellent grade for high scores."""
        result = AQSResult.calculate(
            engagement_score=95.0,
            audience_quality_score=92.0,
            comment_authenticity_score=90.0,
        )

        assert result.score >= 90.0
        assert result.grade == AQSGrade.EXCELLENT

    def test_critical_grade(self):
        """Test critical grade for low scores."""
        result = AQSResult.calculate(
            engagement_score=20.0,
            audience_quality_score=15.0,
            comment_authenticity_score=25.0,
        )

        assert result.score < 40.0
        assert result.grade == AQSGrade.CRITICAL

    def test_component_weights(self):
        """Test that AQS formula uses correct weights."""
        result = AQSResult.calculate(
            engagement_score=100.0,
            audience_quality_score=100.0,
            comment_authenticity_score=100.0,
        )

        # All 100 = AQS of 100
        assert result.score == 100.0

        # Check weights: 0.30 + 0.35 + 0.35 = 1.0
        result2 = AQSResult.calculate(
            engagement_score=100.0,  # 30 points
            audience_quality_score=0.0,  # 0 points
            comment_authenticity_score=0.0,  # 0 points
        )
        assert result2.score == 30.0


class TestFraudAnalysisRecord:
    """Tests for FraudAnalysisRecord creation."""

    def test_create_with_high_aqs(self):
        """Test record creation with high AQS score."""
        aqs = AQSResult.calculate(90.0, 85.0, 88.0)

        record = FraudAnalysisRecord.create(
            platform="tiktok",
            username="test_user",
            cache_key="fraud:tiktok:test_user:v1.0.0",
            aqs=aqs,
        )

        assert record.fraud_risk_level == FraudRiskLevel.LOW
        assert record.fraud_risk_score < 20

    def test_create_with_low_aqs(self):
        """Test record creation with low AQS score."""
        aqs = AQSResult.calculate(20.0, 25.0, 15.0)

        record = FraudAnalysisRecord.create(
            platform="tiktok",
            username="test_user",
            cache_key="fraud:tiktok:test_user:v1.0.0",
            aqs=aqs,
        )

        assert record.fraud_risk_level == FraudRiskLevel.CRITICAL
        assert record.fraud_risk_score > 70

    def test_risk_level_boundaries(self):
        """Test risk level assignment at boundaries."""
        # 80+ = LOW
        aqs_80 = AQSResult.calculate(80.0, 80.0, 80.0)
        record_80 = FraudAnalysisRecord.create(
            platform="tiktok", username="u", cache_key="k", aqs=aqs_80
        )
        assert record_80.fraud_risk_level == FraudRiskLevel.LOW

        # 60-79 = MEDIUM
        aqs_60 = AQSResult.calculate(60.0, 60.0, 60.0)
        record_60 = FraudAnalysisRecord.create(
            platform="tiktok", username="u", cache_key="k", aqs=aqs_60
        )
        assert record_60.fraud_risk_level == FraudRiskLevel.MEDIUM

        # 40-59 = HIGH
        aqs_40 = AQSResult.calculate(40.0, 40.0, 40.0)
        record_40 = FraudAnalysisRecord.create(
            platform="tiktok", username="u", cache_key="k", aqs=aqs_40
        )
        assert record_40.fraud_risk_level == FraudRiskLevel.HIGH


# ── Service Tests (real DB + real Gemini) ────────────────────────────────────


@pytest.mark.db
class TestFraudDetectionService:
    """Tests for FraudDetectionService with real DB."""

    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached(self, fraud_service, fraud_repo, db_conn):
        """Cache hit returns cached result from real DB."""
        # Seed a fraud record into real DB
        record = FraudAnalysisRecord.create(
            platform="tiktok",
            username="test_creator",
            cache_key="fraud:tiktok:test_creator:v2.0.0",
            aqs=AQSResult.calculate(80.0, 80.0, 80.0),
            model_version="2.0.0",
        )
        await fraud_repo.save(record)

        # Analyze should return cached
        sample_followers = [
            FollowerProfile(
                username=f"user_{i}", has_profile_pic=True,
                bio=f"Bio {i}", post_count=10, follower_count=100, following_count=50,
            )
            for i in range(100)
        ]
        sample_stats = CreatorStats(
            username="test_creator", platform=Platform.TIKTOK,
            follower_count=50000, following_count=500, video_count=100,
            total_likes=1000000, avg_likes=10000, avg_comments=500,
        )

        result = await fraud_service.analyze(
            platform="tiktok",
            username="test_creator",
            followers=sample_followers,
            comments=[],
            stats=sample_stats,
        )

        assert result.cached is True
        assert result.record.id == record.id

    @pytest.mark.asyncio
    async def test_get_by_id(self, fraud_service, fraud_repo, db_conn):
        """Get analysis by ID from real DB."""
        # Seed record
        record = FraudAnalysisRecord.create(
            platform="tiktok",
            username="test_user",
            cache_key="fraud:tiktok:test_user_get:v2.0.0",
            aqs=AQSResult.calculate(80.0, 80.0, 80.0),
            model_version="2.0.0",
        )
        await fraud_repo.save(record)

        result = await fraud_service.get_by_id(record.id)

        assert result is not None
        assert result.id == record.id
        assert result.platform == "tiktok"

    @pytest.mark.asyncio
    async def test_cache_key_generation(self, fraud_service):
        """Cache key includes version."""
        key = fraud_service._generate_cache_key("tiktok", "test_user")
        assert key.startswith("fraud:tiktok:test_user:v")

    @pytest.mark.asyncio
    async def test_comment_score_calculation(self, fraud_service):
        """Comment score from bot analysis."""
        # No bot analysis = 50
        assert fraud_service._calculate_comment_score(None) == 50.0

        # 0% bots = 100
        bot_analysis = BotCommentAnalysis(
            total_analyzed=20,
            bot_like_count=0,
            bot_ratio=0.0,
            confidence="high",
            patterns_detected=[],
            suspicious_examples=[],
        )
        assert fraud_service._calculate_comment_score(bot_analysis) == 100.0

        # 50% bots = 50
        bot_analysis_50 = BotCommentAnalysis(
            total_analyzed=20,
            bot_like_count=10,
            bot_ratio=0.5,
            confidence="high",
            patterns_detected=["generic_praise"],
            suspicious_examples=[],
        )
        assert fraud_service._calculate_comment_score(bot_analysis_50) == 50.0

    @pytest.mark.asyncio
    async def test_audience_quality_score_calculation(self, fraud_service):
        """Audience quality score from follower analysis."""
        from src.fraud.models import FollowerAnalysisResult

        # No analysis = 50
        assert fraud_service._calculate_audience_quality_score(None) == 50.0

        # 0% fake = 100
        follower_result = FollowerAnalysisResult(
            fake_follower_percentage=0.0,
            sample_size=100,
            confidence="high",
            suspicious_signals={},
        )
        assert fraud_service._calculate_audience_quality_score(follower_result) == 100.0

        # 30% fake = 70
        follower_result_30 = FollowerAnalysisResult(
            fake_follower_percentage=30.0,
            sample_size=100,
            confidence="high",
            suspicious_signals={},
        )
        assert fraud_service._calculate_audience_quality_score(follower_result_30) == 70.0

    @pytest.mark.asyncio
    @pytest.mark.gemini
    async def test_full_analysis_saves_to_db(self, fraud_service, fraud_repo, db_conn):
        """Full analysis flow saves result to real DB (calls Gemini for bot detection)."""
        sample_followers = [
            FollowerProfile(
                username=f"user_{i}", has_profile_pic=True,
                bio=f"Bio about life #{i}", post_count=50 + i,
                follower_count=200 + i * 10, following_count=150,
            )
            for i in range(100)
        ]
        sample_comments = [
            CommentData(
                text=f"This is a real comment about the video #{i}",
                username=f"commenter_{i}",
                like_count=5,
            )
            for i in range(20)
        ]
        sample_stats = CreatorStats(
            username="real_analysis_test",
            platform=Platform.TIKTOK,
            follower_count=50000,
            following_count=500,
            video_count=100,
            total_likes=1000000,
            avg_likes=10000,
            avg_comments=500,
        )

        result = await fraud_service.analyze(
            platform="tiktok",
            username="real_analysis_test",
            followers=sample_followers,
            comments=sample_comments,
            stats=sample_stats,
            force_refresh=True,
        )

        assert result.cached is False
        assert result.record.aqs_score > 0
        assert result.record.fraud_risk_level in list(FraudRiskLevel)

        # Verify saved in real DB
        saved = await fraud_repo.get_by_id(result.record.id)
        assert saved is not None
        assert saved.id == result.record.id
