"""Brand exposure analytics — interval-merge and aggregation.

Computes per-brand screen time, source/sentiment/context breakdowns,
and multi-video campaign aggregation from timestamped brand mentions.
"""

from __future__ import annotations

from ..common.timestamps import mss_to_seconds
from ..schemas import (
    BrandAnalysis,
    BrandExposureSummary,
    BrandMention,
    MultiVideoBrandExposure,
)


def merge_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Merge overlapping [start, end) intervals. Returns sorted, non-overlapping list."""
    if not intervals:
        return []
    sorted_ivs = sorted(intervals)
    merged = [sorted_ivs[0]]
    for start, end in sorted_ivs[1:]:
        if start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def _mention_to_interval(mention: BrandMention) -> tuple[int, int]:
    """Convert brand mention timestamps to [start, end) interval in seconds.

    Null timestamps → point event at second 0 with 1-second duration.
    Null timestamp_end → point event (1-second duration from start).
    """
    start = mss_to_seconds(mention.timestamp_start) or 0
    end = mss_to_seconds(mention.timestamp_end)
    if end is None or end <= start:
        end = start + 1  # Point event = 1 second
    return (start, end)


def compute_brand_exposure(brand_analysis: BrandAnalysis) -> dict[str, BrandExposureSummary]:
    """Compute per-brand exposure from brand mentions.

    Groups mentions by brand_name (case-insensitive), computes:
    - total_mentions: count of mentions
    - total_screen_time_seconds: interval-merged duration (no double-counting)
    - source_breakdown: count per detection_source
    - sentiment_distribution: ratio per sentiment value
    - context_distribution: count per context value
    - is_competitor: True if any mention flagged
    """
    # Group mentions by brand_name (case-insensitive key, preserve original)
    brands: dict[str, list[BrandMention]] = {}
    for m in brand_analysis.brand_mentions:
        key = m.brand_name.lower()
        brands.setdefault(key, []).append(m)

    result = {}
    for _key, mentions in brands.items():
        # Screen time via interval merge
        intervals = [_mention_to_interval(m) for m in mentions]
        merged = merge_intervals(intervals)
        total_screen_time = sum(end - start for start, end in merged)

        # Source breakdown
        source_counts: dict[str, int] = {}
        for m in mentions:
            source_counts[m.detection_source.value] = source_counts.get(m.detection_source.value, 0) + 1

        # Sentiment distribution (ratios)
        sentiment_counts: dict[str, int] = {}
        for m in mentions:
            sentiment_counts[m.sentiment.value] = sentiment_counts.get(m.sentiment.value, 0) + 1
        total = len(mentions)
        sentiment_dist = {k: round(v / total, 2) for k, v in sentiment_counts.items()}

        # Context distribution
        context_counts: dict[str, int] = {}
        for m in mentions:
            context_counts[m.context.value] = context_counts.get(m.context.value, 0) + 1

        # is_competitor: True if any mention flagged
        is_competitor = any(m.is_competitor for m in mentions)

        brand_name = mentions[0].brand_name  # Use first mention's casing
        result[brand_name] = BrandExposureSummary(
            brand_name=brand_name,
            total_mentions=total,
            total_screen_time_seconds=total_screen_time,
            source_breakdown=source_counts,
            sentiment_distribution=sentiment_dist,
            context_distribution=context_counts,
            is_competitor=is_competitor,
        )

    return result


def aggregate_multi_video(
    exposures: list[tuple[str, dict[str, BrandExposureSummary]]],
) -> dict[str, MultiVideoBrandExposure]:
    """Aggregate brand exposure across multiple videos.

    Args:
        exposures: list of (analysis_id, per_brand_exposure) tuples
    """
    # Collect all brands across all videos
    brand_data: dict[str, dict] = {}

    for analysis_id, per_brand in exposures:
        for brand_name, summary in per_brand.items():
            key = brand_name.lower()
            if key not in brand_data:
                brand_data[key] = {
                    "brand_name": brand_name,
                    "total_mentions": 0,
                    "total_screen_time_seconds": 0,
                    "videos_appearing_in": 0,
                    "source_breakdown": {},
                    "sentiment_counts": {},
                    "sentiment_trend": {},
                    "is_competitor": False,
                }
            data = brand_data[key]
            data["total_mentions"] += summary.total_mentions
            data["total_screen_time_seconds"] += summary.total_screen_time_seconds
            data["videos_appearing_in"] += 1

            # Merge source breakdown
            for source, count in summary.source_breakdown.items():
                data["source_breakdown"][source] = data["source_breakdown"].get(source, 0) + count

            # Accumulate sentiment counts for final ratio
            for sentiment, ratio in summary.sentiment_distribution.items():
                raw_count = round(ratio * summary.total_mentions)
                data["sentiment_counts"][sentiment] = data["sentiment_counts"].get(sentiment, 0) + raw_count

            # Sentiment trend: dominant sentiment per video (chronological)
            dominant = max(summary.sentiment_distribution, key=summary.sentiment_distribution.get)  # type: ignore[arg-type]
            data["sentiment_trend"][analysis_id] = dominant

            if summary.is_competitor:
                data["is_competitor"] = True

    result: dict[str, MultiVideoBrandExposure] = {}
    for _key, data in brand_data.items():
        total_mentions = data["total_mentions"]
        videos_in = data["videos_appearing_in"]

        # Sentiment distribution (ratios from accumulated counts)
        sentiment_total = sum(data["sentiment_counts"].values())
        sentiment_dist = (
            {k: round(v / sentiment_total, 2) for k, v in data["sentiment_counts"].items()}
            if sentiment_total > 0
            else {}
        )

        result[data["brand_name"]] = MultiVideoBrandExposure(
            total_mentions=total_mentions,
            total_screen_time_seconds=data["total_screen_time_seconds"],
            average_screen_time_per_video=round(data["total_screen_time_seconds"] / videos_in, 2) if videos_in > 0 else 0.0,
            videos_appearing_in=videos_in,
            sentiment_trend=data["sentiment_trend"],
            source_breakdown=data["source_breakdown"],
            sentiment_distribution=sentiment_dist,
            is_competitor=data["is_competitor"],
        )

    return result
