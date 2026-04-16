"""Batch processing exceptions."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import BatchJob


class BatchError(Exception):
    """Base batch processing error."""


class BatchNotFoundError(BatchError):
    """Batch job not found or not owned by user."""


class BatchLimitExceededError(BatchError):
    """Batch size exceeds tier limit."""

    def __init__(self, max_size: int, requested: int) -> None:
        self.max_size = max_size
        self.requested = requested
        super().__init__(f"Batch size {requested} exceeds limit {max_size}")


class BatchAlreadyExistsError(BatchError):
    """Idempotency key collision — return existing batch."""

    def __init__(self, existing_batch: BatchJob) -> None:
        self.existing_batch = existing_batch
        super().__init__(f"Batch already exists: {existing_batch.id}")


class BatchNotCancellableError(BatchError):
    """Batch is in terminal state and cannot be cancelled."""


class BatchActiveError(BatchError):
    """Operation blocked because an active batch references this resource."""
