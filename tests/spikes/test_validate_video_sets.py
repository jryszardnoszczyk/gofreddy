"""Validate video_sets.py ground truth labels using Gemini video analysis.

Fetches each video, runs it through Gemini, and compares the AI classification
against our expected labels. Outputs a JSON report with mismatches.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

import pytest

from src.common.enums import Platform

from .conftest import SpikeRunner
from .spike_brand_timestamp_end.prompt import (
    SPIKE_BRAND_DETECTION_PROMPT,
    SPIKE_BRAND_DETECTION_SYSTEM,
)
from .spike_brand_timestamp_end.schemas import ExtendedBrandAnalysis
from .spike_creative_patterns.prompt import (
    CREATIVE_PATTERN_PROMPT,
    CREATIVE_PATTERN_SYSTEM,
)
from .spike_creative_patterns.schemas import CreativePatternAnalysis
from .video_sets import BRAND_EXPOSURE_VIDEOS, CREATIVE_PATTERN_VIDEOS, SpikeVideo

logger = logging.getLogger(__name__)

REPORT_DIR = Path(__file__).parent / "curation_reports"


async def _fetch_and_analyze_brand(
    video: SpikeVideo,
    fetchers: dict,
    r2_storage: Any,
    spike_runner: SpikeRunner,
) -> dict[str, Any]:
    """Fetch one brand video and run brand detection."""
    platform = Platform(video.platform)
    fetcher = fetchers[platform]
    try:
        await fetcher.fetch_video(platform, video.video_id)
        temp_path = await r2_storage.download_to_temp(platform, video.video_id)
    except Exception as e:
        return {
            "video_id": video.video_id,
            "platform": video.platform,
            "status": "fetch_failed",
            "error": str(e),
        }

    try:
        analysis, meta = await spike_runner.run_video(
            video_path=temp_path,
            prompt=SPIKE_BRAND_DETECTION_PROMPT,
            system=SPIKE_BRAND_DETECTION_SYSTEM,
            schema_cls=ExtendedBrandAnalysis,
            temperature=0.3,
        )
        detected_brands = sorted(
            {m.brand_name.lower() for m in analysis.brand_mentions}
        )
        expected_brands = sorted({b.lower() for b in video.expected_brands})
        matched = set(detected_brands) & set(expected_brands)
        missed = set(expected_brands) - set(detected_brands)
        extra = set(detected_brands) - set(expected_brands)

        return {
            "video_id": video.video_id,
            "platform": video.platform,
            "description": video.description,
            "status": "ok",
            "expected_brands": video.expected_brands,
            "detected_brands": detected_brands,
            "matched": sorted(matched),
            "missed_expected": sorted(missed),
            "extra_detected": sorted(extra),
            "has_sponsorship_signals": analysis.has_sponsorship_signals,
            "primary_brand": analysis.primary_brand,
            "mention_count": len(analysis.brand_mentions),
            "token_count": meta.get("token_count", 0),
        }
    except Exception as e:
        return {
            "video_id": video.video_id,
            "platform": video.platform,
            "status": "analysis_failed",
            "error": str(e),
        }
    finally:
        temp_path.unlink(missing_ok=True)


async def _fetch_and_analyze_creative(
    video: SpikeVideo,
    fetchers: dict,
    r2_storage: Any,
    spike_runner: SpikeRunner,
) -> dict[str, Any]:
    """Fetch one creative pattern video and run classification."""
    platform = Platform(video.platform)
    fetcher = fetchers[platform]
    try:
        await fetcher.fetch_video(platform, video.video_id)
        temp_path = await r2_storage.download_to_temp(platform, video.video_id)
    except Exception as e:
        return {
            "video_id": video.video_id,
            "platform": video.platform,
            "status": "fetch_failed",
            "error": str(e),
        }

    try:
        analysis, meta = await spike_runner.run_video(
            video_path=temp_path,
            prompt=CREATIVE_PATTERN_PROMPT,
            system=CREATIVE_PATTERN_SYSTEM,
            schema_cls=CreativePatternAnalysis,
            temperature=0.3,
        )
        p = analysis.patterns
        hook_match = p.hook_type == video.expected_hook
        narrative_match = p.narrative_structure == video.expected_narrative

        return {
            "video_id": video.video_id,
            "platform": video.platform,
            "description": video.description,
            "status": "ok",
            "expected_hook": video.expected_hook,
            "detected_hook": p.hook_type,
            "hook_match": hook_match,
            "hook_confidence": p.hook_confidence,
            "expected_narrative": video.expected_narrative,
            "detected_narrative": p.narrative_structure,
            "narrative_match": narrative_match,
            "narrative_confidence": p.narrative_confidence,
            "pacing": p.pacing,
            "music_usage": p.music_usage,
            "token_count": meta.get("token_count", 0),
        }
    except Exception as e:
        return {
            "video_id": video.video_id,
            "platform": video.platform,
            "status": "analysis_failed",
            "error": str(e),
        }
    finally:
        temp_path.unlink(missing_ok=True)


@pytest.mark.spike
@pytest.mark.gemini
@pytest.mark.external_api
@pytest.mark.slow
class TestValidateBrandVideoSets:
    """Validate brand video ground truth labels against Gemini analysis."""

    @pytest.fixture(autouse=True)
    def _skip_if_empty(self):
        if not BRAND_EXPOSURE_VIDEOS:
            pytest.skip("BRAND_EXPOSURE_VIDEOS is empty")

    @pytest.mark.asyncio
    async def test_validate_brand_labels(
        self, spike_runner, fetchers, r2_storage
    ):
        tasks = [
            _fetch_and_analyze_brand(video, fetchers, r2_storage, spike_runner)
            for video in BRAND_EXPOSURE_VIDEOS
        ]
        results = await asyncio.gather(*tasks)

        # Write report
        ok_results = [r for r in results if r["status"] == "ok"]
        failed = [r for r in results if r["status"] != "ok"]
        total_matched = sum(len(r["matched"]) for r in ok_results)
        total_expected = sum(len(r["expected_brands"]) for r in ok_results)
        total_missed = sum(len(r["missed_expected"]) for r in ok_results)
        total_extra = sum(len(r["extra_detected"]) for r in ok_results)

        report = {
            "summary": {
                "total_videos": len(BRAND_EXPOSURE_VIDEOS),
                "successfully_analyzed": len(ok_results),
                "fetch_or_analysis_failed": len(failed),
                "brand_recall": round(total_matched / max(total_expected, 1), 3),
                "total_expected_brands": total_expected,
                "total_matched": total_matched,
                "total_missed": total_missed,
                "total_extra_detected": total_extra,
            },
            "results": results,
        }

        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        report_path = REPORT_DIR / "brand_validation_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        logger.info("Brand validation report: %s", report_path)

        # Print summary
        print(f"\n{'='*60}")
        print(f"BRAND VALIDATION SUMMARY")
        print(f"{'='*60}")
        print(f"Videos analyzed: {len(ok_results)}/{len(BRAND_EXPOSURE_VIDEOS)}")
        print(f"Brand recall: {report['summary']['brand_recall']:.1%}")
        print(f"Matched: {total_matched}, Missed: {total_missed}, Extra: {total_extra}")
        if failed:
            print(f"\nFailed videos:")
            for f_ in failed:
                print(f"  - {f_['platform']}/{f_['video_id']}: {f_['error']}")
        mismatches = [r for r in ok_results if r["missed_expected"]]
        if mismatches:
            print(f"\nVideos with missed brands:")
            for m in mismatches:
                print(f"  - {m['platform']}/{m['video_id']}: missed {m['missed_expected']}")
        print(f"{'='*60}\n")


@pytest.mark.spike
@pytest.mark.gemini
@pytest.mark.external_api
@pytest.mark.slow
class TestValidateCreativeVideoSets:
    """Validate creative pattern ground truth labels against Gemini analysis."""

    @pytest.fixture(autouse=True)
    def _skip_if_empty(self):
        if not CREATIVE_PATTERN_VIDEOS:
            pytest.skip("CREATIVE_PATTERN_VIDEOS is empty")

    @pytest.mark.asyncio
    async def test_validate_creative_labels(
        self, spike_runner, fetchers, r2_storage
    ):
        tasks = [
            _fetch_and_analyze_creative(video, fetchers, r2_storage, spike_runner)
            for video in CREATIVE_PATTERN_VIDEOS
        ]
        results = await asyncio.gather(*tasks)

        # Write report
        ok_results = [r for r in results if r["status"] == "ok"]
        failed = [r for r in results if r["status"] != "ok"]
        hook_matches = sum(1 for r in ok_results if r["hook_match"])
        narrative_matches = sum(1 for r in ok_results if r["narrative_match"])
        n_ok = max(len(ok_results), 1)

        report = {
            "summary": {
                "total_videos": len(CREATIVE_PATTERN_VIDEOS),
                "successfully_analyzed": len(ok_results),
                "fetch_or_analysis_failed": len(failed),
                "hook_accuracy": round(hook_matches / n_ok, 3),
                "narrative_accuracy": round(narrative_matches / n_ok, 3),
                "hook_matches": hook_matches,
                "narrative_matches": narrative_matches,
            },
            "results": results,
        }

        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        report_path = REPORT_DIR / "creative_validation_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        logger.info("Creative validation report: %s", report_path)

        # Print summary
        print(f"\n{'='*60}")
        print(f"CREATIVE PATTERN VALIDATION SUMMARY")
        print(f"{'='*60}")
        print(f"Videos analyzed: {len(ok_results)}/{len(CREATIVE_PATTERN_VIDEOS)}")
        print(f"Hook accuracy: {hook_matches}/{len(ok_results)} ({hook_matches/n_ok:.1%})")
        print(f"Narrative accuracy: {narrative_matches}/{len(ok_results)} ({narrative_matches/n_ok:.1%})")
        if failed:
            print(f"\nFailed videos:")
            for f_ in failed:
                print(f"  - {f_['platform']}/{f_['video_id']}: {f_['error']}")
        mismatches = [r for r in ok_results if not r["hook_match"] or not r["narrative_match"]]
        if mismatches:
            print(f"\nLabel mismatches ({len(mismatches)} videos):")
            for m in mismatches:
                parts = []
                if not m["hook_match"]:
                    parts.append(f"hook: expected={m['expected_hook']} got={m['detected_hook']} (conf={m['hook_confidence']:.2f})")
                if not m["narrative_match"]:
                    parts.append(f"narrative: expected={m['expected_narrative']} got={m['detected_narrative']} (conf={m['narrative_confidence']:.2f})")
                print(f"  - {m['platform']}/{m['video_id']}: {'; '.join(parts)}")
        print(f"{'='*60}\n")
