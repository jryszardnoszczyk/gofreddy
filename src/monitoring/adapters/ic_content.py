"""IC (Influencers.club) monitoring adapter — TikTok + YouTube via discovery + content API."""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Any

from ...common.cost_recorder import (
    IC_COST_PER_CONTENT,
    IC_COST_PER_DISCOVERY_CREATOR,
    cost_recorder as _cost_recorder,
)
from ...search.exceptions import ICUnavailableError
from ..config import MonitoringSettings
from ..exceptions import MentionFetchError
from ..fetcher_protocol import BaseMentionFetcher
from ..models import DataSource, RawMention

logger = logging.getLogger(__name__)

# Regex to extract quoted terms from boolean queries like: "TestBrand" OR "test brand"
_QUOTED_TERM_RE = re.compile(r'"([^"]+)"')

# IC platform string mapping from DataSource enum
_DATASOURCE_TO_IC_PLATFORM: dict[DataSource, str] = {
    DataSource.TIKTOK: "tiktok",
    DataSource.YOUTUBE: "youtube",
}

# Concurrency for parallel content fetches per adapter call
_CONTENT_SEMAPHORE_LIMIT = 5

# Max creators to discover per fetch (page 0 only)
_DISCOVERY_LIMIT = 20


def _parse_query(query: str) -> dict[str, Any]:
    """Extract IC discovery filters from a boolean monitoring query.

    Returns dict with ``keywords_in_captions`` (list of quoted terms) and
    ``ai_search`` (full query for semantic matching). Boolean operators
    (AND/OR/NOT) are stripped since IC doesn't support them.
    """
    quoted = _QUOTED_TERM_RE.findall(query)
    # Fallback: if no quoted terms, use the raw query as a single keyword
    keywords = quoted if quoted else [query.strip()]
    # Clean up empty strings
    keywords = [k for k in keywords if k.strip()]
    return {
        "keywords_in_captions": keywords,
        "ai_search": query.strip(),
    }


def _safe_int(val: Any) -> int:
    if val is None:
        return 0
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


def _parse_unix_timestamp(val: Any) -> datetime | None:
    if val is None:
        return None
    try:
        return datetime.fromtimestamp(int(val), tz=timezone.utc)
    except (ValueError, TypeError, OSError):
        return None


class ICContentAdapter(BaseMentionFetcher):
    """IC-based monitoring for TikTok and YouTube.

    Two-step flow: discover creators mentioning brand → fetch their recent posts.
    Registered for both DataSource.TIKTOK and DataSource.YOUTUBE in dependencies.py.

    Does NOT own ICBackend lifecycle — close() is a no-op.
    """

    ADAPTER_TIMEOUT = 60.0

    def __init__(
        self,
        ic_backend: Any,  # ICBackend — Any to avoid circular import
        *,
        default_source: DataSource,
        settings: MonitoringSettings | None = None,
    ) -> None:
        if default_source not in _DATASOURCE_TO_IC_PLATFORM:
            raise ValueError(f"ICContentAdapter does not support {default_source}")
        self._ic = ic_backend
        self._default_source = default_source
        self._ic_platform = _DATASOURCE_TO_IC_PLATFORM[default_source]
        super().__init__(settings=settings, timeout_override=self.ADAPTER_TIMEOUT)

    @property
    def source(self) -> DataSource:
        return self._default_source

    async def _do_fetch(
        self,
        query: str,
        *,
        cursor: str | None = None,
        limit: int = 100,
    ) -> tuple[list[RawMention], str | None]:
        """Discover creators mentioning brand, fetch their content, map to RawMention."""
        try:
            # Step 1: Parse query into IC discovery filters
            filters = _parse_query(query)

            # Step 2: Discover creators
            discovery = await self._ic.discover(
                self._ic_platform,
                filters=filters,
                page=0,
                limit=_DISCOVERY_LIMIT,
            )
            accounts = discovery.get("accounts") or []
            if not accounts:
                logger.info(
                    "ic_discovery_empty: platform=%s query=%s",
                    self._ic_platform, query[:80],
                )
                return [], None

            await _cost_recorder.record(
                "ic", "discovery_monitoring",
                cost_usd=IC_COST_PER_DISCOVERY_CREATOR * len(accounts),
            )

            # Step 3: Fetch content for each creator (parallel, semaphore-limited)
            sem = asyncio.Semaphore(_CONTENT_SEMAPHORE_LIMIT)

            async def _fetch_creator_content(handle: str) -> list[dict[str, Any]]:
                async with sem:
                    try:
                        result = await self._ic.get_content(self._ic_platform, handle)
                        await _cost_recorder.record(
                            "ic", "content_monitoring",
                            cost_usd=IC_COST_PER_CONTENT,
                        )
                        posts = result.get("posts") or result.get("data") or []
                        return posts if isinstance(posts, list) else []
                    except ICUnavailableError:
                        raise  # Permanent — propagate
                    except Exception as exc:
                        logger.warning(
                            "ic_content_fetch_failed: platform=%s handle=%s error=%s",
                            self._ic_platform, handle, exc,
                        )
                        return []

            # Extract handles from discovered accounts
            handles = []
            for acct in accounts:
                handle = (
                    acct.get("handle")
                    or acct.get("username")
                    or acct.get("user_id")
                    or ""
                )
                if handle:
                    handles.append(str(handle))

            if not handles:
                return [], None

            # Fetch all content in parallel
            all_posts_nested = await asyncio.gather(
                *[_fetch_creator_content(h) for h in handles],
                return_exceptions=True,
            )

            # Build handle→account lookup for author metadata
            handle_to_account: dict[str, dict[str, Any]] = {}
            for acct, handle in zip(accounts, handles):
                handle_to_account[handle] = acct

            # Step 4: Map posts to RawMention
            mentions: list[RawMention] = []
            for handle, posts_or_exc in zip(handles, all_posts_nested):
                if isinstance(posts_or_exc, ICUnavailableError):
                    raise MentionFetchError(
                        f"IC unavailable during content fetch: {posts_or_exc}"
                    )
                if isinstance(posts_or_exc, BaseException):
                    logger.warning(
                        "ic_content_exception: handle=%s error=%s",
                        handle, posts_or_exc,
                    )
                    continue
                for post in posts_or_exc:
                    if not isinstance(post, dict):
                        continue
                    mention = self._map_post(post, handle, handle_to_account.get(handle, {}))
                    mentions.append(mention)

            # Sort by published_at descending, limit
            mentions.sort(
                key=lambda m: m.published_at or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True,
            )
            return mentions[:limit], None  # No cursor (single page per run)

        except ICUnavailableError as exc:
            raise MentionFetchError(
                f"IC unavailable for {self._ic_platform}: {exc}"
            ) from exc

    def _map_post(
        self,
        post: dict[str, Any],
        handle: str,
        account: dict[str, Any],
    ) -> RawMention:
        """Map an IC content post to RawMention."""
        # Source ID: prefer post URL for stability, fall back to post ID
        post_url = post.get("url") or post.get("link") or ""
        post_id = post.get("id") or post.get("post_id") or post_url
        source_id = str(post_id) if post_id else f"{self._ic_platform}:{handle}:{post.get('taken_at', '')}"

        # Content: caption or description
        content = post.get("caption") or post.get("description") or post.get("text") or ""

        # Published at
        published_at = _parse_unix_timestamp(post.get("taken_at"))
        if published_at is None:
            # Try ISO date string
            date_str = post.get("published_at") or post.get("created_at") or post.get("date")
            if date_str and isinstance(date_str, str):
                try:
                    published_at = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except ValueError:
                    pass

        # Engagement
        engagement = post.get("engagement") or {}
        likes = _safe_int(engagement.get("likes") or post.get("likes") or post.get("digg_count"))
        comments = _safe_int(engagement.get("comments") or post.get("comments") or post.get("comment_count"))
        shares = _safe_int(engagement.get("shares") or post.get("shares") or post.get("share_count"))
        views = _safe_int(engagement.get("views") or post.get("views") or post.get("play_count"))

        # Media URLs
        media_urls: list[str] = []
        thumbnail = post.get("thumbnail") or post.get("cover") or post.get("image")
        if thumbnail and isinstance(thumbnail, str):
            media_urls.append(thumbnail)

        # Metadata
        metadata: dict[str, Any] = {}
        if post.get("hashtags"):
            metadata["hashtags"] = post["hashtags"]
        if post.get("duration"):
            metadata["video_duration"] = post["duration"]
        if account.get("followers"):
            metadata["author_followers"] = _safe_int(account["followers"])
        if account.get("verified"):
            metadata["author_verified"] = True

        return RawMention(
            source=self._default_source,
            source_id=source_id,
            author_handle=handle,
            author_name=account.get("name") or account.get("full_name"),
            content=content,
            url=post_url or None,
            published_at=published_at,
            engagement_likes=likes,
            engagement_shares=shares,
            engagement_comments=comments,
            reach_estimate=views or None,
            media_urls=media_urls,
            metadata=metadata,
        )

    async def close(self) -> None:
        """No-op — adapter does NOT own ICBackend lifecycle."""
