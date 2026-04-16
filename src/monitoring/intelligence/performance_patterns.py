"""PerformancePatterns — deterministic own-account analytics computation.

Same architectural pattern as generate_commodity_baseline() but for own-account
posts, not brand mentions. Zero LLM cost.
"""

from __future__ import annotations

import dataclasses
from collections import Counter
from datetime import date
from statistics import mean
from typing import Any

from .metric_computations import compute_date_gaps, compute_engagement_spikes, compute_velocity_flags
from .models_analytics import AccountPost, AccountSnapshot, PerformancePatterns

_DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _get_engagement(post: AccountPost) -> float:
    """Engagement value: prefer engagement_rate, fall back to raw counts."""
    if post.engagement_rate is not None:
        return post.engagement_rate
    return float(post.likes + post.comments + post.shares)


def _post_summary(post: AccountPost) -> dict[str, Any]:
    return {
        "source_id": post.source_id,
        "content": post.content[:200],
        "engagement_rate": post.engagement_rate,
        "likes": post.likes,
        "comments": post.comments,
        "shares": post.shares,
        "published_at": post.published_at.isoformat() if post.published_at else None,
        "media_type": post.media_type,
    }


def generate_performance_patterns(
    posts: list[AccountPost],
    snapshots: list[AccountSnapshot] | None = None,
    *,
    period_start: date | None = None,
    period_end: date | None = None,
) -> PerformancePatterns:
    """Deterministic computation from account_posts. Zero LLM cost."""
    if not posts:
        today = date.today()
        return PerformancePatterns(
            avg_engagement_rate=0.0,
            top_posts=[],
            worst_posts=[],
            content_type_breakdown={},
            best_posting_hours=[],
            best_posting_days=[],
            follower_growth=None,
            engagement_trend="stable",
            engagement_spikes=[],
            velocity_flags=[],
            date_gaps=[],
            posting_frequency=0.0,
            avg_post_length=0.0,
            engagement_by_length_bucket={},
            total_posts=0,
            period_start=period_start or today,
            period_end=period_end or today,
            markdown="No posts available for pattern computation.",
        )

    # Determine period
    dated_posts = [p for p in posts if p.published_at is not None]
    if dated_posts:
        sorted_by_date = sorted(dated_posts, key=lambda p: p.published_at)  # type: ignore[arg-type]
        p_start = period_start or sorted_by_date[0].published_at.date()  # type: ignore[union-attr]
        p_end = period_end or sorted_by_date[-1].published_at.date()  # type: ignore[union-attr]
    else:
        p_start = period_start or date.today()
        p_end = period_end or date.today()

    # 1. avg_engagement_rate
    rates = [p.engagement_rate for p in posts if p.engagement_rate is not None]
    if rates:
        avg_engagement_rate = mean(rates)
    else:
        raw = [float(p.likes + p.comments + p.shares) for p in posts]
        avg_engagement_rate = mean(raw) if raw else 0.0

    # 2. top_posts / worst_posts
    sorted_by_engagement = sorted(posts, key=_get_engagement, reverse=True)
    top_posts = [_post_summary(p) for p in sorted_by_engagement[:10]]
    worst_posts = [_post_summary(p) for p in sorted_by_engagement[-10:]]

    # 3. content_type_breakdown
    content_type_breakdown = dict(Counter(p.media_type or "unknown" for p in posts))

    # 4. best_posting_hours
    hour_engagement: dict[int, list[float]] = {}
    for p in dated_posts:
        h = p.published_at.hour  # type: ignore[union-attr]
        hour_engagement.setdefault(h, []).append(_get_engagement(p))
    best_posting_hours = sorted(
        hour_engagement.keys(),
        key=lambda h: mean(hour_engagement[h]),
        reverse=True,
    )[:5]

    # 5. best_posting_days
    day_engagement: dict[int, list[float]] = {}
    for p in dated_posts:
        d = p.published_at.weekday()  # type: ignore[union-attr]
        day_engagement.setdefault(d, []).append(_get_engagement(p))
    best_posting_days = sorted(
        day_engagement.keys(),
        key=lambda d: mean(day_engagement[d]),
        reverse=True,
    )[:3]

    # 6. follower_growth
    follower_growth: float | None = None
    if snapshots and len(snapshots) >= 2:
        sorted_snaps = sorted(snapshots, key=lambda s: s.created_at)
        first_fc = sorted_snaps[0].follower_count
        last_fc = sorted_snaps[-1].follower_count
        if first_fc is not None and last_fc is not None:
            follower_growth = float(last_fc - first_fc)

    # 7. engagement_trend — compare chronologically recent vs older posts
    sorted_by_time = sorted(dated_posts, key=lambda p: p.published_at)  # type: ignore[arg-type]
    n = len(sorted_by_time)
    quarter = max(1, n // 4)
    oldest_engagement = mean([_get_engagement(p) for p in sorted_by_time[:quarter]] or [0])
    recent_engagement = mean([_get_engagement(p) for p in sorted_by_time[-quarter:]] or [0])
    if oldest_engagement > 0 and (recent_engagement - oldest_engagement) / oldest_engagement > 0.1:
        engagement_trend = "improving"
    elif oldest_engagement > 0 and (oldest_engagement - recent_engagement) / oldest_engagement > 0.1:
        engagement_trend = "declining"
    else:
        engagement_trend = "stable"

    # 8-10. Shared metrics
    daily_volumes: dict[str, int] = {}
    for p in dated_posts:
        day_str = str(p.published_at.date())  # type: ignore[union-attr]
        daily_volumes[day_str] = daily_volumes.get(day_str, 0) + 1

    spike_items = [
        {"source_id": p.source_id, "content": p.content, "engagement": _get_engagement(p)}
        for p in posts
    ]
    engagement_spikes = compute_engagement_spikes(spike_items, avg_engagement_rate)
    velocity_flags = compute_velocity_flags(daily_volumes)
    date_gaps_list = compute_date_gaps(daily_volumes, p_start, p_end) if p_start and p_end else []

    # 11. posting_frequency
    days_span = (p_end - p_start).days
    posting_frequency = len(posts) / (days_span / 7) if days_span > 0 else 0.0

    # 12. avg_post_length
    avg_post_length = mean([len(p.content) for p in posts]) if posts else 0.0

    # 13. engagement_by_length_bucket
    buckets: dict[str, list[float]] = {"short": [], "medium": [], "long": []}
    for p in posts:
        length = len(p.content)
        if length <= 100:
            buckets["short"].append(_get_engagement(p))
        elif length <= 300:
            buckets["medium"].append(_get_engagement(p))
        else:
            buckets["long"].append(_get_engagement(p))
    engagement_by_length_bucket = {
        k: mean(v) if v else 0.0 for k, v in buckets.items()
    }

    # Build patterns (without markdown first, then render)
    patterns = PerformancePatterns(
        avg_engagement_rate=avg_engagement_rate,
        top_posts=top_posts,
        worst_posts=worst_posts,
        content_type_breakdown=content_type_breakdown,
        best_posting_hours=best_posting_hours,
        best_posting_days=best_posting_days,
        follower_growth=follower_growth,
        engagement_trend=engagement_trend,  # type: ignore[arg-type]
        engagement_spikes=engagement_spikes,
        velocity_flags=velocity_flags,
        date_gaps=date_gaps_list,
        posting_frequency=round(posting_frequency, 1),
        avg_post_length=round(avg_post_length, 1),
        engagement_by_length_bucket=engagement_by_length_bucket,
        total_posts=len(posts),
        period_start=p_start,
        period_end=p_end,
        markdown="",  # placeholder
    )

    markdown = _render_patterns_markdown(patterns)
    return dataclasses.replace(patterns, markdown=markdown)


def _render_patterns_markdown(patterns: PerformancePatterns) -> str:
    """Pre-render markdown for system_instruction injection."""
    lines = [
        f"## Account Performance Patterns ({patterns.total_posts} posts, "
        f"{patterns.period_start} to {patterns.period_end})",
        "",
        f"**Avg engagement rate:** {patterns.avg_engagement_rate:.4f}",
        f"**Posting frequency:** {patterns.posting_frequency} posts/week",
        f"**Engagement trend:** {patterns.engagement_trend}",
    ]

    if patterns.best_posting_hours:
        hours_str = ", ".join(f"{h}:00" for h in patterns.best_posting_hours)
        lines.append(f"**Best posting hours:** {hours_str}")

    if patterns.best_posting_days:
        days_str = ", ".join(_DAY_NAMES[d] for d in patterns.best_posting_days if d < 7)
        lines.append(f"**Best posting days:** {days_str}")

    if patterns.follower_growth is not None:
        sign = "+" if patterns.follower_growth >= 0 else ""
        lines.append(f"**Follower growth:** {sign}{patterns.follower_growth:,.0f} (period)")

    if patterns.content_type_breakdown:
        lines.extend(["", "**Content type performance:**"])
        for media_type, count in sorted(
            patterns.content_type_breakdown.items(), key=lambda x: x[1], reverse=True,
        ):
            lines.append(f"  - {media_type}: {count} posts")

    if patterns.top_posts:
        lines.extend(["", "**Top performers:**"])
        for i, post in enumerate(patterns.top_posts[:5], 1):
            preview = (post.get("content") or "")[:80]
            er = post.get("engagement_rate")
            er_str = f"{er:.4f}" if er is not None else "N/A"
            pub = post.get("published_at", "")
            lines.append(f'  {i}. "{preview}..." ({er_str} engagement, {pub})')

    if patterns.worst_posts:
        lines.extend(["", "**Worst performers:**"])
        for i, post in enumerate(patterns.worst_posts[:3], 1):
            preview = (post.get("content") or "")[:80]
            er = post.get("engagement_rate")
            er_str = f"{er:.4f}" if er is not None else "N/A"
            pub = post.get("published_at", "")
            lines.append(f'  {i}. "{preview}..." ({er_str} engagement, {pub})')

    return "\n".join(lines)
