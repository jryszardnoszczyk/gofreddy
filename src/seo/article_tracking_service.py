"""Article performance tracking via Google Search Console polling."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from .article_repository import PostgresArticleRepository
from .providers.gsc import GSCClient

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PollResult:
    """Result of a GSC polling run."""

    articles_tracked: int
    snapshots_upserted: int
    errors: list[str]


class ArticleTrackingService:
    """Polls GSC for published article performance and upserts snapshots."""

    def __init__(
        self,
        gsc_client: GSCClient,
        article_repo: PostgresArticleRepository,
    ) -> None:
        self._gsc = gsc_client
        self._repo = article_repo

    async def poll_all_articles(self, org_id: UUID, site_url: str) -> PollResult:
        """Poll GSC for all published articles belonging to an org.

        Uses a 7-day rolling window ending 2 days ago (GSC data lag).
        """
        published = await self._repo.list_published_urls(org_id)
        if not published:
            return PollResult(articles_tracked=0, snapshots_upserted=0, errors=[])

        end_date = date.today() - timedelta(days=2)
        start_date = end_date - timedelta(days=6)
        urls = [url for _, url in published]
        url_to_article_id = {url: aid for aid, url in published}

        errors: list[str] = []
        snapshots_upserted = 0

        try:
            result = await self._gsc.get_search_analytics(
                site_url, start_date, end_date, pages=urls
            )
        except Exception as exc:
            logger.error("GSC polling failed for org %s: %s", org_id, exc)
            return PollResult(
                articles_tracked=len(published),
                snapshots_upserted=0,
                errors=[f"GSC API error: {exc}"],
            )

        for row in result.rows:
            article_id = url_to_article_id.get(row.page)
            if not article_id:
                continue
            try:
                await self._repo.upsert_performance_snapshot(
                    article_id=article_id,
                    snapshot_date=end_date,
                    clicks=int(row.clicks),
                    impressions=int(row.impressions),
                    ctr=Decimal(str(row.ctr)),
                    position=Decimal(str(row.position)),
                )
                snapshots_upserted += 1
            except Exception as exc:
                errors.append(f"Upsert failed for article {article_id}: {exc}")
                logger.error("Snapshot upsert failed: %s", exc)

        return PollResult(
            articles_tracked=len(published),
            snapshots_upserted=snapshots_upserted,
            errors=errors,
        )
