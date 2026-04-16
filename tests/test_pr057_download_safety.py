"""Tests for download size limit and temp file safety (PR-057 I12)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.common.enums import Platform
from src.storage.r2_storage import R2VideoStorage
from src.storage.exceptions import StorageError


class AsyncIterChunks:
    """Mock async iterator for S3 Body chunks."""

    def __init__(self, chunks: list[bytes]):
        self._chunks = chunks
        self._index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._index >= len(self._chunks):
            raise StopAsyncIteration
        chunk = self._chunks[self._index]
        self._index += 1
        return chunk


class MockBody:
    """Mock S3 response Body with async context manager and iter_chunks."""

    def __init__(self, chunks: list[bytes]):
        self._chunks = chunks
        self._closed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        self._closed = True

    def iter_chunks(self, chunk_size=None):
        return AsyncIterChunks(self._chunks)

    def close(self):
        self._closed = True


def _make_storage() -> R2VideoStorage:
    """Create a storage instance with mocked S3."""
    storage = R2VideoStorage.__new__(R2VideoStorage)
    storage._config = MagicMock()
    storage._config.bucket_name = "test-bucket"
    storage.DOWNLOAD_CHUNK_SIZE = 2 * 1024 * 1024
    storage.MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB
    return storage


# ── ContentLength Fast Reject ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_download_fast_rejects_large_content_length():
    """Mock S3 response with ContentLength > MAX_VIDEO_SIZE raises StorageError before streaming."""
    storage = _make_storage()

    mock_body = MockBody([])
    mock_response = {
        "ContentLength": 600 * 1024 * 1024,  # 600MB > 500MB
        "Body": mock_body,
    }

    mock_client = AsyncMock()
    mock_client.get_object = AsyncMock(return_value=mock_response)
    storage._get_client = AsyncMock(return_value=mock_client)

    with pytest.raises(StorageError, match="Object too large"):
        await storage.download_to_temp(Platform.TIKTOK, "test123")

    # Body should be closed
    assert mock_body._closed


# ── Streaming Size Limit ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_download_aborts_at_max_size():
    """Download aborts when streaming exceeds MAX_VIDEO_SIZE."""
    storage = _make_storage()
    storage.MAX_VIDEO_SIZE = 100  # 100 bytes for test

    # Create chunks that exceed 100 bytes total
    chunks = [b"x" * 60, b"x" * 60]  # 120 bytes total
    mock_body = MockBody(chunks)
    mock_response = {
        "ContentLength": 0,  # Unknown content length
        "Body": mock_body,
    }

    mock_client = AsyncMock()
    mock_client.get_object = AsyncMock(return_value=mock_response)
    storage._get_client = AsyncMock(return_value=mock_client)

    with pytest.raises(StorageError, match="Download aborted"):
        await storage.download_to_temp(Platform.TIKTOK, "test123")

    # Body should be closed via __aexit__
    assert mock_body._closed


@pytest.mark.asyncio
async def test_download_cleans_up_on_io_error():
    """Mock write failure — temp file is deleted."""
    storage = _make_storage()

    chunks = [b"data"]
    mock_body = MockBody(chunks)
    mock_response = {
        "ContentLength": 4,
        "Body": mock_body,
    }

    mock_client = AsyncMock()
    mock_client.get_object = AsyncMock(return_value=mock_response)
    storage._get_client = AsyncMock(return_value=mock_client)

    # Patch aiofiles.open to raise IOError on write
    with patch("src.storage.r2_storage.aiofiles.open", side_effect=IOError("Disk full")):
        with pytest.raises(IOError, match="Disk full"):
            await storage.download_to_temp(Platform.TIKTOK, "test123")


@pytest.mark.asyncio
async def test_download_body_connection_released_on_abort():
    """Verify response Body __aexit__ called when streaming aborts."""
    storage = _make_storage()
    storage.MAX_VIDEO_SIZE = 10

    chunks = [b"x" * 20]
    mock_body = MockBody(chunks)
    mock_response = {
        "ContentLength": 0,
        "Body": mock_body,
    }

    mock_client = AsyncMock()
    mock_client.get_object = AsyncMock(return_value=mock_response)
    storage._get_client = AsyncMock(return_value=mock_client)

    with pytest.raises(StorageError):
        await storage.download_to_temp(Platform.TIKTOK, "test123")

    assert mock_body._closed


@pytest.mark.asyncio
async def test_download_success_preserves_file():
    """Normal download under limit — temp file exists after return."""
    storage = _make_storage()

    chunks = [b"video data here"]
    mock_body = MockBody(chunks)
    mock_response = {
        "ContentLength": len(chunks[0]),
        "Body": mock_body,
    }

    mock_client = AsyncMock()
    mock_client.get_object = AsyncMock(return_value=mock_response)
    storage._get_client = AsyncMock(return_value=mock_client)

    result = await storage.download_to_temp(Platform.TIKTOK, "test123")
    try:
        assert result.exists()
        assert result.read_bytes() == b"video data here"
    finally:
        result.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_download_byte_counter_accurate():
    """Verify exact byte count tracking across multiple chunks."""
    storage = _make_storage()
    storage.MAX_VIDEO_SIZE = 100

    # 3 chunks of 30 bytes each = 90 total (under 100)
    chunks = [b"x" * 30, b"y" * 30, b"z" * 30]
    mock_body = MockBody(chunks)
    mock_response = {
        "ContentLength": 90,
        "Body": mock_body,
    }

    mock_client = AsyncMock()
    mock_client.get_object = AsyncMock(return_value=mock_response)
    storage._get_client = AsyncMock(return_value=mock_client)

    result = await storage.download_to_temp(Platform.TIKTOK, "test123")
    try:
        assert result.exists()
        assert len(result.read_bytes()) == 90
    finally:
        result.unlink(missing_ok=True)
