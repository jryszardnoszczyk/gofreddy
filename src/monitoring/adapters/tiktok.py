"""TikTok monitoring via Apify scraper (interim until Xpoz adds TikTok)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Self

import httpx

from ...common.cost_recorder import APIFY_COST_PER_CU, cost_recorder as _cost_recorder
from ..config import MonitoringSettings
from ..exceptions import MentionFetchError
from ..fetcher_protocol import BaseMentionFetcher
from ..models import DataSource, RawMention

logger = logging.getLogger(__name__)


def _parse_unix_timestamp(val: Any) -> datetime | None:
    if val is None:
        return None
    try:
        return datetime.fromtimestamp(int(val), tz=timezone.utc)
    except (ValueError, TypeError, OSError):
        return None


def _safe_int(val: Any) -> int:
    if val is None:
        return 0
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


class TikTokAdapter(BaseMentionFetcher):
    """TikTok monitoring via Apify scraper (interim until Xpoz adds TikTok)."""

    ACTOR_ID = "clockworks~tiktok-scraper"
    APIFY_BASE = "https://api.apify.com/v2"
    ADAPTER_TIMEOUT = 150.0  # Apify waitForFinish=120 + buffer

    def __init__(self, settings: MonitoringSettings | None = None) -> None:
        base_settings = settings or MonitoringSettings()
        # Override timeout — BaseMentionFetcher reads self._settings.adapter_timeout_seconds
        super().__init__(base_settings.model_copy(update={"adapter_timeout_seconds": self.ADAPTER_TIMEOUT}))
        self._apify_token = self._settings.apify_token.get_secret_value()
        self._client: httpx.AsyncClient | None = None

    @property
    def source(self) -> DataSource:
        return DataSource.TIKTOK

    async def __aenter__(self) -> Self:
        self._client = httpx.AsyncClient(
            base_url=self.APIFY_BASE,
            headers={"Authorization": f"Bearer {self._apify_token}"},
            timeout=httpx.Timeout(connect=5.0, read=130.0, write=5.0, pool=5.0),
            limits=httpx.Limits(max_connections=5, max_keepalive_connections=2),
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            try:
                await self._client.aclose()
            except RuntimeError:
                pass
            self._client = None

    async def _do_fetch(
        self,
        query: str,
        *,
        cursor: str | None = None,
        limit: int = 100,
    ) -> tuple[list[RawMention], str | None]:
        if self._client is None:
            raise MentionFetchError("adapter not initialized — call __aenter__ first")

        # Start actor run
        run_input = {
            "searchQueries": [query],
            "resultsPerPage": min(limit, 50),
            "shouldDownloadVideos": False,
            "shouldDownloadCovers": False,
        }
        response = await self._client.post(
            f"/acts/{self.ACTOR_ID}/runs",
            json=run_input,
            params={"waitForFinish": 120},
        )
        if response.status_code == 401:
            raise MentionFetchError("Apify: invalid token")
        if response.status_code == 402:
            raise MentionFetchError("Apify: insufficient credits")
        response.raise_for_status()

        run_data = response.json().get("data", {})
        dataset_id = run_data.get("defaultDatasetId")
        if not dataset_id:
            return [], None

        # Fetch dataset items
        items_response = await self._client.get(
            f"/datasets/{dataset_id}/items",
            params={"format": "json", "limit": limit},
        )
        items_response.raise_for_status()
        items = items_response.json()

        actual_cost = run_data.get("usageTotalUsd") if run_data else None
        if actual_cost is not None:
            cost_usd: float | None = float(actual_cost)
        else:
            cu = run_data.get("stats", {}).get("computeUnits", 0) if run_data else 0
            cost_usd = (cu * APIFY_COST_PER_CU) if cu else None
        await _cost_recorder.record("apify", "tiktok_monitoring", cost_usd=cost_usd, model=self.ACTOR_ID)

        mentions = []
        for item in items:
            if isinstance(item, dict):
                mentions.append(self._map_tiktok(item))

        return mentions, None  # Apify doesn't support cursor-based pagination

    def _map_tiktok(self, item: dict[str, Any]) -> RawMention:
        # Author info
        author = item.get("authorMeta") or item.get("author") or {}
        author_handle = author.get("name") or author.get("uniqueId")

        # Hashtags
        hashtags = []
        for tag in item.get("hashtags") or []:
            if isinstance(tag, dict):
                hashtags.append(tag.get("name", ""))
            elif isinstance(tag, str):
                hashtags.append(tag)

        # Media URLs
        media_urls = []
        video = item.get("videoMeta") or item.get("video") or {}
        cover_url = video.get("coverUrl") or video.get("cover")
        if cover_url:
            media_urls.append(cover_url)

        # Metadata
        metadata: dict[str, Any] = {}
        if hashtags:
            metadata["hashtags"] = hashtags
        play_addr = video.get("playAddr") or video.get("downloadAddr")
        if play_addr:
            metadata["video_urls"] = [play_addr]
        if video.get("duration"):
            metadata["video_duration"] = video["duration"]

        music = item.get("musicMeta") or item.get("music") or {}
        music_name = music.get("musicName") or music.get("title")
        if music_name:
            music_author = music.get("musicAuthor") or music.get("authorName", "")
            metadata["music"] = f"{music_name} — {music_author}"

        if item.get("isPaidPartnership") or item.get("isAd"):
            metadata["is_paid"] = True
        if item.get("locationCreated"):
            metadata["city"] = item["locationCreated"]
        if item.get("diversificationLabels"):
            metadata["ai_tags"] = item["diversificationLabels"]

        # Subtitles (searchable text from video)
        subtitles = item.get("subtitleInfos")
        if subtitles and isinstance(subtitles, list):
            metadata["subtitles"] = subtitles

        # Author profiling
        fans = author.get("fans") or author.get("followerCount")
        if fans:
            metadata["author_followers"] = fans
        if author.get("verified"):
            metadata["author_verified"] = True
        if author.get("id"):
            metadata["author_id"] = author["id"]

        # Engagement
        stats = item.get("stats")
        if isinstance(stats, dict):
            likes = stats.get("diggCount", 0)
            comments = stats.get("commentCount", 0)
            shares = stats.get("shareCount", 0)
            views = stats.get("playCount", 0)
        else:
            likes = item.get("diggCount", 0)
            comments = item.get("commentCount", 0)
            shares = item.get("shareCount", 0)
            views = item.get("playCount", 0)

        if item.get("collectCount"):
            metadata["save_count"] = item["collectCount"]
        if item.get("repostCount"):
            metadata["repost_count"] = item["repostCount"]

        return RawMention(
            source=DataSource.TIKTOK,
            source_id=str(item.get("id", "")),
            author_handle=author_handle,
            author_name=author.get("nickname"),
            content=item.get("text") or item.get("desc") or "",
            url=item.get("webVideoUrl") or (
                f"https://www.tiktok.com/@{author_handle}/video/{item.get('id')}"
                if author_handle and item.get("id")
                else None
            ),
            published_at=_parse_unix_timestamp(item.get("createTime")),
            engagement_likes=_safe_int(likes),
            engagement_shares=_safe_int(shares),
            engagement_comments=_safe_int(comments),
            reach_estimate=_safe_int(views) or None,
            media_urls=media_urls,
            metadata=metadata,
        )
