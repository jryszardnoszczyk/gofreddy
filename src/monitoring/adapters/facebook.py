"""Facebook mention fetcher via Apify scraper."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from pydantic import SecretStr

from ...common.cost_recorder import APIFY_COST_PER_CU, cost_recorder as _cost_recorder
from ..config import MonitoringSettings
from ..exceptions import MentionFetchError
from ..fetcher_protocol import BaseMentionFetcher
from ..models import DataSource, RawMention

logger = logging.getLogger(__name__)


def _parse_timestamp(item: dict, key: str = "timestamp") -> datetime | None:
    """Parse a timestamp from an Apify item, always returning tz-aware UTC.

    Handles ISO 8601 strings (with or without offset) and Unix timestamps.
    """
    val = item.get(key)
    if val is None:
        return None
    try:
        if isinstance(val, (int, float)):
            return datetime.fromtimestamp(val, tz=timezone.utc)
        dt = datetime.fromisoformat(str(val).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, OSError):
        return None


def _filter_and_cursor(
    items: list[dict],
    cursor: str | None,
    ts_key: str = "timestamp",
) -> tuple[list[dict], str | None]:
    """Filter items newer than cursor timestamp, return new cursor.

    Args:
        items: Raw Apify result items
        cursor: ISO 8601 timestamp string (tz-aware) or None
        ts_key: Key to read timestamp from each item

    Returns:
        Tuple of (filtered_items, new_cursor_iso_string_or_none)
    """
    if cursor:
        cutoff = datetime.fromisoformat(cursor)
        items = [
            i for i in items
            if (_parse_timestamp(i, ts_key) or datetime.min.replace(tzinfo=timezone.utc)) > cutoff
        ]

    if not items:
        return items, None

    timestamps = [_parse_timestamp(i, ts_key) for i in items]
    valid = [t for t in timestamps if t is not None]
    if not valid:
        return items, None

    latest = max(valid)
    return items, latest.isoformat()


class FacebookMentionFetcher(BaseMentionFetcher):
    """Fetch mentions from Facebook via Apify scraper.

    Uses apify/facebook-posts-scraper actor. All Apify exceptions are caught
    inside _do_fetch() and converted to MentionFetchError to prevent the base
    class from retrying (which burns Apify compute units).
    """

    ACTOR_ID = "apify/facebook-posts-scraper"

    def __init__(
        self,
        apify_token: SecretStr,
        settings: MonitoringSettings | None = None,
    ) -> None:
        super().__init__(settings)
        # Override base class timeout to accommodate Apify actor spin-up + scrape
        self._settings = self._settings.model_copy(
            update={"adapter_timeout_seconds": self._settings.apify_adapter_timeout_seconds + 10}
        )
        self._apify_token = apify_token
        self._client: Any = None  # ApifyClientAsync, lazy init

    @property
    def source(self) -> DataSource:
        return DataSource.FACEBOOK

    def _apify(self) -> Any:
        """Lazy Apify client init (mirrors InstagramFetcher pattern)."""
        if self._client is not None:
            return self._client
        try:
            from apify_client import ApifyClientAsync

            self._client = ApifyClientAsync(
                self._apify_token.get_secret_value()
            )
        except BaseException as exc:  # noqa: BLE001 - pyo3 PanicException
            if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                raise
            raise MentionFetchError(f"Apify client init failed: {exc}") from exc
        return self._client

    async def _do_fetch(
        self,
        query: str,
        *,
        cursor: str | None = None,
        limit: int = 100,
    ) -> tuple[list[RawMention], str | None]:
        try:
            client = self._apify()
            run = await client.actor(self.ACTOR_ID).call(
                run_input={
                    "searchTerms": [query],
                    "resultsLimit": limit,
                    "proxy": {"useApifyProxy": True},
                },
                timeout_secs=int(self._settings.apify_adapter_timeout_seconds),
            )
            if run is None or run.get("status") != "SUCCEEDED":
                raise MentionFetchError(
                    f"Apify actor {self.ACTOR_ID} failed: "
                    f"status={run.get('status') if run else 'None'}"
                )
            items = (
                await client.dataset(run["defaultDatasetId"]).list_items()
            ).items
            actual_cost = run.get("usageTotalUsd") if run else None
            if actual_cost is not None:
                cost_usd = float(actual_cost)
            else:
                cu = run.get("stats", {}).get("computeUnits", 0) if run else 0
                cost_usd = (cu * APIFY_COST_PER_CU) if cu else None
            await _cost_recorder.record("apify", "facebook_posts", cost_usd=cost_usd, model=self.ACTOR_ID)
        except MentionFetchError:
            raise
        except Exception as exc:
            raise MentionFetchError(f"Facebook fetch failed: {exc}") from exc

        filtered, new_cursor = _filter_and_cursor(items, cursor)
        mentions = [self._map_item(item) for item in filtered]
        return mentions, new_cursor

    def _map_item(self, item: dict) -> RawMention:
        """Map an Apify Facebook post item to RawMention."""
        source_id = item.get("postId") or item.get("id") or ""
        author = item.get("author") or {}
        published_at = _parse_timestamp(item)

        # Media URLs
        media_urls: list[str] = []
        for key in ("image", "video", "thumbnail"):
            val = item.get(key)
            if val and isinstance(val, str):
                media_urls.append(val)

        # Metadata
        metadata: dict[str, Any] = {}
        if author.get("id"):
            metadata["author_id"] = author["id"]
        if author.get("url"):
            metadata["author_url"] = author["url"]
        reactions = item.get("reactions")
        if reactions and isinstance(reactions, dict):
            metadata["reactions"] = reactions
        if item.get("type"):
            metadata["media_type"] = item["type"]
        if item.get("external_url"):
            metadata["urls_in_text"] = item["external_url"]

        return RawMention(
            source=DataSource.FACEBOOK,
            source_id=source_id,
            author_name=author.get("name"),
            content=item.get("message") or "",
            url=item.get("url"),
            published_at=published_at,
            engagement_likes=item.get("reactions_count") or 0,
            engagement_shares=item.get("reshare_count") or 0,
            engagement_comments=item.get("comments_count") or 0,
            language="en",
            media_urls=media_urls,
            metadata=metadata,
        )
