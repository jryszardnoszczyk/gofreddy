"""Hybrid creator search for competitive intelligence.

Aggregates creator discovery across TikTok (ScrapeCreators), YouTube (yt-dlp),
and website scraping to find competitor-affiliated creators.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

from ..common.cost_recorder import cost_recorder as _cost_recorder

if TYPE_CHECKING:
    from ..fetcher.tiktok import TikTokFetcher
    from ..fetcher.youtube import YouTubeFetcher
    from ..search.service import SearchService

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CreatorResult:
    """A creator discovered through competitive search."""

    username: str
    platform: str
    display_name: str = ""
    follower_count: int | None = None
    bio: str = ""
    content_type: str = ""  # e.g., "product_review", "sponsored", "organic"
    relevance_signal: str = ""  # Why this creator was flagged
    profile_url: str = ""
    source: str = ""  # How we found them: "tiktok_search", "youtube_search", "website_scrape"


@dataclass
class CreatorSearchResult:
    """Aggregated creator search results."""

    query: str
    creators: list[CreatorResult] = field(default_factory=list)
    platforms_searched: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class CreatorSearchService:
    """Search for creators across platforms for competitive intelligence."""

    MAX_RESULTS_PER_PLATFORM = 20

    def __init__(
        self,
        tiktok_fetcher: TikTokFetcher | None = None,
        youtube_fetcher: YouTubeFetcher | None = None,
        search_service: SearchService | None = None,
    ) -> None:
        self._tiktok = tiktok_fetcher
        self._youtube = youtube_fetcher
        self._search = search_service

    async def search_creators(
        self,
        query: str,
        *,
        platforms: list[str] | None = None,
        limit: int = 20,
    ) -> CreatorSearchResult:
        """Search for creators mentioning a brand or topic.

        Args:
            query: Brand name, product, or topic to search for.
            platforms: Limit to specific platforms. Default: all available.
            limit: Max results per platform.
        """
        result = CreatorSearchResult(query=query)
        limit = min(limit, self.MAX_RESULTS_PER_PLATFORM)
        search_platforms = platforms or ["tiktok", "youtube"]

        tasks: list[asyncio.Task] = []
        task_labels: list[str] = []

        if "tiktok" in search_platforms and self._tiktok:
            tasks.append(asyncio.create_task(self._search_tiktok(query, limit)))
            task_labels.append("tiktok")
            result.platforms_searched.append("tiktok")

        if "youtube" in search_platforms and self._youtube:
            tasks.append(asyncio.create_task(self._search_youtube(query, limit)))
            task_labels.append("youtube")
            result.platforms_searched.append("youtube")

        if "content" in search_platforms and self._search:
            tasks.append(asyncio.create_task(self._search_content(query, limit)))
            task_labels.append("content")
            result.platforms_searched.append("content")

        if not tasks:
            result.errors.append("No search platforms available")
            return result

        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        for label, raw in zip(task_labels, raw_results):
            if isinstance(raw, Exception):
                logger.warning("creator_search_failed: %s: %s", label, raw)
                result.errors.append(f"{label}: {type(raw).__name__}")
            elif isinstance(raw, list):
                result.creators.extend(raw)

        await _cost_recorder.record(
            "creator_search",
            "search_creators",
            cost_usd=0.002 * len(result.platforms_searched),
            metadata={"query": query, "platforms": result.platforms_searched},
        )

        return result

    async def _search_tiktok(self, query: str, limit: int) -> list[CreatorResult]:
        """Search TikTok for creators via TikTokFetcher.search_keyword()."""
        if not self._tiktok:
            return []

        try:
            items = await self._tiktok.search_keyword(query=query, limit=limit)

            creators = []
            for item in items[:limit]:
                author = item.get("author") or item.get("authorInfos") or {}
                nickname = author.get("nickname") or author.get("nickName", "")
                unique_id = author.get("uniqueId") or author.get("unique_id", "")
                stats = item.get("authorStats") or item.get("stats") or {}

                if not unique_id:
                    continue

                creators.append(CreatorResult(
                    username=unique_id,
                    platform="tiktok",
                    display_name=nickname,
                    follower_count=stats.get("followerCount") or stats.get("fans"),
                    bio=author.get("signature", ""),
                    relevance_signal=f"TikTok keyword search: '{query}'",
                    profile_url=f"https://www.tiktok.com/@{unique_id}",
                    source="tiktok_search",
                ))
            return creators
        except Exception as e:
            logger.warning("tiktok_creator_search_failed: %s", e)
            raise

    async def _search_youtube(self, query: str, limit: int) -> list[CreatorResult]:
        """Search YouTube for creators via YouTubeFetcher.search()."""
        if not self._youtube:
            return []

        try:
            items = await self._youtube.search(query=query, max_results=limit)

            creators = []
            seen_channels: set[str] = set()
            for entry in items:
                channel = entry.get("channel") or entry.get("uploader", "")
                channel_id = entry.get("channel_id", "")
                if not channel or channel_id in seen_channels:
                    continue
                seen_channels.add(channel_id)

                creators.append(CreatorResult(
                    username=channel_id or channel,
                    platform="youtube",
                    display_name=channel,
                    follower_count=entry.get("channel_follower_count"),
                    relevance_signal=f"YouTube search: '{query}'",
                    profile_url=f"https://www.youtube.com/channel/{channel_id}" if channel_id else "",
                    source="youtube_search",
                ))

            return creators[:limit]
        except Exception as e:
            logger.warning("youtube_creator_search_failed: %s", e)
            raise

    async def _search_content(self, query: str, limit: int) -> list[CreatorResult]:
        """Search content platforms via existing SearchService."""
        if not self._search:
            return []

        try:
            results = await self._search.search(query=query)
            items = results.get("results", [])

            creators = []
            seen: set[str] = set()
            for item in items[:limit * 2]:
                username = item.get("creator_username") or item.get("author", "")
                platform = item.get("platform", "unknown")
                key = f"{platform}:{username}"
                if not username or key in seen:
                    continue
                seen.add(key)

                creators.append(CreatorResult(
                    username=username,
                    platform=platform,
                    display_name=item.get("creator_display_name", username),
                    follower_count=item.get("follower_count"),
                    content_type=item.get("content_type", ""),
                    relevance_signal=f"Content search: '{query}'",
                    source="content_search",
                ))

            return creators[:limit]
        except Exception as e:
            logger.warning("content_creator_search_failed: %s", e)
            raise
