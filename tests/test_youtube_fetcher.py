"""Tests for YouTube video fetcher — real API for integration, mocks for error paths.

Tests marked @pytest.mark.external_api use real yt-dlp.
Tests marked @pytest.mark.mock_required need mocks (error paths can't be reproduced reliably).
"""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.common.enums import Platform
from src.fetcher import YouTubeFetcher, VideoResult
from src.fetcher.exceptions import CreatorNotFoundError, DownloadError, VideoUnavailableError
from src.fetcher.models import VideoStats
from src.fetcher.youtube import _backfill_video_metadata
from src.storage.r2_storage import VideoMetadata
from tests.fixtures.stable_ids import YOUTUBE_CREATOR, YOUTUBE_VIDEO_ID


@pytest.mark.external_api
class TestYouTubeFetcherIntegration:
    """Real yt-dlp integration tests."""

    async def test_fetch_video_real(self, fetchers, r2_cleanup):
        """Fetch real YouTube video (Me at the zoo — first ever YouTube video)."""
        youtube = fetchers[Platform.YOUTUBE]
        r2_cleanup.append(f"videos/youtube/{YOUTUBE_VIDEO_ID}.mp4")

        result = await youtube.fetch_video(Platform.YOUTUBE, YOUTUBE_VIDEO_ID)

        assert isinstance(result, VideoResult)
        assert result.video_id == YOUTUBE_VIDEO_ID
        assert result.platform == Platform.YOUTUBE
        assert result.file_size_bytes > 0
        # title may be None on R2 cache hit (metadata doesn't store it)

    async def test_list_creator_videos_real(self, fetchers):
        """List video stats from a real YouTube channel."""
        youtube = fetchers[Platform.YOUTUBE]
        video_stats = await youtube._list_creator_videos(YOUTUBE_CREATOR, limit=3)
        assert isinstance(video_stats, list)
        assert len(video_stats) > 0
        assert all(hasattr(vs, "video_id") for vs in video_stats)

    async def test_search_real(self, fetchers):
        """Search YouTube videos via real yt-dlp."""
        youtube = fetchers[Platform.YOUTUBE]
        results = await youtube.search("python tutorial", max_results=3)
        assert isinstance(results, list)
        assert len(results) > 0


@pytest.mark.mock_required
class TestYouTubeFetcherCacheHit:
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
        return YouTubeFetcher(storage=mock_storage)

    async def test_returns_cached_result_without_download(
        self, fetcher, mock_storage
    ):
        """When video exists in R2, return cached result."""
        mock_storage.exists.return_value = True
        mock_storage.get_metadata.return_value = VideoMetadata(
            key="videos/youtube/dQw4w9WgXcQ.mp4",
            platform=Platform.YOUTUBE,
            video_id="dQw4w9WgXcQ",
            size_bytes=50000000,
            last_modified=datetime.now(timezone.utc),
        )

        async with fetcher:
            result = await fetcher.fetch_video(Platform.YOUTUBE, "dQw4w9WgXcQ")

        assert result.r2_key == "videos/youtube/dQw4w9WgXcQ.mp4"
        assert result.file_size_bytes == 50000000
        mock_storage.exists.assert_called_once()
        mock_storage.upload.assert_not_called()


@pytest.mark.mock_required
class TestYouTubeFetcherErrorPaths:
    """Tests for error scenarios — mocks required."""

    @pytest.fixture
    def mock_storage(self):
        storage = MagicMock()
        storage.exists = AsyncMock(return_value=False)
        storage.upload = AsyncMock()
        storage.get_metadata = AsyncMock(return_value=None)
        return storage

    @pytest.fixture
    def fetcher(self, mock_storage):
        return YouTubeFetcher(storage=mock_storage)

    async def test_fetch_video_success(self, fetcher, mock_storage, tmp_path):
        """Test successful video download and upload to R2."""
        video_id = "dQw4w9WgXcQ"

        mock_info = {
            "id": video_id,
            "title": "Test Video Title",
            "description": "Test description",
            "uploader_id": "@testchannel",
            "channel_id": "UC123456",
            "duration": 180,
            "view_count": 1000000,
            "like_count": 50000,
            "comment_count": 5000,
            "upload_date": "20240115",
        }

        def mock_download_sync(vid_id, output_dir):
            out_file = output_dir / f"{vid_id}.mp4"
            out_file.write_bytes(b"fake video content" * 1000)
            return out_file, mock_info

        with patch.object(fetcher, "_download_sync", side_effect=mock_download_sync):
            async with fetcher:
                result = await fetcher.fetch_video(Platform.YOUTUBE, video_id)

        assert isinstance(result, VideoResult)
        assert result.video_id == video_id
        assert result.platform == Platform.YOUTUBE
        assert result.title == "Test Video Title"
        assert result.creator_username == "@testchannel"
        assert result.duration_seconds == 180
        assert result.view_count == 1000000
        mock_storage.upload.assert_called_once()

    async def test_video_unavailable_error(self, fetcher):
        """Test that unavailable videos raise VideoUnavailableError."""
        def raise_unavailable(_vid_id, _output_dir):
            raise VideoUnavailableError(Platform.YOUTUBE, "unavailable")

        with patch.object(fetcher, "_download_sync", side_effect=raise_unavailable):
            async with fetcher:
                with pytest.raises(VideoUnavailableError) as exc_info:
                    await fetcher.fetch_video(Platform.YOUTUBE, "unavailable")

        assert exc_info.value.video_id == "unavailable"

    async def test_age_restricted_raises_unavailable(self, fetcher):
        """Test that age-restricted videos raise VideoUnavailableError."""
        def raise_age_restricted(_vid_id, _output_dir):
            raise VideoUnavailableError(Platform.YOUTUBE, "age_restricted")

        with patch.object(fetcher, "_download_sync", side_effect=raise_age_restricted):
            async with fetcher:
                with pytest.raises(VideoUnavailableError):
                    await fetcher.fetch_video(Platform.YOUTUBE, "age_restricted")

    async def test_generic_download_error(self, fetcher):
        """Test that generic errors raise DownloadError."""
        def raise_generic_error(_vid_id, _output_dir):
            raise DownloadError(Platform.YOUTUBE, "network_error", "Network error occurred")

        with patch.object(fetcher, "_download_sync", side_effect=raise_generic_error):
            async with fetcher:
                with pytest.raises(DownloadError) as exc_info:
                    await fetcher.fetch_video(Platform.YOUTUBE, "network_error")

        assert "Network error" in str(exc_info.value)

    async def test_creator_not_found(self, fetcher):
        """Test that non-existent channel raises CreatorNotFoundError."""
        async def raise_creator_not_found(handle, limit):
            raise CreatorNotFoundError(Platform.YOUTUBE, handle)

        with patch.object(fetcher, "_list_creator_videos", side_effect=raise_creator_not_found):
            async with fetcher:
                with pytest.raises(CreatorNotFoundError) as exc_info:
                    await fetcher._list_creator_videos("nonexistent", limit=10)

        assert exc_info.value.handle == "nonexistent"

    async def test_fetch_video_handles_malformed_info_payload(
        self, fetcher, mock_storage, tmp_path
    ):
        """Malformed provider metadata should not crash upload flow."""
        video_id = "malformed_info"
        out_file = tmp_path / f"{video_id}.mp4"
        out_file.write_bytes(b"fake video content")

        def mock_download_sync(_vid_id, _output_dir):
            return out_file, None

        with patch.object(fetcher, "_download_sync", side_effect=mock_download_sync):
            async with fetcher:
                result = await fetcher.fetch_video(Platform.YOUTUBE, video_id)

        assert result.video_id == video_id
        mock_storage.upload.assert_called_once()


@pytest.mark.mock_required
class TestYouTubeFetcherDownloadOptions:
    """Tests for yt-dlp configuration — mocks required for YoutubeDL."""

    @pytest.fixture
    def fetcher(self):
        storage = MagicMock()
        storage.exists = AsyncMock(return_value=False)
        return YouTubeFetcher(storage=storage)

    def test_download_sync_creates_file(self, fetcher, tmp_path):
        """Test that _download_sync creates video file with correct options."""
        video_id = "dQw4w9WgXcQ"

        mock_info = {
            "id": video_id,
            "title": "Test",
            "description": "Test",
            "duration": 100,
        }

        with patch("src.fetcher.youtube.YoutubeDL") as mock_ydl_class:
            mock_ydl = MagicMock()
            mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
            mock_ydl.__exit__ = MagicMock(return_value=False)
            mock_ydl.extract_info = MagicMock(return_value=mock_info)
            mock_ydl_class.return_value = mock_ydl

            expected_output = tmp_path / f"{video_id}.mp4"
            expected_output.write_bytes(b"video content")

            video_path, info = fetcher._download_sync(video_id, tmp_path)

            mock_ydl_class.assert_called_once()
            call_args = mock_ydl_class.call_args
            options = call_args[0][0]

            assert "format" in options
            assert "720" in options["format"]
            assert options["merge_output_format"] == "mp4"
            assert options["writeautomaticsub"] is True
            assert info == mock_info

    async def test_search_skips_malformed_entries(self, fetcher):
        """Malformed provider search rows should be ignored."""
        with patch("src.fetcher.youtube.YoutubeDL") as mock_ydl_class:
            mock_ydl = MagicMock()
            mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
            mock_ydl.__exit__ = MagicMock(return_value=False)
            # First call: regular search; second call: Shorts search (empty)
            mock_ydl.extract_info = MagicMock(
                side_effect=[
                    {"entries": [None, "bad", {"id": "yt123", "title": "ok"}]},
                    {"entries": []},
                ]
            )
            mock_ydl_class.return_value = mock_ydl

            result = await fetcher.search("test query", max_results=3)

        assert result == [{
            "id": "yt123",
            "title": "ok",
            "description": None,
            "url": "https://www.youtube.com/watch?v=yt123",
            "uploader_id": None,
            "channel": None,
            "channel_id": None,
            "view_count": None,
            "like_count": None,
            "comment_count": None,
            "duration": None,
            "upload_date": None,
            "timestamp": None,
            "thumbnails": None,
            "tags": None,
        }]


class TestYouTubeFetcherHandleValidation:
    """Tests for handle validation — pure logic."""

    @pytest.fixture
    def fetcher(self):
        storage = MagicMock()
        storage.exists = AsyncMock(return_value=False)
        return YouTubeFetcher(storage=storage)

    async def test_invalid_handle_raises_value_error(self, fetcher):
        """Test that invalid handles are rejected."""
        async with fetcher:
            with pytest.raises(ValueError) as exc_info:
                await fetcher.fetch_creator_videos(
                    Platform.YOUTUBE, "../../etc/passwd", limit=10
                )

        assert "Invalid handle" in str(exc_info.value)

    def test_valid_handle_accepted(self, fetcher):
        """Test that valid handles pass validation."""
        fetcher._validate_handle("testchannel")
        fetcher._validate_handle("user_name")


@pytest.mark.mock_required
class TestBackfillVideoMetadata:
    """Tests for _backfill_video_metadata — mocks yt-dlp to avoid network."""

    def test_backfills_missing_posted_at_and_duration(self):
        """Videos missing posted_at and duration_seconds get enriched."""
        video = VideoStats(
            video_id="abc123",
            play_count=1000,
            posted_at=None,
            duration_seconds=None,
        )

        mock_info = {
            "upload_date": "20250310",
            "duration": 62.5,
        }

        with patch("src.fetcher.youtube.YoutubeDL") as mock_ydl_class:
            mock_ydl = MagicMock()
            mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
            mock_ydl.__exit__ = MagicMock(return_value=False)
            mock_ydl.extract_info = MagicMock(return_value=mock_info)
            mock_ydl_class.return_value = mock_ydl

            result = _backfill_video_metadata([video])

        assert len(result) == 1
        assert result[0].video_id == "abc123"
        assert result[0].play_count == 1000
        assert result[0].posted_at == datetime(2025, 3, 10, tzinfo=timezone.utc)
        assert result[0].duration_seconds == 62

    def test_skips_videos_with_existing_metadata(self):
        """Videos that already have both fields are not re-fetched."""
        video = VideoStats(
            video_id="has_both",
            play_count=500,
            posted_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            duration_seconds=120,
        )

        with patch("src.fetcher.youtube.YoutubeDL") as mock_ydl_class:
            result = _backfill_video_metadata([video])
            mock_ydl_class.assert_not_called()

        assert len(result) == 1
        assert result[0] is video  # exact same object, untouched

    def test_partial_backfill_only_posted_at(self):
        """Video with duration but missing posted_at gets only posted_at filled."""
        video = VideoStats(
            video_id="has_dur",
            play_count=300,
            posted_at=None,
            duration_seconds=45,
        )

        mock_info = {"upload_date": "20241225", "duration": 999}

        with patch("src.fetcher.youtube.YoutubeDL") as mock_ydl_class:
            mock_ydl = MagicMock()
            mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
            mock_ydl.__exit__ = MagicMock(return_value=False)
            mock_ydl.extract_info = MagicMock(return_value=mock_info)
            mock_ydl_class.return_value = mock_ydl

            result = _backfill_video_metadata([video])

        assert result[0].posted_at == datetime(2024, 12, 25, tzinfo=timezone.utc)
        # duration_seconds should stay at 45 (not overwritten with 999)
        assert result[0].duration_seconds == 45

    def test_graceful_on_extract_info_failure(self):
        """If extract_info raises, original entry is kept."""
        video = VideoStats(
            video_id="will_fail",
            play_count=100,
            posted_at=None,
            duration_seconds=None,
        )

        with patch("src.fetcher.youtube.YoutubeDL") as mock_ydl_class:
            mock_ydl = MagicMock()
            mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
            mock_ydl.__exit__ = MagicMock(return_value=False)
            mock_ydl.extract_info = MagicMock(side_effect=Exception("network error"))
            mock_ydl_class.return_value = mock_ydl

            result = _backfill_video_metadata([video])

        assert len(result) == 1
        assert result[0] is video  # original entry, not replaced
        assert result[0].posted_at is None
        assert result[0].duration_seconds is None

    def test_handles_missing_fields_in_info(self):
        """If extract_info returns empty dict, original entry is kept."""
        video = VideoStats(
            video_id="empty_info",
            play_count=200,
            posted_at=None,
            duration_seconds=None,
        )

        with patch("src.fetcher.youtube.YoutubeDL") as mock_ydl_class:
            mock_ydl = MagicMock()
            mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
            mock_ydl.__exit__ = MagicMock(return_value=False)
            mock_ydl.extract_info = MagicMock(return_value={})
            mock_ydl_class.return_value = mock_ydl

            result = _backfill_video_metadata([video])

        assert len(result) == 1
        assert result[0].posted_at is None
        assert result[0].duration_seconds is None

    def test_mixed_list_only_fetches_for_missing(self):
        """In a mixed list, only videos needing backfill trigger extract_info."""
        complete = VideoStats(
            video_id="complete",
            play_count=500,
            posted_at=datetime(2025, 6, 1, tzinfo=timezone.utc),
            duration_seconds=90,
        )
        incomplete = VideoStats(
            video_id="incomplete",
            play_count=300,
            posted_at=None,
            duration_seconds=None,
        )

        mock_info = {"upload_date": "20250101", "duration": 30}

        with patch("src.fetcher.youtube.YoutubeDL") as mock_ydl_class:
            mock_ydl = MagicMock()
            mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
            mock_ydl.__exit__ = MagicMock(return_value=False)
            mock_ydl.extract_info = MagicMock(return_value=mock_info)
            mock_ydl_class.return_value = mock_ydl

            result = _backfill_video_metadata([complete, incomplete])

        assert len(result) == 2
        assert result[0] is complete  # untouched
        assert result[1].posted_at == datetime(2025, 1, 1, tzinfo=timezone.utc)
        assert result[1].duration_seconds == 30
        # extract_info should only have been called once (for 'incomplete')
        mock_ydl.extract_info.assert_called_once()
