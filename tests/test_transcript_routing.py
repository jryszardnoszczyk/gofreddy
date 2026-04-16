"""Tests for transcript-first lane routing integration."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.analysis.config import LaneRoutingSettings
from src.analysis.lane_selector import AnalysisLane
from src.analysis.service import AnalysisResult, AnalysisService
from src.common.enums import Platform
from src.schemas import VideoAnalysis


def _make_video_analysis(video_id: str = "test123") -> VideoAnalysis:
    """Create a minimal VideoAnalysis for testing."""
    return VideoAnalysis(
        video_id=video_id,
        overall_safe=True,
        overall_confidence=0.95,
        risks_detected=[],
        summary="Test analysis",
        content_categories=[],
        moderation_flags=[],
        sponsored_content=None,
        processing_time_seconds=0.01,
        token_count=1234,
        error=None,
    )


class TestTranscriptRouting:
    """Integration tests for analysis service lane routing."""

    @pytest.fixture
    def mock_analyzer(self):
        analyzer = MagicMock()
        analyzer.analyze_video = AsyncMock(return_value=_make_video_analysis())
        analyzer.analyze_transcript = AsyncMock(return_value=_make_video_analysis())
        return analyzer

    @pytest.fixture
    def mock_storage(self, tmp_path):
        storage = MagicMock()
        temp_file = tmp_path / "temp_video.mp4"
        temp_file.write_bytes(b"fake video")
        storage.download_to_temp = AsyncMock(return_value=temp_file)
        return storage

    @pytest.fixture
    def mock_repo(self):
        repo = MagicMock()
        repo.get_by_cache_key = AsyncMock(return_value=None)
        repo.save = AsyncMock(side_effect=lambda r: r)
        repo.grant_user_access = AsyncMock()
        return repo

    @pytest.fixture
    def lane_settings_enabled(self):
        return LaneRoutingSettings(
            transcript_first_enabled=True,
            quality_threshold=0.6,
        )

    @pytest.fixture
    def lane_settings_disabled(self):
        return LaneRoutingSettings(
            transcript_first_enabled=False,
            quality_threshold=0.6,
        )

    @pytest.mark.asyncio
    async def test_l1_route_with_good_transcript(
        self, mock_analyzer, mock_repo, mock_storage, lane_settings_enabled
    ):
        """Flag enabled + high-quality transcript → L1 (analyze_transcript called)."""
        service = AnalysisService(
            analyzer=mock_analyzer,
            repository=mock_repo,
            storage=mock_storage,
            lane_settings=lane_settings_enabled,
        )

        transcript = " ".join(["hello"] * 200)  # 200 words → quality 1.0

        result = await service.analyze(
            platform=Platform.YOUTUBE,
            video_id="test123",
            video_uuid=uuid4(),
            transcript_text=transcript,
            duration_seconds=60,
        )

        assert result.lane == AnalysisLane.L1_TRANSCRIPT_FIRST
        assert result.cached is False
        mock_analyzer.analyze_transcript.assert_awaited_once()
        mock_analyzer.analyze_video.assert_not_awaited()
        # L1 should NOT download the video
        mock_storage.download_to_temp.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_l2_route_with_flag_disabled(
        self, mock_analyzer, mock_repo, mock_storage, lane_settings_disabled
    ):
        """Flag disabled → L2 regardless of transcript availability."""
        service = AnalysisService(
            analyzer=mock_analyzer,
            repository=mock_repo,
            storage=mock_storage,
            lane_settings=lane_settings_disabled,
        )

        transcript = " ".join(["hello"] * 200)

        result = await service.analyze(
            platform=Platform.YOUTUBE,
            video_id="test123",
            video_uuid=uuid4(),
            transcript_text=transcript,
            duration_seconds=60,
        )

        assert result.lane == AnalysisLane.L2_MULTIMODAL_AUDIO
        mock_analyzer.analyze_video.assert_awaited_once()
        mock_analyzer.analyze_transcript.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_l2_route_with_low_quality_transcript(
        self, mock_analyzer, mock_repo, mock_storage, lane_settings_enabled
    ):
        """Flag enabled + low-quality transcript → L2."""
        service = AnalysisService(
            analyzer=mock_analyzer,
            repository=mock_repo,
            storage=mock_storage,
            lane_settings=lane_settings_enabled,
        )

        transcript = " ".join(["word"] * 10)  # 10 words → quality 0.0

        result = await service.analyze(
            platform=Platform.YOUTUBE,
            video_id="test123",
            video_uuid=uuid4(),
            transcript_text=transcript,
            duration_seconds=60,
        )

        assert result.lane == AnalysisLane.L2_MULTIMODAL_AUDIO
        mock_analyzer.analyze_video.assert_awaited_once()
        mock_analyzer.analyze_transcript.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_l2_route_with_no_transcript(
        self, mock_analyzer, mock_repo, mock_storage, lane_settings_enabled
    ):
        """Flag enabled + no transcript → L2."""
        service = AnalysisService(
            analyzer=mock_analyzer,
            repository=mock_repo,
            storage=mock_storage,
            lane_settings=lane_settings_enabled,
        )

        result = await service.analyze(
            platform=Platform.YOUTUBE,
            video_id="test123",
            video_uuid=uuid4(),
            transcript_text=None,
        )

        assert result.lane == AnalysisLane.L2_MULTIMODAL_AUDIO
        mock_analyzer.analyze_video.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_cached_result_has_no_lane(
        self, mock_analyzer, mock_storage, lane_settings_enabled
    ):
        """Cached results return lane=None."""
        from src.analysis.models import VideoAnalysisRecord

        cached_record = MagicMock(spec=VideoAnalysisRecord)
        cached_record.id = uuid4()
        cached_record.to_video_analysis.return_value = _make_video_analysis()

        repo = MagicMock()
        repo.get_by_cache_key = AsyncMock(return_value=cached_record)
        repo.grant_user_access = AsyncMock()

        service = AnalysisService(
            analyzer=mock_analyzer,
            repository=repo,
            storage=mock_storage,
            lane_settings=lane_settings_enabled,
        )

        result = await service.analyze(
            platform=Platform.TIKTOK,
            video_id="abc123",
            video_uuid=uuid4(),
            transcript_text=" ".join(["word"] * 200),
        )

        assert result.cached is True
        assert result.lane is None


class TestFakeVideoAnalyzerTranscript:
    """Test that FakeVideoAnalyzer has analyze_transcript."""

    @pytest.mark.asyncio
    async def test_fake_analyzer_returns_valid_analysis(self):
        from src.api.fake_externals import FakeVideoAnalyzer

        analyzer = FakeVideoAnalyzer()
        result = await analyzer.analyze_transcript("hello world " * 100, "test123")
        assert isinstance(result, VideoAnalysis)
        assert result.video_id == "test123"
        assert result.overall_safe is True


class TestYouTubeVttExtraction:
    """Tests for YouTube VTT transcript extraction."""

    def test_parse_vtt_basic(self, tmp_path):
        from src.fetcher.youtube import YouTubeFetcher

        vtt_content = """WEBVTT

00:00:00.000 --> 00:00:05.000
Hello world this is a test

00:00:05.000 --> 00:00:10.000
Another line of text here
"""
        vtt_file = tmp_path / "test.vtt"
        vtt_file.write_text(vtt_content)

        result = YouTubeFetcher._parse_vtt_to_text(vtt_file)
        assert result is not None
        assert "Hello world this is a test" in result
        assert "Another line of text here" in result

    def test_parse_vtt_strips_html_tags(self, tmp_path):
        from src.fetcher.youtube import YouTubeFetcher

        vtt_content = """WEBVTT

00:00:00.000 --> 00:00:05.000
<c.colorE5E5E5>Hello</c> <c.colorCCCCCC>world</c>
"""
        vtt_file = tmp_path / "test.vtt"
        vtt_file.write_text(vtt_content)

        result = YouTubeFetcher._parse_vtt_to_text(vtt_file)
        assert result is not None
        assert "<c." not in result
        assert "Hello" in result
        assert "world" in result

    def test_parse_vtt_deduplicates_consecutive_lines(self, tmp_path):
        from src.fetcher.youtube import YouTubeFetcher

        vtt_content = """WEBVTT

00:00:00.000 --> 00:00:05.000
Hello world

00:00:03.000 --> 00:00:08.000
Hello world

00:00:05.000 --> 00:00:10.000
New content here
"""
        vtt_file = tmp_path / "test.vtt"
        vtt_file.write_text(vtt_content)

        result = YouTubeFetcher._parse_vtt_to_text(vtt_file)
        assert result is not None
        # "Hello world" should appear only once
        assert result.count("Hello world") == 1
        assert "New content here" in result

    def test_parse_vtt_skips_numeric_cue_ids(self, tmp_path):
        from src.fetcher.youtube import YouTubeFetcher

        vtt_content = """WEBVTT

1
00:00:00.000 --> 00:00:05.000
Line one

2
00:00:05.000 --> 00:00:10.000
Line two
"""
        vtt_file = tmp_path / "test.vtt"
        vtt_file.write_text(vtt_content)

        result = YouTubeFetcher._parse_vtt_to_text(vtt_file)
        assert result is not None
        assert "1" not in result.split(" ")[0]  # "1" is not at start
        assert "Line one" in result
        assert "Line two" in result

    def test_parse_vtt_empty_file_returns_none(self, tmp_path):
        from src.fetcher.youtube import YouTubeFetcher

        vtt_file = tmp_path / "test.vtt"
        vtt_file.write_text("WEBVTT\n\n")

        result = YouTubeFetcher._parse_vtt_to_text(vtt_file)
        assert result is None

    def test_parse_vtt_oversized_file_returns_none(self, tmp_path):
        from src.fetcher.youtube import YouTubeFetcher

        vtt_file = tmp_path / "test.vtt"
        # Write > 1MB
        vtt_file.write_text("x" * 1_100_000)

        result = YouTubeFetcher._parse_vtt_to_text(vtt_file)
        assert result is None

    def test_extract_vtt_finds_en_file(self, tmp_path):
        from src.fetcher.youtube import YouTubeFetcher

        # Create a VTT file matching the expected pattern
        vtt_content = """WEBVTT

00:00:00.000 --> 00:00:05.000
Subtitle content here
"""
        vtt_file = tmp_path / "testvid.en.vtt"
        vtt_file.write_text(vtt_content)

        fetcher = object.__new__(YouTubeFetcher)
        result = fetcher._extract_vtt_transcript(tmp_path, "testvid")
        assert result is not None
        assert "Subtitle content here" in result

    def test_extract_vtt_glob_fallback(self, tmp_path):
        from src.fetcher.youtube import YouTubeFetcher

        # Create VTT with non-standard name
        vtt_content = """WEBVTT

00:00:00.000 --> 00:00:05.000
Fallback content
"""
        vtt_file = tmp_path / "testvid.en-US.vtt"
        vtt_file.write_text(vtt_content)

        fetcher = object.__new__(YouTubeFetcher)
        result = fetcher._extract_vtt_transcript(tmp_path, "testvid")
        assert result is not None
        assert "Fallback content" in result

    def test_extract_vtt_no_file_returns_none(self, tmp_path):
        from src.fetcher.youtube import YouTubeFetcher

        fetcher = object.__new__(YouTubeFetcher)
        result = fetcher._extract_vtt_transcript(tmp_path, "testvid")
        assert result is None


class TestTikTokTranscriptNone:
    """Test that TikTok fetcher returns transcript_text=None."""

    def test_video_result_default_transcript_none(self):
        """VideoResult defaults transcript_text to None."""
        from src.fetcher.models import VideoResult

        result = VideoResult(
            video_id="123",
            platform=Platform.TIKTOK,
            r2_key="videos/tiktok/123.mp4",
        )
        assert result.transcript_text is None
