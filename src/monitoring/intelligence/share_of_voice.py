"""Share of Voice calculation — pure SQL-based competitive analysis."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING
from uuid import UUID

from ..models import ShareOfVoiceEntry

if TYPE_CHECKING:
    from ..repository import PostgresMonitoringRepository


async def calculate_sov(
    repo: PostgresMonitoringRepository,
    monitor_id: UUID,
    user_id: UUID,
    monitor_name: str,
    competitor_brands: list[str],
    *,
    window_days: int = 30,
) -> list[ShareOfVoiceEntry]:
    """Calculate share of voice for a monitor's brand vs competitors.

    Uses FTS (websearch_to_tsquery) to count competitor mentions within
    the monitor's own mention pool. Parameterized queries prevent FTS injection.
    """
    from datetime import datetime as dt, timezone
    date_from = dt.now(timezone.utc) - timedelta(days=window_days)

    # Count total mentions for the monitor (the "my brand" baseline)
    my_count_sql = """
        SELECT COUNT(*) FROM mentions m
        JOIN monitors mon ON mon.id = m.monitor_id
        WHERE mon.user_id = $1 AND m.monitor_id = $2
          AND m.published_at >= $3
    """

    my_sentiment_sql = """
        SELECT AVG(m.sentiment_score) FROM mentions m
        JOIN monitors mon ON mon.id = m.monitor_id
        WHERE mon.user_id = $1 AND m.monitor_id = $2
          AND m.published_at >= $3
          AND m.sentiment_score IS NOT NULL
    """

    async with repo._acquire_connection() as conn:
        my_count = await conn.fetchval(my_count_sql, user_id, monitor_id, date_from)
        my_sentiment = await conn.fetchval(my_sentiment_sql, user_id, monitor_id, date_from)

        # Batch all competitor brands into a single query using LATERAL + unnest
        competitor_entries: list[ShareOfVoiceEntry] = []
        if competitor_brands:
            batch_sql = """
                SELECT b.brand,
                       COUNT(m.id) AS mention_count,
                       AVG(m.sentiment_score) FILTER (WHERE m.sentiment_score IS NOT NULL) AS sentiment_avg
                FROM unnest($4::text[]) AS b(brand)
                LEFT JOIN LATERAL (
                    SELECT m.id, m.sentiment_score
                    FROM mentions m
                    JOIN monitors mon ON mon.id = m.monitor_id
                    WHERE mon.user_id = $1 AND m.monitor_id = $2
                      AND m.published_at >= $3
                      AND m.search_vector @@ websearch_to_tsquery('simple', b.brand)
                ) m ON true
                GROUP BY b.brand
            """
            rows = await conn.fetch(
                batch_sql, user_id, monitor_id, date_from, competitor_brands
            )
            counts_by_brand = {row["brand"]: row for row in rows}
            for brand in competitor_brands:
                row = counts_by_brand.get(brand)
                competitor_entries.append(
                    ShareOfVoiceEntry(
                        brand=brand,
                        mention_count=row["mention_count"] if row else 0,
                        percentage=0.0,  # Computed below
                        sentiment_avg=float(row["sentiment_avg"]) if row and row["sentiment_avg"] is not None else None,
                    )
                )

    # Compute percentages
    my_count = my_count or 0
    total = my_count + sum(e.mention_count for e in competitor_entries)

    entries: list[ShareOfVoiceEntry] = []

    # My brand entry
    entries.append(
        ShareOfVoiceEntry(
            brand=monitor_name,
            mention_count=my_count,
            percentage=round(my_count / total * 100, 1) if total > 0 else 100.0,
            sentiment_avg=float(my_sentiment) if my_sentiment is not None else None,
        )
    )

    # Competitor entries with computed percentages
    for e in competitor_entries:
        entries.append(
            ShareOfVoiceEntry(
                brand=e.brand,
                mention_count=e.mention_count,
                percentage=round(e.mention_count / total * 100, 1) if total > 0 else 0.0,
                sentiment_avg=e.sentiment_avg,
            )
        )

    return entries
