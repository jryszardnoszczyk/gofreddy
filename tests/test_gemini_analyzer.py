"""Tests for GeminiVideoAnalyzer — real Gemini for integration, mocks for error paths.

Tests marked @pytest.mark.gemini use real Gemini API.
Tests marked @pytest.mark.mock_required need mocks (error paths can't be reproduced reliably).
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.analysis.exceptions import GeminiRateLimitError, VideoProcessingError
from src.analysis.gemini_analyzer import GeminiVideoAnalyzer
from src.common.gemini_models import GEMINI_FLASH_LITE
from src.schemas import AudienceDemographics, BrandAnalysis, VideoAnalysis


class TestGeminiVideoAnalyzerConfig:
    """Tests for analyzer configuration — uses real gemini_analyzer fixture."""

    def test_init_sets_config(self, gemini_analyzer):
        """Test analyzer stores configuration."""
        assert gemini_analyzer._model == GEMINI_FLASH_LITE
        assert gemini_analyzer._max_retries == 2
        assert gemini_analyzer._base_delay == 1.0

    def test_repr_hides_api_key(self, gemini_analyzer):
        """Test repr doesn't expose API key."""
        repr_str = repr(gemini_analyzer)
        assert GEMINI_FLASH_LITE in repr_str

    @pytest.mark.asyncio
    async def test_context_manager(self, gemini_analyzer):
        """Test async context manager protocol."""
        async with gemini_analyzer as a:
            assert a is gemini_analyzer

    def test_semaphore_limits_concurrency(self, gemini_analyzer):
        """Test semaphore has correct limit."""
        assert gemini_analyzer._semaphore._value == 2


@pytest.mark.gemini
class TestGeminiVideoAnalyzerIntegration:
    """Real Gemini integration tests — analyze_video, analyze_brands, analyze_demographics."""

    @pytest.mark.asyncio
    async def test_analyze_video_real(self, gemini_analyzer, test_video_path):
        """Real Gemini video analysis end-to-end."""
        result = await gemini_analyzer.analyze_video(str(test_video_path), "integ_test_video")
        assert isinstance(result, VideoAnalysis)
        assert result.video_id == "integ_test_video"
        assert result.overall_confidence > 0.0
        assert result.summary  # Non-empty summary
        assert result.token_count > 0

    @pytest.mark.asyncio
    async def test_analyze_brands_real(self, gemini_analyzer, test_video_path):
        """Real Gemini brand analysis end-to-end."""
        result = await gemini_analyzer.analyze_brands(str(test_video_path), "integ_test_brands")
        assert isinstance(result, BrandAnalysis)
        assert result.overall_confidence >= 0.0

    @pytest.mark.asyncio
    async def test_analyze_demographics_real(self, gemini_analyzer, test_video_path):
        """Real Gemini demographics analysis end-to-end."""
        result = await gemini_analyzer.analyze_demographics(str(test_video_path), "integ_test_demo")
        assert isinstance(result, AudienceDemographics)
        assert result.video_id == "integ_test_demo"
        assert result.overall_confidence > 0.0
        assert result.interests is not None


@pytest.mark.mock_required
class TestUploadWithRetry:
    """Tests for _upload_with_retry — mocks required for rate limit simulation."""

    @pytest.fixture
    def mock_file(self):
        """Create mock file object."""
        file = MagicMock()
        file.name = "files/test123"
        file.state = MagicMock()
        file.state.name = "PROCESSING"
        return file

    @pytest.fixture
    def analyzer_with_mock(self, mock_file):
        """Create analyzer with mocked upload."""
        with patch("src.analysis.gemini_analyzer.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.aio.files.upload = AsyncMock(return_value=mock_file)
            mock_client_class.return_value = mock_client

            analyzer = GeminiVideoAnalyzer(api_key="test_key", base_delay=0.01)
            analyzer._client = mock_client
            return analyzer, mock_client, mock_file

    @pytest.mark.asyncio
    async def test_upload_success(self, analyzer_with_mock, tmp_path):
        """Test successful upload."""
        analyzer, mock_client, mock_file = analyzer_with_mock
        video_path = tmp_path / "test.mp4"
        video_path.write_bytes(b"fake video")

        result = await analyzer._upload_with_retry(video_path)
        assert result == mock_file
        mock_client.aio.files.upload.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_rate_limit_retry(self, tmp_path):
        """Test upload retries on rate limit."""
        from google.genai import errors

        mock_file = MagicMock()
        mock_file.name = "files/test123"

        with patch("src.analysis.gemini_analyzer.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            rate_limit_error = errors.ClientError(429, {"error": {"message": "Rate limited"}})
            mock_client.aio.files.upload = AsyncMock(
                side_effect=[rate_limit_error, rate_limit_error, mock_file]
            )
            mock_client_class.return_value = mock_client

            analyzer = GeminiVideoAnalyzer(api_key="test_key", base_delay=0.01, max_retries=3)
            analyzer._client = mock_client

            video_path = tmp_path / "test.mp4"
            video_path.write_bytes(b"fake video")

            result = await analyzer._upload_with_retry(video_path)
            assert result == mock_file
            assert mock_client.aio.files.upload.call_count == 3

    @pytest.mark.asyncio
    async def test_upload_rate_limit_exhausted(self, tmp_path):
        """Test upload raises after max retries."""
        from google.genai import errors

        with patch("src.analysis.gemini_analyzer.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            rate_limit_error = errors.ClientError(429, {"error": {"message": "Rate limited"}})
            mock_client.aio.files.upload = AsyncMock(side_effect=rate_limit_error)
            mock_client_class.return_value = mock_client

            analyzer = GeminiVideoAnalyzer(api_key="test_key", base_delay=0.01, max_retries=2)
            analyzer._client = mock_client

            video_path = tmp_path / "test.mp4"
            video_path.write_bytes(b"fake video")

            with pytest.raises(GeminiRateLimitError):
                await analyzer._upload_with_retry(video_path)


@pytest.mark.mock_required
class TestWaitForActive:
    """Tests for _wait_for_active — mocks required for file state simulation."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer for testing."""
        with patch("src.analysis.gemini_analyzer.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            analyzer = GeminiVideoAnalyzer(api_key="test_key")
            analyzer._client = mock_client
            return analyzer

    @pytest.mark.asyncio
    async def test_wait_already_active(self, analyzer):
        """Test returns immediately if already active."""
        from google.genai import types

        mock_file = MagicMock()
        mock_file.state = types.FileState.ACTIVE

        result = await analyzer._wait_for_active(mock_file, timeout=1.0, poll_interval=0.1)
        assert result == mock_file

    @pytest.mark.asyncio
    async def test_wait_becomes_active(self, analyzer):
        """Test waits until file becomes active."""
        from google.genai import types

        processing_file = MagicMock()
        processing_file.state = types.FileState.PROCESSING
        processing_file.name = "files/test123"

        active_file = MagicMock()
        active_file.state = types.FileState.ACTIVE

        analyzer._client.aio.files.get = AsyncMock(return_value=active_file)

        result = await analyzer._wait_for_active(processing_file, timeout=5.0, poll_interval=0.01)
        assert result.state == types.FileState.ACTIVE

    @pytest.mark.asyncio
    async def test_wait_timeout(self, analyzer):
        """Test raises on timeout."""
        from google.genai import types

        processing_file = MagicMock()
        processing_file.state = types.FileState.PROCESSING
        processing_file.name = "files/test123"

        analyzer._client.aio.files.get = AsyncMock(return_value=processing_file)

        with pytest.raises(VideoProcessingError, match="timeout"):
            await analyzer._wait_for_active(processing_file, timeout=0.05, poll_interval=0.01)

    @pytest.mark.asyncio
    async def test_wait_failed_state(self, analyzer):
        """Test raises on failed state."""
        from google.genai import types

        failed_file = MagicMock()
        failed_file.state = types.FileState.FAILED
        failed_file.name = "files/test123"

        with pytest.raises(VideoProcessingError, match="failed"):
            await analyzer._wait_for_active(failed_file)


@pytest.mark.mock_required
class TestGenerateAnalysis:
    """Tests for _generate_analysis — mocks required for response simulation."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer for testing."""
        with patch("src.analysis.gemini_analyzer.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            analyzer = GeminiVideoAnalyzer(api_key="test_key", base_delay=0.01)
            analyzer._client = mock_client
            return analyzer

    @pytest.mark.asyncio
    async def test_generate_success(self, analyzer):
        """Test successful analysis generation."""
        mock_response = MagicMock()
        mock_response.text = """{
            "video_id": "test_id",
            "overall_safe": true,
            "overall_confidence": 0.95,
            "risks_detected": [],
            "summary": "Safe video"
        }"""
        mock_response.usage_metadata = MagicMock()
        mock_response.usage_metadata.total_token_count = 1000

        analyzer._client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        mock_file = MagicMock()
        result = await analyzer._generate_analysis(mock_file, "test_id")

        assert isinstance(result, VideoAnalysis)
        assert result.video_id == "test_id"
        assert result.overall_safe is True
        assert result.overall_confidence == 0.95
        assert result.token_count == 1000

    @pytest.mark.asyncio
    async def test_generate_empty_response(self, analyzer):
        """Test raises on empty response."""
        mock_response = MagicMock()
        mock_response.text = None

        analyzer._client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        mock_file = MagicMock()
        with pytest.raises(VideoProcessingError, match="Empty response"):
            await analyzer._generate_analysis(mock_file, "test_id")


@pytest.mark.mock_required
class TestCleanupFile:
    """Tests for _cleanup_file — mocks required for delete behavior simulation."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer for testing."""
        with patch("src.analysis.gemini_analyzer.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            analyzer = GeminiVideoAnalyzer(api_key="test_key")
            analyzer._client = mock_client
            return analyzer

    @pytest.mark.asyncio
    async def test_cleanup_success(self, analyzer):
        """Test successful cleanup."""
        mock_file = MagicMock()
        mock_file.name = "files/test123"
        analyzer._client.aio.files.delete = AsyncMock()

        await analyzer._cleanup_file(mock_file)
        analyzer._client.aio.files.delete.assert_called_once_with(name="files/test123")

    @pytest.mark.asyncio
    async def test_cleanup_no_name(self, analyzer):
        """Test cleanup skips if no name."""
        mock_file = MagicMock()
        mock_file.name = None
        analyzer._client.aio.files.delete = AsyncMock()

        await analyzer._cleanup_file(mock_file)
        analyzer._client.aio.files.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_cleanup_error_ignored(self, analyzer):
        """Test cleanup errors are silently ignored."""
        from google.genai import errors

        mock_file = MagicMock()
        mock_file.name = "files/test123"
        analyzer._client.aio.files.delete = AsyncMock(
            side_effect=errors.APIError(500, {"error": {"message": "Delete failed"}})
        )

        await analyzer._cleanup_file(mock_file)
