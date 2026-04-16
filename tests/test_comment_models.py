"""Tests for comment inbox models."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from src.monitoring.comments.models import Comment, CommentSyncResult


class TestCommentFromRow:
    def test_from_row_maps_all_fields(self):
        row = {
            "id": uuid4(), "connection_id": uuid4(), "org_id": uuid4(),
            "platform": "twitter", "external_post_id": "post_123",
            "external_comment_id": "comment_456",
            "author_handle": "@user", "author_name": "User Name",
            "author_avatar_url": "https://example.com/avatar.jpg",
            "body": "Great post!", "published_at": datetime.now(timezone.utc),
            "parent_external_id": None, "likes": 5,
            "sentiment_score": 0.8, "sentiment_label": "positive",
            "is_spam": False, "is_read": False,
            "replied_at": None, "reply_text": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        comment = Comment.from_row(row)
        assert comment.body == "Great post!"
        assert comment.platform == "twitter"
        assert comment.likes == 5
        assert comment.is_spam is False
        assert comment.author_handle == "@user"
        assert comment.sentiment_score == 0.8

    def test_from_row_handles_null_optional_fields(self):
        row = {
            "id": uuid4(), "connection_id": uuid4(), "org_id": uuid4(),
            "platform": "instagram", "external_post_id": "p1",
            "external_comment_id": "c1",
            "author_handle": None, "author_name": None,
            "author_avatar_url": None, "body": "test",
            "published_at": datetime.now(timezone.utc),
            "parent_external_id": None, "likes": 0,
            "sentiment_score": None, "sentiment_label": None,
            "is_spam": False, "is_read": True,
            "replied_at": None, "reply_text": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        comment = Comment.from_row(row)
        assert comment.author_handle is None
        assert comment.author_name is None
        assert comment.author_avatar_url is None
        assert comment.sentiment_score is None
        assert comment.sentiment_label is None
        assert comment.is_read is True

    def test_from_row_preserves_uuids(self):
        uid = uuid4()
        conn_id = uuid4()
        org_id = uuid4()
        row = {
            "id": uid, "connection_id": conn_id, "org_id": org_id,
            "platform": "tiktok", "external_post_id": "p",
            "external_comment_id": "c",
            "author_handle": "h", "author_name": "n",
            "author_avatar_url": None, "body": "b",
            "published_at": datetime.now(timezone.utc),
            "parent_external_id": "parent_1", "likes": 0,
            "sentiment_score": None, "sentiment_label": None,
            "is_spam": True, "is_read": False,
            "replied_at": datetime.now(timezone.utc), "reply_text": "thanks",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        comment = Comment.from_row(row)
        assert comment.id == uid
        assert comment.connection_id == conn_id
        assert comment.org_id == org_id
        assert comment.parent_external_id == "parent_1"
        assert comment.reply_text == "thanks"


class TestCommentSyncResult:
    def test_values(self):
        result = CommentSyncResult(synced=10, skipped=2, errors=1)
        assert result.synced == 10
        assert result.skipped == 2
        assert result.errors == 1

    def test_frozen(self):
        result = CommentSyncResult(synced=10, skipped=2, errors=1)
        with pytest.raises(AttributeError):
            result.synced = 20  # type: ignore[misc]
