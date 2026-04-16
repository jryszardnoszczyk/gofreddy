"""PostgreSQL comment inbox repository."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator
from uuid import UUID

import asyncpg

from ...common.exceptions import PoolExhaustedError
from .models import Comment

logger = logging.getLogger(__name__)


class PostgresCommentRepository:
    """PostgreSQL repository for the comment inbox."""

    ACQUIRE_TIMEOUT = 5.0

    # ── Queries ──

    _UPSERT_COMMENTS = """
        INSERT INTO comments (
            connection_id, org_id, platform, external_post_id, external_comment_id,
            author_handle, author_name, author_avatar_url, body, published_at,
            parent_external_id, likes
        )
        SELECT
            unnest($1::uuid[]),   unnest($2::uuid[]),   unnest($3::text[]),
            unnest($4::text[]),   unnest($5::text[]),    unnest($6::text[]),
            unnest($7::text[]),   unnest($8::text[]),    unnest($9::text[]),
            unnest($10::timestamptz[]), unnest($11::text[]), unnest($12::int[])
        ON CONFLICT (connection_id, external_comment_id) DO UPDATE
        SET body       = EXCLUDED.body,
            likes      = EXCLUDED.likes,
            updated_at = NOW()
    """

    _GET_INBOX = """
        SELECT * FROM comments
        WHERE org_id = $1
          {connection_filter}
          {unread_filter}
          {platform_filter}
        ORDER BY published_at DESC
        LIMIT ${{limit_param}} OFFSET ${{offset_param}}
    """

    _GET_COMMENTS_FOR_POST = """
        SELECT * FROM comments
        WHERE connection_id = $1 AND external_post_id = $2
        ORDER BY published_at ASC
        LIMIT $3
    """

    _MARK_READ = """
        UPDATE comments SET is_read = TRUE, updated_at = NOW()
        WHERE id = ANY($1::uuid[])
    """

    _MARK_REPLIED = """
        UPDATE comments
        SET replied_at = NOW(), reply_text = $2, updated_at = NOW()
        WHERE id = $1
        RETURNING id
    """

    _DELETE_OLD_READ_REPLIED = """
        DELETE FROM comments
        WHERE is_read = TRUE AND replied_at IS NOT NULL
          AND updated_at < NOW() - ($1 || ' days')::interval
    """

    _COUNT_UNREAD = """
        SELECT COUNT(*) FROM comments
        WHERE connection_id = $1 AND is_read = FALSE
    """

    _GET_COMMENT = """
        SELECT * FROM comments WHERE id = $1
    """

    _CHECK_UNAUTHORIZED = """
        SELECT id FROM comments WHERE id = ANY($1::uuid[]) AND org_id != $2
    """

    _GET_UNCLASSIFIED = """
        SELECT * FROM comments
        WHERE sentiment_label IS NULL AND is_spam = FALSE
        ORDER BY created_at ASC
        LIMIT $1
    """

    _UPDATE_CLASSIFICATION = """
        UPDATE comments
        SET sentiment_label = $2, sentiment_score = $3, is_spam = $4, updated_at = NOW()
        WHERE id = $1
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

    # ── Methods ──

    async def upsert_comments(
        self, org_id: UUID, connection_id: UUID, comments: list[tuple],
    ) -> int:
        """Batch upsert comments. Each tuple: (platform, external_post_id,
        external_comment_id, author_handle, author_name, author_avatar_url,
        body, published_at, parent_external_id, likes)."""
        if not comments:
            return 0
        conn_ids = [connection_id] * len(comments)
        org_ids = [org_id] * len(comments)
        platforms = [c[0] for c in comments]
        post_ids = [c[1] for c in comments]
        comment_ids = [c[2] for c in comments]
        handles = [c[3] for c in comments]
        names = [c[4] for c in comments]
        avatars = [c[5] for c in comments]
        bodies = [c[6] for c in comments]
        published = [c[7] for c in comments]
        parents = [c[8] for c in comments]
        likes = [c[9] for c in comments]

        async with self._acquire_connection() as conn:
            result = await conn.execute(
                self._UPSERT_COMMENTS,
                conn_ids, org_ids, platforms, post_ids, comment_ids,
                handles, names, avatars, bodies, published, parents, likes,
            )
        # e.g. "INSERT 0 12"
        return int(result.split()[-1]) if result else 0

    async def get_inbox(
        self,
        org_id: UUID,
        connection_id: UUID | None = None,
        *,
        unread_only: bool = True,
        platform: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Comment]:
        params: list[Any] = [org_id]
        idx = 2

        if connection_id is not None:
            connection_filter = f"AND connection_id = ${idx}"
            params.append(connection_id)
            idx += 1
        else:
            connection_filter = ""

        unread_filter = "AND is_read = FALSE" if unread_only else ""

        if platform is not None:
            platform_filter = f"AND platform = ${idx}"
            params.append(platform)
            idx += 1
        else:
            platform_filter = ""

        query = (
            "SELECT * FROM comments WHERE org_id = $1 "
            f"{connection_filter} {unread_filter} {platform_filter} "
            f"ORDER BY published_at DESC LIMIT ${idx} OFFSET ${idx + 1}"
        )
        params.extend([limit, offset])

        async with self._acquire_connection() as conn:
            rows = await conn.fetch(query, *params)
        return [Comment.from_row(r) for r in rows]

    async def get_comments_for_post(
        self, connection_id: UUID, external_post_id: str, *, limit: int = 100,
    ) -> list[Comment]:
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(
                self._GET_COMMENTS_FOR_POST, connection_id, external_post_id, limit,
            )
        return [Comment.from_row(r) for r in rows]

    async def mark_read(self, comment_ids: list[UUID]) -> int:
        if not comment_ids:
            return 0
        async with self._acquire_connection() as conn:
            result = await conn.execute(self._MARK_READ, comment_ids)
        return int(result.split()[-1]) if result else 0

    async def mark_replied(self, comment_id: UUID, reply_text: str) -> bool:
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(self._MARK_REPLIED, comment_id, reply_text)
        return row is not None

    async def delete_old_read_replied(self, days: int = 90) -> int:
        async with self._acquire_connection() as conn:
            result = await conn.execute(self._DELETE_OLD_READ_REPLIED, str(days))
        return int(result.split()[-1]) if result else 0

    async def count_unread(self, connection_id: UUID) -> int:
        async with self._acquire_connection() as conn:
            return await conn.fetchval(self._COUNT_UNREAD, connection_id)

    async def get_comment(self, comment_id: UUID) -> Comment | None:
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(self._GET_COMMENT, comment_id)
        return Comment.from_row(row) if row else None

    async def check_unauthorized_comments(
        self, comment_ids: list[UUID], org_id: UUID,
    ) -> list[UUID]:
        """Return comment IDs that do NOT belong to the given org."""
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(
                self._CHECK_UNAUTHORIZED, comment_ids, org_id,
            )
        return [row["id"] for row in rows]

    async def get_unclassified(self, limit: int = 200) -> list[Comment]:
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(self._GET_UNCLASSIFIED, limit)
        return [Comment.from_row(r) for r in rows]

    async def update_classification(
        self,
        comment_id: UUID,
        sentiment_label: str | None,
        sentiment_score: float | None,
        is_spam: bool,
    ) -> None:
        async with self._acquire_connection() as conn:
            await conn.execute(
                self._UPDATE_CLASSIFICATION,
                comment_id, sentiment_label, sentiment_score, is_spam,
            )
