"""Google Trends correlation — compares mention volume with Google Trends interest scores."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import StatisticsError, correlation
from uuid import UUID

from ..repository import PostgresMonitoringRepository

# Window → timedelta mapping (asyncpg needs timedelta, not strings)
_WINDOW_INTERVALS: dict[str, timedelta] = {
    "1d": timedelta(days=1),
    "7d": timedelta(days=7),
    "14d": timedelta(days=14),
    "30d": timedelta(days=30),
    "90d": timedelta(days=90),
}


@dataclass(frozen=True, slots=True)
class TrendsCorrelationBucket:
    period_start: datetime
    mention_count: int
    google_trends_score: float | None  # avg interest_score from GOOGLE_TRENDS mentions


@dataclass(frozen=True, slots=True)
class TrendsCorrelationResult:
    buckets: list[TrendsCorrelationBucket]
    correlation_coefficient: float | None  # Pearson r, None if insufficient data
    keyword: str


def safe_pearson(x: list[float], y: list[float], min_points: int = 3) -> float | None:
    """Pearson r with guards. Returns None if insufficient/constant data."""
    if len(x) < min_points or len(y) < min_points:
        return None
    try:
        return correlation(x, y)
    except StatisticsError:
        return None


async def get_trends_correlation(
    repo: PostgresMonitoringRepository,
    monitor_id: UUID,
    user_id: UUID,
    *,
    keyword: str,
    window: str = "30d",
) -> TrendsCorrelationResult:
    """Correlate mention volume with Google Trends interest scores over time buckets."""
    from datetime import timezone
    date_from = datetime.now(timezone.utc) - _WINDOW_INTERVALS.get(window, timedelta(days=7))

    # Query 1: Non-Google-Trends mention volume by day
    mention_sql = """
        SELECT date_trunc('day', m.published_at) AS period, count(*) AS cnt
        FROM mentions m
        JOIN monitors mon ON mon.id = m.monitor_id
        WHERE mon.user_id = $1
          AND m.monitor_id = $2
          AND m.source != 'google_trends'
          AND m.published_at >= $3
        GROUP BY 1
        ORDER BY 1 ASC
    """

    # Query 2: Google Trends interest scores by day
    trends_sql = """
        SELECT date_trunc('day', m.published_at) AS period,
               avg((m.metadata->>'interest_score')::float) AS avg_score
        FROM mentions m
        JOIN monitors mon ON mon.id = m.monitor_id
        WHERE mon.user_id = $1
          AND m.monitor_id = $2
          AND m.source = 'google_trends'
          AND m.published_at >= $3
        GROUP BY 1
        ORDER BY 1 ASC
    """

    async with repo._acquire_connection() as conn:
        mention_rows = await conn.fetch(mention_sql, user_id, monitor_id, date_from)
        trends_rows = await conn.fetch(trends_sql, user_id, monitor_id, date_from)

    # Index by period for joining
    mention_by_period: dict[datetime, int] = {row["period"]: row["cnt"] for row in mention_rows}
    trends_by_period: dict[datetime, float] = {
        row["period"]: float(row["avg_score"]) for row in trends_rows if row["avg_score"] is not None
    }

    # Union all periods
    all_periods = sorted(set(mention_by_period) | set(trends_by_period))

    buckets = [
        TrendsCorrelationBucket(
            period_start=p,
            mention_count=mention_by_period.get(p, 0),
            google_trends_score=trends_by_period.get(p),
        )
        for p in all_periods
    ]

    # Pearson correlation on overlapping points only
    overlapping = [(b.mention_count, b.google_trends_score) for b in buckets if b.google_trends_score is not None]
    if overlapping:
        x_vals = [float(mc) for mc, _ in overlapping]
        y_vals = [gs for _, gs in overlapping]
        coeff = safe_pearson(x_vals, y_vals)
    else:
        coeff = None

    return TrendsCorrelationResult(
        buckets=buckets,
        correlation_coefficient=coeff,
        keyword=keyword,
    )
