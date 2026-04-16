"""Validation spike: Can Gemini reliably extract timestamp_end for brand mentions?

Run with: RUN_GEMINI=1 pytest tests/spikes/spike_brand_timestamp_end/ -v
"""

from __future__ import annotations

import asyncio
import logging
from collections import Counter
from pathlib import Path
from typing import Any

import pytest

from src.common.timestamps import mss_to_seconds

from ..conftest import SpikeRunner, write_spike_report
from ..video_sets import BRAND_EXPOSURE_VIDEOS
from .prompt import SPIKE_BRAND_DETECTION_PROMPT, SPIKE_BRAND_DETECTION_SYSTEM
from .schemas import ExtendedBrandAnalysis, ExtendedBrandMention

logger = logging.getLogger(__name__)

REPORT_PATH = Path(__file__).parent / "spike_results.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mentions_with_timestamps(
    mentions: list[ExtendedBrandMention],
) -> list[ExtendedBrandMention]:
    """Filter to mentions that have at least timestamp_start."""
    return [m for m in mentions if m.timestamp_start is not None]


def _has_valid_end(mention: ExtendedBrandMention) -> bool:
    """Check if mention has valid timestamp_end > timestamp_start."""
    if mention.timestamp_end is None or mention.timestamp_start is None:
        return False
    start = mss_to_seconds(mention.timestamp_start)
    end = mss_to_seconds(mention.timestamp_end)
    if start is None or end is None:
        return False
    return end > start


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def _require_videos():
    """Skip entire module if no brand exposure videos are configured."""
    if not BRAND_EXPOSURE_VIDEOS:
        pytest.skip("No brand exposure videos configured in video_sets.py")


async def _process_brand_video(
    video,
    fetchers,
    r2_storage,
    spike_runner: SpikeRunner,
) -> dict[str, Any]:
    """Fetch and analyze a single brand video (parallelizable unit)."""
    from src.common.enums import Platform

    platform = Platform(video.platform)
    fetcher = fetchers[platform]

    try:
        await fetcher.fetch_video(platform, video.video_id)
        temp_path = await r2_storage.download_to_temp(platform, video.video_id)
    except Exception as e:
        logger.error("Failed to fetch %s/%s: %s", video.platform, video.video_id, e)
        return {
            "video": {
                "platform": video.platform,
                "video_id": video.video_id,
                "description": video.description,
            },
            "error": f"fetch_failed: {e}",
        }

    try:
        analysis, meta = await spike_runner.run_video(
            video_path=temp_path,
            prompt=SPIKE_BRAND_DETECTION_PROMPT,
            system=SPIKE_BRAND_DETECTION_SYSTEM,
            schema_cls=ExtendedBrandAnalysis,
            temperature=0.3,
        )
        return {
            "video": {
                "platform": video.platform,
                "video_id": video.video_id,
                "description": video.description,
                "expected_brands": video.expected_brands,
            },
            "analysis": analysis.model_dump(),
            "metadata": meta,
        }
    except Exception as e:
        logger.error("Failed to analyze %s/%s: %s", video.platform, video.video_id, e)
        return {
            "video": {
                "platform": video.platform,
                "video_id": video.video_id,
                "description": video.description,
            },
            "error": str(e),
        }
    finally:
        temp_path.unlink(missing_ok=True)


@pytest.fixture(scope="module")
async def all_results(
    spike_runner: SpikeRunner,
    fetchers,
    r2_storage,
    _require_videos,
) -> list[dict[str, Any]]:
    """Run the spike prompt against all configured brand exposure videos.

    Downloads each video (or uses R2 cache), runs the modified prompt,
    and collects all results for subsequent test assertions.
    Parallelized via asyncio.gather — concurrency bounded by SpikeRunner's semaphore.
    """
    tasks = [
        _process_brand_video(video, fetchers, r2_storage, spike_runner)
        for video in BRAND_EXPOSURE_VIDEOS
    ]
    return list(await asyncio.gather(*tasks))


def _all_mentions(
    results: list[dict[str, Any]],
) -> list[ExtendedBrandMention]:
    """Extract all brand mentions from results."""
    mentions = []
    for r in results:
        if "error" in r:
            continue
        for m_dict in r["analysis"]["brand_mentions"]:
            mentions.append(ExtendedBrandMention.model_validate(m_dict))
    return mentions


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.spike
@pytest.mark.gemini
@pytest.mark.slow
class TestTimestampEndSanity:
    """Smoke test with the local test video (no curated videos needed)."""

    async def test_single_video_sanity(
        self, spike_runner: SpikeRunner, test_video_path: Path
    ):
        """Modified prompt + schema produces valid ExtendedBrandAnalysis."""
        analysis, meta = await spike_runner.run_video(
            video_path=test_video_path,
            prompt=SPIKE_BRAND_DETECTION_PROMPT,
            system=SPIKE_BRAND_DETECTION_SYSTEM,
            schema_cls=ExtendedBrandAnalysis,
            temperature=0.3,
        )

        assert isinstance(analysis, ExtendedBrandAnalysis)
        assert analysis.overall_confidence >= 0.0
        assert meta["token_count"] > 0
        logger.info(
            "Sanity test passed: %d brand mentions, %d tokens",
            len(analysis.brand_mentions),
            meta["token_count"],
        )


@pytest.mark.spike
@pytest.mark.gemini
@pytest.mark.slow
class TestTimestampEndCompleteness:
    """Validate that timestamp_end is populated for most mentions."""

    async def test_timestamp_end_completeness(
        self, all_results: list[dict[str, Any]]
    ):
        """>=60% of mentions with timestamp_start should also have timestamp_end."""
        mentions = _all_mentions(all_results)
        with_start = _mentions_with_timestamps(mentions)

        if not with_start:
            pytest.skip("No mentions with timestamp_start found")

        with_both = [m for m in with_start if m.timestamp_end is not None]
        rate = len(with_both) / len(with_start)

        logger.info(
            "Completeness: %d/%d mentions have timestamp_end (%.1f%%)",
            len(with_both),
            len(with_start),
            rate * 100,
        )

        assert rate >= 0.60, (
            f"timestamp_end fill rate {rate:.1%} is below 60% threshold. "
            f"{len(with_both)}/{len(with_start)} mentions."
        )


@pytest.mark.spike
@pytest.mark.gemini
@pytest.mark.slow
class TestTimestampEndValidity:
    """Validate that timestamp_end values make sense."""

    async def test_timestamp_end_after_start(
        self, all_results: list[dict[str, Any]]
    ):
        """All timestamp_end values must be > timestamp_start."""
        mentions = _all_mentions(all_results)
        with_both = [
            m
            for m in mentions
            if m.timestamp_start is not None and m.timestamp_end is not None
        ]

        if not with_both:
            pytest.skip("No mentions with both timestamps found")

        violations = []
        for m in with_both:
            start = mss_to_seconds(m.timestamp_start)
            end = mss_to_seconds(m.timestamp_end)
            if start is not None and end is not None and end <= start:
                violations.append({
                    "brand": m.brand_name,
                    "start": m.timestamp_start,
                    "end": m.timestamp_end,
                })

        assert not violations, (
            f"{len(violations)} mentions have timestamp_end <= timestamp_start: "
            f"{violations[:5]}"
        )

    async def test_no_extreme_durations(
        self, all_results: list[dict[str, Any]]
    ):
        """No single brand mention should span > 300 seconds (5 min)."""
        mentions = _all_mentions(all_results)
        extreme = []
        for m in mentions:
            if m.timestamp_start is None or m.timestamp_end is None:
                continue
            start = mss_to_seconds(m.timestamp_start)
            end = mss_to_seconds(m.timestamp_end)
            if start is not None and end is not None:
                duration = end - start
                if duration > 300:
                    extreme.append({
                        "brand": m.brand_name,
                        "start": m.timestamp_start,
                        "end": m.timestamp_end,
                        "duration_s": duration,
                    })

        if extreme:
            logger.warning(
                "Found %d mentions with >300s duration: %s",
                len(extreme),
                extreme[:5],
            )
        # Warning, not hard failure — some background logos may genuinely
        # be visible for the entire video
        assert len(extreme) <= len(mentions) * 0.2, (
            f"Too many extreme durations: {len(extreme)}/{len(mentions)} (>20%)"
        )


@pytest.mark.spike
@pytest.mark.gemini
@pytest.mark.slow
class TestTimestampEndBySource:
    """Break down timestamp_end accuracy by detection source."""

    async def test_per_source_completeness(
        self, all_results: list[dict[str, Any]]
    ):
        """Report timestamp_end fill rate per detection source."""
        mentions = _all_mentions(all_results)
        with_start = _mentions_with_timestamps(mentions)

        by_source: dict[str, dict[str, int]] = {}
        for m in with_start:
            source = m.detection_source.value
            if source not in by_source:
                by_source[source] = {"total": 0, "with_end": 0}
            by_source[source]["total"] += 1
            if m.timestamp_end is not None:
                by_source[source]["with_end"] += 1

        logger.info("=== timestamp_end fill rate by detection source ===")
        for source, counts in sorted(by_source.items()):
            rate = counts["with_end"] / counts["total"] if counts["total"] else 0
            logger.info(
                "  %s: %d/%d (%.1f%%)",
                source,
                counts["with_end"],
                counts["total"],
                rate * 100,
            )

        # Speech should have highest fill rate
        if "speech" in by_source and by_source["speech"]["total"] >= 3:
            speech_rate = (
                by_source["speech"]["with_end"] / by_source["speech"]["total"]
            )
            logger.info("Speech fill rate: %.1f%%", speech_rate * 100)
            # Informational — no hard assertion on per-source rates


@pytest.mark.spike
@pytest.mark.gemini
@pytest.mark.slow
class TestGenerateReport:
    """Generate the final spike report."""

    async def test_generate_report(self, all_results: list[dict[str, Any]]):
        """Write comprehensive results to JSON for review."""
        mentions = _all_mentions(all_results)
        with_start = _mentions_with_timestamps(mentions)
        with_both = [m for m in with_start if m.timestamp_end is not None]
        valid_end = [m for m in with_both if _has_valid_end(m)]

        # Per-source breakdown
        source_counts: Counter[str] = Counter()
        source_with_end: Counter[str] = Counter()
        for m in with_start:
            source_counts[m.detection_source.value] += 1
            if m.timestamp_end is not None:
                source_with_end[m.detection_source.value] += 1

        report = {
            "spike": "brand_exposure_timestamp_end",
            "summary": {
                "videos_tested": len(all_results),
                "videos_succeeded": sum(
                    1 for r in all_results if "error" not in r
                ),
                "total_mentions": len(mentions),
                "mentions_with_start": len(with_start),
                "mentions_with_both": len(with_both),
                "mentions_with_valid_end": len(valid_end),
                "completeness_rate": (
                    len(with_both) / len(with_start) if with_start else 0
                ),
                "validity_rate": (
                    len(valid_end) / len(with_both) if with_both else 0
                ),
            },
            "per_source": {
                source: {
                    "total": source_counts[source],
                    "with_end": source_with_end[source],
                    "rate": (
                        source_with_end[source] / source_counts[source]
                        if source_counts[source]
                        else 0
                    ),
                }
                for source in sorted(source_counts)
            },
            "pass_criteria": {
                "completeness_>=60%": (
                    len(with_both) / len(with_start) >= 0.60
                    if with_start
                    else None
                ),
                "all_end_after_start": (
                    len(valid_end) == len(with_both) if with_both else None
                ),
            },
            "raw_results": all_results,
        }

        write_spike_report(REPORT_PATH, report)
        logger.info(
            "Report: completeness=%.1f%%, validity=%.1f%%",
            report["summary"]["completeness_rate"] * 100,
            report["summary"]["validity_rate"] * 100,
        )
