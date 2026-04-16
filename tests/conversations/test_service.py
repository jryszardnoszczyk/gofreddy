"""Tests for ConversationService business logic.

Repository is mocked -- we only test orchestration, ownership enforcement,
tier-based TTLs, daily limits, and auto-title fallback.
"""

import pytest
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

from src.billing.tiers import Tier
from src.conversations.exceptions import ConversationNotFoundError, MessageLimitError
from src.conversations.models import Conversation, ConversationMessage
from src.conversations.service import ConversationService


class TestConversationService:

    @pytest.fixture
    def mock_repo(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_repo):
        return ConversationService(repository=mock_repo, gemini_client=None)

    def _make_conversation(self, user_id=None, **kwargs):
        return Conversation(
            id=kwargs.get("id", uuid4()),
            user_id=user_id or uuid4(),
            title=kwargs.get("title", "Test"),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )

    async def test_create_conversation_free_tier(self, service, mock_repo):
        user_id = uuid4()
        mock_repo.create.return_value = self._make_conversation(user_id)
        result = await service.create_conversation(user_id, Tier.FREE)
        mock_repo.create.assert_called_once()
        call_args = mock_repo.create.call_args
        # expires_at should be ~7 days from now
        expires_at = call_args[0][2]
        assert (expires_at - datetime.now(UTC)).days in (6, 7)

    async def test_create_conversation_pro_tier(self, service, mock_repo):
        user_id = uuid4()
        mock_repo.create.return_value = self._make_conversation(user_id)
        await service.create_conversation(user_id, Tier.PRO)
        call_args = mock_repo.create.call_args
        expires_at = call_args[0][2]
        assert (expires_at - datetime.now(UTC)).days in (29, 30)

    async def test_get_conversation_ownership_enforced(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None  # Not found / wrong user
        with pytest.raises(ConversationNotFoundError):
            await service.get_conversation(uuid4(), uuid4())

    async def test_get_conversation_success(self, service, mock_repo):
        user_id = uuid4()
        conv = self._make_conversation(user_id)
        mock_repo.get_by_id.return_value = conv
        result = await service.get_conversation(conv.id, user_id)
        assert result.id == conv.id

    async def test_list_conversations(self, service, mock_repo):
        user_id = uuid4()
        convs = [self._make_conversation(user_id) for _ in range(3)]
        mock_repo.list_by_user.return_value = convs
        result = await service.list_conversations(user_id, limit=50, offset=0)
        assert len(result) == 3
        mock_repo.list_by_user.assert_called_once_with(user_id, 50, 0)

    async def test_check_daily_limit_within_limit(self, service, mock_repo):
        mock_repo.count_messages_today.return_value = 10
        remaining = await service.check_daily_limit(uuid4(), Tier.FREE)
        assert remaining == 10  # 20 - 10 (TierConfig.agent_messages_per_day)

    async def test_check_daily_limit_exhausted(self, service, mock_repo):
        mock_repo.count_messages_today.return_value = 20
        with pytest.raises(MessageLimitError) as exc_info:
            await service.check_daily_limit(uuid4(), Tier.FREE)
        assert exc_info.value.limit == 20
        assert exc_info.value.retry_after_seconds > 0

    async def test_check_daily_limit_pro_tier(self, service, mock_repo):
        mock_repo.count_messages_today.return_value = 100
        remaining = await service.check_daily_limit(uuid4(), Tier.PRO)
        assert remaining == 900  # 1_000 - 100 (TierConfig.agent_messages_per_day)

    async def test_auto_title_fallback_no_client(self, service, mock_repo):
        mock_repo.update_title.return_value = self._make_conversation()
        title = await service.auto_title(uuid4(), "What is the engagement rate for this TikTok creator?")
        # Should truncate to first 50 chars at word boundary
        assert len(title) <= 50
        mock_repo.update_title.assert_called_once()

    async def test_auto_title_fallback_empty_message(self, service, mock_repo):
        mock_repo.update_title.return_value = self._make_conversation()
        title = await service.auto_title(uuid4(), "")
        assert title == "New conversation"

    async def test_auto_title_truncates_at_word_boundary(self, service, mock_repo):
        mock_repo.update_title.return_value = self._make_conversation()
        # A long message that exceeds 50 chars
        long_msg = "This is a very long message that definitely exceeds fifty characters limit here"
        title = await service.auto_title(uuid4(), long_msg)
        assert len(title) <= 50
        # Should not cut mid-word
        assert not title.endswith("cha")  # would happen if cut at exact 50

    async def test_rename_conversation(self, service, mock_repo):
        user_id = uuid4()
        conv = self._make_conversation(user_id)
        mock_repo.get_by_id.return_value = conv
        renamed = self._make_conversation(user_id, title="New name")
        mock_repo.update_title.return_value = renamed
        result = await service.rename_conversation(conv.id, user_id, "New name")
        assert result.title == "New name"

    async def test_rename_conversation_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(ConversationNotFoundError):
            await service.rename_conversation(uuid4(), uuid4(), "New name")

    async def test_delete_conversation(self, service, mock_repo):
        user_id = uuid4()
        conv = self._make_conversation(user_id)
        mock_repo.get_by_id.return_value = conv
        mock_repo.delete.return_value = True
        await service.delete_conversation(conv.id, user_id)
        mock_repo.delete.assert_called_once_with(conv.id, user_id)

    async def test_delete_conversation_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(ConversationNotFoundError):
            await service.delete_conversation(uuid4(), uuid4())

    async def test_add_message(self, service, mock_repo):
        user_id = uuid4()
        conv_id = uuid4()
        conv = self._make_conversation(user_id, id=conv_id)
        mock_repo.get_by_id.return_value = conv
        msg = ConversationMessage(
            id=uuid4(), conversation_id=conv_id, role="user",
            content="test", metadata={}, created_at=datetime.now(UTC),
        )
        mock_repo.add_message.return_value = msg
        result = await service.add_message(conv_id, user_id, "user", "test")
        assert result.content == "test"

    async def test_add_message_ownership_enforced(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(ConversationNotFoundError):
            await service.add_message(uuid4(), uuid4(), "user", "test")

    async def test_get_messages(self, service, mock_repo):
        user_id = uuid4()
        conv_id = uuid4()
        conv = self._make_conversation(user_id, id=conv_id)
        mock_repo.get_by_id.return_value = conv
        messages = [
            ConversationMessage(
                id=uuid4(), conversation_id=conv_id, role="user",
                content=f"msg {i}", metadata={}, created_at=datetime.now(UTC),
            )
            for i in range(3)
        ]
        mock_repo.get_messages.return_value = messages
        result = await service.get_messages(conv_id, user_id, limit=100, offset=0)
        assert len(result) == 3
        mock_repo.get_messages.assert_called_once_with(conv_id, 100, 0)

    async def test_get_messages_ownership_enforced(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(ConversationNotFoundError):
            await service.get_messages(uuid4(), uuid4())
