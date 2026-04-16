"""Google Trends adapter — Apify google-trends-scraper → mentions."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from apify_client import ApifyClientAsync

from ..config import MonitoringSettings
from ..exceptions import MentionFetchError
from ..fetcher_protocol import BaseMentionFetcher
from ..models import DataSource, RawMention
from ._common import build_apify_client, parse_apify_items, parse_date

logger = logging.getLogger(__name__)


class GoogleTrendsAdapter(BaseMentionFetcher):
    """Apify google-trends-scraper → mentions with source=GOOGLE_TRENDS."""

    ACTOR_ID = "apify/google-trends-scraper"
    TIMEOUT_SECONDS = 150  # Trends scraper needs ~120s; 150s buffer

    def __init__(
        self,
        apify_token: str,
        *,
        settings: MonitoringSettings | None = None,
    ) -> None:
        super().__init__(settings=settings, timeout_override=self.TIMEOUT_SECONDS)
        self._token = apify_token
        self._client: ApifyClientAsync | None = None

    @property
    def source(self) -> DataSource:
        return DataSource.GOOGLE_TRENDS

    async def _do_fetch(
        self,
        query: str,
        *,
        cursor: str | None = None,
        limit: int = 100,
    ) -> tuple[list[RawMention], str | None]:
        if not self._token:
            raise MentionFetchError("APIFY_TOKEN not configured for Google Trends")

        if self._client is None:
            self._client = build_apify_client(self._token)

        search_terms = [t.strip() for t in query.split(",") if t.strip()]
        if not search_terms:
            return ([], None)

        run_input: dict[str, Any] = {
            "searchTerms": search_terms,
            "timeRange": cursor or "past 7 days",
            "geo": "",
            "maxItems": limit,
        }

        try:
            run = await self._client.actor(self.ACTOR_ID).call(
                run_input=run_input,
                timeout_secs=120,
            )
        except Exception as e:
            err_str = str(e).lower()
            if "404" in err_str or "not found" in err_str:
                raise MentionFetchError(f"Google Trends actor not found: {e}") from e
            raise  # Transient — base class retries

        items = await parse_apify_items(run, self._client)
        mentions: list[RawMention] = []

        for item in items:
            try:
                mention = self._parse_item(item)
                mentions.append(mention)
            except Exception:
                logger.warning(
                    "google_trends_item_parse_error",
                    extra={"item_keys": list(item.keys()) if isinstance(item, dict) else "not_dict"},
                    exc_info=True,
                )

        return (mentions, None)  # No pagination for trends

    def _parse_item(self, item: dict[str, Any]) -> RawMention:
        """Parse a single Apify trends item into a RawMention."""
        search_term = item.get("searchTerm", "")

        # Deterministic source_id for dedup
        date_str = item.get("date") or datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
        geo = item.get("geo", "WW")
        source_id = f"{search_term}:{date_str}:{geo}"

        # Parse published_at
        published_at = parse_date(item.get("date"), fallback_to_now=True)

        # Parse interest value — can be int or string like ">5000%"
        raw_value = item.get("value", 0)
        interest_score = _parse_interest_value(raw_value)

        # Related queries and topics
        related_queries = item.get("relatedQueries", {})
        related_topics = item.get("relatedTopics", {})
        geo_data = item.get("interestByRegion", [])

        # Detect breakout
        breakout_raw = str(raw_value) if raw_value else None
        is_breakout = breakout_raw is not None and (
            ">5000%" in breakout_raw or "Breakout" in breakout_raw
        )

        return RawMention(
            source=DataSource.GOOGLE_TRENDS,
            source_id=source_id,
            content=search_term,
            published_at=published_at,
            sentiment_score=None,  # Trends are not sentiment data
            sentiment_label=None,
            metadata={
                "interest_score": interest_score,
                "related_queries": related_queries,
                "related_topics": related_topics,
                "geo_data": geo_data,
                "breakout": is_breakout,
                "breakout_raw": breakout_raw,
            },
        )

    async def close(self) -> None:
        """Cleanup Apify client connection pool."""
        self._client = None


def _parse_interest_value(raw: Any) -> int:
    """Parse Google Trends interest value. Handles ints and breakout strings."""
    if isinstance(raw, int):
        return raw
    if isinstance(raw, float):
        return int(raw)
    if isinstance(raw, str):
        # Strip % and comparison operators
        cleaned = raw.replace("%", "").replace(">", "").replace(",", "").strip()
        try:
            return int(cleaned)
        except ValueError:
            return 0
    return 0
