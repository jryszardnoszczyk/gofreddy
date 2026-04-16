"""Tests for Brand Detection module — real PostgreSQL for DB tests, pure logic for models.

Test isolation: each test runs inside a transaction that rolls back on teardown.
Uses brand_repo, db_conn fixtures from conftest.py.
"""

import json
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.brands.service import BrandService, BrandAnalysisResult
from src.schemas import (
    BrandAnalysis,
    BrandContext,
    BrandDetectionSource,
    BrandMention,
    BrandSentiment,
)


# ── Helpers ──────────────────────────────────────────────────────────────────


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
def sample_brand_mention():
    """Create a sample brand mention for testing."""
    return BrandMention(
        brand_name="Nike",
        detection_source=BrandDetectionSource.SPEECH,
        confidence=0.95,
        timestamp_start="1:23",
        sentiment=BrandSentiment.POSITIVE,
        context=BrandContext.ENDORSEMENT,
        evidence="Creator says 'I love my new Nike shoes'",
        is_competitor=False,
    )


@pytest.fixture
def sample_competitor_mention():
    """Create a sample competitor mention for testing."""
    return BrandMention(
        brand_name="Adidas",
        detection_source=BrandDetectionSource.VISUAL_LOGO,
        confidence=0.7,
        sentiment=BrandSentiment.NEUTRAL,
        context=BrandContext.BACKGROUND,
        evidence="Adidas logo visible on clothing in background",
        is_competitor=True,
    )


@pytest.fixture
def sample_brand_analysis(sample_brand_mention, sample_competitor_mention):
    """Create a sample BrandAnalysis for testing."""
    return BrandAnalysis(
        video_id="test_video_123",
        brand_mentions=[sample_brand_mention, sample_competitor_mention],
        primary_brand="Nike",
        overall_sentiment=BrandSentiment.POSITIVE,
        has_sponsorship_signals=True,
        sponsoring_brand="Nike",
        overall_confidence=0.88,
        processing_time_seconds=3.2,
        token_count=1850,
    )


class TestBrandMention:
    """Tests for BrandMention model."""

    def test_valid_brand_mention(self, sample_brand_mention):
        """Test creating a valid brand mention."""
        assert sample_brand_mention.brand_name == "Nike"
        assert sample_brand_mention.confidence == 0.95
        assert sample_brand_mention.is_competitor is False

    def test_competitor_brand_mention(self, sample_competitor_mention):
        """Test brand mention marked as competitor."""
        assert sample_competitor_mention.is_competitor is True
        assert sample_competitor_mention.brand_name == "Adidas"

    def test_timestamp_validation_valid(self):
        """Test valid timestamp formats."""
        valid_timestamps = ["0:00", "0:45", "1:23", "12:34"]
        for ts in valid_timestamps:
            mention = BrandMention(
                brand_name="Test",
                detection_source=BrandDetectionSource.SPEECH,
                confidence=0.8,
                timestamp_start=ts,
                sentiment=BrandSentiment.NEUTRAL,
                context=BrandContext.BACKGROUND,
                evidence="Test evidence",
            )
            assert mention.timestamp_start == ts

    def test_timestamp_validation_invalid(self):
        """Test invalid timestamp formats are rejected."""
        from pydantic import ValidationError

        invalid_timestamps = ["1:2", "123:45", "1:234", "abc", "1:2:3", ""]
        for ts in invalid_timestamps:
            with pytest.raises(ValidationError):
                BrandMention(
                    brand_name="Test",
                    detection_source=BrandDetectionSource.SPEECH,
                    confidence=0.8,
                    timestamp_start=ts,
                    sentiment=BrandSentiment.NEUTRAL,
                    context=BrandContext.BACKGROUND,
                    evidence="Test evidence",
                )

    def test_timestamp_none_allowed(self):
        """Test that None timestamps are allowed."""
        mention = BrandMention(
            brand_name="Test",
            detection_source=BrandDetectionSource.VISUAL_LOGO,
            confidence=0.7,
            timestamp_start=None,
            sentiment=BrandSentiment.NEUTRAL,
            context=BrandContext.BACKGROUND,
            evidence="Logo visible",
        )
        assert mention.timestamp_start is None

    def test_confidence_range_validation(self):
        """Test confidence must be between 0 and 1."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            BrandMention(
                brand_name="Test",
                detection_source=BrandDetectionSource.SPEECH,
                confidence=1.5,  # Invalid
                sentiment=BrandSentiment.POSITIVE,
                context=BrandContext.ENDORSEMENT,
                evidence="Test",
            )

        with pytest.raises(ValidationError):
            BrandMention(
                brand_name="Test",
                detection_source=BrandDetectionSource.SPEECH,
                confidence=-0.1,  # Invalid
                sentiment=BrandSentiment.POSITIVE,
                context=BrandContext.ENDORSEMENT,
                evidence="Test",
            )

    def test_all_detection_sources(self):
        """Test all detection sources are valid."""
        for source in BrandDetectionSource:
            mention = BrandMention(
                brand_name="Test",
                detection_source=source,
                confidence=0.8,
                sentiment=BrandSentiment.NEUTRAL,
                context=BrandContext.BACKGROUND,
                evidence="Test",
            )
            assert mention.detection_source == source

    def test_all_sentiments(self):
        """Test all sentiment values are valid."""
        for sentiment in BrandSentiment:
            mention = BrandMention(
                brand_name="Test",
                detection_source=BrandDetectionSource.SPEECH,
                confidence=0.8,
                sentiment=sentiment,
                context=BrandContext.BACKGROUND,
                evidence="Test",
            )
            assert mention.sentiment == sentiment

    def test_all_contexts(self):
        """Test all context values are valid."""
        for context in BrandContext:
            mention = BrandMention(
                brand_name="Test",
                detection_source=BrandDetectionSource.SPEECH,
                confidence=0.8,
                sentiment=BrandSentiment.NEUTRAL,
                context=context,
                evidence="Test",
            )
            assert mention.context == context


class TestBrandAnalysis:
    """Tests for BrandAnalysis model."""

    def test_empty_analysis(self):
        """Test brand analysis with no brands detected."""
        analysis = BrandAnalysis(
            video_id="test-video-123",
            brand_mentions=[],
            overall_confidence=0.9,
        )
        assert analysis.video_id == "test-video-123"
        assert len(analysis.brand_mentions) == 0
        assert analysis.primary_brand is None
        assert len(analysis.competitor_mentions) == 0

    def test_analysis_with_brands(self, sample_brand_analysis):
        """Test brand analysis with detected brands including competitor."""
        assert len(sample_brand_analysis.brand_mentions) == 2
        assert sample_brand_analysis.primary_brand == "Nike"

    def test_competitor_mentions_property(self, sample_brand_analysis):
        """Test competitor_mentions computed property."""
        competitors = sample_brand_analysis.competitor_mentions
        assert len(competitors) == 1
        assert competitors[0].brand_name == "Adidas"
        assert competitors[0].is_competitor is True

    def test_max_brand_mentions(self):
        """Test brand mentions list has max length of 50."""
        from pydantic import ValidationError

        # Create 51 mentions - should fail
        mentions = [
            BrandMention(
                brand_name=f"Brand{i}",
                detection_source=BrandDetectionSource.SPEECH,
                confidence=0.8,
                sentiment=BrandSentiment.NEUTRAL,
                context=BrandContext.BACKGROUND,
                evidence="Test",
            )
            for i in range(51)
        ]
        with pytest.raises(ValidationError):
            BrandAnalysis(
                video_id="test",
                brand_mentions=mentions,
                overall_confidence=0.8,
            )

    def test_sponsorship_signals(self):
        """Test sponsorship signal fields."""
        analysis = BrandAnalysis(
            video_id="test",
            brand_mentions=[],
            overall_confidence=0.9,
            has_sponsorship_signals=True,
            sponsoring_brand="Nike",
        )
        assert analysis.has_sponsorship_signals is True
        assert analysis.sponsoring_brand == "Nike"

    def test_serialization_roundtrip(self, sample_brand_analysis):
        """Test serialization and deserialization."""
        json_str = sample_brand_analysis.model_dump_json()
        restored = BrandAnalysis.model_validate_json(json_str)

        assert restored.video_id == sample_brand_analysis.video_id
        assert restored.overall_confidence == sample_brand_analysis.overall_confidence
        assert len(restored.brand_mentions) == len(sample_brand_analysis.brand_mentions)
        assert restored.primary_brand == sample_brand_analysis.primary_brand

    def test_error_field(self):
        """Test brand analysis with error."""
        analysis = BrandAnalysis(
            video_id="test",
            brand_mentions=[],
            overall_confidence=0.0,
            error="Analysis failed: video too short",
        )
        assert analysis.error == "Analysis failed: video too short"


@pytest.mark.db
class TestPostgresBrandRepository:
    """Tests for PostgresBrandRepository with real DB."""

    @pytest.mark.asyncio
    async def test_get_by_analysis_id_found(self, brand_repo, db_conn, sample_brand_analysis):
        """Save then retrieve brand analysis from real DB."""
        analysis_id = await _seed_video_analysis(db_conn)
        await brand_repo.save(sample_brand_analysis, analysis_id)

        result = await brand_repo.get_by_analysis_id(analysis_id)

        assert result is not None
        assert result.video_id == "test_video_123"
        assert result.overall_confidence == 0.88
        assert len(result.brand_mentions) == 2

    @pytest.mark.asyncio
    async def test_get_by_analysis_id_not_found(self, brand_repo):
        """Returns None when not found in real DB."""
        result = await brand_repo.get_by_analysis_id(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_save_success(self, brand_repo, db_conn, sample_brand_analysis):
        """Successful save to real DB."""
        analysis_id = await _seed_video_analysis(db_conn)
        result = await brand_repo.save(sample_brand_analysis, analysis_id)

        assert result is True

        # Verify in DB
        saved = await brand_repo.get_by_analysis_id(analysis_id)
        assert saved is not None
        assert saved.primary_brand == "Nike"

    @pytest.mark.asyncio
    async def test_save_fk_violation(self, brand_repo, sample_brand_analysis):
        """Returns False on foreign key violation (real DB constraint)."""
        result = await brand_repo.save(sample_brand_analysis, uuid4())
        assert result is False

    @pytest.mark.asyncio
    async def test_upsert_updates_existing(self, brand_repo, db_conn, sample_brand_analysis):
        """Upsert overwrites existing brand analysis."""
        analysis_id = await _seed_video_analysis(db_conn)
        await brand_repo.save(sample_brand_analysis, analysis_id)

        # Update with different analysis
        updated_analysis = BrandAnalysis(
            video_id="test_video_123",
            brand_mentions=[],
            overall_confidence=0.5,
        )
        result = await brand_repo.save(updated_analysis, analysis_id)
        assert result is True

        # Verify updated
        saved = await brand_repo.get_by_analysis_id(analysis_id)
        assert saved is not None
        assert saved.overall_confidence == 0.5
        assert len(saved.brand_mentions) == 0


@pytest.mark.db
class TestBrandService:
    """Tests for BrandService with real DB, mock Gemini analyzer."""

    @pytest.fixture
    def mock_analyzer(self):
        """Mock Gemini analyzer (real Gemini deferred to Phase 5)."""
        analyzer = MagicMock()
        analyzer.analyze_brands = AsyncMock()
        return analyzer

    @pytest.fixture
    def service(self, mock_analyzer, brand_repo):
        """Create service with mock analyzer + real DB repo."""
        return BrandService(
            analyzer=mock_analyzer,
            repository=brand_repo,
        )

    @pytest.mark.asyncio
    async def test_analyze_brands_cache_hit(
        self, service, brand_repo, db_conn, sample_brand_analysis
    ):
        """Cache hit returns cached result from real DB."""
        analysis_id = await _seed_video_analysis(db_conn)
        await brand_repo.save(sample_brand_analysis, analysis_id)

        result = await service.analyze_brands(
            video_path="/tmp/video.mp4",
            video_analysis_id=analysis_id,
            video_id="test123",
        )

        assert result.cached is True
        assert result.analysis.video_id == "test_video_123"

    @pytest.mark.asyncio
    async def test_analyze_brands_cache_miss(
        self, service, mock_analyzer, brand_repo, db_conn, sample_brand_analysis
    ):
        """Cache miss triggers analysis (mock) and saves to real DB."""
        analysis_id = await _seed_video_analysis(db_conn)
        mock_analyzer.analyze_brands.return_value = sample_brand_analysis

        result = await service.analyze_brands(
            video_path="/tmp/video.mp4",
            video_analysis_id=analysis_id,
            video_id="test123",
        )

        assert result.cached is False
        assert result.analysis.video_id == "test_video_123"
        mock_analyzer.analyze_brands.assert_called_once()

        # Verify saved in real DB
        saved = await brand_repo.get_by_analysis_id(analysis_id)
        assert saved is not None

    @pytest.mark.asyncio
    async def test_analyze_brands_force_refresh(
        self, service, mock_analyzer, db_conn, sample_brand_analysis
    ):
        """force_refresh bypasses cache."""
        analysis_id = await _seed_video_analysis(db_conn)
        mock_analyzer.analyze_brands.return_value = sample_brand_analysis

        result = await service.analyze_brands(
            video_path="/tmp/video.mp4",
            video_analysis_id=analysis_id,
            video_id="test123",
            force_refresh=True,
        )

        assert result.cached is False
        mock_analyzer.analyze_brands.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_brands_save_failure(
        self, service, mock_analyzer, sample_brand_analysis
    ):
        """Save failure (FK violation) handled gracefully."""
        mock_analyzer.analyze_brands.return_value = sample_brand_analysis

        # Use random UUID with no parent video_analysis → FK violation
        result = await service.analyze_brands(
            video_path="/tmp/video.mp4",
            video_analysis_id=uuid4(),
            video_id="test123",
        )

        assert result.cached is False
        assert result.analysis.error is not None
        assert "orphaned_result" in result.analysis.error

    @pytest.mark.asyncio
    async def test_get_brand_analysis(self, service, brand_repo, db_conn, sample_brand_analysis):
        """get_brand_analysis retrieves from real DB."""
        analysis_id = await _seed_video_analysis(db_conn)
        await brand_repo.save(sample_brand_analysis, analysis_id)

        result = await service.get_brand_analysis(analysis_id)

        assert result is not None
        assert result.video_id == "test_video_123"

    @pytest.mark.asyncio
    async def test_get_brand_analysis_not_found(self, service):
        """get_brand_analysis returns None when not found."""
        result = await service.get_brand_analysis(uuid4())
        assert result is None


class TestBrandAnalysisResult:
    """Tests for BrandAnalysisResult dataclass."""

    def test_immutable(self, sample_brand_analysis):
        """Test result is immutable."""
        result = BrandAnalysisResult(
            analysis=sample_brand_analysis,
            cached=True,
        )

        with pytest.raises(AttributeError):
            result.cached = False  # type: ignore

    def test_slots(self, sample_brand_analysis):
        """Test result uses slots (no __dict__)."""
        result = BrandAnalysisResult(
            analysis=sample_brand_analysis,
            cached=False,
        )

        # Dataclass with slots=True should not have __dict__
        assert not hasattr(result, "__dict__")


class TestBrandEnums:
    """Tests for brand-related enums."""

    def test_brand_detection_source_values(self):
        """Test all detection sources have expected values."""
        expected = ["speech", "text_overlay", "visual_logo", "hashtag"]
        actual = [source.value for source in BrandDetectionSource]
        assert sorted(actual) == sorted(expected)

    def test_brand_sentiment_values(self):
        """Test all sentiment values are defined."""
        expected = ["positive", "neutral", "negative", "mixed"]
        actual = [sentiment.value for sentiment in BrandSentiment]
        assert sorted(actual) == sorted(expected)

    def test_brand_context_values(self):
        """Test all context values are defined."""
        expected = ["endorsement", "comparison", "background", "criticism", "sponsored", "review"]
        actual = [context.value for context in BrandContext]
        assert sorted(actual) == sorted(expected)

    def test_enums_are_strenum(self):
        """Verify enums use StrEnum for cleaner serialization."""
        assert BrandDetectionSource.SPEECH == "speech"
        assert str(BrandDetectionSource.SPEECH) == "speech"
        assert BrandSentiment.POSITIVE == "positive"
        assert BrandContext.ENDORSEMENT == "endorsement"


@pytest.mark.db
@pytest.mark.gemini
class TestBrandServiceRealGemini:
    """Full pipeline tests: real Gemini brand analysis + real DB."""

    @pytest.fixture
    def service(self, gemini_analyzer, brand_repo):
        """Real Gemini + real DB."""
        return BrandService(
            analyzer=gemini_analyzer,
            repository=brand_repo,
        )

    @pytest.mark.asyncio
    async def test_full_brand_analysis(self, service, brand_repo, db_conn, test_video_path):
        """Real Gemini brand detection → real DB save."""
        analysis_id = await _seed_video_analysis(db_conn)

        result = await service.analyze_brands(
            video_path=str(test_video_path),
            video_analysis_id=analysis_id,
            video_id="gemini_brand_test",
        )

        assert isinstance(result, BrandAnalysisResult)
        assert result.cached is False
        assert result.analysis.video_id == "gemini_brand_test"
        assert isinstance(result.analysis.brand_mentions, list)
        assert result.analysis.overall_confidence >= 0.0

        # Verify saved in real DB
        saved = await brand_repo.get_by_analysis_id(analysis_id)
        assert saved is not None
        assert saved.video_id == "gemini_brand_test"

    @pytest.mark.asyncio
    async def test_brand_cache_roundtrip(self, service, db_conn, test_video_path):
        """First call: real Gemini. Second call: cache hit."""
        analysis_id = await _seed_video_analysis(db_conn)

        # First call → cache miss
        result1 = await service.analyze_brands(
            video_path=str(test_video_path),
            video_analysis_id=analysis_id,
            video_id="brand_cache_test",
        )
        assert result1.cached is False

        # Second call → cache hit
        result2 = await service.analyze_brands(
            video_path=str(test_video_path),
            video_analysis_id=analysis_id,
            video_id="brand_cache_test",
        )
        assert result2.cached is True
