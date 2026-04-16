"""Validation spike: Does the creative pattern taxonomy produce >=70% consistent results?

Run with: RUN_GEMINI=1 pytest tests/spikes/spike_creative_patterns/ -v
"""

from __future__ import annotations

import asyncio
import logging
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any

import pytest

from ..conftest import SpikeRunner, write_spike_report
from ..video_sets import CREATIVE_PATTERN_VIDEOS
from .prompt import CREATIVE_PATTERN_PROMPT, CREATIVE_PATTERN_SYSTEM
from .schemas import CreativePatternAnalysis, CreativePatterns

logger = logging.getLogger(__name__)

REPORT_PATH = Path(__file__).parent / "spike_results.json"

# Fields to check for self-consistency
CONSISTENCY_FIELDS = [
    "hook_type",
    "narrative_structure",
    "cta_type",
    "cta_placement",
    "pacing",
    "music_usage",
    "text_overlay_density",
]

# Corresponding confidence fields
CONFIDENCE_FIELDS = {
    "hook_type": "hook_confidence",
    "narrative_structure": "narrative_confidence",
    "cta_type": "cta_confidence",
    "pacing": "pacing_confidence",
    "music_usage": "music_confidence",
    "text_overlay_density": "text_overlay_confidence",
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def _require_videos():
    """Skip entire module if no creative pattern videos are configured."""
    if not CREATIVE_PATTERN_VIDEOS:
        pytest.skip("No creative pattern videos configured in video_sets.py")


async def _process_creative_video(
    video,
    fetchers,
    r2_storage,
    spike_runner: SpikeRunner,
) -> dict[str, Any]:
    """Fetch and analyze a single creative video 3x (parallelizable unit)."""
    from src.common.enums import Platform

    platform = Platform(video.platform)
    fetcher = fetchers[platform]

    try:
        await fetcher.fetch_video(platform, video.video_id)
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

    temp_path = await r2_storage.download_to_temp(platform, video.video_id)
    try:
        run_results = await spike_runner.run_video_n_times(
            video_path=temp_path,
            prompt=CREATIVE_PATTERN_PROMPT,
            system=CREATIVE_PATTERN_SYSTEM,
            schema_cls=CreativePatternAnalysis,
            n=3,
            temperature=0.3,
        )
        return {
            "video": {
                "platform": video.platform,
                "video_id": video.video_id,
                "description": video.description,
                "expected_hook": video.expected_hook,
                "expected_narrative": video.expected_narrative,
            },
            "runs": [
                {"analysis": r.model_dump(), "metadata": m}
                for r, m in run_results
            ],
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
    """Run creative pattern prompt 3x against all configured videos.

    Parallelized via asyncio.gather — concurrency bounded by SpikeRunner's semaphore.
    Returns list of dicts, each containing:
        - video: SpikeVideo metadata
        - runs: list of 3 (CreativePatternAnalysis.model_dump(), metadata) tuples
        - or error: str if all runs failed
    """
    tasks = [
        _process_creative_video(video, fetchers, r2_storage, spike_runner)
        for video in CREATIVE_PATTERN_VIDEOS
    ]
    return list(await asyncio.gather(*tasks))


def _successful_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter to results that have all 3 runs."""
    return [r for r in results if "runs" in r and len(r["runs"]) == 3]


def _get_field_values(
    result: dict[str, Any], field: str
) -> list[str]:
    """Get a field value from all 3 runs for a single video."""
    return [run["analysis"]["patterns"][field] for run in result["runs"]]


def _mode(values: list[str]) -> str:
    """Return the most common value."""
    return Counter(values).most_common(1)[0][0]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.spike
@pytest.mark.gemini
@pytest.mark.slow
class TestCreativePatternSanity:
    """Smoke test with the local test video."""

    async def test_single_video_sanity(
        self, spike_runner: SpikeRunner, test_video_path: Path
    ):
        """Creative pattern prompt + schema produces valid output."""
        analysis, meta = await spike_runner.run_video(
            video_path=test_video_path,
            prompt=CREATIVE_PATTERN_PROMPT,
            system=CREATIVE_PATTERN_SYSTEM,
            schema_cls=CreativePatternAnalysis,
            temperature=0.3,
        )

        assert isinstance(analysis, CreativePatternAnalysis)
        assert isinstance(analysis.patterns, CreativePatterns)
        assert meta["token_count"] > 0
        logger.info(
            "Sanity: hook=%s (%.2f), narrative=%s (%.2f), %d tokens",
            analysis.patterns.hook_type,
            analysis.patterns.hook_confidence,
            analysis.patterns.narrative_structure,
            analysis.patterns.narrative_confidence,
            meta["token_count"],
        )


@pytest.mark.spike
@pytest.mark.gemini
@pytest.mark.slow
class TestSelfConsistency:
    """Validate taxonomy self-consistency across 3 runs per video."""

    async def test_self_consistency(self, all_results: list[dict[str, Any]]):
        """hook_type and narrative_structure agreement >= 70% across videos."""
        successful = _successful_results(all_results)
        if not successful:
            pytest.skip("No successful video analyses")

        field_agreement: dict[str, list[bool]] = {
            f: [] for f in CONSISTENCY_FIELDS
        }

        for result in successful:
            for field in CONSISTENCY_FIELDS:
                values = _get_field_values(result, field)
                # All 3 runs agree
                agrees = len(set(values)) == 1
                field_agreement[field].append(agrees)

        logger.info("=== Self-consistency rates ===")
        for field, agreements in field_agreement.items():
            rate = sum(agreements) / len(agreements) if agreements else 0
            logger.info(
                "  %s: %d/%d (%.1f%%)",
                field,
                sum(agreements),
                len(agreements),
                rate * 100,
            )

        # Primary assertions
        n = len(successful)
        hook_rate = sum(field_agreement["hook_type"]) / n
        narrative_rate = sum(field_agreement["narrative_structure"]) / n

        assert hook_rate >= 0.70, (
            f"hook_type self-consistency {hook_rate:.1%} < 70% threshold"
        )
        assert narrative_rate >= 0.70, (
            f"narrative_structure self-consistency {narrative_rate:.1%} < 70%"
        )


@pytest.mark.spike
@pytest.mark.gemini
@pytest.mark.slow
class TestDistribution:
    """Validate taxonomy captures real-world variety."""

    async def test_distribution_not_degenerate(
        self, all_results: list[dict[str, Any]]
    ):
        """No single category dominates; taxonomy captures variety."""
        successful = _successful_results(all_results)
        if len(successful) < 10:
            pytest.skip("Need at least 10 videos for distribution analysis")

        # Use first run from each video
        hooks = [_get_field_values(r, "hook_type")[0] for r in successful]
        narratives = [
            _get_field_values(r, "narrative_structure")[0] for r in successful
        ]

        hook_counts = Counter(hooks)
        narrative_counts = Counter(narratives)
        n = len(successful)

        logger.info("=== Distribution ===")
        logger.info("Hook types: %s", dict(hook_counts.most_common()))
        logger.info("Narrative types: %s", dict(narrative_counts.most_common()))

        # No single hook captures > 50%
        max_hook_pct = hook_counts.most_common(1)[0][1] / n
        assert max_hook_pct <= 0.50, (
            f"Hook type '{hook_counts.most_common(1)[0][0]}' captures "
            f"{max_hook_pct:.0%} of videos (>50%)"
        )

        # No single narrative captures > 40%
        max_narrative_pct = narrative_counts.most_common(1)[0][1] / n
        assert max_narrative_pct <= 0.40, (
            f"Narrative '{narrative_counts.most_common(1)[0][0]}' captures "
            f"{max_narrative_pct:.0%} of videos (>40%)"
        )

        # At least 4 distinct hook types
        assert len(hook_counts) >= 4, (
            f"Only {len(hook_counts)} distinct hook types observed (need >=4)"
        )

        # At least 5 distinct narrative structures
        assert len(narrative_counts) >= 5, (
            f"Only {len(narrative_counts)} distinct narrative types (need >=5)"
        )


@pytest.mark.spike
@pytest.mark.gemini
@pytest.mark.slow
class TestConfidenceCalibration:
    """Validate that confidence correlates with consistency."""

    async def test_confidence_calibration(
        self, all_results: list[dict[str, Any]]
    ):
        """High confidence should correlate with agreement across runs."""
        successful = _successful_results(all_results)
        if len(successful) < 10:
            pytest.skip("Need at least 10 videos for calibration analysis")

        agree_confidences: list[float] = []
        disagree_confidences: list[float] = []

        for result in successful:
            for field in ["hook_type", "narrative_structure"]:
                values = _get_field_values(result, field)
                conf_field = CONFIDENCE_FIELDS[field]
                confs = [
                    run["analysis"]["patterns"][conf_field]
                    for run in result["runs"]
                ]
                avg_conf = mean(confs)

                if len(set(values)) == 1:
                    agree_confidences.append(avg_conf)
                else:
                    disagree_confidences.append(avg_conf)

        if agree_confidences:
            avg_agree = mean(agree_confidences)
            logger.info(
                "Avg confidence when runs agree: %.3f (%d cases)",
                avg_agree,
                len(agree_confidences),
            )
        if disagree_confidences:
            avg_disagree = mean(disagree_confidences)
            logger.info(
                "Avg confidence when runs disagree: %.3f (%d cases)",
                avg_disagree,
                len(disagree_confidences),
            )

        # Informational — log but don't hard-fail on calibration
        if agree_confidences and disagree_confidences:
            avg_agree = mean(agree_confidences)
            avg_disagree = mean(disagree_confidences)
            if avg_agree > avg_disagree:
                logger.info(
                    "Confidence is well-calibrated (agree=%.3f > disagree=%.3f)",
                    avg_agree,
                    avg_disagree,
                )
            else:
                logger.warning(
                    "Confidence is poorly calibrated (agree=%.3f <= disagree=%.3f)",
                    avg_agree,
                    avg_disagree,
                )


@pytest.mark.spike
@pytest.mark.gemini
@pytest.mark.slow
class TestGroundTruthAccuracy:
    """Validate against user-provided ground truth labels."""

    async def test_ground_truth_accuracy(
        self, all_results: list[dict[str, Any]]
    ):
        """>=70% match on hook_type and narrative_structure vs ground truth."""
        successful = _successful_results(all_results)

        # Filter to videos with ground truth labels
        labeled_hook = [
            r for r in successful if r["video"].get("expected_hook")
        ]
        labeled_narrative = [
            r for r in successful if r["video"].get("expected_narrative")
        ]

        if not labeled_hook and not labeled_narrative:
            pytest.skip("No ground truth labels provided in video_sets.py")

        if labeled_hook:
            correct = 0
            for r in labeled_hook:
                values = _get_field_values(r, "hook_type")
                predicted = _mode(values)
                expected = r["video"]["expected_hook"]
                if predicted == expected:
                    correct += 1
                else:
                    logger.info(
                        "Hook mismatch: %s — predicted=%s, expected=%s",
                        r["video"]["video_id"],
                        predicted,
                        expected,
                    )
            rate = correct / len(labeled_hook)
            logger.info(
                "Hook accuracy: %d/%d (%.1f%%)",
                correct,
                len(labeled_hook),
                rate * 100,
            )
            assert rate >= 0.70, (
                f"Hook accuracy {rate:.1%} < 70% ({correct}/{len(labeled_hook)})"
            )

        if labeled_narrative:
            correct = 0
            for r in labeled_narrative:
                values = _get_field_values(r, "narrative_structure")
                predicted = _mode(values)
                expected = r["video"]["expected_narrative"]
                if predicted == expected:
                    correct += 1
                else:
                    logger.info(
                        "Narrative mismatch: %s — predicted=%s, expected=%s",
                        r["video"]["video_id"],
                        predicted,
                        expected,
                    )
            rate = correct / len(labeled_narrative)
            logger.info(
                "Narrative accuracy: %d/%d (%.1f%%)",
                correct,
                len(labeled_narrative),
                rate * 100,
            )
            assert rate >= 0.70, (
                f"Narrative accuracy {rate:.1%} < 70% "
                f"({correct}/{len(labeled_narrative)})"
            )


@pytest.mark.spike
@pytest.mark.gemini
@pytest.mark.slow
class TestGenerateReport:
    """Generate comprehensive spike report."""

    async def test_generate_report(self, all_results: list[dict[str, Any]]):
        """Write results to JSON for review."""
        successful = _successful_results(all_results)

        # Self-consistency per field
        consistency: dict[str, float] = {}
        for field in CONSISTENCY_FIELDS:
            agreements = []
            for r in successful:
                values = _get_field_values(r, field)
                agreements.append(len(set(values)) == 1)
            consistency[field] = (
                sum(agreements) / len(agreements) if agreements else 0
            )

        # Distribution from first runs
        distributions: dict[str, dict[str, int]] = {}
        for field in CONSISTENCY_FIELDS:
            values = [_get_field_values(r, field)[0] for r in successful]
            distributions[field] = dict(Counter(values).most_common())

        report = {
            "spike": "creative_pattern_taxonomy",
            "summary": {
                "videos_tested": len(all_results),
                "videos_succeeded": len(successful),
                "runs_per_video": 3,
            },
            "self_consistency": consistency,
            "distributions": distributions,
            "pass_criteria": {
                "hook_type_consistency_>=70%": consistency.get("hook_type", 0) >= 0.70,
                "narrative_consistency_>=70%": (
                    consistency.get("narrative_structure", 0) >= 0.70
                ),
            },
            "raw_results": all_results,
        }

        write_spike_report(REPORT_PATH, report)
        logger.info("Report written to %s", REPORT_PATH)
        for field, rate in consistency.items():
            logger.info("  %s consistency: %.1f%%", field, rate * 100)
