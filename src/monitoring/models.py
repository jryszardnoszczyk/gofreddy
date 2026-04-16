"""Monitoring domain models — DataSource, Monitor, Mention, cursors, and adapter DTO."""

from __future__ import annotations

import enum
import html as _html
import re as _re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any
from uuid import UUID


class DataSource(str, enum.Enum):
    """Monitoring data sources. Threads deferred (API access uncertain)."""

    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    REDDIT = "reddit"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"
    BLUESKY = "bluesky"
    NEWSDATA = "newsdata"
    TRUSTPILOT = "trustpilot"
    APP_STORE = "app_store"
    PLAY_STORE = "play_store"
    GOOGLE_TRENDS = "google_trends"
    PODCAST = "podcast"
    AI_SEARCH = "ai_search"
    # THREADS = "threads"  # Deferred: API access uncertain


# Bridge mapping for PR-072 video-mention integration
_PLATFORM_TO_DATASOURCE: dict[str, DataSource] = {
    "tiktok": DataSource.TIKTOK,
    "instagram": DataSource.INSTAGRAM,
    "youtube": DataSource.YOUTUBE,
}


def platform_to_datasource(platform_value: str) -> DataSource | None:
    """Map a Platform enum value to its DataSource equivalent. Returns None if no mapping."""
    return _PLATFORM_TO_DATASOURCE.get(platform_value)


class SentimentLabel(str, enum.Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class IntentLabel(str, enum.Enum):
    COMPLAINT = "complaint"
    QUESTION = "question"
    RECOMMENDATION = "recommendation"
    PURCHASE_SIGNAL = "purchase_signal"
    GENERAL_DISCUSSION = "general_discussion"


@dataclass(frozen=True, slots=True)
class Monitor:
    """A brand monitoring query configuration."""

    id: UUID
    user_id: UUID
    name: str
    keywords: list[str]
    boolean_query: str | None
    sources: list[DataSource]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    client_id: UUID | None = None
    next_run_at: datetime | None = None
    competitor_brands: list[str] = field(default_factory=list)
    last_user_edit_at: datetime | None = None
    last_analysis_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class MonitorRun:
    """Record of a single monitor execution cycle."""

    id: UUID
    monitor_id: UUID
    started_at: datetime
    completed_at: datetime | None
    status: str  # running | completed | failed
    mentions_ingested: int
    sources_succeeded: int
    sources_failed: int
    error_details: dict[str, Any] | None


@dataclass(frozen=True, slots=True)
class Mention:
    """A single mention from any data source. Immutable after persistence."""

    id: UUID
    monitor_id: UUID
    source: DataSource
    source_id: str
    author_handle: str | None
    author_name: str | None
    content: str
    url: str | None
    published_at: datetime | None
    sentiment_score: float | None  # -1.0 to 1.0
    sentiment_label: SentimentLabel | None
    engagement_likes: int
    engagement_shares: int
    engagement_comments: int
    reach_estimate: int | None
    language: str
    geo_country: str | None  # ISO 3166-1 alpha-2
    media_urls: list[str]
    metadata: dict[str, Any]
    created_at: datetime
    intent: str | None = None
    classified_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class SentimentBucket:
    """One time-series bucket for sentiment aggregation."""

    period_start: datetime
    avg_sentiment: float
    mention_count: int
    positive_count: int
    negative_count: int
    neutral_count: int
    mixed_count: int


@dataclass(frozen=True, slots=True)
class SourceSentiment:
    """Per-source sentiment aggregation for cross-signal anomaly detection."""

    source: DataSource
    avg_sentiment: float
    mention_count: int
    bucket: datetime


@dataclass(frozen=True, slots=True)
class TopicCluster:
    """A topic cluster from daily Gemini clustering."""

    id: UUID
    monitor_id: UUID
    cluster_date: date
    topic_label: str
    mention_count: int
    representative_mentions: list[dict[str, Any]]
    sentiment_avg: float | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class ShareOfVoiceEntry:
    """SOV for one brand in the competitive set."""

    brand: str
    mention_count: int
    percentage: float
    sentiment_avg: float | None


@dataclass(frozen=True, slots=True)
class MonitorChangelog:
    """A single changelog entry from post-ingestion analysis or user action."""

    id: UUID
    monitor_id: UUID
    change_type: str  # noise_exclusion, threshold_calibration, keyword_expansion, source_rebalance, competitor_detected, scope_change
    change_detail: dict[str, Any]  # {"field": "boolean_query", "old_value": "...", "new_value": "..."}
    rationale: str
    autonomy_level: str  # auto, notify, ask
    status: str  # applied, pending, rejected, reverted
    applied_by: str  # 'system' or user_id
    analysis_run_id: UUID | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class Refinement:
    """A proposed refinement from the PostIngestionAnalyzer."""

    change_type: str  # noise_exclusion, threshold_calibration, keyword_expansion, source_rebalance, competitor_detected, scope_change
    field: str  # the monitor field to change (boolean_query, sources, competitor_brands, etc.)
    old_value: Any
    new_value: Any
    rationale: str
    autonomy_level: str  # auto, notify, ask
    confidence: float  # 0.0 to 1.0


@dataclass(frozen=True, slots=True)
class MonitorSourceCursor:
    """Tracks last-fetched position per monitor per source."""

    monitor_id: UUID
    source: DataSource
    cursor_value: str
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class XpozUser:
    """Creator/user from Xpoz SDK — consumed by search_creators tool."""

    platform: DataSource
    user_id: str
    username: str
    display_name: str | None
    bio: str | None
    follower_count: int | None
    following_count: int | None
    post_count: int | None
    is_verified: bool
    profile_image_url: str | None
    # Bot detection (Twitter only — consumed by search_creators bot badge)
    is_inauthentic: bool | None
    inauthentic_prob_score: float | None  # 0.0–1.0
    # Relevance (from keyword search — consumed by search_creators ranking)
    relevance_score: float | None
    relevant_posts_count: int | None
    relevant_engagement_sum: int | None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class XpozComment:
    """Comment from Xpoz SDK — consumed by get_post_comments tool."""

    comment_id: str
    post_id: str
    platform: DataSource
    author_username: str | None
    content: str
    like_count: int
    is_spam: bool | None  # Instagram only
    controversiality: int | None  # Reddit only (binary 0/1)
    is_submitter: bool | None  # Reddit only — OP involvement
    distinguished: str | None  # Reddit only — mod/admin
    depth: int | None  # Reddit only — nesting level
    published_at: datetime | None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class XpozSubreddit:
    """Subreddit from Xpoz SDK — consumed by search_subreddits tool."""

    name: str
    title: str | None
    description: str | None
    subscribers_count: int | None
    active_users_count: int | None
    subreddit_type: str | None  # public/private/archived
    over18: bool
    language: str | None
    url: str | None
    relevance_score: float | None
    relevant_posts_count: int | None
    metadata: dict[str, Any] = field(default_factory=dict)


def _clean_text(text: str) -> str:
    """Sanitize adapter text: decode HTML entities, unescape literal \\n, strip broken surrogates."""
    if not text:
        return text
    # 1. Decode HTML entities (loop handles double-encoding: &amp;amp; → &amp; → &)
    prev = None
    while prev != text:
        prev = text
        text = _html.unescape(text)
    # 2. Unescape literal \n, \t, \" (some APIs return escaped chars as text)
    text = text.replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"')
    # 3. Strip U+FFFD replacement characters (broken surrogate pairs from SDK)
    text = text.replace("\ufffd", "")
    # 4. Collapse runs of blank lines left by stripped chars (3+ newlines → 2)
    text = _re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


@dataclass(slots=True)
class RawMention:
    """Adapter-produced DTO before persistence. Mutable for enrichment."""

    source: DataSource
    source_id: str
    author_handle: str | None = None
    author_name: str | None = None
    content: str = ""
    url: str | None = None
    published_at: datetime | None = None
    sentiment_score: float | None = None
    sentiment_label: SentimentLabel | None = None
    engagement_likes: int = 0
    engagement_shares: int = 0
    engagement_comments: int = 0
    reach_estimate: int | None = None
    language: str = "en"
    geo_country: str | None = None
    media_urls: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Sanitize text fields on construction — every adapter benefits automatically.
        if self.content:
            self.content = _clean_text(self.content)
        if self.author_name:
            self.author_name = _clean_text(self.author_name)


@dataclass(frozen=True, slots=True)
class DigestStory:
    """A weekly story aggregated from daily TopicClusters. Does NOT extend TopicCluster."""

    story_label: str
    daily_clusters: list[UUID]  # TopicCluster IDs (not objects)
    mention_ids: list[UUID]
    total_mention_count: int
    days_active: int
    significance_score: float
    sentiment_trajectory: list[float]  # daily avg sentiment
    sources: list[str]
    linked_alerts: list[UUID]


@dataclass(frozen=True, slots=True)
class WeeklyDigestRecord:
    """Persisted weekly digest metadata."""

    id: UUID
    monitor_id: UUID
    client_id: UUID | None
    week_ending: date
    stories: list[dict[str, Any]]  # serialized DigestStory
    executive_summary: str
    action_items: list[dict[str, Any]]
    dqs_score: float | None
    iteration_count: int
    avg_story_delta: float | None
    generated_at: datetime
    digest_markdown: str | None = None


@dataclass(frozen=True, slots=True)
class DiscoverSourceError:
    source: str
    reason: str  # "timeout" | "circuit_breaker" | error message (truncated to 200 chars)


@dataclass(frozen=True, slots=True)
class DiscoverResult:
    mentions: list[RawMention]
    sources_searched: list[str]
    sources_failed: list[DiscoverSourceError]
    sources_unavailable: list[str]
