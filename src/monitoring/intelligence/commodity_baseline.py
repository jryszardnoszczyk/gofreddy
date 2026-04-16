"""Commodity baseline — deterministic structured summary from monitoring data.

Produces the "before" state: a factual dashboard dump. The agent's synthesis
is measured against this baseline (Signal 2: data integrity verification).
Same input always produces the same output.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from .metric_computations import compute_date_gaps, compute_engagement_spikes, compute_velocity_flags


class InsufficientDataError(Exception):
    """Raised when there are zero mentions to generate a baseline from."""


@dataclass(frozen=True, slots=True)
class CommodityBaseline:
    period_start: date
    period_end: date
    total_mentions: int
    source_breakdown: dict[str, int]
    sentiment: dict[str, float]  # positive/neutral/negative percentages
    previous_sentiment: dict[str, float] | None  # None for first week
    top_topics: list[tuple[str, int]]  # (topic, mention_count)
    top_mentions: list[dict[str, Any]]  # top by engagement
    alerts_triggered: int
    share_of_voice: dict[str, float] | None
    markdown: str  # pre-rendered markdown
    # G1: Enhanced statistics
    daily_volumes: dict[str, int] = field(default_factory=dict)
    engagement_per_mention: float = 0.0
    top_authors: list[dict[str, Any]] = field(default_factory=list)
    author_concentration_flag: bool = False
    reach_tiers: dict[str, int] = field(default_factory=dict)
    language_distribution: dict[str, int] = field(default_factory=dict)
    engagement_spikes: list[dict[str, Any]] = field(default_factory=list)
    velocity_flags: list[str] = field(default_factory=list)
    date_gaps: list[str] = field(default_factory=list)


def generate_commodity_baseline(
    mentions_data: dict[str, Any],
    sentiment_data: dict[str, Any],
    sov_data: dict[str, Any] | None,
    alerts_data: list[dict[str, Any]],
    period_start: date | None = None,
    period_end: date | None = None,
    previous_sentiment: dict[str, float] | None = None,
) -> CommodityBaseline:
    """Generate deterministic commodity baseline from CLI data.

    Graceful degradation:
    - sov_data=None → omit SOV section
    - previous_sentiment=None → omit delta comparison (first week)
    - empty alerts → "No alerts triggered"
    """
    # Extract mentions list — API returns "data" key, CLI wrappers may use "mentions"
    mentions = mentions_data.get("mentions") or mentions_data.get("data") or []
    total_mentions = len(mentions)

    if not mentions:
        raise InsufficientDataError("Zero mentions — cannot generate baseline")

    # Source breakdown (reused below for reach tiers)
    source_counts: dict[str, int] = {}
    for m in mentions:
        src = m.get("source", "unknown")
        source_counts[src] = source_counts.get(src, 0) + 1

    # Sentiment breakdown from sentiment_data or compute from mentions
    buckets = sentiment_data.get("buckets", [])
    if buckets:
        pos = sum(b.get("positive_count", 0) for b in buckets)
        neg = sum(b.get("negative_count", 0) for b in buckets)
        neu = sum(b.get("neutral_count", 0) for b in buckets)
        total_sentiment = pos + neg + neu
        if total_sentiment > 0:
            sentiment_pcts = {
                "positive": round(pos / total_sentiment * 100, 1),
                "negative": round(neg / total_sentiment * 100, 1),
                "neutral": round(neu / total_sentiment * 100, 1),
            }
        else:
            sentiment_pcts = {"positive": 0.0, "negative": 0.0, "neutral": 0.0}
    else:
        sentiment_pcts = {"positive": 0.0, "negative": 0.0, "neutral": 0.0}

    # Topics — keyword frequency from mention content (TopicClusterer removed)
    word_freq: dict[str, int] = {}
    for m in mentions:
        content = m.get("content", "")
        for word in content.lower().split():
            if len(word) > 4:  # Skip short words
                word_freq[word] = word_freq.get(word, 0) + 1
    top_topics = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]

    # Top mentions by engagement
    def engagement_score(m: dict) -> int:
        total = m.get("engagement_total")
        if total is not None:
            return int(total)
        return (
            m.get("engagement_likes", 0)
            + m.get("engagement_shares", 0)
            + m.get("engagement_comments", 0)
        )

    sorted_mentions = sorted(mentions, key=engagement_score, reverse=True)[:5]
    top_mentions = [
        {
            "source": m.get("source", "unknown"),
            "content": (m.get("content", ""))[:200],
            "engagement": engagement_score(m),
            "url": m.get("url"),
        }
        for m in sorted_mentions
    ]

    # Alerts
    alerts_count = len(alerts_data)

    # Share of voice
    sov_breakdown: dict[str, float] | None = None
    if sov_data:
        entries = sov_data.get("entries", [])
        sov_breakdown = {
            e.get("brand", "unknown"): e.get("percentage", 0.0)
            for e in entries
        }

    # ── G1: Enhanced statistics ──

    # Daily volumes
    daily_volumes: dict[str, int] = {}
    for m in mentions:
        pub = m.get("published_at", "")
        if pub:
            day = str(pub)[:10]  # YYYY-MM-DD
            daily_volumes[day] = daily_volumes.get(day, 0) + 1

    # Engagement per mention
    total_engagement = sum(engagement_score(m) for m in mentions)
    engagement_per_mention = round(total_engagement / total_mentions, 2) if total_mentions else 0.0

    # Top authors with concentration
    author_counts: dict[str, int] = Counter(
        m.get("author_handle") or "unknown" for m in mentions
    )
    sorted_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    top_authors = []
    author_concentration_flag = False
    for handle, count in sorted_authors:
        share = round(count / total_mentions * 100, 1)
        if share > 15.0:
            author_concentration_flag = True
        # Sum reach for this author
        author_reach = sum(
            m.get("reach_estimate") or 0
            for m in mentions if (m.get("author_handle") or "unknown") == handle
        )
        top_authors.append({
            "handle": handle, "count": count, "share": share, "reach": author_reach,
        })

    # Reach tiers
    reach_tiers = {"institutional": 0, "influencer": 0, "organic": 0}
    for m in mentions:
        reach = m.get("reach_estimate") or 0
        if reach > 100_000:
            reach_tiers["institutional"] += 1
        elif reach > 10_000:
            reach_tiers["influencer"] += 1
        else:
            reach_tiers["organic"] += 1

    # Language distribution
    language_distribution: dict[str, int] = Counter(
        m.get("language") or "unknown" for m in mentions
    )

    # Engagement spikes (mentions with engagement > 10x average — ratios, agent decides)
    spike_items = [
        {"source_id": m.get("source_id", ""), "content": m.get("content", ""), "engagement": engagement_score(m)}
        for m in mentions
    ]
    engagement_spikes = compute_engagement_spikes(spike_items, engagement_per_mention)

    # Velocity flags (dates with 3+ consecutive daily increases)
    velocity_flags = compute_velocity_flags(daily_volumes)

    # Date gaps
    if period_start and period_end:
        date_gaps = compute_date_gaps(daily_volumes, period_start, period_end)
    else:
        date_gaps = []

    # Render markdown
    md = _render_markdown(
        period_start=period_start,
        period_end=period_end,
        total_mentions=total_mentions,
        source_counts=source_counts,
        sentiment_pcts=sentiment_pcts,
        previous_sentiment=previous_sentiment,
        top_topics=top_topics,
        top_mentions=top_mentions,
        alerts_count=alerts_count,
        alerts_data=alerts_data,
        sov_breakdown=sov_breakdown,
        daily_volumes=daily_volumes,
        engagement_per_mention=engagement_per_mention,
        top_authors=top_authors,
        author_concentration_flag=author_concentration_flag,
        reach_tiers=reach_tiers,
        language_distribution=dict(language_distribution),
        engagement_spikes=engagement_spikes,
        velocity_flags=velocity_flags,
        date_gaps=date_gaps,
    )

    return CommodityBaseline(
        period_start=period_start or date.today(),
        period_end=period_end or date.today(),
        total_mentions=total_mentions,
        source_breakdown=source_counts,
        sentiment=sentiment_pcts,
        previous_sentiment=previous_sentiment,
        top_topics=top_topics,
        top_mentions=top_mentions,
        alerts_triggered=alerts_count,
        share_of_voice=sov_breakdown,
        markdown=md,
        daily_volumes=daily_volumes,
        engagement_per_mention=engagement_per_mention,
        top_authors=top_authors,
        author_concentration_flag=author_concentration_flag,
        reach_tiers=reach_tiers,
        language_distribution=dict(language_distribution),
        engagement_spikes=engagement_spikes,
        velocity_flags=velocity_flags,
        date_gaps=date_gaps,
    )


def _render_markdown(
    *,
    period_start: date | None,
    period_end: date | None,
    total_mentions: int,
    source_counts: dict[str, int],
    sentiment_pcts: dict[str, float],
    previous_sentiment: dict[str, float] | None,
    top_topics: list[tuple[str, int]],
    top_mentions: list[dict[str, Any]],
    alerts_count: int,
    alerts_data: list[dict[str, Any]],
    sov_breakdown: dict[str, float] | None,
    daily_volumes: dict[str, int] | None = None,
    engagement_per_mention: float = 0.0,
    top_authors: list[dict[str, Any]] | None = None,
    author_concentration_flag: bool = False,
    reach_tiers: dict[str, int] | None = None,
    language_distribution: dict[str, int] | None = None,
    engagement_spikes: list[dict[str, Any]] | None = None,
    velocity_flags: list[str] | None = None,
    date_gaps: list[str] | None = None,
) -> str:
    lines: list[str] = []

    date_str = f"{period_start}" if period_start else "unknown"
    lines.append(f"## Week of {date_str} — Commodity Baseline")
    lines.append("")

    # Volume
    source_str = ", ".join(f"{s}: {c}" for s, c in sorted(source_counts.items(), key=lambda x: x[1], reverse=True))
    lines.append(f"**Volume:** {total_mentions} mentions across {len(source_counts)} sources ({source_str})")

    # Daily volumes
    if daily_volumes:
        daily_str = ", ".join(f"{d}: {c}" for d, c in sorted(daily_volumes.items()))
        lines.append(f"**Daily volumes:** {daily_str}")

    # Date gaps
    if date_gaps:
        lines.append(f"**Date gaps (no mentions):** {', '.join(date_gaps)}")

    # Velocity flags
    if velocity_flags:
        lines.append(f"**Velocity flags (3+ consecutive daily increases):** {', '.join(velocity_flags)}")

    # Engagement
    lines.append(f"**Engagement per mention:** {engagement_per_mention}")

    # Sentiment
    sentiment_str = f"{sentiment_pcts['positive']}% positive, {sentiment_pcts['neutral']}% neutral, {sentiment_pcts['negative']}% negative"
    if previous_sentiment:
        prev_str = f"{previous_sentiment.get('positive', 0)}%/{previous_sentiment.get('neutral', 0)}%/{previous_sentiment.get('negative', 0)}%"
        lines.append(f"**Sentiment:** {sentiment_str} (previous week: {prev_str})")
    else:
        lines.append(f"**Sentiment:** {sentiment_str}")

    # Topics
    if top_topics:
        topics_str = ", ".join(f"{t[0]} ({t[1]})" for t in top_topics[:5])
        lines.append(f"**Top topics by volume:** {topics_str}")

    # Top authors
    if top_authors:
        lines.append("**Top authors:**")
        for a in top_authors[:5]:
            flag = " ⚠️ >15% concentration" if a.get("share", 0) > 15 else ""
            lines.append(f"  - @{a['handle']}: {a['count']} mentions ({a['share']}% share, reach: {a['reach']}){flag}")
    if author_concentration_flag:
        lines.append("**⚠️ Author concentration detected:** One or more authors account for >15% of mentions")

    # Reach tiers
    if reach_tiers:
        lines.append(f"**Reach tiers:** institutional (>100K): {reach_tiers.get('institutional', 0)}, influencer (>10K): {reach_tiers.get('influencer', 0)}, organic: {reach_tiers.get('organic', 0)}")

    # Language distribution
    if language_distribution:
        lang_str = ", ".join(f"{l}: {c}" for l, c in sorted(language_distribution.items(), key=lambda x: x[1], reverse=True)[:5])
        lines.append(f"**Languages:** {lang_str}")

    # Top mentions
    if top_mentions:
        lines.append("**Top mentions by engagement:**")
        for i, m in enumerate(top_mentions, 1):
            content_preview = m["content"][:100]
            lines.append(f"  {i}. {m['source']}: \"{content_preview}\" ({m['engagement']} engagement)")

    # Engagement spikes
    if engagement_spikes:
        lines.append(f"**Engagement spikes (>10x avg):** {len(engagement_spikes)} mentions")
        for s in engagement_spikes[:3]:
            lines.append(f"  - \"{s['content'][:80]}\" ({s['engagement']} engagement, {s['ratio']}x avg)")

    # Alerts
    if alerts_count > 0:
        alert_types = [a.get("condition_summary", "unknown") for a in alerts_data[:3]]
        lines.append(f"**Alerts triggered:** {alerts_count} ({', '.join(alert_types)})")
    else:
        lines.append("**Alerts triggered:** 0")

    # SOV
    if sov_breakdown:
        sov_str = ", ".join(f"{brand}: {pct:.1f}%" for brand, pct in sorted(sov_breakdown.items(), key=lambda x: x[1], reverse=True))
        lines.append(f"**Share of voice:** {sov_str}")

    return "\n".join(lines)
