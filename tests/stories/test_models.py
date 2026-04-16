"""Tests for story models."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from src.common.enums import Platform
from src.stories.models import CapturedStory, StoryResult


class TestStoryResult:
    """Tests for StoryResult dataclass."""

    def test_story_result_creation(self):
        """Test creating a StoryResult with all fields."""
        result = StoryResult(
            story_id="12345",
            media_url="https://example.com/video.mp4",
            media_type="video",
            creator_username="testuser",
            posted_at=datetime(2026, 2, 5, 12, 0, 0, tzinfo=timezone.utc),
            expires_at=datetime(2026, 2, 6, 12, 0, 0, tzinfo=timezone.utc),
            duration_seconds=15,
            raw_metadata={"key": "value"},
        )

        assert result.story_id == "12345"
        assert result.media_url == "https://example.com/video.mp4"
        assert result.media_type == "video"
        assert result.creator_username == "testuser"
        assert result.duration_seconds == 15
        assert result.raw_metadata == {"key": "value"}

    def test_story_result_optional_fields(self):
        """Test StoryResult with optional fields as None."""
        result = StoryResult(
            story_id="12345",
            media_url="https://example.com/image.jpg",
            media_type="image",
            creator_username="testuser",
        )

        assert result.posted_at is None
        assert result.expires_at is None
        assert result.duration_seconds is None
        assert result.raw_metadata is None

    def test_story_result_is_frozen(self):
        """Test that StoryResult is immutable."""
        result = StoryResult(
            story_id="12345",
            media_url="https://example.com/video.mp4",
            media_type="video",
            creator_username="testuser",
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            result.story_id = "67890"


class TestCapturedStory:
    """Tests for CapturedStory dataclass."""

    def test_captured_story_creation(self):
        """Test creating a CapturedStory with all fields."""
        story_id = uuid4()
        user_id = uuid4()
        now = datetime.now(timezone.utc)

        story = CapturedStory(
            id=story_id,
            user_id=user_id,
            platform=Platform.INSTAGRAM,
            story_id="ig_12345",
            creator_username="testcreator",
            media_type="video",
            r2_key="stories/instagram/testcreator/ig_12345.mp4",
            duration_seconds=10,
            file_size_bytes=1024000,
            original_posted_at=now,
            original_expires_at=now,
            captured_at=now,
            raw_metadata={"source": "apify"},
        )

        assert story.id == story_id
        assert story.user_id == user_id
        assert story.platform == Platform.INSTAGRAM
        assert story.story_id == "ig_12345"
        assert story.creator_username == "testcreator"
        assert story.media_type == "video"
        assert story.r2_key == "stories/instagram/testcreator/ig_12345.mp4"
        assert story.duration_seconds == 10
        assert story.file_size_bytes == 1024000

    def test_captured_story_optional_fields(self):
        """Test CapturedStory with optional fields."""
        story = CapturedStory(
            id=uuid4(),
            user_id=uuid4(),
            platform=Platform.INSTAGRAM,
            story_id="ig_12345",
            creator_username="testcreator",
            media_type="image",
            r2_key="stories/instagram/testcreator/ig_12345.jpg",
            duration_seconds=None,
            file_size_bytes=None,
            original_posted_at=None,
            original_expires_at=None,
            captured_at=datetime.now(timezone.utc),
        )

        assert story.duration_seconds is None
        assert story.file_size_bytes is None
        assert story.original_posted_at is None
        assert story.raw_metadata is None

    def test_captured_story_is_frozen(self):
        """Test that CapturedStory is immutable."""
        story = CapturedStory(
            id=uuid4(),
            user_id=uuid4(),
            platform=Platform.INSTAGRAM,
            story_id="ig_12345",
            creator_username="testcreator",
            media_type="video",
            r2_key="stories/instagram/testcreator/ig_12345.mp4",
            duration_seconds=10,
            file_size_bytes=1024000,
            original_posted_at=None,
            original_expires_at=None,
            captured_at=datetime.now(timezone.utc),
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            story.story_id = "modified"
