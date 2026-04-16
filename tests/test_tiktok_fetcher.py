"""Tests for TikTok video fetcher — real API for integration, mocks for error paths.

Tests marked @pytest.mark.external_api use real ScrapeCreators API.
Tests marked @pytest.mark.mock_required need mocks (error paths can't be reproduced reliably).
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
import respx
import httpx
from httpx import Response

from src.common.enums import Platform
from src.fetcher import TikTokFetcher, VideoResult
from src.fetcher.exceptions import DownloadError, RateLimitError, VideoUnavailableError
from src.storage.r2_storage import VideoMetadata
from tests.fixtures.stable_ids import TIKTOK_CREATOR


@pytest.mark.external_api
class TestTikTokFetcherIntegration:
    """Real ScrapeCreators API integration tests."""

    async def test_search_keyword_real(self, fetchers):
        """Search TikTok by keyword via real ScrapeCreators API."""
        tiktok = fetchers[Platform.TIKTOK]
        results = await tiktok.search_keyword("dance", limit=5)
        assert isinstance(results, list)
        assert len(results) > 0
        assert isinstance(results[0], dict)

    async def test_search_hashtag_real(self, fetchers):
        """Search TikTok by hashtag via real ScrapeCreators API."""
        tiktok = fetchers[Platform.TIKTOK]
        results = await tiktok.search_hashtag("fitness", limit=5)
        assert isinstance(results, list)
        assert len(results) > 0

    async def test_list_creator_videos_real(self, fetchers):
        """List video stats from a real TikTok creator."""
        tiktok = fetchers[Platform.TIKTOK]
        video_stats = await tiktok._list_creator_videos(TIKTOK_CREATOR, limit=3)
        assert isinstance(video_stats, list)
        assert len(video_stats) > 0
        assert all(hasattr(vs, "video_id") for vs in video_stats)

    async def test_fetch_profile_stats_real(self, fetchers):
        """Fetch real TikTok creator profile stats."""
        tiktok = fetchers[Platform.TIKTOK]
        stats = await tiktok.fetch_profile_stats(TIKTOK_CREATOR)
        assert stats.platform == Platform.TIKTOK
        assert stats.follower_count is not None
        assert stats.follower_count > 0


@pytest.mark.mock_required
class TestTikTokFetcherCacheHit:
    """Tests for cache hit scenarios — mocks required to control R2 state."""

    @pytest.fixture
    def mock_storage(self):
        storage = MagicMock()
        storage.exists = AsyncMock(return_value=False)
        storage.upload = AsyncMock()
        storage.get_metadata = AsyncMock(return_value=None)
        return storage

    @pytest.fixture
    def fetcher(self, mock_storage):
        return TikTokFetcher(storage=mock_storage)

    async def test_returns_cached_result_without_api_call(
        self, fetcher, mock_storage
    ):
        """When video exists in R2, return cached result."""
        mock_storage.exists.return_value = True
        mock_storage.get_metadata.return_value = VideoMetadata(
            key="videos/tiktok/123456.mp4",
            platform=Platform.TIKTOK,
            video_id="123456",
            size_bytes=1000,
            last_modified=datetime.now(timezone.utc),
        )

        async with fetcher:
            result = await fetcher.fetch_video(Platform.TIKTOK, "123456")

        assert result.r2_key == "videos/tiktok/123456.mp4"
        assert result.file_size_bytes == 1000
        mock_storage.exists.assert_called_once()
        mock_storage.upload.assert_not_called()


@pytest.mark.mock_required
class TestTikTokFetcherApiErrors:
    """Tests for API error scenarios — mocks required."""

    @pytest.fixture
    def mock_storage(self):
        storage = MagicMock()
        storage.exists = AsyncMock(return_value=False)
        storage.upload = AsyncMock()
        storage.get_metadata = AsyncMock(return_value=None)
        return storage

    @pytest.fixture
    def fetcher(self, mock_storage):
        return TikTokFetcher(storage=mock_storage)

    @respx.mock
    async def test_fetch_video_success(self, fetcher, mock_storage):
        """Test successful video fetch and store flow with transcript."""
        respx.get("https://api.scrapecreators.com/v2/tiktok/video").mock(
            return_value=Response(200, json={
                "aweme_detail": {
                    "aweme_id": "123456",
                    "desc": "Test video description",
                    "video": {
                        "play_addr": {
                            "url_list": ["https://v16-webapp.tiktok.com/video.mp4"]
                        },
                        "duration": 15000,
                    },
                    "statistics": {
                        "play_count": 1000,
                        "digg_count": 100,
                        "comment_count": 50,
                    },
                    "author": {
                        "unique_id": "testuser",
                        "uid": "user123",
                    },
                    "create_time": 1700000000,
                },
                "transcript": "WEBVTT\n\n00:00:00.120 --> 00:00:01.840\nTest transcript content here.\n",
            })
        )

        respx.get("https://v16-webapp.tiktok.com/video.mp4").mock(
            return_value=Response(200, content=b"fake video content")
        )

        async with fetcher:
            result = await fetcher.fetch_video(Platform.TIKTOK, "123456")

        assert isinstance(result, VideoResult)
        assert result.video_id == "123456"
        assert result.platform == Platform.TIKTOK
        assert result.title == "Test video description"
        assert result.creator_username == "testuser"
        assert result.view_count == 1000
        assert result.transcript_text is not None
        assert "Test transcript content here" in result.transcript_text
        mock_storage.upload.assert_called_once()

    @respx.mock
    async def test_fetch_video_no_transcript_field(self, fetcher, mock_storage):
        """When API response has no transcript field, transcript_text is None."""
        respx.get("https://api.scrapecreators.com/v2/tiktok/video").mock(
            return_value=Response(200, json={
                "aweme_detail": {
                    "aweme_id": "123456",
                    "desc": "No transcript video",
                    "video": {
                        "play_addr": {
                            "url_list": ["https://v16-webapp.tiktok.com/video.mp4"]
                        },
                        "duration": 15000,
                    },
                    "statistics": {},
                    "author": {},
                    "create_time": 1700000000,
                },
            })
        )

        respx.get("https://v16-webapp.tiktok.com/video.mp4").mock(
            return_value=Response(200, content=b"fake video content")
        )

        async with fetcher:
            result = await fetcher.fetch_video(Platform.TIKTOK, "123456")

        assert result.transcript_text is None

    @respx.mock
    async def test_video_not_found_raises_error(self, fetcher):
        """Test 404 response raises VideoUnavailableError."""
        respx.get("https://api.scrapecreators.com/v2/tiktok/video").mock(
            return_value=Response(404)
        )

        async with fetcher:
            with pytest.raises(VideoUnavailableError) as exc_info:
                await fetcher.fetch_video(Platform.TIKTOK, "nonexistent")

        assert exc_info.value.video_id == "nonexistent"
        assert exc_info.value.platform == Platform.TIKTOK

    @respx.mock
    async def test_rate_limit_raises_error(self, fetcher):
        """Test 429 response raises RateLimitError."""
        respx.get("https://api.scrapecreators.com/v2/tiktok/video").mock(
            return_value=Response(429, headers={"Retry-After": "60"})
        )

        async with fetcher:
            with pytest.raises(RateLimitError) as exc_info:
                await fetcher.fetch_video(Platform.TIKTOK, "123456")

        assert exc_info.value.retry_after_seconds == 60

    @respx.mock
    async def test_refetch_on_url_expiration(self, fetcher, mock_storage):
        """Test that expired URL triggers re-fetch."""
        call_count = [0]

        def api_response(request):
            call_count[0] += 1
            url = (
                "https://v16-webapp.tiktok.com/video_fresh.mp4"
                if call_count[0] > 1
                else "https://v16-webapp.tiktok.com/video_expired.mp4"
            )
            return Response(200, json={
                "aweme_detail": {
                    "aweme_id": "123456",
                    "desc": "Test",
                    "video": {"play_addr": {"url_list": [url]}},
                    "statistics": {},
                    "author": {},
                }
            })

        respx.get("https://api.scrapecreators.com/v2/tiktok/video").mock(
            side_effect=api_response
        )

        respx.get("https://v16-webapp.tiktok.com/video_expired.mp4").mock(
            return_value=Response(403)
        )

        respx.get("https://v16-webapp.tiktok.com/video_fresh.mp4").mock(
            return_value=Response(200, content=b"video content")
        )

        async with fetcher:
            result = await fetcher.fetch_video(Platform.TIKTOK, "123456")

        assert result.video_id == "123456"
        assert call_count[0] == 2

    @respx.mock
    async def test_provider_timeout_during_video_download(self, fetcher):
        """Provider timeout while downloading content raises DownloadError."""
        respx.get("https://api.scrapecreators.com/v2/tiktok/video").mock(
            return_value=Response(200, json={
                "aweme_detail": {
                    "aweme_id": "123456",
                    "video": {"play_addr": {"url_list": ["https://v16-webapp.tiktok.com/video.mp4"]}},
                }
            })
        )
        respx.get("https://v16-webapp.tiktok.com/video.mp4").mock(
            side_effect=httpx.ReadTimeout("timed out")
        )

        async with fetcher:
            with pytest.raises(DownloadError):
                await fetcher.fetch_video(Platform.TIKTOK, "123456")

    @respx.mock
    async def test_malformed_provider_payload_missing_url_list(self, fetcher):
        """Malformed provider payload (missing URL list) fails fast."""
        respx.get("https://api.scrapecreators.com/v2/tiktok/video").mock(
            return_value=Response(200, json={"aweme_detail": {"video": {"play_addr": {}}}})
        )

        async with fetcher:
            with pytest.raises(ValueError, match="No download URL"):
                await fetcher.fetch_video(Platform.TIKTOK, "123456")

    @respx.mock
    async def test_search_keyword_malformed_payload_returns_empty_list(self, fetcher):
        """Malformed search payload should not crash and should degrade to empty list."""
        respx.get("https://api.scrapecreators.com/v1/tiktok/search/keyword").mock(
            return_value=Response(200, json={"aweme_list": "not-a-list"})
        )

        async with fetcher:
            results = await fetcher.search_keyword("dance", limit=5)

        assert results == []

    @respx.mock
    async def test_fetch_profile_stats_malformed_payload_degrades(self, fetcher):
        """Malformed profile payload should return minimal stats instead of raising."""
        respx.get("https://api.scrapecreators.com/v1/tiktok/profile").mock(
            return_value=Response(200, json={"user": "bad", "stats": "bad"})
        )

        async with fetcher:
            stats = await fetcher.fetch_profile_stats("testuser")

        assert stats.username == "testuser"
        assert stats.platform == Platform.TIKTOK
        assert stats.follower_count is None

    @respx.mock
    async def test_fetch_profile_stats_preserves_zero_counts(self, fetcher):
        """Valid zero values should remain 0, not degrade to None."""
        respx.get("https://api.scrapecreators.com/v1/tiktok/profile").mock(
            return_value=Response(
                200,
                json={
                    "user": {"unique_id": "new_creator"},
                    "stats": {
                        "follower_count": 0,
                        "following_count": 0,
                        "video_count": 0,
                        "heart_count": 0,
                    },
                },
            )
        )

        async with fetcher:
            stats = await fetcher.fetch_profile_stats("new_creator")

        assert stats.follower_count == 0
        assert stats.following_count == 0
        assert stats.video_count == 0
        assert stats.total_likes == 0

    @respx.mock
    async def test_fetch_followers_skips_malformed_rows(self, fetcher):
        """Malformed follower rows should be ignored rather than crashing."""
        respx.get("https://api.scrapecreators.com/v1/tiktok/user/followers").mock(
            return_value=Response(
                200,
                json={
                    "users": [
                        None,
                        "bad",
                        {
                            "unique_id": "valid_follower",
                            "aweme_count": "7",
                            "follower_count": "100",
                            "following_count": "20",
                        },
                    ]
                },
            )
        )

        async with fetcher:
            followers = await fetcher.fetch_followers("testuser", count=50)

        assert len(followers) == 1
        assert followers[0].username == "valid_follower"
        assert followers[0].post_count == 7


class TestTikTokFetcherHandleValidation:
    """Tests for handle validation — pure logic."""

    @pytest.fixture
    def fetcher(self):
        storage = MagicMock()
        storage.exists = AsyncMock(return_value=False)
        return TikTokFetcher(storage=storage)

    async def test_invalid_handle_raises_value_error(self, fetcher):
        """Test that SQL injection attempts are rejected."""
        async with fetcher:
            with pytest.raises(ValueError) as exc_info:
                await fetcher.fetch_creator_videos(
                    Platform.TIKTOK, "'; DROP TABLE--", limit=10
                )

        assert "Invalid handle" in str(exc_info.value)

    def test_valid_handle_accepted(self, fetcher):
        """Test that valid handles pass validation."""
        fetcher._validate_handle("valid_user123")
        fetcher._validate_handle("user.name")
        fetcher._validate_handle("khaby.lame")

    def test_invalid_handle_rejected(self, fetcher):
        """Test that invalid handles fail validation."""
        with pytest.raises(ValueError, match="Invalid handle"):
            fetcher._validate_handle("'; DROP TABLE--")
        with pytest.raises(ValueError, match="Invalid handle"):
            fetcher._validate_handle("<script>alert(1)</script>")
        with pytest.raises(ValueError, match="Invalid handle"):
            fetcher._validate_handle("../../etc/passwd")


class TestTikTokVttParsing:
    """Tests for TikTok VTT transcript parsing — pure logic."""

    def test_parse_vtt_basic(self):
        """Basic VTT is parsed to clean plain text."""
        vtt = (
            "WEBVTT\n\n"
            "00:00:00.120 --> 00:00:01.840\n"
            "Hello world.\n\n"
            "00:00:02.000 --> 00:00:03.500\n"
            "This is a test.\n"
        )
        result = TikTokFetcher._parse_vtt_to_text(vtt)
        assert result == "Hello world. This is a test."

    def test_parse_vtt_returns_none_for_empty(self):
        """Empty VTT (header only) returns None."""
        assert TikTokFetcher._parse_vtt_to_text("WEBVTT\n\n") is None

    def test_parse_vtt_deduplicates_consecutive_lines(self):
        """Consecutive identical lines are deduplicated."""
        vtt = (
            "WEBVTT\n\n"
            "00:00:00.000 --> 00:00:02.000\n"
            "Hello\n\n"
            "00:00:01.000 --> 00:00:03.000\n"
            "Hello\n\n"
            "00:00:02.000 --> 00:00:04.000\n"
            "World\n"
        )
        result = TikTokFetcher._parse_vtt_to_text(vtt)
        assert result == "Hello World"

    def test_parse_vtt_strips_html_tags(self):
        """HTML tags in VTT cues are stripped."""
        vtt = (
            "WEBVTT\n\n"
            "00:00:00.000 --> 00:00:05.000\n"
            "<c.colorE5E5E5>Hello</c> <c.colorCCCCCC>world</c>\n"
        )
        result = TikTokFetcher._parse_vtt_to_text(vtt)
        assert result is not None
        assert "<c." not in result
        assert "Hello" in result
        assert "world" in result

    def test_parse_vtt_oversized_returns_none(self):
        """Oversized VTT input (>1MB) returns None."""
        assert TikTokFetcher._parse_vtt_to_text("x" * 1_100_000) is None
