"""Tests for story storage — real R2 for integration, pure logic for key generation.

Tests marked @pytest.mark.r2 require real Cloudflare R2 credentials in .env.
Integration tests are also marked @pytest.mark.external_api so the default
`-m "not external_api ..."` suite stays network-free.
"""

from uuid import uuid4

import pytest

from src.common.enums import Platform
from src.stories.storage import StoryStorageResult  # noqa: F401


class TestStoryKey:
    """Tests for story key generation — pure logic."""

    def test_video_key_format(self, r2_story_storage):
        """Test video story key format."""
        key = r2_story_storage._story_key(
            platform=Platform.INSTAGRAM,
            username="testuser",
            story_id="12345",
            media_type="video",
        )
        assert key == "stories/instagram/testuser/12345.mp4"

    def test_image_key_format(self, r2_story_storage):
        """Test image story key format."""
        key = r2_story_storage._story_key(
            platform=Platform.INSTAGRAM,
            username="testuser",
            story_id="12345",
            media_type="image",
        )
        assert key == "stories/instagram/testuser/12345.jpg"


@pytest.mark.r2
@pytest.mark.external_api
class TestStoryStorageIntegration:
    """Real R2 integration tests for story storage."""

    @pytest.mark.asyncio
    async def test_upload_and_presigned_url(self, r2_story_storage, r2_cleanup):
        """Upload content directly to R2, then generate presigned URL."""
        story_id = f"test-{uuid4().hex[:8]}"
        key = f"stories/instagram/testuser/{story_id}.mp4"
        r2_cleanup.append(key)

        # Upload directly via S3 client (simulates download_and_upload_story)
        client = await r2_story_storage._video_storage._get_client()
        await client.put_object(
            Bucket=r2_story_storage._settings.bucket_name,
            Key=key,
            Body=b"fake video content for test",
            ContentType="video/mp4",
        )

        # Generate presigned URL
        url = await r2_story_storage.generate_presigned_url(key, expiration_seconds=3600)
        assert url.startswith("https://")
        assert story_id in url

    @pytest.mark.asyncio
    async def test_presigned_url_max_expiration(self, r2_story_storage, r2_cleanup):
        """Test presigned URL clamps to max expiration (7 days)."""
        story_id = f"test-{uuid4().hex[:8]}"
        key = f"stories/instagram/testuser/{story_id}.mp4"
        r2_cleanup.append(key)

        client = await r2_story_storage._video_storage._get_client()
        await client.put_object(
            Bucket=r2_story_storage._settings.bucket_name,
            Key=key,
            Body=b"test data",
            ContentType="video/mp4",
        )

        # Request expiration > 7 days — should still work (clamped internally)
        url = await r2_story_storage.generate_presigned_url(key, expiration_seconds=1000000)
        assert url.startswith("https://")

    @pytest.mark.asyncio
    async def test_delete_story_success(self, r2_story_storage, r2_cleanup):
        """Upload then delete story from R2."""
        story_id = f"test-{uuid4().hex[:8]}"
        key = f"stories/instagram/testuser/{story_id}.mp4"
        # No cleanup needed — we delete it ourselves

        client = await r2_story_storage._video_storage._get_client()
        await client.put_object(
            Bucket=r2_story_storage._settings.bucket_name,
            Key=key,
            Body=b"test data to delete",
            ContentType="video/mp4",
        )

        result = await r2_story_storage.delete_story(key)
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_story_nonexistent(self, r2_story_storage):
        """Delete nonexistent story returns True (R2 delete is idempotent)."""
        # R2/S3 delete_object doesn't raise for nonexistent keys
        result = await r2_story_storage.delete_story(
            f"stories/instagram/testuser/nonexistent-{uuid4().hex[:8]}.mp4"
        )
        assert result is True
