"""Tests for CreativePatternService with real DB, mock Gemini analyzer."""

import json
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.analysis.exceptions import VideoProcessingError
from src.creative.service import CreativePatternAnalysisResult, CreativePatternService
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
class TestCreativePatternService:
    """Tests for CreativePatternService with real DB, mock Gemini analyzer."""

    @pytest.fixture
    def mock_analyzer(self):
        analyzer = MagicMock()
        analyzer.analyze_creative_patterns = AsyncMock()
        return analyzer

    @pytest.fixture
    def service(self, mock_analyzer, creative_repo):
        return CreativePatternService(
            analyzer=mock_analyzer,
            repository=creative_repo,
        )

    @pytest.mark.asyncio
    async def test_get_cached(self, service, creative_repo, db_conn, sample_creative_patterns):
        """get_creative_patterns retrieves from real DB."""
        analysis_id = await _seed_video_analysis(db_conn)
        await creative_repo.save(sample_creative_patterns, analysis_id)

        result = await service.get_creative_patterns(analysis_id)

        assert result is not None
        assert result.hook_type == "question"

    @pytest.mark.asyncio
    async def test_get_none(self, service):
        """get_creative_patterns returns None when not found."""
        result = await service.get_creative_patterns(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_analyze_cache_hit(
        self, service, creative_repo, db_conn, sample_creative_patterns
    ):
        """Cache hit returns cached result from real DB."""
        analysis_id = await _seed_video_analysis(db_conn)
        await creative_repo.save(sample_creative_patterns, analysis_id)

        result = await service.analyze_creative_patterns(
            video_path="/tmp/video.mp4",
            video_analysis_id=analysis_id,
            video_id="test123",
        )

        assert result.cached is True
        assert result.patterns.hook_type == "question"

    @pytest.mark.asyncio
    async def test_analyze_cache_miss(
        self, service, mock_analyzer, creative_repo, db_conn, sample_creative_patterns
    ):
        """Cache miss triggers analysis (mock) and saves to real DB."""
        analysis_id = await _seed_video_analysis(db_conn)
        mock_analyzer.analyze_creative_patterns.return_value = sample_creative_patterns

        result = await service.analyze_creative_patterns(
            video_path="/tmp/video.mp4",
            video_analysis_id=analysis_id,
            video_id="test123",
        )

        assert result.cached is False
        assert result.patterns.hook_type == "question"
        mock_analyzer.analyze_creative_patterns.assert_called_once()

        # Verify saved in real DB
        saved = await creative_repo.get_by_analysis_id(analysis_id)
        assert saved is not None

    @pytest.mark.asyncio
    async def test_analyze_force_refresh(
        self, service, mock_analyzer, db_conn, sample_creative_patterns
    ):
        """force_refresh bypasses cache."""
        analysis_id = await _seed_video_analysis(db_conn)
        mock_analyzer.analyze_creative_patterns.return_value = sample_creative_patterns

        result = await service.analyze_creative_patterns(
            video_path="/tmp/video.mp4",
            video_analysis_id=analysis_id,
            video_id="test123",
            force_refresh=True,
        )

        assert result.cached is False
        mock_analyzer.analyze_creative_patterns.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyzer_error_propagates(self, service, mock_analyzer, db_conn):
        """Analyzer raising a non-VideoProcessingError propagates to caller."""
        analysis_id = await _seed_video_analysis(db_conn)
        mock_analyzer.analyze_creative_patterns.side_effect = RuntimeError("Gemini down")

        with pytest.raises(RuntimeError, match="Gemini down"):
            await service.analyze_creative_patterns(
                video_path="/tmp/video.mp4",
                video_analysis_id=analysis_id,
                video_id="test123",
            )

    @pytest.mark.asyncio
    async def test_video_processing_error_saves_sentinel(
        self, service, mock_analyzer, creative_repo, db_conn
    ):
        """VideoProcessingError saves sentinel error record instead of propagating."""
        analysis_id = await _seed_video_analysis(db_conn)
        mock_analyzer.analyze_creative_patterns.side_effect = VideoProcessingError(
            "Creative pattern extraction failed after retries: parse error"
        )

        result = await service.analyze_creative_patterns(
            video_path="/tmp/video.mp4",
            video_analysis_id=analysis_id,
            video_id="test123",
        )

        assert result.cached is False
        assert result.patterns.error is not None
        assert "extraction failed" in result.patterns.error

        # Verify sentinel was persisted to DB
        saved = await creative_repo.get_by_analysis_id(analysis_id)
        assert saved is not None
        assert saved.error is not None

    @pytest.mark.asyncio
    async def test_sentinel_save_failure_still_returns(
        self, mock_analyzer
    ):
        """If sentinel DB save fails, still returns in-memory sentinel."""
        mock_repo = MagicMock()
        mock_repo.get_by_analysis_id = AsyncMock(return_value=None)
        mock_repo.save = AsyncMock(side_effect=RuntimeError("DB down"))

        svc = CreativePatternService(analyzer=mock_analyzer, repository=mock_repo)
        mock_analyzer.analyze_creative_patterns.side_effect = VideoProcessingError("parse failed")

        result = await svc.analyze_creative_patterns(
            video_path="/tmp/video.mp4",
            video_analysis_id=uuid4(),
            video_id="test123",
        )

        assert result.cached is False
        assert result.patterns.error is not None
        assert "parse failed" in result.patterns.error

    @pytest.mark.asyncio
    async def test_save_false_preserves_patterns(
        self, service, mock_analyzer, sample_creative_patterns
    ):
        """Save failure (FK violation) preserves patterns with error annotation."""
        mock_analyzer.analyze_creative_patterns.return_value = sample_creative_patterns

        # Use random UUID with no parent video_analysis → FK violation
        result = await service.analyze_creative_patterns(
            video_path="/tmp/video.mp4",
            video_analysis_id=uuid4(),
            video_id="test123",
        )

        assert result.cached is False
        assert result.patterns.error is not None
        assert "orphaned_result" in result.patterns.error
        # Original data preserved
        assert result.patterns.hook_type == "question"


class TestCreativePatternAnalysisResult:
    """Tests for CreativePatternAnalysisResult dataclass."""

    def test_immutable(self, sample_creative_patterns):
        result = CreativePatternAnalysisResult(
            patterns=sample_creative_patterns,
            cached=True,
        )
        with pytest.raises(AttributeError):
            result.cached = False  # type: ignore

    def test_slots(self, sample_creative_patterns):
        result = CreativePatternAnalysisResult(
            patterns=sample_creative_patterns,
            cached=False,
        )
        assert not hasattr(result, "__dict__")
