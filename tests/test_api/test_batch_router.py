import pytest
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient

from src.api.dependencies import get_current_user_id
from src.api.main import create_app
from src.api.rate_limit import limiter
from src.api.routers.batch import _get_batch_worker
from src.batch.exceptions import (
    BatchNotCancellableError,
    BatchNotFoundError,
    BatchError,
)
from src.batch.models import BatchJob, BatchStatus


@pytest.fixture
def test_user_id():
    return uuid4()


@pytest.fixture
def mock_batch_service():
    return AsyncMock()


@pytest.fixture
def mock_batch_worker():
    worker = MagicMock()
    worker.process_batch = AsyncMock()
    return worker


@pytest.fixture
def app(mock_batch_service, mock_batch_worker, test_user_id):
    app = create_app()
    app.state.batch_service = mock_batch_service

    async def override_user_id():
        return test_user_id

    app.dependency_overrides[get_current_user_id] = override_user_id
    app.dependency_overrides[_get_batch_worker] = lambda: mock_batch_worker
    limiter.enabled = False
    yield app
    limiter.enabled = True
    app.dependency_overrides.clear()


@pytest.fixture
def client(app):
    return TestClient(app, raise_server_exceptions=False)


def _make_batch(**kwargs):
    defaults = {
        "id": uuid4(),
        "conversation_id": uuid4(),
        "collection_id": uuid4(),
        "user_id": uuid4(),
        "status": BatchStatus.PROCESSING,
        "total_items": 10,
        "completed_items": 3,
        "failed_items": 1,
        "flagged_items": 0,
        "analysis_types": ["brand_safety"],
        "idempotency_key": None,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    defaults.update(kwargs)
    return BatchJob(**defaults)


class TestGetBatch:

    def test_get_batch_success(self, client, mock_batch_service, test_user_id):
        batch = _make_batch(user_id=test_user_id)
        mock_batch_service.get_batch.return_value = batch

        resp = client.get(f"/v1/batch/{batch.id}")

        assert resp.status_code == 200
        data = resp.json()
        assert data["batch_id"] == str(batch.id)
        assert data["status"] == "processing"
        assert data["total_items"] == 10
        assert data["completed_items"] == 3
        assert data["failed_items"] == 1
        assert data["flagged_items"] == 0
        assert data["analysis_types"] == ["brand_safety"]
        assert "created_at" in data
        assert "updated_at" in data

    def test_get_batch_not_found(self, client, mock_batch_service):
        batch_id = uuid4()
        mock_batch_service.get_batch.side_effect = BatchNotFoundError("not found")

        resp = client.get(f"/v1/batch/{batch_id}")

        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "batch_not_found"


class TestCancelBatch:

    def test_cancel_batch_success(self, client, mock_batch_service, test_user_id):
        batch = _make_batch(user_id=test_user_id, status=BatchStatus.CANCELLED)
        mock_batch_service.cancel_batch.return_value = batch

        resp = client.post(f"/v1/batch/{batch.id}/cancel")

        assert resp.status_code == 202
        data = resp.json()
        assert data["batch_id"] == str(batch.id)
        assert data["cancellation_requested"] is True

    def test_cancel_batch_not_found(self, client, mock_batch_service):
        batch_id = uuid4()
        mock_batch_service.cancel_batch.side_effect = BatchNotFoundError("not found")

        resp = client.post(f"/v1/batch/{batch_id}/cancel")

        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "batch_not_found"

    def test_cancel_batch_not_cancellable(self, client, mock_batch_service):
        batch_id = uuid4()
        mock_batch_service.cancel_batch.side_effect = BatchNotCancellableError(
            "Batch is already in terminal state"
        )

        resp = client.post(f"/v1/batch/{batch_id}/cancel")

        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "batch_not_cancellable"


class TestRetryFailed:

    def test_retry_failed_success(self, client, mock_batch_service, test_user_id):
        batch = _make_batch(user_id=test_user_id, status=BatchStatus.PROCESSING)
        mock_batch_service.retry_failed.return_value = batch

        resp = client.post(f"/v1/batch/{batch.id}/retry-failed")

        assert resp.status_code == 202
        data = resp.json()
        assert data["batch_id"] == str(batch.id)
        assert data["retry_requested"] is True

    def test_retry_failed_not_found(self, client, mock_batch_service):
        batch_id = uuid4()
        mock_batch_service.retry_failed.side_effect = BatchNotFoundError("not found")

        resp = client.post(f"/v1/batch/{batch_id}/retry-failed")

        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "batch_not_found"

    def test_retry_failed_invalid_state(self, client, mock_batch_service):
        batch_id = uuid4()
        mock_batch_service.retry_failed.side_effect = BatchError(
            "Batch has no failed items to retry"
        )

        resp = client.post(f"/v1/batch/{batch_id}/retry-failed")

        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "batch_retry_failed"
