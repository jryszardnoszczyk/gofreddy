"""Instagram video fetcher using Apify actors."""

from __future__ import annotations

import asyncio
import re
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Self

from apify_client import ApifyClientAsync

from ..common.cost_recorder import APIFY_COST_PER_CU, cost_recorder as _cost_recorder
from ..common.enums import Platform
from .base import BaseFetcher


def _apify_cost(run: dict) -> float | None:
    """Extract actual cost from an Apify run dict.

    Prefers ``usageTotalUsd`` (real billing data returned by Apify API).
    Falls back to ``computeUnits * rate`` if unavailable.
    """
    total = run.get("usageTotalUsd")
    if total is not None:
        return float(total)
    cu = (run.get("stats") or {}).get("computeUnits", 0)
    return (cu * APIFY_COST_PER_CU) if cu else None
from .exceptions import CreatorNotFoundError, DownloadError, VideoUnavailableError
from .models import CommentData, CreatorStats, FollowerProfile, VideoResult, VideoStats

if TYPE_CHECKING:
    from ..storage import R2VideoStorage
    from .config import FetcherSettings


class InstagramFetcher(BaseFetcher):
    """Fetch Instagram videos via Apify actors."""

    REEL_SCRAPER_ACTOR = "apify/instagram-reel-scraper"
    PROFILE_SCRAPER_ACTOR = "apify/instagram-profile-scraper"

    def __init__(
        self,
        storage: R2VideoStorage,
        settings: FetcherSettings | None = None,
    ) -> None:
        super().__init__(storage, settings)
        self._apify_client: ApifyClientAsync | None = None

    @property
    def platform(self) -> Platform:
        return Platform.INSTAGRAM

    async def __aenter__(self) -> Self:
        await super().__aenter__()
        return self

    async def __aexit__(self, *args) -> None:
        await super().__aexit__(*args)
        # ApifyClientAsync doesn't need explicit close

    def _apify(self) -> ApifyClientAsync:
        """Lazily create the Apify client only when a provider call is needed.

        Some runtimes may raise pyo3 panic exceptions (BaseException) during
        client construction. Convert those to regular fetcher errors so callers
        can degrade gracefully instead of crashing test/session setup.
        """
        if self._apify_client is not None:
            return self._apify_client

        try:
            self._apify_client = ApifyClientAsync(
                token=self.settings.apify_token.get_secret_value()
            )
        except BaseException as e:  # noqa: BLE001 - pyo3 PanicException is BaseException
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            raise DownloadError(
                self.platform,
                "apify_client_init",
                f"Apify client initialization failed: {type(e).__name__}",
            ) from e

        return self._apify_client

    async def _scrape_reel(self, reel_url: str) -> dict[str, Any]:
        """Scrape a single reel via Apify actor."""
        client = self._apify()
        run_input = {
            "directUrls": [reel_url],
            "resultsLimit": 1,
            "username": ["_"],  # Required by actor schema; unused when directUrls present
        }

        run = await client.actor(self.REEL_SCRAPER_ACTOR).call(
            run_input=run_input,
            timeout_secs=120,
            logger=None,
        )

        if not run:
            raise DownloadError(self.platform, reel_url, "Apify actor failed")

        await _cost_recorder.record("apify", "ig_reel_scrape", cost_usd=_apify_cost(run), model=self.REEL_SCRAPER_ACTOR)
        dataset = client.dataset(run["defaultDatasetId"])
        items = await dataset.list_items()

        if not items.items:
            raise VideoUnavailableError(self.platform, reel_url)

        for item in items.items:
            if isinstance(item, dict):
                return item
        raise VideoUnavailableError(self.platform, reel_url)

    async def _fetch_and_store(self, video_id: str) -> VideoResult:
        """Fetch Instagram reel and store to R2."""
        # Construct reel URL
        reel_url = f"https://www.instagram.com/reel/{video_id}/"

        # Scrape via Apify
        item = await self._scrape_reel(reel_url)

        video_url = item.get("videoUrl")
        # Skip if only displayUrl (image, not video)
        if not video_url:
            raise VideoUnavailableError(self.platform, video_id)

        # Download video
        async def get_fresh_url() -> str:
            fresh_item = await self._scrape_reel(reel_url)
            url = fresh_item.get("videoUrl")
            if not url:
                raise VideoUnavailableError(self.platform, video_id)
            return url

        temp_path = await self._download_with_retry(
            video_id, video_url, get_fresh_url
        )

        try:
            # Get file size before upload
            file_size = temp_path.stat().st_size

            # Upload to R2 using temp file path (matches R2VideoStorage interface)
            await self.storage.upload(
                local_path=temp_path,
                platform=self.platform,
                video_id=video_id,
            )

            # Parse timestamp
            timestamp_str = item.get("timestamp")
            posted_at = None
            if timestamp_str:
                try:
                    posted_at = datetime.fromisoformat(
                        timestamp_str.replace("Z", "+00:00")
                    )
                except ValueError:
                    pass

            # Extract hashtags and mentions from caption
            caption = item.get("caption") or ""
            hashtags = re.findall(r"#(\w+)", caption)[:20] if caption else None
            mentions = re.findall(r"@([\w.]+)", caption)[:20] if caption else None

            return VideoResult(
                video_id=video_id,
                platform=self.platform,
                r2_key=f"videos/instagram/{video_id}.mp4",
                title=caption or None,
                description=caption or None,
                creator_username=item.get("ownerUsername"),
                creator_id=item.get("ownerId"),
                duration_seconds=int(item.get("duration", 0)),
                view_count=item.get("videoViewCount") or item.get("playsCount"),
                like_count=item.get("likesCount"),
                comment_count=item.get("commentsCount"),
                posted_at=posted_at,
                fetched_at=datetime.now(timezone.utc),
                file_size_bytes=file_size,
                thumbnail_url=item.get("displayUrl"),
                hashtags=hashtags or None,
                mentions=mentions or None,
            )
        finally:
            temp_path.unlink(missing_ok=True)

    async def _list_creator_videos(
        self, handle: str, limit: int
    ) -> list[VideoStats]:
        """List reel IDs and per-video stats from an Instagram creator's profile."""
        client = self._apify()
        run_input = {
            "username": [handle],
            "resultsLimit": limit,
        }

        run = await client.actor(self.REEL_SCRAPER_ACTOR).call(
            run_input=run_input,
            timeout_secs=300,
            logger=None,
        )

        if not run:
            raise CreatorNotFoundError(self.platform, handle)

        await _cost_recorder.record("apify", "ig_list_reels", cost_usd=_apify_cost(run), model=self.REEL_SCRAPER_ACTOR)
        dataset = client.dataset(run["defaultDatasetId"])
        items = await dataset.list_items()

        if not items.items:
            raise CreatorNotFoundError(self.platform, handle)

        results: list[VideoStats] = []
        for item in items.items:
            if not isinstance(item, dict):
                continue
            video_id = item.get("shortCode") or item.get("id")
            if video_id:
                # Apify reel scraper: timestamp (ISO str), caption, videoDuration (float s)
                raw_ts = item.get("timestamp")
                posted_at = None
                if isinstance(raw_ts, str):
                    try:
                        posted_at = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
                    except (ValueError, TypeError):
                        pass
                elif isinstance(raw_ts, (int, float)):
                    posted_at = datetime.fromtimestamp(int(raw_ts), tz=timezone.utc)
                raw_dur = item.get("videoDuration")
                results.append(VideoStats(
                    video_id=video_id,
                    play_count=item.get("videoViewCount") or item.get("videoPlayCount"),
                    like_count=item.get("likesCount"),
                    comment_count=item.get("commentsCount"),
                    posted_at=posted_at,
                    title=item.get("caption") or None,
                    duration_seconds=int(raw_dur) if raw_dur is not None else None,
                ))
        return results

    # ─── Fraud Detection Methods ────────────────────────────────────────────

    # NOTE: apify/instagram-follower-scraper was removed from Apify (circa Feb 2026).
    # Instagram fraud detection uses follower COUNT (from profile scraper), not follower LIST.
    # If follower-list collection is needed again, re-evaluate third-party provider support first.
    FOLLOWER_SCRAPER_ACTOR = "apify/instagram-follower-scraper"
    COMMENT_SCRAPER_ACTOR = "apify/instagram-comment-scraper"

    async def fetch_followers(
        self, username: str, count: int = 100
    ) -> list[FollowerProfile]:
        """Fetch a sample of followers for fraud analysis.

        Args:
            username: Instagram username
            count: Number of followers to fetch (50-200)

        Returns:
            List of FollowerProfile objects
        """
        self._validate_handle(username)
        count = max(50, min(count, 200))
        client = self._apify()

        run_input = {
            "username": [username],
            "resultsLimit": count,
        }

        try:
            run = await client.actor(self.FOLLOWER_SCRAPER_ACTOR).call(
                run_input=run_input,
                timeout_secs=300,
                logger=None,
            )
        except Exception as e:
            raise DownloadError(
                self.platform, username,
                f"Follower scraper unavailable: {e}",
            ) from e

        if not run:
            raise CreatorNotFoundError(self.platform, username)

        await _cost_recorder.record("apify", "ig_fetch_followers", cost_usd=_apify_cost(run), model=self.FOLLOWER_SCRAPER_ACTOR)
        dataset = client.dataset(run["defaultDatasetId"])
        items = await dataset.list_items()

        followers = []
        for user in items.items:
            if not isinstance(user, dict):
                continue
            followers.append(
                FollowerProfile(
                    username=user.get("username", ""),
                    has_profile_pic=bool(user.get("profilePicUrl")),
                    bio=user.get("biography"),
                    post_count=user.get("postsCount", 0),
                    follower_count=user.get("followersCount"),
                    following_count=user.get("followingCount"),
                )
            )

        return followers

    async def fetch_comments(
        self, post_url: str, count: int = 50
    ) -> list[CommentData]:
        """Fetch comments from a post for bot detection.

        Args:
            post_url: Instagram post/reel URL
            count: Number of comments to fetch (max 50)

        Returns:
            List of CommentData objects
        """
        count = min(count, 50)
        client = self._apify()

        run_input = {
            "directUrls": [post_url],
            "resultsLimit": count,
        }

        run = await client.actor(self.COMMENT_SCRAPER_ACTOR).call(
            run_input=run_input,
            timeout_secs=120,
            logger=None,
        )

        if not run:
            return []  # Graceful degradation

        await _cost_recorder.record("apify", "ig_fetch_comments", cost_usd=_apify_cost(run), model=self.COMMENT_SCRAPER_ACTOR)
        dataset = client.dataset(run["defaultDatasetId"])
        items = await dataset.list_items()

        comments = []
        for comment in items.items:
            if not isinstance(comment, dict):
                continue
            posted_at = None
            timestamp_str = comment.get("timestamp")
            if timestamp_str:
                try:
                    posted_at = datetime.fromisoformat(
                        timestamp_str.replace("Z", "+00:00")
                    )
                except ValueError:
                    pass

            comments.append(
                CommentData(
                    text=comment.get("text", ""),
                    username=comment.get("ownerUsername", ""),
                    like_count=comment.get("likesCount"),
                    posted_at=posted_at,
                )
            )

        return comments

    async def fetch_profile_stats(self, username: str) -> CreatorStats:
        """Fetch creator profile statistics for fraud analysis.

        Args:
            username: Instagram username

        Returns:
            CreatorStats object with profile data
        """
        self._validate_handle(username)
        client = self._apify()

        run_input = {
            "usernames": [username],
            "resultsLimit": 1,
        }

        run = await client.actor(self.PROFILE_SCRAPER_ACTOR).call(
            run_input=run_input,
            timeout_secs=120,
            logger=None,
        )

        if not run:
            raise CreatorNotFoundError(self.platform, username)

        await _cost_recorder.record("apify", "ig_fetch_profile", cost_usd=_apify_cost(run), model=self.PROFILE_SCRAPER_ACTOR)
        dataset = client.dataset(run["defaultDatasetId"])
        items = await dataset.list_items()

        if not items.items:
            raise CreatorNotFoundError(self.platform, username)

        profile = next((item for item in items.items if isinstance(item, dict)), None)
        if profile is None:
            raise CreatorNotFoundError(self.platform, username)

        return CreatorStats(
            username=profile.get("username", username),
            platform=self.platform,
            follower_count=profile.get("followersCount"),
            following_count=profile.get("followingCount"),
            video_count=profile.get("postsCount"),
            total_likes=None,  # Not directly available
            total_views=None,  # Not directly available
            avg_likes=None,  # Would need to calculate from posts
            avg_comments=None,  # Would need to calculate from posts
            display_name=profile.get("fullName"),
            bio=profile.get("biography"),
            is_verified=profile.get("verified", False),
        )

    # ─── Search Methods (PR-012) ───────────────────────────────────────────────

    SEARCH_SCRAPER_ACTOR = "apify/instagram-search-scraper"
    HASHTAG_SCRAPER_ACTOR = "apify/instagram-hashtag-scraper"

    async def search_keyword(self, query: str, limit: int = 50) -> list[dict[str, Any]]:
        """Search Instagram content by keyword.

        Args:
            query: Search query string
            limit: Maximum number of results (default 50)

        Returns:
            List of post data dictionaries
        """
        # Strip chars disallowed by Apify instagram-search-scraper
        query = re.sub(r"[!?.,:;\-+=*&%$#@/\\~^|<>()\[\]{}\"\\'`]", "", query).strip()
        if not query:
            return []

        client = self._apify()
        run_input = {
            "search": query,
            "resultsLimit": limit,
        }

        run = await client.actor(self.SEARCH_SCRAPER_ACTOR).call(
            run_input=run_input,
            timeout_secs=300,
            logger=None,
        )

        if not run:
            return []  # Graceful degradation

        await _cost_recorder.record("apify", "ig_search_videos", cost_usd=_apify_cost(run), model=self.SEARCH_SCRAPER_ACTOR)
        dataset = client.dataset(run["defaultDatasetId"])
        items = await dataset.list_items()

        return [item for item in items.items if isinstance(item, dict)]

    async def search_hashtag(
        self, hashtag: str | None = None, limit: int = 50,
        *, hashtags: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Search Instagram reels by hashtag(s).

        Args:
            hashtag: Single hashtag to search (without #). Deprecated, use hashtags.
            limit: Maximum number of video results (default 50)
            hashtags: List of hashtags to search (without #). Takes precedence over hashtag.

        Returns:
            List of reel/video data dictionaries
        """
        tags = hashtags or ([hashtag.lstrip("#")] if hashtag else [])
        tags = [t.lstrip("#") for t in tags if t]
        if not tags:
            return []

        client = self._apify()

        run_input = {
            "hashtags": tags,
            "resultsLimit": limit,
            "resultsType": "reels",
        }

        run = await client.actor(self.HASHTAG_SCRAPER_ACTOR).call(
            run_input=run_input,
            timeout_secs=300,
            logger=None,
        )

        if not run:
            return []  # Graceful degradation

        await _cost_recorder.record("apify", "ig_search_hashtag", cost_usd=_apify_cost(run), model=self.HASHTAG_SCRAPER_ACTOR)
        dataset = client.dataset(run["defaultDatasetId"])
        items = await dataset.list_items()

        return [item for item in items.items if isinstance(item, dict)][:limit]

    # ─── Stories Methods (PR-018) ───────────────────────────────────────────────

    STORY_SCRAPER_ACTOR = "louisdeconinck/instagram-stories-scraper"
    MAX_STORY_FETCH_RETRIES = 3

    async def fetch_stories(self, username: str) -> list:
        """Fetch active Stories from an Instagram account.

        Args:
            username: Instagram username

        Returns:
            List of StoryResult objects with media URLs and metadata

        Raises:
            CreatorNotFoundError: If username doesn't exist
            RateLimitError: If API rate limit hit after retries
        """
        from ..stories.models import StoryResult

        self._validate_handle(username)
        client = self._apify()

        run_input = {
            "usernames": [username],
        }

        # Retry with limits to prevent API quota burn
        run = None
        for attempt in range(self.MAX_STORY_FETCH_RETRIES):
            try:
                run = await client.actor(self.STORY_SCRAPER_ACTOR).call(
                    run_input=run_input,
                    timeout_secs=120,
                    logger=None,
                )
                break
            except Exception as e:
                if attempt == self.MAX_STORY_FETCH_RETRIES - 1:
                    raise DownloadError(
                        self.platform,
                        "stories",
                        f"Failed after {self.MAX_STORY_FETCH_RETRIES} attempts: {e}",
                    )
                await asyncio.sleep(2**attempt)  # Simple backoff: 1s, 2s, 4s

        if not run:
            return []  # No active stories - graceful empty response

        await _cost_recorder.record("apify", "ig_fetch_stories", cost_usd=_apify_cost(run), model=self.STORY_SCRAPER_ACTOR)
        dataset = client.dataset(run["defaultDatasetId"])
        items = await dataset.list_items()

        stories = []
        for item in items.items:
            posted_at = None
            timestamp_val = item.get("timestamp") or item.get("takenAt")
            if timestamp_val:
                try:
                    if isinstance(timestamp_val, int):
                        posted_at = datetime.fromtimestamp(timestamp_val, tz=timezone.utc)
                    else:
                        posted_at = datetime.fromisoformat(
                            timestamp_val.replace("Z", "+00:00")
                        )
                except (ValueError, OSError):
                    pass

            expires_at = posted_at + timedelta(hours=24) if posted_at else None

            # Get media URL (video or image)
            media_url = item.get("videoUrl") or item.get("imageUrl")
            if not media_url:
                continue  # Skip stories without media URL

            stories.append(
                StoryResult(
                    story_id=item.get("id"),
                    media_url=media_url,
                    media_type="video" if item.get("videoUrl") else "image",
                    creator_username=username,
                    posted_at=posted_at,
                    expires_at=expires_at,
                    duration_seconds=int(item.get("duration", 0)) // 1000
                    if item.get("videoUrl") and item.get("duration", 0) > 1000
                    else (int(item.get("duration", 0)) if item.get("videoUrl") else None),
                    raw_metadata=item,
                )
            )

        return stories
