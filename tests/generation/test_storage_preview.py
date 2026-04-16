"""Tests for R2GenerationStorage preview methods."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.generation.storage import R2GenerationStorage


@pytest.fixture
def mock_r2():
    s3_client = AsyncMock()
    s3_client.put_object = AsyncMock()
    s3_client.generate_presigned_url = AsyncMock(return_value="https://r2.example.com/signed")

    video_storage = MagicMock()
    video_storage._get_client = AsyncMock(return_value=s3_client)

    settings = MagicMock()
    settings.bucket_name = "test-bucket"

    storage = R2GenerationStorage(video_storage=video_storage, settings=settings)
    return storage, s3_client


class TestPreviewKey:
    def test_valid_uuid(self, mock_r2):
        storage, _ = mock_r2
        uid = uuid4()
        filename = "a" * 32 + ".png"
        key = storage.preview_key(uid, filename)
        assert key == f"previews/{uid}/{filename}"

    def test_invalid_uuid_raises(self, mock_r2):
        storage, _ = mock_r2
        with pytest.raises(ValueError, match="Invalid UUID"):
            storage.preview_key("not-a-uuid", "a" * 32 + ".png")  # type: ignore[arg-type]

    def test_path_traversal_rejected(self, mock_r2):
        storage, _ = mock_r2
        uid = uuid4()
        with pytest.raises(ValueError, match="Invalid preview filename"):
            storage.preview_key(uid, "../../etc/passwd")

    def test_non_hex_filename_rejected(self, mock_r2):
        storage, _ = mock_r2
        uid = uuid4()
        with pytest.raises(ValueError, match="Invalid preview filename"):
            storage.preview_key(uid, "test.png")


class TestUploadPreview:
    @pytest.mark.asyncio
    async def test_upload_success(self, mock_r2):
        storage, s3_client = mock_r2
        uid = uuid4()
        filename = "a" * 32 + ".png"
        key = await storage.upload_preview(uid, filename, b"image-data")

        assert key == f"previews/{uid}/{filename}"
        s3_client.put_object.assert_awaited_once_with(
            Bucket="test-bucket",
            Key=f"previews/{uid}/{filename}",
            Body=b"image-data",
            ContentType="image/png",
        )


class TestGetPreviewUrl:
    @pytest.mark.asyncio
    async def test_presigned_url(self, mock_r2):
        storage, s3_client = mock_r2
        url = await storage.get_preview_url("previews/uid/test.png")

        assert url == "https://r2.example.com/signed"
        s3_client.generate_presigned_url.assert_awaited_once_with(
            "get_object",
            Params={"Bucket": "test-bucket", "Key": "previews/uid/test.png"},
            ExpiresIn=3600,
        )

    @pytest.mark.asyncio
    async def test_custom_expiry_capped(self, mock_r2):
        storage, s3_client = mock_r2
        await storage.get_preview_url("previews/uid/test.png", expiry=999999)

        call_kwargs = s3_client.generate_presigned_url.call_args
        assert call_kwargs[1]["ExpiresIn"] == 7 * 24 * 3600
