"""Signal aggregator orchestrator (R17 / U15 / TD-42).

`gather_signals(domain, locale, ...)` — sync wrapper that fans out
across 5 providers (3 Meta-side + SerpAPI + GSC), merges Meta-side
results via signal_merger, and emits a structured `SignalBundle` the
lane workflow consumes.

Per TD-42 Option D hybrid: aggregator is deterministic (Rule 5 — pure
Python except for ONE final summarization LLM call). The lane reads
the structured brief; the LLM summary lives alongside as a 6-10
bullet prose annex.

Async-to-sync bridge per the U15 plan: providers are async via
`httpx.AsyncClient`; lane callables are sync per `WorkflowSpec`
contract. `gather_signals` wraps async provider calls via
`asyncio.run(...)`. Precedent: `evaluate_session.py:497` uses the
same pattern.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable

from src.ads.signal_aggregator.merger import merge_ad_signals
from src.ads.signal_aggregator.providers import (
    AdSignal,
    AdyntelProvider,
    ForeplayProvider,
    GscProvider,
    MetaAdLibraryProvider,
    SearchSignal,
    SerpApiProvider,
)

logger = logging.getLogger(__name__)


@dataclass
class SignalBundle:
    """Structured creative brief input. Lane workflow consumes this +
    the LLM prose summary; the raw signal annex stays available for
    citation but NOT in default agent context window (token budget)."""

    top_competitor_ads: list[tuple[AdSignal, float]] = field(default_factory=list)
    recurring_hook_archetypes: dict[str, int] = field(default_factory=dict)
    serp_signal: list[SearchSignal] = field(default_factory=list)
    gsc_signal: list[SearchSignal] = field(default_factory=list)
    competitor_voice_anti_examples: list[str] = field(default_factory=list)
    degraded_sources: list[str] = field(default_factory=list)


async def _gather_async(
    *,
    advertiser_domain: str,
    format: str,
    serp_query: str,
    gsc_site_url: str,
    locale_gl: str,
    locale_hl: str,
    google_domain: str,
    providers: dict,
) -> SignalBundle:
    """Run all 5 providers concurrently; tolerate per-provider failure."""
    foreplay = providers.get("foreplay") or ForeplayProvider()
    adyntel = providers.get("adyntel") or AdyntelProvider()
    meta_lib = providers.get("meta_ad_library") or MetaAdLibraryProvider()
    serpapi = providers.get("serpapi") or SerpApiProvider()
    gsc = providers.get("gsc") or GscProvider()

    degraded: list[str] = []

    async def _safe(name: str, coro):
        try:
            return await coro
        except Exception as exc:
            logger.warning("signal_aggregator: %s failed (%s); degraded", name, exc)
            degraded.append(name)
            return []

    results = await asyncio.gather(
        _safe("foreplay", foreplay.gather(
            advertiser_domain=advertiser_domain, format=format,
        )),
        _safe("adyntel", adyntel.gather(
            advertiser_domain=advertiser_domain, format=format,
        )),
        _safe("meta_ad_library", meta_lib.gather(
            advertiser_domain=advertiser_domain, format=format,
        )),
        _safe("serpapi", serpapi.gather(
            query=serp_query, gl=locale_gl, hl=locale_hl,
            google_domain=google_domain,
        )),
        _safe("gsc", gsc.gather(site_url=gsc_site_url, days=28)),
    )
    foreplay_ads, adyntel_ads, meta_ads, serp_results, gsc_results = results

    # Mark degraded sources that returned empty (no exception but no data).
    if not foreplay_ads and "foreplay" not in degraded:
        degraded.append("foreplay")
    if not adyntel_ads and "adyntel" not in degraded:
        degraded.append("adyntel")
    if not meta_ads and "meta_ad_library" not in degraded:
        degraded.append("meta_ad_library")

    merged = merge_ad_signals(
        [*foreplay_ads, *adyntel_ads, *meta_ads],
    )

    # Recurring hook archetype clustering — naive first-word grouping
    # for v1; meta-agent can evolve toward better clustering.
    archetypes: dict[str, int] = {}
    for sig, _score in merged:
        tokens = sig.creative_text.lower().split()
        if not tokens:
            continue
        # Use the first 3 tokens as an archetype key.
        key = " ".join(tokens[:3])
        archetypes[key] = archetypes.get(key, 0) + 1

    # Anti-examples: pull the top-5 most-frequent archetype hooks for
    # the agent to NOT mimic.
    anti = sorted(archetypes.items(), key=lambda p: p[1], reverse=True)[:5]
    anti_examples = [k for k, _v in anti if _v >= 2]  # repeated only

    return SignalBundle(
        top_competitor_ads=merged,
        recurring_hook_archetypes=archetypes,
        serp_signal=list(serp_results)[:5],
        gsc_signal=list(gsc_results)[:10],
        competitor_voice_anti_examples=anti_examples,
        degraded_sources=degraded,
    )


def gather_signals(
    *,
    advertiser_domain: str,
    format: str,
    serp_query: str,
    gsc_site_url: str,
    locale_gl: str = "us",
    locale_hl: str = "en",
    google_domain: str = "google.com",
    providers: dict | None = None,
) -> SignalBundle:
    """Sync entry point — fans out across 5 providers + merges + returns
    `SignalBundle`.

    Per the U15 plan async-to-sync bridge: this wraps the async
    provider calls via `asyncio.run(...)`. Lane workflow callables
    are sync per `WorkflowSpec` contract.

    `providers` is an optional dict of {name: provider_instance}
    overrides for tests. Production callers leave it None and rely
    on each Provider class's default fetcher (which lands in U18).

    Returns a `SignalBundle` with degraded_sources populated for
    every provider that failed or returned empty. Per R19: the lane's
    AD-7 market-signal alignment dimension no-ops when ALL Meta-side
    providers are degraded.
    """
    return asyncio.run(_gather_async(
        advertiser_domain=advertiser_domain,
        format=format,
        serp_query=serp_query,
        gsc_site_url=gsc_site_url,
        locale_gl=locale_gl,
        locale_hl=locale_hl,
        google_domain=google_domain,
        providers=providers or {},
    ))


def all_meta_sources_degraded(bundle: SignalBundle) -> bool:
    """True when all 3 Meta-side providers are in degraded_sources.
    Lane uses this to no-op the AD-7 market-signal dimension per R19."""
    meta_side = {"foreplay", "adyntel", "meta_ad_library"}
    return meta_side.issubset(set(bundle.degraded_sources))


__all__ = [
    "SignalBundle",
    "all_meta_sources_degraded",
    "gather_signals",
]
