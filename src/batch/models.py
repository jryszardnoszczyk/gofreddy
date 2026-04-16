"""Batch processing data models."""

import json
from dataclasses import dataclass, fields
from datetime import datetime
from enum import Enum
from typing import Any, Self
from uuid import UUID


class BatchStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class ItemStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class BatchJob:
    id: UUID
    conversation_id: UUID
    collection_id: UUID
    user_id: UUID | None
    status: BatchStatus
    total_items: int
    completed_items: int
    failed_items: int
    flagged_items: int
    analysis_types: list[str]
    idempotency_key: str | None
    created_at: datetime
    updated_at: datetime

    _JSONB_FIELDS = frozenset({"analysis_types"})

    @property
    def is_terminal(self) -> bool:
        return self.status in (BatchStatus.COMPLETED, BatchStatus.CANCELLED, BatchStatus.FAILED)

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
            if k == "status":
                v = BatchStatus(v)
            data[k] = v
        return cls(**data)


@dataclass(frozen=True, slots=True)
class BatchItem:
    id: UUID
    batch_id: UUID
    workspace_item_id: UUID | None
    status: ItemStatus
    error_message: str | None
    claimed_at: datetime | None
    completed_at: datetime | None

    @classmethod
    def from_row(cls, row: Any) -> Self:
        """Create record from database row."""
        known = {f.name for f in fields(cls)}
        data = {}
        for k, v in dict(row).items():
            if k not in known:
                continue
            if k == "status":
                v = ItemStatus(v)
            data[k] = v
        return cls(**data)
