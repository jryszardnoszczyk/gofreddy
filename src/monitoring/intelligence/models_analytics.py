"""Domain models for own-account analytics and engagement prediction."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class AccountPost:
    """Row from account_posts table."""

    id: UUID
    org_id: UUID
    platform: str
    username: str
    source_id: str
    content: str
    published_at: datetime | None
    likes: int
    shares: int
    comments: int
    impressions: int
    engagement_rate: float | None
    media_type: str | None
    hashtags: list[str]
    metadata: dict[str, Any]
    created_at: datetime


@dataclass(frozen=True, slots=True)
class AccountSnapshot:
    """Row from account_snapshots table."""

    id: UUID
    org_id: UUID
    platform: str
    username: str
    follower_count: int | None
    following_count: int | None
    post_count: int | None
    engagement_rate: float | None
    audience_data: dict[str, Any]
    created_at: datetime


@dataclass(frozen=True, slots=True)
class PerformancePatterns:
    """Deterministic computation from account_posts. Separate from CommodityBaseline."""

    avg_engagement_rate: float
    top_posts: list[dict[str, Any]]
    worst_posts: list[dict[str, Any]]
    content_type_breakdown: dict[str, int]
    best_posting_hours: list[int]
    best_posting_days: list[int]
    follower_growth: float | None
    engagement_trend: Literal["improving", "declining", "stable"]
    engagement_spikes: list[dict[str, Any]]
    velocity_flags: list[str]
    date_gaps: list[str]
    posting_frequency: float
    avg_post_length: float
    engagement_by_length_bucket: dict[str, float]
    total_posts: int
    period_start: date
    period_end: date
    markdown: str


@dataclass(frozen=True, slots=True)
class EngagementPrediction:
    """Result of predict_engagement()."""

    likely_performance: Literal["strong", "average", "weak"]
    confidence: Literal["high", "medium", "low"]
    contributing_factors: list[str]
    comparison_baseline: Literal["personal_20+", "personal_<20", "platform_defaults"]
