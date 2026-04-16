"""Engagement prediction — deterministic comparison against own-account patterns.

Simple above/below average comparison with 3-tier cold-start fallback.
Zero LLM cost.
"""

from __future__ import annotations

from typing import Any, Literal

from .models_analytics import EngagementPrediction, PerformancePatterns

# Platform-specific defaults for cold-start (tier 2 and 3)
_PLATFORM_DEFAULTS: dict[str, dict[str, Any]] = {
    "twitter": {
        "best_hours": [9, 12, 17],
        "best_days": [1, 2, 3],
        "avg_length": 180,
    },
    "instagram": {
        "best_hours": [11, 14, 19],
        "best_days": [0, 2, 4],
        "avg_length": 120,
    },
    "tiktok": {
        "best_hours": [12, 15, 21],
        "best_days": [1, 4, 5],
        "avg_length": 80,
    },
    "youtube": {
        "best_hours": [14, 17],
        "best_days": [4, 5],
        "avg_length": 500,
    },
}


def predict_engagement(
    draft_features: dict[str, Any],
    patterns: PerformancePatterns | None,
    *,
    platform: str = "twitter",
) -> EngagementPrediction:
    """Compare draft features against user's own averages from performance_patterns."""
    if patterns is None or patterns.total_posts == 0:
        return _cold_start_prediction(draft_features, platform, post_count=0)

    if patterns.total_posts < 20:
        return _cold_start_prediction(draft_features, platform, post_count=patterns.total_posts, patterns=patterns)

    # Full personal patterns — confidence = "high"
    signals: list[str] = []  # "above", "average", "below"
    factors: list[str] = []

    # 1. Post length
    content_length = draft_features.get("content_length", 0)
    _compare_length(content_length, patterns.avg_post_length, signals, factors)

    # 2. Posting hour
    posting_hour = draft_features.get("posting_hour")
    if posting_hour is not None:
        _compare_hour(posting_hour, patterns.best_posting_hours, signals, factors)

    # 3. Posting day
    posting_day = draft_features.get("posting_day")
    if posting_day is not None:
        _compare_day(posting_day, patterns.best_posting_days, signals, factors)

    # 4. Media type
    media_type = draft_features.get("media_type", "text")
    _compare_media_type(media_type, patterns.content_type_breakdown, signals, factors)

    # 5. Hashtag count
    hashtag_count = draft_features.get("hashtag_count", 0)
    if hashtag_count > 0:
        factors.append(f"Using {hashtag_count} hashtags")
        signals.append("average")

    return EngagementPrediction(
        likely_performance=_aggregate_performance(signals),
        confidence="high",
        contributing_factors=factors,
        comparison_baseline="personal_20+",
    )


def _cold_start_prediction(
    draft_features: dict[str, Any],
    platform: str,
    post_count: int,
    patterns: PerformancePatterns | None = None,
) -> EngagementPrediction:
    """Handle tier 2 (<20 posts) and tier 3 (zero data) cold starts."""
    defaults = _PLATFORM_DEFAULTS.get(platform, _PLATFORM_DEFAULTS["twitter"])

    if post_count == 0:
        # Tier 3: platform defaults only
        return EngagementPrediction(
            likely_performance="average",
            confidence="low",
            contributing_factors=[
                "Based on platform best practices, no personal data available.",
            ],
            comparison_baseline="platform_defaults",
        )

    # Tier 2: personal patterns + platform defaults for missing signals
    signals: list[str] = []
    factors: list[str] = []

    best_hours = patterns.best_posting_hours if patterns and patterns.best_posting_hours else defaults["best_hours"]
    best_days = patterns.best_posting_days if patterns and patterns.best_posting_days else defaults["best_days"]
    avg_length = patterns.avg_post_length if patterns and patterns.avg_post_length > 0 else defaults["avg_length"]

    content_length = draft_features.get("content_length", 0)
    _compare_length(content_length, avg_length, signals, factors)

    posting_hour = draft_features.get("posting_hour")
    if posting_hour is not None:
        _compare_hour(posting_hour, best_hours, signals, factors)

    posting_day = draft_features.get("posting_day")
    if posting_day is not None:
        _compare_day(posting_day, best_days, signals, factors)

    confidence = "medium" if post_count >= 5 else "low"

    return EngagementPrediction(
        likely_performance=_aggregate_performance(signals),
        confidence=confidence,  # type: ignore[arg-type]
        contributing_factors=factors,
        comparison_baseline="personal_<20",
    )


def _compare_length(content_length: int, avg_length: float, signals: list[str], factors: list[str]) -> None:
    diff = content_length - avg_length
    if abs(diff) < avg_length * 0.3:
        signals.append("average")
        factors.append(f"Post length ({content_length} chars) is close to your average ({avg_length:.0f} chars)")
    elif diff > 0:
        signals.append("above")
        factors.append(f"Post length ({content_length} chars) is above your average ({avg_length:.0f} chars)")
    else:
        signals.append("below")
        factors.append(f"Post length ({content_length} chars) is below your average ({avg_length:.0f} chars)")


def _compare_hour(posting_hour: int, best_hours: list[int], signals: list[str], factors: list[str]) -> None:
    if posting_hour in best_hours[:3]:
        signals.append("above")
        factors.append(f"Posting at {posting_hour}:00 matches your best-performing hour")
    elif posting_hour in best_hours:
        signals.append("average")
        factors.append(f"Posting at {posting_hour}:00 is a reasonable time based on your history")
    else:
        signals.append("below")
        factors.append(f"Posting at {posting_hour}:00 is outside your best-performing hours")


_DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _compare_day(posting_day: int, best_days: list[int], signals: list[str], factors: list[str]) -> None:
    day_name = _DAY_NAMES[posting_day]
    if posting_day in best_days[:3]:
        signals.append("above")
        factors.append(f"Posting on {day_name} matches your best-performing day")
    elif posting_day in best_days[:min(5, len(best_days))]:
        signals.append("average")
        factors.append(f"Posting on {day_name} is a reasonable day based on your history")
    else:
        signals.append("below")
        factors.append(f"Posting on {day_name} is outside your best-performing days")


def _compare_media_type(
    media_type: str,
    type_breakdown: dict[str, int],
    signals: list[str],
    factors: list[str],
) -> None:
    count = type_breakdown.get(media_type, 0)
    total = sum(type_breakdown.values())
    if total == 0:
        signals.append("average")
        factors.append(f"{media_type} content type — no historical data to compare")
        return

    share = count / total
    if share > 0.3:
        signals.append("above")
        factors.append(f"{media_type} is your most-used content type ({share:.0%} of posts)")
    elif count > 0:
        signals.append("average")
        factors.append(f"{media_type} makes up {share:.0%} of your posts")
    else:
        signals.append("below")
        factors.append(f"You haven't posted {media_type} content before")


def _aggregate_performance(signals: list[str]) -> Literal["strong", "average", "weak"]:
    """Majority vote: more above than below = strong, more below = weak, else average."""
    above = signals.count("above")
    below = signals.count("below")
    if above > below:
        return "strong"
    elif below > above:
        return "weak"
    return "average"
