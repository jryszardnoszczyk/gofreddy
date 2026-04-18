"""Sentiment time-series aggregation — pure query-time SQL, no pre-computed tables."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal
from uuid import UUID

from cachetools import TTLCache

from ..models import SentimentBucket
from ..repository import PostgresMonitoringRepository

# Cache sentiment results for 30 minutes — data is static for a given time window.
_sentiment_cache: TTLCache[str, list[SentimentBucket]] = TTLCache(maxsize=200, ttl=1800)

# Valid window → timedelta mapping for computing start date
_WINDOW_INTERVALS: dict[str, timedelta] = {
    "1d": timedelta(days=1),
    "7d": timedelta(days=7),
    "14d": timedelta(days=14),
    "30d": timedelta(days=30),
    "90d": timedelta(days=90),
}

# Granularity → PostgreSQL date_trunc unit
_GRANULARITY_MAP: dict[str, str] = {
    "1h": "hour",
    "6h": "hour",  # 6h uses hour buckets, grouped in Python
    "1d": "day",
}

Granularity = Literal["1h", "6h", "1d"]
Window = Literal["1d", "7d", "14d", "30d", "90d"]


async def get_sentiment_time_series(
    repo: PostgresMonitoringRepository,
    monitor_id: UUID,
    user_id: UUID,
    *,
    window: Window = "7d",
    granularity: Granularity = "1d",
) -> list[SentimentBucket]:
    """Query-time sentiment aggregation. Returns empty list for no data."""
    cache_key = f"{monitor_id}:{window}:{granularity}"
    cached = _sentiment_cache.get(cache_key)
    if cached is not None:
        return cached

    from datetime import timezone
    date_from = datetime.now(timezone.utc) - _WINDOW_INTERVALS[window]

    # For 6h granularity, we query by hour then aggregate in Python
    if granularity == "6h":
        trunc_unit = "hour"
    else:
        trunc_unit = _GRANULARITY_MAP[granularity]

    sql = """
        SELECT
            date_trunc($3, m.published_at) AS period,
            AVG(m.sentiment_score) AS avg_sentiment,
            COUNT(*) AS mention_count,
            COUNT(*) FILTER (WHERE m.sentiment_label = 'positive') AS positive_count,
            COUNT(*) FILTER (WHERE m.sentiment_label = 'negative') AS negative_count,
            COUNT(*) FILTER (WHERE m.sentiment_label = 'neutral') AS neutral_count,
            COUNT(*) FILTER (WHERE m.sentiment_label = 'mixed') AS mixed_count
        FROM mentions m
        JOIN monitors mon ON mon.id = m.monitor_id
        WHERE mon.user_id = $1
          AND m.monitor_id = $2
          AND m.sentiment_score IS NOT NULL
          AND m.published_at >= $4
        GROUP BY period
        ORDER BY period ASC
    """

    async with repo._acquire_connection() as conn:
        rows = await conn.fetch(sql, user_id, monitor_id, trunc_unit, date_from)

    buckets = [
        SentimentBucket(
            period_start=row["period"],
            avg_sentiment=float(row["avg_sentiment"]) if row["avg_sentiment"] is not None else 0.0,
            mention_count=row["mention_count"],
            positive_count=row["positive_count"],
            negative_count=row["negative_count"],
            neutral_count=row["neutral_count"],
            mixed_count=row["mixed_count"],
        )
        for row in rows
    ]

    # For 6h granularity, merge hourly buckets into 6-hour windows
    if granularity == "6h":
        buckets = _merge_to_6h(buckets)

    _sentiment_cache[cache_key] = buckets
    return buckets


def _merge_to_6h(buckets: list[SentimentBucket]) -> list[SentimentBucket]:
    """Merge hourly buckets into 6-hour windows."""
    if not buckets:
        return []

    merged: dict[datetime, list[SentimentBucket]] = {}
    for b in buckets:
        # Round down to nearest 6-hour boundary
        hour = b.period_start.hour
        window_hour = (hour // 6) * 6
        window_start = b.period_start.replace(hour=window_hour, minute=0, second=0, microsecond=0)
        merged.setdefault(window_start, []).append(b)

    result = []
    for period, group in sorted(merged.items()):
        total_count = sum(b.mention_count for b in group)
        total_sentiment = sum(b.avg_sentiment * b.mention_count for b in group)
        result.append(
            SentimentBucket(
                period_start=period,
                avg_sentiment=total_sentiment / total_count if total_count > 0 else 0.0,
                mention_count=total_count,
                positive_count=sum(b.positive_count for b in group),
                negative_count=sum(b.negative_count for b in group),
                neutral_count=sum(b.neutral_count for b in group),
                mixed_count=sum(b.mixed_count for b in group),
            )
        )
    return result
