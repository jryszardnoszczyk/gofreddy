"""RSS/Atom feed monitor for blog-to-social draft creation.

Two usage paths:
1. Standalone: `freddy write from-rss --feed-url X --platforms linkedin,bluesky`
2. Automated: cron calls process_feeds() for all configured feeds.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID

import httpx

from .exceptions import PublishError
from .models import FeedConfig, FeedEntry

if TYPE_CHECKING:
    from .repository import PostgresPublishingRepository

logger = logging.getLogger(__name__)

_MAX_FEED_SIZE = 1_048_576  # 1MB — prevent XML bombs


class RSSMonitor:
    """Monitor RSS/Atom feeds and create social drafts for new entries."""

    def __init__(
        self,
        http: httpx.AsyncClient,
        repository: PostgresPublishingRepository,
    ) -> None:
        self._http = http
        self._repo = repository

    async def parse_feed(self, feed_url: str) -> list[FeedEntry]:
        """Fetch and parse an RSS/Atom feed URL."""
        from ..common.url_validation import resolve_and_validate

        await resolve_and_validate(feed_url)

        try:
            resp = await self._http.get(
                feed_url,
                headers={"User-Agent": "Freddy/1.0 RSS Monitor"},
                timeout=15.0,
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise PublishError(f"Failed to fetch feed: {feed_url}") from exc

        if len(resp.content) > _MAX_FEED_SIZE:
            raise PublishError("Feed exceeds 1MB size limit")

        import feedparser

        parsed = feedparser.parse(resp.text)
        entries: list[FeedEntry] = []
        for entry in parsed.entries:
            # feedparser values can be None even when key is present
            title = (getattr(entry, "title", None) or "").strip()
            link = (getattr(entry, "link", None) or "").strip()
            summary = (getattr(entry, "summary", None) or "").strip()

            if not link:
                continue

            # Parse published date
            published_at = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                except (TypeError, ValueError):
                    pass

            # Content HTML
            content_html = None
            if hasattr(entry, "content") and entry.content:
                # entry.content is a list of dicts with 'type' and 'value' keys
                for c in entry.content:
                    if isinstance(c, dict) and c.get("value"):
                        content_html = c["value"]
                        break

            # Tags
            tags: list[str] = []
            if hasattr(entry, "tags") and entry.tags:
                tags = [(t.get("term") or "").strip() for t in entry.tags if isinstance(t, dict)]
                tags = [t for t in tags if t]

            entries.append(FeedEntry(
                title=title,
                url=link,
                summary=summary,
                published_at=published_at,
                author=(getattr(entry, "author", None) or "").strip() or None,
                content_html=content_html,
                tags=tags,
            ))

        return entries

    async def create_draft_from_entry(
        self,
        entry: FeedEntry,
        platform: str,
        org_id: UUID,
        connection_id: UUID,
    ) -> UUID | None:
        """Create a publish_queue draft from a feed entry. Returns None if duplicate."""
        # Dedup check: skip if we already have a draft from this URL
        existing = await self._repo.find_queue_item_by_source_url(
            org_id=org_id, platform=platform, source_url=entry.url,
        )
        if existing:
            return None

        body = entry.title
        if entry.summary:
            body += f"\n\n{entry.summary}"
        body += f"\n\n{entry.url}"

        item = await self._repo.create_queue_item(
            org_id=org_id,
            platform=platform,
            connection_id=connection_id,
            content_parts=[{"body": body, "url": entry.url, "title": entry.title}],
            labels=entry.tags[:5],
            metadata={"source_url": entry.url, "source": "rss"},
        )
        return item.id

    async def process_feeds(self, feeds: list[FeedConfig]) -> list[UUID]:
        """Process multiple feeds, creating drafts for new entries."""
        created_ids: list[UUID] = []
        for feed in feeds:
            try:
                entries = await self.parse_feed(feed.feed_url)
                for entry in entries[:10]:  # Limit to 10 most recent per feed
                    for platform in feed.target_platforms:
                        conn_id = feed.connection_ids.get(platform)
                        if not conn_id:
                            continue
                        try:
                            item_id = await self.create_draft_from_entry(
                                entry, platform, feed.org_id, conn_id,
                            )
                            if item_id is not None:
                                created_ids.append(item_id)
                        except Exception:
                            logger.warning(
                                "rss_draft_creation_failed",
                                extra={"url": entry.url, "platform": platform},
                                exc_info=True,
                            )
            except Exception:
                logger.warning(
                    "rss_feed_processing_failed",
                    extra={"feed_url": feed.feed_url},
                    exc_info=True,
                )
        return created_ids
