"""Curate candidate videos for validation spikes via end-to-end search.

Runs natural language queries through the full SearchService pipeline
(Gemini parser -> platform fetchers) to discover candidate videos for:
  - Spike 1: Brand Exposure timestamp_end validation (15-20 videos)
  - Spike 2: Creative Pattern taxonomy validation (50 videos)

Also serves as a stress test of our search capabilities.

Run with:
    RUN_LIVE_EXTERNAL=1 RUN_GEMINI=1 pytest tests/spikes/test_curate_videos.py -v -s
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from .conftest import write_spike_report

logger = logging.getLogger(__name__)

REPORT_DIR = Path(__file__).parent / "curation_reports"

# Rate limit protection between queries (seconds)
QUERY_DELAY = 2.0


# ---------------------------------------------------------------------------
# Query definitions
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CurationQuery:
    """A natural language query for video curation."""

    query: str
    platforms: list[str] = field(default_factory=list)
    rationale: str = ""
    # Expected ground truth labels (for populating video_sets.py later)
    expected_brands: list[str] = field(default_factory=list)
    expected_hook: str | None = None
    expected_narrative: str | None = None


# Spike 1: Brand Exposure — 8 queries, target 15-20 videos
SPIKE1_BRAND_QUERIES: list[CurationQuery] = [
    CurationQuery(
        query="sponsored iPhone review unboxing YouTube",
        platforms=["youtube"],
        rationale="Tech review with prominent Apple branding (speech + visual logo + text overlay)",
        expected_brands=["Apple", "iPhone"],
    ),
    CurationQuery(
        query="TikTok creator showing off new skincare products #ad",
        platforms=["tiktok"],
        rationale="Sponsored skincare content (speech + hashtag detection)",
        expected_brands=["CeraVe", "The Ordinary"],
    ),
    CurationQuery(
        query="Nike or Adidas sneaker haul try on",
        platforms=[],
        rationale="Athletic brand logos prominently visible (visual logo + speech)",
        expected_brands=["Nike", "Adidas"],
    ),
    CurationQuery(
        query="energy drink brand deal Red Bull Monster",
        platforms=["youtube", "tiktok"],
        rationale="Energy drink sponsorships (speech + visual logo)",
        expected_brands=["Red Bull", "Monster"],
    ),
    CurationQuery(
        query="Instagram fashion influencer paid partnership designer bags",
        platforms=["instagram"],
        rationale="Fashion paid partnership with text overlay (text_overlay + visual_logo)",
        expected_brands=["Gucci", "Louis Vuitton"],
    ),
    CurationQuery(
        query="tech reviewer comparing Samsung Galaxy vs iPhone",
        platforms=["youtube"],
        rationale="Phone comparison review (speech + visual_logo)",
        expected_brands=["Samsung", "Apple"],
    ),
    CurationQuery(
        query="meal prep sponsored by HelloFresh cooking",
        platforms=["youtube", "tiktok"],
        rationale="Meal kit sponsorship (speech + text_overlay)",
        expected_brands=["HelloFresh"],
    ),
    CurationQuery(
        query="gaming setup tour keyboard mouse headset brands",
        platforms=["youtube"],
        rationale="Gaming peripherals with visible brand logos (visual_logo + speech)",
        expected_brands=["Razer", "Logitech"],
    ),
]


# Spike 2: Creative Patterns — 18 queries, target 50 videos
# Coverage: all 7 hook types, all 10 narrative structures, all 3 platforms
SPIKE2_CREATIVE_QUERIES: list[CurationQuery] = [
    CurationQuery(
        query="what would happen if I tried this for 30 days",
        platforms=["youtube"],
        rationale="Challenge/transformation content (question hook + transformation narrative)",
        expected_hook="question",
        expected_narrative="transformation",
    ),
    CurationQuery(
        query="you won't believe what I found at the thrift store",
        platforms=["tiktok", "youtube"],
        rationale="Curiosity-driven vlog (shock_curiosity hook + vlog narrative)",
        expected_hook="shock_curiosity",
        expected_narrative="vlog",
    ),
    CurationQuery(
        query="trending sound TikTok dance challenge viral audio",
        platforms=["tiktok"],
        rationale="Audio-driven trend content (trend_audio hook)",
        expected_hook="trend_audio",
        expected_narrative="other",
    ),
    CurationQuery(
        query="storytime how I quit my job and started a business",
        platforms=["youtube", "tiktok"],
        rationale="Personal storytelling (storytelling hook + vlog narrative)",
        expected_hook="storytelling",
        expected_narrative="vlog",
    ),
    CurationQuery(
        query="new product launch reveal first look gadget 2025",
        platforms=["youtube"],
        rationale="Product reveal content (product_reveal hook + review narrative)",
        expected_hook="product_reveal",
        expected_narrative="review",
    ),
    CurationQuery(
        query="24 hour challenge overnight in store",
        platforms=["youtube"],
        rationale="Challenge format (challenge hook + vlog narrative)",
        expected_hook="challenge",
        expected_narrative="vlog",
    ),
    CurationQuery(
        query="how to fix a leaking faucet step by step plumbing",
        platforms=["youtube"],
        rationale="Straightforward tutorial (none hook + tutorial narrative)",
        expected_hook="none",
        expected_narrative="tutorial",
    ),
    CurationQuery(
        query="beginner makeup tutorial natural look step by step",
        platforms=["youtube", "instagram"],
        rationale="Beauty tutorial (question hook + tutorial narrative)",
        expected_hook="question",
        expected_narrative="tutorial",
    ),
    CurationQuery(
        query="honest review of the new MacBook after one month",
        platforms=["youtube"],
        rationale="Long-term review (question hook + review narrative)",
        expected_hook="question",
        expected_narrative="review",
    ),
    CurationQuery(
        query="unboxing mystery box subscription package opening",
        platforms=["youtube", "tiktok"],
        rationale="Unboxing content (product_reveal hook + unboxing narrative)",
        expected_hook="product_reveal",
        expected_narrative="unboxing",
    ),
    CurationQuery(
        query="day in the life of a software engineer San Francisco",
        platforms=["youtube", "tiktok"],
        rationale="Day-in-life vlog (storytelling hook + day_in_life narrative)",
        expected_hook="storytelling",
        expected_narrative="day_in_life",
    ),
    CurationQuery(
        query="extreme room makeover before and after on a budget",
        platforms=["youtube", "tiktok"],
        rationale="Transformation content (shock_curiosity hook + transformation narrative)",
        expected_hook="shock_curiosity",
        expected_narrative="transformation",
    ),
    CurationQuery(
        query="cheap vs expensive headphones which sounds better",
        platforms=["youtube"],
        rationale="Comparison content (question hook + comparison narrative)",
        expected_hook="question",
        expected_narrative="comparison",
    ),
    CurationQuery(
        query="top 10 travel destinations you need to visit 2025",
        platforms=["youtube"],
        rationale="Listicle content (shock_curiosity hook + listicle narrative)",
        expected_hook="shock_curiosity",
        expected_narrative="listicle",
    ),
    CurationQuery(
        query="funny comedy skit relatable school moments",
        platforms=["tiktok", "instagram"],
        rationale="Comedy skit (storytelling hook + skit narrative)",
        expected_hook="storytelling",
        expected_narrative="skit",
    ),
    CurationQuery(
        query="moving to a new city apartment hunting vlog",
        platforms=["youtube"],
        rationale="Lifestyle vlog (storytelling hook + vlog narrative)",
        expected_hook="storytelling",
        expected_narrative="vlog",
    ),
    CurationQuery(
        query="fast paced TikTok edits with transitions and effects",
        platforms=["tiktok"],
        rationale="Edit-heavy trend content (trend_audio hook)",
        expected_hook="trend_audio",
        expected_narrative="other",
    ),
    CurationQuery(
        query="cinematic travel film drone footage landscape 4K",
        platforms=["youtube"],
        rationale="Cinematic content with no explicit hook (none hook + vlog narrative)",
        expected_hook="none",
        expected_narrative="vlog",
    ),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _compute_keyword_relevance(
    results: list[dict[str, Any]], query: str
) -> float:
    """Fraction of results where a core query keyword appears in title or description."""
    if not results:
        return 0.0

    # Extract meaningful keywords (skip short words and platform names)
    stop_words = {
        "a", "an", "the", "in", "on", "of", "for", "to", "and", "or",
        "with", "by", "at", "vs", "i", "my", "you", "new", "how",
        "youtube", "tiktok", "instagram", "#ad",
    }
    keywords = [
        w.lower().strip("#")
        for w in query.split()
        if len(w) > 2 and w.lower().strip("#") not in stop_words
    ]

    if not keywords:
        return 0.0

    matches = 0
    for r in results:
        text = f"{r.get('title') or ''} {r.get('description') or ''}".lower()
        if any(kw in text for kw in keywords):
            matches += 1

    return matches / len(results)


async def _run_query(
    search_service: Any,
    curation_query: CurationQuery,
    limit: int = 20,
) -> dict[str, Any]:
    """Execute a single curation query and compute metrics."""
    start = time.monotonic()

    try:
        response = await search_service.search(
            query=curation_query.query,
            platforms=curation_query.platforms or None,
            limit=limit,
        )
    except Exception as e:
        elapsed_ms = (time.monotonic() - start) * 1000
        logger.error("Query failed: %s — %s", curation_query.query, e)
        return {
            "query_text": curation_query.query,
            "platforms_param": curation_query.platforms,
            "rationale": curation_query.rationale,
            "error": str(e),
            "metrics": {
                "latency_ms": round(elapsed_ms),
            },
            "candidates": [],
        }

    elapsed_ms = (time.monotonic() - start) * 1000
    results = response.get("results", [])
    interpretation = response.get("interpretation", {})

    # Compute metrics
    results_with_video_id = sum(1 for r in results if r.get("video_id"))
    keyword_pct = _compute_keyword_relevance(results, curation_query.query)

    metrics = {
        "parse_confidence": interpretation.get("confidence", 0.0),
        "confidence_level": response.get("confidence", "unknown"),
        "used_fallback": bool(interpretation.get("unsupported_aspects")),
        "platforms_succeeded": response.get("platforms_searched", []),
        "platforms_failed": response.get("platforms_failed", []),
        "total_results": response.get("total", 0),
        "results_returned": len(results),
        "results_with_video_id": results_with_video_id,
        "keyword_in_title_pct": round(keyword_pct, 3),
        "latency_ms": round(elapsed_ms),
    }

    # Extract candidate info (cap at 20 per query)
    candidates = []
    for r in results[:20]:
        candidates.append({
            "platform": r.get("platform"),
            "video_id": r.get("video_id"),
            "creator_handle": r.get("creator_handle"),
            "title": r.get("title"),
            "description": (r.get("description") or "")[:200],
            "view_count": r.get("view_count"),
            "video_url": r.get("video_url"),
            "thumbnail_url": r.get("thumbnail_url"),
            "relevance_score": r.get("relevance_score"),
        })

    return {
        "query_text": curation_query.query,
        "platforms_param": curation_query.platforms,
        "rationale": curation_query.rationale,
        "expected_brands": curation_query.expected_brands,
        "expected_hook": curation_query.expected_hook,
        "expected_narrative": curation_query.expected_narrative,
        "metrics": metrics,
        "candidates": candidates,
    }


def _build_summary(query_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Build summary statistics from a list of query results."""
    all_candidates = []
    video_ids = set()
    platform_counts: dict[str, int] = {}

    for qr in query_results:
        for c in qr.get("candidates", []):
            all_candidates.append(c)
            vid = c.get("video_id")
            if vid:
                video_ids.add(f"{c.get('platform')}:{vid}")
            plat = c.get("platform")
            if plat:
                platform_counts[plat] = platform_counts.get(plat, 0) + 1

    return {
        "total_candidates": len(all_candidates),
        "unique_video_ids": len(video_ids),
        "platform_breakdown": platform_counts,
    }


# ---------------------------------------------------------------------------
# Helpers: run all queries for a spike
# ---------------------------------------------------------------------------


async def _run_spike_queries(
    search_service: Any,
    queries: list[CurationQuery],
    label: str,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Run a list of curation queries sequentially with rate limiting."""
    results = []
    for i, q in enumerate(queries):
        logger.info("[%s %d/%d] %s", label, i + 1, len(queries), q.query)
        result = await _run_query(search_service, q, limit=limit)
        results.append(result)
        logger.info(
            "  -> %d candidates, %dms",
            len(result.get("candidates", [])),
            result.get("metrics", {}).get("latency_ms", 0),
        )
        if i < len(queries) - 1:
            await asyncio.sleep(QUERY_DELAY)
    return results


def _log_and_write_report(
    query_results: list[dict[str, Any]],
    spike_name: str,
    report_path: Path,
    n_queries: int,
) -> int:
    """Log per-query summary, write report, return count of queries with results."""
    total_candidates = 0
    queries_with_results = 0
    for qr in query_results:
        n = len(qr.get("candidates", []))
        total_candidates += n
        if n > 0:
            queries_with_results += 1
        metrics = qr.get("metrics", {})
        status = "OK" if not qr.get("error") else f"ERROR: {qr['error']}"
        logger.info(
            "  [%s] %d results, confidence=%.2f, %dms — %s",
            qr["query_text"][:50],
            n,
            metrics.get("parse_confidence", 0),
            metrics.get("latency_ms", 0),
            status,
        )

    logger.info(
        "%s total: %d candidates from %d/%d queries",
        spike_name,
        total_candidates,
        queries_with_results,
        n_queries,
    )

    report = {
        "spike": spike_name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "queries": query_results,
        "summary": _build_summary(query_results),
    }
    write_spike_report(report_path, report)
    return queries_with_results


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.spike
@pytest.mark.external_api
@pytest.mark.gemini
@pytest.mark.slow
class TestSpike1BrandCuration:
    """Curate candidate videos for Spike 1 (Brand Exposure timestamp_end)."""

    async def test_curate_brand_videos(self, search_service):
        """Run 8 brand queries and write candidate report."""
        spike1_results = await _run_spike_queries(
            search_service, SPIKE1_BRAND_QUERIES, "Spike1", limit=20,
        )
        assert len(spike1_results) == len(SPIKE1_BRAND_QUERIES)

        queries_with_results = _log_and_write_report(
            spike1_results,
            "brand_exposure",
            REPORT_DIR / "spike1_candidates.json",
            len(SPIKE1_BRAND_QUERIES),
        )

        assert queries_with_results >= 1, (
            f"No queries returned results out of {len(SPIKE1_BRAND_QUERIES)}"
        )


@pytest.mark.spike
@pytest.mark.external_api
@pytest.mark.gemini
@pytest.mark.slow
class TestSpike2CreativeCuration:
    """Curate candidate videos for Spike 2 (Creative Pattern taxonomy)."""

    async def test_curate_creative_videos(self, search_service):
        """Run 18 creative pattern queries and write candidate report."""
        spike2_results = await _run_spike_queries(
            search_service, SPIKE2_CREATIVE_QUERIES, "Spike2", limit=15,
        )
        assert len(spike2_results) == len(SPIKE2_CREATIVE_QUERIES)

        queries_with_results = _log_and_write_report(
            spike2_results,
            "creative_patterns",
            REPORT_DIR / "spike2_candidates.json",
            len(SPIKE2_CREATIVE_QUERIES),
        )

        assert queries_with_results >= 1, (
            f"No queries returned results out of {len(SPIKE2_CREATIVE_QUERIES)}"
        )


@pytest.mark.spike
@pytest.mark.external_api
@pytest.mark.gemini
@pytest.mark.slow
class TestSearchQualitySummary:
    """Aggregate search quality metrics across all curation queries."""

    async def test_search_quality_report(self, search_service):
        """Compute and write aggregate search quality metrics."""
        # Run both spikes (or read from reports if already written)
        spike1_report = REPORT_DIR / "spike1_candidates.json"
        spike2_report = REPORT_DIR / "spike2_candidates.json"

        if spike1_report.exists() and spike2_report.exists():
            import json

            with open(spike1_report) as f:
                spike1_data = json.load(f)
            with open(spike2_report) as f:
                spike2_data = json.load(f)
            all_query_results = spike1_data["queries"] + spike2_data["queries"]
        else:
            spike1_results = await _run_spike_queries(
                search_service, SPIKE1_BRAND_QUERIES, "Spike1", limit=20,
            )
            spike2_results = await _run_spike_queries(
                search_service, SPIKE2_CREATIVE_QUERIES, "Spike2", limit=15,
            )
            all_query_results = spike1_results + spike2_results

        total_queries = len(all_query_results)
        confidences = []
        zero_result_queries = 0
        fallback_queries = 0
        latencies = []
        keyword_relevances = []
        platform_attempts: dict[str, int] = {}
        platform_failures: dict[str, int] = {}
        results_per_query = []

        for qr in all_query_results:
            metrics = qr.get("metrics", {})

            conf = metrics.get("parse_confidence")
            if conf is not None:
                confidences.append(conf)

            n_results = metrics.get("results_returned", 0)
            results_per_query.append(n_results)
            if n_results == 0:
                zero_result_queries += 1

            if metrics.get("used_fallback"):
                fallback_queries += 1

            latency = metrics.get("latency_ms")
            if latency is not None:
                latencies.append(latency)

            kw_pct = metrics.get("keyword_in_title_pct")
            if kw_pct is not None:
                keyword_relevances.append(kw_pct)

            for p in metrics.get("platforms_succeeded", []):
                platform_attempts[p] = platform_attempts.get(p, 0) + 1
            for p in metrics.get("platforms_failed", []):
                platform_attempts[p] = platform_attempts.get(p, 0) + 1
                platform_failures[p] = platform_failures.get(p, 0) + 1

        # Compute failure rates
        platform_failure_rate = {
            p: (
                platform_failures.get(p, 0) / platform_attempts[p]
                if platform_attempts[p]
                else 0
            )
            for p in platform_attempts
        }

        avg_confidence = (
            sum(confidences) / len(confidences) if confidences else 0
        )
        avg_latency = (
            sum(latencies) / len(latencies) if latencies else 0
        )
        avg_results = (
            sum(results_per_query) / len(results_per_query)
            if results_per_query
            else 0
        )
        avg_keyword = (
            sum(keyword_relevances) / len(keyword_relevances)
            if keyword_relevances
            else 0
        )

        summary = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_queries": total_queries,
            "avg_parse_confidence": round(avg_confidence, 3),
            "queries_with_zero_results": zero_result_queries,
            "queries_using_fallback": fallback_queries,
            "platform_failure_rate": {
                k: round(v, 3) for k, v in sorted(platform_failure_rate.items())
            },
            "platform_attempts": platform_attempts,
            "avg_results_per_query": round(avg_results, 1),
            "avg_keyword_relevance": round(avg_keyword, 3),
            "avg_latency_ms": round(avg_latency),
            "per_query_details": [
                {
                    "query": qr["query_text"],
                    "confidence": qr.get("metrics", {}).get("parse_confidence"),
                    "results": qr.get("metrics", {}).get("results_returned", 0),
                    "latency_ms": qr.get("metrics", {}).get("latency_ms"),
                    "error": qr.get("error"),
                }
                for qr in all_query_results
            ],
        }

        write_spike_report(REPORT_DIR / "search_quality_summary.json", summary)

        # Log key metrics
        logger.info("=== Search Quality Summary ===")
        logger.info("  Total queries: %d", total_queries)
        logger.info("  Avg parse confidence: %.3f", avg_confidence)
        logger.info("  Queries with zero results: %d", zero_result_queries)
        logger.info("  Queries using fallback: %d", fallback_queries)
        logger.info("  Avg results per query: %.1f", avg_results)
        logger.info("  Avg keyword relevance: %.3f", avg_keyword)
        logger.info("  Avg latency: %dms", avg_latency)
        for p, rate in sorted(platform_failure_rate.items()):
            logger.info("  %s failure rate: %.1f%%", p, rate * 100)

        # Soft assertions — only fail if pipeline is completely broken
        assert zero_result_queries < total_queries, (
            "All queries returned zero results — search pipeline may be broken"
        )

        # Log confidence as a finding (observed: 0.30 avg)
        if avg_confidence > 0 and avg_confidence < 0.5:
            logger.warning(
                "Low avg parse confidence (%.3f) — parser may need tuning "
                "for natural language curation queries",
                avg_confidence,
            )
