"""U15 — signal_aggregator orchestrator tests (TD-42 5-provider DI)."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.ads.signal_aggregator import (
    SignalBundle,
    all_meta_sources_degraded,
    gather_signals,
)
from src.ads.signal_aggregator.providers import (
    AdyntelProvider,
    ForeplayProvider,
    GscProvider,
    MetaAdLibraryProvider,
    SerpApiProvider,
)


async def _fake_foreplay_fetch(advertiser_domain: str, format: str, **kw):
    return [{
        "ad_id": "fp_001",
        "advertiser_id": "adv_x",
        "creative_text": "Tired of broken workflows? Meet our platform.",
        "format": format,
        "last_seen_active": datetime.now(timezone.utc).isoformat(),
        "days_running": 30,
    }]


async def _fake_adyntel_fetch(advertiser_domain: str, format: str, **kw):
    return [{
        "ad_id": "ad_001",
        "advertiser_id": "adv_x",
        "creative_text": "Different angle for the same advertiser.",
        "format": format,
        "last_seen_active": datetime.now(timezone.utc).isoformat(),
        "days_running": 60,
    }]


async def _fake_meta_lib_fetch(advertiser_domain: str, format: str, country: str = "ALL", **kw):
    return [{
        "ad_id": "meta_001",
        "advertiser_id": "adv_x",
        "creative_text": "Authoritative EU-DSA-disclosed ad.",
        "format": format,
        "last_seen_active": datetime.now(timezone.utc).isoformat(),
        "days_running": 45,
    }]


async def _fake_serpapi_fetch(query: str, **kw):
    return [{"query": query, "rank": 1, "impressions": 1000}]


async def _fake_gsc_fetch(site_url: str, days: int = 28, **kw):
    return [{
        "query": "our offer keyword",
        "impressions": 500,
        "ctr": 0.05,
        "delta_position": -2.0,
    }]


async def _failing_fetch(**kw):
    raise RuntimeError("simulated provider failure")


# ---------------------------------------------------------------------------
# Happy path — all 5 providers return data
# ---------------------------------------------------------------------------


def test_gather_signals_returns_bundle_when_all_providers_ok() -> None:
    bundle = gather_signals(
        advertiser_domain="example.com",
        format="meta_image",
        serp_query="our offer",
        gsc_site_url="https://example.com",
        providers={
            "foreplay": ForeplayProvider(fetch=_fake_foreplay_fetch),
            "adyntel": AdyntelProvider(fetch=_fake_adyntel_fetch),
            "meta_ad_library": MetaAdLibraryProvider(fetch=_fake_meta_lib_fetch),
            "serpapi": SerpApiProvider(fetch=_fake_serpapi_fetch),
            "gsc": GscProvider(fetch=_fake_gsc_fetch),
        },
    )
    assert isinstance(bundle, SignalBundle)
    assert len(bundle.top_competitor_ads) > 0
    assert len(bundle.serp_signal) > 0
    assert len(bundle.gsc_signal) > 0
    assert bundle.degraded_sources == []


# ---------------------------------------------------------------------------
# Degraded providers
# ---------------------------------------------------------------------------


def test_gather_signals_marks_degraded_sources_on_failure() -> None:
    bundle = gather_signals(
        advertiser_domain="example.com",
        format="meta_image",
        serp_query="x",
        gsc_site_url="https://example.com",
        providers={
            "foreplay": ForeplayProvider(fetch=_failing_fetch),
            "adyntel": AdyntelProvider(fetch=_fake_adyntel_fetch),
            "meta_ad_library": MetaAdLibraryProvider(fetch=_fake_meta_lib_fetch),
            "serpapi": SerpApiProvider(fetch=_fake_serpapi_fetch),
            "gsc": GscProvider(fetch=_fake_gsc_fetch),
        },
    )
    assert "foreplay" in bundle.degraded_sources


def test_all_meta_sources_degraded_true_when_all_3_fail() -> None:
    bundle = gather_signals(
        advertiser_domain="example.com",
        format="meta_image",
        serp_query="x",
        gsc_site_url="https://example.com",
        providers={
            "foreplay": ForeplayProvider(fetch=_failing_fetch),
            "adyntel": AdyntelProvider(fetch=_failing_fetch),
            "meta_ad_library": MetaAdLibraryProvider(fetch=_failing_fetch),
            "serpapi": SerpApiProvider(fetch=_fake_serpapi_fetch),
            "gsc": GscProvider(fetch=_fake_gsc_fetch),
        },
    )
    assert all_meta_sources_degraded(bundle) is True


def test_all_meta_sources_degraded_false_when_one_works() -> None:
    bundle = gather_signals(
        advertiser_domain="example.com",
        format="meta_image",
        serp_query="x",
        gsc_site_url="https://example.com",
        providers={
            "foreplay": ForeplayProvider(fetch=_fake_foreplay_fetch),
            "adyntel": AdyntelProvider(fetch=_failing_fetch),
            "meta_ad_library": MetaAdLibraryProvider(fetch=_failing_fetch),
            "serpapi": SerpApiProvider(fetch=_fake_serpapi_fetch),
            "gsc": GscProvider(fetch=_fake_gsc_fetch),
        },
    )
    assert all_meta_sources_degraded(bundle) is False


# ---------------------------------------------------------------------------
# Empty-data path (no exception but no signal)
# ---------------------------------------------------------------------------


def test_provider_returning_empty_marked_degraded() -> None:
    """Per R19: a provider returning [] (no exception) is still
    degraded — the lane's AD-7 dimension should know."""
    async def empty(**kw):
        return []

    bundle = gather_signals(
        advertiser_domain="example.com",
        format="meta_image",
        serp_query="x",
        gsc_site_url="https://example.com",
        providers={
            "foreplay": ForeplayProvider(fetch=empty),
            "adyntel": AdyntelProvider(fetch=empty),
            "meta_ad_library": MetaAdLibraryProvider(fetch=empty),
            "serpapi": SerpApiProvider(fetch=_fake_serpapi_fetch),
            "gsc": GscProvider(fetch=_fake_gsc_fetch),
        },
    )
    assert set(bundle.degraded_sources) >= {"foreplay", "adyntel", "meta_ad_library"}


# ---------------------------------------------------------------------------
# Archetype clustering + anti-examples
# ---------------------------------------------------------------------------


def test_recurring_hook_archetypes_clustered() -> None:
    """Multiple ads sharing opening 3-gram cluster into archetypes."""
    async def shared_opener_foreplay(**kw):
        return [
            {
                "ad_id": f"fp_{i}",
                "advertiser_id": f"adv_{i}",
                "creative_text": f"Tired of broken workflows option {i}.",
                "format": "meta_image",
                "last_seen_active": datetime.now(timezone.utc).isoformat(),
                "days_running": 30,
            }
            for i in range(3)
        ]

    bundle = gather_signals(
        advertiser_domain="example.com",
        format="meta_image",
        serp_query="x",
        gsc_site_url="https://example.com",
        providers={
            "foreplay": ForeplayProvider(fetch=shared_opener_foreplay),
            "adyntel": AdyntelProvider(),  # default = no fetch
            "meta_ad_library": MetaAdLibraryProvider(),
            "serpapi": SerpApiProvider(),
            "gsc": GscProvider(),
        },
    )
    assert "tired of broken" in bundle.recurring_hook_archetypes
    assert bundle.recurring_hook_archetypes["tired of broken"] == 3
    assert "tired of broken" in bundle.competitor_voice_anti_examples
