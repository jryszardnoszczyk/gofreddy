"""Tests for Evolution Service — real PostgreSQL.

Test isolation: each test runs inside a transaction that rolls back on teardown.
Uses evolution_service, evolution_repo, db_conn fixtures from conftest.py.
"""

import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from src.common.enums import Platform
from src.evolution.exceptions import CreatorNotFoundError, InsufficientDataError
from src.evolution.models import EvolutionResponse
from src.evolution.repository import CreatorAnalysisRow
from src.evolution.service import EvolutionService


# ── Helpers ──────────────────────────────────────────────────────────────────


async def _seed_creator_analyses(
    conn,
    *,
    platform: Platform = Platform.TIKTOK,
    username: str = "testcreator",
    count: int = 10,
    days_span: int = 30,
    overall_safe: bool = True,
    content_categories: dict | None = None,
    moderation_flags: list | None = None,
    varied_safe: list[bool] | None = None,
    varied_categories: list[dict] | None = None,
    varied_flags: list[list] | None = None,
):
    """Insert a creator + video_analysis rows for evolution tests.

    Returns creator_id for convenience.
    """
    creator_id = uuid4()
    await conn.execute(
        "INSERT INTO creators (id, platform, username) VALUES ($1, $2, $3)",
        creator_id, platform.value, username,
    )

    base_date = datetime(2026, 2, 5)
    default_cats = content_categories or {"fitness": 10, "lifestyle": 5}
    default_flags = moderation_flags or []

    def _cats_to_array(cats: dict) -> list:
        """Convert dict categories to array format for DB CHECK constraint."""
        return [{"vertical": k, "sub_category": k, "confidence": v} for k, v in cats.items()]

    for i in range(count):
        safe = varied_safe[i] if varied_safe else overall_safe
        cats = varied_categories[i] if varied_categories else default_cats
        flags = varied_flags[i] if varied_flags else default_flags
        analyzed_at = base_date - timedelta(days=int(days_span * i / max(count - 1, 1)))

        await conn.execute(
            """INSERT INTO video_analysis
               (id, video_id, cache_key, overall_safe, overall_confidence,
                risks_detected, summary, content_categories, moderation_flags,
                model_version, creator_id)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)""",
            uuid4(), uuid4(), f"test:{uuid4().hex[:8]}:v1",
            safe, 0.9,
            "[]", "Test summary",
            json.dumps(_cats_to_array(cats)), json.dumps(flags),
            "1", creator_id,
        )

    return creator_id


# ── Evolution Service Tests (real DB) ────────────────────────────────────────


@pytest.mark.db
class TestEvolutionService:
    @pytest.mark.asyncio
    async def test_get_evolution_success(self, evolution_service, db_conn):
        """Successful evolution analysis with 10 videos."""
        await _seed_creator_analyses(
            db_conn, platform=Platform.TIKTOK, username="fitnessjen", count=10,
        )

        result = await evolution_service.get_evolution(
            platform=Platform.TIKTOK, username="fitnessjen", period_days=90,
        )

        assert isinstance(result, EvolutionResponse)
        assert result.creator_username == "fitnessjen"
        assert result.platform == Platform.TIKTOK
        assert result.period_days == 90
        assert result.videos_analyzed == 10
        assert result.confidence_level == "medium"  # 10-29 videos

    @pytest.mark.asyncio
    async def test_get_evolution_creator_not_found(self, evolution_service):
        """Raises CreatorNotFoundError when no analyses exist."""
        with pytest.raises(CreatorNotFoundError) as exc_info:
            await evolution_service.get_evolution(
                platform=Platform.INSTAGRAM, username="unknown_creator_xyz", period_days=90,
            )
        assert exc_info.value.platform == "instagram"
        assert exc_info.value.username == "unknown_creator_xyz"

    @pytest.mark.asyncio
    async def test_get_evolution_insufficient_data(self, evolution_service, db_conn):
        """Raises InsufficientDataError when not enough videos (< 5)."""
        await _seed_creator_analyses(
            db_conn, platform=Platform.TIKTOK, username="newcreator", count=3,
        )

        with pytest.raises(InsufficientDataError) as exc_info:
            await evolution_service.get_evolution(
                platform=Platform.TIKTOK, username="newcreator", period_days=90,
            )
        assert exc_info.value.required == 5
        assert exc_info.value.actual == 3

    @pytest.mark.asyncio
    async def test_get_evolution_topic_shift_warning(self, evolution_service, db_conn):
        """Warning when insufficient data for topic shift (7 videos)."""
        await _seed_creator_analyses(
            db_conn, platform=Platform.TIKTOK, username="smallcreator", count=7,
        )

        result = await evolution_service.get_evolution(
            platform=Platform.TIKTOK, username="smallcreator", period_days=90,
        )

        assert len(result.warnings) == 1
        assert "Topic shift detection requires 10+ videos" in result.warnings[0]
        assert result.topic_shifts == []

    @pytest.mark.asyncio
    async def test_get_evolution_with_topic_shift(self, evolution_service, db_conn):
        """Topic shift detection — first 5 fitness, last 5 travel."""
        await _seed_creator_analyses(
            db_conn, platform=Platform.INSTAGRAM, username="pivoter", count=10,
            varied_categories=[
                {"fitness": 10} if i < 5 else {"travel": 10}
                for i in range(10)
            ],
        )

        result = await evolution_service.get_evolution(
            platform=Platform.INSTAGRAM, username="pivoter", period_days=90,
        )

        assert len(result.topic_shifts) > 0
        shift = result.topic_shifts[0]
        assert "fitness" in shift.from_topics
        assert "travel" in shift.to_topics

    @pytest.mark.asyncio
    async def test_get_evolution_risk_trajectory(self, evolution_service, db_conn):
        """Risk trajectory — increasing risk over time."""
        await _seed_creator_analyses(
            db_conn, platform=Platform.YOUTUBE, username="riskycreator", count=6,
            varied_safe=[i < 3 for i in range(6)],
            varied_flags=[["flag"] * i for i in range(6)],
        )

        result = await evolution_service.get_evolution(
            platform=Platform.YOUTUBE, username="riskycreator", period_days=90,
        )

        assert result.risk_trajectory is not None
        assert result.risk_trajectory.direction == "deteriorating"
        assert result.risk_trajectory.trend_slope > 0

    @pytest.mark.asyncio
    async def test_get_evolution_current_state(self, evolution_service, db_conn):
        """Current state summary — unsafe content with flags."""
        await _seed_creator_analyses(
            db_conn, platform=Platform.TIKTOK, username="riskylifestyle", count=10,
            overall_safe=False,
            content_categories={"lifestyle": 6, "fitness": 4},
            moderation_flags=["flag1", "flag2"],
        )

        result = await evolution_service.get_evolution(
            platform=Platform.TIKTOK, username="riskylifestyle", period_days=90,
        )

        assert result.current_risk_level == "high"
        assert "lifestyle" in result.current_topics
        assert "fitness" in result.current_topics

    @pytest.mark.asyncio
    async def test_get_evolution_date_range(self, evolution_service, db_conn):
        """Date range extraction from analyses."""
        creator_id = uuid4()
        await db_conn.execute(
            "INSERT INTO creators (id, platform, username) VALUES ($1, $2, $3)",
            creator_id, "tiktok", "consistent",
        )
        dates = [
            datetime(2026, 1, 15, 12, tzinfo=timezone.utc),
            datetime(2026, 1, 20, 12, tzinfo=timezone.utc),
            datetime(2026, 1, 25, 12, tzinfo=timezone.utc),
            datetime(2026, 1, 30, 12, tzinfo=timezone.utc),
            datetime(2026, 2, 5, 12, tzinfo=timezone.utc),
        ]
        for d in dates:
            await db_conn.execute(
                """INSERT INTO video_analysis
                   (id, video_id, cache_key, overall_safe, overall_confidence,
                    risks_detected, summary, content_categories, moderation_flags,
                    model_version, creator_id, analyzed_at)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)""",
                uuid4(), uuid4(), f"test:{uuid4().hex[:8]}:v1",
                True, 0.9, "[]", "Test",
                json.dumps([{"vertical": "fitness", "sub_category": "fitness", "confidence": 10}]),
                "[]",
                "1", creator_id, d,
            )

        result = await evolution_service.get_evolution(
            platform=Platform.TIKTOK, username="consistent", period_days=90,
        )

        from datetime import date
        assert result.date_range_start == date(2026, 1, 15)
        assert result.date_range_end == date(2026, 2, 5)

    @pytest.mark.asyncio
    async def test_get_evolution_confidence_levels(self, evolution_service, db_conn):
        """Confidence level: low (<10), medium (10-29), high (30+)."""
        # Low — 6 videos
        await _seed_creator_analyses(
            db_conn, platform=Platform.TIKTOK, username="small", count=6,
        )
        result_low = await evolution_service.get_evolution(
            platform=Platform.TIKTOK, username="small", period_days=90,
        )
        assert result_low.confidence_level == "low"

        # Medium — 20 videos
        await _seed_creator_analyses(
            db_conn, platform=Platform.TIKTOK, username="medium", count=20,
        )
        result_medium = await evolution_service.get_evolution(
            platform=Platform.TIKTOK, username="medium", period_days=90,
        )
        assert result_medium.confidence_level == "medium"

        # High — 35 videos
        await _seed_creator_analyses(
            db_conn, platform=Platform.TIKTOK, username="prolific", count=35,
        )
        result_high = await evolution_service.get_evolution(
            platform=Platform.TIKTOK, username="prolific", period_days=90,
        )
        assert result_high.confidence_level == "high"


# ── Risk Calculation Tests (pure logic — no DB needed) ───────────────────────


class TestEvolutionServiceRiskCalculation:
    @pytest.fixture
    def service(self):
        return EvolutionService(repository=object())  # type: ignore[arg-type]

    def test_risk_score_safe_no_flags(self, service):
        analysis = CreatorAnalysisRow(
            analyzed_at=datetime(2026, 2, 1), overall_safe=True,
            content_categories={"fitness": 10}, moderation_flags=[],
        )
        assert service._to_risk_score(analysis) == 0.0

    def test_risk_score_unsafe(self, service):
        analysis = CreatorAnalysisRow(
            analyzed_at=datetime(2026, 2, 1), overall_safe=False,
            content_categories={"controversial": 10}, moderation_flags=[],
        )
        assert service._to_risk_score(analysis) == 0.5

    def test_risk_score_with_flags(self, service):
        analysis = CreatorAnalysisRow(
            analyzed_at=datetime(2026, 2, 1), overall_safe=True,
            content_categories={"fitness": 10}, moderation_flags=["flag1", "flag2", "flag3"],
        )
        assert service._to_risk_score(analysis) == pytest.approx(0.3)

    def test_risk_score_capped(self, service):
        analysis = CreatorAnalysisRow(
            analyzed_at=datetime(2026, 2, 1), overall_safe=False,
            content_categories={"dangerous": 10},
            moderation_flags=["f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8"],
        )
        assert service._to_risk_score(analysis) == 1.0

    def test_risk_level_low(self, service):
        analysis = CreatorAnalysisRow(
            analyzed_at=datetime(2026, 2, 1), overall_safe=True,
            content_categories={"fitness": 10}, moderation_flags=[],
        )
        assert service._calculate_risk_level(analysis) == "low"

    def test_risk_level_medium(self, service):
        analysis = CreatorAnalysisRow(
            analyzed_at=datetime(2026, 2, 1), overall_safe=True,
            content_categories={"fitness": 10}, moderation_flags=["flag1", "flag2", "flag3"],
        )
        assert service._calculate_risk_level(analysis) == "medium"

    def test_risk_level_high(self, service):
        analysis = CreatorAnalysisRow(
            analyzed_at=datetime(2026, 2, 1), overall_safe=False,
            content_categories={"edgy": 10}, moderation_flags=["flag1"],
        )
        assert service._calculate_risk_level(analysis) == "high"

    def test_risk_level_critical(self, service):
        analysis = CreatorAnalysisRow(
            analyzed_at=datetime(2026, 2, 1), overall_safe=False,
            content_categories={"dangerous": 10},
            moderation_flags=["f1", "f2", "f3", "f4"],
        )
        assert service._calculate_risk_level(analysis) == "critical"
