"""Article performance tracking models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ContentArticle(BaseModel):
    """Generated article stored in content_articles table."""

    model_config = ConfigDict(frozen=True)

    id: UUID
    org_id: UUID
    client_id: UUID | None = None
    title: str
    slug: str | None = None
    article_result: dict[str, Any]
    article_md: str | None = None
    published_url: str | None = None
    canonical_url: str | None = None
    word_count: int = 0
    generation_cost_usd: Decimal = Decimal("0")
    site_link_graph_snapshot: dict[str, Any] | None = None
    generation_model: str = "gemini-2.0-flash"
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ArticlePerformanceSnapshot(BaseModel):
    """Daily GSC performance snapshot for a published article."""

    model_config = ConfigDict(frozen=True)

    id: UUID
    article_id: UUID
    snapshot_date: date
    clicks: int = 0
    impressions: int = 0
    ctr: Decimal = Decimal("0")
    position: Decimal = Decimal("0")
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ArticlePerformanceSummary:
    """Aggregated performance metrics for an article."""

    total_clicks: int
    total_impressions: int
    avg_ctr: float
    avg_position: float
    position_trend: str  # improving / stable / declining
    days_tracked: int
