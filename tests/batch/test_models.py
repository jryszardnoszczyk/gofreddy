"""Tests for batch processing models, exceptions, and config."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.batch.config import BatchSettings
from src.batch.exceptions import (
    BatchAlreadyExistsError,
    BatchError,
    BatchLimitExceededError,
    BatchNotCancellableError,
    BatchNotFoundError,
)
from src.batch.models import BatchItem, BatchJob, BatchStatus, ItemStatus


class TestBatchStatus:
    """Tests for BatchStatus enum."""

    def test_values(self):
        """Test all BatchStatus enum values."""
        assert BatchStatus.PENDING.value == "pending"
        assert BatchStatus.PROCESSING.value == "processing"
        assert BatchStatus.COMPLETED.value == "completed"
        assert BatchStatus.CANCELLED.value == "cancelled"
        assert BatchStatus.FAILED.value == "failed"

    def test_is_str_enum(self):
        """Test BatchStatus is a str enum."""
        assert isinstance(BatchStatus.PENDING, str)
        assert BatchStatus.PENDING == "pending"


class TestItemStatus:
    """Tests for ItemStatus enum."""

    def test_values(self):
        """Test all ItemStatus enum values."""
        assert ItemStatus.PENDING.value == "pending"
        assert ItemStatus.RUNNING.value == "running"
        assert ItemStatus.SUCCEEDED.value == "succeeded"
        assert ItemStatus.FAILED.value == "failed"
        assert ItemStatus.SKIPPED.value == "skipped"
        assert ItemStatus.CANCELLED.value == "cancelled"

    def test_is_str_enum(self):
        """Test ItemStatus is a str enum."""
        assert isinstance(ItemStatus.RUNNING, str)
        assert ItemStatus.RUNNING == "running"


class TestBatchJobIsTerminal:
    """Tests for BatchJob.is_terminal property."""

    @pytest.fixture
    def _base_kwargs(self):
        """Common kwargs for creating a BatchJob."""
        now = datetime.now(UTC)
        return dict(
            id=uuid4(),
            conversation_id=uuid4(),
            collection_id=uuid4(),
            user_id=uuid4(),
            total_items=10,
            completed_items=0,
            failed_items=0,
            flagged_items=0,
            analysis_types=["content"],
            idempotency_key=None,
            created_at=now,
            updated_at=now,
        )

    def test_pending_not_terminal(self, _base_kwargs):
        """PENDING is not a terminal status."""
        job = BatchJob(status=BatchStatus.PENDING, **_base_kwargs)
        assert job.is_terminal is False

    def test_processing_not_terminal(self, _base_kwargs):
        """PROCESSING is not a terminal status."""
        job = BatchJob(status=BatchStatus.PROCESSING, **_base_kwargs)
        assert job.is_terminal is False

    def test_completed_is_terminal(self, _base_kwargs):
        """COMPLETED is a terminal status."""
        job = BatchJob(status=BatchStatus.COMPLETED, **_base_kwargs)
        assert job.is_terminal is True

    def test_cancelled_is_terminal(self, _base_kwargs):
        """CANCELLED is a terminal status."""
        job = BatchJob(status=BatchStatus.CANCELLED, **_base_kwargs)
        assert job.is_terminal is True

    def test_failed_is_terminal(self, _base_kwargs):
        """FAILED is a terminal status."""
        job = BatchJob(status=BatchStatus.FAILED, **_base_kwargs)
        assert job.is_terminal is True


class TestBatchJobFromRow:
    """Tests for BatchJob.from_row class method."""

    def test_from_row_basic(self):
        """Test from_row with a plain dict row."""
        now = datetime.now(UTC)
        job_id = uuid4()
        conv_id = uuid4()
        coll_id = uuid4()
        user_id = uuid4()

        row = {
            "id": job_id,
            "conversation_id": conv_id,
            "collection_id": coll_id,
            "user_id": user_id,
            "status": "processing",
            "total_items": 5,
            "completed_items": 2,
            "failed_items": 1,
            "flagged_items": 0,
            "analysis_types": ["content", "brand"],
            "idempotency_key": "key-123",
            "created_at": now,
            "updated_at": now,
        }

        job = BatchJob.from_row(row)

        assert job.id == job_id
        assert job.conversation_id == conv_id
        assert job.collection_id == coll_id
        assert job.user_id == user_id
        assert job.status == BatchStatus.PROCESSING
        assert isinstance(job.status, BatchStatus)
        assert job.total_items == 5
        assert job.completed_items == 2
        assert job.failed_items == 1
        assert job.flagged_items == 0
        assert job.analysis_types == ["content", "brand"]
        assert job.idempotency_key == "key-123"

    def test_from_row_jsonb_string_parsing(self):
        """Test from_row parses JSONB string fields."""
        now = datetime.now(UTC)
        row = {
            "id": uuid4(),
            "conversation_id": uuid4(),
            "collection_id": uuid4(),
            "user_id": None,
            "status": "pending",
            "total_items": 3,
            "completed_items": 0,
            "failed_items": 0,
            "flagged_items": 0,
            "analysis_types": '["content", "demographics"]',
            "idempotency_key": None,
            "created_at": now,
            "updated_at": now,
        }

        job = BatchJob.from_row(row)

        assert job.analysis_types == ["content", "demographics"]
        assert isinstance(job.analysis_types, list)

    def test_from_row_jsonb_already_parsed(self):
        """Test from_row passes through already-parsed JSONB (list)."""
        now = datetime.now(UTC)
        row = {
            "id": uuid4(),
            "conversation_id": uuid4(),
            "collection_id": uuid4(),
            "user_id": None,
            "status": "completed",
            "total_items": 1,
            "completed_items": 1,
            "failed_items": 0,
            "flagged_items": 0,
            "analysis_types": ["brand"],
            "idempotency_key": None,
            "created_at": now,
            "updated_at": now,
        }

        job = BatchJob.from_row(row)

        assert job.analysis_types == ["brand"]

    def test_from_row_extra_keys_ignored(self):
        """Test from_row ignores unknown columns."""
        now = datetime.now(UTC)
        row = {
            "id": uuid4(),
            "conversation_id": uuid4(),
            "collection_id": uuid4(),
            "user_id": None,
            "status": "pending",
            "total_items": 1,
            "completed_items": 0,
            "failed_items": 0,
            "flagged_items": 0,
            "analysis_types": [],
            "idempotency_key": None,
            "created_at": now,
            "updated_at": now,
            "some_extra_column": "should be ignored",
            "another_unknown": 42,
        }

        job = BatchJob.from_row(row)

        assert job.total_items == 1
        assert not hasattr(job, "some_extra_column")

    def test_frozen(self):
        """Test BatchJob is immutable."""
        now = datetime.now(UTC)
        job = BatchJob(
            id=uuid4(),
            conversation_id=uuid4(),
            collection_id=uuid4(),
            user_id=None,
            status=BatchStatus.PENDING,
            total_items=1,
            completed_items=0,
            failed_items=0,
            flagged_items=0,
            analysis_types=[],
            idempotency_key=None,
            created_at=now,
            updated_at=now,
        )
        with pytest.raises(AttributeError):
            job.status = BatchStatus.COMPLETED  # type: ignore


class TestBatchItemFromRow:
    """Tests for BatchItem.from_row class method."""

    def test_from_row_basic(self):
        """Test from_row with a plain dict row."""
        now = datetime.now(UTC)
        item_id = uuid4()
        batch_id = uuid4()
        ws_item_id = uuid4()

        row = {
            "id": item_id,
            "batch_id": batch_id,
            "workspace_item_id": ws_item_id,
            "status": "succeeded",
            "error_message": None,
            "claimed_at": now,
            "completed_at": now,
        }

        item = BatchItem.from_row(row)

        assert item.id == item_id
        assert item.batch_id == batch_id
        assert item.workspace_item_id == ws_item_id
        assert item.status == ItemStatus.SUCCEEDED
        assert isinstance(item.status, ItemStatus)
        assert item.error_message is None
        assert item.claimed_at == now
        assert item.completed_at == now

    def test_from_row_failed_with_error(self):
        """Test from_row for a failed item with error message."""
        row = {
            "id": uuid4(),
            "batch_id": uuid4(),
            "workspace_item_id": None,
            "status": "failed",
            "error_message": "Video not found",
            "claimed_at": datetime.now(UTC),
            "completed_at": datetime.now(UTC),
        }

        item = BatchItem.from_row(row)

        assert item.status == ItemStatus.FAILED
        assert item.error_message == "Video not found"

    def test_from_row_extra_keys_ignored(self):
        """Test from_row ignores unknown columns."""
        row = {
            "id": uuid4(),
            "batch_id": uuid4(),
            "workspace_item_id": None,
            "status": "pending",
            "error_message": None,
            "claimed_at": None,
            "completed_at": None,
            "extra_col": "ignored",
        }

        item = BatchItem.from_row(row)

        assert item.status == ItemStatus.PENDING
        assert not hasattr(item, "extra_col")

    def test_frozen(self):
        """Test BatchItem is immutable."""
        item = BatchItem(
            id=uuid4(),
            batch_id=uuid4(),
            workspace_item_id=None,
            status=ItemStatus.PENDING,
            error_message=None,
            claimed_at=None,
            completed_at=None,
        )
        with pytest.raises(AttributeError):
            item.status = ItemStatus.RUNNING  # type: ignore


class TestBatchExceptions:
    """Tests for batch exception classes."""

    def test_batch_error_hierarchy(self):
        """Test exception hierarchy."""
        assert issubclass(BatchNotFoundError, BatchError)
        assert issubclass(BatchLimitExceededError, BatchError)
        assert issubclass(BatchAlreadyExistsError, BatchError)
        assert issubclass(BatchNotCancellableError, BatchError)

    def test_batch_limit_exceeded_stores_attributes(self):
        """Test BatchLimitExceededError stores max_size and requested."""
        err = BatchLimitExceededError(max_size=50, requested=100)

        assert err.max_size == 50
        assert err.requested == 100
        assert "100" in str(err)
        assert "50" in str(err)

    def test_batch_already_exists_stores_batch(self):
        """Test BatchAlreadyExistsError stores existing_batch."""
        now = datetime.now(UTC)
        batch = BatchJob(
            id=uuid4(),
            conversation_id=uuid4(),
            collection_id=uuid4(),
            user_id=uuid4(),
            status=BatchStatus.PENDING,
            total_items=5,
            completed_items=0,
            failed_items=0,
            flagged_items=0,
            analysis_types=["content"],
            idempotency_key="idem-key",
            created_at=now,
            updated_at=now,
        )

        err = BatchAlreadyExistsError(existing_batch=batch)

        assert err.existing_batch is batch
        assert str(batch.id) in str(err)

    def test_batch_not_found_error(self):
        """Test BatchNotFoundError can be raised."""
        with pytest.raises(BatchNotFoundError):
            raise BatchNotFoundError("not found")

    def test_batch_not_cancellable_error(self):
        """Test BatchNotCancellableError can be raised."""
        with pytest.raises(BatchNotCancellableError):
            raise BatchNotCancellableError("already completed")


class TestBatchSettings:
    """Tests for BatchSettings configuration."""

    def test_default_values(self):
        """Test BatchSettings default values."""
        settings = BatchSettings()

        assert settings.concurrency == 50
        assert settings.rate_limit_per_sec == 50
        assert settings.max_retries == 3
        assert settings.claim_timeout_seconds == 300
        assert settings.backoff_base == 1.0
        assert settings.deadline_seconds == 540

    def test_env_override(self, monkeypatch):
        """Test BatchSettings reads from BATCH_ prefixed env vars."""
        monkeypatch.setenv("BATCH_CONCURRENCY", "20")
        monkeypatch.setenv("BATCH_RATE_LIMIT_PER_SEC", "50")
        monkeypatch.setenv("BATCH_MAX_RETRIES", "5")
        monkeypatch.setenv("BATCH_CLAIM_TIMEOUT_SECONDS", "600")
        monkeypatch.setenv("BATCH_BACKOFF_BASE", "2.5")

        settings = BatchSettings()

        assert settings.concurrency == 20
        assert settings.rate_limit_per_sec == 50
        assert settings.max_retries == 5
        assert settings.claim_timeout_seconds == 600
        assert settings.backoff_base == 2.5
