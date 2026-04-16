"""AI Search monitoring adapter — tracks brand visibility across AI platforms.

Queries ChatGPT, Perplexity, Gemini, Grok, etc. via Cloro API.
Maps one RawMention per citation (not per engine response).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Self

from ...common.cost_recorder import cost_recorder as _cost_recorder
from ...geo.providers.cloro import (
    CLORO_COST_PER_QUERY,
    CloroClient,
    QueryRequest,
)
from ..config import MonitoringSettings
from ..exceptions import MentionFetchError
from ..fetcher_protocol import BaseMentionFetcher
from ..models import DataSource, RawMention

logger = logging.getLogger(__name__)


class AiSearchAdapter(BaseMentionFetcher):
    """AI Search monitoring adapter via Cloro API.

    Queries multiple AI platforms and maps each citation to a RawMention.
    No cursor pagination — returns (mentions, None).
    """

    DEFAULT_PLATFORMS = ("chatgpt", "perplexity", "gemini")

    def __init__(
        self,
        settings: MonitoringSettings | None = None,
        cloro_api_key: str = "",
    ) -> None:
        super().__init__(settings)
        self._api_key = cloro_api_key
        self._client: CloroClient | None = None

    @property
    def source(self) -> DataSource:
        return DataSource.AI_SEARCH

    async def __aenter__(self) -> Self:
        if self._api_key:
            self._client = CloroClient(
                api_key=self._api_key,
                timeout=60.0,
            )
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            await self._client.close()
            self._client = None

    async def _do_fetch(
        self,
        query: str,
        *,
        cursor: str | None = None,
        limit: int = 100,
    ) -> tuple[list[RawMention], str | None]:
        """Query Cloro and map citations to RawMentions.

        Each citation from any AI platform becomes one RawMention.
        Returns (mentions, None) — no cursor pagination.
        """
        if not self._client:
            raise MentionFetchError("AI search adapter not initialized — missing Cloro API key")

        if not self._client.is_available:
            raise MentionFetchError("AI search circuit breaker open")

        request = QueryRequest(
            prompt=query,
            platforms=list(self.DEFAULT_PLATFORMS),
        )

        result = await self._client.query(request)

        # Map citations to RawMentions — one mention per citation
        mentions: list[RawMention] = []
        now = datetime.now(timezone.utc)

        for platform, response in result.results.items():
            for i, citation in enumerate(response.citations):
                source_id = f"{platform}:{citation.url}"
                mentions.append(RawMention(
                    source=DataSource.AI_SEARCH,
                    source_id=source_id,
                    author_handle=platform,
                    author_name=f"AI: {platform.title()}",
                    content=f"Cited in {platform} response: {citation.title or citation.url}",
                    url=citation.url,
                    published_at=now,
                    metadata={
                        "ai_platform": platform,
                        "citation_index": i,
                        "citation_title": citation.title,
                        "citation_source": citation.source,
                        "response_text_preview": response.text[:200] if response.text else "",
                    },
                ))

        # Log errors for failed platforms
        for platform, error in result.errors.items():
            logger.warning(
                "ai_search_platform_error",
                extra={"platform": platform, "error": error},
            )

        # Cost is recorded per-platform by CloroClient._make_request()
        # No additional recording needed here

        return mentions, None  # No cursor pagination
