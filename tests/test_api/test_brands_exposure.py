"""Tests for brand exposure REST endpoints — router-level HTTP behavior.

Tests the /v1/brands/* endpoints:
- GET /v1/brands/{analysis_id}/exposure (single-video)
- GET /v1/brands/exposure (multi-video aggregation, Pro-only)
- GET /v1/brands/{analysis_id} (with computed exposure_summary)
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient

from src.billing.tiers import Tier
from src.schemas import (
    BrandAnalysis,
    BrandExposureSummary,
    BrandMention,
    BrandSentiment,
    BrandDetectionSource,
    BrandContext,
    MultiVideoExposureResponse,
    MultiVideoBrandExposure,
)


# ── Helpers ───────────────────────────────────────────────────


def _make_exposure_summary(brand: str = "Nike") -> dict[str, BrandExposureSummary]:
    return {
        brand: BrandExposureSummary(
            brand_name=brand,
            total_mentions=3,
            total_screen_time_seconds=30,
            source_breakdown={"speech": 2, "visual_logo": 1},
            sentiment_distribution={"positive": 0.67, "neutral": 0.33},
            context_distribution={"endorsement": 2, "background": 1},
            is_competitor=False,
        )
    }


def _make_brand_analysis() -> BrandAnalysis:
    return BrandAnalysis(
        video_id="test_video",
        brand_mentions=[
            BrandMention(
                brand_name="Nike",
                detection_source=BrandDetectionSource.SPEECH,
                confidence=0.9,
                timestamp_start="0:10",
                timestamp_end="0:20",
                sentiment=BrandSentiment.POSITIVE,
                context=BrandContext.ENDORSEMENT,
                evidence="test evidence",
                is_competitor=False,
            ),
        ],
        overall_confidence=0.9,
    )


# ── GET /v1/brands/{analysis_id}/exposure ─────────────────────


class TestGetBrandExposure:
    def test_returns_exposure_for_valid_analysis(self, client: TestClient) -> None:
        exposure = _make_exposure_summary()
        client.app.state.brand_service.get_exposure_summary = AsyncMock(return_value=exposure)
        client.app.state.analysis_service.get_by_id = AsyncMock(return_value=MagicMock())
        client.app.state.analysis_repository.user_has_access = AsyncMock(return_value=True)

        aid = uuid4()
        response = client.get(
            f"/v1/brands/{aid}/exposure",
            headers={"Authorization": "Bearer test_key"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "Nike" in data
        assert data["Nike"]["total_mentions"] == 3
        assert data["Nike"]["total_screen_time_seconds"] == 30

    def test_404_when_analysis_not_found(self, client: TestClient) -> None:
        client.app.state.analysis_service.get_by_id = AsyncMock(return_value=None)

        response = client.get(
            f"/v1/brands/{uuid4()}/exposure",
            headers={"Authorization": "Bearer test_key"},
        )
        assert response.status_code == 404

    def test_404_when_user_no_access(self, client: TestClient) -> None:
        client.app.state.analysis_service.get_by_id = AsyncMock(return_value=MagicMock())
        client.app.state.analysis_repository.user_has_access = AsyncMock(return_value=False)

        response = client.get(
            f"/v1/brands/{uuid4()}/exposure",
            headers={"Authorization": "Bearer test_key"},
        )
        assert response.status_code == 404

    def test_404_when_brand_analysis_missing(self, client: TestClient) -> None:
        client.app.state.analysis_service.get_by_id = AsyncMock(return_value=MagicMock())
        client.app.state.analysis_repository.user_has_access = AsyncMock(return_value=True)
        client.app.state.brand_service.get_exposure_summary = AsyncMock(return_value=None)

        response = client.get(
            f"/v1/brands/{uuid4()}/exposure",
            headers={"Authorization": "Bearer test_key"},
        )
        assert response.status_code == 404

    def test_401_without_auth(self, client: TestClient) -> None:
        response = client.get(f"/v1/brands/{uuid4()}/exposure")
        assert response.status_code == 401


# ── GET /v1/brands/exposure (multi-video) ─────────────────────


class TestGetMultiVideoExposure:
    def test_returns_aggregation_for_pro_tier(self, client: TestClient) -> None:
        mv_response = MultiVideoExposureResponse(
            brands={
                "Nike": MultiVideoBrandExposure(
                    total_mentions=5,
                    total_screen_time_seconds=50,
                    average_screen_time_per_video=25.0,
                    videos_appearing_in=2,
                    sentiment_trend={"aid-1": "positive", "aid-2": "neutral"},
                    source_breakdown={"speech": 3, "visual_logo": 2},
                    sentiment_distribution={"positive": 0.6, "neutral": 0.4},
                    is_competitor=False,
                )
            },
            video_count=2,
            analysis_ids=["aid-1", "aid-2"],
        )
        client.app.state.brand_service.get_multi_video_exposure = AsyncMock(return_value=mv_response)

        aid1, aid2 = uuid4(), uuid4()
        client.app.state.analysis_repository.batch_user_has_access = AsyncMock(
            return_value={aid1, aid2}
        )

        response = client.get(
            f"/v1/brands/exposure?analysis_ids={aid1},{aid2}",
            headers={"Authorization": "Bearer test_key"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["video_count"] == 2
        assert "Nike" in data["brands"]
        assert data["brands"]["Nike"]["total_mentions"] == 5

    def test_403_for_free_tier(self, client: TestClient) -> None:
        """Free tier users cannot access multi-video aggregation."""
        from src.api.dependencies import get_billing_context
        from src.billing.models import BillingContext, UsagePeriod, User
        from datetime import UTC, datetime

        now = datetime.now(UTC)
        user_id = uuid4()
        free_ctx = BillingContext(
            user=User(id=user_id, email="test@test.com", stripe_customer_id=None, created_at=now),
            tier=Tier.FREE,
            usage_period=UsagePeriod(
                id=uuid4(), user_id=user_id,
                period_start=now, period_end=now,
                videos_used=0, videos_limit=100,
            ),
            subscription=None,
        )
        client.app.dependency_overrides[get_billing_context] = lambda: free_ctx

        response = client.get(
            f"/v1/brands/exposure?analysis_ids={uuid4()},{uuid4()}",
            headers={"Authorization": "Bearer test_key"},
        )
        assert response.status_code == 403
        body = response.json()
        # Custom exception handler maps detail → error
        error = body.get("detail") or body.get("error")
        assert error["code"] == "tier_required"

        # Clean up override
        del client.app.dependency_overrides[get_billing_context]

    def test_422_invalid_uuid(self, client: TestClient) -> None:
        response = client.get(
            "/v1/brands/exposure?analysis_ids=not-a-uuid",
            headers={"Authorization": "Bearer test_key"},
        )
        assert response.status_code == 422

    def test_422_empty_analysis_ids(self, client: TestClient) -> None:
        response = client.get(
            "/v1/brands/exposure?analysis_ids=",
            headers={"Authorization": "Bearer test_key"},
        )
        assert response.status_code == 422

    def test_404_when_access_denied(self, client: TestClient) -> None:
        """If user doesn't have access to all IDs, returns 404."""
        aid1, aid2 = uuid4(), uuid4()
        # Only authorize one of two
        client.app.state.analysis_repository.batch_user_has_access = AsyncMock(
            return_value={aid1}
        )

        response = client.get(
            f"/v1/brands/exposure?analysis_ids={aid1},{aid2}",
            headers={"Authorization": "Bearer test_key"},
        )
        assert response.status_code == 404

    def test_deduplicates_analysis_ids(self, client: TestClient) -> None:
        """Duplicate UUIDs should be deduplicated."""
        aid = uuid4()
        mv_response = MultiVideoExposureResponse(
            brands={},
            video_count=1,
            analysis_ids=[str(aid)],
        )
        client.app.state.brand_service.get_multi_video_exposure = AsyncMock(return_value=mv_response)
        client.app.state.analysis_repository.batch_user_has_access = AsyncMock(
            return_value={aid}
        )

        response = client.get(
            f"/v1/brands/exposure?analysis_ids={aid},{aid},{aid}",
            headers={"Authorization": "Bearer test_key"},
        )
        assert response.status_code == 200
        # batch_user_has_access should be called with deduplicated list
        call_args = client.app.state.analysis_repository.batch_user_has_access.call_args
        assert len(call_args[0][0]) == 1  # Only 1 unique UUID


# ── GET /v1/brands/{analysis_id} (with exposure_summary) ──────


class TestGetBrandAnalysisWithExposure:
    def test_includes_exposure_summary(self, client: TestClient) -> None:
        analysis = _make_brand_analysis()
        client.app.state.brand_service.get_brand_analysis = AsyncMock(return_value=analysis)
        client.app.state.analysis_service.get_by_id = AsyncMock(return_value=MagicMock())
        client.app.state.analysis_repository.user_has_access = AsyncMock(return_value=True)

        aid = uuid4()
        response = client.get(
            f"/v1/brands/{aid}",
            headers={"Authorization": "Bearer test_key"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "exposure_summary" in data
        assert "Nike" in data["exposure_summary"]
        assert data["exposure_summary"]["Nike"]["total_mentions"] == 1

    def test_404_when_brand_analysis_not_found(self, client: TestClient) -> None:
        client.app.state.analysis_service.get_by_id = AsyncMock(return_value=MagicMock())
        client.app.state.analysis_repository.user_has_access = AsyncMock(return_value=True)
        client.app.state.brand_service.get_brand_analysis = AsyncMock(return_value=None)

        response = client.get(
            f"/v1/brands/{uuid4()}",
            headers={"Authorization": "Bearer test_key"},
        )
        assert response.status_code == 404
