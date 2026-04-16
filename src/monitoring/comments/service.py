"""Comment inbox service — IDOR-safe operations over the comment repository."""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

import asyncpg

from ...common.exceptions import PoolExhaustedError
from .models import Comment
from .repository import PostgresCommentRepository

logger = logging.getLogger(__name__)


class CommentService:
    """Orchestrates comment inbox access with ownership checks."""

    ACQUIRE_TIMEOUT = 5.0

    def __init__(
        self,
        repository: PostgresCommentRepository,
        pool: asyncpg.Pool,
    ) -> None:
        self._repo = repository
        self._pool = pool

    # ── Helpers ──

    async def _get_org_id_for_connection(self, connection_id: UUID) -> UUID | None:
        """Resolve org_id from a platform_connection, used for IDOR checks."""
        try:
            async with asyncio.timeout(self.ACQUIRE_TIMEOUT):
                conn = await self._pool.acquire()
        except asyncio.TimeoutError:
            raise PoolExhaustedError(
                pool_size=self._pool.get_size(),
                timeout_seconds=self.ACQUIRE_TIMEOUT,
            )
        try:
            row = await conn.fetchrow(
                "SELECT org_id FROM platform_connections WHERE id = $1",
                connection_id,
            )
            return row["org_id"] if row else None
        finally:
            await self._pool.release(conn)

    async def _verify_connection_owner(
        self, connection_id: UUID, user_id: UUID,
    ) -> UUID:
        """Return org_id if user_id matches, otherwise raise PermissionError."""
        org_id = await self._get_org_id_for_connection(connection_id)
        if org_id is None or org_id != user_id:
            raise PermissionError("Connection does not belong to this user")
        return org_id

    async def _verify_comment_owner(
        self, comment_id: UUID, user_id: UUID,
    ) -> Comment:
        """Return the comment if its org_id matches user_id."""
        comment = await self._repo.get_comment(comment_id)
        if comment is None or comment.org_id != user_id:
            raise PermissionError("Comment does not belong to this user")
        return comment

    # ── Public API ──

    async def get_inbox(
        self,
        connection_id: UUID,
        user_id: UUID,
        *,
        unread_only: bool = True,
        platform: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Comment]:
        org_id = await self._verify_connection_owner(connection_id, user_id)
        return await self._repo.get_inbox(
            org_id,
            connection_id,
            unread_only=unread_only,
            platform=platform,
            limit=limit,
            offset=offset,
        )

    async def get_thread(
        self,
        connection_id: UUID,
        user_id: UUID,
        external_post_id: str,
    ) -> list[Comment]:
        await self._verify_connection_owner(connection_id, user_id)
        return await self._repo.get_comments_for_post(connection_id, external_post_id)

    async def mark_read(
        self, user_id: UUID, comment_ids: list[UUID],
    ) -> int:
        if not comment_ids:
            return 0
        # Single batch query instead of per-comment IDOR check
        unauthorized = await self._repo.check_unauthorized_comments(
            comment_ids, user_id,
        )
        if unauthorized:
            raise PermissionError("One or more comments do not belong to this user")
        return await self._repo.mark_read(comment_ids)

    async def mark_replied(
        self, user_id: UUID, comment_id: UUID, reply_text: str,
    ) -> bool:
        await self._verify_comment_owner(comment_id, user_id)
        return await self._repo.mark_replied(comment_id, reply_text)

    async def reply(
        self, user_id: UUID, comment_id: UUID, reply_text: str,
    ) -> bool:
        """Alias for mark_replied — matches router call signature."""
        return await self.mark_replied(user_id, comment_id, reply_text)

    async def get_unread_count(
        self, user_id: UUID, connection_id: UUID,
    ) -> int:
        """Return unread comment count after verifying connection ownership."""
        await self._verify_connection_owner(connection_id, user_id)
        return await self._repo.count_unread(connection_id)

    async def cleanup_stale(self, days: int = 90) -> int:
        """System-level cleanup — no IDOR check needed."""
        return await self._repo.delete_old_read_replied(days)

    async def get_comment(self, comment_id: UUID) -> Comment | None:
        """Internal use — no IDOR check."""
        return await self._repo.get_comment(comment_id)
