"""Tests for generation API router."""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.routers.generation import router, _require_generation_enabled
from src.billing.models import BillingContext, UsagePeriod, User
from src.billing.tiers import Tier
from src.generation.config import GenerationSettings
from src.generation.exceptions import (
    GenerationConcurrentLimitExceeded,
    GenerationDailySpendLimitExceeded,
    GenerationError,
)
from src.generation.fake_storage import FakeGenerationAssetStorage


def _make_billing(user_id, tier=Tier.PRO):
    now = datetime.now(timezone.utc)
    user = User(id=user_id, email="test@test.com", stripe_customer_id=None, created_at=now)
    usage = UsagePeriod(
        id=uuid4(), user_id=user_id,
        period_start=now, period_end=now,
        videos_used=0, videos_limit=50000,
    )
    return BillingContext(user=user, tier=tier, usage_period=usage, subscription=None)


@pytest.fixture
def mock_service():
    return MagicMock()


@pytest.fixture
def user_id():
    return uuid4()


@pytest.fixture
def app(mock_service, user_id):
    from src.api.dependencies import get_current_user_id, require_pro_generation

    test_app = FastAPI()
    test_app.include_router(router, prefix="/v1")

    billing = _make_billing(user_id)
    test_app.dependency_overrides[get_current_user_id] = lambda: user_id
    test_app.dependency_overrides[require_pro_generation] = lambda: billing
    test_app.dependency_overrides[_require_generation_enabled] = lambda: None
    test_app.state.generation_service = mock_service

    return test_app


@pytest.fixture
def client(app):
    return TestClient(app)


def _make_composition_spec():
    return {
        "cadres": [
            {"index": 0, "prompt": "a sunset scene", "duration_seconds": 5},
            {"index": 1, "prompt": "a beach scene", "duration_seconds": 5},
        ],
    }


class TestSubmitJob:
    def test_success(self, client, mock_service):
        job_id = uuid4()
        mock_service.submit_job = AsyncMock(return_value={
            "job_id": job_id,
            "status": "pending",
            "cadre_count": 2,
            "estimated_cost_cents": 70,
        })

        resp = client.post(
            "/v1/generation/jobs",
            json={"composition_spec": _make_composition_spec()},
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "pending"
        assert data["cadre_count"] == 2

    def test_concurrent_limit(self, client, mock_service):
        mock_service.submit_job = AsyncMock(
            side_effect=GenerationConcurrentLimitExceeded("Max 2 concurrent")
        )

        resp = client.post(
            "/v1/generation/jobs",
            json={"composition_spec": _make_composition_spec()},
        )

        assert resp.status_code == 429

    def test_daily_spend_limit(self, client, mock_service):
        mock_service.submit_job = AsyncMock(
            side_effect=GenerationDailySpendLimitExceeded("Over limit")
        )

        resp = client.post(
            "/v1/generation/jobs",
            json={"composition_spec": _make_composition_spec()},
        )

        assert resp.status_code == 403

    def test_generation_error(self, client, mock_service):
        mock_service.submit_job = AsyncMock(
            side_effect=GenerationError("Service unavailable")
        )

        resp = client.post(
            "/v1/generation/jobs",
            json={"composition_spec": _make_composition_spec()},
        )

        assert resp.status_code == 503

    def test_empty_cadres_rejected(self, client, mock_service):
        resp = client.post(
            "/v1/generation/jobs",
            json={"composition_spec": {"cadres": []}},
        )

        assert resp.status_code == 422

    def test_too_many_cadres_rejected(self, client, mock_service):
        spec = {
            "cadres": [
                {"index": i % 20, "prompt": f"cadre {i}", "duration_seconds": 5}
                for i in range(21)
            ],
        }
        resp = client.post(
            "/v1/generation/jobs",
            json={"composition_spec": spec},
        )

        assert resp.status_code == 422


class TestGetJob:
    def test_success(self, client, mock_service):
        job_id = uuid4()
        mock_service.get_job_status = AsyncMock(return_value={
            "job_id": job_id,
            "status": "generating",
            "current_cadre": 1,
            "total_cadres": 2,
            "video_url": None,
            "video_url_expires_at": None,
            "cost_cents": 35,
            "cadre_statuses": [
                {"index": 0, "status": "completed"},
                {"index": 1, "status": "generating"},
            ],
            "error": None,
        })

        resp = client.get(f"/v1/generation/jobs/{job_id}")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "generating"
        assert len(data["cadre_statuses"]) == 2

    def test_not_found(self, client, mock_service):
        mock_service.get_job_status = AsyncMock(return_value=None)

        resp = client.get(f"/v1/generation/jobs/{uuid4()}")

        assert resp.status_code == 404


class TestListJobs:
    def test_success(self, client, mock_service):
        from datetime import datetime, timezone
        job_id = uuid4()
        mock_service.list_jobs = AsyncMock(return_value={
            "jobs": [
                {
                    "id": job_id,
                    "status": "pending",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "cadre_count": 2,
                    "video_url": None,
                }
            ],
            "total": 1,
        })

        resp = client.get("/v1/generation/jobs")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["jobs"]) == 1

    def test_with_status_filter(self, client, mock_service):
        mock_service.list_jobs = AsyncMock(return_value={"jobs": [], "total": 0})

        resp = client.get("/v1/generation/jobs?status=completed")

        assert resp.status_code == 200
        mock_service.list_jobs.assert_called_once()
        call_args = mock_service.list_jobs.call_args
        assert call_args[0][1] == "completed"  # status_filter


class TestCancelJob:
    def test_success(self, client, mock_service):
        job_id = uuid4()
        mock_service.cancel_job = AsyncMock(return_value={
            "job_id": job_id,
            "status": "pending",
            "cancellation_requested": True,
        })

        resp = client.delete(f"/v1/generation/jobs/{job_id}")

        assert resp.status_code == 200
        data = resp.json()
        assert data["cancellation_requested"] is True

    def test_not_found(self, client, mock_service):
        mock_service.cancel_job = AsyncMock(return_value=None)

        resp = client.delete(f"/v1/generation/jobs/{uuid4()}")

        assert resp.status_code == 404


class TestFeatureDisabled:
    def test_503_when_disabled(self, mock_service, user_id):
        from src.api.dependencies import get_current_user_id, require_pro_generation

        test_app = FastAPI()
        test_app.include_router(router, prefix="/v1")

        config = GenerationSettings(_env_file=None, generation_enabled=False)

        billing = _make_billing(user_id)
        test_app.dependency_overrides[get_current_user_id] = lambda: user_id
        test_app.dependency_overrides[require_pro_generation] = lambda: billing
        test_app.state.generation_service = mock_service
        # Wire real _require_generation_enabled with disabled config
        test_app.state.generation_config = config

        client = TestClient(test_app)
        resp = client.get(f"/v1/generation/jobs/{uuid4()}")

        assert resp.status_code == 503


class TestFakeAssets:
    def test_serves_fake_generation_asset(self, app):
        backend = FakeGenerationAssetStorage("http://127.0.0.1:8080")
        backend.put_asset("generated/test-user/test-job/final.mp4", b"fake-video", "video/mp4")
        app.state.generation_storage = type(
            "FakeGenerationStorageState",
            (),
            {"_video_storage": backend},
        )()

        client = TestClient(app)
        resp = client.get("/v1/generation/assets/generated/test-user/test-job/final.mp4")

        assert resp.status_code == 200
        assert resp.headers["content-type"] == "video/mp4"
        assert resp.content == b"fake-video"

    def test_missing_fake_generation_asset_returns_404(self, app):
        backend = FakeGenerationAssetStorage("http://127.0.0.1:8080")
        app.state.generation_storage = type(
            "FakeGenerationStorageState",
            (),
            {"_video_storage": backend},
        )()

        client = TestClient(app)
        resp = client.get("/v1/generation/assets/generated/test-user/test-job/missing.mp4")

        assert resp.status_code == 404
