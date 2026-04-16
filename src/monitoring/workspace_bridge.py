"""Workspace bridge — save monitoring mentions to workspace collections."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from uuid import UUID

from .models import Mention

if TYPE_CHECKING:
    from ..workspace.repository import PostgresWorkspaceRepository

logger = logging.getLogger(__name__)


class WorkspaceBridge:
    """Maps monitoring mentions to workspace items for canvas display."""

    def __init__(self, workspace_repo: PostgresWorkspaceRepository) -> None:
        self._workspace_repo = workspace_repo

    async def save_mentions(
        self,
        mentions: list[Mention],
        collection_id: UUID,
        annotations: dict[str, str] | None = None,
    ) -> int:
        """Save mentions as workspace items. Returns count of items added.

        Uses workspace repo's add_items() with built-in dedup.
        """
        if not mentions:
            return 0

        items = [self._mention_to_item(m, annotations) for m in mentions]
        return await self._workspace_repo.add_items(collection_id, items)

    def _mention_to_item(self, mention: Mention, annotations: dict[str, str] | None = None) -> dict:
        """Convert a Mention to a workspace item dict."""
        # Use title from metadata if available, otherwise truncate content
        title = None
        if mention.metadata:
            title = mention.metadata.get("title")
        if not title and mention.content:
            title = mention.content[:100]

        # Serialize mention to payload
        payload = {
            "mention_id": str(mention.id),
            "monitor_id": str(mention.monitor_id),
            "source": mention.source.value,
            "source_id": mention.source_id,
            "author_handle": mention.author_handle,
            "author_name": mention.author_name,
            "content": mention.content,
            "url": mention.url,
            "published_at": mention.published_at.isoformat() if mention.published_at else None,
            "sentiment_score": mention.sentiment_score,
            "sentiment_label": mention.sentiment_label.value if mention.sentiment_label else None,
            "engagement_likes": mention.engagement_likes,
            "engagement_shares": mention.engagement_shares,
            "engagement_comments": mention.engagement_comments,
            "intent": mention.intent,
            "language": mention.language,
            "geo_country": mention.geo_country,
            "metadata": mention.metadata,
        }

        if annotations and str(mention.id) in annotations:
            payload["user_annotation"] = annotations[str(mention.id)][:500]

        return {
            "source_id": mention.source_id,
            "platform": mention.source.value,
            "title": title,
            "creator_handle": mention.author_handle,
            "payload_json": payload,
        }
