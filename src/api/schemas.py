"""API request/response schemas."""

from datetime import datetime
from enum import Enum, StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from ..common.enums import Platform


# ─── Library (Analysis Library page) ─────────────────────────────────────────


class ContentRiskLevel(StrEnum):
    SAFE = "safe"
    RISKY = "risky"
    CRITICAL = "critical"


class LibraryItemResponse(BaseModel):
    """Single item in library listing."""

    id: UUID
    video_id: UUID
    title: str | None
    platform: str
    risk_level: ContentRiskLevel
    analyzed_at: datetime
    has_brands: bool
    has_demographics: bool
    has_deepfake: bool
    has_creative: bool
    has_fraud: bool


class LibraryListResponse(BaseModel):
    """Paginated library listing."""

    items: list[LibraryItemResponse]
    has_more: bool
    next_cursor: str | None  # base64-encoded "{analyzed_at_iso}|{uuid}"


class CreatorGroupResponse(BaseModel):
    """A creator with aggregated analysis stats."""

    creator_id: UUID
    platform: str
    username: str
    video_count: int
    last_analyzed_at: datetime


class CreatorGroupListResponse(BaseModel):
    """List of creator groups."""

    groups: list[CreatorGroupResponse]


class SessionGroupResponse(BaseModel):
    """A conversation with analysis item counts."""

    conversation_id: UUID
    title: str | None
    item_count: int
    last_updated_at: datetime


class SessionGroupListResponse(BaseModel):
    """List of session groups."""

    groups: list[SessionGroupResponse]


def compute_risk_level(
    overall_safe: bool, moderation_flags: list[dict]
) -> ContentRiskLevel:
    """Map analysis safety to display risk level.

    Safe: overall_safe=True
    Critical: overall_safe=False AND highest moderation severity is high/critical
    Risky: overall_safe=False otherwise
    """
    if overall_safe:
        return ContentRiskLevel.SAFE
    high_severities = {"high", "critical"}
    for flag in moderation_flags:
        severity = flag.get("severity", "")
        if isinstance(severity, dict):
            severity = severity.get("value", "")
        if str(severity).lower() in high_severities:
            return ContentRiskLevel.CRITICAL
    return ContentRiskLevel.RISKY

# ─── Evidence Timeline Response (PR-039) ─────────────────────────────────────


class TimelineFinding(BaseModel):
    """A single finding at a specific point in the timeline."""

    type: Literal["moderation", "risk", "brand"]
    category: str
    severity: str | None = None
    confidence: float
    evidence: str
    timestamp_end_seconds: int | None = None
    brand_name: str | None = None
    sentiment: str | None = None


class TimelineGroup(BaseModel):
    """Group of co-located findings at the same timestamp second."""

    timestamp_seconds: int
    findings: list[TimelineFinding]


class EvidenceTimelineResponse(BaseModel):
    """Complete evidence timeline for a video analysis."""

    analysis_id: UUID
    playback_url: str | None = None
    timeline: list[TimelineGroup]
    unanchored_findings: list[TimelineFinding]
    excluded_sources: list[str] = Field(default_factory=list)


# ─── Analysis Requests ───────────────────────────────────────────────────────


class AnalysisTier(str, Enum):
    """Tier of processing speed vs cost."""

    STANDARD = "standard"  # Fast, real-time Gemini API (default)
    BATCH = "batch"        # Slow, 24h turnaround, 50% cost

class AnalyzeVideosRequest(BaseModel):
    """Request to analyze specific video URLs."""

    urls: list[str] = Field(
        ..., min_length=1, max_length=50, description="Video URLs to analyze"
    )
    tier: AnalysisTier = Field(
        default=AnalysisTier.STANDARD,
        description="The processing tier. Batch is 50% cheaper but takes up to 24 hours.",
    )

    @field_validator("urls")
    @classmethod
    def validate_urls(cls, v: list[str]) -> list[str]:
        for url in v:
            if not url.startswith(("https://", "http://")):
                raise ValueError(f"Invalid URL format: {url}")
        return v


class AnalyzeCreatorRequest(BaseModel):
    """Request to analyze a creator's recent videos."""

    platform: Platform
    username: str = Field(
        ..., min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9._-]+$"
    )
    limit: int = Field(default=20, ge=1, le=100, description="Max videos to analyze")
    force_refresh: bool = Field(default=False, description="Bypass cache")


# ─── Content Categorization Response (PR-009) ─────────────────────────────────


class ContentCategoryResponse(BaseModel):
    """Content category in API response."""

    vertical: str
    sub_category: str
    confidence: float
    is_primary: bool


# ─── Moderation Response (PR-009) ─────────────────────────────────────────────


class ModerationFlagResponse(BaseModel):
    """Moderation flag in API response."""

    moderation_class: str
    severity: str
    confidence: float
    timestamp_start: str | None = None
    timestamp_end: str | None = None
    description: str
    evidence: str


# ─── Legacy Risk Response (Track B Tightening) ───────────────────────────────


class RiskDetectionResponse(BaseModel):
    """A typed legacy risk item in API responses.

    `risk_type` is the canonical field.
    `category` is kept as a deprecated mirror for compatibility.
    """

    risk_type: str = Field(description="Canonical risk type identifier.")
    category: str = Field(
        description="Deprecated compatibility mirror of risk_type.",
        deprecated=True,
    )
    severity: str
    confidence: float = Field(ge=0.0, le=1.0, description="Detection confidence (0-1).")
    timestamp_start: str | None = None
    timestamp_end: str | None = None
    description: str
    evidence: str


# ─── Sponsored Content Response (PR-009) ──────────────────────────────────────


class SponsoredContentResponse(BaseModel):
    """Sponsored content in API response."""

    is_sponsored: bool
    confidence: float
    disclosure_detected: bool
    disclosure_clarity_score: float | None = None  # Informational only, not legal
    signals: list[str]
    brands_detected: list[str]
    # Compliance fields (nullable for backward compat with old cached analyses)
    disclosure_placement: Literal["first_3_seconds", "middle", "end", "absent"] | None = None
    disclosure_visibility: Literal["verbal", "text_overlay", "hashtag_only", "none"] | None = None
    disclosure_before_product: bool | None = None
    placement_score: float | None = None
    visibility_score: float | None = None
    timing_score: float | None = None
    compliance_grade: Literal["A", "B", "C", "D", "F"] | None = None
    improvement_suggestions: list[str] = Field(default_factory=list)
    jurisdiction: str = "US"
    disclaimer: str = Field(
        default="Informational assessment only. Not legal or regulatory advice. "
        "Not a determination of FTC compliance.",
        description="Legal disclaimer. Always present in compliance responses.",
    )


# ─── Analysis Responses ──────────────────────────────────────────────────────


class VideoAnalysisResult(BaseModel):
    """Single video analysis result."""

    video_id: str
    platform: Platform
    analysis_id: UUID | None = None
    overall_safe: bool
    overall_confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Model confidence in the overall assessment (0-1).",
    )
    risks_detected: list[RiskDetectionResponse]
    summary: str
    analyzed_at: datetime
    cached: bool
    cost_usd: float

    # NEW: Content Categorization (PR-009)
    content_categories: list[ContentCategoryResponse] = Field(default_factory=list)

    # NEW: Moderation Flags (PR-009)
    moderation_flags: list[ModerationFlagResponse] = Field(default_factory=list)

    # NEW: Sponsored Content (PR-009)
    sponsored_content: SponsoredContentResponse | None = None


class AnalyzeVideosResponse(BaseModel):
    """Response for video analysis request."""

    results: list[VideoAnalysisResult]
    errors: list[dict] = Field(default_factory=list)
    success_rate: float


class AnalyzeCreatorResponse(BaseModel):
    """Response for creator analysis request."""

    creator_username: str
    platform: Platform
    videos_analyzed: int
    results: list[VideoAnalysisResult]
    errors: list[dict] = Field(default_factory=list)
    aggregate_risk_score: float
    success_rate: float


class AnalysisStatusResponse(BaseModel):
    """Response for analysis retrieval."""

    id: UUID
    status: str  # pending, in_progress, complete, failed
    progress: float | None = None
    result: VideoAnalysisResult | None = None
    error: dict | None = None


# ─── Creator Responses ───────────────────────────────────────────────────────


class CreatorProfileResponse(BaseModel):
    """Cached creator profile."""

    platform: Platform
    username: str
    display_name: str | None
    follower_count: int | None
    video_count: int | None
    last_analyzed: datetime | None
    cached_at: datetime


# ─── Health Responses ────────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    timestamp: datetime


class RuntimeModesDiagnostics(BaseModel):
    """Resolved runtime mode diagnostics."""

    environment: str
    externals_mode: Literal["real", "fake"]
    task_client_mode: Literal["cloud", "mock"]


class ReadyResponse(BaseModel):
    """Readiness check response."""

    status: str
    database: str
    runtime_modes: RuntimeModesDiagnostics
    timestamp: datetime


# ─── Fraud Detection Requests ───────────────────────────────────────────────


class FraudAnalyzeRequest(BaseModel):
    """Request to analyze a creator for fraud."""

    platform: Platform
    username: str = Field(
        ..., min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9._-]+$"
    )
    options: "FraudAnalyzeOptions" = Field(default_factory=lambda: FraudAnalyzeOptions())

    @field_validator("platform")
    @classmethod
    def reject_youtube(cls, v: Platform) -> Platform:
        if v == Platform.YOUTUBE:
            raise ValueError("Fraud analysis is not available for YouTube. Supported: tiktok, instagram")
        return v


class FraudAnalyzeOptions(BaseModel):
    """Options for fraud analysis."""

    sample_size: int = Field(default=100, ge=50, le=200, description="Follower sample size")
    force_refresh: bool = Field(default=False, description="Bypass cache")


# ─── Fraud Detection Responses ──────────────────────────────────────────────


class FraudAnalysisResult(BaseModel):
    """Fraud detection component results."""

    aqs_score: float = Field(ge=0, le=100, description="Audience Quality Score")
    aqs_grade: str = Field(description="Grade: excellent, very_good, good, poor, critical")
    aqs_components: dict = Field(description="Component scores breakdown")

    fake_follower_percentage: float | None = Field(
        default=None, description="Percentage of fake followers"
    )
    follower_sample_size: int | None = Field(
        default=None, description="Number of followers analyzed"
    )
    follower_confidence: str | None = Field(
        default=None, description="Confidence: low, medium, high"
    )

    engagement_rate: float | None = Field(
        default=None, description="Calculated engagement rate"
    )
    engagement_anomaly: str | None = Field(
        default=None, description="Detected anomaly type"
    )

    bot_comment_ratio: float | None = Field(
        default=None, description="Ratio of bot-like comments"
    )
    comments_analyzed: int | None = Field(
        default=None, description="Number of comments analyzed"
    )

    growth_data_available: bool = Field(default=False)
    methodology: str = Field(default="platform_calibrated")


class FraudAnalysisResponse(BaseModel):
    """Response schema for fraud analysis endpoint."""

    analysis_id: UUID
    creator_username: str
    platform: Platform

    fraud_analysis: FraudAnalysisResult = Field(description="Fraud detection results")

    risk_level: str = Field(description="Overall risk: low, medium, high, critical")
    risk_score: int = Field(ge=0, le=100, description="Risk score 0-100")
    recommendation: str = Field(description="Recommended action")

    status: str = Field(description="completed or cached")
    cached: bool
    analyzed_at: datetime
    processing_time_seconds: float | None = None


class FraudStatusResponse(BaseModel):
    """Response for fraud analysis retrieval by ID."""

    analysis_id: UUID
    status: str  # completed, pending, failed
    result: FraudAnalysisResponse | None = None
    error: dict | None = None


# ─── Async Job Responses ────────────────────────────────────────────────────


class AnalysisJobResponse(BaseModel):
    """Response for async job submission."""

    job_id: UUID
    status: str  # pending, running, complete, failed
    message: str


class JobSummary(BaseModel):
    """Summary of a job for listing."""

    id: UUID
    status: str
    total_videos: int
    completed_videos: int
    progress_percent: float
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    @classmethod
    def from_job(cls, job) -> "JobSummary":
        """Create summary from AnalysisJob."""
        return cls(
            id=job.id,
            status=job.status.value,
            total_videos=job.total_videos,
            completed_videos=job.completed_videos,
            progress_percent=job.progress_percent,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
        )


class Pagination(BaseModel):
    """Pagination metadata."""

    limit: int
    offset: int
    total: int


class JobListResponse(BaseModel):
    """Response for job listing."""

    jobs: list[JobSummary]
    pagination: Pagination


class JobStatusResponse(BaseModel):
    """Response for job status query."""

    id: UUID
    status: str
    progress_percent: float
    completed_videos: int
    total_videos: int
    results: list[dict] | None = None
    failure_reason: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    poll_after_seconds: int = 0


class JobCancellationResponse(BaseModel):
    """Response for job cancellation."""

    job_id: UUID
    status: str
    cancellation_requested: bool
    completed_videos: int
    total_videos: int
    partial_results: list[dict]


# ─── Search Requests/Responses (PR-012) ────────────────────────────────────────


class SearchResultItem(BaseModel):
    """Normalized search result across platforms."""

    platform: Platform
    video_id: str | None = None
    creator_id: str | None = None
    creator_handle: str
    title: str | None = None
    description: str | None = None
    thumbnail_url: str | None = None
    video_url: str | None = None
    view_count: int | None = None
    like_count: int | None = None
    comment_count: int | None = None
    follower_count: int | None = None
    engagement_rate: float | None = None
    created_at: str | None = None
    relevance_score: float = 0.0


class SearchFiltersInput(BaseModel):
    """Search filters for structured queries."""

    query: str | None = None
    hashtags: list[str] = Field(default_factory=list)
    min_views: int | None = None
    max_views: int | None = None
    min_followers: int | None = None
    max_followers: int | None = None
    min_engagement_rate: float | None = None
    date_range: str | None = None
    region: str | None = None


class ParsedSearchQueryInput(BaseModel):
    """Structured query for agent-native bypass of NL parsing."""

    scope: str = "videos"  # videos, influencers
    platforms: list[str] = Field(default_factory=list)
    search_type: str = "keyword"  # keyword, hashtag
    filters: SearchFiltersInput = Field(default_factory=SearchFiltersInput)
    sort_by: str = "relevance"
    limit: int = Field(default=50, ge=1, le=500)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    confidence_level: str = "high"  # high, medium, low
    unsupported_aspects: list[str] = Field(default_factory=list)


class SearchRequest(BaseModel):
    """Search request with natural language query."""

    query: str = Field(..., min_length=1, max_length=500)
    platforms: list[Literal["tiktok", "instagram", "youtube"]] | None = Field(
        default=None,
        max_length=3,
        description="Platforms to search: tiktok, instagram, youtube",
    )
    limit: int = Field(default=50, ge=1, le=500)

    # Agent-Native: Allow structured query to bypass NL parsing
    structured_query: ParsedSearchQueryInput | None = Field(
        default=None,
        description="If provided, skip NL parsing and use this directly.",
    )


class SearchResponse(BaseModel):
    """Search response with results and metadata."""

    interpretation: dict
    confidence: str
    results: list[SearchResultItem]
    total: int = 0
    platforms_searched: list[str] = Field(default_factory=list)
    platforms_failed: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


# ── GEO/SEO Audit ──────────────────────────────────────────────────────


class GeoAuditRequest(BaseModel):
    """Request to run a GEO audit on a URL."""

    url: str = Field(..., min_length=8, max_length=2048, pattern=r"^https?://")
    keywords: list[str] | None = Field(
        default=None,
        max_length=20,
        description="Target keywords for optimization",
    )


class GeoVisibilityRequest(BaseModel):
    """Request to check AI platform visibility for a brand."""

    brand: str = Field(..., min_length=1, max_length=200)
    keywords: list[str] = Field(..., min_length=1, max_length=20)
    platforms: list[str] | None = Field(
        default=None,
        max_length=10,
        description="AI platforms to check (chatgpt, perplexity, gemini, grok, copilot, claude, google_ai_mode)",
    )
    country: str | None = Field(
        default=None,
        pattern=r"^[A-Z]{2}$",
        description="ISO 3166-1 alpha-2 country code",
    )


class GeoOptimizeRequest(BaseModel):
    """Request to retrieve optimized content from a completed audit."""

    audit_id: UUID


class GeoAuditResponse(BaseModel):
    """Response for a GEO audit."""

    audit_id: UUID
    url: str
    status: str
    overall_score: float | None = None
    report_md: str | None = None
    findings: dict | None = None
    opportunities: dict | None = None
    keywords: list[str] | None = None
    created_at: datetime
    updated_at: datetime | None = None


class GeoAuditListItem(BaseModel):
    """Summary item for audit listing."""

    id: UUID
    url: str
    status: str
    overall_score: float | None = None
    keywords: list[str] | None = None
    created_at: datetime


class GeoAuditListResponse(BaseModel):
    """Paginated list of GEO audits."""

    audits: list[GeoAuditListItem]
    limit: int
    offset: int


class GeoVisibilityResponse(BaseModel):
    """Response for AI platform visibility check."""

    brand: str
    keywords: list[str]
    platforms_checked: list[str]
    results: dict
    total_brand_citations: int
    summary: str


class GeoOptimizeResponse(BaseModel):
    """Response for content optimization from audit."""

    audit_id: UUID
    url: str
    status: str
    overall_score: float | None = None
    optimized_content: dict | None = None
    findings_summary: dict | None = None


# ─── Competitive Ad Search ─────────────────────────────────────────────────


class CompetitiveAdSearchRequest(BaseModel):
    """Request to search competitor ads."""

    domain: str = Field(
        ..., min_length=1, max_length=253, pattern=r"^[a-zA-Z0-9.-]+$",
    )
    platform: str = Field(default="all")
    limit: int = Field(default=25, ge=1, le=100)


class CompetitiveAdSearchResponse(BaseModel):
    """Response for competitor ad search."""

    domain: str
    ad_count: int
    ads: list[dict]
    raw_foreplay_ads_count: int = 0


# ─── Creator Search ───────────────────────────────────────────────────────


class CreatorSearchRequest(BaseModel):
    """Request to search for competitor-affiliated creators."""

    query: str = Field(..., min_length=1, max_length=200)
    platforms: list[str] | None = Field(default=None, description="Limit to platforms: tiktok, youtube, content")
    limit: int = Field(default=20, ge=1, le=50)


class CreatorSearchResponse(BaseModel):
    """Response for creator search."""

    query: str
    creator_count: int
    creators: list[dict]
    platforms_searched: list[str]
    errors: list[str] = Field(default_factory=list)


# ─── Competitive Brief ─────────────────────────────────────────────────────


class CompetitiveBriefRequest(BaseModel):
    """Request to generate a competitive brief."""

    client_id: UUID
    date_range: str = Field(default="7d", pattern=r"^(7d|14d|30d)$")
    focus: str = Field(default="volume", max_length=100)
    depth: str = Field(default="snapshot", pattern=r"^(snapshot|deep)$")


class CompetitiveBriefResponse(BaseModel):
    """Response for competitive brief generation."""

    brief_id: UUID
    client_id: UUID
    brief_data: dict
    created_at: datetime


# ─── GEO Detect / Scrape ──────────────────────────────────────────────────


class GeoDetectRequest(BaseModel):
    """Request to detect GEO infrastructure on a URL."""

    url: str = Field(..., min_length=8, max_length=2048, pattern=r"^https://")
    full: bool = Field(default=False)


class GeoDetectResponse(BaseModel):
    """Response for GEO infrastructure detection."""

    url: str
    final_url: str
    geo_infrastructure: dict
    seo_technical: dict
    seo_full: dict | None = None


class GeoScrapeRequest(BaseModel):
    """Request to scrape a page."""

    url: str = Field(..., min_length=8, max_length=2048, pattern=r"^https://")


class GeoScrapeResponse(BaseModel):
    """Response for page scraping."""

    url: str
    final_url: str
    title: str | None = None
    h1: str | None = None
    h2s: list[str]
    meta_description: str | None = None
    text: str
    word_count: int
    schema_types: list[str]
    status_code: int
    text_truncated: bool = False
