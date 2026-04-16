"""Tests for GET /v1/library endpoint and supporting functions."""

import base64
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.analysis.models import LibraryItem
from src.api.routers.library import _decode_cursor, _encode_cursor
from src.api.schemas import ContentRiskLevel, compute_risk_level
from src.billing.models import BillingContext, UsagePeriod, User
from src.billing.tiers import Tier


# ── compute_risk_level (pure function) ──────────────────────────────────────


class TestComputeContentRiskLevel:
    """Pure function: compute_risk_level(overall_safe, moderation_flags)."""

    def test_safe_returns_safe(self):
        assert compute_risk_level(True, []) == ContentRiskLevel.SAFE

    def test_safe_ignores_flags(self):
        flags = [{"severity": "high", "moderation_class": "violence"}]
        assert compute_risk_level(True, flags) == ContentRiskLevel.SAFE

    def test_unsafe_no_high_severity_returns_risky(self):
        flags = [{"severity": "low", "moderation_class": "mild_language"}]
        assert compute_risk_level(False, flags) == ContentRiskLevel.RISKY

    def test_unsafe_high_severity_returns_critical(self):
        flags = [{"severity": "high", "moderation_class": "violence"}]
        assert compute_risk_level(False, flags) == ContentRiskLevel.CRITICAL

    def test_unsafe_critical_severity_returns_critical(self):
        flags = [{"severity": "critical", "moderation_class": "csam"}]
        assert compute_risk_level(False, flags) == ContentRiskLevel.CRITICAL

    def test_unsafe_empty_flags_returns_risky(self):
        assert compute_risk_level(False, []) == ContentRiskLevel.RISKY

    def test_severity_as_dict(self):
        """Handle severity stored as dict with 'value' key."""
        flags = [{"severity": {"value": "high"}, "moderation_class": "violence"}]
        assert compute_risk_level(False, flags) == ContentRiskLevel.CRITICAL

    def test_severity_case_insensitive(self):
        flags = [{"severity": "HIGH", "moderation_class": "violence"}]
        assert compute_risk_level(False, flags) == ContentRiskLevel.CRITICAL


# ── Cursor encode/decode ────────────────────────────────────────────────────


class TestCursorCodec:
    """Cursor encoding and decoding round-trips correctly."""

    def test_round_trip(self):
        item = LibraryItem(
            id=uuid4(),
            video_id=uuid4(),
            title="Test",
            platform="tiktok",
            overall_safe=True,
            moderation_flags=[],
            analyzed_at=datetime(2026, 3, 1, 12, 0, 0, tzinfo=UTC),
            has_brands=False,
            has_demographics=False,
            has_deepfake=False,
            has_creative=False,
            has_fraud=False,
        )
        encoded = _encode_cursor(item)
        decoded_date, decoded_id = _decode_cursor(encoded)
        assert decoded_id == item.id
        assert decoded_date == item.analyzed_at

    def test_invalid_cursor_raises(self):
        with pytest.raises(Exception):
            _decode_cursor("not-valid-base64!!!")

    def test_malformed_payload_raises(self):
        bad = base64.b64encode(b"no-pipe-here").decode()
        with pytest.raises(Exception):
            _decode_cursor(bad)


# ── GET /v1/library router tests ────────────────────────────────────────────


def _make_library_item(**overrides) -> LibraryItem:
    """Helper to create LibraryItem with sensible defaults."""
    defaults = dict(
        id=uuid4(),
        video_id=uuid4(),
        title="Test Video",
        platform="tiktok",
        overall_safe=True,
        moderation_flags=[],
        analyzed_at=datetime.now(UTC),
        has_brands=False,
        has_demographics=False,
        has_deepfake=False,
        has_creative=False,
        has_fraud=False,
    )
    defaults.update(overrides)
    return LibraryItem(**defaults)


class TestLibraryEndpoint:
    """Tests for GET /v1/library."""

    def test_empty_library(self, client: TestClient):
        """Returns empty list when user has no analyses."""
        client.app.state.analysis_repository.list_for_user = AsyncMock(
            return_value=([], False)
        )
        resp = client.get(
            "/v1/library",
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["has_more"] is False
        assert data["next_cursor"] is None

    def test_returns_items_with_risk_level(self, client: TestClient):
        """Items include computed risk_level."""
        items = [
            _make_library_item(overall_safe=True),
            _make_library_item(
                overall_safe=False,
                moderation_flags=[{"severity": "high", "moderation_class": "violence"}],
            ),
        ]
        client.app.state.analysis_repository.list_for_user = AsyncMock(
            return_value=(items, False)
        )
        resp = client.get(
            "/v1/library",
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["items"][0]["risk_level"] == "safe"
        assert data["items"][1]["risk_level"] == "critical"

    def test_pagination_cursor(self, client: TestClient):
        """When has_more=True, response includes next_cursor."""
        items = [_make_library_item()]
        client.app.state.analysis_repository.list_for_user = AsyncMock(
            return_value=(items, True)
        )
        resp = client.get(
            "/v1/library",
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["has_more"] is True
        assert data["next_cursor"] is not None

    def test_invalid_platform_returns_400(self, client: TestClient):
        """Unknown platform returns 400."""
        resp = client.get(
            "/v1/library?platform=twitter",
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "invalid_platform"

    def test_valid_platforms_accepted(self, client: TestClient):
        """Known platforms pass validation."""
        client.app.state.analysis_repository.list_for_user = AsyncMock(
            return_value=([], False)
        )
        for platform in ("tiktok", "instagram", "youtube"):
            resp = client.get(
                f"/v1/library?platform={platform}",
                headers={"Authorization": "Bearer test-token"},
            )
            assert resp.status_code == 200, f"Failed for {platform}"

    def test_invalid_cursor_returns_400(self, client: TestClient):
        """Malformed cursor returns 400."""
        resp = client.get(
            "/v1/library?cursor=not-valid",
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "invalid_cursor"

    def test_limit_bounds(self, client: TestClient):
        """Limit must be 1-100."""
        resp = client.get(
            "/v1/library?limit=0",
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 422  # FastAPI validation

        resp = client.get(
            "/v1/library?limit=101",
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 422

    def test_search_max_length(self, client: TestClient):
        """Search query over 200 chars is rejected."""
        long_search = "a" * 201
        resp = client.get(
            f"/v1/library?search={long_search}",
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 422

    def test_requires_auth(self, client: TestClient):
        """Unauthenticated request is rejected."""
        resp = client.get("/v1/library")
        assert resp.status_code in (401, 403)

    def test_free_tier_filters_old_items(self, client: TestClient):
        """Free tier excludes items older than 30 days."""
        from src.api.dependencies import get_billing_context

        # Override billing context to return free tier
        now = datetime.now(UTC)
        free_ctx = BillingContext(
            user=User(id=uuid4(), email="free@test.com", stripe_customer_id=None, created_at=now),
            tier=Tier.FREE,
            usage_period=UsagePeriod(
                id=uuid4(), user_id=uuid4(),
                period_start=now, period_end=now,
                videos_used=0, videos_limit=100,
            ),
            subscription=None,
        )
        client.app.dependency_overrides[get_billing_context] = lambda: free_ctx

        recent_item = _make_library_item(analyzed_at=now - timedelta(days=5))
        old_item = _make_library_item(analyzed_at=now - timedelta(days=45))

        client.app.state.analysis_repository.list_for_user = AsyncMock(
            return_value=([recent_item, old_item], False)
        )

        resp = client.get(
            "/v1/library",
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == str(recent_item.id)

    def test_pro_tier_returns_all_items(self, client: TestClient):
        """Pro tier returns items regardless of age."""
        now = datetime.now(UTC)
        old_item = _make_library_item(analyzed_at=now - timedelta(days=90))

        client.app.state.analysis_repository.list_for_user = AsyncMock(
            return_value=([old_item], False)
        )

        resp = client.get(
            "/v1/library",
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 200
        data = resp.json()
        # Default client fixture is Pro tier
        assert len(data["items"]) == 1
