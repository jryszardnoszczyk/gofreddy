"""Conversation domain exceptions."""

from uuid import UUID


class ConversationError(Exception):
    """Base exception for conversation operations."""


class ConversationNotFoundError(ConversationError):
    """Conversation not found or user doesn't own it."""

    def __init__(self, conversation_id: UUID) -> None:
        self.conversation_id = conversation_id
        super().__init__(f"Conversation {conversation_id} not found")


class MessageLimitError(ConversationError):
    """Daily message limit exhausted."""

    def __init__(self, limit: int, retry_after_seconds: int) -> None:
        self.limit = limit
        self.retry_after_seconds = retry_after_seconds
        super().__init__(f"Daily message limit ({limit}) reached")
