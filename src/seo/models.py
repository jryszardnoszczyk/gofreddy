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
