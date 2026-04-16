"""Tests for video fetcher module."""

from datetime import datetime, timezone

import pytest

from src.common.enums import Platform
from src.fetcher.models import (
    BatchFetchResult,
    FetchError,
    FetchErrorType,
    VideoResult,
)
from src.fetcher.protocols import VideoFetcher


class TestVideoResult:
    """Tests for VideoResult dataclass."""

    def test_create_video_result(self):
        """Test creating a VideoResult with required fields."""
        result = VideoResult(
            video_id="abc123",
            platform=Platform.TIKTOK,
            r2_key="videos/tiktok/abc123.mp4",
        )
        assert result.video_id == "abc123"
        assert result.platform == Platform.TIKTOK
        assert result.r2_key == "videos/tiktok/abc123.mp4"

    def test_video_result_with_metadata(self):
        """Test VideoResult with optional metadata."""
        now = datetime.now(timezone.utc)
        result = VideoResult(
            video_id="xyz789",
            platform=Platform.INSTAGRAM,
            r2_key="videos/instagram/xyz789.mp4",
            title="Test Video",
            description="A test video description",
            creator_username="testuser",
            creator_id="user123",
            duration_seconds=60,
            view_count=1000,
            like_count=100,
            comment_count=10,
            posted_at=now,
            file_size_bytes=1024000,
        )
        assert result.title == "Test Video"
        assert result.duration_seconds == 60
        assert result.view_count == 1000

    def test_video_result_immutable(self):
        """Test VideoResult is immutable."""
        result = VideoResult(
            video_id="abc",
            platform=Platform.YOUTUBE,
            r2_key="videos/youtube/abc.mp4",
        )
        with pytest.raises(AttributeError):
            result.video_id = "changed"

    def test_video_result_has_default_fetched_at(self):
        """Test VideoResult gets default fetched_at timestamp."""
        before = datetime.now(timezone.utc)
        result = VideoResult(
            video_id="test",
            platform=Platform.TIKTOK,
            r2_key="videos/tiktok/test.mp4",
        )
        after = datetime.now(timezone.utc)
        assert before <= result.fetched_at <= after


class TestFetchErrorType:
    """Tests for FetchErrorType enum."""

    def test_error_types_exist(self):
        """Test all expected error types exist."""
        assert FetchErrorType.NOT_FOUND.value == "not_found"
        assert FetchErrorType.PRIVATE.value == "private"
        assert FetchErrorType.RATE_LIMITED.value == "rate_limited"
        assert FetchErrorType.NETWORK_ERROR.value == "network_error"
        assert FetchErrorType.PLATFORM_ERROR.value == "platform_error"


class TestFetchError:
    """Tests for FetchError dataclass."""

    def test_create_fetch_error(self):
        """Test creating a FetchError."""
        error = FetchError(
            video_id="vid1",
            platform=Platform.TIKTOK,
            error_type=FetchErrorType.NOT_FOUND,
            message="Video not found on platform",
        )
        assert error.video_id == "vid1"
        assert error.error_type == FetchErrorType.NOT_FOUND
        assert not error.retryable

    def test_fetch_error_retryable(self):
        """Test FetchError with retry info."""
        error = FetchError(
            video_id="vid2",
            platform=Platform.INSTAGRAM,
            error_type=FetchErrorType.RATE_LIMITED,
            message="Rate limit exceeded",
            retryable=True,
            retry_after_seconds=60,
        )
        assert error.retryable
        assert error.retry_after_seconds == 60

    def test_to_agent_message_basic(self):
        """Test agent message formatting."""
        error = FetchError(
            video_id="vid3",
            platform=Platform.YOUTUBE,
            error_type=FetchErrorType.PRIVATE,
            message="Video is private",
        )
        msg = error.to_agent_message()
        assert "private" in msg
        assert "Video is private" in msg

    def test_to_agent_message_with_retry(self):
        """Test agent message includes retry info."""
        error = FetchError(
            video_id="vid4",
            platform=Platform.TIKTOK,
            error_type=FetchErrorType.RATE_LIMITED,
            message="Rate limited",
            retryable=True,
            retry_after_seconds=30,
        )
        msg = error.to_agent_message()
        assert "retry after 30s" in msg

    def test_to_agent_message_with_suggestion(self):
        """Test agent message includes alternative action."""
        error = FetchError(
            video_id="vid5",
            platform=Platform.INSTAGRAM,
            error_type=FetchErrorType.NOT_FOUND,
            message="Video deleted",
            alternative_action="Try fetching from archive",
        )
        msg = error.to_agent_message()
        assert "Suggestion: Try fetching from archive" in msg


class TestBatchFetchResult:
    """Tests for BatchFetchResult dataclass."""

    def test_empty_batch_result(self):
        """Test empty batch result."""
        result = BatchFetchResult(results=[], errors=[])
        assert len(result.results) == 0
        assert len(result.errors) == 0
        assert result.success_rate == 0.0

    def test_batch_result_all_success(self):
        """Test batch with all successful fetches."""
        videos = [
            VideoResult(
                video_id=f"vid{i}",
                platform=Platform.TIKTOK,
                r2_key=f"videos/tiktok/vid{i}.mp4",
            )
            for i in range(5)
        ]
        result = BatchFetchResult(results=videos, errors=[])
        assert result.success_rate == 1.0

    def test_batch_result_all_failures(self):
        """Test batch with all failures."""
        errors = [
            FetchError(
                video_id=f"vid{i}",
                platform=Platform.TIKTOK,
                error_type=FetchErrorType.NOT_FOUND,
                message="Not found",
            )
            for i in range(3)
        ]
        result = BatchFetchResult(results=[], errors=errors)
        assert result.success_rate == 0.0

    def test_batch_result_partial_success(self):
        """Test batch with partial success."""
        videos = [
            VideoResult(
                video_id="vid1",
                platform=Platform.TIKTOK,
                r2_key="videos/tiktok/vid1.mp4",
            )
        ]
        errors = [
            FetchError(
                video_id="vid2",
                platform=Platform.TIKTOK,
                error_type=FetchErrorType.NOT_FOUND,
                message="Not found",
            )
        ]
        result = BatchFetchResult(results=videos, errors=errors)
        assert result.success_rate == 0.5


class TestVideoFetcherProtocol:
    """Tests for VideoFetcher protocol."""

    def test_protocol_defines_fetch_video(self):
        """Test protocol defines fetch_video method."""
        assert hasattr(VideoFetcher, "fetch_video")

    def test_protocol_defines_fetch_creator_videos(self):
        """Test protocol defines fetch_creator_videos method."""
        assert hasattr(VideoFetcher, "fetch_creator_videos")

    def test_mock_implementation_satisfies_protocol(self):
        """Test a mock implementation satisfies the protocol."""

        class MockFetcher:
            async def fetch_video(
                self, platform: Platform, video_id: str
            ) -> VideoResult:
                return VideoResult(
                    video_id=video_id,
                    platform=platform,
                    r2_key=f"videos/{platform.value}/{video_id}.mp4",
                )

            async def fetch_creator_videos(
                self, platform: Platform, creator_handle: str, limit: int = 50
            ) -> BatchFetchResult:
                return BatchFetchResult(results=[], errors=[])

        def use_fetcher(fetcher: VideoFetcher) -> None:
            pass

        # Should not raise TypeError
        use_fetcher(MockFetcher())
