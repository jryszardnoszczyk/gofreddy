"""Tests for AnalysisService — real PostgreSQL for DB tests, pure logic for models.

Test isolation: each test runs inside a transaction that rolls back on teardown.
Uses analysis_repo, db_conn fixtures from conftest.py.
"""

import shutil
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.analysis.models import VideoAnalysisRecord
from src.analysis.service import AnalysisResult, AnalysisService
from src.common.enums import Platform
from src.schemas import VideoAnalysis


@pytest.mark.db
class TestAnalyze:
    """Tests for analyze method — real DB, mock Gemini analyzer and R2 storage."""

    @pytest.fixture
    def mock_analyzer(self):
        """Mock Gemini analyzer (real Gemini deferred to Phase 5)."""
        analyzer = MagicMock()
        analyzer.analyze_video = AsyncMock()
        return analyzer

    @pytest.fixture
    def mock_storage(self, tmp_path):
        """Mock R2 storage — returns a real temp file."""
        storage = MagicMock()
        temp_file = tmp_path / "temp_video.mp4"
        temp_file.write_bytes(b"fake video")
        storage.download_to_temp = AsyncMock(return_value=temp_file)
        return storage

    @pytest.fixture
    def service(self, mock_analyzer, analysis_repo, mock_storage):
        """Create service with mock analyzer + real DB repo + mock storage."""
        return AnalysisService(
            analyzer=mock_analyzer,
            repository=analysis_repo,
            storage=mock_storage,
        )

    @pytest.mark.asyncio
    async def test_cache_hit(self, service, analysis_repo):
        """Cache hit returns cached result from real DB."""
        video_uuid = uuid4()
        cache_key = service._generate_cache_key(Platform.TIKTOK, "abc123")

        # Seed a real record into the DB
        cached_record = VideoAnalysisRecord(
            id=uuid4(),
            video_id=video_uuid,
            cache_key=cache_key,
            overall_safe=True,
            overall_confidence=0.95,
            risks_detected=[],
            summary="Test summary",
            content_categories=[],
            moderation_flags=[],
            sponsored_content=None,
            processing_time_seconds=5.0,
            token_count=1000,
            error=None,
            model_version="2",
            analyzed_at=datetime.now(timezone.utc),
            analysis_cost_usd=0.01,
        )
        await analysis_repo.save(cached_record)

        result = await service.analyze(
            platform=Platform.TIKTOK,
            video_id="abc123",
            video_uuid=video_uuid,
        )

        assert isinstance(result, AnalysisResult)
        assert result.cached is True
        assert result.cost_usd == 0.0
        assert result.record_id == cached_record.id

    @pytest.mark.asyncio
    async def test_cache_miss_triggers_analysis(
        self, service, mock_analyzer, analysis_repo, mock_storage
    ):
        """Cache miss triggers Gemini analysis and saves to real DB."""
        video_uuid = uuid4()

        mock_analysis = VideoAnalysis(
            video_id="abc123",
            overall_safe=True,
            overall_confidence=0.9,
            risks_detected=[],
            summary="Safe video",
            token_count=500,
        )
        mock_analyzer.analyze_video.return_value = mock_analysis

        result = await service.analyze(
            platform=Platform.TIKTOK,
            video_id="abc123",
            video_uuid=video_uuid,
        )

        assert result.cached is False
        assert result.analysis.overall_safe is True
        mock_analyzer.analyze_video.assert_called_once()

        # Verify saved in real DB
        saved = await analysis_repo.get_by_cache_key(service._generate_cache_key(Platform.TIKTOK, "abc123"))
        assert saved is not None
        assert saved.overall_safe is True
        assert saved.summary == "Safe video"

    @pytest.mark.asyncio
    async def test_force_refresh_bypasses_cache(
        self, service, mock_analyzer, analysis_repo, mock_storage
    ):
        """force_refresh=True bypasses cache and re-analyzes."""
        video_uuid = uuid4()

        # Seed a cached record
        cached_record = VideoAnalysisRecord(
            id=uuid4(),
            video_id=video_uuid,
            cache_key=service._generate_cache_key(Platform.TIKTOK, "refresh_test"),
            overall_safe=True,
            overall_confidence=0.95,
            risks_detected=[],
            summary="Old cached result",
            content_categories=[],
            moderation_flags=[],
            sponsored_content=None,
            processing_time_seconds=5.0,
            token_count=1000,
            error=None,
            model_version="2",
            analyzed_at=datetime.now(timezone.utc),
            analysis_cost_usd=0.01,
        )
        await analysis_repo.save(cached_record)

        mock_analysis = VideoAnalysis(
            video_id="refresh_test",
            overall_safe=False,
            overall_confidence=0.8,
            risks_detected=[],
            summary="Fresh analysis",
            token_count=500,
        )
        mock_analyzer.analyze_video.return_value = mock_analysis

        result = await service.analyze(
            platform=Platform.TIKTOK,
            video_id="refresh_test",
            video_uuid=video_uuid,
            force_refresh=True,
        )

        assert result.cached is False
        assert result.analysis.overall_safe is False
        mock_analyzer.analyze_video.assert_called_once()

    @pytest.mark.asyncio
    async def test_temp_file_cleanup(self, service, mock_analyzer, mock_storage, tmp_path):
        """Temp file is cleaned up after analysis."""
        video_uuid = uuid4()
        temp_file = tmp_path / "temp_video.mp4"
        temp_file.write_bytes(b"fake video")
        mock_storage.download_to_temp.return_value = temp_file

        mock_analysis = VideoAnalysis(
            video_id="cleanup_test",
            overall_safe=True,
            overall_confidence=0.9,
            risks_detected=[],
            summary="Safe video",
        )
        mock_analyzer.analyze_video.return_value = mock_analysis

        await service.analyze(
            platform=Platform.TIKTOK,
            video_id="cleanup_test",
            video_uuid=video_uuid,
        )

        # Temp file should be deleted
        assert not temp_file.exists()


class TestValidateVideoId:
    """Tests for _validate_video_id method."""

    @pytest.fixture
    def service(self):
        """Create service for testing — pure logic, deps never called."""
        return AnalysisService(
            analyzer=object(),  # type: ignore[arg-type]
            repository=object(),  # type: ignore[arg-type]
            storage=object(),  # type: ignore[arg-type]
        )

    def test_valid_ids(self, service):
        """Test valid video IDs pass validation."""
        # Should not raise
        service._validate_video_id("abc123")
        service._validate_video_id("video-id_test")
        service._validate_video_id("A" * 128)

    def test_invalid_ids(self, service):
        """Test invalid video IDs fail validation."""
        with pytest.raises(ValueError, match="Invalid video_id"):
            service._validate_video_id("../etc/passwd")

        with pytest.raises(ValueError, match="Invalid video_id"):
            service._validate_video_id("video/with/slashes")

        with pytest.raises(ValueError, match="Invalid video_id"):
            service._validate_video_id("")

        with pytest.raises(ValueError, match="Invalid video_id"):
            service._validate_video_id("a" * 129)


class TestGenerateCacheKey:
    """Tests for _generate_cache_key method."""

    @pytest.fixture
    def service(self):
        """Create service for testing — pure logic, deps never called."""
        return AnalysisService(
            analyzer=object(),  # type: ignore[arg-type]
            repository=object(),  # type: ignore[arg-type]
            storage=object(),  # type: ignore[arg-type]
        )

    def test_cache_key_format(self, service):
        """Test cache key follows expected format with prompt hash."""
        from src.analysis.service import _PROMPT_HASH
        key = service._generate_cache_key(Platform.TIKTOK, "abc123")
        assert key == f"tiktok:abc123:v{service.ANALYSIS_VERSION}:ph{_PROMPT_HASH}"

    def test_cache_key_different_platforms(self, service):
        """Test cache keys differ by platform."""
        tiktok_key = service._generate_cache_key(Platform.TIKTOK, "abc")
        instagram_key = service._generate_cache_key(Platform.INSTAGRAM, "abc")
        youtube_key = service._generate_cache_key(Platform.YOUTUBE, "abc")

        assert tiktok_key != instagram_key
        assert instagram_key != youtube_key


class TestEstimateCost:
    """Tests for _estimate_cost method."""

    @pytest.fixture
    def service(self):
        """Create service for testing — pure logic, deps never called."""
        return AnalysisService(
            analyzer=object(),  # type: ignore[arg-type]
            repository=object(),  # type: ignore[arg-type]
            storage=object(),  # type: ignore[arg-type]
        )

    def test_cost_calculation(self, service):
        """Test cost is calculated from token count (Gemini 3 Flash blended rate)."""
        analysis = VideoAnalysis(
            video_id="test",
            overall_safe=True,
            overall_confidence=0.9,
            risks_detected=[],
            summary="",
            token_count=1_000_000,
        )

        cost = service._estimate_cost(analysis)
        assert cost == pytest.approx(0.875)  # $0.875/M blended (85% input@$0.50 + 15% output@$3.00)

    def test_zero_tokens(self, service):
        """Test zero cost for no tokens."""
        analysis = VideoAnalysis(
            video_id="test",
            overall_safe=True,
            overall_confidence=0.9,
            risks_detected=[],
            summary="",
            token_count=0,
        )

        cost = service._estimate_cost(analysis)
        assert cost == 0.0


class TestAnalysisResult:
    """Tests for AnalysisResult dataclass."""

    def test_frozen(self):
        """Test result is immutable."""
        analysis = VideoAnalysis(
            video_id="test",
            overall_safe=True,
            overall_confidence=0.9,
            risks_detected=[],
            summary="",
        )

        result = AnalysisResult(
            analysis=analysis,
            cached=True,
            cost_usd=0.0,
            record_id=uuid4(),
        )

        with pytest.raises(AttributeError):
            result.cached = False  # type: ignore

    def test_slots(self):
        """Test result uses slots for memory efficiency."""
        analysis = VideoAnalysis(
            video_id="test",
            overall_safe=True,
            overall_confidence=0.9,
            risks_detected=[],
            summary="",
        )

        result = AnalysisResult(
            analysis=analysis,
            cached=True,
            cost_usd=0.0,
            record_id=uuid4(),
        )

        # Slots means no __dict__
        with pytest.raises(AttributeError):
            result.__dict__


@pytest.mark.db
@pytest.mark.gemini
class TestAnalyzeRealGemini:
    """Full pipeline tests: real Gemini analyzer + real DB, mock R2 storage only."""

    @pytest.fixture
    def mock_storage(self, tmp_path, test_video_path):
        """Mock R2 storage — returns a copy of the real test video."""
        storage = MagicMock()
        temp_file = tmp_path / "temp_video.mp4"
        shutil.copy2(test_video_path, temp_file)
        storage.download_to_temp = AsyncMock(return_value=temp_file)
        return storage

    @pytest.fixture
    def service(self, gemini_analyzer, analysis_repo, mock_storage):
        """Real Gemini + real DB + mock R2."""
        return AnalysisService(
            analyzer=gemini_analyzer,
            repository=analysis_repo,
            storage=mock_storage,
        )

    @pytest.mark.asyncio
    async def test_full_analysis_pipeline(self, service, analysis_repo):
        """Real Gemini analysis → real DB save → verify result shape."""
        video_uuid = uuid4()

        result = await service.analyze(
            platform=Platform.TIKTOK,
            video_id="gemini_pipeline_test",
            video_uuid=video_uuid,
        )

        assert isinstance(result, AnalysisResult)
        assert result.cached is False
        assert result.cost_usd > 0.0
        assert result.analysis.summary  # Non-empty summary from real Gemini
        assert result.analysis.overall_confidence > 0.0

        # Verify persisted in real DB
        saved = await analysis_repo.get_by_cache_key(service._generate_cache_key(Platform.TIKTOK, "gemini_pipeline_test"))
        assert saved is not None
        assert saved.summary == result.analysis.summary

    @pytest.mark.asyncio
    async def test_cache_roundtrip_with_real_gemini(
        self, service, tmp_path, test_video_path
    ):
        """First call: real Gemini. Second call: cache hit from DB."""
        video_uuid = uuid4()

        # First call → cache miss, real analysis
        result1 = await service.analyze(
            platform=Platform.TIKTOK,
            video_id="cache_roundtrip_test",
            video_uuid=video_uuid,
        )
        assert result1.cached is False

        # Re-create storage mock (temp file was deleted by first call)
        temp_file = tmp_path / "temp_video2.mp4"
        shutil.copy2(test_video_path, temp_file)
        service._storage.download_to_temp = AsyncMock(return_value=temp_file)

        # Second call → cache hit
        result2 = await service.analyze(
            platform=Platform.TIKTOK,
            video_id="cache_roundtrip_test",
            video_uuid=video_uuid,
        )
        assert result2.cached is True
        assert result2.cost_usd == 0.0
        assert result2.record_id == result1.record_id
