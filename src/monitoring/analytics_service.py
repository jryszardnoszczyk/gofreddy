"""AccountAnalyticsService — own-account post fetching, snapshots, and derived metrics."""

from __future__ import annotations

import asyncio
import dataclasses
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from .exceptions import AnalyticsError
from .intelligence.models_analytics import AccountPost, AccountSnapshot, PerformancePatterns
from .intelligence.performance_patterns import generate_performance_patterns
from .models import DataSource, RawMention
from .repository_analytics import PostgresAnalyticsRepository

logger = logging.getLogger(__name__)


class AccountAnalyticsService:
    """Orchestrates own-account post fetching, snapshot creation, and derived metrics."""

    def __init__(
        self,
        repository: PostgresAnalyticsRepository,
        xpoz_adapter: Any | None = None,
        ic_backend: Any | None = None,
    ) -> None:
        self._repo = repository
        self._xpoz = xpoz_adapter
        self._ic = ic_backend

    async def sync_posts(
        self, org_id: UUID, platform: str, username: str,
    ) -> dict[str, Any]:
        """Fetch posts from adapter and upsert. Returns result dict with error handling."""
        try:
            raw_posts = await self._fetch_posts_from_adapter(platform, username)
            account_posts = [self._map_raw_to_account_post(m, org_id, platform, username) for m in raw_posts]
            count = await self._repo.upsert_posts(account_posts) if account_posts else 0
            return {"posts_synced": count, "platform": platform, "error": None}
        except Exception:
            logger.warning("sync_posts failed for %s/%s", platform, username, exc_info=True)
            return {"posts_synced": 0, "platform": platform, "error": "Sync failed — check server logs"}

    async def sync_snapshot(
        self, org_id: UUID, platform: str, username: str,
    ) -> AccountSnapshot | None:
        """Fetch current account-level metrics and create a snapshot row."""
        try:
            profile_data = await self._fetch_profile(platform, username)
            if not profile_data:
                return None
            snapshot = AccountSnapshot(
                id=uuid4(),
                org_id=org_id,
                platform=platform,
                username=username,
                follower_count=profile_data.get("follower_count"),
                following_count=profile_data.get("following_count"),
                post_count=profile_data.get("post_count"),
                engagement_rate=profile_data.get("engagement_rate"),
                audience_data=profile_data.get("audience_data", {}),
                created_at=datetime.now(timezone.utc),
            )
            return await self._repo.insert_snapshot(snapshot)
        except Exception:
            logger.warning("sync_snapshot failed for %s/%s", platform, username, exc_info=True)
            return None

    async def get_dashboard(
        self, org_id: UUID, platform: str, username: str,
    ) -> dict[str, Any]:
        """Derived metrics for dashboard rendering."""
        posts, latest_snapshot, patterns_result = await asyncio.gather(
            self._repo.get_posts(org_id, platform, username, limit=200),
            self._repo.get_latest_snapshot(org_id, platform, username),
            self._repo.get_patterns(org_id, platform, username),
        )

        total_engagement = sum(p.likes + p.comments + p.shares for p in posts)
        avg_engagement = total_engagement / len(posts) if posts else 0

        return {
            "platform": platform,
            "username": username,
            "total_posts": len(posts),
            "avg_engagement": round(avg_engagement, 2),
            "latest_snapshot": dataclasses.asdict(latest_snapshot) if latest_snapshot else None,
            "has_patterns": patterns_result is not None,
            "pattern_post_count": patterns_result[2] if patterns_result else 0,
        }

    async def get_posting_heatmap(
        self, org_id: UUID, platform: str, username: str,
    ) -> dict[str, dict[str, float]]:
        """Returns {day_of_week: {hour: avg_engagement}} for heatmap rendering."""
        posts = await self._repo.get_posts_for_patterns(org_id, platform, username, max_posts=500)

        heatmap: dict[str, dict[str, list[float]]] = {}
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for p in posts:
            if p.published_at is None:
                continue
            day = day_names[p.published_at.weekday()]
            hour = str(p.published_at.hour)
            heatmap.setdefault(day, {}).setdefault(hour, []).append(
                p.engagement_rate if p.engagement_rate is not None else float(p.likes + p.comments + p.shares)
            )

        result: dict[str, dict[str, float]] = {}
        for day, hours in heatmap.items():
            result[day] = {}
            for hour, values in hours.items():
                result[day][hour] = round(sum(values) / len(values), 4) if values else 0.0
        return result

    async def get_patterns(
        self, org_id: UUID, platform: str, username: str,
    ) -> tuple[dict[str, Any], str, int] | None:
        """Get stored patterns. Returns (pattern_data, markdown, post_count) or None."""
        return await self._repo.get_patterns(org_id, platform, username)

    async def get_patterns_as_dataclass(
        self, org_id: UUID, platform: str, username: str,
    ) -> PerformancePatterns | None:
        """Get stored patterns reconstructed as PerformancePatterns dataclass."""
        result = await self._repo.get_patterns(org_id, platform, username)
        if not result:
            return None
        pattern_data = result[0]
        try:
            from datetime import date
            pattern_data["period_start"] = date.fromisoformat(str(pattern_data.get("period_start", "")))
            pattern_data["period_end"] = date.fromisoformat(str(pattern_data.get("period_end", "")))
            return PerformancePatterns(**pattern_data)
        except Exception:
            logger.warning("Failed to deserialize PerformancePatterns", exc_info=True)
            return None

    async def recompute_patterns(
        self, org_id: UUID, platform: str, username: str,
    ) -> PerformancePatterns:
        """Recompute and persist patterns from account_posts."""
        posts, snapshots = await asyncio.gather(
            self._repo.get_posts_for_patterns(org_id, platform, username),
            self._repo.get_snapshots(org_id, platform, username),
        )
        patterns = generate_performance_patterns(posts, snapshots)
        await self._repo.upsert_patterns(
            org_id, platform, username,
            pattern_data=dataclasses.asdict(patterns),
            markdown=patterns.markdown,
            post_count=patterns.total_posts,
        )
        return patterns

    # ── Private helpers ──

    async def _fetch_posts_from_adapter(self, platform: str, username: str) -> list[RawMention]:
        """Route to correct adapter based on platform."""
        if platform in ("twitter", "instagram"):
            if not self._xpoz:
                raise AnalyticsError("Xpoz adapter not configured")
            ds = DataSource.TWITTER if platform == "twitter" else DataSource.INSTAGRAM
            return await self._xpoz.get_posts_by_author(username, platform=ds, limit=50)
        elif platform in ("tiktok", "youtube"):
            if not self._ic:
                raise AnalyticsError("IC backend not configured")
            result = await self._ic.get_content(platform, username)
            return self._map_ic_posts(result, platform, username)
        else:
            raise AnalyticsError(f"Unsupported platform: {platform}")

    async def _fetch_profile(self, platform: str, username: str) -> dict[str, Any] | None:
        """Fetch account-level profile data for snapshots."""
        if platform in ("twitter", "instagram"):
            if not self._xpoz:
                return None
            ds = DataSource.TWITTER if platform == "twitter" else DataSource.INSTAGRAM
            user = await self._xpoz.get_user_profile(username, platform=ds)
            if not user:
                return None
            return {
                "follower_count": user.follower_count,
                "following_count": user.following_count,
                "post_count": user.post_count,
                "engagement_rate": None,
                "audience_data": {},
            }
        elif platform in ("tiktok", "youtube"):
            if not self._ic:
                return None
            result = await self._ic.get_discovery(platform, username)
            if not result:
                return None
            profile = result.get("profile", result)
            return {
                "follower_count": profile.get("followers") or profile.get("follower_count"),
                "following_count": profile.get("following") or profile.get("following_count"),
                "post_count": profile.get("posts_count") or profile.get("post_count"),
                "engagement_rate": profile.get("engagement_rate"),
                "audience_data": {},
            }
        return None

    def _map_raw_to_account_post(
        self, raw: RawMention, org_id: UUID, platform: str, username: str,
    ) -> AccountPost:
        """Map RawMention from adapter to AccountPost for storage."""
        likes = raw.engagement_likes
        shares = raw.engagement_shares
        comments = raw.engagement_comments
        impressions = raw.metadata.get("impressions", 0) or 0

        engagement_rate: float | None = None
        if impressions > 0:
            engagement_rate = (likes + comments + shares) / impressions

        hashtags = raw.metadata.get("hashtags", [])
        if isinstance(hashtags, str):
            hashtags = [h.strip() for h in hashtags.split(",") if h.strip()]

        return AccountPost(
            id=uuid4(),
            org_id=org_id,
            platform=platform,
            username=username,
            source_id=raw.source_id,
            content=raw.content,
            published_at=raw.published_at,
            likes=likes,
            shares=shares,
            comments=comments,
            impressions=impressions,
            engagement_rate=engagement_rate,
            media_type=raw.metadata.get("media_type"),
            hashtags=hashtags if isinstance(hashtags, list) else [],
            metadata={k: v for k, v in raw.metadata.items() if k not in ("hashtags", "media_type", "impressions")},
            created_at=datetime.now(timezone.utc),
        )

    def _map_ic_posts(self, result: dict[str, Any], platform: str, username: str) -> list[RawMention]:
        """Map IC get_content response to list of RawMention."""
        posts_data = result.get("data", result.get("posts", []))
        if isinstance(posts_data, dict):
            posts_data = posts_data.get("posts", [])
        if not isinstance(posts_data, list):
            return []

        mentions: list[RawMention] = []
        for post in posts_data:
            post_url = post.get("url") or post.get("link") or ""
            post_id = post.get("id") or post.get("post_id") or post_url
            source_id = str(post_id) if post_id else f"{platform}:{username}"

            content = post.get("caption") or post.get("description") or post.get("text") or ""

            published_at = None
            taken_at = post.get("taken_at")
            if isinstance(taken_at, (int, float)):
                published_at = datetime.fromtimestamp(taken_at, tz=timezone.utc)
            elif isinstance(taken_at, str):
                try:
                    published_at = datetime.fromisoformat(taken_at.replace("Z", "+00:00"))
                except ValueError:
                    pass
            if published_at is None:
                date_str = post.get("published_at") or post.get("created_at") or post.get("date")
                if date_str and isinstance(date_str, str):
                    try:
                        published_at = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    except ValueError:
                        pass

            engagement = post.get("engagement") or {}
            likes = int(engagement.get("likes") or post.get("likes") or post.get("digg_count") or 0)
            comments_count = int(engagement.get("comments") or post.get("comments") or post.get("comment_count") or 0)
            shares = int(engagement.get("shares") or post.get("shares") or post.get("share_count") or 0)

            metadata: dict[str, Any] = {}
            views = int(engagement.get("views") or post.get("views") or post.get("play_count") or 0)
            if views:
                metadata["impressions"] = views
            if post.get("hashtags"):
                metadata["hashtags"] = post["hashtags"]
            if post.get("duration"):
                metadata["video_duration"] = post["duration"]
            media_type = post.get("media_type") or post.get("type")
            if media_type:
                metadata["media_type"] = media_type

            _DS_MAP = {
                "twitter": DataSource.TWITTER,
                "instagram": DataSource.INSTAGRAM,
                "tiktok": DataSource.TIKTOK,
                "youtube": DataSource.YOUTUBE,
            }
            ds = _DS_MAP.get(platform, DataSource.TWITTER)

            mentions.append(RawMention(
                source=ds,
                source_id=source_id,
                author_handle=username,
                content=content,
                url=post_url or None,
                published_at=published_at,
                engagement_likes=likes,
                engagement_comments=comments_count,
                engagement_shares=shares,
                metadata=metadata,
            ))
        return mentions
