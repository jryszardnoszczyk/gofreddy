"""5-provider signal aggregator clients (R17 / U15 / TD-34 + TD-42).

Per JR's 2026-05-19 U15 decision: ship all 5 providers as
dependency-injected fetchers. Each provider's `fetch_*` callable
defaults to an httpx-based real client; tests inject fakes;
production wiring (API keys + httpx calls) lands at U18.

Provider responsibility:
- ForeplayProvider     — Meta/IG/TikTok/LinkedIn crowdsourced ad library
- AdyntelProvider      — Meta/LinkedIn/Google transparency-pull by domain
- MetaAdLibraryProvider — Meta Ad Library API (EU-DSA-favored, free)
- SerpApiProvider      — SerpAPI Starter ($25/mo for SERP signal)
- GscProvider          — Google Search Console (first-party SEO)

Each provider returns a normalized `AdSignal` (for ad-shaped sources)
or `SearchSignal` (for SERP/GSC). The signal_aggregator orchestrates
all 5 and the signal_merger dedupes + weights.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Protocol


@dataclass(frozen=True)
class AdSignal:
    """Normalized ad-shaped signal across Foreplay / Adyntel / Meta Ad Library."""

    ad_id: str | None  # stable ID where present (Meta Ad Library); else hash
    advertiser_id: str
    creative_text: str
    format: str  # "meta_reels" | "meta_image" | "linkedin_sponsored" | ...
    last_seen_active: datetime
    days_running: int
    sources: list[str] = field(default_factory=list)  # which provider(s) returned this
    raw: dict = field(default_factory=dict)  # provider-specific raw response


@dataclass(frozen=True)
class SearchSignal:
    """Normalized search-shaped signal across SerpAPI + GSC."""

    query: str
    rank: int | None  # SERP position (1-indexed) or None for GSC
    impressions: int | None
    ctr: float | None
    delta_position: float | None  # 28d position change, GSC only
    source: str  # "serpapi" | "gsc"
    raw: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Fetcher protocol — DI surface
# ---------------------------------------------------------------------------


class Fetcher(Protocol):
    """Async fetcher signature. Real impls use `httpx.AsyncClient`; test
    fakes return canned bundles."""

    async def __call__(self, **kwargs) -> list[dict]: ...


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------


@dataclass
class ForeplayProvider:
    """Foreplay (foreplay.co) — crowdsourced Meta/IG/TikTok/LinkedIn
    ad library. Auth: `FOREPLAY_API_KEY`. US-DTC-skewed; archive
    depth weak beyond 3 months (freshness_floor_days mitigates)."""

    fetch: Fetcher | None = None  # injected per call; default real fetcher in U18

    async def gather(
        self, advertiser_domain: str, format: str, **kwargs
    ) -> list[AdSignal]:
        if self.fetch is None:
            return []  # degraded mode — production wiring in U18
        raw = await self.fetch(
            advertiser_domain=advertiser_domain, format=format, **kwargs,
        )
        return [_parse_ad(entry, source="foreplay") for entry in raw]


@dataclass
class AdyntelProvider:
    """Adyntel — Meta/LinkedIn/Google transparency-pull by domain.
    Auth: `ADYNTEL_API_KEY`. Broad geographic coverage; 24-72h
    indexing lag."""

    fetch: Fetcher | None = None

    async def gather(
        self, advertiser_domain: str, format: str, **kwargs
    ) -> list[AdSignal]:
        if self.fetch is None:
            return []
        raw = await self.fetch(
            advertiser_domain=advertiser_domain, format=format, **kwargs,
        )
        return [_parse_ad(entry, source="adyntel") for entry in raw]


@dataclass
class MetaAdLibraryProvider:
    """Meta Ad Library API (free; EU-DSA enhanced disclosure). Auth:
    `META_AD_LIBRARY_TOKEN`. Authoritative for EU advertisers; stable
    `ad_id` for cross-provider dedupe."""

    fetch: Fetcher | None = None

    async def gather(
        self, advertiser_domain: str, format: str, country: str = "ALL", **kwargs
    ) -> list[AdSignal]:
        if self.fetch is None:
            return []
        raw = await self.fetch(
            advertiser_domain=advertiser_domain, format=format,
            country=country, **kwargs,
        )
        return [_parse_ad(entry, source="meta_ad_library") for entry in raw]


@dataclass
class SerpApiProvider:
    """SerpAPI Starter — top-N SERP signal for offer keywords +
    intent classification. Auth: `SERPAPI_API_KEY`. Locale-aware
    (reads `ClientConfig.locale.gl/hl/google_domain`)."""

    fetch: Fetcher | None = None

    async def gather(
        self, query: str, gl: str = "us", hl: str = "en",
        google_domain: str = "google.com", **kwargs,
    ) -> list[SearchSignal]:
        if self.fetch is None:
            return []
        raw = await self.fetch(
            query=query, gl=gl, hl=hl, google_domain=google_domain, **kwargs,
        )
        return [_parse_search(entry, source="serpapi") for entry in raw]


@dataclass
class GscProvider:
    """Google Search Console — first-party SEO. Auth: per-client
    OAuth refresh tokens (shared OAuth client). Reads top queries +
    impressions + CTR + position deltas over 28d."""

    fetch: Fetcher | None = None

    async def gather(
        self, site_url: str, days: int = 28, **kwargs,
    ) -> list[SearchSignal]:
        if self.fetch is None:
            return []
        raw = await self.fetch(site_url=site_url, days=days, **kwargs)
        return [_parse_search(entry, source="gsc") for entry in raw]


# ---------------------------------------------------------------------------
# Parsers — provider-specific raw dict → normalized signal
# ---------------------------------------------------------------------------


def _parse_ad(entry: dict, source: str) -> AdSignal:
    """Normalize a provider's ad record into AdSignal.

    Each provider exposes slightly different field names; this parser
    accepts a permissive shape so providers can ship fakes for tests
    without exact API replication.
    """
    last_seen = entry.get("last_seen_active") or entry.get("last_seen") or datetime.now(timezone.utc)
    if isinstance(last_seen, str):
        try:
            last_seen = datetime.fromisoformat(last_seen.replace("Z", "+00:00"))
        except ValueError:
            last_seen = datetime.now(timezone.utc)
    return AdSignal(
        ad_id=entry.get("ad_id") or entry.get("id"),
        advertiser_id=str(entry.get("advertiser_id") or entry.get("page_id") or ""),
        creative_text=str(entry.get("creative_text") or entry.get("body") or ""),
        format=str(entry.get("format") or ""),
        last_seen_active=last_seen,
        days_running=int(entry.get("days_running", 0)),
        sources=[source],
        raw=entry,
    )


def _parse_search(entry: dict, source: str) -> SearchSignal:
    """Normalize SERP / GSC dict into SearchSignal."""
    return SearchSignal(
        query=str(entry.get("query") or ""),
        rank=entry.get("rank") or entry.get("position"),
        impressions=entry.get("impressions"),
        ctr=entry.get("ctr"),
        delta_position=entry.get("delta_position"),
        source=source,
        raw=entry,
    )


__all__ = [
    "AdSignal",
    "AdyntelProvider",
    "Fetcher",
    "ForeplayProvider",
    "GscProvider",
    "MetaAdLibraryProvider",
    "SearchSignal",
    "SerpApiProvider",
]
