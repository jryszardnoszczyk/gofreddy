"""NewsData.io REST adapter — news monitoring with sentiment + AI tags."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Self

import httpx

from ...common.cost_recorder import NEWSDATA_COST_PER_REQUEST, cost_recorder as _cost_recorder
from ..config import MonitoringSettings
from ..exceptions import MentionFetchError
from ..fetcher_protocol import BaseMentionFetcher
from ..models import DataSource, RawMention, SentimentLabel

logger = logging.getLogger(__name__)


class _NewsDataBadRequest(Exception):
    """Sentinel for 422 bad request — caught in _do_fetch to return ([], None)."""


def _first_or_none(val: Any) -> str | None:
    """Extract first item from list or return string as-is."""
    if isinstance(val, list) and val:
        return str(val[0])
    if isinstance(val, str):
        return val
    return None


def _join_text(*parts: str | None) -> str:
    """Join non-None text parts with newlines."""
    return "\n\n".join(p for p in parts if p)


def _parse_datetime(val: str | None) -> datetime | None:
    if not val:
        return None
    try:
        return datetime.fromisoformat(val.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


class NewsDataAdapter(BaseMentionFetcher):
    """NewsData.io REST adapter — news monitoring with sentiment + AI tags.

    Auth: API key passed as `apikey` query parameter (not a header).
    Log safety: httpx debug logs include query params — ensure logger level
    is WARNING+ in production to prevent key leakage.
    """

    BASE_URL = "https://newsdata.io/api/1"

    def __init__(self, settings: MonitoringSettings | None = None) -> None:
        super().__init__(settings)
        self._api_key = self._settings.newsdata_api_key.get_secret_value()
        self._client: httpx.AsyncClient | None = None

    @property
    def source(self) -> DataSource:
        return DataSource.NEWSDATA

    async def __aenter__(self) -> Self:
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=httpx.Timeout(connect=5.0, read=25.0, write=5.0, pool=5.0),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            try:
                await self._client.aclose()
            except RuntimeError:
                pass  # Event loop closed during test teardown
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

        params: dict[str, str | int] = {
            "apikey": self._api_key,
            "q": query,
            "language": "en",
            "removeduplicate": 1,
            "size": min(limit, 10),  # NewsData free plan max is 10 per page
        }
        if cursor:
            params["page"] = cursor

        response = await self._client.get("/latest", params=params)
        try:
            self._check_response(response)
        except _NewsDataBadRequest:
            return [], None

        data = response.json()
        await _cost_recorder.record("newsdata", "search", cost_usd=NEWSDATA_COST_PER_REQUEST)
        mentions = [self._map_article(article) for article in (data.get("results") or [])]
        next_cursor = data.get("nextPage")  # None when exhausted
        return mentions, next_cursor

    def _check_response(self, response: httpx.Response) -> None:
        if response.status_code == 401:
            raise MentionFetchError("NewsData.io: invalid API key")
        if response.status_code == 422:
            logger.warning("newsdata_bad_request", extra={"body": response.text[:200]})
            raise _NewsDataBadRequest()
        # 429 and 5xx: let raise_for_status() throw httpx.HTTPStatusError
        # which BaseMentionFetcher retries (it only skips MentionFetchError)
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After", "unknown")
            logger.warning("newsdata_rate_limit", extra={"retry_after": retry_after})
        response.raise_for_status()

    def _map_article(self, article: dict[str, Any]) -> RawMention:
        # Sentiment mapping (free plan returns strings instead of dicts)
        sentiment_label = None
        raw_sentiment = article.get("sentiment")
        if raw_sentiment in ("positive", "negative", "neutral"):
            sentiment_label = SentimentLabel(raw_sentiment)

        sentiment_stats = article.get("sentiment_stats")
        sentiment_score = self._compute_sentiment_score(sentiment_stats) if isinstance(sentiment_stats, dict) else None

        # Media URLs
        media_urls = []
        if article.get("image_url"):
            media_urls.append(article["image_url"])
        if article.get("video_url"):
            media_urls.append(article["video_url"])

        # Metadata bucket for AI enrichment + provider extras
        # Free plan returns "ONLY AVAILABLE IN..." strings — skip those
        metadata: dict[str, Any] = {}
        for key in ("ai_tag", "ai_org", "ai_region", "ai_summary"):
            val = article.get(key)
            if val and isinstance(val, (list, dict)):
                metadata[key] = val
        if article.get("source_id"):
            metadata["source_name"] = article["source_id"]
        if article.get("source_url"):
            metadata["source_url"] = article["source_url"]
        if article.get("source_icon"):
            metadata["source_icon"] = article["source_icon"]
        if article.get("source_priority"):
            metadata["source_priority"] = article["source_priority"]
        if article.get("keywords"):
            metadata["hashtags"] = article["keywords"]
        if article.get("category"):
            cat = article["category"]
            metadata.setdefault("ai_tags", []).extend(
                cat if isinstance(cat, list) else [cat]
            )
        if article.get("duplicate"):
            metadata["is_duplicate"] = article["duplicate"]
        if article.get("datatype"):
            metadata["content_type"] = article["datatype"]

        return RawMention(
            source=DataSource.NEWSDATA,
            source_id=article.get("article_id", ""),
            author_handle=None,
            author_name=_first_or_none(article.get("creator")),
            content=_join_text(
                article.get("title"), article.get("description"), article.get("content")
            ),
            url=article.get("link"),
            published_at=_parse_datetime(article.get("pubDate")),
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            language=article.get("language", "en"),
            geo_country=_first_or_none(article.get("country")),
            media_urls=media_urls,
            metadata=metadata,
        )

    @staticmethod
    def _compute_sentiment_score(stats: dict[str, float]) -> float | None:
        pos = stats.get("positive", 0.0)
        neg = stats.get("negative", 0.0)
        if not pos and not neg:
            return None
        return round(pos - neg, 4)  # Range: -1.0 to 1.0
