"""PostgreSQL publishing repository — platform connections and publish queue."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

import asyncpg

from .models import (
    AuthType,
    PlatformConnection,
    PublishPlatform,
    PublishStatus,
    QueueItem,
)

logger = logging.getLogger(__name__)

# Single source of truth for retry delays (seconds): 5min, 10min, 20min
RETRY_DELAYS = [300, 600, 1200]


def _row_to_connection(row: asyncpg.Record) -> PlatformConnection:
    return PlatformConnection(
        id=row["id"],
        org_id=row["org_id"],
        platform=PublishPlatform(row["platform"]),
        auth_type=AuthType(row["auth_type"]),
        account_id=row["account_id"],
        account_name=row["account_name"],
        is_active=row["is_active"],
        scopes=list(row["scopes"] or []),
        key_version=row["key_version"],
        token_expires_at=row["token_expires_at"],
        last_used_at=row["last_used_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_queue_item(row: asyncpg.Record) -> QueueItem:
    raw_parts = row["content_parts"]
    content_parts = json.loads(raw_parts) if isinstance(raw_parts, str) else (raw_parts or [])
    raw_media = row["media"]
    media = json.loads(raw_media) if isinstance(raw_media, str) else (raw_media or [])
    raw_labels = row["labels"]
    labels = json.loads(raw_labels) if isinstance(raw_labels, str) else (raw_labels or [])
    raw_meta = row["metadata"]
    metadata = json.loads(raw_meta) if isinstance(raw_meta, str) else (raw_meta or {})

    return QueueItem(
        id=row["id"],
        org_id=row["org_id"],
        client_id=row["client_id"],
        platform=row["platform"],
        connection_id=row["connection_id"],
        content_parts=content_parts,
        media=media,
        first_comment=row["first_comment"],
        thumbnail_url=row["thumbnail_url"],
        og_title=row["og_title"],
        og_description=row["og_description"],
        og_image_url=row["og_image_url"],
        twitter_card_type=row["twitter_card_type"],
        canonical_url=row["canonical_url"],
        slug=row["slug"],
        labels=labels,
        group_id=row["group_id"],
        newsletter_subject=row["newsletter_subject"],
        newsletter_segment=row["newsletter_segment"],
        status=PublishStatus(row["status"]),
        approved_at=row["approved_at"],
        approved_by=row["approved_by"],
        scheduled_at=row["scheduled_at"],
        external_id=row["external_id"],
        external_url=row["external_url"],
        error_message=row["error_message"],
        retry_count=row["retry_count"],
        metadata=metadata,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class PostgresPublishingRepository:
    """Pool-based repository for publishing tables."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    # ── Platform Connections ──────────────────────────────────────────────

    async def create_connection(
        self,
        org_id: UUID,
        platform: str,
        auth_type: str,
        account_id: str,
        account_name: str,
        *,
        credential_enc: bytes | None = None,
        access_token_enc: bytes | None = None,
        refresh_token_enc: bytes | None = None,
        token_expires_at: datetime | None = None,
        scopes: list[str] | None = None,
        key_version: int = 1,
    ) -> PlatformConnection:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO platform_connections (
                    org_id, platform, auth_type, account_id, account_name,
                    credential_enc, access_token_enc, refresh_token_enc,
                    token_expires_at, scopes, key_version
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                RETURNING *
                """,
                org_id, platform, auth_type, account_id, account_name,
                credential_enc, access_token_enc, refresh_token_enc,
                token_expires_at, scopes or [], key_version,
            )
            return _row_to_connection(row)

    async def get_connection(
        self, connection_id: UUID, org_id: UUID
    ) -> PlatformConnection | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM platform_connections WHERE id = $1 AND org_id = $2",
                connection_id, org_id,
            )
            return _row_to_connection(row) if row else None

    async def list_connections(self, org_id: UUID) -> list[PlatformConnection]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT * FROM platform_connections
                   WHERE org_id = $1 AND is_active = TRUE
                   ORDER BY created_at DESC""",
                org_id,
            )
            return [_row_to_connection(r) for r in rows]

    async def deactivate_connection(
        self, connection_id: UUID, org_id: UUID
    ) -> bool:
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """UPDATE platform_connections SET is_active = FALSE
                   WHERE id = $1 AND org_id = $2""",
                connection_id, org_id,
            )
            return result.endswith("1")

    async def get_connection_credentials(
        self, connection_id: UUID, org_id: UUID
    ) -> dict[str, bytes | None]:
        """Return raw encrypted bytes for decryption by service layer. IDOR-safe."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """SELECT credential_enc, access_token_enc, refresh_token_enc,
                          key_version
                   FROM platform_connections WHERE id = $1 AND org_id = $2""",
                connection_id, org_id,
            )
            if not row:
                return {}
            return {
                "credential_enc": row["credential_enc"],
                "access_token_enc": row["access_token_enc"],
                "refresh_token_enc": row["refresh_token_enc"],
                "key_version": row["key_version"],
            }

    async def update_last_used(self, connection_id: UUID) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                "UPDATE platform_connections SET last_used_at = NOW() WHERE id = $1",
                connection_id,
            )

    async def update_key_version(
        self,
        connection_id: UUID,
        credential_enc: bytes | None,
        access_token_enc: bytes | None,
        refresh_token_enc: bytes | None,
        new_key_version: int,
    ) -> None:
        """Re-encrypt a connection's credentials with a new key version."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                """UPDATE platform_connections
                   SET credential_enc = $2, access_token_enc = $3,
                       refresh_token_enc = $4, key_version = $5
                   WHERE id = $1""",
                connection_id, credential_enc, access_token_enc,
                refresh_token_enc, new_key_version,
            )

    async def get_connections_for_rotation(
        self, current_version: int, batch_size: int
    ) -> list[asyncpg.Record]:
        async with self._pool.acquire() as conn:
            return await conn.fetch(
                """SELECT id, credential_enc, access_token_enc, refresh_token_enc,
                          key_version
                   FROM platform_connections
                   WHERE key_version < $1 AND is_active = TRUE
                   ORDER BY updated_at ASC
                   LIMIT $2""",
                current_version, batch_size,
            )

    async def count_connections_for_rotation(self, current_version: int) -> int:
        async with self._pool.acquire() as conn:
            return await conn.fetchval(
                """SELECT COUNT(*) FROM platform_connections
                   WHERE key_version < $1 AND is_active = TRUE""",
                current_version,
            )

    # ── Publish Queue ─────────────────────────────────────────────────────

    async def create_queue_item(
        self,
        org_id: UUID,
        platform: str,
        connection_id: UUID,
        content_parts: list[dict[str, Any]],
        **kwargs: Any,
    ) -> QueueItem:
        fields = {
            "org_id": org_id,
            "platform": platform,
            "connection_id": connection_id,
            "content_parts": json.dumps(content_parts),
            "media": json.dumps(kwargs.get("media", [])),
            "labels": json.dumps(kwargs.get("labels", [])),
            "metadata": json.dumps(kwargs.get("metadata", {})),
        }
        # Optional text fields
        for key in (
            "first_comment", "thumbnail_url", "og_title", "og_description",
            "og_image_url", "twitter_card_type", "canonical_url", "slug",
            "newsletter_subject", "newsletter_segment",
        ):
            if key in kwargs:
                fields[key] = kwargs[key]
        if "group_id" in kwargs:
            fields["group_id"] = kwargs["group_id"]
        if "client_id" in kwargs:
            fields["client_id"] = kwargs["client_id"]

        columns = ", ".join(fields.keys())
        placeholders = ", ".join(f"${i+1}" for i in range(len(fields)))
        values = list(fields.values())

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                f"INSERT INTO publish_queue ({columns}) VALUES ({placeholders}) RETURNING *",
                *values,
            )
            return _row_to_queue_item(row)

    async def find_queue_item_by_source_url(
        self, org_id: UUID, platform: str, source_url: str,
    ) -> QueueItem | None:
        """Find an existing queue item by source_url in metadata (RSS dedup)."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """SELECT * FROM publish_queue
                   WHERE org_id = $1 AND platform = $2
                     AND metadata->>'source_url' = $3
                   LIMIT 1""",
                org_id, platform, source_url,
            )
            return _row_to_queue_item(row) if row else None

    async def get_publishing_item(self, item_id: UUID) -> QueueItem | None:
        """Get item in 'publishing' status only. Used by dispatcher (no org_id needed
        because the dispatcher claimed the item via FOR UPDATE SKIP LOCKED)."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM publish_queue WHERE id = $1 AND status = 'publishing'",
                item_id,
            )
            return _row_to_queue_item(row) if row else None

    async def get_active_connection(self, connection_id: UUID) -> PlatformConnection | None:
        """Get active connection by ID. Used by dispatcher for publish flow."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM platform_connections WHERE id = $1 AND is_active = TRUE",
                connection_id,
            )
            return _row_to_connection(row) if row else None

    async def get_queue_item(
        self, item_id: UUID, org_id: UUID
    ) -> QueueItem | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM publish_queue WHERE id = $1 AND org_id = $2",
                item_id, org_id,
            )
            return _row_to_queue_item(row) if row else None

    async def list_queue_items(
        self,
        org_id: UUID,
        *,
        status: str | None = None,
        platform: str | None = None,
        label: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[QueueItem]:
        conditions = ["org_id = $1"]
        params: list[Any] = [org_id]
        idx = 2

        if status:
            conditions.append(f"status = ${idx}")
            params.append(status)
            idx += 1
        if platform:
            conditions.append(f"platform = ${idx}")
            params.append(platform)
            idx += 1
        if label:
            conditions.append(f"labels @> ${idx}::jsonb")
            params.append(json.dumps([label]))
            idx += 1

        where = " AND ".join(conditions)
        params.extend([limit, offset])

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                f"""SELECT * FROM publish_queue
                    WHERE {where}
                    ORDER BY COALESCE(scheduled_at, created_at) DESC
                    LIMIT ${idx} OFFSET ${idx + 1}""",
                *params,
            )
            return [_row_to_queue_item(r) for r in rows]

    async def count_queue_items(self, org_id: UUID) -> int:
        async with self._pool.acquire() as conn:
            return await conn.fetchval(
                """SELECT COUNT(*) FROM publish_queue
                   WHERE org_id = $1 AND status NOT IN ('published', 'cancelled')""",
                org_id,
            )

    # Allowlist of columns safe for client-driven update
    _UPDATABLE_FIELDS = frozenset({
        "content_parts", "media", "first_comment", "thumbnail_url",
        "og_title", "og_description", "og_image_url", "canonical_url",
        "slug", "labels", "metadata", "twitter_card_type",
        "newsletter_subject", "newsletter_segment",
    })

    async def update_queue_item(
        self, item_id: UUID, org_id: UUID, **fields: Any
    ) -> QueueItem | None:
        if not fields:
            return await self.get_queue_item(item_id, org_id)

        # Reject any column not in allowlist (defense-in-depth)
        disallowed = set(fields.keys()) - self._UPDATABLE_FIELDS
        if disallowed:
            raise ValueError(f"Cannot update fields: {disallowed}")

        # Serialize JSONB fields
        for key in ("content_parts", "media", "labels", "metadata"):
            if key in fields and not isinstance(fields[key], str):
                fields[key] = json.dumps(fields[key])

        set_clauses = []
        params: list[Any] = []
        idx = 1
        for k, v in fields.items():
            set_clauses.append(f"{k} = ${idx}")
            params.append(v)
            idx += 1

        params.extend([item_id, org_id])
        set_sql = ", ".join(set_clauses)

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                f"""UPDATE publish_queue SET {set_sql}
                    WHERE id = ${idx} AND org_id = ${idx + 1} AND status = 'draft'
                    RETURNING *""",
                *params,
            )
            return _row_to_queue_item(row) if row else None

    async def delete_queue_item(self, item_id: UUID, org_id: UUID) -> bool:
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """DELETE FROM publish_queue
                   WHERE id = $1 AND org_id = $2
                     AND status IN ('draft', 'cancelled')""",
                item_id, org_id,
            )
            return result.endswith("1")

    async def approve_item(
        self, item_id: UUID, org_id: UUID, approved_by: UUID
    ) -> QueueItem | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """UPDATE publish_queue
                   SET approved_at = NOW(), approved_by = $3
                   WHERE id = $1 AND org_id = $2
                     AND status IN ('draft', 'failed')
                   RETURNING *""",
                item_id, org_id, approved_by,
            )
            return _row_to_queue_item(row) if row else None

    async def schedule_item(
        self, item_id: UUID, org_id: UUID, scheduled_at: datetime
    ) -> QueueItem | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """UPDATE publish_queue
                   SET status = 'scheduled', scheduled_at = $3
                   WHERE id = $1 AND org_id = $2
                     AND status IN ('draft', 'failed')
                     AND approved_at IS NOT NULL
                   RETURNING *""",
                item_id, org_id, scheduled_at,
            )
            return _row_to_queue_item(row) if row else None

    async def cancel_item(
        self, item_id: UUID, org_id: UUID
    ) -> QueueItem | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """UPDATE publish_queue SET status = 'cancelled'
                   WHERE id = $1 AND org_id = $2
                     AND status IN ('draft', 'scheduled', 'failed')
                   RETURNING *""",
                item_id, org_id,
            )
            return _row_to_queue_item(row) if row else None

    # ── Dispatch Methods ──────────────────────────────────────────────────

    async def reap_stale_publishing_items(
        self, threshold_minutes: int, now: datetime
    ) -> int:
        """Transition items stuck in 'publishing' for > threshold to 'failed'."""
        cutoff = now - timedelta(minutes=threshold_minutes)
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """UPDATE publish_queue
                   SET status = 'failed', error_message = 'stale_reap'
                   WHERE status = 'publishing' AND updated_at < $1""",
                cutoff,
            )
            count = int(result.split()[-1])
            return count

    async def claim_scheduled_items(
        self, batch_size: int, now: datetime
    ) -> list[QueueItem]:
        """Atomically claim scheduled + retryable items via FOR UPDATE SKIP LOCKED."""
        max_retries = len(RETRY_DELAYS)
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                WITH claimable AS (
                    SELECT id
                    FROM publish_queue
                    WHERE (
                        (status = 'scheduled' AND scheduled_at <= $1
                         AND approved_at IS NOT NULL)
                        OR (status = 'failed' AND retry_count < $3
                            AND next_retry_at <= $1)
                    )
                    ORDER BY scheduled_at ASC NULLS LAST
                    LIMIT $2
                    FOR UPDATE SKIP LOCKED
                )
                UPDATE publish_queue
                SET status = 'publishing', updated_at = NOW()
                WHERE id IN (SELECT id FROM claimable)
                RETURNING *
                """,
                now, batch_size, max_retries,
            )
            return [_row_to_queue_item(r) for r in rows]

    async def mark_published(
        self,
        item_id: UUID,
        external_id: str | None,
        external_url: str | None,
    ) -> bool:
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """UPDATE publish_queue
                   SET status = 'published', external_id = $2, external_url = $3
                   WHERE id = $1 AND status = 'publishing'""",
                item_id, external_id, external_url,
            )
            return result.endswith("1")

    async def mark_failed(
        self,
        item_id: UUID,
        error_message: str,
        metadata_patch: dict[str, Any] | None = None,
    ) -> bool:
        """Mark item as failed with retry scheduling. Single atomic UPDATE."""
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """UPDATE publish_queue
                   SET status = 'failed',
                       error_message = $2,
                       retry_count = retry_count + 1,
                       next_retry_at = CASE
                           WHEN retry_count < 1 THEN NOW() + INTERVAL '300 seconds'
                           WHEN retry_count < 2 THEN NOW() + INTERVAL '600 seconds'
                           WHEN retry_count < 3 THEN NOW() + INTERVAL '1200 seconds'
                           ELSE NULL
                       END,
                       metadata = metadata || $3::jsonb
                   WHERE id = $1 AND status = 'publishing'""",
                item_id, error_message, json.dumps(metadata_patch or {}),
            )
            return result.endswith("1")

    # ── Labels ────────────────────────────────────────────────────────────

    async def add_labels(
        self, item_id: UUID, org_id: UUID, labels: list[str]
    ) -> list[str]:
        """Add labels to a queue item, deduplicating. Max 20 enforced."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """UPDATE publish_queue
                   SET labels = (
                       SELECT jsonb_agg(DISTINCT elem)
                       FROM jsonb_array_elements_text(
                           COALESCE(labels, '[]'::jsonb) || $3::jsonb
                       ) AS elem
                   )
                   WHERE id = $1 AND org_id = $2
                   RETURNING labels""",
                item_id, org_id, json.dumps(labels),
            )
            if not row:
                return []
            raw = row["labels"]
            result = json.loads(raw) if isinstance(raw, str) else (raw or [])
            return result[:20]  # enforce max

    async def remove_labels(
        self, item_id: UUID, org_id: UUID, labels: list[str]
    ) -> list[str]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """UPDATE publish_queue
                   SET labels = (
                       SELECT COALESCE(jsonb_agg(elem), '[]'::jsonb)
                       FROM jsonb_array_elements_text(labels) AS elem
                       WHERE elem != ALL($3::text[])
                   )
                   WHERE id = $1 AND org_id = $2
                   RETURNING labels""",
                item_id, org_id, labels,
            )
            if not row:
                return []
            raw = row["labels"]
            return json.loads(raw) if isinstance(raw, str) else (raw or [])

    async def list_items_by_label(
        self, org_id: UUID, label: str, limit: int = 50
    ) -> list[QueueItem]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT * FROM publish_queue
                   WHERE org_id = $1 AND labels @> $2::jsonb
                   ORDER BY created_at DESC LIMIT $3""",
                org_id, json.dumps([label]), limit,
            )
            return [_row_to_queue_item(r) for r in rows]

    async def get_distinct_labels(self, org_id: UUID) -> list[str]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT DISTINCT jsonb_array_elements_text(labels) AS label
                   FROM publish_queue WHERE org_id = $1
                   ORDER BY label""",
                org_id,
            )
            return [r["label"] for r in rows]

    # ── OAuth Support ─────────────────────────────────────────────────────

    async def update_connection_token_metadata(
        self,
        connection_id: UUID,
        token_expires_at: datetime | None,
        scopes: list[str] | None,
    ) -> None:
        async with self._pool.acquire() as conn:
            if token_expires_at and scopes is not None:
                await conn.execute(
                    """UPDATE platform_connections
                       SET token_expires_at = $2, scopes = $3
                       WHERE id = $1""",
                    connection_id, token_expires_at, scopes,
                )
            elif token_expires_at:
                await conn.execute(
                    "UPDATE platform_connections SET token_expires_at = $2 WHERE id = $1",
                    connection_id, token_expires_at,
                )
            elif scopes is not None:
                await conn.execute(
                    "UPDATE platform_connections SET scopes = $2 WHERE id = $1",
                    connection_id, scopes,
                )

    async def get_expiring_connections(
        self, within_minutes: int = 60
    ) -> list[PlatformConnection]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT * FROM platform_connections
                   WHERE is_active = TRUE
                     AND token_expires_at IS NOT NULL
                     AND token_expires_at < NOW() + ($1 || ' minutes')::interval
                   ORDER BY token_expires_at ASC""",
                str(within_minutes),
            )
            return [_row_to_connection(r) for r in rows]

    async def update_connection_credentials(
        self,
        connection_id: UUID,
        *,
        credential_enc: bytes,
        key_version: int,
        token_expires_at: datetime | None = None,
    ) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """UPDATE platform_connections
                   SET credential_enc = $2, key_version = $3,
                       token_expires_at = COALESCE($4, token_expires_at)
                   WHERE id = $1""",
                connection_id, credential_enc, key_version, token_expires_at,
            )

    # ── Auto-Repost ───────────────────────────────────────────────────────

    async def mark_for_repost(
        self, item_id: UUID, org_id: UUID, schedule: dict
    ) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """UPDATE publish_queue
                   SET metadata = metadata || jsonb_build_object('repost_schedule', $3::jsonb)
                   WHERE id = $1 AND org_id = $2""",
                item_id, org_id, json.dumps(schedule),
            )

    async def get_pending_reposts(self) -> list[QueueItem]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT * FROM publish_queue
                   WHERE status = 'published'
                     AND metadata->>'repost_schedule' IS NOT NULL
                     AND (
                         (metadata->'repost_schedule'->>'reposts_done')::int
                         < (metadata->'repost_schedule'->>'max_reposts')::int
                     )
                     AND (
                         metadata->>'last_reposted_at' IS NULL
                         OR (metadata->>'last_reposted_at')::timestamptz
                            + ((metadata->'repost_schedule'->>'interval_days')::int * interval '1 day')
                            < NOW()
                     )
                   ORDER BY updated_at ASC
                   LIMIT 50""",
            )
            return [_row_to_queue_item(r) for r in rows]

    async def increment_repost_count(self, item_id: UUID) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """UPDATE publish_queue
                   SET metadata = jsonb_set(
                       jsonb_set(
                           metadata,
                           '{repost_schedule,reposts_done}',
                           (COALESCE((metadata->'repost_schedule'->>'reposts_done')::int, 0) + 1)::text::jsonb
                       ),
                       '{last_reposted_at}',
                       to_jsonb(NOW()::text)
                   )
                   WHERE id = $1""",
                item_id,
            )
