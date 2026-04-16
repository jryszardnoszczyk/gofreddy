"""Tests for model enhancements (Phase 3).

Verifies new fields on VideoResult, CommentData, VideoStats, and AudioTrackInfo.
"""

from datetime import datetime, timezone

import pytest

from src.common.enums import Platform
from src.fetcher.models import AudioTrackInfo, CommentData, VideoResult, VideoStats


class TestAudioTrackInfo:
    def test_creation(self):
        a = AudioTrackInfo(title="Original Sound", artist="creator123", is_original=True)
        assert a.title == "Original Sound"
        assert a.artist == "creator123"
        assert a.is_original is True

    def test_defaults(self):
        a = AudioTrackInfo()
        assert a.title is None
        assert a.artist is None
        assert a.is_original is None

    def test_frozen(self):
        a = AudioTrackInfo(title="test")
        with pytest.raises(AttributeError):
            a.title = "changed"  # type: ignore[misc]


class TestVideoResultNewFields:
    def test_new_fields_default_none(self):
        r = VideoResult(video_id="123", platform=Platform.TIKTOK, r2_key="videos/tiktok/123.mp4")
        assert r.thumbnail_url is None
        assert r.share_count is None
        assert r.hashtags is None
        assert r.mentions is None
        assert r.audio_track is None

    def test_all_new_fields(self):
        audio = AudioTrackInfo(title="Song", artist="Artist")
        r = VideoResult(
            video_id="123",
            platform=Platform.TIKTOK,
            r2_key="videos/tiktok/123.mp4",
            thumbnail_url="https://example.com/thumb.jpg",
            share_count=1500,
            hashtags=["fitness", "gym"],
            mentions=["trainer_bob"],
            audio_track=audio,
        )
        assert r.thumbnail_url == "https://example.com/thumb.jpg"
        assert r.share_count == 1500
        assert r.hashtags == ["fitness", "gym"]
        assert r.mentions == ["trainer_bob"]
        assert r.audio_track.title == "Song"

    def test_backward_compatible(self):
        """Old-style creation without new fields still works."""
        r = VideoResult(
            video_id="abc",
            platform=Platform.INSTAGRAM,
            r2_key="videos/instagram/abc.mp4",
            title="test",
            view_count=1000,
        )
        assert r.video_id == "abc"
        assert r.view_count == 1000


class TestCommentDataNewFields:
    def test_new_fields_default_none(self):
        c = CommentData(text="nice video", username="user1")
        assert c.reply_count is None
        assert c.display_name is None

    def test_all_fields(self):
        c = CommentData(
            text="great content!",
            username="user1",
            like_count=5,
            posted_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            reply_count=3,
            display_name="User One",
        )
        assert c.reply_count == 3
        assert c.display_name == "User One"

    def test_backward_compatible(self):
        c = CommentData(text="hello", username="test", like_count=1)
        assert c.text == "hello"


class TestVideoStatsNewFields:
    def test_share_count(self):
        v = VideoStats(
            video_id="123",
            play_count=10000,
            like_count=500,
            comment_count=50,
            share_count=200,
        )
        assert v.share_count == 200

    def test_share_count_default_none(self):
        v = VideoStats(video_id="123")
        assert v.share_count is None
