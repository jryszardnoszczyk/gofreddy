"""Pod Engine adapter — REST API → mentions with source=PODCAST."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from aiolimiter import AsyncLimiter

from ...common.cost_recorder import cost_recorder as _cost_recorder
from ..config import MonitoringSettings
from ..exceptions import MentionFetchError
from ..fetcher_protocol import BaseMentionFetcher
from ..models import DataSource, RawMention, SentimentLabel
from ._common import parse_date

logger = logging.getLogger(__name__)

MAX_CONTENT_LENGTH = 2000


class PodEngineAdapter(BaseMentionFetcher):
    """Pod Engine REST API → mentions with source=PODCAST."""

    BASE_URL = "https://api.podengine.ai/v1"
    TIMEOUT_SECONDS = 45  # REST API, fast responses

    def __init__(
        self,
        api_key: str,
        *,
        settings: MonitoringSettings | None = None,
    ) -> None:
        super().__init__(settings=settings, timeout_override=self.TIMEOUT_SECONDS)
        self._api_key = api_key
        self._rate_limiter = AsyncLimiter(5, 60)  # 5 requests per minute
        self._http_client: httpx.AsyncClient | None = None

    @property
    def source(self) -> DataSource:
        return DataSource.PODCAST

    async def _do_fetch(
        self,
        query: str,
        *,
        cursor: str | None = None,
        limit: int = 100,
    ) -> tuple[list[RawMention], str | None]:
        if not self._api_key:
            raise MentionFetchError("POD_ENGINE_API_KEY not configured")

        async with self._rate_limiter:
            return await self._fetch_transcripts(query, cursor=cursor, limit=limit)

    async def _fetch_transcripts(
        self,
        query: str,
        *,
        cursor: str | None = None,
        limit: int = 100,
    ) -> tuple[list[RawMention], str | None]:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)

        offset = int(cursor) if cursor else 0
        params: dict[str, Any] = {
            "query": query,
            "limit": min(limit, 50),
            "offset": offset,
        }

        try:
            response = await self._http_client.get(
                f"{self.BASE_URL}/search/transcripts",
                headers={"Authorization": f"Bearer {self._api_key}"},
                params=params,
            )
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            # Transient — let base class retry
            raise RuntimeError(f"Pod Engine connection failed: {e}") from e
        except httpx.HTTPError as e:
            raise MentionFetchError(f"Pod Engine request failed: {e}") from e

        if response.status_code == 401:
            raise MentionFetchError("Invalid POD_ENGINE_API_KEY")
        if response.status_code == 429:
            raise MentionFetchError("Pod Engine rate limit exceeded")
        if response.status_code >= 500:
            # Transient — let base class retry
            raise Exception(f"Pod Engine server error: {response.status_code}")

        response.raise_for_status()
        await _cost_recorder.record("podengine", "search")

        data = response.json()
        results = data.get("results", []) if isinstance(data, dict) else []

        mentions: list[RawMention] = []
        for result in results:
            try:
                mentions.append(self._parse_result(result))
            except Exception:
                logger.warning(
                    "podcast_item_parse_error",
                    extra={"result_id": result.get("id", "unknown") if isinstance(result, dict) else "not_dict"},
                    exc_info=True,
                )

        # Pagination: return next offset cursor if more results
        next_cursor: str | None = None
        if results:
            next_offset = offset + len(results)
            total = data.get("total", 0) if isinstance(data, dict) else 0
            if next_offset < total:
                next_cursor = str(next_offset)

        return (mentions, next_cursor)

    def _parse_result(self, result: dict[str, Any]) -> RawMention:
        """Parse a single Pod Engine transcript result into a RawMention."""
        source_id = str(result.get("episode_id") or result.get("id", ""))

        # Content: transcript segment, NOT full episode — truncate to limit
        content = result.get("matched_text", "") or result.get("text", "")
        if len(content) > MAX_CONTENT_LENGTH:
            content = content[:MAX_CONTENT_LENGTH]

        # Sentiment: use Pod Engine's if provided, else None
        sentiment_score = result.get("sentiment_score")
        sentiment_label = None
        if sentiment_score is not None:
            if sentiment_score > 0.2:
                sentiment_label = SentimentLabel.POSITIVE
            elif sentiment_score < -0.2:
                sentiment_label = SentimentLabel.NEGATIVE
            else:
                sentiment_label = SentimentLabel.NEUTRAL

        return RawMention(
            source=DataSource.PODCAST,
            source_id=source_id,
            content=content,
            author_handle=result.get("show_name"),
            author_name=result.get("host_name"),
            url=result.get("episode_url"),
            published_at=parse_date(result.get("published_date")),
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            metadata={
                "transcript_timestamp": {
                    "start": result.get("start_time"),
                    "end": result.get("end_time"),
                },
                "speaker_id": result.get("speaker"),
                "is_ad_segment": result.get("is_sponsored", False),
                "show_name": result.get("show_name"),
                "episode_title": result.get("episode_title"),
                "episode_duration": result.get("duration_seconds"),
            },
        )

    async def close(self) -> None:
        """Cleanup httpx connection pool."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
