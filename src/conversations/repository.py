"""PostgreSQL conversation repository."""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator
from uuid import UUID, uuid4

import asyncpg

from .exceptions import ConversationNotFoundError
from .models import Conversation, ConversationMessage

logger = logging.getLogger(__name__)


class PostgresConversationRepository:
    """PostgreSQL repository for conversations and messages."""

    ACQUIRE_TIMEOUT = 5.0

    _CREATE = """
        INSERT INTO conversations (user_id, title, expires_at)
        VALUES ($1, $2, $3)
        RETURNING *
    """

    _GET_BY_ID = """
        SELECT * FROM conversations
        WHERE id = $1 AND user_id = $2 AND expires_at > NOW()
    """

    _LIST_BY_USER = """
        SELECT * FROM conversations
        WHERE user_id = $1 AND expires_at > NOW()
        ORDER BY updated_at DESC
        LIMIT $2 OFFSET $3
    """

    _UPDATE_TITLE = """
        UPDATE conversations SET title = $1, updated_at = NOW()
        WHERE id = $2
        RETURNING *
    """

    _DELETE = """
        DELETE FROM conversations WHERE id = $1 AND user_id = $2
    """

    _ADD_MESSAGE = """
        INSERT INTO conversation_messages (conversation_id, role, content, metadata)
        VALUES ($1, $2, $3, $4)
        RETURNING *
    """

    _UPDATE_CONVERSATION_UPDATED_AT = """
        UPDATE conversations SET updated_at = NOW() WHERE id = $1
    """

    _GET_MESSAGES = """
        SELECT * FROM conversation_messages
        WHERE conversation_id = $1
        ORDER BY created_at ASC
        LIMIT $2 OFFSET $3
    """

    _COUNT_MESSAGES_TODAY = """
        SELECT COUNT(*) FROM conversation_messages cm
        JOIN conversations c ON cm.conversation_id = c.id
        WHERE c.user_id = $1
          AND cm.role = 'user'
          AND cm.created_at >= (date_trunc('day', NOW() AT TIME ZONE 'UTC')) AT TIME ZONE 'UTC'
    """

    # Advisory lock namespace — unique per lock domain to avoid cross-domain collisions
    _AGENT_MSG_LOCK_NS = 1001

    _INSERT_IF_UNDER_LIMIT = """
        WITH today_count AS (
            SELECT COUNT(*) AS cnt
            FROM conversation_messages cm
            JOIN conversations c ON cm.conversation_id = c.id
            WHERE c.user_id = $1
              AND cm.role = 'user'
              AND cm.created_at >= (date_trunc('day', NOW() AT TIME ZONE 'UTC'))
                                    AT TIME ZONE 'UTC'
        ),
        inserted AS (
            INSERT INTO conversation_messages (id, conversation_id, role, content, metadata, created_at)
            SELECT $2, $3, $4, $5, $6, NOW()
            FROM today_count
            WHERE today_count.cnt < $7
            RETURNING id, conversation_id
        )
        UPDATE conversations SET updated_at = NOW()
        FROM inserted
        WHERE conversations.id = inserted.conversation_id
        RETURNING inserted.id
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

    async def create(
        self, user_id: UUID, title: str | None, expires_at: Any
    ) -> Conversation:
        """Create a new conversation."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(self._CREATE, user_id, title, expires_at)
            return Conversation.from_row(row)

    async def get_by_id(
        self, conversation_id: UUID, user_id: UUID
    ) -> Conversation | None:
        """Fetch conversation by ID. Returns None if not found, expired, or wrong user."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(self._GET_BY_ID, conversation_id, user_id)
            return Conversation.from_row(row) if row else None

    async def list_by_user(
        self, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[Conversation]:
        """List user's non-expired conversations, most recent first."""
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(self._LIST_BY_USER, user_id, limit, offset)
            return [Conversation.from_row(r) for r in rows]

    async def update_title(
        self, conversation_id: UUID, title: str
    ) -> Conversation | None:
        """Update conversation title."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(self._UPDATE_TITLE, title, conversation_id)
            return Conversation.from_row(row) if row else None

    async def delete(self, conversation_id: UUID, user_id: UUID) -> bool:
        """Delete conversation. CASCADE handles children. Returns True if deleted."""
        async with self._acquire_connection() as conn:
            result = await conn.execute(self._DELETE, conversation_id, user_id)
            return result == "DELETE 1"

    async def add_message(
        self,
        conversation_id: UUID,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationMessage:
        """Add message and update conversation.updated_at in a transaction.

        Catches ForeignKeyViolationError for concurrent delete protection.
        """
        async with self._acquire_connection() as conn:
            async with conn.transaction():
                try:
                    row = await conn.fetchrow(
                        self._ADD_MESSAGE,
                        conversation_id,
                        role,
                        content,
                        json.dumps(metadata or {}),
                    )
                    await conn.execute(
                        self._UPDATE_CONVERSATION_UPDATED_AT, conversation_id
                    )
                except asyncpg.ForeignKeyViolationError:
                    raise ConversationNotFoundError(conversation_id)
            return ConversationMessage.from_row(row)

    async def get_messages(
        self, conversation_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[ConversationMessage]:
        """Get messages in chronological order with pagination."""
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(
                self._GET_MESSAGES, conversation_id, limit, offset
            )
            return [ConversationMessage.from_row(r) for r in rows]

    async def count_messages_today(self, user_id: UUID) -> int:
        """Count user-role messages sent today (UTC midnight reset)."""
        async with self._acquire_connection() as conn:
            count = await conn.fetchval(self._COUNT_MESSAGES_TODAY, user_id)
            return int(count or 0)

    async def insert_message_if_under_limit(
        self,
        user_id: UUID,
        conversation_id: UUID,
        role: str,
        content: str,
        metadata: dict[str, Any] | None,
        daily_limit: int,
    ) -> UUID | None:
        """Atomically insert message only if under daily limit.

        Uses pg_advisory_xact_lock to serialize per-user, preventing
        TOCTOU races under READ COMMITTED isolation.
        Returns message ID if inserted, None if limit reached.
        """
        message_id = uuid4()
        async with self._acquire_connection() as conn:
            async with conn.transaction():
                # Serialize per-user — different users are fully parallel
                await conn.execute(
                    "SELECT pg_advisory_xact_lock($1, hashtext($2::text))",
                    self._AGENT_MSG_LOCK_NS,
                    str(user_id),
                )
                try:
                    result = await conn.fetchval(
                        self._INSERT_IF_UNDER_LIMIT,
                        user_id, message_id, conversation_id, role, content,
                        json.dumps(metadata or {}), daily_limit,
                    )
                except asyncpg.ForeignKeyViolationError:
                    raise ConversationNotFoundError(conversation_id)
                return result

    async def delete_expired(self, *, batch_size: int = 500) -> int:
        """Delete expired conversations in batches. CASCADE deletes related data."""
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                DELETE FROM conversations
                WHERE id IN (
                    SELECT id FROM conversations
                    WHERE expires_at < NOW()
                    ORDER BY expires_at ASC
                    LIMIT $1
                )
                """,
                batch_size,
            )
            # asyncpg returns "DELETE N"
            return int(result.split()[-1])
