"""Batch processing service."""

import logging
from uuid import UUID

from .exceptions import (
    BatchAlreadyExistsError,
    BatchError,
    BatchLimitExceededError,
    BatchNotCancellableError,
    BatchNotFoundError,
)
from .models import BatchJob, BatchStatus, ItemStatus
from .repository import PostgresBatchRepository
from ..workspace.repository import PostgresWorkspaceRepository

logger = logging.getLogger(__name__)

_VALID_ANALYSIS_TYPES = frozenset({"brand_safety", "content_moderation", "demographics", "brands"})

# Per-user active batch limits by tier
_MAX_ACTIVE_BATCHES = {"free": 1, "pro": 3}


class BatchService:
    """Orchestrates batch processing operations."""

    def __init__(
        self,
        repository: PostgresBatchRepository,
        workspace_repository: PostgresWorkspaceRepository,
    ) -> None:
        self._repository = repository
        self._workspace_repository = workspace_repository

    async def create_batch(
        self,
        conversation_id: UUID,
        collection_id: UUID,
        user_id: UUID,
        analysis_types: list[str],
        *,
        idempotency_key: str | None = None,
        max_batch_size: int = 50,
        tier: str = "free",
    ) -> BatchJob:
        """Create a new batch job.

        Validates:
        1. analysis_types are valid
        2. Collection exists and belongs to conversation
        3. Collection item count <= max_batch_size
        4. No active batch already running for this conversation
        5. Per-user active batch limit
        6. Idempotency: duplicate key returns existing batch
        """
        # 1. Validate analysis types
        invalid = set(analysis_types) - _VALID_ANALYSIS_TYPES
        if invalid:
            raise BatchError(f"Invalid analysis types: {invalid}")

        # 2. Validate collection exists and belongs to conversation
        collection = await self._workspace_repository.get_collection(collection_id)
        if collection is None or collection.conversation_id != conversation_id:
            raise BatchNotFoundError(f"Collection {collection_id} not found in conversation {conversation_id}")

        # 3. Check no active batch for conversation
        active = await self._repository.get_active_batch(conversation_id)
        if active is not None:
            raise BatchError(f"Active batch already exists for conversation: {active.id}")

        # 4. Per-user active batch limit
        max_active = _MAX_ACTIVE_BATCHES.get(tier, 1)
        active_count = await self._repository.count_active_batches_for_user(user_id)
        if active_count >= max_active:
            raise BatchError(f"Active batch limit reached ({max_active})")

        # 5. Get workspace items — respect active_filters so batch operates
        #    on the filtered subset (or all items when no filters are set).
        filters = collection.active_filters or None
        workspace_items = await self._workspace_repository.get_items(
            collection_id, filters=filters, limit=max_batch_size + 1,
        )

        # 6. Check batch size against actual (filtered) item count
        if len(workspace_items) > max_batch_size:
            raise BatchLimitExceededError(max_batch_size, len(workspace_items))

        # Handle empty result set — return COMPLETED immediately
        if not workspace_items:
            try:
                batch = await self._repository.create_batch_with_items(
                    conversation_id=conversation_id,
                    collection_id=collection_id,
                    user_id=user_id,
                    workspace_item_ids=[],
                    analysis_types=analysis_types,
                    idempotency_key=idempotency_key,
                )
            except BatchAlreadyExistsError as e:
                return e.existing_batch
            completed = await self._repository.update_batch_status(batch.id, BatchStatus.COMPLETED)
            return completed or batch

        item_ids = [item.id for item in workspace_items[:max_batch_size]]

        try:
            return await self._repository.create_batch_with_items(
                conversation_id=conversation_id,
                collection_id=collection_id,
                user_id=user_id,
                workspace_item_ids=item_ids,
                analysis_types=analysis_types,
                idempotency_key=idempotency_key,
            )
        except BatchAlreadyExistsError as e:
            return e.existing_batch

    async def get_batch(self, batch_id: UUID, user_id: UUID) -> BatchJob:
        """Ownership-checked get. Raises BatchNotFoundError if not found or not owned."""
        batch = await self._repository.get_batch_for_user(batch_id, user_id)
        if batch is None:
            raise BatchNotFoundError(f"Batch {batch_id} not found")
        return batch

    async def get_batch_unchecked(self, batch_id: UUID) -> BatchJob | None:
        """No ownership check — use only after ownership validated at connection time."""
        return await self._repository.get_batch(batch_id)

    async def cancel_batch(self, batch_id: UUID, user_id: UUID) -> BatchJob:
        """Cancel pending items. Running items finish."""
        batch = await self.get_batch(batch_id, user_id)
        if batch.is_terminal:
            raise BatchNotCancellableError(f"Batch {batch_id} is already {batch.status.value}")

        # Cancel pending items
        await self._repository.cancel_pending_items(batch_id)

        # Check if any items still running
        running = await self._repository.get_items_by_status(batch_id, ItemStatus.RUNNING)
        if not running:
            updated = await self._repository.update_batch_status(batch_id, BatchStatus.CANCELLED)
            return updated or batch

        # Items still running — batch stays PROCESSING, will be set to CANCELLED
        # when last running item completes
        return batch

    async def retry_failed(self, batch_id: UUID, user_id: UUID) -> BatchJob:
        """Reset failed items to pending. Only valid on COMPLETED batches with failed_items > 0."""
        batch = await self.get_batch(batch_id, user_id)
        if batch.status != BatchStatus.COMPLETED:
            raise BatchError(f"Can only retry failed items on COMPLETED batches, got {batch.status.value}")
        if batch.failed_items == 0:
            raise BatchError("No failed items to retry")

        # Single atomic CTE: resets failed items to pending AND adjusts counters
        updated = await self._repository.prepare_retry(batch_id)
        return updated or batch

    async def get_active_batch(self, conversation_id: UUID) -> BatchJob | None:
        """Get active batch for conversation."""
        return await self._repository.get_active_batch(conversation_id)
