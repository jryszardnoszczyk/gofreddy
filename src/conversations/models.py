"""Conversation data models."""

import json
from dataclasses import dataclass, fields
from datetime import datetime
from typing import Any, Self
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Conversation:
    """Database record for a conversation."""

    id: UUID
    user_id: UUID
    title: str | None
    created_at: datetime
    updated_at: datetime
    expires_at: datetime

    @classmethod
    def from_row(cls, row: Any) -> Self:
        """Create record from database row."""
        known = {f.name for f in fields(cls)}
        data = {}
        for k, v in dict(row).items():
            if k not in known:
                continue
            data[k] = v
        return cls(**data)


@dataclass(frozen=True, slots=True)
class ConversationMessage:
    """Database record for a conversation message."""

    id: UUID
    conversation_id: UUID
    role: str
    content: str
    metadata: dict[str, Any]
    created_at: datetime

    _JSONB_FIELDS = frozenset({"metadata"})

    @classmethod
    def from_row(cls, row: Any) -> Self:
        """Create record from database row."""
        known = {f.name for f in fields(cls)}
        data = {}
        for k, v in dict(row).items():
            if k not in known:
                continue
            if k in cls._JSONB_FIELDS and isinstance(v, str):
                v = json.loads(v)
            data[k] = v
        return cls(**data)
