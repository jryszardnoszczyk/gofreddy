"""PostgreSQL monitoring repository — monitors, mentions, and cursors."""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from typing import Any, AsyncIterator
from uuid import UUID

import asyncpg

from ..common.exceptions import PoolExhaustedError
from .alerts.models import AlertEvent, AlertRule
from .models import (
    DataSource,
    Mention,
    Monitor,
    MonitorChangelog,
    MonitorRun,
    MonitorSourceCursor,
    SentimentLabel,
    SourceSentiment,
    WeeklyDigestRecord,
)

logger = logging.getLogger(__name__)


def _normalize_date_to(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    if dt.hour == 0 and dt.minute == 0 and dt.second == 0 and dt.microsecond == 0:
        dt = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    return dt


def _row_to_monitor(row: asyncpg.Record) -> Monitor:
    return Monitor(
        id=row["id"],
        user_id=row["user_id"],
        name=row["name"],
        keywords=list(row["keywords"] or []),
        boolean_query=row["boolean_query"],
        sources=[DataSource(s) for s in (row["sources"] or [])],
        is_active=row["is_active"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        client_id=row.get("client_id"),
        next_run_at=row.get("next_run_at"),
        competitor_brands=list(row.get("competitor_brands") or []),
        last_user_edit_at=row.get("last_user_edit_at"),
        last_analysis_at=row.get("last_analysis_at"),
    )


def _row_to_changelog(row: asyncpg.Record) -> MonitorChangelog:
    raw_detail = row["change_detail"]
    if isinstance(raw_detail, str):
        change_detail = json.loads(raw_detail)
    else:
        change_detail = raw_detail or {}
    return MonitorChangelog(
        id=row["id"],
        monitor_id=row["monitor_id"],
        change_type=row["change_type"],
        change_detail=change_detail,
        rationale=row["rationale"],
        autonomy_level=row["autonomy_level"],
        status=row["status"],
        applied_by=row["applied_by"],
        analysis_run_id=row.get("analysis_run_id"),
        created_at=row["created_at"],
    )


def _row_to_monitor_run(row: asyncpg.Record) -> MonitorRun:
    raw_details = row["error_details"]
    if isinstance(raw_details, str):
        error_details = json.loads(raw_details)
    else:
        error_details = raw_details

    return MonitorRun(
        id=row["id"],
        monitor_id=row["monitor_id"],
        started_at=row["started_at"],
        completed_at=row["completed_at"],
        status=row["status"],
        mentions_ingested=row["mentions_ingested"],
        sources_succeeded=row["sources_succeeded"],
        sources_failed=row["sources_failed"],
        error_details=error_details,
    )


def _row_to_alert_rule(row: asyncpg.Record) -> AlertRule:
    raw_config = row["config"]
    if isinstance(raw_config, str):
        config = json.loads(raw_config)
    else:
        config = raw_config or {}
    return AlertRule(
        id=row["id"],
        monitor_id=row["monitor_id"],
        user_id=row["user_id"],
        rule_type=row["rule_type"],
        config=config,
        webhook_url=row["webhook_url"],
        is_active=row["is_active"],
        cooldown_minutes=row["cooldown_minutes"],
        last_triggered_at=row["last_triggered_at"],
        consecutive_failures=row["consecutive_failures"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_alert_event(row: asyncpg.Record) -> AlertEvent:
    raw_payload = row["payload"]
    if isinstance(raw_payload, str):
        payload = json.loads(raw_payload)
    else:
        payload = raw_payload or {}
    return AlertEvent(
        id=row["id"],
        rule_id=row["rule_id"],
        monitor_id=row["monitor_id"],
        triggered_at=row["triggered_at"],
        condition_summary=row["condition_summary"],
        payload=payload,
        delivery_status=row["delivery_status"],
        delivery_attempts=row["delivery_attempts"],
        last_delivery_at=row["last_delivery_at"],
        created_at=row["created_at"],
    )


def _row_to_mention(row: asyncpg.Record) -> Mention:
    raw_metadata = row["metadata"]
    if isinstance(raw_metadata, str):
        metadata = json.loads(raw_metadata)
    else:
        metadata = raw_metadata or {}

    sentiment_label_val = row["sentiment_label"]
    return Mention(
        id=row["id"],
        monitor_id=row["monitor_id"],
        source=DataSource(row["source"]),
        source_id=row["source_id"],
        author_handle=row["author_handle"],
        author_name=row["author_name"],
        content=row["content"],
        url=row["url"],
        published_at=row["published_at"],
        sentiment_score=row["sentiment_score"],
        sentiment_label=SentimentLabel(sentiment_label_val) if sentiment_label_val else None,
        engagement_likes=row["engagement_likes"],
        engagement_shares=row["engagement_shares"],
        engagement_comments=row["engagement_comments"],
        reach_estimate=row["reach_estimate"],
        language=row["language"],
        geo_country=row["geo_country"],
        media_urls=list(row["media_urls"] or []),
        metadata=metadata,
        created_at=row["created_at"],
        intent=row.get("intent"),
        classified_at=row.get("classified_at"),
    )


class PostgresMonitoringRepository:
    """PostgreSQL repository for monitors, mentions, and cursors."""

    ACQUIRE_TIMEOUT = 5.0

    # ── Monitor CRUD ──

    _CREATE_MONITOR = """
        INSERT INTO monitors (user_id, name, keywords, boolean_query, sources, is_active, competitor_brands)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING *
    """

    _GET_MONITOR = """
        SELECT * FROM monitors WHERE id = $1 AND user_id = $2
    """

    _LIST_MONITORS = """
        SELECT * FROM monitors WHERE user_id = $1 ORDER BY created_at DESC
    """

    _LIST_MONITORS_ENRICHED = """
        SELECT m.*,
               mr.status AS last_run_status,
               mr.completed_at AS last_run_completed_at,
               mr.error_details AS last_run_error,
               (SELECT COUNT(*) FROM mentions mn
                WHERE mn.monitor_id = m.id) AS mention_count,
               (SELECT COUNT(*) FROM alert_events ae
                JOIN alert_rules ar ON ar.id = ae.rule_id
                WHERE ar.monitor_id = m.id
                AND ae.created_at > NOW() - INTERVAL '24 hours') AS alert_count_24h,
               (SELECT COUNT(*) FROM monitor_changelog mc
                WHERE mc.monitor_id = m.id
                AND mc.status = 'pending') AS pending_changes_count
        FROM monitors m
        LEFT JOIN LATERAL (
            SELECT status, completed_at, error_details
            FROM monitor_runs
            WHERE monitor_id = m.id
            ORDER BY started_at DESC
            LIMIT 1
        ) mr ON true
        WHERE m.user_id = $1
        ORDER BY m.next_run_at ASC NULLS LAST
    """

    _DELETE_MONITOR = """
        DELETE FROM monitors WHERE id = $1 AND user_id = $2 RETURNING id
    """

    _COUNT_MONITORS = """
        SELECT COUNT(*) FROM monitors WHERE user_id = $1
    """

    _COUNT_MENTIONS = """
        SELECT COUNT(*) FROM mentions WHERE monitor_id = $1
    """

    _GET_ACTIVE_MONITORS = """
        SELECT * FROM monitors WHERE is_active = TRUE
    """

    # ── Alert rules ──

    _CREATE_ALERT_RULE = """
        INSERT INTO alert_rules (monitor_id, user_id, rule_type, config, webhook_url, cooldown_minutes)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING *
    """

    _GET_ALERT_RULE = """
        SELECT ar.* FROM alert_rules ar
        JOIN monitors m ON m.id = ar.monitor_id
        WHERE ar.id = $1 AND m.user_id = $2
    """

    _LIST_ALERT_RULES = """
        SELECT ar.* FROM alert_rules ar
        JOIN monitors m ON m.id = ar.monitor_id
        WHERE ar.monitor_id = $1 AND m.user_id = $2
        ORDER BY ar.created_at DESC
    """

    _DELETE_ALERT_RULE = """
        DELETE FROM alert_rules ar
        USING monitors m
        WHERE ar.id = $1 AND m.id = ar.monitor_id AND m.user_id = $2
        RETURNING ar.id
    """

    _COUNT_ALERT_RULES = """
        SELECT COUNT(*) FROM alert_rules WHERE monitor_id = $1
    """

    _GET_ACTIVE_RULES_FOR_MONITOR = """
        SELECT * FROM alert_rules
        WHERE monitor_id = $1 AND is_active = TRUE
    """

    _COUNT_MENTIONS_IN_WINDOW = """
        SELECT COUNT(*) FROM mentions
        WHERE monitor_id = $1
          AND created_at >= $2
          AND created_at < $3
    """

    _COUNT_COMPLETED_RUNS = """
        SELECT COUNT(*) FROM monitor_runs
        WHERE monitor_id = $1 AND status = 'completed'
    """

    _CREATE_ALERT_EVENT = """
        INSERT INTO alert_events (rule_id, monitor_id, condition_summary, payload)
        VALUES ($1, $2, $3, $4)
        RETURNING *
    """

    _UPDATE_ALERT_EVENT_STATUS = """
        UPDATE alert_events
        SET delivery_status = $2, delivery_attempts = $3, last_delivery_at = NOW()
        WHERE id = $1
    """

    _LIST_ALERT_EVENTS = """
        SELECT ae.* FROM alert_events ae
        JOIN monitors m ON m.id = ae.monitor_id
        WHERE ae.monitor_id = $1 AND m.user_id = $2
        ORDER BY ae.triggered_at DESC
        LIMIT $3 OFFSET $4
    """

    # ── Mention queries ──

    _INSERT_MENTION = """
        INSERT INTO mentions (
            monitor_id, source, source_id, author_handle, author_name,
            content, url, published_at, sentiment_score, sentiment_label,
            engagement_likes, engagement_shares, engagement_comments,
            reach_estimate, language, geo_country, media_urls, metadata
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
            $11, $12, $13, $14, $15, $16, $17, $18
        ) ON CONFLICT (monitor_id, source, source_id) DO NOTHING
        RETURNING id
    """

    _GET_MENTIONS = """
        SELECT m.* FROM mentions m
        JOIN monitors mon ON mon.id = m.monitor_id
        WHERE mon.user_id = $1 AND m.monitor_id = $2
    """

    _SEARCH_MENTIONS = """
        WITH query AS (SELECT websearch_to_tsquery('simple', $3) AS q)
        SELECT m.* FROM mentions m
        JOIN monitors mon ON mon.id = m.monitor_id, query
        WHERE mon.user_id = $1 AND m.monitor_id = $2
            AND m.search_vector @@ query.q
        ORDER BY ts_rank(m.search_vector, query.q) DESC
        LIMIT $4 OFFSET $5
    """

    # ── Cursor ──

    _GET_CURSOR = """
        SELECT * FROM monitor_source_cursors
        WHERE monitor_id = $1 AND source = $2
    """

    _UPSERT_CURSOR = """
        INSERT INTO monitor_source_cursors (monitor_id, source, cursor_value)
        VALUES ($1, $2, $3)
        ON CONFLICT (monitor_id, source)
        DO UPDATE SET cursor_value = $3, updated_at = NOW()
    """

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    @asynccontextmanager
    async def _acquire_connection(self) -> AsyncIterator[Any]:
        try:
            async with asyncio.timeout(self.ACQUIRE_TIMEOUT):
                conn = await self._pool.acquire()
        except asyncio.TimeoutError:
            raise PoolExhaustedError(
                pool_size=self._pool.get_size(),
                timeout_seconds=self.ACQUIRE_TIMEOUT,
            )
        try:
            yield conn
        finally:
            await self._pool.release(conn)

    # ── Monitor CRUD ──

    async def create_monitor(
        self,
        user_id: UUID,
        name: str,
        keywords: list[str],
        sources: list[DataSource],
        *,
        boolean_query: str | None = None,
        is_active: bool = True,
        competitor_brands: list[str] | None = None,
    ) -> Monitor:
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(
                self._CREATE_MONITOR,
                user_id,
                name,
                keywords,
                boolean_query,
                [s.value for s in sources],
                is_active,
                competitor_brands or [],
            )
            return _row_to_monitor(row)

    async def get_monitor(self, monitor_id: UUID, user_id: UUID) -> Monitor | None:
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(self._GET_MONITOR, monitor_id, user_id)
            return _row_to_monitor(row) if row else None

    async def list_monitors(self, user_id: UUID) -> list[Monitor]:
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(self._LIST_MONITORS, user_id)
            return [_row_to_monitor(r) for r in rows]

    async def list_monitors_enriched(self, user_id: UUID) -> list[dict[str, Any]]:
        """Enriched monitor list with run status, mention count, alert count — single SQL."""
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(self._LIST_MONITORS_ENRICHED, user_id)
            results = []
            for row in rows:
                # Parse error_details from last run
                raw_error = row["last_run_error"]
                if isinstance(raw_error, str):
                    error_details = json.loads(raw_error)
                else:
                    error_details = raw_error

                # Extract only the sanitized "reason" key, truncated
                last_run_error = (
                    error_details.get("reason", "Unknown error")[:200]
                    if isinstance(error_details, dict)
                    else None
                )

                results.append({
                    "id": row["id"],
                    "name": row["name"],
                    "keywords": list(row["keywords"] or []),
                    "boolean_query": row["boolean_query"],
                    "sources": list(row["sources"] or []),
                    "competitor_brands": list(row.get("competitor_brands") or []),
                    "is_active": row["is_active"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "next_run_at": row.get("next_run_at"),
                    "last_run_status": row["last_run_status"],
                    "last_run_completed_at": row["last_run_completed_at"],
                    "last_run_error": last_run_error,
                    "alert_count_24h": row["alert_count_24h"],
                    "mention_count": row["mention_count"],
                    "pending_changes_count": row.get("pending_changes_count", 0),
                })
            return results

    async def update_monitor(
        self,
        monitor_id: UUID,
        user_id: UUID,
        **fields: Any,
    ) -> Monitor | None:
        """PATCH semantics — only update provided fields."""
        allowed = {"name", "keywords", "boolean_query", "sources", "is_active", "competitor_brands", "last_user_edit_at"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return await self.get_monitor(monitor_id, user_id)

        set_clauses = []
        params: list[Any] = []
        idx = 3  # $1=monitor_id, $2=user_id

        for key, val in updates.items():
            if key == "sources":
                val = [s.value if isinstance(s, DataSource) else s for s in val]
            set_clauses.append(f"{key} = ${idx}")
            params.append(val)
            idx += 1

        sql = f"""
            UPDATE monitors SET {', '.join(set_clauses)}
            WHERE id = $1 AND user_id = $2
            RETURNING *
        """

        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(sql, monitor_id, user_id, *params)
            return _row_to_monitor(row) if row else None

    async def delete_monitor(self, monitor_id: UUID, user_id: UUID) -> bool:
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(self._DELETE_MONITOR, monitor_id, user_id)
            return row is not None

    async def count_monitors(self, user_id: UUID) -> int:
        async with self._acquire_connection() as conn:
            return await conn.fetchval(self._COUNT_MONITORS, user_id)

    async def get_active_monitors(self) -> list[Monitor]:
        """System-level: all active monitors across all users (for scheduler)."""
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(self._GET_ACTIVE_MONITORS)
            return [_row_to_monitor(r) for r in rows]

    async def count_mentions(self, monitor_id: UUID) -> int:
        async with self._acquire_connection() as conn:
            return await conn.fetchval(self._COUNT_MENTIONS, monitor_id)

    async def count_discover_searches_today(self, user_id: UUID) -> int:
        async with self._acquire_connection() as conn:
            return await conn.fetchval(
                """
                SELECT COUNT(*) FROM usage_records
                WHERE user_id = $1
                  AND operation = 'discover_search'
                  AND recorded_at >= CURRENT_DATE
                """,
                user_id,
            )

    async def record_discover_search(self, user_id: UUID) -> None:
        async with self._acquire_connection() as conn:
            await conn.execute(
                """
                INSERT INTO usage_records (user_id, operation, recorded_at)
                VALUES ($1, 'discover_search', NOW())
                """,
                user_id,
            )

    # ── Mention insert ──

    _BATCH_INSERT_MENTIONS = """
        INSERT INTO mentions (
            monitor_id, source, source_id, author_handle, author_name,
            content, url, published_at, sentiment_score, sentiment_label,
            engagement_likes, engagement_shares, engagement_comments,
            reach_estimate, language, geo_country, media_urls, metadata
        )
        SELECT $1,
            unnest($2::text[]), unnest($3::text[]), unnest($4::text[]), unnest($5::text[]),
            unnest($6::text[]), unnest($7::text[]), unnest($8::timestamptz[]),
            unnest($9::float8[]), unnest($10::text[]),
            unnest($11::int[]), unnest($12::int[]), unnest($13::int[]),
            unnest($14::int[]), unnest($15::text[]), unnest($16::text[]),
            unnest($17::text[]), unnest($18::jsonb[])
        ON CONFLICT (monitor_id, source, source_id) DO NOTHING
        RETURNING id
    """

    @staticmethod
    def _unzip_mention_tuples(mentions: list[tuple[Any, ...]]) -> list[list]:
        """Transpose list-of-tuples into list-of-columns for unnest batch insert."""
        if not mentions:
            return [[] for _ in range(17)]
        return [list(col) for col in zip(*mentions)]

    async def insert_mentions(
        self,
        monitor_id: UUID,
        mentions: list[tuple[Any, ...]],
    ) -> int:
        """Batch insert mentions via unnest. Returns count of newly inserted rows."""
        if not mentions:
            return 0
        cols = self._unzip_mention_tuples(mentions)
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(self._BATCH_INSERT_MENTIONS, monitor_id, *cols)
        return len(rows)

    async def insert_mentions_and_advance_cursor(
        self,
        monitor_id: UUID,
        mentions: list[tuple[Any, ...]],
        source: DataSource,
        cursor_value: str,
    ) -> int:
        """Transactional: batch insert mentions + advance cursor atomically."""
        if not mentions:
            return 0
        cols = self._unzip_mention_tuples(mentions)
        async with self._acquire_connection() as conn:
            async with conn.transaction():
                rows = await conn.fetch(
                    self._BATCH_INSERT_MENTIONS, monitor_id, *cols
                )
                await conn.execute(
                    self._UPSERT_CURSOR,
                    monitor_id,
                    source.value,
                    cursor_value,
                )
        return len(rows)

    # ── Mention queries ──

    async def get_mentions(
        self,
        user_id: UUID,
        monitor_id: UUID,
        *,
        source: DataSource | None = None,
        sentiment: SentimentLabel | None = None,
        sentiment_min: float | None = None,
        sentiment_max: float | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Mention]:
        """IDOR-safe: JOINs through monitors to verify user_id."""
        sql = self._GET_MENTIONS
        params: list[Any] = [user_id, monitor_id]
        idx = 3

        if source is not None:
            sql += f" AND m.source = ${idx}"
            params.append(source.value)
            idx += 1
        if sentiment is not None:
            sql += f" AND m.sentiment_label = ${idx}"
            params.append(sentiment.value)
            idx += 1
        if sentiment_min is not None:
            sql += f" AND m.sentiment_score >= ${idx}"
            params.append(sentiment_min)
            idx += 1
        if sentiment_max is not None:
            sql += f" AND m.sentiment_score <= ${idx}"
            params.append(sentiment_max)
            idx += 1
        if date_from is not None:
            sql += f" AND m.published_at >= ${idx}"
            params.append(date_from)
            idx += 1
        if date_to is not None:
            sql += f" AND m.published_at <= ${idx}"
            params.append(_normalize_date_to(date_to))
            idx += 1

        sql += f" ORDER BY m.published_at DESC NULLS LAST LIMIT ${idx} OFFSET ${idx + 1}"
        params.extend([limit, offset])

        async with self._acquire_connection() as conn:
            rows = await conn.fetch(sql, *params)
            return [_row_to_mention(r) for r in rows]

    async def search_mentions(
        self,
        user_id: UUID,
        monitor_id: UUID,
        query: str,
        *,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Mention], int]:
        """FTS search with IDOR protection. Returns (mentions, total_count)."""
        sql = """
            WITH query AS (SELECT websearch_to_tsquery('simple', $3) AS q)
            SELECT m.*, COUNT(*) OVER() AS total_count,
                   ts_rank(m.search_vector, query.q) AS rank
            FROM mentions m
            JOIN monitors mon ON mon.id = m.monitor_id, query
            WHERE mon.user_id = $1 AND m.monitor_id = $2
                AND m.search_vector @@ query.q
        """
        params: list = [user_id, monitor_id, query]
        idx = 4

        if date_from is not None:
            sql += f" AND m.published_at >= ${idx}"
            params.append(date_from)
            idx += 1
        if date_to is not None:
            sql += f" AND m.published_at <= ${idx}"
            params.append(_normalize_date_to(date_to))
            idx += 1

        sql += f" ORDER BY rank DESC LIMIT ${idx} OFFSET ${idx + 1}"
        params.extend([limit, offset])

        async with self._acquire_connection() as conn:
            rows = await conn.fetch(sql, *params)
            mentions = [_row_to_mention(r) for r in rows]
            total_count = rows[0]["total_count"] if rows else 0
            return mentions, total_count

    async def query_mentions(
        self,
        monitor_id: UUID,
        user_id: UUID,
        *,
        q: str | None = None,
        source: DataSource | None = None,
        sentiment: SentimentLabel | None = None,
        intent: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        sort_by: str = "published_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Mention], int]:
        """Unified mention query with FTS, filters, sorting, and total count."""
        params: list[Any] = [user_id, monitor_id]
        idx = 3
        where_clauses: list[str] = []

        # FTS
        ts_query_ref = None
        if q and q.strip():
            where_clauses.append(f"m.search_vector @@ websearch_to_tsquery('english', ${idx})")
            ts_query_ref = f"websearch_to_tsquery('english', ${idx})"
            params.append(q)
            idx += 1

        if source is not None:
            where_clauses.append(f"m.source = ${idx}")
            params.append(source.value)
            idx += 1

        if sentiment is not None:
            where_clauses.append(f"m.sentiment_label = ${idx}")
            params.append(sentiment.value)
            idx += 1

        if intent is not None:
            where_clauses.append(f"m.intent = ${idx}")
            params.append(intent)
            idx += 1

        if date_from is not None:
            where_clauses.append(f"m.published_at >= ${idx}")
            params.append(date_from)
            idx += 1

        if date_to is not None:
            where_clauses.append(f"m.published_at <= ${idx}")
            params.append(_normalize_date_to(date_to))
            idx += 1

        where_sql = (" AND " + " AND ".join(where_clauses)) if where_clauses else ""

        # Sorting
        if sort_by == "relevance" and ts_query_ref:
            order_sql = f"ts_rank(m.search_vector, {ts_query_ref}) DESC"
        elif sort_by == "engagement":
            direction = "DESC" if sort_order == "desc" else "ASC"
            order_sql = f"(COALESCE(m.engagement_likes,0) + COALESCE(m.engagement_shares,0) + COALESCE(m.engagement_comments,0)) {direction}"
        else:
            direction = "DESC" if sort_order == "desc" else "ASC"
            order_sql = f"m.published_at {direction} NULLS LAST"

        sql = f"""
            WITH filtered AS (
                SELECT m.* FROM mentions m
                JOIN monitors mon ON mon.id = m.monitor_id
                WHERE mon.user_id = $1 AND m.monitor_id = $2{where_sql}
            )
            SELECT *, COUNT(*) OVER() AS total_count
            FROM filtered m
            ORDER BY {order_sql}
            LIMIT ${idx} OFFSET ${idx + 1}
        """
        params.extend([limit, offset])

        async with self._acquire_connection() as conn:
            rows = await conn.fetch(sql, *params)
            mentions = [_row_to_mention(r) for r in rows]
            total_count = rows[0]["total_count"] if rows else 0
            return mentions, total_count

    async def check_and_claim_run(
        self,
        monitor_id: UUID,
        cooldown_minutes: int,
        trigger: str,
    ) -> bool:
        """Atomically check cooldown and insert run record. Returns True if run was created."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO monitor_runs (monitor_id, status, trigger)
                SELECT $1, 'pending', $2
                WHERE NOT EXISTS (
                    SELECT 1 FROM monitor_runs
                    WHERE monitor_id = $1
                    AND started_at > NOW() - ($3 || ' minutes')::interval
                    AND status IN ('pending', 'running')
                )
                RETURNING id
                """,
                monitor_id,
                trigger,
                str(cooldown_minutes),
            )
            return row is not None

    # ── Cursor ──

    async def get_cursor(
        self, monitor_id: UUID, source: DataSource
    ) -> MonitorSourceCursor | None:
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(self._GET_CURSOR, monitor_id, source.value)
            if row is None:
                return None
            return MonitorSourceCursor(
                monitor_id=row["monitor_id"],
                source=DataSource(row["source"]),
                cursor_value=row["cursor_value"],
                updated_at=row["updated_at"],
            )

    # ── Scheduling + Runs ──

    async def get_due_monitors(self, limit: int = 50) -> list[Monitor]:
        """System-level: monitors where next_run_at <= NOW() and is_active."""
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM monitors
                WHERE is_active = TRUE AND next_run_at <= NOW()
                ORDER BY next_run_at ASC
                LIMIT $1
                """,
                limit,
            )
            return [_row_to_monitor(r) for r in rows]

    async def get_monitor_by_id_system(self, monitor_id: UUID) -> Monitor | None:
        """System-level: get monitor without user_id check (for workers)."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM monitors WHERE id = $1", monitor_id
            )
            return _row_to_monitor(row) if row else None

    async def try_create_run(self, monitor_id: UUID) -> bool:
        """Atomically create a 'running' row. Returns False if already running."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO monitor_runs (monitor_id, status)
                VALUES ($1, 'running')
                ON CONFLICT DO NOTHING
                RETURNING id
                """,
                monitor_id,
            )
            return row is not None

    async def mark_stale_runs_failed(self, threshold_minutes: int = 45) -> int:
        """Mark runs stuck in 'running' for > threshold as failed."""
        async with self._acquire_connection() as conn:
            result = await conn.execute(
                """
                UPDATE monitor_runs
                SET status = 'failed',
                    completed_at = NOW(),
                    error_details = '{"reason": "stale_run_recovery"}'::jsonb
                WHERE status = 'running'
                  AND started_at < NOW() - ($1 || ' minutes')::interval
                """,
                str(threshold_minutes),
            )
            return int(result.split()[-1])  # "UPDATE N"

    async def fail_run(self, monitor_id: UUID, error: str) -> None:
        """Mark the current running run for this monitor as failed."""
        async with self._acquire_connection() as conn:
            await conn.execute(
                """
                UPDATE monitor_runs
                SET status = 'failed', completed_at = NOW(),
                    error_details = jsonb_build_object('reason', $2)
                WHERE monitor_id = $1 AND status = 'running'
                """,
                monitor_id,
                error,
            )

    async def complete_run_and_advance(
        self,
        monitor_id: UUID,
        mentions_ingested: int,
        sources_succeeded: int,
        sources_failed: int,
        error_details: dict | None = None,
        interval_minutes: int = 30,
    ) -> None:
        """Atomically complete the run AND advance next_run_at."""
        run_status = (
            "failed"
            if sources_succeeded == 0 and sources_failed > 0
            else "completed"
        )
        async with self._acquire_connection() as conn:
            async with conn.transaction():
                await conn.execute(
                    """
                    UPDATE monitor_runs
                    SET status = $2, completed_at = NOW(),
                        mentions_ingested = $3, sources_succeeded = $4,
                        sources_failed = $5, error_details = $6
                    WHERE monitor_id = $1 AND status = 'running'
                    """,
                    monitor_id,
                    run_status,
                    mentions_ingested,
                    sources_succeeded,
                    sources_failed,
                    json.dumps(error_details) if error_details else None,
                )
                await conn.execute(
                    """
                    UPDATE monitors
                    SET next_run_at = NOW() + ($2 || ' minutes')::interval
                    WHERE id = $1
                    """,
                    monitor_id,
                    str(interval_minutes),
                )

    async def get_runs(
        self,
        monitor_id: UUID,
        user_id: UUID,
        limit: int = 25,
        offset: int = 0,
    ) -> list[MonitorRun]:
        """User-facing: get run history for a monitor (IDOR-safe)."""
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT r.* FROM monitor_runs r
                JOIN monitors m ON m.id = r.monitor_id
                WHERE r.monitor_id = $1 AND m.user_id = $2
                ORDER BY r.started_at DESC
                LIMIT $3 OFFSET $4
                """,
                monitor_id,
                user_id,
                limit,
                offset,
            )
            return [_row_to_monitor_run(r) for r in rows]

    async def count_mentions_this_month(self, user_id: UUID) -> int:
        """Count mentions ingested this calendar month for a user's monitors.

        Uses subquery + composite index for index-only scan (avoids JOIN).
        """
        async with self._acquire_connection() as conn:
            return await conn.fetchval(
                """
                SELECT COUNT(*) FROM mentions
                WHERE monitor_id = ANY(SELECT id FROM monitors WHERE user_id = $1)
                  AND created_at >= date_trunc('month', NOW())
                """,
                user_id,
            )
    # ── Aggregation queries (PR-072) ──

    async def get_mention_aggregates(
        self,
        monitor_id: UUID,
        user_id: UUID,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> dict[str, Any]:
        """SQL-level aggregation for dashboard stats. Returns source/sentiment/author breakdowns."""
        params: list[Any] = [user_id, monitor_id]
        idx = 3
        date_clauses = ""
        if date_from is not None:
            date_clauses += f" AND m.published_at >= ${idx}"
            params.append(date_from)
            idx += 1
        if date_to is not None:
            date_clauses += f" AND m.published_at < ${idx}"
            params.append(_normalize_date_to(date_to))
            idx += 1
        sql = f"""
            SELECT
                m.source,
                m.sentiment_label,
                COUNT(*) AS cnt,
                SUM(COALESCE(m.engagement_likes, 0) + COALESCE(m.engagement_shares, 0) + COALESCE(m.engagement_comments, 0)) AS total_engagement,
                m.author_handle
            FROM mentions m
            JOIN monitors mon ON mon.id = m.monitor_id
            WHERE mon.user_id = $1 AND m.monitor_id = $2{date_clauses}
            GROUP BY m.source, m.sentiment_label, m.author_handle
            ORDER BY cnt DESC
        """
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(sql, *params)

        # Aggregate into structured breakdown
        source_counts: dict[str, int] = {}
        sentiment_counts: dict[str, int] = {}
        author_counts: dict[str, int] = {}
        total_engagement = 0

        for row in rows:
            src = row["source"]
            source_counts[src] = source_counts.get(src, 0) + row["cnt"]

            sent = row["sentiment_label"] or "unknown"
            sentiment_counts[sent] = sentiment_counts.get(sent, 0) + row["cnt"]

            author = row["author_handle"] or "unknown"
            author_counts[author] = author_counts.get(author, 0) + row["cnt"]

            total_engagement += row["total_engagement"] or 0

        # Top 10 authors by mention count
        top_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "source_breakdown": source_counts,
            "sentiment_breakdown": sentiment_counts,
            "top_authors": [{"handle": h, "count": c} for h, c in top_authors],
            "total_engagement": total_engagement,
        }

    async def get_sentiment_by_source(
        self,
        monitor_id: UUID,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[SourceSentiment]:
        """Per-source sentiment breakdown for cross-signal anomaly detection."""
        params: list[Any] = [monitor_id]
        idx = 2
        date_clauses = ""
        if date_from is not None:
            date_clauses += f" AND m.published_at >= ${idx}"
            params.append(date_from)
            idx += 1
        if date_to is not None:
            date_clauses += f" AND m.published_at < ${idx}"
            params.append(_normalize_date_to(date_to))
            idx += 1
        sql = f"""
            SELECT
                m.source,
                AVG(m.sentiment_score) AS avg_sentiment,
                COUNT(*) AS mention_count,
                date_trunc('day', m.published_at) AS bucket
            FROM mentions m
            WHERE m.monitor_id = $1
              AND m.sentiment_score IS NOT NULL{date_clauses}
            GROUP BY m.source, date_trunc('day', m.published_at)
            ORDER BY bucket DESC, m.source
        """
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(sql, *params)
        return [
            SourceSentiment(
                source=DataSource(r["source"]),
                avg_sentiment=float(r["avg_sentiment"]),
                mention_count=r["mention_count"],
                bucket=r["bucket"],
            )
            for r in rows
        ]

    # ── Stubs for downstream PRs ──

    async def update_mention_engagement(
        self,
        mention_id: UUID,
        likes: int,
        shares: int,
        comments: int,
    ) -> bool:
        """Stub for PR-071 enrichment. Updates engagement metrics without corrupting ingestion."""
        async with self._acquire_connection() as conn:
            result = await conn.execute(
                """
                UPDATE mentions
                SET engagement_likes = $2, engagement_shares = $3, engagement_comments = $4
                WHERE id = $1
                """,
                mention_id,
                likes,
                shares,
                comments,
            )
            return result == "UPDATE 1"

    # ── Alert rules (PR-068) ──

    async def create_alert_rule(
        self,
        monitor_id: UUID,
        user_id: UUID,
        rule_type: str,
        config: dict,
        webhook_url: str,
        cooldown_minutes: int,
    ) -> AlertRule:
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(
                self._CREATE_ALERT_RULE,
                monitor_id, user_id, rule_type,
                json.dumps(config), webhook_url, cooldown_minutes,
            )
            return _row_to_alert_rule(row)

    async def get_alert_rule(self, rule_id: UUID, user_id: UUID) -> AlertRule | None:
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(self._GET_ALERT_RULE, rule_id, user_id)
            return _row_to_alert_rule(row) if row else None

    async def list_alert_rules(self, monitor_id: UUID, user_id: UUID) -> list[AlertRule]:
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(self._LIST_ALERT_RULES, monitor_id, user_id)
            return [_row_to_alert_rule(r) for r in rows]

    async def update_alert_rule(
        self,
        rule_id: UUID,
        user_id: UUID,
        **fields,
    ) -> AlertRule | None:
        """PATCH semantics — only update provided fields."""
        allowed = {"config", "webhook_url", "is_active", "cooldown_minutes"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return await self.get_alert_rule(rule_id, user_id)

        set_clauses = ["updated_at = NOW()"]
        params: list = []
        idx = 3  # $1=rule_id, $2=user_id

        for key, val in updates.items():
            if key == "config":
                val = json.dumps(val)
            set_clauses.append(f"{key} = ${idx}")
            params.append(val)
            idx += 1

        # Reset consecutive_failures when re-enabling
        if updates.get("is_active") is True:
            set_clauses.append("consecutive_failures = 0")

        sql = f"""
            UPDATE alert_rules ar SET {', '.join(set_clauses)}
            FROM monitors m
            WHERE ar.id = $1 AND m.id = ar.monitor_id AND m.user_id = $2
            RETURNING ar.*
        """

        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(sql, rule_id, user_id, *params)
            return _row_to_alert_rule(row) if row else None

    async def delete_alert_rule(self, rule_id: UUID, user_id: UUID) -> bool:
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(self._DELETE_ALERT_RULE, rule_id, user_id)
            return row is not None

    async def count_alert_rules(self, monitor_id: UUID) -> int:
        async with self._acquire_connection() as conn:
            return await conn.fetchval(self._COUNT_ALERT_RULES, monitor_id)

    async def get_active_rules_for_monitor(self, monitor_id: UUID) -> list[AlertRule]:
        """System-level: no user_id check (called from worker)."""
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(self._GET_ACTIVE_RULES_FOR_MONITOR, monitor_id)
            return [_row_to_alert_rule(r) for r in rows]

    async def count_mentions_in_window(
        self, monitor_id: UUID, start: datetime, end: datetime,
    ) -> int:
        async with self._acquire_connection() as conn:
            return await conn.fetchval(
                self._COUNT_MENTIONS_IN_WINDOW, monitor_id, start, end
            )

    async def count_completed_runs(self, monitor_id: UUID) -> int:
        async with self._acquire_connection() as conn:
            return await conn.fetchval(self._COUNT_COMPLETED_RUNS, monitor_id)

    async def create_alert_event_and_trigger(
        self,
        rule_id: UUID,
        monitor_id: UUID,
        condition_summary: str,
        payload: dict,
    ) -> AlertEvent:
        """Atomic: insert event + update last_triggered_at in single transaction."""
        async with self._acquire_connection() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    self._CREATE_ALERT_EVENT,
                    rule_id, monitor_id, condition_summary, json.dumps(payload),
                )
                await conn.execute(
                    "UPDATE alert_rules SET last_triggered_at = NOW() WHERE id = $1",
                    rule_id,
                )
                return _row_to_alert_event(row)

    async def update_alert_event_status(
        self, event_id: UUID, status: str, attempts: int,
    ) -> None:
        async with self._acquire_connection() as conn:
            await conn.execute(
                self._UPDATE_ALERT_EVENT_STATUS, event_id, status, attempts,
            )

    async def list_alert_events(
        self,
        monitor_id: UUID,
        user_id: UUID,
        limit: int = 25,
        offset: int = 0,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[AlertEvent]:
        params: list[Any] = [monitor_id, user_id]
        idx = 3
        date_clauses = ""
        if date_from is not None:
            date_clauses += f" AND ae.triggered_at >= ${idx}"
            params.append(date_from)
            idx += 1
        if date_to is not None:
            date_clauses += f" AND ae.triggered_at < ${idx}"
            params.append(_normalize_date_to(date_to))
            idx += 1
        params.extend([limit, offset])
        sql = f"""
            SELECT ae.* FROM alert_events ae
            JOIN monitors m ON m.id = ae.monitor_id
            WHERE ae.monitor_id = $1 AND m.user_id = $2{date_clauses}
            ORDER BY ae.triggered_at DESC
            LIMIT ${idx} OFFSET ${idx + 1}
        """
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(sql, *params)
            return [_row_to_alert_event(r) for r in rows]

    async def increment_consecutive_failures(self, rule_id: UUID) -> int:
        """Increment and return new count."""
        async with self._acquire_connection() as conn:
            return await conn.fetchval(
                """
                UPDATE alert_rules
                SET consecutive_failures = consecutive_failures + 1
                WHERE id = $1
                RETURNING consecutive_failures
                """,
                rule_id,
            )

    async def reset_consecutive_failures(self, rule_id: UUID) -> None:
        async with self._acquire_connection() as conn:
            await conn.execute(
                "UPDATE alert_rules SET consecutive_failures = 0 WHERE id = $1",
                rule_id,
            )

    async def disable_rule(self, rule_id: UUID) -> None:
        """Circuit breaker: disable rule after too many consecutive failures."""
        async with self._acquire_connection() as conn:
            await conn.execute(
                "UPDATE alert_rules SET is_active = FALSE, updated_at = NOW() WHERE id = $1",
                rule_id,
            )

    # ── Intelligence Layer (PR-071) ──

    async def get_unclassified_mentions(
        self,
        monitor_id: UUID,
        user_id: UUID,
        limit: int = 100,
    ) -> list[Mention]:
        """Get mentions without intent classification, oldest first. IDOR-safe."""
        sql = """
            SELECT m.* FROM mentions m
            JOIN monitors mon ON mon.id = m.monitor_id
            WHERE mon.user_id = $1 AND m.monitor_id = $2
              AND m.intent IS NULL
            ORDER BY m.published_at ASC NULLS LAST
            LIMIT $3
        """
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(sql, user_id, monitor_id, limit)
            return [_row_to_mention(r) for r in rows]

    async def update_mention_intents(
        self,
        updates: list[tuple[UUID, str]],
    ) -> int:
        """Batch update intent + classified_at for mentions using unnest pattern."""
        if not updates:
            return 0
        ids = [u[0] for u in updates]
        intents = [u[1] for u in updates]
        sql = """
            UPDATE mentions
            SET intent = u.intent, classified_at = NOW()
            FROM unnest($1::uuid[], $2::text[]) AS u(id, intent)
            WHERE mentions.id = u.id
        """
        async with self._acquire_connection() as conn:
            result = await conn.execute(sql, ids, intents)
            return int(result.split()[-1])  # "UPDATE N"

    async def update_mention_sentiments(
        self,
        updates: list[tuple[UUID, str]],
    ) -> int:
        """Batch update sentiment_label for mentions using unnest pattern."""
        if not updates:
            return 0
        ids = [u[0] for u in updates]
        sentiments = [u[1] for u in updates]
        sql = """
            UPDATE mentions
            SET sentiment_label = u.sentiment
            FROM unnest($1::uuid[], $2::text[]) AS u(id, sentiment)
            WHERE mentions.id = u.id
        """
        async with self._acquire_connection() as conn:
            result = await conn.execute(sql, ids, sentiments)
            return int(result.split()[-1])  # "UPDATE N"

    async def get_daily_classification_count(
        self,
        monitor_id: UUID,
        target_date: date,
    ) -> int:
        """Count mentions classified on a specific date for a monitor."""
        sql = """
            SELECT COUNT(*) FROM mentions
            WHERE monitor_id = $1 AND classified_at::date = $2
        """
        async with self._acquire_connection() as conn:
            return await conn.fetchval(sql, monitor_id, target_date)

    async def get_mentions_for_date(
        self,
        monitor_id: UUID,
        target_date: date,
    ) -> list[Mention]:
        """Get all mentions published on a specific date (system-level, for topic clustering)."""
        sql = """
            SELECT * FROM mentions
            WHERE monitor_id = $1
              AND published_at::date = $2
            ORDER BY published_at ASC
        """
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(sql, monitor_id, target_date)
            return [_row_to_mention(r) for r in rows]

    async def get_mentions_by_ids(
        self,
        monitor_id: UUID,
        mention_ids: list[UUID],
    ) -> list[Mention]:
        """Get mentions by IDs, scoped to a specific monitor. IDOR: caller must verify monitor ownership."""
        if not mention_ids:
            return []
        sql = """
            SELECT * FROM mentions
            WHERE id = ANY($1) AND monitor_id = $2
        """
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(sql, mention_ids, monitor_id)
            return [_row_to_mention(r) for r in rows]

    # ── Changelog (V2 self-optimizing refinement) ──

    async def insert_changelog_entry(
        self,
        monitor_id: UUID,
        change_type: str,
        change_detail: dict[str, Any],
        rationale: str,
        autonomy_level: str,
        status: str = "applied",
        applied_by: str = "system",
        analysis_run_id: UUID | None = None,
    ) -> MonitorChangelog:
        """Insert a changelog entry for a monitor refinement."""
        sql = """
            INSERT INTO monitor_changelog
                (monitor_id, change_type, change_detail, rationale, autonomy_level, status, applied_by, analysis_run_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING *
        """
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(
                sql, monitor_id, change_type, json.dumps(change_detail),
                rationale, autonomy_level, status, applied_by, analysis_run_id,
            )
            return _row_to_changelog(row)

    async def get_changelog(
        self,
        monitor_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[MonitorChangelog], int]:
        """Get changelog entries for a monitor, newest first."""
        sql = """
            WITH filtered AS (
                SELECT * FROM monitor_changelog WHERE monitor_id = $1
            )
            SELECT *, COUNT(*) OVER() AS total_count
            FROM filtered
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
        """
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(sql, monitor_id, limit, offset)
            entries = [_row_to_changelog(r) for r in rows]
            total = rows[0]["total_count"] if rows else 0
            return entries, total

    async def count_changelog_entries(
        self,
        monitor_id: UUID,
        status: str | None = None,
        hours: int | None = None,
    ) -> int:
        """Count changelog entries with optional status and time filters."""
        params: list[Any] = [monitor_id]
        clauses = ["monitor_id = $1"]
        idx = 2
        if status is not None:
            clauses.append(f"status = ${idx}")
            params.append(status)
            idx += 1
        if hours is not None:
            clauses.append(f"created_at >= NOW() - make_interval(hours => ${idx})")
            params.append(hours)
            idx += 1
        sql = f"SELECT COUNT(*) FROM monitor_changelog WHERE {' AND '.join(clauses)}"
        async with self._acquire_connection() as conn:
            return await conn.fetchval(sql, *params)

    async def update_changelog_status(
        self,
        entry_id: UUID,
        monitor_id: UUID,
        new_status: str,
    ) -> MonitorChangelog | None:
        """Update a changelog entry status (approve/reject)."""
        sql = """
            UPDATE monitor_changelog
            SET status = $3
            WHERE id = $1 AND monitor_id = $2 AND status = 'pending'
            RETURNING *
        """
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(sql, entry_id, monitor_id, new_status)
            return _row_to_changelog(row) if row else None

    async def system_update_monitor(
        self,
        monitor_id: UUID,
        **fields: Any,
    ) -> Monitor | None:
        """System-level monitor update — no user_id check. For PostIngestionAnalyzer."""
        allowed = {
            "name", "keywords", "boolean_query", "sources", "is_active",
            "competitor_brands", "last_analysis_at",
        }
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return await self.get_monitor_by_id_system(monitor_id)

        set_clauses = []
        params: list[Any] = [monitor_id]  # $1 = monitor_id
        idx = 2

        for key, val in updates.items():
            if key == "sources":
                val = [s.value if isinstance(s, DataSource) else s for s in val]
            set_clauses.append(f"{key} = ${idx}")
            params.append(val)
            idx += 1

        sql = f"""
            UPDATE monitors SET {', '.join(set_clauses)}
            WHERE id = $1
            RETURNING *
        """
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(sql, *params)
            return _row_to_monitor(row) if row else None

    async def delete_cursors_for_monitor(self, monitor_id: UUID) -> int:
        """Delete all source cursors for a monitor (used after boolean_query changes)."""
        async with self._acquire_connection() as conn:
            result = await conn.execute(
                "DELETE FROM monitor_source_cursors WHERE monitor_id = $1",
                monitor_id,
            )
            # result is like "DELETE 5"
            return int(result.split()[-1]) if result else 0

    # ── Weekly Digests (digest agent persistence) ──

    async def save_weekly_digest(self, digest: WeeklyDigestRecord) -> UUID:
        """Upsert a weekly digest record. Returns the digest ID."""
        sql = """
            INSERT INTO weekly_digests (
                monitor_id, client_id, week_ending, stories, executive_summary,
                action_items, dqs_score, iteration_count, avg_story_delta, generated_at,
                digest_markdown
            ) VALUES ($1, $2, $3, $4::jsonb, $5, $6::jsonb, $7, $8, $9, $10, $11)
            ON CONFLICT (monitor_id, week_ending) DO UPDATE SET
                client_id = EXCLUDED.client_id,
                stories = EXCLUDED.stories,
                executive_summary = EXCLUDED.executive_summary,
                action_items = EXCLUDED.action_items,
                dqs_score = EXCLUDED.dqs_score,
                iteration_count = EXCLUDED.iteration_count,
                avg_story_delta = EXCLUDED.avg_story_delta,
                generated_at = EXCLUDED.generated_at,
                digest_markdown = EXCLUDED.digest_markdown
            RETURNING id
        """
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(
                sql,
                digest.monitor_id, digest.client_id, digest.week_ending,
                json.dumps(digest.stories), digest.executive_summary,
                json.dumps(digest.action_items), digest.dqs_score,
                digest.iteration_count, digest.avg_story_delta, digest.generated_at,
                digest.digest_markdown,
            )
            return row["id"]

    async def get_weekly_digest(
        self, monitor_id: UUID, week_ending: date,
    ) -> WeeklyDigestRecord | None:
        """Get a specific weekly digest by monitor + week."""
        sql = """
            SELECT * FROM weekly_digests
            WHERE monitor_id = $1 AND week_ending = $2
        """
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(sql, monitor_id, week_ending)
            return _row_to_weekly_digest(row) if row else None

    async def list_weekly_digests(
        self, monitor_id: UUID, limit: int = 10,
    ) -> list[WeeklyDigestRecord]:
        """List recent weekly digests for a monitor."""
        sql = """
            SELECT * FROM weekly_digests
            WHERE monitor_id = $1
            ORDER BY week_ending DESC
            LIMIT $2
        """
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(sql, monitor_id, limit)
            return [_row_to_weekly_digest(r) for r in rows]


def _row_to_weekly_digest(row: asyncpg.Record) -> WeeklyDigestRecord:
    raw_stories = row["stories"]
    if isinstance(raw_stories, str):
        stories = json.loads(raw_stories)
    else:
        stories = raw_stories or []

    raw_actions = row["action_items"]
    if isinstance(raw_actions, str):
        action_items = json.loads(raw_actions)
    else:
        action_items = raw_actions or []

    return WeeklyDigestRecord(
        id=row["id"],
        monitor_id=row["monitor_id"],
        client_id=row.get("client_id"),
        week_ending=row["week_ending"],
        stories=stories,
        executive_summary=row["executive_summary"],
        action_items=action_items,
        dqs_score=row.get("dqs_score"),
        iteration_count=row["iteration_count"],
        avg_story_delta=row.get("avg_story_delta"),
        generated_at=row["generated_at"],
        digest_markdown=row.get("digest_markdown"),
    )
