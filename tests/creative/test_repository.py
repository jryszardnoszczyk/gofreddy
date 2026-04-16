"""Tests for PostgresCreativePatternRepository with real PostgreSQL."""

import json
from uuid import uuid4

import pytest

from src.creative.repository import PostgresCreativePatternRepository
from src.schemas import CreativePatterns


async def _seed_video_analysis(conn) -> "uuid4":
    """Insert a minimal video_analysis row and return its ID (for FK)."""
    analysis_id = uuid4()
    video_id = uuid4()
    await conn.execute(
        """INSERT INTO video_analysis
           (id, video_id, cache_key, overall_safe, overall_confidence,
            risks_detected, summary, content_categories, moderation_flags,
            model_version)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""",
        analysis_id, video_id, f"test:{uuid4().hex[:8]}:v1",
        True, 0.9, "[]", "Test summary",
        json.dumps([{"vertical": "test", "sub_category": "test", "confidence": 10}]),
        "[]", "1",
    )
    return analysis_id


@pytest.fixture
def sample_creative_patterns():
    return CreativePatterns(
        hook_type="question",
        hook_duration_seconds=3,
        narrative_structure="tutorial",
        cta_type="link_in_bio",
        cta_placement="end",
        pacing="fast_cut",
        music_usage="trending_audio",
        text_overlay_density="moderate",
        hook_confidence=0.92,
        narrative_confidence=0.85,
        cta_confidence=0.78,
        pacing_confidence=0.90,
        music_confidence=0.88,
        text_overlay_confidence=0.75,
        processing_time_seconds=2.1,
        token_count=1200,
        transcript_summary="Test transcript",
        story_arc="Setup then resolution",
        emotional_journey="curiosity to satisfaction",
        protagonist="Test subject",
        theme="Test theme",
        visual_style="Close-up shots",
        audio_style="Clear voiceover",
        scene_beat_map="(1) HOOK 0-3s: close_up static",
    )


@pytest.mark.db
class TestPostgresCreativePatternRepository:
    """Tests for PostgresCreativePatternRepository with real DB."""

    @pytest.mark.asyncio
    async def test_save_and_get(self, creative_repo, db_conn, sample_creative_patterns):
        """Save then retrieve creative patterns from real DB."""
        analysis_id = await _seed_video_analysis(db_conn)
        await creative_repo.save(sample_creative_patterns, analysis_id)

        result = await creative_repo.get_by_analysis_id(analysis_id)

        assert result is not None
        assert result.hook_type == "question"
        assert result.hook_duration_seconds == 3
        assert result.narrative_structure == "tutorial"
        assert result.hook_confidence == 0.92

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, creative_repo):
        """Returns None when not found in real DB."""
        result = await creative_repo.get_by_analysis_id(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_upsert_updates_existing(self, creative_repo, db_conn, sample_creative_patterns):
        """Upsert overwrites existing creative patterns."""
        analysis_id = await _seed_video_analysis(db_conn)
        await creative_repo.save(sample_creative_patterns, analysis_id)

        updated = CreativePatterns(
            hook_type="shock_curiosity",
            narrative_structure="review",
            pacing="slow_cinematic",
            hook_confidence=0.60,
            transcript_summary="Updated transcript",
            story_arc="Updated arc",
            emotional_journey="tension to relief",
            protagonist="Updated subject",
            theme="Updated theme",
            visual_style="Wide angle shots",
            audio_style="Background music",
            scene_beat_map="(1) INTRO 0-5s: wide static",
        )
        result = await creative_repo.save(updated, analysis_id)
        assert result is True

        saved = await creative_repo.get_by_analysis_id(analysis_id)
        assert saved is not None
        assert saved.hook_type == "shock_curiosity"
        assert saved.narrative_structure == "review"
        assert saved.pacing == "slow_cinematic"

    @pytest.mark.asyncio
    async def test_save_fk_violation(self, creative_repo, sample_creative_patterns):
        """Returns False on foreign key violation (real DB constraint)."""
        result = await creative_repo.save(sample_creative_patterns, uuid4())
        assert result is False
