"""Tests for R2 storage module — real R2 for integration tests, pure logic for models.

Tests marked @pytest.mark.r2 require real Cloudflare R2 credentials in .env.
Pure logic tests (settings validation, key formatting, exceptions) run without R2.
"""

import os
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import pytest

from src.common.enums import Platform
from src.storage.config import R2Settings
from src.storage.exceptions import UploadError, VideoNotFoundError
from src.storage.r2_storage import VideoListResult, VideoMetadata, VideoStorage


class TestR2Settings:
    """Tests for R2 configuration — pure Pydantic validation."""

    def test_valid_settings(self):
        """Test valid R2 settings load correctly."""
        with patch.dict(
            os.environ,
            {
                "R2_ACCOUNT_ID": "a" * 32,
                "R2_ACCESS_KEY_ID": "test_key",
                "R2_SECRET_ACCESS_KEY": "test_secret",
                "R2_BUCKET_NAME": "test-bucket",
            },
            clear=False,
        ):
            settings = R2Settings()
            assert settings.account_id == "a" * 32
            assert settings.access_key_id == "test_key"
            assert settings.secret_access_key.get_secret_value() == "test_secret"
            assert settings.bucket_name == "test-bucket"

    def test_endpoint_url(self):
        """Test endpoint URL is correctly formed."""
        with patch.dict(
            os.environ,
            {
                "R2_ACCOUNT_ID": "a" * 32,
                "R2_ACCESS_KEY_ID": "test_key",
                "R2_SECRET_ACCESS_KEY": "test_secret",
            },
            clear=False,
        ):
            settings = R2Settings()
            assert settings.endpoint_url == f"https://{'a' * 32}.r2.cloudflarestorage.com"

    def test_invalid_account_id_format(self):
        """Test validation rejects invalid account ID."""
        with patch.dict(
            os.environ,
            {
                "R2_ACCOUNT_ID": "invalid",
                "R2_ACCESS_KEY_ID": "test_key",
                "R2_SECRET_ACCESS_KEY": "test_secret",
            },
            clear=False,
        ):
            with pytest.raises(ValueError, match="32-character hex string"):
                R2Settings()

    def test_repr_hides_secrets(self):
        """Test repr doesn't expose secrets."""
        with patch.dict(
            os.environ,
            {
                "R2_ACCOUNT_ID": "a" * 32,
                "R2_ACCESS_KEY_ID": "test_key",
                "R2_SECRET_ACCESS_KEY": "super_secret",
            },
            clear=False,
        ):
            settings = R2Settings()
            repr_str = repr(settings)
            assert "super_secret" not in repr_str
            assert "a" * 32 in repr_str


class TestVideoMetadata:
    """Tests for VideoMetadata dataclass."""

    def test_immutable(self):
        """Test VideoMetadata is immutable."""
        metadata = VideoMetadata(
            key="videos/tiktok/abc123.mp4",
            platform=Platform.TIKTOK,
            video_id="abc123",
            size_bytes=1024,
            last_modified=datetime.now(timezone.utc),
        )
        with pytest.raises(AttributeError):
            metadata.size_bytes = 2048


class TestVideoListResult:
    """Tests for VideoListResult dataclass."""

    def test_empty_list(self):
        """Test empty video list."""
        result = VideoListResult(
            videos=[],
            total_count=0,
            has_more=False,
            next_cursor=None,
        )
        assert len(result.videos) == 0
        assert not result.has_more


@pytest.mark.r2
class TestR2VideoStorageLogic:
    """Tests for R2VideoStorage pure logic — uses real storage instance."""

    def test_video_key_format(self, r2_storage):
        """Test video key is correctly formatted."""
        key = r2_storage._video_key(Platform.TIKTOK, "abc123")
        assert key == "videos/tiktok/abc123.mp4"

    def test_video_key_platform_prefix(self, r2_storage):
        """Test each platform has correct prefix."""
        assert r2_storage._video_key(Platform.TIKTOK, "id1") == "videos/tiktok/id1.mp4"
        assert r2_storage._video_key(Platform.INSTAGRAM, "id2") == "videos/instagram/id2.mp4"
        assert r2_storage._video_key(Platform.YOUTUBE, "id3") == "videos/youtube/id3.mp4"

    def test_validate_video_id_valid(self, r2_storage):
        """Test valid video IDs pass validation."""
        r2_storage._validate_video_id("abc123")
        r2_storage._validate_video_id("video-id_test")
        r2_storage._validate_video_id("A" * 128)

    def test_validate_video_id_invalid(self, r2_storage):
        """Test invalid video IDs fail validation."""
        with pytest.raises(ValueError, match="Invalid video_id"):
            r2_storage._validate_video_id("../etc/passwd")
        with pytest.raises(ValueError, match="Invalid video_id"):
            r2_storage._validate_video_id("video/with/slashes")
        with pytest.raises(ValueError, match="Invalid video_id"):
            r2_storage._validate_video_id("")
        with pytest.raises(ValueError, match="Invalid video_id"):
            r2_storage._validate_video_id("a" * 129)

    def test_parse_key_valid(self, r2_storage):
        """Test parsing valid R2 keys."""
        result = r2_storage._parse_key("videos/tiktok/abc123.mp4")
        assert result == (Platform.TIKTOK, "abc123")
        result = r2_storage._parse_key("videos/instagram/xyz.mp4")
        assert result == (Platform.INSTAGRAM, "xyz")

    def test_parse_key_invalid(self, r2_storage):
        """Test parsing invalid R2 keys returns None."""
        assert r2_storage._parse_key("invalid/path") is None
        assert r2_storage._parse_key("videos/unknown/abc.mp4") is None
        assert r2_storage._parse_key("other/tiktok/abc.mp4") is None

    @pytest.mark.asyncio
    async def test_upload_file_not_found(self, r2_storage, tmp_path):
        """Test upload raises error for missing file."""
        nonexistent = tmp_path / "nonexistent.mp4"
        with pytest.raises(UploadError):
            await r2_storage.upload(nonexistent, Platform.TIKTOK, "test_id")

    @pytest.mark.asyncio
    async def test_upload_file_too_large(self, r2_storage, tmp_path):
        """Test upload raises error for oversized file."""
        large_file = tmp_path / "large.mp4"
        large_file.touch()
        with patch.object(Path, "stat") as mock_stat:
            mock_stat.return_value.st_size = 600 * 1024 * 1024  # 600MB
            with patch.object(Path, "exists", return_value=True):
                with pytest.raises(UploadError):
                    await r2_storage.upload(large_file, Platform.TIKTOK, "test_id")


@pytest.mark.r2
class TestR2VideoStorageIntegration:
    """Real R2 integration tests — upload, download, metadata, delete."""

    @pytest.mark.asyncio
    async def test_upload_and_download_roundtrip(self, r2_storage, test_video_path, r2_cleanup):
        """Upload a file to R2, download it, verify content matches."""
        video_id = f"test-{uuid4().hex[:8]}"
        r2_cleanup.append(f"videos/tiktok/{video_id}.mp4")

        metadata = await r2_storage.upload(test_video_path, Platform.TIKTOK, video_id)

        assert metadata.platform == Platform.TIKTOK
        assert metadata.video_id == video_id
        assert metadata.size_bytes > 0
        assert metadata.key == f"videos/tiktok/{video_id}.mp4"

        # Download and verify
        temp_path = await r2_storage.download_to_temp(Platform.TIKTOK, video_id)
        try:
            assert temp_path.exists()
            assert temp_path.stat().st_size == metadata.size_bytes
        finally:
            temp_path.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_exists_and_metadata(self, r2_storage, test_video_path, r2_cleanup):
        """Upload, check exists + get_metadata, then verify fields."""
        video_id = f"test-{uuid4().hex[:8]}"
        r2_cleanup.append(f"videos/tiktok/{video_id}.mp4")

        await r2_storage.upload(test_video_path, Platform.TIKTOK, video_id)

        assert await r2_storage.exists(Platform.TIKTOK, video_id) is True
        assert await r2_storage.exists(Platform.TIKTOK, "nonexistent") is False

        meta = await r2_storage.get_metadata(Platform.TIKTOK, video_id)
        assert meta is not None
        assert meta.video_id == video_id
        assert meta.size_bytes == test_video_path.stat().st_size

    @pytest.mark.asyncio
    async def test_delete(self, r2_storage, test_video_path, r2_cleanup):
        """Upload then delete, verify gone."""
        video_id = f"test-{uuid4().hex[:8]}"
        # No cleanup needed — we're deleting in the test itself

        await r2_storage.upload(test_video_path, Platform.TIKTOK, video_id)
        assert await r2_storage.exists(Platform.TIKTOK, video_id) is True

        deleted = await r2_storage.delete(Platform.TIKTOK, video_id)
        assert deleted is True
        assert await r2_storage.exists(Platform.TIKTOK, video_id) is False

        # Delete nonexistent returns False
        deleted_again = await r2_storage.delete(Platform.TIKTOK, video_id)
        assert deleted_again is False

    @pytest.mark.asyncio
    async def test_generate_download_url(self, r2_storage, test_video_path, r2_cleanup):
        """Upload and generate presigned URL."""
        video_id = f"test-{uuid4().hex[:8]}"
        r2_cleanup.append(f"videos/tiktok/{video_id}.mp4")

        await r2_storage.upload(test_video_path, Platform.TIKTOK, video_id)

        url = await r2_storage.generate_download_url(Platform.TIKTOK, video_id)
        assert url.startswith("https://")
        assert video_id in url

    @pytest.mark.asyncio
    async def test_list_videos(self, r2_storage, test_video_path, r2_cleanup):
        """Upload and verify listing."""
        video_id = f"test-{uuid4().hex[:8]}"
        r2_cleanup.append(f"videos/tiktok/{video_id}.mp4")

        await r2_storage.upload(test_video_path, Platform.TIKTOK, video_id)

        result = await r2_storage.list_videos(platform=Platform.TIKTOK, limit=100)
        assert isinstance(result, VideoListResult)
        found = any(v.video_id == video_id for v in result.videos)
        assert found, f"Uploaded video {video_id} not found in listing"

    @pytest.mark.asyncio
    async def test_download_nonexistent_raises(self, r2_storage):
        """Download nonexistent video raises VideoNotFoundError."""
        with pytest.raises(VideoNotFoundError):
            await r2_storage.download_to_temp(Platform.TIKTOK, f"nonexistent-{uuid4().hex[:8]}")


class TestVideoStorageProtocol:
    """Tests for VideoStorage protocol compliance."""

    def test_r2_storage_implements_protocol(self, r2_storage):
        """Verify R2VideoStorage can be used where VideoStorage is expected."""
        def use_storage(storage: VideoStorage) -> None:
            pass

        use_storage(r2_storage)


class TestExceptions:
    """Tests for storage exceptions."""

    def test_video_not_found_error(self):
        """Test VideoNotFoundError stores context."""
        error = VideoNotFoundError(Platform.TIKTOK, "abc123")
        assert error.platform == Platform.TIKTOK
        assert error.video_id == "abc123"
        assert "tiktok/abc123" in str(error)

    def test_upload_error(self):
        """Test UploadError stores context."""
        cause = ValueError("test cause")
        error = UploadError(Platform.INSTAGRAM, "xyz", cause)
        assert error.platform == Platform.INSTAGRAM
        assert error.video_id == "xyz"
        assert "test cause" in str(error)

    def test_upload_error_without_cause(self):
        """Test UploadError works without cause."""
        error = UploadError(Platform.YOUTUBE, "vid1")
        assert "youtube/vid1" in str(error).lower()
