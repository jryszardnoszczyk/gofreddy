"""TikTok video fetcher using ScrapeCreators API."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from ..common.cost_recorder import SCRAPECREATORS_COST_PER_REQUEST, cost_recorder as _cost_recorder
from ..common.enums import Platform
from .base import BaseFetcher
from .exceptions import CreatorNotFoundError, RateLimitError, VideoUnavailableError
from .models import AudioTrackInfo, CommentData, CreatorStats, FollowerProfile, VideoResult, VideoStats

# Pre-compiled regex for VTT HTML tag stripping
_VTT_TAG_RE = re.compile(r"<[^>]+>")
_MENTION_RE = re.compile(r"@([\w.]+)")
_HASHTAG_RE = re.compile(r"#(\w+)")


class TikTokFetcher(BaseFetcher):
    """Fetch TikTok videos via ScrapeCreators API."""

    @property
    def platform(self) -> Platform:
        return Platform.TIKTOK

    @staticmethod
    def _parse_vtt_to_text(vtt_text: str) -> str | None:
        """Parse VTT string to plain text, removing timestamps and tags."""
        if len(vtt_text) > 1_000_000:
            return None
        lines: list[str] = []
        for line in vtt_text.splitlines():
            line = line.strip()
            if not line or line.startswith("WEBVTT") or "-->" in line or line.isdigit():
                continue
            clean = _VTT_TAG_RE.sub("", line)
            if clean.strip():
                lines.append(clean.strip())
        deduped: list[str] = []
        for line in lines:
            if not deduped or deduped[-1] != line:
                deduped.append(line)
        result = " ".join(deduped)
        return result if result.strip() else None

    @staticmethod
    def _as_dict(value: Any) -> dict[str, Any]:
        """Coerce unknown provider payload values to dicts safely."""
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _as_list_of_dicts(value: Any) -> list[dict[str, Any]]:
        """Coerce unknown provider payload values to list[dict]."""
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, dict)]

    @staticmethod
    def _as_int_or_none(value: Any) -> int | None:
        """Coerce numeric-like values safely to int."""
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _coalesce_int(*values: Any) -> int | None:
        """Return the first value that can be safely coerced to int."""
        for value in values:
            coerced = TikTokFetcher._as_int_or_none(value)
            if coerced is not None:
                return coerced
        return None

    async def _fetch_video_metadata(self, video_id: str) -> dict[str, Any]:
        """Fetch video metadata from ScrapeCreators."""
        url = f"{self.settings.scrapecreators_base_url}/v2/tiktok/video"
        headers = {
            "x-api-key": self.settings.scrapecreators_api_key.get_secret_value(),
            "Content-Type": "application/json",
        }
        # The /v2/tiktok/video endpoint requires a full TikTok URL, not a video_id.
        # The @_ placeholder username works — TikTok resolves by video ID regardless.
        params = {
            "url": f"https://www.tiktok.com/@_/video/{video_id}",
            "get_transcript": True,
        }

        response = await self._http_client.get(
            url, headers=headers, params=params
        )

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                self.platform,
                int(retry_after) if retry_after else None,
            )
        if response.status_code == 404:
            raise VideoUnavailableError(self.platform, video_id)

        response.raise_for_status()
        await _cost_recorder.record("scrapecreators", "fetch_video", cost_usd=SCRAPECREATORS_COST_PER_REQUEST)
        return response.json()

    def _extract_download_url(self, data: dict) -> str:
        """Extract no-watermark download URL from response."""
        aweme = self._as_dict(data.get("aweme_detail"))
        video = self._as_dict(aweme.get("video"))
        play_addr = self._as_dict(video.get("play_addr"))
        url_list = play_addr.get("url_list")

        if isinstance(url_list, list):
            for url in url_list:
                if isinstance(url, str) and url:
                    return url

        raise ValueError("No download URL in ScrapeCreators response")

    async def _fetch_and_store(self, video_id: str) -> VideoResult:
        """Fetch TikTok video and store to R2."""
        # Get metadata
        data = await self._fetch_video_metadata(video_id)
        aweme = self._as_dict(data.get("aweme_detail"))

        # Extract VTT transcript (ScrapeCreators returns WebVTT at top level)
        raw_transcript = data.get("transcript")
        transcript_text = (
            self._parse_vtt_to_text(raw_transcript)
            if isinstance(raw_transcript, str) and raw_transcript
            else None
        )

        # Download with URL expiration handling
        async def get_fresh_url() -> str:
            fresh_data = await self._fetch_video_metadata(video_id)
            return self._extract_download_url(fresh_data)

        download_url = self._extract_download_url(data)
        temp_path = await self._download_with_retry(
            video_id, download_url, get_fresh_url
        )

        try:
            # Get file size before upload (for result)
            file_size = temp_path.stat().st_size

            # Upload to R2 using temp file path (not bytes - matches R2VideoStorage interface)
            await self.storage.upload(
                local_path=temp_path,
                platform=self.platform,
                video_id=video_id,
            )

            # Build result
            stats = self._as_dict(aweme.get("statistics"))
            author = self._as_dict(aweme.get("author"))
            video = self._as_dict(aweme.get("video"))
            music = self._as_dict(aweme.get("music"))
            posted_at = self._as_int_or_none(aweme.get("create_time"))
            duration_ms = self._as_int_or_none(video.get("duration")) or 0

            # Extract hashtags from cha_list or description
            desc = aweme.get("desc") or ""
            cha_list = aweme.get("cha_list")
            if isinstance(cha_list, list) and cha_list:
                hashtags = [c.get("cha_name") or c.get("hashtag_name", "") for c in cha_list if isinstance(c, dict)][:20]
            else:
                hashtags = _HASHTAG_RE.findall(desc)[:20] if desc else None

            # Extract mentions from description
            mentions = _MENTION_RE.findall(desc)[:20] if desc else None

            # Audio track metadata
            audio_track = None
            if music.get("title") or music.get("author"):
                audio_track = AudioTrackInfo(
                    title=music.get("title"),
                    artist=music.get("author"),
                    is_original=music.get("is_original"),
                )

            return VideoResult(
                video_id=video_id,
                platform=self.platform,
                r2_key=f"videos/tiktok/{video_id}.mp4",
                title=desc or None,
                description=desc or None,
                creator_username=author.get("unique_id"),
                creator_id=author.get("uid"),
                duration_seconds=max(0, duration_ms // 1000),
                view_count=self._as_int_or_none(stats.get("play_count")),
                like_count=self._as_int_or_none(stats.get("digg_count")),
                comment_count=self._as_int_or_none(stats.get("comment_count")),
                posted_at=datetime.fromtimestamp(posted_at, tz=timezone.utc) if posted_at else None,
                fetched_at=datetime.now(timezone.utc),
                file_size_bytes=file_size,
                transcript_text=transcript_text,
                thumbnail_url=video.get("cover") or video.get("origin_cover"),
                share_count=self._as_int_or_none(stats.get("share_count")),
                hashtags=hashtags or None,
                mentions=mentions or None,
                audio_track=audio_track,
            )
        finally:
            temp_path.unlink(missing_ok=True)

    async def _list_creator_videos(
        self, handle: str, limit: int
    ) -> list[VideoStats]:
        """List video IDs and per-video stats from a TikTok creator's profile."""
        url = f"{self.settings.scrapecreators_base_url}/v3/tiktok/profile/videos"
        headers = {
            "x-api-key": self.settings.scrapecreators_api_key.get_secret_value(),
        }
        params = {"handle": handle, "count": limit}

        response = await self._http_client.get(
            url, headers=headers, params=params
        )

        if response.status_code == 404:
            raise CreatorNotFoundError(self.platform, handle)

        response.raise_for_status()
        await _cost_recorder.record("scrapecreators", "list_videos", cost_usd=SCRAPECREATORS_COST_PER_REQUEST)
        data = response.json()
        videos = self._as_list_of_dicts(data.get("aweme_list"))

        results: list[VideoStats] = []
        for video in videos:
            raw_id = video.get("aweme_id")
            if isinstance(raw_id, (str, int)) and str(raw_id):
                stats = self._as_dict(video.get("statistics"))
                create_time = self._as_int_or_none(video.get("create_time"))
                video_info = self._as_dict(video.get("video"))
                duration_ms = self._as_int_or_none(video_info.get("duration"))
                results.append(VideoStats(
                    video_id=str(raw_id),
                    play_count=self._as_int_or_none(stats.get("play_count")),
                    like_count=self._as_int_or_none(stats.get("digg_count")),
                    comment_count=self._as_int_or_none(stats.get("comment_count")),
                    share_count=self._as_int_or_none(stats.get("share_count")),
                    posted_at=datetime.fromtimestamp(create_time, tz=timezone.utc) if create_time else None,
                    title=video.get("desc") or None,
                    duration_seconds=duration_ms // 1000 if duration_ms else None,
                ))
        return results

    # ─── Fraud Detection Methods ────────────────────────────────────────────

    async def fetch_followers(
        self, username: str, count: int = 100
    ) -> list[FollowerProfile]:
        """Fetch a sample of followers for fraud analysis.

        Args:
            username: TikTok username (handle)
            count: Number of followers to fetch (50-200)

        Returns:
            List of FollowerProfile objects
        """
        self._validate_handle(username)
        count = max(50, min(count, 200))  # Clamp to 50-200

        url = f"{self.settings.scrapecreators_base_url}/v1/tiktok/user/followers"
        headers = {
            "x-api-key": self.settings.scrapecreators_api_key.get_secret_value(),
        }
        params = {"handle": username, "count": count}

        response = await self._http_client.get(url, headers=headers, params=params)

        if response.status_code == 404:
            raise CreatorNotFoundError(self.platform, username)
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                self.platform,
                int(retry_after) if retry_after else None,
            )

        response.raise_for_status()
        await _cost_recorder.record("scrapecreators", "fetch_followers", cost_usd=SCRAPECREATORS_COST_PER_REQUEST)
        data = response.json()

        followers = []
        for user in self._as_list_of_dicts(data.get("users")):
            followers.append(
                FollowerProfile(
                    username=user.get("unique_id", ""),
                    has_profile_pic=bool(user.get("avatar_thumb")),
                    bio=user.get("signature"),
                    post_count=self._as_int_or_none(user.get("aweme_count")) or 0,
                    follower_count=self._as_int_or_none(user.get("follower_count")),
                    following_count=self._as_int_or_none(user.get("following_count")),
                )
            )

        return followers

    async def fetch_comments(
        self, video_url: str, count: int = 50
    ) -> list[CommentData]:
        """Fetch comments from a video for bot detection.

        Args:
            video_url: Full TikTok video URL
            count: Number of comments to fetch (max 50)

        Returns:
            List of CommentData objects
        """
        count = min(count, 50)

        url = f"{self.settings.scrapecreators_base_url}/v1/tiktok/video/comments"
        headers = {
            "x-api-key": self.settings.scrapecreators_api_key.get_secret_value(),
        }
        params = {"url": video_url, "count": count}

        response = await self._http_client.get(url, headers=headers, params=params)

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                self.platform,
                int(retry_after) if retry_after else None,
            )

        response.raise_for_status()
        await _cost_recorder.record("scrapecreators", "fetch_comments", cost_usd=SCRAPECREATORS_COST_PER_REQUEST)
        data = response.json()

        comments = []
        for comment in self._as_list_of_dicts(data.get("comments")):
            comment_user = self._as_dict(comment.get("user"))
            posted_at = None
            create_time = self._as_int_or_none(comment.get("create_time"))
            if create_time:
                posted_at = datetime.fromtimestamp(create_time, tz=timezone.utc)

            comments.append(
                CommentData(
                    text=comment.get("text", ""),
                    username=comment_user.get("unique_id", ""),
                    like_count=self._as_int_or_none(comment.get("digg_count")),
                    posted_at=posted_at,
                    reply_count=self._as_int_or_none(comment.get("reply_comment_total")),
                    display_name=comment_user.get("nickname"),
                )
            )

        return comments

    async def fetch_profile_stats(self, username: str) -> CreatorStats:
        """Fetch creator profile statistics for fraud analysis.

        Args:
            username: TikTok username (handle)

        Returns:
            CreatorStats object with profile data
        """
        self._validate_handle(username)

        url = f"{self.settings.scrapecreators_base_url}/v1/tiktok/profile"
        headers = {
            "x-api-key": self.settings.scrapecreators_api_key.get_secret_value(),
        }
        params = {"handle": username}

        response = await self._http_client.get(url, headers=headers, params=params)

        if response.status_code == 404:
            raise CreatorNotFoundError(self.platform, username)
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                self.platform,
                int(retry_after) if retry_after else None,
            )

        response.raise_for_status()
        await _cost_recorder.record("scrapecreators", "fetch_stats", cost_usd=SCRAPECREATORS_COST_PER_REQUEST)
        data = response.json()

        user = self._as_dict(data.get("user"))
        stats = self._as_dict(data.get("stats"))
        profile_username = user.get("uniqueId")
        if not profile_username:
            profile_username = user.get("unique_id")
        if not isinstance(profile_username, str):
            profile_username = username

        return CreatorStats(
            username=profile_username,
            platform=self.platform,
            follower_count=self._coalesce_int(
                stats.get("followerCount"),
                stats.get("follower_count"),
            ),
            following_count=self._coalesce_int(
                stats.get("followingCount"),
                stats.get("following_count"),
            ),
            video_count=self._coalesce_int(
                stats.get("videoCount"),
                stats.get("video_count"),
            ),
            total_likes=self._coalesce_int(
                stats.get("heart"),
                stats.get("heart_count"),
            ),
            total_views=None,  # Not directly available
            avg_likes=None,  # Would need to calculate from videos
            avg_comments=None,  # Would need to calculate from videos
            display_name=user.get("nickname") if isinstance(user.get("nickname"), str) else None,
            bio=user.get("signature") if isinstance(user.get("signature"), str) else None,
            is_verified=user.get("verified", False),
        )

    # ─── Search Methods (PR-012) ───────────────────────────────────────────────

    async def search_keyword(self, query: str, limit: int = 50) -> list[dict[str, Any]]:
        """Search TikTok videos by keyword.

        Args:
            query: Search query string
            limit: Maximum number of results (default 50)

        Returns:
            List of video data dictionaries
        """
        url = f"{self.settings.scrapecreators_base_url}/v1/tiktok/search/keyword"
        headers = {
            "x-api-key": self.settings.scrapecreators_api_key.get_secret_value(),
        }
        params = {"query": query, "count": limit}

        response = await self._http_client.get(url, headers=headers, params=params)

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                self.platform,
                int(retry_after) if retry_after else None,
            )

        response.raise_for_status()
        await _cost_recorder.record("scrapecreators", "search_videos", cost_usd=SCRAPECREATORS_COST_PER_REQUEST)
        data = response.json()
        for key in ("aweme_list", "search_item_list", "videos"):
            results = self._as_list_of_dicts(data.get(key))
            if results:
                # search_item_list wraps each item in {"aweme_info": {...}} — unwrap
                if key == "search_item_list":
                    results = [
                        r["aweme_info"] if isinstance(r.get("aweme_info"), dict) else r
                        for r in results
                    ]
                return results
        return []

    async def search_hashtag(self, hashtag: str, limit: int = 50) -> list[dict[str, Any]]:
        """Search TikTok videos by hashtag.

        Args:
            hashtag: Hashtag to search (without #)
            limit: Maximum number of results (default 50)

        Returns:
            List of video data dictionaries
        """
        # Remove # if present
        hashtag = hashtag.lstrip("#")

        url = f"{self.settings.scrapecreators_base_url}/v1/tiktok/search/hashtag"
        headers = {
            "x-api-key": self.settings.scrapecreators_api_key.get_secret_value(),
        }
        params = {"hashtag": hashtag, "count": limit}

        response = await self._http_client.get(url, headers=headers, params=params)

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                self.platform,
                int(retry_after) if retry_after else None,
            )

        response.raise_for_status()
        await _cost_recorder.record("scrapecreators", "search_by_hashtag", cost_usd=SCRAPECREATORS_COST_PER_REQUEST)
        data = response.json()
        for key in ("aweme_list", "videos"):
            results = self._as_list_of_dicts(data.get(key))
            if results:
                return results
        return []
