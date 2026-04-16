"""Tests for story service — mocks required for capture pipeline.

Stories are ephemeral (24h) — cannot guarantee active stories at test time.
Capture pipeline tests need mocks to control fetcher/storage/repo responses.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.common.enums import Platform
from src.stories.models import CapturedStory, StoryResult
from src.stories.service import StoryService
from src.stories.storage import StoryStorageResult


@pytest.fixture
def mock_repository():
    """Create a mock story repository."""
    return AsyncMock()


@pytest.fixture
def mock_storage():
    """Create a mock story storage."""
    return AsyncMock()


@pytest.fixture
def mock_instagram_fetcher():
    """Create a mock Instagram fetcher."""
    return AsyncMock()


@pytest.fixture
def mock_story_service(mock_repository, mock_storage, mock_instagram_fetcher):
    """Create a story service with mocked dependencies."""
    return StoryService(
        repository=mock_repository,
        storage=mock_storage,
        instagram_fetcher=mock_instagram_fetcher,
    )


@pytest.mark.mock_required
class TestCaptureStoriesNow:
    """Tests for the capture_stories_now method — mocks required (stories are ephemeral)."""

    async def test_capture_stories_empty_response(
        self, mock_story_service, mock_instagram_fetcher
    ):
        """Test capturing when creator has no active stories."""
        mock_instagram_fetcher.fetch_stories.return_value = []

        result = await mock_story_service.capture_stories_now(
            user_id=uuid4(),
            platform=Platform.INSTAGRAM,
            creator_username="testuser",
        )

        assert result["captured"] == []
        assert result["skipped"] == 0
        mock_instagram_fetcher.fetch_stories.assert_called_once_with("testuser")

    async def test_capture_stories_success(
        self, mock_story_service, mock_repository, mock_storage, mock_instagram_fetcher
    ):
        """Test successfully capturing stories."""
        user_id = uuid4()
        now = datetime.now(timezone.utc)
        story_id = uuid4()

        mock_story = StoryResult(
            story_id="ig_12345",
            media_url="https://instagram.com/story.mp4",
            media_type="video",
            creator_username="testuser",
            posted_at=now,
            expires_at=now + timedelta(hours=24),
            duration_seconds=15,
        )
        mock_instagram_fetcher.fetch_stories.return_value = [mock_story]

        mock_repository.get_existing_story_ids.return_value = set()

        mock_storage.download_and_upload_story.return_value = StoryStorageResult(
            r2_key="stories/instagram/testuser/ig_12345.mp4",
            platform=Platform.INSTAGRAM,
            story_id="ig_12345",
            creator_username="testuser",
            media_type="video",
            file_size_bytes=1024000,
            captured_at=now,
        )

        captured = CapturedStory(
            id=story_id,
            user_id=user_id,
            platform=Platform.INSTAGRAM,
            story_id="ig_12345",
            creator_username="testuser",
            media_type="video",
            r2_key="stories/instagram/testuser/ig_12345.mp4",
            duration_seconds=15,
            file_size_bytes=1024000,
            original_posted_at=now,
            original_expires_at=now + timedelta(hours=24),
            captured_at=now,
        )
        mock_repository.save_captured_story.return_value = captured

        mock_storage.generate_presigned_url.return_value = "https://presigned.url"

        result = await mock_story_service.capture_stories_now(
            user_id=user_id,
            platform=Platform.INSTAGRAM,
            creator_username="testuser",
        )

        assert len(result["captured"]) == 1
        assert result["skipped"] == 0
        assert result["captured"][0]["story_id"] == "ig_12345"
        assert result["captured"][0]["media_url"] == "https://presigned.url"

    async def test_capture_stories_skips_existing(
        self, mock_story_service, mock_repository, mock_instagram_fetcher
    ):
        """Test that already-captured stories are skipped."""
        mock_stories = [
            StoryResult(
                story_id="ig_existing",
                media_url="https://instagram.com/existing.mp4",
                media_type="video",
                creator_username="testuser",
            ),
            StoryResult(
                story_id="ig_new",
                media_url="https://instagram.com/new.mp4",
                media_type="video",
                creator_username="testuser",
            ),
        ]
        mock_instagram_fetcher.fetch_stories.return_value = mock_stories

        mock_repository.get_existing_story_ids.return_value = {"ig_existing"}

        result = await mock_story_service.capture_stories_now(
            user_id=uuid4(),
            platform=Platform.INSTAGRAM,
            creator_username="testuser",
        )

        assert result["skipped"] == 1

    async def test_capture_stories_handles_storage_error(
        self, mock_story_service, mock_repository, mock_storage, mock_instagram_fetcher
    ):
        """Test graceful handling of storage errors."""
        mock_story = StoryResult(
            story_id="ig_12345",
            media_url="https://instagram.com/story.mp4",
            media_type="video",
            creator_username="testuser",
        )
        mock_instagram_fetcher.fetch_stories.return_value = [mock_story]
        mock_repository.get_existing_story_ids.return_value = set()

        mock_storage.download_and_upload_story.side_effect = Exception("Storage error")

        result = await mock_story_service.capture_stories_now(
            user_id=uuid4(),
            platform=Platform.INSTAGRAM,
            creator_username="testuser",
        )

        assert result["captured"] == []
        assert result["skipped"] == 0


@pytest.mark.mock_required
class TestGetCapturedStories:
    """Tests for the get_captured_stories method — mocks required for controlled data."""

    async def test_get_captured_stories_success(
        self, mock_story_service, mock_repository, mock_storage
    ):
        """Test retrieving captured stories."""
        user_id = uuid4()
        now = datetime.now(timezone.utc)

        stories = [
            CapturedStory(
                id=uuid4(),
                user_id=user_id,
                platform=Platform.INSTAGRAM,
                story_id="ig_12345",
                creator_username="testuser",
                media_type="video",
                r2_key="stories/instagram/testuser/ig_12345.mp4",
                duration_seconds=15,
                file_size_bytes=1024000,
                original_posted_at=now,
                original_expires_at=now + timedelta(hours=24),
                captured_at=now,
            ),
        ]
        mock_repository.get_stories_by_creator.return_value = stories
        mock_storage.generate_presigned_url.return_value = "https://presigned.url"

        result = await mock_story_service.get_captured_stories(
            user_id=user_id,
            platform=Platform.INSTAGRAM,
            creator_username="testuser",
        )

        assert len(result) == 1
        assert result[0]["story_id"] == "ig_12345"
        assert result[0]["media_url"] == "https://presigned.url"

    async def test_get_captured_stories_empty(
        self, mock_story_service, mock_repository
    ):
        """Test retrieving when no stories have been captured."""
        mock_repository.get_stories_by_creator.return_value = []

        result = await mock_story_service.get_captured_stories(
            user_id=uuid4(),
            platform=Platform.INSTAGRAM,
            creator_username="testuser",
        )

        assert result == []
