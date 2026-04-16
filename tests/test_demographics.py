"""Tests for Demographics module — real PostgreSQL for DB tests, pure logic for models.

Test isolation: each test runs inside a transaction that rolls back on teardown.
Uses demographics_repo, db_conn fixtures from conftest.py.
"""

import json
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.demographics.service import DemographicsService, DemographicsResult
from src.schemas import (
    AgeBucket,
    AgeDistribution,
    AudienceDemographics,
    GenderDistribution,
    GeographyInference,
    IncomeDistribution,
    InferredInterests,
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
def sample_demographics():
    """Create a sample AudienceDemographics for testing."""
    return AudienceDemographics(
        video_id="test_video_123",
        interests=InferredInterests(
            primary=["fitness", "health", "wellness"],
            confidence=0.82,
            evidence=["gym footage", "protein shake visible"],
        ),
        age_distribution=AgeDistribution(
            teen_13_17=0.05,
            young_adult_18_24=0.45,
            adult_25_34=0.35,
            mid_adult_35_44=0.10,
            mature_45_plus=0.05,
            primary_bucket=AgeBucket.YOUNG_ADULT,
            confidence=0.68,
            evidence=["Gen Z slang", "college setting"],
        ),
        gender_distribution=GenderDistribution(
            male=0.55,
            female=0.45,
            confidence=0.62,
            evidence=["fitness content"],
        ),
        geography=GeographyInference(
            primary_countries=[
                {"country": "US", "probability": 0.70},
                {"country": "UK", "probability": 0.15},
            ],
            primary_language="English (American)",
            confidence=0.75,
            evidence=["American accent", "USD pricing"],
        ),
        income_level=IncomeDistribution(
            low=0.15,
            middle=0.50,
            middle_upper=0.25,
            high=0.10,
            confidence=0.45,
            evidence=["mid-range gym equipment"],
        ),
        overall_confidence=0.66,
        processing_time_seconds=3.2,
        token_count=1850,
    )


@pytest.mark.db
class TestPostgresDemographicsRepository:
    """Tests for PostgresDemographicsRepository with real DB."""

    @pytest.mark.asyncio
    async def test_get_by_analysis_id_found(self, demographics_repo, db_conn, sample_demographics):
        """Save then retrieve demographics from real DB."""
        analysis_id = await _seed_video_analysis(db_conn)
        await demographics_repo.save(sample_demographics, analysis_id)

        result = await demographics_repo.get_by_analysis_id(analysis_id)

        assert result is not None
        assert result.video_id == "test_video_123"
        assert result.overall_confidence == 0.66
        assert result.interests.confidence == 0.82

    @pytest.mark.asyncio
    async def test_get_by_analysis_id_not_found(self, demographics_repo):
        """Returns None when not found in real DB."""
        result = await demographics_repo.get_by_analysis_id(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_save_success(self, demographics_repo, db_conn, sample_demographics):
        """Successful save to real DB."""
        analysis_id = await _seed_video_analysis(db_conn)
        result = await demographics_repo.save(sample_demographics, analysis_id)

        assert result is True

        # Verify in DB
        saved = await demographics_repo.get_by_analysis_id(analysis_id)
        assert saved is not None
        assert saved.interests.primary == ["fitness", "health", "wellness"]

    @pytest.mark.asyncio
    async def test_save_fk_violation(self, demographics_repo, sample_demographics):
        """Returns False on foreign key violation (real DB constraint)."""
        result = await demographics_repo.save(sample_demographics, uuid4())
        assert result is False

    @pytest.mark.asyncio
    async def test_upsert_updates_existing(self, demographics_repo, db_conn, sample_demographics):
        """Upsert overwrites existing demographics."""
        analysis_id = await _seed_video_analysis(db_conn)
        await demographics_repo.save(sample_demographics, analysis_id)

        # Update with different demographics
        updated = AudienceDemographics(
            video_id="updated_video",
            interests=InferredInterests(primary=["gaming"], confidence=0.5, evidence=[]),
            age_distribution=AgeDistribution(
                teen_13_17=0.5, young_adult_18_24=0.5, adult_25_34=0.0,
                mid_adult_35_44=0.0, mature_45_plus=0.0,
                primary_bucket=AgeBucket.TEEN, confidence=0.5, evidence=[],
            ),
            gender_distribution=GenderDistribution(
                male=0.7, female=0.3, confidence=0.5, evidence=[],
            ),
            geography=GeographyInference(
                primary_countries=[], primary_language="English",
                confidence=0.5, evidence=[],
            ),
            income_level=IncomeDistribution(
                low=0.5, middle=0.5, middle_upper=0.0, high=0.0,
                confidence=0.3, evidence=[],
            ),
            overall_confidence=0.4,
        )
        result = await demographics_repo.save(updated, analysis_id)
        assert result is True

        saved = await demographics_repo.get_by_analysis_id(analysis_id)
        assert saved is not None
        assert saved.video_id == "updated_video"
        assert saved.interests.primary == ["gaming"]


@pytest.mark.db
class TestDemographicsService:
    """Tests for DemographicsService with real DB, mock Gemini analyzer."""

    @pytest.fixture
    def mock_analyzer(self):
        """Mock Gemini analyzer (real Gemini deferred to Phase 5)."""
        analyzer = MagicMock()
        analyzer.analyze_demographics = AsyncMock()
        return analyzer

    @pytest.fixture
    def service(self, mock_analyzer, demographics_repo):
        """Create service with mock analyzer + real DB repo."""
        return DemographicsService(
            analyzer=mock_analyzer,
            repository=demographics_repo,
        )

    @pytest.mark.asyncio
    async def test_infer_demographics_cache_hit(
        self, service, demographics_repo, db_conn, sample_demographics
    ):
        """Cache hit returns cached result from real DB."""
        analysis_id = await _seed_video_analysis(db_conn)
        await demographics_repo.save(sample_demographics, analysis_id)

        result = await service.infer_demographics(
            video_path="/tmp/video.mp4",
            video_analysis_id=analysis_id,
            video_id="test123",
        )

        assert result.cached is True
        assert result.demographics.video_id == "test_video_123"

    @pytest.mark.asyncio
    async def test_infer_demographics_cache_miss(
        self, service, mock_analyzer, demographics_repo, db_conn, sample_demographics
    ):
        """Cache miss triggers inference (mock) and saves to real DB."""
        analysis_id = await _seed_video_analysis(db_conn)
        mock_analyzer.analyze_demographics.return_value = sample_demographics

        result = await service.infer_demographics(
            video_path="/tmp/video.mp4",
            video_analysis_id=analysis_id,
            video_id="test123",
        )

        assert result.cached is False
        assert result.demographics.video_id == "test_video_123"
        mock_analyzer.analyze_demographics.assert_called_once()

        # Verify saved in real DB
        saved = await demographics_repo.get_by_analysis_id(analysis_id)
        assert saved is not None

    @pytest.mark.asyncio
    async def test_infer_demographics_force_refresh(
        self, service, mock_analyzer, db_conn, sample_demographics
    ):
        """force_refresh bypasses cache."""
        analysis_id = await _seed_video_analysis(db_conn)
        mock_analyzer.analyze_demographics.return_value = sample_demographics

        result = await service.infer_demographics(
            video_path="/tmp/video.mp4",
            video_analysis_id=analysis_id,
            video_id="test123",
            force_refresh=True,
        )

        assert result.cached is False
        mock_analyzer.analyze_demographics.assert_called_once()

    @pytest.mark.asyncio
    async def test_infer_demographics_caps_income_confidence(
        self, service, mock_analyzer, db_conn
    ):
        """Income confidence is capped at 0.6."""
        analysis_id = await _seed_video_analysis(db_conn)
        high_income_confidence = AudienceDemographics(
            video_id="test123",
            interests=InferredInterests(primary=[], confidence=0.5, evidence=[]),
            age_distribution=AgeDistribution(
                teen_13_17=0.2,
                young_adult_18_24=0.2,
                adult_25_34=0.2,
                mid_adult_35_44=0.2,
                mature_45_plus=0.2,
                primary_bucket=AgeBucket.ADULT,
                confidence=0.5,
                evidence=[],
            ),
            gender_distribution=GenderDistribution(
                male=0.5, female=0.5, confidence=0.5, evidence=[]
            ),
            geography=GeographyInference(
                primary_countries=[], primary_language="English", confidence=0.5, evidence=[]
            ),
            income_level=IncomeDistribution(
                low=0.25,
                middle=0.25,
                middle_upper=0.25,
                high=0.25,
                confidence=0.9,  # HIGH - should be capped
                evidence=[],
            ),
            overall_confidence=0.5,
        )
        mock_analyzer.analyze_demographics.return_value = high_income_confidence

        result = await service.infer_demographics(
            video_path="/tmp/video.mp4",
            video_analysis_id=analysis_id,
            video_id="test123",
        )

        # Income confidence should be capped at 0.6
        assert result.demographics.income_level.confidence == 0.6

    @pytest.mark.asyncio
    async def test_infer_demographics_low_confidence_warning(
        self, service, mock_analyzer, db_conn
    ):
        """Low overall confidence adds warning."""
        analysis_id = await _seed_video_analysis(db_conn)
        low_confidence_result = AudienceDemographics(
            video_id="test123",
            interests=InferredInterests(primary=[], confidence=0.3, evidence=[]),
            age_distribution=AgeDistribution(
                teen_13_17=0.2,
                young_adult_18_24=0.2,
                adult_25_34=0.2,
                mid_adult_35_44=0.2,
                mature_45_plus=0.2,
                primary_bucket=AgeBucket.ADULT,
                confidence=0.3,
                evidence=[],
            ),
            gender_distribution=GenderDistribution(
                male=0.5, female=0.5, confidence=0.3, evidence=[]
            ),
            geography=GeographyInference(
                primary_countries=[], primary_language="English", confidence=0.3, evidence=[]
            ),
            income_level=IncomeDistribution(
                low=0.25, middle=0.25, middle_upper=0.25, high=0.25, confidence=0.3, evidence=[]
            ),
            overall_confidence=0.3,  # LOW - should trigger warning
        )
        mock_analyzer.analyze_demographics.return_value = low_confidence_result

        result = await service.infer_demographics(
            video_path="/tmp/video.mp4",
            video_analysis_id=analysis_id,
            video_id="test123",
        )

        assert result.demographics.error is not None
        assert "low_confidence_warning" in result.demographics.error

    @pytest.mark.asyncio
    async def test_get_demographics(self, service, demographics_repo, db_conn, sample_demographics):
        """get_demographics retrieves from real DB."""
        analysis_id = await _seed_video_analysis(db_conn)
        await demographics_repo.save(sample_demographics, analysis_id)

        result = await service.get_demographics(analysis_id)

        assert result is not None
        assert result.video_id == "test_video_123"

    @pytest.mark.asyncio
    async def test_get_demographics_not_found(self, service):
        """get_demographics returns None when not found."""
        result = await service.get_demographics(uuid4())
        assert result is None


class TestDemographicsResult:
    """Tests for DemographicsResult dataclass."""

    def test_immutable(self, sample_demographics):
        """Test result is immutable."""
        result = DemographicsResult(
            demographics=sample_demographics,
            cached=True,
        )

        with pytest.raises(AttributeError):
            result.cached = False  # type: ignore

    def test_slots(self, sample_demographics):
        """Test result uses slots (no __dict__)."""
        result = DemographicsResult(
            demographics=sample_demographics,
            cached=False,
        )

        # Dataclass with slots=True should not have __dict__
        assert not hasattr(result, "__dict__")


@pytest.mark.db
@pytest.mark.gemini
class TestDemographicsServiceRealGemini:
    """Full pipeline tests: real Gemini demographics inference + real DB."""

    @pytest.fixture
    def service(self, gemini_analyzer, demographics_repo):
        """Real Gemini + real DB."""
        return DemographicsService(
            analyzer=gemini_analyzer,
            repository=demographics_repo,
        )

    @pytest.mark.asyncio
    async def test_full_demographics_inference(
        self, service, demographics_repo, db_conn, test_video_path
    ):
        """Real Gemini demographics → real DB save."""
        analysis_id = await _seed_video_analysis(db_conn)

        result = await service.infer_demographics(
            video_path=str(test_video_path),
            video_analysis_id=analysis_id,
            video_id="gemini_demo_test",
        )

        assert isinstance(result, DemographicsResult)
        assert result.cached is False
        assert result.demographics.video_id == "gemini_demo_test"
        assert result.demographics.overall_confidence > 0.0
        assert result.demographics.interests is not None
        assert result.demographics.age_distribution is not None
        # Income confidence should be capped at 0.6
        assert result.demographics.income_level.confidence <= 0.6

        # Verify saved in real DB
        saved = await demographics_repo.get_by_analysis_id(analysis_id)
        assert saved is not None
        assert saved.video_id == "gemini_demo_test"

    @pytest.mark.asyncio
    async def test_demographics_cache_roundtrip(self, service, db_conn, test_video_path):
        """First call: real Gemini. Second call: cache hit."""
        analysis_id = await _seed_video_analysis(db_conn)

        # First call → cache miss
        result1 = await service.infer_demographics(
            video_path=str(test_video_path),
            video_analysis_id=analysis_id,
            video_id="demo_cache_test",
        )
        assert result1.cached is False

        # Second call → cache hit
        result2 = await service.infer_demographics(
            video_path=str(test_video_path),
            video_analysis_id=analysis_id,
            video_id="demo_cache_test",
        )
        assert result2.cached is True
        assert result2.demographics.video_id == result1.demographics.video_id
