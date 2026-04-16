"""Tests for competitive ad search router."""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.routers.competitive import router
from src.api.dependencies import require_pro_competitive
from src.billing.models import BillingContext


def _make_billing_context():
    """Create a mock billing context."""
    ctx = AsyncMock(spec=BillingContext)
    ctx.user = AsyncMock()
    ctx.user.id = uuid4()
    return ctx


def _make_app(ad_service=None, billing_ctx=None) -> FastAPI:
    """Create a test FastAPI app with competitive router."""
    app = FastAPI()

    if ad_service is not None:
        app.state.ad_service = ad_service

    if billing_ctx is None:
        billing_ctx = _make_billing_context()

    async def mock_billing():
        return billing_ctx

    app.dependency_overrides[require_pro_competitive] = mock_billing
    app.include_router(router, prefix="/v1")
    return app


class TestSearchAds:

    def test_search_ads_success(self):
        """POST /v1/competitive/ads/search returns results."""
        ad_service = AsyncMock()
        ad_service.search_ads.return_value = [
            {"id": "ad1", "platform": "meta", "headline": "Test Ad"},
        ]

        app = _make_app(ad_service=ad_service)
        client = TestClient(app)

        resp = client.post("/v1/competitive/ads/search", json={
            "domain": "example.com",
            "limit": 10,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["domain"] == "example.com"
        assert data["ad_count"] == 1
        assert len(data["ads"]) == 1

    def test_search_ads_service_unavailable(self):
        """503 when ad_service not configured."""
        app = _make_app(ad_service=None)
        # Remove ad_service to trigger 503
        if hasattr(app.state, "ad_service"):
            delattr(app.state, "ad_service")
        client = TestClient(app)

        resp = client.post("/v1/competitive/ads/search", json={
            "domain": "example.com",
        })
        assert resp.status_code == 503

    def test_search_ads_invalid_domain(self):
        """422 when domain contains invalid characters."""
        ad_service = AsyncMock()
        app = _make_app(ad_service=ad_service)
        client = TestClient(app)

        resp = client.post("/v1/competitive/ads/search", json={
            "domain": "http://evil.com/path",
        })
        assert resp.status_code == 422

    def test_search_ads_empty_domain(self):
        """422 when domain is empty."""
        ad_service = AsyncMock()
        app = _make_app(ad_service=ad_service)
        client = TestClient(app)

        resp = client.post("/v1/competitive/ads/search", json={
            "domain": "",
        })
        assert resp.status_code == 422

    def test_search_ads_service_error(self):
        """500 when service raises."""
        ad_service = AsyncMock()
        ad_service.search_ads.side_effect = RuntimeError("provider failed")

        app = _make_app(ad_service=ad_service)
        client = TestClient(app)

        resp = client.post("/v1/competitive/ads/search", json={
            "domain": "example.com",
        })
        assert resp.status_code == 500

    def test_search_ads_limit_clamped(self):
        """Limit is clamped to 100 max by schema."""
        ad_service = AsyncMock()
        app = _make_app(ad_service=ad_service)
        client = TestClient(app)

        resp = client.post("/v1/competitive/ads/search", json={
            "domain": "example.com",
            "limit": 999,
        })
        assert resp.status_code == 422
