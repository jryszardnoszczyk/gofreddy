"""Tests for GET /v1/usage — credit field extensions (PR-045)."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient


_USAGE_STATS = {
    "tier": "pro",
    "videos_used": 5,
    "videos_limit": 50000,
    "videos_remaining": 49995,
    "usage_percent": 0.01,
    "billing_period_start": "2026-02-01T00:00:00Z",
    "billing_period_end": "2026-03-01T00:00:00Z",
    "rate_limit_per_minute": 60,
    "subscription_status": "active",
}


class TestUsageCredits:
    """Tests for credit fields on GET /v1/usage."""

    def test_usage_without_hybrid_flag(self, client: TestClient):
        """When hybrid_read_enabled is False, credit fields are omitted."""
        client.app.state.billing_service.get_usage_stats = AsyncMock(return_value=_USAGE_STATS)
        client.app.state.billing_flags.hybrid_read_enabled = False

        resp = client.get(
            "/v1/usage",
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["tier"] == "pro"
        assert data["videos_used"] == 5
        # Credit fields must be absent (response_model_exclude_none=True)
        assert "included_credits_remaining" not in data
        assert "topup_credits_remaining" not in data
        assert "credits_reserved" not in data
        assert "billing_model_version" not in data

    def test_usage_with_hybrid_flag(self, client: TestClient):
        """When hybrid_read_enabled is True, credit fields are populated."""
        client.app.state.billing_service.get_usage_stats = AsyncMock(return_value=_USAGE_STATS)
        client.app.state.billing_flags.hybrid_read_enabled = True

        # Credit service returns balance
        mock_balance = MagicMock()
        mock_balance.included_remaining = 100
        mock_balance.topup_remaining = 50
        mock_balance.reserved_total = 10
        client.app.state.credit_service.get_billing_summary = AsyncMock(
            return_value=mock_balance
        )

        resp = client.get(
            "/v1/usage",
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["tier"] == "pro"
        assert data["included_credits_remaining"] == 100
        assert data["topup_credits_remaining"] == 50
        assert data["credits_reserved"] == 10
        assert data["billing_model_version"] == "credits_v1"

    def test_usage_requires_auth(self, client: TestClient):
        """Usage endpoint rejects unauthenticated requests."""
        resp = client.get("/v1/usage")
        assert resp.status_code in (401, 403)
