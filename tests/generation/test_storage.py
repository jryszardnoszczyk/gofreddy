"""Tests for R2GenerationStorage."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.generation.storage import R2GenerationStorage


@pytest.fixture
def mock_storage():
    video_storage = MagicMock()
    s3_client = AsyncMock()
    video_storage._get_client = AsyncMock(return_value=s3_client)
    settings = MagicMock()
    settings.bucket_name = "test-bucket"
    storage = R2GenerationStorage(video_storage, settings)
    return storage, s3_client


class TestGenerationKey:
    def test_valid_key(self, mock_storage):
        storage, _ = mock_storage
        uid = uuid4()
        gid = uuid4()
        key = storage._generation_key(uid, gid, "cadre_0.mp4")
        assert key == f"generated/{uid}/{gid}/cadre_0.mp4"

    def test_final_filename(self, mock_storage):
        storage, _ = mock_storage
        uid = uuid4()
        gid = uuid4()
        key = storage._generation_key(uid, gid, "final.mp4")
        assert key.endswith("final.mp4")

    def test_frame_png_filename(self, mock_storage):
        storage, _ = mock_storage
        uid = uuid4()
        gid = uuid4()
        key = storage._generation_key(uid, gid, "frame_0.png")
        assert key.endswith("frame_0.png")

    @pytest.mark.parametrize("filename", [
        "../../etc/passwd",
        "evil.sh",
        "cadre_0.mp3",
        "../cadre_0.mp4",
        "cadre_-1.mp4",
    ])
    def test_rejects_invalid_filenames(self, mock_storage, filename):
        storage, _ = mock_storage
        with pytest.raises(ValueError, match="Invalid filename"):
            storage._generation_key(uuid4(), uuid4(), filename)

    def test_rejects_non_uuid(self, mock_storage):
        storage, _ = mock_storage
        with pytest.raises(ValueError, match="Invalid UUID"):
            storage._generation_key("not-a-uuid", uuid4(), "cadre_0.mp4")


class TestPresignedUrl:
    @pytest.mark.asyncio
    async def test_get_presigned_url(self, mock_storage):
        storage, s3_client = mock_storage
        s3_client.generate_presigned_url = AsyncMock(return_value="https://example.com/signed")
        url = await storage.get_presigned_url("generated/uid/gid/final.mp4")
        assert url == "https://example.com/signed"
        s3_client.generate_presigned_url.assert_called_once()

    @pytest.mark.asyncio
    async def test_presigned_url_clamped_to_7_days(self, mock_storage):
        storage, s3_client = mock_storage
        s3_client.generate_presigned_url = AsyncMock(return_value="https://example.com/signed")
        await storage.get_presigned_url("generated/uid/gid/final.mp4", expiry=999999)
        call_kwargs = s3_client.generate_presigned_url.call_args
        assert call_kwargs.kwargs.get("ExpiresIn", call_kwargs[1].get("ExpiresIn")) == 7 * 24 * 3600


class TestDeleteGeneration:
    @pytest.mark.asyncio
    async def test_delete_generation(self, mock_storage):
        storage, s3_client = mock_storage
        s3_client.list_objects_v2 = AsyncMock(return_value={
            "Contents": [
                {"Key": "generated/uid/gid/cadre_0.mp4"},
                {"Key": "generated/uid/gid/final.mp4"},
            ]
        })
        s3_client.delete_object = AsyncMock()
        uid = uuid4()
        gid = uuid4()
        await storage.delete_generation(uid, gid)
        assert s3_client.delete_object.call_count == 2

    @pytest.mark.asyncio
    async def test_delete_generation_invalid_uuid(self, mock_storage):
        storage, _ = mock_storage
        with pytest.raises(ValueError, match="Invalid UUID"):
            await storage.delete_generation("not-uuid", uuid4())
