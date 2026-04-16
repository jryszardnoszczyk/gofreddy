"""Shared metric computation functions for CommodityBaseline and PerformancePatterns.

Extracted from commodity_baseline.py to enable reuse across both brand-mention
baselines and own-account analytics.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any


def compute_engagement_spikes(
    items: list[dict[str, Any]],
    avg_engagement: float,
    *,
    threshold_ratio: float = 10.0,
    content_preview_len: int = 150,
) -> list[dict[str, Any]]:
    """Items with engagement > threshold_ratio x average.

    Works for both mentions (CommodityBaseline) and posts (PerformancePatterns).
    Caller provides the engagement value via item["engagement"] key.
    """
    if avg_engagement <= 0:
        return []

    spikes = []
    for item in items:
        engagement = item.get("engagement", 0)
        ratio = engagement / avg_engagement
        if ratio > threshold_ratio:
            spikes.append({
                "source_id": item.get("source_id", ""),
                "content": (item.get("content", ""))[:content_preview_len],
                "engagement": engagement,
                "ratio": round(ratio, 1),
            })
    return spikes


def compute_velocity_flags(
    daily_volumes: dict[str, int],
    *,
    consecutive_threshold: int = 3,
) -> list[str]:
    """Dates where N+ consecutive daily volume increases occurred."""
    sorted_days = sorted(daily_volumes.keys())
    flags: list[str] = []
    consecutive_increases = 0
    for i in range(1, len(sorted_days)):
        if daily_volumes[sorted_days[i]] > daily_volumes[sorted_days[i - 1]]:
            consecutive_increases += 1
            if consecutive_increases >= consecutive_threshold:
                flags.append(sorted_days[i])
        else:
            consecutive_increases = 0
    return flags


def compute_date_gaps(
    daily_volumes: dict[str, int],
    period_start: date,
    period_end: date,
) -> list[str]:
    """Dates with zero volume within the period range."""
    gaps: list[str] = []
    current = period_start
    while current <= period_end:
        if str(current) not in daily_volumes:
            gaps.append(str(current))
        current += timedelta(days=1)
    return gaps
