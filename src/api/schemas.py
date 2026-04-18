"""API request/response schemas — trimmed to autoresearch-used subset.

This file was ported from freddy/src/api/schemas.py (802 LOC, 59 classes) and
trimmed to only the 16 classes referenced by the ported geo + competitive
routers. Classes removed (never imported in gofreddy): Library/CreatorGroup/
SessionGroup/Timeline/Analyze*/VideoAnalysis/Fraud/AnalysisJob/Pagination/
Search* and CompetitiveBrief{Request,Response}.

If you add a new router that needs one of the removed classes, restore it
from freddy/src/api/schemas.py at the same revision.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


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
