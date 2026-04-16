"""LinkedIn mention fetcher via Apify scraper."""

from __future__ import annotations

import logging
from typing import Any

from pydantic import SecretStr

from ...common.cost_recorder import APIFY_COST_PER_CU, cost_recorder as _cost_recorder
from ..config import MonitoringSettings
from ..exceptions import MentionFetchError
from ..fetcher_protocol import BaseMentionFetcher
from ..models import DataSource, RawMention
from .facebook import _filter_and_cursor, _parse_timestamp

logger = logging.getLogger(__name__)


class LinkedInMentionFetcher(BaseMentionFetcher):
    """Fetch mentions from LinkedIn via Apify scraper.

    Uses curious_coder/linkedin-post-search-scraper actor.
    Hard cap at 50 results due to LinkedIn anti-bot measures.
    """

    ACTOR_ID = "curious_coder/linkedin-post-search-scraper"
    MAX_RESULTS = 50

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
        return DataSource.LINKEDIN

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
        effective_limit = min(limit, self.MAX_RESULTS)
        if limit > self.MAX_RESULTS:
            logger.warning(
                "linkedin_limit_clamped",
                extra={"requested": limit, "clamped_to": self.MAX_RESULTS},
            )

        try:
            client = self._apify()
            run = await client.actor(self.ACTOR_ID).call(
                run_input={
                    "searchTerms": query,  # string, NOT [query] like Facebook
                    "resultsLimit": effective_limit,
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
            await _cost_recorder.record("apify", "linkedin_posts", cost_usd=cost_usd, model=self.ACTOR_ID)
        except MentionFetchError:
            raise
        except Exception as exc:
            raise MentionFetchError(f"LinkedIn fetch failed: {exc}") from exc

        filtered, new_cursor = _filter_and_cursor(items, cursor)
        mentions = [self._map_item(item) for item in filtered]
        return mentions, new_cursor

    def _map_item(self, item: dict) -> RawMention:
        """Map an Apify LinkedIn post item to RawMention."""
        source_id = item.get("urn") or item.get("postUrl") or ""
        author = item.get("author") or {}
        published_at = _parse_timestamp(item)

        # Media URLs
        media_urls: list[str] = []
        for key in ("image", "video", "document"):
            val = item.get(key)
            if val and isinstance(val, str):
                media_urls.append(val)

        # Metadata — B2B valuable fields
        metadata: dict[str, Any] = {}
        if author.get("profile_id"):
            metadata["author_id"] = author["profile_id"]
        if author.get("job_title"):
            metadata["job_title"] = author["job_title"]
        if author.get("company"):
            metadata["company"] = author["company"]
        reactions_detail = item.get("reactions")
        if reactions_detail and isinstance(reactions_detail, dict):
            metadata["reactions"] = reactions_detail
        if item.get("document"):
            metadata["media_type"] = "document"

        # Engagement: reactions can be int (total) or dict (breakdown)
        engagement_likes = 0
        raw_reactions = item.get("reactions")
        if isinstance(raw_reactions, int):
            engagement_likes = raw_reactions
        elif isinstance(raw_reactions, dict):
            engagement_likes = int(sum(v for v in raw_reactions.values() if isinstance(v, (int, float))))

        return RawMention(
            source=DataSource.LINKEDIN,
            source_id=source_id,
            author_name=author.get("name"),
            content=item.get("text") or "",
            url=item.get("url"),
            published_at=published_at,
            engagement_likes=engagement_likes,
            engagement_shares=item.get("repost_count") or item.get("reshare_count") or 0,
            engagement_comments=item.get("comments_count") or 0,
            language="en",
            media_urls=media_urls,
            metadata=metadata,
        )
