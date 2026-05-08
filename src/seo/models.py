"""SEO audit data models."""

from dataclasses import dataclass, field
from datetime import date
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class TechnicalIssue:
    """Single technical SEO issue."""

    category: str  # e.g. "meta_tags", "indexability", "links"
    severity: str  # "critical", "warning", "info"
    description: str
    details: str | None = None


@dataclass(frozen=True, slots=True)
class TechnicalAuditResult:
    """Result from DataForSEO on-page audit."""

    url: str
    status_code: int | None = None
    title: str | None = None
    description: str | None = None
    h1: str | None = None
    canonical: str | None = None
    is_indexable: bool | None = None
    issues: tuple[TechnicalIssue, ...] = ()


@dataclass(frozen=True, slots=True)
class KeywordData:
    """Keyword research data from DataForSEO."""

    keyword: str
    search_volume: int | None = None
    cpc: float | None = None
    competition: float | None = None  # 0.0-1.0
    difficulty: int | None = None  # 0-100
    trend: tuple[float, ...] = ()  # Monthly search volume trend


@dataclass(frozen=True, slots=True)
class KeywordAnalysisResult:
    """Result from keyword analysis."""

    keywords: tuple[KeywordData, ...] = ()
    location_code: int | None = None
    language_code: str | None = None


@dataclass(frozen=True, slots=True)
class BacklinkData:
    """Single backlink record."""

    source_url: str
    target_url: str
    anchor: str | None = None
    domain_rank: int | None = None
    is_dofollow: bool = True


@dataclass(frozen=True, slots=True)
class BacklinkSnapshot:
    """Backlink profile snapshot from DataForSEO."""

    target_url: str
    total_backlinks: int = 0
    referring_domains: int = 0
    dofollow_count: int = 0
    nofollow_count: int = 0
    top_backlinks: tuple[BacklinkData, ...] = ()


@dataclass(frozen=True, slots=True)
class PerformanceResult:
    """PageSpeed Insights result."""

    url: str
    performance_score: float | None = None  # 0.0-1.0
    fcp_ms: float | None = None  # First Contentful Paint
    lcp_ms: float | None = None  # Largest Contentful Paint
    cls: float | None = None  # Cumulative Layout Shift
    tbt_ms: float | None = None  # Total Blocking Time
    speed_index_ms: float | None = None
    strategy: str = "mobile"  # mobile or desktop


@dataclass(frozen=True, slots=True)
class DomainRankSnapshot:
    """Domain-level rank snapshot from DataForSEO backlinks/summary."""

    domain: str
    rank: int | None = None  # 0-1000
    backlinks_total: int = 0
    referring_domains: int = 0
    snapshot_date: date | None = None
    org_id: UUID | None = None


# --- L2 marketing-audit additions (master plan §4.9 work item #5) ---------


@dataclass(frozen=True, slots=True)
class SerpFeature:
    """Single SERP feature row from DataForSEO Labs serp_competitors / SERP."""

    feature_type: str  # e.g. "answer_box", "featured_snippet", "people_also_ask"
    rank: int | None = None
    url: str | None = None
    domain: str | None = None
    title: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class SerpFeaturesResult:
    """Aggregated SERP features for a keyword query."""

    keyword: str
    location_code: int | None = None
    language_code: str | None = None
    features_present: tuple[str, ...] = ()  # distinct feature types in result
    items: tuple[SerpFeature, ...] = ()
    total_count: int = 0


@dataclass(frozen=True, slots=True)
class HistoricalRankPoint:
    """One row of the historical rank time series."""

    period: str  # "YYYY-MM" or "YYYY-MM-DD"
    rank: int | None = None
    backlinks: int | None = None
    referring_domains: int | None = None


@dataclass(frozen=True, slots=True)
class HistoricalRankResult:
    """Historical domain-rank time series from DataForSEO."""

    target: str  # domain or url
    points: tuple[HistoricalRankPoint, ...] = ()
    date_from: str | None = None
    date_to: str | None = None


@dataclass(frozen=True, slots=True)
class GbpHours:
    """Google Business Profile open hours summary."""

    monday: str | None = None
    tuesday: str | None = None
    wednesday: str | None = None
    thursday: str | None = None
    friday: str | None = None
    saturday: str | None = None
    sunday: str | None = None


@dataclass(frozen=True, slots=True)
class GbpResult:
    """Google Business Profile data row from DataForSEO business_data."""

    name: str
    place_id: str | None = None
    cid: str | None = None
    address: str | None = None
    domain: str | None = None
    phone: str | None = None
    rating_value: float | None = None
    rating_count: int | None = None
    category: str | None = None
    additional_categories: tuple[str, ...] = ()
    latitude: float | None = None
    longitude: float | None = None
    url: str | None = None
    is_claimed: bool | None = None
    hours: GbpHours | None = None
    attributes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class GbpSearchResult:
    """Result of a DataForSEO GBP keyword + location search."""

    keyword: str
    location_code: int | None = None
    items: tuple[GbpResult, ...] = ()
    total_count: int = 0
