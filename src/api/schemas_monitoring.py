"""Monitoring API request/response schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from ..monitoring.alerts.models import AlertEvent, AlertRule, SpikeConfig
from ..monitoring.models import DataSource


class CreateMonitorRequest(BaseModel):
    name: str = Field(max_length=200)
    keywords: str = Field(max_length=512)
    sources: list[DataSource] = Field(min_length=1, max_length=10)
    boolean_query: str | None = Field(None, max_length=1024)
    competitor_brands: list[str] = Field(default_factory=list, max_length=10)


class UpdateMonitorRequest(BaseModel):
    name: str | None = Field(None, max_length=200)
    keywords: str | None = Field(None, max_length=512)
    sources: list[DataSource] | None = Field(None, min_length=1, max_length=10)
    boolean_query: str | None = Field(None, max_length=1024)
    is_active: bool | None = None
    competitor_brands: list[str] | None = Field(
        None, max_length=10, description="Competitor brand names for SOV"
    )


class MonitorResponse(BaseModel):
    id: UUID
    name: str
    keywords: str
    sources: list[DataSource]
    boolean_query: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    competitor_brands: list[str] = []
    mention_count: int | None = None

    @classmethod
    def from_monitor(cls, monitor, mention_count: int | None = None) -> MonitorResponse:
        return cls(
            id=monitor.id,
            name=monitor.name,
            keywords=",".join(monitor.keywords) if isinstance(monitor.keywords, list) else monitor.keywords,
            sources=monitor.sources,
            boolean_query=monitor.boolean_query,
            is_active=monitor.is_active,
            created_at=monitor.created_at,
            updated_at=monitor.updated_at,
            competitor_brands=getattr(monitor, "competitor_brands", []) or [],
            mention_count=mention_count,
        )


class MonitorSummaryResponse(BaseModel):
    """Enriched monitor summary for list view — single SQL, no N+1."""

    id: UUID
    name: str
    keywords: list[str]
    boolean_query: str | None
    sources: list[str]
    competitor_brands: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    next_run_at: datetime | None
    last_run_status: str | None
    last_run_completed_at: datetime | None
    last_run_error: str | None
    alert_count_24h: int
    mention_count: int
    pending_changes_count: int = 0


class MentionResponse(BaseModel):
    id: UUID
    source: DataSource
    source_id: str
    author_name: str | None
    author_handle: str | None
    content: str | None
    url: str | None
    published_at: datetime | None
    sentiment_score: float | None
    sentiment_label: str | None
    intent: str | None
    engagement_total: int | None
    engagement_likes: int | None = None
    engagement_shares: int | None = None
    engagement_comments: int | None = None
    reach_estimate: int | None
    language: str | None
    geo_country: str | None
    media_urls: list[str]
    metadata: dict[str, Any]

    @classmethod
    def from_mention(cls, m) -> MentionResponse:
        return cls(
            id=m.id,
            source=m.source,
            source_id=m.source_id,
            author_name=m.author_name,
            author_handle=m.author_handle,
            content=m.content,
            url=m.url,
            published_at=m.published_at,
            sentiment_score=m.sentiment_score,
            sentiment_label=m.sentiment_label.value if m.sentiment_label else None,
            intent=getattr(m, "intent", None),
            engagement_total=(m.engagement_likes or 0) + (m.engagement_shares or 0) + (m.engagement_comments or 0),
            engagement_likes=m.engagement_likes,
            engagement_shares=m.engagement_shares,
            engagement_comments=m.engagement_comments,
            reach_estimate=m.reach_estimate,
            language=m.language,
            geo_country=m.geo_country,
            media_urls=m.media_urls or [],
            metadata=m.metadata or {},
        )


class MentionSearchResponse(BaseModel):
    mentions: list[MentionResponse]
    total_count: int
    query: str


# ── Alert schemas (PR-068) ──


class CreateAlertRuleRequest(BaseModel):
    rule_type: Literal["mention_spike"] = "mention_spike"
    webhook_url: str = Field(max_length=2048)
    config: SpikeConfig = Field(default_factory=SpikeConfig)
    cooldown_minutes: int = Field(default=60, ge=15, le=1440)


class UpdateAlertRuleRequest(BaseModel):
    webhook_url: str | None = Field(None, max_length=2048)
    config: SpikeConfig | None = None
    is_active: bool | None = None
    cooldown_minutes: int | None = Field(None, ge=15, le=1440)


class AlertRuleResponse(BaseModel):
    id: UUID
    monitor_id: UUID
    rule_type: str
    config: dict[str, Any]
    webhook_url: str
    is_active: bool
    cooldown_minutes: int
    last_triggered_at: datetime | None
    consecutive_failures: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_rule(cls, rule: AlertRule) -> AlertRuleResponse:
        return cls(
            id=rule.id,
            monitor_id=rule.monitor_id,
            rule_type=rule.rule_type,
            config=rule.config,
            webhook_url=rule.webhook_url,
            is_active=rule.is_active,
            cooldown_minutes=rule.cooldown_minutes,
            last_triggered_at=rule.last_triggered_at,
            consecutive_failures=rule.consecutive_failures,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
        )


class AlertEventResponse(BaseModel):
    id: UUID
    rule_id: UUID
    monitor_id: UUID
    triggered_at: datetime
    condition_summary: str
    delivery_status: str
    delivery_attempts: int
    created_at: datetime

    @classmethod
    def from_event(cls, event: AlertEvent) -> AlertEventResponse:
        return cls(
            id=event.id,
            rule_id=event.rule_id,
            monitor_id=event.monitor_id,
            triggered_at=event.triggered_at,
            condition_summary=event.condition_summary,
            delivery_status=event.delivery_status,
            delivery_attempts=event.delivery_attempts,
            created_at=event.created_at,
        )


# ── Intelligence Layer Schemas (PR-071) ──


class SentimentBucketResponse(BaseModel):
    period_start: datetime
    avg_sentiment: float
    mention_count: int
    positive_count: int
    negative_count: int
    neutral_count: int
    mixed_count: int


class SentimentTimeSeriesResponse(BaseModel):
    monitor_id: UUID
    window: str
    granularity: str
    buckets: list[SentimentBucketResponse]


class ClassifyIntentRequest(BaseModel):
    mention_ids: list[UUID] | None = Field(
        None, max_length=100, description="Specific mention IDs to classify"
    )


class ClassifyIntentResponse(BaseModel):
    classified_count: int


class ShareOfVoiceEntryResponse(BaseModel):
    brand: str
    mention_count: int
    percentage: float
    sentiment_avg: float | None


class ShareOfVoiceResponse(BaseModel):
    monitor_id: UUID
    window_days: int
    entries: list[ShareOfVoiceEntryResponse]


class TrendsCorrelationBucketResponse(BaseModel):
    period_start: datetime
    mention_count: int
    google_trends_score: float | None


class TrendsCorrelationResponse(BaseModel):
    monitor_id: UUID
    window_days: int
    keyword: str
    correlation_coefficient: float | None
    buckets: list[TrendsCorrelationBucketResponse]


class SaveToWorkspaceRequest(BaseModel):
    collection_id: UUID
    mention_ids: list[UUID] | None = Field(
        None, max_length=500, description="Specific mentions to save"
    )
    annotations: dict[str, str] | None = Field(
        None, description="Mention ID -> annotation text (max 500 chars each)"
    )


class SaveToWorkspaceResponse(BaseModel):
    saved_count: int
    collection_id: UUID


# ── Weekly Digests (digest agent persistence) ──


class WeeklyDigestCreate(BaseModel):
    week_ending: date
    stories: list[dict[str, Any]] = Field(default_factory=list, max_length=50)
    executive_summary: str = Field("", max_length=10000)
    action_items: list[dict[str, Any]] = Field(default_factory=list, max_length=50)
    iteration_count: int = 0
    avg_story_delta: float | None = None
    digest_markdown: str | None = Field(None, max_length=500000)


class WeeklyDigestResponse(BaseModel):
    id: UUID
    monitor_id: UUID
    week_ending: date
    executive_summary: str
    stories: list[dict[str, Any]]
    action_items: list[dict[str, Any]]
    digest_markdown: str | None = None
    dqs_score: float | None = None
    generated_at: datetime | None = None

    @classmethod
    def from_digest(cls, d) -> WeeklyDigestResponse:
        return cls(
            id=d.id,
            monitor_id=d.monitor_id,
            week_ending=d.week_ending,
            executive_summary=d.executive_summary,
            stories=d.stories,
            action_items=d.action_items,
            digest_markdown=d.digest_markdown,
            dqs_score=d.dqs_score,
            generated_at=d.generated_at,
        )


# ── Changelog (V2 self-optimizing refinement) ──


class ChangelogEntryResponse(BaseModel):
    id: UUID
    monitor_id: UUID
    change_type: str
    change_detail: dict[str, Any]
    rationale: str
    autonomy_level: str
    status: str
    applied_by: str
    analysis_run_id: UUID | None
    created_at: datetime


class ChangelogListResponse(BaseModel):
    entries: list[ChangelogEntryResponse]
    total: int
