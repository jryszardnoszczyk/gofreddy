"""PostgreSQL repository for content articles and performance snapshots."""

from __future__ import annotations

import json
import logging
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

import asyncpg

from .article_models import (
    ArticlePerformanceSnapshot,
    ArticlePerformanceSummary,
    ContentArticle,
)

logger = logging.getLogger(__name__)


class PostgresArticleRepository:
    """PostgreSQL repository for content articles and performance tracking."""

    ACQUIRE_TIMEOUT = 5.0

    _INSERT_ARTICLE = """
        INSERT INTO content_articles (
            org_id, client_id, title, slug, article_result, article_md,
            word_count, generation_cost_usd, site_link_graph_snapshot,
            generation_model
        ) VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8, $9::jsonb, $10)
        RETURNING *
    """

    _SELECT_ARTICLE = """
        SELECT * FROM content_articles WHERE id = $1 AND org_id = $2
    """

    _LIST_ARTICLES = """
        SELECT * FROM content_articles
        WHERE org_id = $1
        ORDER BY created_at DESC
        LIMIT $2 OFFSET $3
    """

    _UPDATE_PUBLISHED_URL = """
        UPDATE content_articles
        SET published_url = $1, canonical_url = $2
        WHERE id = $3 AND org_id = $4
    """

    _LIST_PUBLISHED_URLS = """
        SELECT id, published_url FROM content_articles
        WHERE org_id = $1 AND published_url IS NOT NULL
    """

    _UPSERT_SNAPSHOT = """
        INSERT INTO article_performance_snapshots (
            article_id, snapshot_date, clicks, impressions, ctr, position
        ) VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (article_id, snapshot_date)
        DO UPDATE SET
            clicks = EXCLUDED.clicks,
            impressions = EXCLUDED.impressions,
            ctr = EXCLUDED.ctr,
            position = EXCLUDED.position
    """

    _SELECT_PERFORMANCE_HISTORY = """
        SELECT * FROM article_performance_snapshots
        WHERE article_id = $1
          AND snapshot_date >= CURRENT_DATE - ($2 || ' days')::interval
        ORDER BY snapshot_date DESC
    """

    _SELECT_PERFORMANCE_SUMMARY = """
        SELECT
            COALESCE(SUM(clicks), 0) AS total_clicks,
            COALESCE(SUM(impressions), 0) AS total_impressions,
            COALESCE(AVG(ctr), 0) AS avg_ctr,
            COALESCE(AVG(position), 0) AS avg_position,
            COUNT(*) AS days_tracked
        FROM article_performance_snapshots
        WHERE article_id = $1
    """

    _SELECT_POSITION_TREND = """
        SELECT position FROM article_performance_snapshots
        WHERE article_id = $1
        ORDER BY snapshot_date DESC
        LIMIT 7
    """

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    def _article_from_row(self, row: asyncpg.Record) -> ContentArticle:
        return ContentArticle(
            id=row["id"],
            org_id=row["org_id"],
            client_id=row["client_id"],
            title=row["title"],
            slug=row["slug"],
            article_result=json.loads(row["article_result"]) if isinstance(row["article_result"], str) else row["article_result"],
            article_md=row["article_md"],
            published_url=row["published_url"],
            canonical_url=row["canonical_url"],
            word_count=row["word_count"],
            generation_cost_usd=row["generation_cost_usd"],
            site_link_graph_snapshot=(
                json.loads(row["site_link_graph_snapshot"])
                if isinstance(row["site_link_graph_snapshot"], str)
                else row["site_link_graph_snapshot"]
            ),
            generation_model=row["generation_model"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def create_article(
        self,
        org_id: UUID,
        title: str,
        article_result: dict[str, Any],
        *,
        client_id: UUID | None = None,
        slug: str | None = None,
        article_md: str | None = None,
        word_count: int = 0,
        generation_cost_usd: Decimal = Decimal("0"),
        site_link_graph_snapshot: dict[str, Any] | None = None,
        generation_model: str = "gemini-2.0-flash",
    ) -> ContentArticle:
        row = await self._pool.fetchrow(
            self._INSERT_ARTICLE,
            org_id,
            client_id,
            title,
            slug,
            json.dumps(article_result),
            article_md,
            word_count,
            generation_cost_usd,
            json.dumps(site_link_graph_snapshot) if site_link_graph_snapshot else None,
            generation_model,
        )
        return self._article_from_row(row)

    async def get_article(self, article_id: UUID, org_id: UUID) -> ContentArticle | None:
        row = await self._pool.fetchrow(self._SELECT_ARTICLE, article_id, org_id)
        return self._article_from_row(row) if row else None

    async def list_articles(
        self, org_id: UUID, *, limit: int = 20, offset: int = 0
    ) -> list[ContentArticle]:
        rows = await self._pool.fetch(self._LIST_ARTICLES, org_id, limit, offset)
        return [self._article_from_row(r) for r in rows]

    async def update_published_url(
        self,
        article_id: UUID,
        org_id: UUID,
        published_url: str,
        canonical_url: str | None = None,
    ) -> None:
        await self._pool.execute(
            self._UPDATE_PUBLISHED_URL,
            published_url,
            canonical_url,
            article_id,
            org_id,
        )

    async def list_published_urls(self, org_id: UUID) -> list[tuple[UUID, str]]:
        rows = await self._pool.fetch(self._LIST_PUBLISHED_URLS, org_id)
        return [(row["id"], row["published_url"]) for row in rows]

    async def upsert_performance_snapshot(
        self,
        article_id: UUID,
        snapshot_date: date,
        clicks: int,
        impressions: int,
        ctr: Decimal,
        position: Decimal,
    ) -> None:
        await self._pool.execute(
            self._UPSERT_SNAPSHOT,
            article_id, snapshot_date, clicks, impressions, ctr, position,
        )

    async def get_performance_history(
        self, article_id: UUID, *, days: int = 30
    ) -> list[ArticlePerformanceSnapshot]:
        rows = await self._pool.fetch(
            self._SELECT_PERFORMANCE_HISTORY, article_id, str(days)
        )
        return [
            ArticlePerformanceSnapshot(
                id=r["id"],
                article_id=r["article_id"],
                snapshot_date=r["snapshot_date"],
                clicks=r["clicks"],
                impressions=r["impressions"],
                ctr=r["ctr"],
                position=r["position"],
                created_at=r["created_at"],
            )
            for r in rows
        ]

    async def get_performance_summary(self, article_id: UUID) -> ArticlePerformanceSummary:
        row = await self._pool.fetchrow(self._SELECT_PERFORMANCE_SUMMARY, article_id)
        trend_rows = await self._pool.fetch(self._SELECT_POSITION_TREND, article_id)

        trend = "stable"
        if len(trend_rows) >= 3:
            recent = float(trend_rows[0]["position"])
            older = float(trend_rows[-1]["position"])
            if recent < older - 1:
                trend = "improving"
            elif recent > older + 1:
                trend = "declining"

        return ArticlePerformanceSummary(
            total_clicks=row["total_clicks"],
            total_impressions=row["total_impressions"],
            avg_ctr=float(row["avg_ctr"]),
            avg_position=float(row["avg_position"]),
            position_trend=trend,
            days_tracked=row["days_tracked"],
        )
