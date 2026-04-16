"""PostgreSQL batch processing repository."""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator
from uuid import UUID

import asyncpg

from .exceptions import BatchAlreadyExistsError
from .models import BatchItem, BatchJob, BatchStatus, ItemStatus

logger = logging.getLogger(__name__)


class PostgresBatchRepository:
    """PostgreSQL repository for batch jobs and items."""

    ACQUIRE_TIMEOUT = 5.0

    # ── Batch Job SQL ──────────────────────────────────────────────────────

    _CREATE_BATCH = """
        INSERT INTO batch_jobs (conversation_id, collection_id, user_id, total_items, analysis_types, idempotency_key)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING *
    """

    _GET_BATCH = """
        SELECT * FROM batch_jobs WHERE id = $1
    """

    _GET_BATCH_FOR_USER = """
        SELECT * FROM batch_jobs WHERE id = $1 AND user_id = $2
    """

    _GET_ACTIVE_BATCH = """
        SELECT * FROM batch_jobs
        WHERE conversation_id = $1 AND status IN ('pending', 'processing')
        LIMIT 1
    """

    _COUNT_ACTIVE_BATCHES_FOR_USER = """
        SELECT COUNT(*) FROM batch_jobs
        WHERE user_id = $1 AND status IN ('pending', 'processing')
    """

    _UPDATE_BATCH_STATUS = """
        UPDATE batch_jobs SET status = $2
        WHERE id = $1
        RETURNING *
    """

    _PREPARE_RETRY = """
        WITH reset AS (
            UPDATE batch_items
            SET status = 'pending', error_message = NULL, completed_at = NULL
            WHERE batch_id = $1 AND status = 'failed'
            RETURNING id
        )
        UPDATE batch_jobs
        SET failed_items = GREATEST(0, failed_items - (SELECT COUNT(*) FROM reset)),
            status = 'processing'
        WHERE id = $1
        RETURNING *
    """

    _FAIL_PENDING_AND_COUNT = """
        WITH failed AS (
            UPDATE batch_items
            SET status = 'failed', error_message = $2, completed_at = NOW()
            WHERE batch_id = $1 AND status = 'pending'
            RETURNING id
        )
        UPDATE batch_jobs
        SET failed_items = failed_items + (SELECT COUNT(*) FROM failed)
        WHERE id = $1
        RETURNING *
    """

    # ── Batch Items SQL ────────────────────────────────────────────────────

    _CREATE_ITEMS = """
        INSERT INTO batch_items (batch_id, workspace_item_id)
        VALUES ($1, $2)
    """

    _CLAIM_PENDING = """
        UPDATE batch_items SET status = 'running', claimed_at = NOW()
        WHERE id IN (
            SELECT id FROM batch_items
            WHERE batch_id = $1 AND (
                status = 'pending'
                OR (status = 'running' AND claimed_at < NOW() - INTERVAL '1 second' * $3)
            )
            FOR UPDATE SKIP LOCKED
            LIMIT $2
        )
        RETURNING *
    """

    _COMPLETE_ITEM = """
        UPDATE batch_items
        SET status = $2, error_message = $3, completed_at = NOW()
        WHERE id = $1
        RETURNING *
    """

    _INCREMENT_COMPLETED = """
        UPDATE batch_jobs
        SET completed_items = completed_items + 1
        WHERE id = $1
        RETURNING *
    """

    _INCREMENT_FAILED = """
        UPDATE batch_jobs
        SET failed_items = failed_items + 1
        WHERE id = $1
        RETURNING *
    """

    _INCREMENT_FLAGGED = """
        UPDATE batch_jobs
        SET flagged_items = flagged_items + 1
        WHERE id = $1
        RETURNING *
    """

    _CANCEL_PENDING_ITEMS = """
        UPDATE batch_items SET status = 'cancelled'
        WHERE batch_id = $1 AND status = 'pending'
    """

    _RESET_FAILED_ITEMS = """
        UPDATE batch_items
        SET status = 'pending', error_message = NULL, claimed_at = NULL, completed_at = NULL
        WHERE batch_id = $1 AND status = 'failed'
    """

    _GET_ITEMS_BY_STATUS = """
        SELECT * FROM batch_items
        WHERE batch_id = $1 AND status = $2
        ORDER BY id
    """

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    @asynccontextmanager
    async def _acquire_connection(self) -> AsyncIterator[Any]:
        """Acquire connection with proper error handling."""
        try:
            async with asyncio.timeout(self.ACQUIRE_TIMEOUT):
                conn = await self._pool.acquire()
        except asyncio.TimeoutError:
            raise asyncpg.InterfaceError("Connection pool exhausted")
        try:
            yield conn
        finally:
            await self._pool.release(conn)

    # ── Batch Job Methods ──────────────────────────────────────────────────

    async def create_batch_with_items(
        self,
        conversation_id: UUID,
        collection_id: UUID,
        user_id: UUID,
        workspace_item_ids: list[UUID],
        analysis_types: list[str],
        idempotency_key: str | None = None,
    ) -> BatchJob:
        """Atomic: INSERT batch_jobs + INSERT batch_items in single transaction.
        ON CONFLICT (user_id, idempotency_key) returns existing batch via exception."""
        async with self._acquire_connection() as conn:
            async with conn.transaction():
                try:
                    row = await conn.fetchrow(
                        self._CREATE_BATCH,
                        conversation_id,
                        collection_id,
                        user_id,
                        len(workspace_item_ids),
                        json.dumps(analysis_types),
                        idempotency_key,
                    )
                except asyncpg.UniqueViolationError as e:
                    constraint = getattr(e, "constraint_name", "") or ""
                    if "idempotency" in constraint:
                        # Return existing batch for idempotency
                        existing = await conn.fetchrow(
                            "SELECT * FROM batch_jobs WHERE user_id = $1 AND idempotency_key = $2",
                            user_id,
                            idempotency_key,
                        )
                        if existing:
                            raise BatchAlreadyExistsError(BatchJob.from_row(existing)) from e
                    raise

                batch = BatchJob.from_row(row)

                # Bulk insert items
                if workspace_item_ids:
                    records = [(batch.id, item_id) for item_id in workspace_item_ids]
                    await conn.executemany(self._CREATE_ITEMS, records)

                return batch

    async def get_batch(self, batch_id: UUID) -> BatchJob | None:
        """Get batch by ID (no ownership check)."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(self._GET_BATCH, batch_id)
            return BatchJob.from_row(row) if row else None

    async def get_batch_for_user(self, batch_id: UUID, user_id: UUID) -> BatchJob | None:
        """Get batch with ownership check."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(self._GET_BATCH_FOR_USER, batch_id, user_id)
            return BatchJob.from_row(row) if row else None

    async def get_active_batch(self, conversation_id: UUID) -> BatchJob | None:
        """Returns batch with status IN ('pending', 'processing') for conversation."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(self._GET_ACTIVE_BATCH, conversation_id)
            return BatchJob.from_row(row) if row else None

    async def count_active_batches_for_user(self, user_id: UUID) -> int:
        """Count active batches across all conversations for a user."""
        async with self._acquire_connection() as conn:
            count = await conn.fetchval(self._COUNT_ACTIVE_BATCHES_FOR_USER, user_id)
            return int(count or 0)

    async def update_batch_status(self, batch_id: UUID, new_status: BatchStatus) -> BatchJob | None:
        """Update batch status. Returns None if batch not found (CASCADE deleted)."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(self._UPDATE_BATCH_STATUS, batch_id, new_status.value)
            return BatchJob.from_row(row) if row else None

    async def prepare_retry(self, batch_id: UUID) -> BatchJob | None:
        """Atomically reset counters and set status to PROCESSING for retry."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(self._PREPARE_RETRY, batch_id)
            return BatchJob.from_row(row) if row else None

    # ── Batch Item Methods ─────────────────────────────────────────────────

    async def claim_pending_items(
        self, batch_id: UUID, limit: int, claim_timeout_seconds: int = 300,
    ) -> list[BatchItem]:
        """Atomic claim using FOR UPDATE SKIP LOCKED.
        Also reclaims stale items (claimed > claim_timeout_seconds ago)."""
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(
                self._CLAIM_PENDING, batch_id, limit, claim_timeout_seconds,
            )
            return [BatchItem.from_row(r) for r in rows]

    async def complete_item_and_increment(
        self,
        item_id: UUID,
        batch_id: UUID,
        status: ItemStatus,
        error_message: str | None = None,
        *,
        flagged: bool = False,
        workspace_update: dict | None = None,
    ) -> BatchItem | None:
        """Atomic transaction: UPDATE batch_items + UPDATE batch_jobs counters.
        Optionally updates workspace item in same transaction.
        Returns None if item not found (CASCADE deleted)."""
        async with self._acquire_connection() as conn:
            async with conn.transaction():
                # Update item status
                item_row = await conn.fetchrow(
                    self._COMPLETE_ITEM, item_id, status.value, error_message,
                )
                if item_row is None:
                    return None  # Item deleted (CASCADE)

                # Increment batch counters atomically (disjoint model:
                # completed = succeeded only, failed = failed + skipped)
                if status in (ItemStatus.FAILED, ItemStatus.SKIPPED):
                    batch_row = await conn.fetchrow(self._INCREMENT_FAILED, batch_id)
                else:
                    batch_row = await conn.fetchrow(self._INCREMENT_COMPLETED, batch_id)

                # Handle flagged items (additional counter)
                if flagged and batch_row is not None:
                    await conn.fetchrow(self._INCREMENT_FLAGGED, batch_id)

                # Update workspace item with analysis results (same transaction)
                if workspace_update and batch_row is not None:
                    await conn.execute(
                        """UPDATE workspace_items
                           SET risk_score = $1, analysis_results = $2, updated_at = NOW()
                           WHERE id = $3""",
                        workspace_update["risk_score"],
                        workspace_update["analysis_results"],
                        workspace_update["item_id"],
                    )

                if batch_row is None:
                    return None  # Batch deleted (CASCADE)

                return BatchItem.from_row(item_row)

    async def cancel_pending_items(self, batch_id: UUID) -> int:
        """Cancel all pending items. Returns count of cancelled items."""
        async with self._acquire_connection() as conn:
            result = await conn.execute(self._CANCEL_PENDING_ITEMS, batch_id)
            # result is like "UPDATE N"
            return int(result.split()[-1])

    async def reset_failed_items(self, batch_id: UUID) -> int:
        """Reset failed items to pending. Returns count of reset items."""
        async with self._acquire_connection() as conn:
            result = await conn.execute(self._RESET_FAILED_ITEMS, batch_id)
            return int(result.split()[-1])

    async def get_items_by_status(self, batch_id: UUID, status: ItemStatus) -> list[BatchItem]:
        """Get items filtered by status."""
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(self._GET_ITEMS_BY_STATUS, batch_id, status.value)
            return [BatchItem.from_row(r) for r in rows]

    async def fail_pending_items(self, batch_id: UUID, reason: str) -> BatchJob | None:
        """Mark all remaining PENDING items as FAILED and increment failed_items counter atomically."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(self._FAIL_PENDING_AND_COUNT, batch_id, reason)
            return BatchJob.from_row(row) if row else None

    _ACTIVE_BATCH_FOR_COLLECTION = """
        SELECT * FROM batch_jobs
        WHERE collection_id = $1 AND status IN ('pending', 'processing')
        LIMIT 1
    """

    async def get_active_batch_for_collection(self, collection_id: UUID) -> BatchJob | None:
        """Get active batch for a collection (if any)."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(self._ACTIVE_BATCH_FOR_COLLECTION, collection_id)
            return BatchJob.from_row(row) if row else None
