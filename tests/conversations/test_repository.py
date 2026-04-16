"""Tests for PostgresConversationRepository against real DB.

Uses SingleConnectionPool adapter for transactional test isolation.
"""

import pytest
import pytest_asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from tests.helpers.pool_adapter import SingleConnectionPool
from src.conversations.repository import PostgresConversationRepository
from src.conversations.models import Conversation, ConversationMessage
from src.conversations.exceptions import ConversationNotFoundError


@pytest.mark.db
class TestConversationRepository:

    @pytest_asyncio.fixture
    async def repo(self, db_conn):
        return PostgresConversationRepository(SingleConnectionPool(db_conn))

    @pytest_asyncio.fixture
    async def conversation(self, repo, test_user):
        """Create a test conversation."""
        expires = datetime.now(UTC) + timedelta(days=7)
        return await repo.create(test_user["id"], "Test conversation", expires)

    async def test_create_conversation(self, repo, test_user):
        expires = datetime.now(UTC) + timedelta(days=7)
        conv = await repo.create(test_user["id"], "My chat", expires)
        assert conv.user_id == test_user["id"]
        assert conv.title == "My chat"
        assert isinstance(conv, Conversation)

    async def test_get_by_id_found(self, repo, test_user, conversation):
        result = await repo.get_by_id(conversation.id, test_user["id"])
        assert result is not None
        assert result.id == conversation.id

    async def test_get_by_id_not_found(self, repo, test_user):
        result = await repo.get_by_id(uuid4(), test_user["id"])
        assert result is None

    async def test_get_by_id_expired(self, repo, test_user):
        expires = datetime.now(UTC) - timedelta(hours=1)
        conv = await repo.create(test_user["id"], "Expired", expires)
        result = await repo.get_by_id(conv.id, test_user["id"])
        assert result is None

    async def test_get_by_id_wrong_user(self, repo, db_conn, conversation):
        other_user_id = uuid4()
        await db_conn.execute(
            "INSERT INTO users (id, email) VALUES ($1, $2)",
            other_user_id, f"other-{other_user_id.hex[:8]}@test.com",
        )
        result = await repo.get_by_id(conversation.id, other_user_id)
        assert result is None

    async def test_list_by_user(self, repo, test_user):
        expires = datetime.now(UTC) + timedelta(days=7)
        await repo.create(test_user["id"], "Conv 1", expires)
        await repo.create(test_user["id"], "Conv 2", expires)
        convs = await repo.list_by_user(test_user["id"])
        assert len(convs) == 2
        titles = {c.title for c in convs}
        assert titles == {"Conv 1", "Conv 2"}

    async def test_list_by_user_excludes_expired(self, repo, test_user):
        await repo.create(test_user["id"], "Active", datetime.now(UTC) + timedelta(days=7))
        await repo.create(test_user["id"], "Expired", datetime.now(UTC) - timedelta(hours=1))
        convs = await repo.list_by_user(test_user["id"])
        assert len(convs) == 1
        assert convs[0].title == "Active"

    async def test_list_by_user_excludes_other_users(self, repo, db_conn, test_user):
        other_user_id = uuid4()
        await db_conn.execute(
            "INSERT INTO users (id, email) VALUES ($1, $2)",
            other_user_id, f"other-{other_user_id.hex[:8]}@test.com",
        )
        expires = datetime.now(UTC) + timedelta(days=7)
        await repo.create(test_user["id"], "Mine", expires)
        await repo.create(other_user_id, "Theirs", expires)
        convs = await repo.list_by_user(test_user["id"])
        assert len(convs) == 1
        assert convs[0].title == "Mine"

    async def test_update_title(self, repo, conversation):
        updated = await repo.update_title(conversation.id, "New Title")
        assert updated is not None
        assert updated.title == "New Title"

    async def test_delete(self, repo, test_user, conversation):
        deleted = await repo.delete(conversation.id, test_user["id"])
        assert deleted is True
        result = await repo.get_by_id(conversation.id, test_user["id"])
        assert result is None

    async def test_delete_cascades_messages(self, repo, test_user, conversation):
        await repo.add_message(conversation.id, "user", "Hello")
        await repo.delete(conversation.id, test_user["id"])
        messages = await repo.get_messages(conversation.id)
        assert messages == []

    async def test_add_message(self, repo, conversation):
        msg = await repo.add_message(conversation.id, "user", "Hello world")
        assert msg.role == "user"
        assert msg.content == "Hello world"
        assert isinstance(msg, ConversationMessage)
        assert msg.conversation_id == conversation.id

    async def test_add_message_with_metadata(self, repo, conversation):
        msg = await repo.add_message(conversation.id, "assistant", "Hi", {"tool_calls": [1]})
        assert msg.metadata == {"tool_calls": [1]}

    async def test_add_message_fk_violation(self, repo):
        """Adding a message to a non-existent conversation raises ConversationNotFoundError."""
        with pytest.raises(ConversationNotFoundError):
            await repo.add_message(uuid4(), "user", "test")

    async def test_get_messages_pagination(self, repo, conversation):
        for i in range(10):
            await repo.add_message(conversation.id, "user", f"Message {i}")
        messages = await repo.get_messages(conversation.id, limit=5, offset=0)
        assert len(messages) == 5
        assert messages[0].content == "Message 0"  # chronological order

    async def test_count_messages_today(self, repo, test_user, conversation):
        await repo.add_message(conversation.id, "user", "User msg 1")
        await repo.add_message(conversation.id, "assistant", "Bot reply")
        await repo.add_message(conversation.id, "user", "User msg 2")
        count = await repo.count_messages_today(test_user["id"])
        assert count == 2  # Only user role
