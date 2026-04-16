"""Mock-based tests for BatchService."""

import pytest
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.batch.exceptions import (
    BatchAlreadyExistsError,
    BatchError,
    BatchLimitExceededError,
    BatchNotCancellableError,
    BatchNotFoundError,
)
from src.batch.models import BatchJob, BatchStatus, ItemStatus
from src.batch.service import BatchService


class TestBatchService:

    @pytest.fixture
    def mock_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_ws_repo(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_repo, mock_ws_repo):
        return BatchService(repository=mock_repo, workspace_repository=mock_ws_repo)

    def _make_batch(self, **kwargs):
        defaults = {
            "id": uuid4(),
            "conversation_id": uuid4(),
            "collection_id": uuid4(),
            "user_id": uuid4(),
            "status": BatchStatus.PENDING,
            "total_items": 10,
            "completed_items": 0,
            "failed_items": 0,
            "flagged_items": 0,
            "analysis_types": ["brand_safety"],
            "idempotency_key": None,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
        defaults.update(kwargs)
        return BatchJob(**defaults)

    def _make_collection(self, conversation_id, item_count=5):
        coll = MagicMock()
        coll.conversation_id = conversation_id
        coll.item_count = item_count
        return coll

    def _make_workspace_item(self):
        item = MagicMock()
        item.id = uuid4()
        return item

    # ── create_batch ─────────────────────────────────────────────────────

    async def test_create_batch_happy_path(self, service, mock_repo, mock_ws_repo):
        conv_id = uuid4()
        coll_id = uuid4()
        user_id = uuid4()
        collection = self._make_collection(conv_id, item_count=3)
        items = [self._make_workspace_item() for _ in range(3)]
        batch = self._make_batch(
            conversation_id=conv_id, collection_id=coll_id, user_id=user_id,
        )

        mock_ws_repo.get_collection.return_value = collection
        mock_repo.get_active_batch.return_value = None
        mock_repo.count_active_batches_for_user.return_value = 0
        mock_ws_repo.get_items.return_value = items
        mock_repo.create_batch_with_items.return_value = batch

        result = await service.create_batch(
            conv_id, coll_id, user_id, ["brand_safety"],
        )

        assert result == batch
        mock_ws_repo.get_collection.assert_called_once_with(coll_id)
        mock_repo.get_active_batch.assert_called_once_with(conv_id)
        mock_repo.count_active_batches_for_user.assert_called_once_with(user_id)
        mock_ws_repo.get_items.assert_called_once()
        mock_repo.create_batch_with_items.assert_called_once()

    async def test_create_batch_invalid_analysis_types(self, service, mock_repo, mock_ws_repo):
        with pytest.raises(BatchError, match="Invalid analysis types"):
            await service.create_batch(
                uuid4(), uuid4(), uuid4(), ["brand_safety", "nonexistent_type"],
            )
        # Should fail before touching any repo
        mock_ws_repo.get_collection.assert_not_called()

    async def test_create_batch_collection_not_found(self, service, mock_repo, mock_ws_repo):
        mock_ws_repo.get_collection.return_value = None

        with pytest.raises(BatchNotFoundError, match="not found"):
            await service.create_batch(
                uuid4(), uuid4(), uuid4(), ["brand_safety"],
            )

    async def test_create_batch_collection_wrong_conversation(self, service, mock_repo, mock_ws_repo):
        conv_id = uuid4()
        other_conv_id = uuid4()
        collection = self._make_collection(other_conv_id, item_count=5)
        mock_ws_repo.get_collection.return_value = collection

        with pytest.raises(BatchNotFoundError, match="not found"):
            await service.create_batch(
                conv_id, uuid4(), uuid4(), ["brand_safety"],
            )

    async def test_create_batch_exceeds_max_size(self, service, mock_repo, mock_ws_repo):
        conv_id = uuid4()
        collection = self._make_collection(conv_id, item_count=100)
        mock_ws_repo.get_collection.return_value = collection
        mock_repo.get_active_batch.return_value = None
        mock_repo.count_active_batches_for_user.return_value = 0
        # Size check now uses len(workspace_items), not collection.item_count
        mock_ws_repo.get_items.return_value = [self._make_workspace_item() for _ in range(100)]

        with pytest.raises(BatchLimitExceededError) as exc_info:
            await service.create_batch(
                conv_id, uuid4(), uuid4(), ["brand_safety"], max_batch_size=50,
            )
        assert exc_info.value.max_size == 50
        assert exc_info.value.requested == 100

    async def test_create_batch_active_batch_exists(self, service, mock_repo, mock_ws_repo):
        conv_id = uuid4()
        collection = self._make_collection(conv_id, item_count=5)
        active_batch = self._make_batch(conversation_id=conv_id)

        mock_ws_repo.get_collection.return_value = collection
        mock_repo.get_active_batch.return_value = active_batch

        with pytest.raises(BatchError, match="Active batch already exists"):
            await service.create_batch(
                conv_id, uuid4(), uuid4(), ["brand_safety"],
            )

    async def test_create_batch_per_user_limit_reached_free(self, service, mock_repo, mock_ws_repo):
        conv_id = uuid4()
        user_id = uuid4()
        collection = self._make_collection(conv_id, item_count=5)

        mock_ws_repo.get_collection.return_value = collection
        mock_repo.get_active_batch.return_value = None
        mock_repo.count_active_batches_for_user.return_value = 1  # free limit is 1

        with pytest.raises(BatchError, match="Active batch limit reached"):
            await service.create_batch(
                conv_id, uuid4(), user_id, ["brand_safety"], tier="free",
            )

    async def test_create_batch_per_user_limit_reached_pro(self, service, mock_repo, mock_ws_repo):
        conv_id = uuid4()
        user_id = uuid4()
        collection = self._make_collection(conv_id, item_count=5)

        mock_ws_repo.get_collection.return_value = collection
        mock_repo.get_active_batch.return_value = None
        mock_repo.count_active_batches_for_user.return_value = 3  # pro limit is 3

        with pytest.raises(BatchError, match="Active batch limit reached"):
            await service.create_batch(
                conv_id, uuid4(), user_id, ["brand_safety"], tier="pro",
            )

    async def test_create_batch_empty_collection(self, service, mock_repo, mock_ws_repo):
        conv_id = uuid4()
        coll_id = uuid4()
        user_id = uuid4()
        collection = self._make_collection(conv_id, item_count=0)
        batch = self._make_batch(
            conversation_id=conv_id, collection_id=coll_id, user_id=user_id,
            total_items=0,
        )
        completed_batch = self._make_batch(
            id=batch.id, conversation_id=conv_id, collection_id=coll_id,
            user_id=user_id, status=BatchStatus.COMPLETED, total_items=0,
        )

        mock_ws_repo.get_collection.return_value = collection
        mock_repo.get_active_batch.return_value = None
        mock_repo.count_active_batches_for_user.return_value = 0
        mock_ws_repo.get_items.return_value = []  # empty filtered result set
        mock_repo.create_batch_with_items.return_value = batch
        mock_repo.update_batch_status.return_value = completed_batch

        result = await service.create_batch(
            conv_id, coll_id, user_id, ["brand_safety"],
        )

        assert result.status == BatchStatus.COMPLETED
        mock_repo.create_batch_with_items.assert_called_once()
        # Verify empty items list was passed
        call_kwargs = mock_repo.create_batch_with_items.call_args.kwargs
        assert call_kwargs["workspace_item_ids"] == []
        mock_repo.update_batch_status.assert_called_once_with(batch.id, BatchStatus.COMPLETED)

    async def test_create_batch_empty_collection_update_returns_none(self, service, mock_repo, mock_ws_repo):
        """When update_batch_status returns None, fall back to original batch."""
        conv_id = uuid4()
        collection = self._make_collection(conv_id, item_count=0)
        batch = self._make_batch(conversation_id=conv_id, total_items=0)

        mock_ws_repo.get_collection.return_value = collection
        mock_repo.get_active_batch.return_value = None
        mock_repo.count_active_batches_for_user.return_value = 0
        mock_ws_repo.get_items.return_value = []  # empty filtered result set
        mock_repo.create_batch_with_items.return_value = batch
        mock_repo.update_batch_status.return_value = None

        result = await service.create_batch(
            conv_id, uuid4(), uuid4(), ["brand_safety"],
        )

        assert result == batch

    async def test_create_batch_idempotency_returns_existing(self, service, mock_repo, mock_ws_repo):
        conv_id = uuid4()
        user_id = uuid4()
        collection = self._make_collection(conv_id, item_count=5)
        existing_batch = self._make_batch(conversation_id=conv_id, user_id=user_id)
        items = [self._make_workspace_item() for _ in range(5)]

        mock_ws_repo.get_collection.return_value = collection
        mock_repo.get_active_batch.return_value = None
        mock_repo.count_active_batches_for_user.return_value = 0
        mock_ws_repo.get_items.return_value = items
        mock_repo.create_batch_with_items.side_effect = BatchAlreadyExistsError(existing_batch)

        result = await service.create_batch(
            conv_id, uuid4(), user_id, ["brand_safety"], idempotency_key="key-123",
        )

        assert result == existing_batch

    async def test_create_batch_idempotency_empty_collection(self, service, mock_repo, mock_ws_repo):
        """Idempotency on empty collection path returns existing batch."""
        conv_id = uuid4()
        collection = self._make_collection(conv_id, item_count=0)
        existing_batch = self._make_batch(
            conversation_id=conv_id, status=BatchStatus.COMPLETED, total_items=0,
        )

        mock_ws_repo.get_collection.return_value = collection
        mock_repo.get_active_batch.return_value = None
        mock_repo.count_active_batches_for_user.return_value = 0
        mock_repo.create_batch_with_items.side_effect = BatchAlreadyExistsError(existing_batch)

        result = await service.create_batch(
            conv_id, uuid4(), uuid4(), ["brand_safety"], idempotency_key="key-123",
        )

        assert result == existing_batch
        mock_repo.update_batch_status.assert_not_called()

    # ── get_batch ────────────────────────────────────────────────────────

    async def test_get_batch_found(self, service, mock_repo):
        batch = self._make_batch()
        mock_repo.get_batch_for_user.return_value = batch

        result = await service.get_batch(batch.id, batch.user_id)
        assert result == batch

    async def test_get_batch_not_found(self, service, mock_repo):
        mock_repo.get_batch_for_user.return_value = None

        with pytest.raises(BatchNotFoundError, match="not found"):
            await service.get_batch(uuid4(), uuid4())

    # ── get_batch_unchecked ──────────────────────────────────────────────

    async def test_get_batch_unchecked_found(self, service, mock_repo):
        batch = self._make_batch()
        mock_repo.get_batch.return_value = batch

        result = await service.get_batch_unchecked(batch.id)
        assert result == batch

    async def test_get_batch_unchecked_not_found(self, service, mock_repo):
        mock_repo.get_batch.return_value = None

        result = await service.get_batch_unchecked(uuid4())
        assert result is None

    # ── cancel_batch ─────────────────────────────────────────────────────

    async def test_cancel_batch_terminal_completed(self, service, mock_repo):
        batch = self._make_batch(status=BatchStatus.COMPLETED)
        mock_repo.get_batch_for_user.return_value = batch

        with pytest.raises(BatchNotCancellableError, match="completed"):
            await service.cancel_batch(batch.id, batch.user_id)

    async def test_cancel_batch_terminal_cancelled(self, service, mock_repo):
        batch = self._make_batch(status=BatchStatus.CANCELLED)
        mock_repo.get_batch_for_user.return_value = batch

        with pytest.raises(BatchNotCancellableError, match="cancelled"):
            await service.cancel_batch(batch.id, batch.user_id)

    async def test_cancel_batch_terminal_failed(self, service, mock_repo):
        batch = self._make_batch(status=BatchStatus.FAILED)
        mock_repo.get_batch_for_user.return_value = batch

        with pytest.raises(BatchNotCancellableError, match="failed"):
            await service.cancel_batch(batch.id, batch.user_id)

    async def test_cancel_batch_no_running_items(self, service, mock_repo):
        batch = self._make_batch(status=BatchStatus.PROCESSING)
        cancelled_batch = self._make_batch(
            id=batch.id, status=BatchStatus.CANCELLED,
        )
        mock_repo.get_batch_for_user.return_value = batch
        mock_repo.get_items_by_status.return_value = []  # no running items
        mock_repo.update_batch_status.return_value = cancelled_batch

        result = await service.cancel_batch(batch.id, batch.user_id)

        assert result.status == BatchStatus.CANCELLED
        mock_repo.cancel_pending_items.assert_called_once_with(batch.id)
        mock_repo.get_items_by_status.assert_called_once_with(batch.id, ItemStatus.RUNNING)
        mock_repo.update_batch_status.assert_called_once_with(batch.id, BatchStatus.CANCELLED)

    async def test_cancel_batch_no_running_items_update_returns_none(self, service, mock_repo):
        """When update_batch_status returns None, fall back to original batch."""
        batch = self._make_batch(status=BatchStatus.PENDING)
        mock_repo.get_batch_for_user.return_value = batch
        mock_repo.get_items_by_status.return_value = []
        mock_repo.update_batch_status.return_value = None

        result = await service.cancel_batch(batch.id, batch.user_id)
        assert result == batch

    async def test_cancel_batch_with_running_items(self, service, mock_repo):
        batch = self._make_batch(status=BatchStatus.PROCESSING)
        running_item = MagicMock()
        mock_repo.get_batch_for_user.return_value = batch
        mock_repo.get_items_by_status.return_value = [running_item]

        result = await service.cancel_batch(batch.id, batch.user_id)

        # Batch stays in current status while items are still running
        assert result == batch
        mock_repo.cancel_pending_items.assert_called_once_with(batch.id)
        mock_repo.update_batch_status.assert_not_called()

    # ── retry_failed ─────────────────────────────────────────────────────

    async def test_retry_failed_non_completed_raises(self, service, mock_repo):
        batch = self._make_batch(status=BatchStatus.PROCESSING)
        mock_repo.get_batch_for_user.return_value = batch

        with pytest.raises(BatchError, match="Can only retry failed items on COMPLETED"):
            await service.retry_failed(batch.id, batch.user_id)

    async def test_retry_failed_pending_raises(self, service, mock_repo):
        batch = self._make_batch(status=BatchStatus.PENDING)
        mock_repo.get_batch_for_user.return_value = batch

        with pytest.raises(BatchError, match="Can only retry failed items on COMPLETED"):
            await service.retry_failed(batch.id, batch.user_id)

    async def test_retry_failed_zero_failed_items(self, service, mock_repo):
        batch = self._make_batch(status=BatchStatus.COMPLETED, failed_items=0)
        mock_repo.get_batch_for_user.return_value = batch

        with pytest.raises(BatchError, match="No failed items to retry"):
            await service.retry_failed(batch.id, batch.user_id)

    async def test_retry_failed_happy_path(self, service, mock_repo):
        batch = self._make_batch(
            status=BatchStatus.COMPLETED, total_items=10,
            completed_items=10, failed_items=3,
        )
        processing_batch = self._make_batch(
            id=batch.id, status=BatchStatus.PROCESSING,
            completed_items=7, failed_items=0,
        )
        mock_repo.get_batch_for_user.return_value = batch
        mock_repo.prepare_retry.return_value = processing_batch

        result = await service.retry_failed(batch.id, batch.user_id)

        assert result.status == BatchStatus.PROCESSING
        assert result.failed_items == 0
        assert result.completed_items == 7
        mock_repo.prepare_retry.assert_called_once_with(batch.id)

    async def test_retry_failed_prepare_retry_returns_none(self, service, mock_repo):
        """When prepare_retry returns None, fall back to original batch."""
        batch = self._make_batch(status=BatchStatus.COMPLETED, failed_items=2)
        mock_repo.get_batch_for_user.return_value = batch
        mock_repo.reset_failed_items.return_value = 2
        mock_repo.prepare_retry.return_value = None

        result = await service.retry_failed(batch.id, batch.user_id)
        assert result == batch

    # ── get_active_batch ─────────────────────────────────────────────────

    async def test_get_active_batch_found(self, service, mock_repo):
        batch = self._make_batch(status=BatchStatus.PROCESSING)
        mock_repo.get_active_batch.return_value = batch

        result = await service.get_active_batch(batch.conversation_id)
        assert result == batch

    async def test_get_active_batch_none(self, service, mock_repo):
        mock_repo.get_active_batch.return_value = None

        result = await service.get_active_batch(uuid4())
        assert result is None
