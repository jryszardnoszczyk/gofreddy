"""Tests for reports router — competitive brief endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from unittest.mock import MagicMock

from src.api.routers.reports import router
from src.api.dependencies import get_current_user_id, require_pro_geo
from src.competitive.exceptions import BriefNotFoundError
from src.competitive.models import CompetitiveBrief


def _make_app(brief_generator=None, competitive_repo=None, current_user_id=None) -> FastAPI:
    """Create a test FastAPI app with reports router."""
    app = FastAPI()

    if brief_generator is not None:
        # Router uses brief_pipeline which wraps brief_generator
        from src.competitive.brief import CompetitiveBriefPipeline
        app.state.brief_pipeline = CompetitiveBriefPipeline(generator=brief_generator)
    if competitive_repo is not None:
        app.state.competitive_repo = competitive_repo

    if current_user_id:
        async def mock_user_id():
            return current_user_id
        app.dependency_overrides[get_current_user_id] = mock_user_id

    # Override billing — tests don't need real billing
    app.dependency_overrides[require_pro_geo] = lambda: MagicMock()

    app.include_router(router, prefix="/v1")
    return app


def _make_brief(**overrides) -> CompetitiveBrief:
    return CompetitiveBrief(
        id=overrides.get("id", uuid4()),
        client_id=overrides.get("client_id", uuid4()),
        org_id=overrides.get("org_id", uuid4()),
        date_range="7d",
        schema_version=1,
        brief_data=overrides.get("brief_data", {
            "client_name": "TestCo",
            "sections": [],
            "executive_summary": "Test",
            "recommendations": [],
        }),
        idempotency_key=None,
        created_at=datetime.now(timezone.utc),
    )


class TestGenerateBrief:

    def test_generate_brief_success(self):
        """POST /v1/reports/competitive-brief generates brief."""
        user_id = uuid4()
        client_id = uuid4()
        brief = _make_brief(client_id=client_id, org_id=user_id)

        generator = AsyncMock()
        generator.generate.return_value = brief

        app = _make_app(brief_generator=generator, current_user_id=user_id)
        client = TestClient(app)

        resp = client.post("/v1/reports/competitive-brief", json={
            "client_id": str(client_id),
            "date_range": "7d",
            "focus": "volume",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["brief_id"] == str(brief.id)
        assert data["client_id"] == str(client_id)

    def test_generate_brief_service_unavailable(self):
        """503 when brief_generator not configured."""
        app = _make_app(brief_generator=None, current_user_id=uuid4())
        client = TestClient(app)

        resp = client.post("/v1/reports/competitive-brief", json={
            "client_id": str(uuid4()),
        })
        assert resp.status_code == 503

    def test_generate_brief_invalid_date_range(self):
        """422 when date_range is invalid."""
        generator = AsyncMock()
        app = _make_app(brief_generator=generator, current_user_id=uuid4())
        client = TestClient(app)

        resp = client.post("/v1/reports/competitive-brief", json={
            "client_id": str(uuid4()),
            "date_range": "99d",
        })
        assert resp.status_code == 422

    def test_generate_brief_with_idempotency_key(self):
        """POST with Idempotency-Key header forwards to service."""
        user_id = uuid4()
        brief = _make_brief(org_id=user_id)

        generator = AsyncMock()
        generator.generate.return_value = brief

        app = _make_app(brief_generator=generator, current_user_id=user_id)
        client = TestClient(app)

        resp = client.post(
            "/v1/reports/competitive-brief",
            json={"client_id": str(uuid4())},
            headers={"Idempotency-Key": "test-key-123"},
        )
        assert resp.status_code == 200
        generator.generate.assert_called_once()
        call_kwargs = generator.generate.call_args
        assert call_kwargs.kwargs.get("idempotency_key") == "test-key-123"


class TestGetBrief:

    def test_get_brief_success(self):
        """GET /v1/reports/competitive-brief/{id} returns brief."""
        user_id = uuid4()
        brief = _make_brief(org_id=user_id)

        repo = AsyncMock()
        repo.get_brief_with_ownership.return_value = brief

        app = _make_app(competitive_repo=repo, current_user_id=user_id)
        client = TestClient(app)

        resp = client.get(f"/v1/reports/competitive-brief/{brief.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["brief_id"] == str(brief.id)

    def test_get_brief_not_found(self):
        """404 when brief not found."""
        repo = AsyncMock()
        repo.get_brief_with_ownership.side_effect = BriefNotFoundError("not found")

        app = _make_app(competitive_repo=repo, current_user_id=uuid4())
        client = TestClient(app)

        resp = client.get(f"/v1/reports/competitive-brief/{uuid4()}")
        assert resp.status_code == 404

    def test_get_brief_service_unavailable(self):
        """503 when competitive_repo not configured."""
        app = _make_app(competitive_repo=None, current_user_id=uuid4())
        client = TestClient(app)

        resp = client.get(f"/v1/reports/competitive-brief/{uuid4()}")
        assert resp.status_code == 503
