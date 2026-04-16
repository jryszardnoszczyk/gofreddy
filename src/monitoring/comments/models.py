"""Comment inbox domain models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Comment:
    id: UUID
    connection_id: UUID
    org_id: UUID
    platform: str
    external_post_id: str
    external_comment_id: str
    author_handle: str | None
    author_name: str | None
    author_avatar_url: str | None
    body: str
    published_at: datetime
    parent_external_id: str | None
    likes: int
    sentiment_score: float | None
    sentiment_label: str | None
    is_spam: bool
    is_read: bool
    replied_at: datetime | None
    reply_text: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row) -> Comment:
        return cls(
            id=row["id"],
            connection_id=row["connection_id"],
            org_id=row["org_id"],
            platform=row["platform"],
            external_post_id=row["external_post_id"],
            external_comment_id=row["external_comment_id"],
            author_handle=row["author_handle"],
            author_name=row["author_name"],
            author_avatar_url=row["author_avatar_url"],
            body=row["body"],
            published_at=row["published_at"],
            parent_external_id=row["parent_external_id"],
            likes=row["likes"],
            sentiment_score=row["sentiment_score"],
            sentiment_label=row["sentiment_label"],
            is_spam=row["is_spam"],
            is_read=row["is_read"],
            replied_at=row["replied_at"],
            reply_text=row["reply_text"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


@dataclass(frozen=True, slots=True)
class CommentSyncResult:
    synced: int
    skipped: int
    errors: int
