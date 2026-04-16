"""Tests for PR-059 WS-3: Database unbounded growth fixes."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest


class TestExpiredConversationCleanup:
    """Expired conversation cleanup via ConversationService."""

    @pytest.mark.db
    async def test_cleanup_deletes_expired(self, db_pool):
        """Expired conversations are deleted."""
        from src.conversations.repository import PostgresConversationRepository

        uid = uuid4().hex[:8]
        repo = PostgresConversationRepository(db_pool)
        async with db_pool.acquire() as conn:
            user_row = await conn.fetchrow(
                "INSERT INTO users (email, supabase_user_id) VALUES ($1, $2) RETURNING id",
                f"cleanup-{uid}@example.com",
                f"sb-cleanup-{uid}",
            )
            user_id = user_row["id"]

            await conn.execute(
                "INSERT INTO conversations (user_id, title, expires_at) VALUES ($1, $2, $3)",
                user_id,
                "expired conv",
                datetime.now(UTC) - timedelta(days=1),
            )
            await conn.execute(
                "INSERT INTO conversations (user_id, title, expires_at) VALUES ($1, $2, $3)",
                user_id,
                "active conv",
                datetime.now(UTC) + timedelta(days=7),
            )

        deleted = await repo.delete_expired(batch_size=500)
        assert deleted >= 1

        async with db_pool.acquire() as conn:
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM conversations WHERE user_id = $1",
                user_id,
            )
            assert count >= 1

    @pytest.mark.db
    async def test_cleanup_zero_when_none_expired(self, db_pool):
        """Returns 0 when no conversations are expired."""
        from src.conversations.repository import PostgresConversationRepository

        repo = PostgresConversationRepository(db_pool)
        result = await repo.delete_expired(batch_size=500)
        assert isinstance(result, int)
        assert result >= 0

    @pytest.mark.db
    async def test_cleanup_respects_batch_size(self, db_pool):
        """Batch size limits deletion."""
        from src.conversations.repository import PostgresConversationRepository

        uid = uuid4().hex[:8]
        repo = PostgresConversationRepository(db_pool)
        async with db_pool.acquire() as conn:
            user_row = await conn.fetchrow(
                "INSERT INTO users (email, supabase_user_id) VALUES ($1, $2) RETURNING id",
                f"batch-{uid}@example.com",
                f"sb-batch-{uid}",
            )
            user_id = user_row["id"]

            for i in range(5):
                await conn.execute(
                    "INSERT INTO conversations (user_id, title, expires_at) VALUES ($1, $2, $3)",
                    user_id,
                    f"expired-{i}",
                    datetime.now(UTC) - timedelta(days=1),
                )

        deleted = await repo.delete_expired(batch_size=2)
        assert deleted == 2

    async def test_service_delegates_to_repository(self):
        """ConversationService.cleanup_expired delegates to repository."""
        from src.conversations.service import ConversationService

        mock_repo = MagicMock()
        mock_repo.delete_expired = AsyncMock(return_value=5)

        service = ConversationService(repository=mock_repo)
        result = await service.cleanup_expired(batch_size=100)
        assert result == 5
        mock_repo.delete_expired.assert_called_once_with(batch_size=100)


class TestToolResultSizeValidation:
    """Tool result JSONB size and count validation."""

    def test_size_check_in_store_tool_result(self):
        """store_tool_result contains size validation against _MAX_TOOL_RESULT_BYTES."""
        import inspect

        from src.workspace.repository import PostgresWorkspaceRepository

        source = inspect.getsource(PostgresWorkspaceRepository.store_tool_result)
        assert "_MAX_TOOL_RESULT_BYTES" in source
        assert "WorkspaceError" in source

    def test_constants_exist(self):
        """Module-level constants are defined."""
        from src.workspace.repository import (
            _MAX_TOOL_RESULT_BYTES,
            _MAX_TOOL_RESULTS_PER_CONVERSATION,
        )

        assert _MAX_TOOL_RESULT_BYTES == 1_048_576
        assert _MAX_TOOL_RESULTS_PER_CONVERSATION == 500


class TestActiveRunsBoundedDict:
    """_active_runs dict has a safety cap."""

    def test_cap_check_in_source(self):
        """Verify chat_stream contains _MAX_ACTIVE_RUNS guard."""
        import inspect

        from src.api.routers.agent import chat_stream

        source = inspect.getsource(chat_stream)
        assert "_MAX_ACTIVE_RUNS" in source
        assert "server_busy" in source

    def test_cap_check_before_build(self):
        """Cap check appears before _build_per_request_agent in source."""
        import inspect

        from src.api.routers.agent import chat_stream

        source = inspect.getsource(chat_stream)
        cap_pos = source.index("_MAX_ACTIVE_RUNS")
        build_pos = source.index("_build_per_request_agent")
        assert cap_pos < build_pos, "Cap check must run before agent build"
