"""Tests for Instagram video fetcher — real API for integration, mocks for error paths.

Tests marked @pytest.mark.external_api use real Apify API.
Tests marked @pytest.mark.mock_required need mocks (error paths can't be reproduced reliably).
"""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import respx
from httpx import Response

from src.common.enums import Platform
from src.fetcher import InstagramFetcher, VideoResult
from src.fetcher.exceptions import CreatorNotFoundError, DownloadError, VideoUnavailableError
from src.storage.r2_storage import VideoMetadata
from tests.fixtures.stable_ids import INSTAGRAM_CREATOR


@pytest.mark.external_api
class TestInstagramFetcherIntegration:
    """Real Apify API integration tests."""

    async def test_list_creator_videos_real(self, fetchers):
        """List video stats from a real Instagram creator."""
        instagram = fetchers[Platform.INSTAGRAM]
        video_stats = await instagram._list_creator_videos(INSTAGRAM_CREATOR, limit=3)
        assert isinstance(video_stats, list)
        assert len(video_stats) > 0
        assert all(hasattr(vs, "video_id") for vs in video_stats)

    async def test_search_keyword_real(self, fetchers):
        """Search Instagram by keyword via real Apify API."""
        instagram = fetchers[Platform.INSTAGRAM]
        results = await instagram.search_keyword("fitness", limit=5)
        assert isinstance(results, list)
        assert len(results) > 0

    async def test_fetch_profile_stats_real(self, fetchers):
        """Fetch real Instagram creator profile stats."""
        instagram = fetchers[Platform.INSTAGRAM]
        stats = await instagram.fetch_profile_stats(INSTAGRAM_CREATOR)
        assert stats.platform == Platform.INSTAGRAM
        assert stats.follower_count is not None


@pytest.mark.mock_required
class TestInstagramFetcherCacheHit:
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
        return InstagramFetcher(storage=mock_storage)

    async def test_returns_cached_result_without_api_call(
        self, fetcher, mock_storage
    ):
        """When video exists in R2, return cached result."""
        mock_storage.exists.return_value = True
        mock_storage.get_metadata.return_value = VideoMetadata(
            key="videos/instagram/ABC123.mp4",
            platform=Platform.INSTAGRAM,
            video_id="ABC123",
            size_bytes=2000,
            last_modified=datetime.now(timezone.utc),
        )

        async with fetcher:
            result = await fetcher.fetch_video(Platform.INSTAGRAM, "ABC123")

        assert result.r2_key == "videos/instagram/ABC123.mp4"
        assert result.file_size_bytes == 2000
        mock_storage.exists.assert_called_once()
        mock_storage.upload.assert_not_called()

    async def test_cache_hit_does_not_initialize_apify_client(
        self, fetcher, mock_storage
    ):
        """Cache hits should not create external provider clients."""
        mock_storage.exists.return_value = True
        mock_storage.get_metadata.return_value = VideoMetadata(
            key="videos/instagram/ABC123.mp4",
            platform=Platform.INSTAGRAM,
            video_id="ABC123",
            size_bytes=2000,
            last_modified=datetime.now(timezone.utc),
        )

        with patch("src.fetcher.instagram.ApifyClientAsync") as mock_apify_cls:
            async with fetcher:
                await fetcher.fetch_video(Platform.INSTAGRAM, "ABC123")

        mock_apify_cls.assert_not_called()


@pytest.mark.mock_required
class TestInstagramFetcherApiErrors:
    """Tests for Apify API error scenarios — mocks required."""

    @pytest.fixture
    def mock_storage(self):
        storage = MagicMock()
        storage.exists = AsyncMock(return_value=False)
        storage.upload = AsyncMock()
        storage.get_metadata = AsyncMock(return_value=None)
        return storage

    @pytest.fixture
    def mock_apify_client(self):
        client = MagicMock()
        actor_mock = MagicMock()
        actor_mock.call = AsyncMock(return_value={"defaultDatasetId": "dataset123"})
        client.actor = MagicMock(return_value=actor_mock)
        dataset_mock = MagicMock()
        dataset_mock.list_items = AsyncMock()
        client.dataset = MagicMock(return_value=dataset_mock)
        return client

    @pytest.fixture
    def fetcher(self, mock_storage):
        return InstagramFetcher(storage=mock_storage)

    async def test_apify_client_initializes_lazily(
        self, fetcher, mock_apify_client,
    ):
        """Client should be created only when a method actually needs Apify."""
        mock_apify_client.dataset().list_items = AsyncMock(
            return_value=MagicMock(items=[{"shortCode": "ABC123", "id": "1"}])
        )

        with patch("src.fetcher.instagram.ApifyClientAsync", return_value=mock_apify_client) as ctor:
            async with fetcher:
                ctor.assert_not_called()
                result = await fetcher._list_creator_videos("testcreator", limit=1)

        ctor.assert_called_once()
        assert len(result) == 1
        assert result[0].video_id == "ABC123"

    async def test_apify_client_panic_is_wrapped_as_download_error(
        self, fetcher,
    ):
        """BaseException during client init should not crash the process."""

        class _FakePanic(BaseException):
            pass

        with patch("src.fetcher.instagram.ApifyClientAsync", side_effect=_FakePanic("panic")):
            async with fetcher:
                with pytest.raises(DownloadError) as exc_info:
                    await fetcher._list_creator_videos("testcreator", limit=1)

        assert exc_info.value.platform == Platform.INSTAGRAM
        assert exc_info.value.video_id == "apify_client_init"
        assert "Apify client initialization failed" in str(exc_info.value)

    async def test_fetch_video_success(
        self, fetcher, mock_storage, mock_apify_client
    ):
        """Test successful video fetch via Apify."""
        mock_apify_client.dataset().list_items = AsyncMock(
            return_value=MagicMock(
                items=[{
                    "shortCode": "ABC123",
                    "videoUrl": "https://scontent.cdninstagram.com/video.mp4",
                    "caption": "Test reel caption",
                    "ownerUsername": "testcreator",
                    "ownerId": "creator123",
                    "duration": 30,
                    "videoViewCount": 5000,
                    "likesCount": 200,
                    "commentsCount": 25,
                    "timestamp": "2024-01-15T12:00:00Z",
                }]
            )
        )

        with patch("src.fetcher.instagram.ApifyClientAsync", return_value=mock_apify_client):
            async with fetcher:
                with respx.mock:
                    respx.get("https://scontent.cdninstagram.com/video.mp4").mock(
                        return_value=Response(200, content=b"video content")
                    )
                    result = await fetcher.fetch_video(Platform.INSTAGRAM, "ABC123")

        assert isinstance(result, VideoResult)
        assert result.video_id == "ABC123"
        assert result.platform == Platform.INSTAGRAM
        assert result.title == "Test reel caption"
        assert result.creator_username == "testcreator"
        assert result.view_count == 5000
        mock_storage.upload.assert_called_once()

    async def test_video_unavailable_when_no_video_url(
        self, fetcher, mock_apify_client
    ):
        """Test that missing videoUrl raises VideoUnavailableError (image, not video)."""
        mock_apify_client.dataset().list_items = AsyncMock(
            return_value=MagicMock(
                items=[{
                    "shortCode": "ABC123",
                    "displayUrl": "https://scontent.cdninstagram.com/image.jpg",
                }]
            )
        )

        with patch("src.fetcher.instagram.ApifyClientAsync", return_value=mock_apify_client):
            async with fetcher:
                with pytest.raises(VideoUnavailableError) as exc_info:
                    await fetcher.fetch_video(Platform.INSTAGRAM, "ABC123")

        assert exc_info.value.video_id == "ABC123"

    async def test_video_unavailable_when_empty_result(
        self, fetcher, mock_apify_client
    ):
        """Test that empty Apify result raises VideoUnavailableError."""
        mock_apify_client.dataset().list_items = AsyncMock(
            return_value=MagicMock(items=[])
        )

        with patch("src.fetcher.instagram.ApifyClientAsync", return_value=mock_apify_client):
            async with fetcher:
                with pytest.raises(VideoUnavailableError):
                    await fetcher.fetch_video(Platform.INSTAGRAM, "nonexistent")

    async def test_list_creator_videos(
        self, fetcher, mock_apify_client
    ):
        """Test listing reels from a creator's profile."""
        mock_apify_client.dataset().list_items = AsyncMock(
            return_value=MagicMock(
                items=[
                    {"shortCode": "ABC123", "id": "1"},
                    {"shortCode": "DEF456", "id": "2"},
                    {"shortCode": "GHI789", "id": "3"},
                ]
            )
        )

        with patch("src.fetcher.instagram.ApifyClientAsync", return_value=mock_apify_client):
            async with fetcher:
                result = await fetcher._list_creator_videos("testcreator", limit=10)

        assert [r.video_id for r in result] == ["ABC123", "DEF456", "GHI789"]

    async def test_creator_not_found(
        self, fetcher, mock_apify_client
    ):
        """Test that empty creator result raises CreatorNotFoundError."""
        mock_apify_client.dataset().list_items = AsyncMock(
            return_value=MagicMock(items=[])
        )

        with patch("src.fetcher.instagram.ApifyClientAsync", return_value=mock_apify_client):
            async with fetcher:
                with pytest.raises(CreatorNotFoundError) as exc_info:
                    await fetcher._list_creator_videos("nonexistent", limit=10)

        assert exc_info.value.handle == "nonexistent"

    async def test_fetch_video_timeout_from_provider(
        self, fetcher, mock_apify_client
    ):
        """Timeout in provider actor call surfaces as timeout failure."""
        mock_apify_client.actor().call = AsyncMock(
            side_effect=asyncio.TimeoutError("apify timeout")
        )

        with patch("src.fetcher.instagram.ApifyClientAsync", return_value=mock_apify_client):
            async with fetcher:
                with pytest.raises(asyncio.TimeoutError):
                    await fetcher.fetch_video(Platform.INSTAGRAM, "ABC123")

    async def test_list_creator_videos_skips_malformed_items(
        self, fetcher, mock_apify_client
    ):
        """Malformed provider rows should be ignored instead of crashing."""
        mock_apify_client.dataset().list_items = AsyncMock(
            return_value=MagicMock(
                items=[None, "bad_row", {"shortCode": "GOOD123", "id": "1"}]
            )
        )

        with patch("src.fetcher.instagram.ApifyClientAsync", return_value=mock_apify_client):
            async with fetcher:
                result = await fetcher._list_creator_videos("testcreator", limit=10)

        assert [r.video_id for r in result] == ["GOOD123"]

    async def test_search_keyword_disables_apify_log_stream(
        self, fetcher, mock_apify_client
    ):
        """Search calls Apify with logger disabled to avoid noisy log streaming."""
        mock_apify_client.dataset().list_items = AsyncMock(
            return_value=MagicMock(items=[])
        )

        with patch("src.fetcher.instagram.ApifyClientAsync", return_value=mock_apify_client):
            async with fetcher:
                await fetcher.search_keyword("fitness", limit=5)

        call_kwargs = mock_apify_client.actor().call.await_args.kwargs
        assert call_kwargs["logger"] is None


class TestInstagramFetcherHandleValidation:
    """Tests for handle validation — pure logic."""

    @pytest.fixture
    def fetcher(self):
        storage = MagicMock()
        storage.exists = AsyncMock(return_value=False)
        return InstagramFetcher(storage=storage)

    async def test_invalid_handle_raises_value_error(self, fetcher):
        """Test that invalid handles are rejected."""
        async with fetcher:
            with pytest.raises(ValueError) as exc_info:
                await fetcher.fetch_creator_videos(
                    Platform.INSTAGRAM, "<script>alert(1)</script>", limit=10
                )

        assert "Invalid handle" in str(exc_info.value)

    def test_valid_handle_accepted(self, fetcher):
        """Test that valid handles pass validation."""
        fetcher._validate_handle("valid_user123")
        fetcher._validate_handle("user.name")
        fetcher._validate_handle("instagram")

    def test_handle_with_period_accepted(self, fetcher):
        """Test that handles with periods are valid (common on Instagram)."""
        fetcher._validate_handle("user.name")
        fetcher._validate_handle("first.last.name")
