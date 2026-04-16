"""Tests for Instagram Stories fetcher — mocks required for response format testing.

Stories are ephemeral (24h) — cannot guarantee any account has active stories at test time.
All tests use mocks to control exact Apify response shapes for parsing validation.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.common.enums import Platform
from src.stories.models import StoryMediaType


@pytest.fixture
def mock_apify_client():
    """Create mock Apify client."""
    return AsyncMock()


@pytest.fixture
def mock_storage():
    """Create mock storage."""
    return AsyncMock()


@pytest.fixture
def instagram_fetcher(mock_storage):
    """Create Instagram fetcher for testing."""
    from src.fetcher.instagram import InstagramFetcher
    from src.fetcher.config import FetcherSettings

    settings = FetcherSettings()
    return InstagramFetcher(mock_storage, settings)


@pytest.mark.mock_required
class TestFetchStories:
    """Tests for InstagramFetcher.fetch_stories method — mocks required for response format."""

    async def test_fetch_stories_success(self, instagram_fetcher, mock_apify_client):
        """Should fetch and parse stories successfully."""
        instagram_fetcher._apify_client = mock_apify_client

        mock_dataset = AsyncMock()
        mock_dataset.list_items = AsyncMock(
            return_value=MagicMock(
                items=[
                    {
                        "id": "story123",
                        "videoUrl": "https://example.com/story.mp4",
                        "timestamp": "2026-02-05T10:00:00Z",
                        "duration": 15000,
                        "mentions": [{"username": "user1"}],
                        "hashtags": [{"name": "tag1"}],
                    },
                    {
                        "id": "story456",
                        "imageUrl": "https://example.com/story.jpg",
                        "timestamp": 1738749600,
                    },
                ]
            )
        )

        mock_actor = AsyncMock()
        mock_actor.call = AsyncMock(
            return_value={"defaultDatasetId": "dataset123"}
        )

        mock_apify_client.actor = MagicMock(return_value=mock_actor)
        mock_apify_client.dataset = MagicMock(return_value=mock_dataset)

        stories = await instagram_fetcher.fetch_stories("testuser")

        assert len(stories) == 2

        assert stories[0].story_id == "story123"
        assert stories[0].media_type == StoryMediaType.VIDEO
        assert stories[0].media_url == "https://example.com/story.mp4"
        assert stories[0].creator_username == "testuser"
        assert stories[0].duration_seconds == 15
        assert stories[0].raw_metadata["mentions"] == [{"username": "user1"}]
        assert stories[0].raw_metadata["hashtags"] == [{"name": "tag1"}]
        assert stories[0].posted_at is not None
        assert stories[0].expires_at is not None

        assert stories[1].story_id == "story456"
        assert stories[1].media_type == StoryMediaType.IMAGE
        assert stories[1].media_url == "https://example.com/story.jpg"
        assert stories[1].duration_seconds is None

    async def test_fetch_stories_empty(self, instagram_fetcher, mock_apify_client):
        """Should return empty list when no stories available."""
        instagram_fetcher._apify_client = mock_apify_client

        mock_actor = AsyncMock()
        mock_actor.call = AsyncMock(return_value=None)
        mock_apify_client.actor = MagicMock(return_value=mock_actor)

        stories = await instagram_fetcher.fetch_stories("testuser")

        assert stories == []

    async def test_fetch_stories_no_items(self, instagram_fetcher, mock_apify_client):
        """Should return empty list when no items in dataset."""
        instagram_fetcher._apify_client = mock_apify_client

        mock_dataset = AsyncMock()
        mock_dataset.list_items = AsyncMock(
            return_value=MagicMock(items=[])
        )

        mock_actor = AsyncMock()
        mock_actor.call = AsyncMock(
            return_value={"defaultDatasetId": "dataset123"}
        )

        mock_apify_client.actor = MagicMock(return_value=mock_actor)
        mock_apify_client.dataset = MagicMock(return_value=mock_dataset)

        stories = await instagram_fetcher.fetch_stories("testuser")

        assert stories == []

    async def test_fetch_stories_validates_handle(self, instagram_fetcher):
        """Should validate username format."""
        with pytest.raises(ValueError, match="Invalid handle"):
            await instagram_fetcher.fetch_stories("../invalid")

    async def test_fetch_stories_skips_no_media_url(
        self, instagram_fetcher, mock_apify_client
    ):
        """Should skip items without media URL."""
        instagram_fetcher._apify_client = mock_apify_client

        mock_dataset = AsyncMock()
        mock_dataset.list_items = AsyncMock(
            return_value=MagicMock(
                items=[
                    {
                        "id": "story123",
                    },
                    {
                        "id": "story456",
                        "videoUrl": "https://example.com/story.mp4",
                    },
                ]
            )
        )

        mock_actor = AsyncMock()
        mock_actor.call = AsyncMock(
            return_value={"defaultDatasetId": "dataset123"}
        )

        mock_apify_client.actor = MagicMock(return_value=mock_actor)
        mock_apify_client.dataset = MagicMock(return_value=mock_dataset)

        stories = await instagram_fetcher.fetch_stories("testuser")

        assert len(stories) == 1
        assert stories[0].story_id == "story456"

    async def test_fetch_stories_handles_timestamp_formats(
        self, instagram_fetcher, mock_apify_client
    ):
        """Should handle both ISO and Unix timestamp formats."""
        instagram_fetcher._apify_client = mock_apify_client

        mock_dataset = AsyncMock()
        mock_dataset.list_items = AsyncMock(
            return_value=MagicMock(
                items=[
                    {
                        "id": "story1",
                        "videoUrl": "https://example.com/story1.mp4",
                        "timestamp": "2026-02-05T10:00:00Z",
                    },
                    {
                        "id": "story2",
                        "videoUrl": "https://example.com/story2.mp4",
                        "timestamp": 1738749600,
                    },
                    {
                        "id": "story3",
                        "videoUrl": "https://example.com/story3.mp4",
                        "takenAt": "2026-02-05T12:00:00+00:00",
                    },
                ]
            )
        )

        mock_actor = AsyncMock()
        mock_actor.call = AsyncMock(
            return_value={"defaultDatasetId": "dataset123"}
        )

        mock_apify_client.actor = MagicMock(return_value=mock_actor)
        mock_apify_client.dataset = MagicMock(return_value=mock_dataset)

        stories = await instagram_fetcher.fetch_stories("testuser")

        assert len(stories) == 3
        assert stories[0].posted_at is not None
        assert stories[1].posted_at is not None
        assert stories[2].posted_at is not None

    async def test_fetch_stories_duration_conversion(
        self, instagram_fetcher, mock_apify_client
    ):
        """Should convert duration from milliseconds to seconds."""
        instagram_fetcher._apify_client = mock_apify_client

        mock_dataset = AsyncMock()
        mock_dataset.list_items = AsyncMock(
            return_value=MagicMock(
                items=[
                    {
                        "id": "story1",
                        "videoUrl": "https://example.com/story1.mp4",
                        "duration": 15000,
                    },
                    {
                        "id": "story2",
                        "videoUrl": "https://example.com/story2.mp4",
                        "duration": 10,
                    },
                ]
            )
        )

        mock_actor = AsyncMock()
        mock_actor.call = AsyncMock(
            return_value={"defaultDatasetId": "dataset123"}
        )

        mock_apify_client.actor = MagicMock(return_value=mock_actor)
        mock_apify_client.dataset = MagicMock(return_value=mock_dataset)

        stories = await instagram_fetcher.fetch_stories("testuser")

        assert stories[0].duration_seconds == 15
        assert stories[1].duration_seconds == 10
