"""Tests for creator endpoints — router-level HTTP behavior."""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.analysis.service import AnalysisResult
from src.common.enums import Platform
from src.fetcher.exceptions import CreatorNotFoundError
from src.schemas import RiskCategory, RiskDetection, Severity, VideoAnalysis


@pytest.mark.mock_required
class TestAnalyzeCreator:
    """Tests for POST /v1/analyze/creator — mocks required for service responses."""

    def test_analyzes_creator_videos(
        self,
        client: TestClient,
        mock_analysis_service,
        mock_fetchers,
        mock_video_result,
        valid_api_key: str,
    ) -> None:
        """Analyzes creator's videos successfully."""
        mock_analysis_service.analyze = AsyncMock(
            return_value=AnalysisResult(
                analysis=VideoAnalysis(
                    video_id="123456789",
                    overall_safe=True,
                    overall_confidence=0.95,
                    risks_detected=[],
                    summary="No risks",
                ),
                cached=False,
                cost_usd=0.001,
                record_id=uuid4(),
            )
        )

        response = client.post(
            "/v1/analyze/creator",
            json={"platform": "tiktok", "username": "testuser", "limit": 5},
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["creator_username"] == "testuser"
        assert data["platform"] == "tiktok"
        assert data["videos_analyzed"] == 1
        assert data["success_rate"] == 1.0
        assert isinstance(data["results"][0]["overall_confidence"], (int, float))
        assert 0.0 <= data["results"][0]["overall_confidence"] <= 1.0

    def test_returns_typed_risk_items(
        self,
        client: TestClient,
        mock_analysis_service,
        mock_fetchers,
        mock_video_result,
        valid_api_key: str,
    ) -> None:
        """Ensures creator analyze responses return typed legacy risk payloads."""
        mock_analysis_service.analyze = AsyncMock(
            return_value=AnalysisResult(
                analysis=VideoAnalysis(
                    video_id="123456789",
                    overall_safe=False,
                    overall_confidence=0.9,
                    risks_detected=[
                        RiskDetection(
                            category=RiskCategory.CONTROVERSIAL,
                            severity=Severity.MEDIUM,
                            confidence=0.82,
                            description="Controversial topic discussed",
                            evidence="Speech references polarizing social issue",
                        )
                    ],
                    summary="Moderate controversy risk detected",
                ),
                cached=False,
                cost_usd=0.001,
                record_id=uuid4(),
            )
        )

        response = client.post(
            "/v1/analyze/creator",
            json={"platform": "tiktok", "username": "testuser", "limit": 5},
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 200
        data = response.json()
        risk = data["results"][0]["risks_detected"][0]
        assert risk["risk_type"] == RiskCategory.CONTROVERSIAL.value
        assert risk["category"] == RiskCategory.CONTROVERSIAL.value
        assert risk["severity"] == Severity.MEDIUM.value
        assert isinstance(risk["confidence"], (int, float))
        assert 0.0 <= risk["confidence"] <= 1.0
        assert isinstance(risk["description"], str)
        assert isinstance(risk["evidence"], str)

    def test_returns_404_for_unknown_creator(
        self,
        client: TestClient,
        mock_fetchers,
        valid_api_key: str,
    ) -> None:
        """Returns 404 when creator is not found."""
        mock_fetchers[Platform.TIKTOK].fetch_creator_videos = AsyncMock(
            side_effect=CreatorNotFoundError(Platform.TIKTOK, "unknown_user")
        )

        response = client.post(
            "/v1/analyze/creator",
            json={"platform": "tiktok", "username": "unknown_user", "limit": 5},
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "creator_not_found"

    def test_handles_empty_video_list(
        self,
        client: TestClient,
        mock_fetchers,
        valid_api_key: str,
    ) -> None:
        """Handles creator with no videos."""
        empty_batch = MagicMock()
        empty_batch.successes = []
        empty_batch.errors = []
        mock_fetchers[Platform.TIKTOK].fetch_creator_videos = AsyncMock(
            return_value=empty_batch
        )

        response = client.post(
            "/v1/analyze/creator",
            json={"platform": "tiktok", "username": "empty_user", "limit": 5},
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["videos_analyzed"] == 0
        assert data["success_rate"] == 1.0

    def test_upserts_creator_profile_when_no_videos_are_analyzable(
        self,
        client: TestClient,
        mock_fetchers,
        valid_api_key: str,
    ) -> None:
        """Persists creator profile cache row even when no videos were analyzed."""
        batch = SimpleNamespace(results=[], errors=[])
        mock_fetchers[Platform.TIKTOK].fetch_creator_videos = AsyncMock(return_value=batch)

        response = client.post(
            "/v1/analyze/creator",
            json={"platform": "tiktok", "username": "empty_user", "limit": 5},
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )

        assert response.status_code == 200
        assert response.json()["videos_analyzed"] == 0

        upsert_mock = client.app.state.evolution_repository.upsert_creator_profile
        upsert_mock.assert_awaited_once()
        upsert_kwargs = upsert_mock.await_args.kwargs
        assert upsert_kwargs["platform"] == Platform.TIKTOK
        assert upsert_kwargs["username"] == "empty_user"
        assert upsert_kwargs["last_analyzed_at"] is None
        assert upsert_kwargs["cached_at"] is not None

    def test_preserves_batch_fetch_errors_in_response(
        self,
        client: TestClient,
        mock_analysis_service,
        mock_fetchers,
        mock_video_result,
        valid_api_key: str,
    ) -> None:
        """Includes fetch-layer errors alongside analyzed results."""
        mock_analysis_service.analyze = AsyncMock(
            return_value=AnalysisResult(
                analysis=VideoAnalysis(
                    video_id="123456789",
                    overall_safe=True,
                    overall_confidence=0.95,
                    risks_detected=[],
                    summary="No risks",
                ),
                cached=False,
                cost_usd=0.001,
                record_id=uuid4(),
            )
        )
        fetch_error = SimpleNamespace(
            video_id="missing_video",
            platform=Platform.TIKTOK,
            error_type=SimpleNamespace(value="not_found"),
            message="Video not found",
            retryable=False,
            retry_after_seconds=None,
            alternative_action="Try later",
        )
        batch = SimpleNamespace(results=[mock_video_result], errors=[fetch_error])
        mock_fetchers[Platform.TIKTOK].fetch_creator_videos = AsyncMock(return_value=batch)

        response = client.post(
            "/v1/analyze/creator",
            json={"platform": "tiktok", "username": "testuser", "limit": 5},
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["videos_analyzed"] == 1
        assert len(data["errors"]) == 1
        assert data["success_rate"] == 0.5
        assert data["errors"][0]["video_id"] == "missing_video"
        assert data["errors"][0]["error_code"] == "not_found"

    def test_normalizes_fetch_errors_when_no_videos_analyzed(
        self,
        client: TestClient,
        mock_fetchers,
        valid_api_key: str,
    ) -> None:
        """Returns normalized fetch errors even when batch has zero successful videos."""
        fetch_error = SimpleNamespace(
            video_id="missing_video",
            platform=Platform.TIKTOK,
            error_type=SimpleNamespace(value="not_found"),
            message="Video not found",
            retryable=False,
            retry_after_seconds=None,
            alternative_action="Try later",
        )
        batch = SimpleNamespace(results=[], errors=[fetch_error])
        mock_fetchers[Platform.TIKTOK].fetch_creator_videos = AsyncMock(return_value=batch)

        response = client.post(
            "/v1/analyze/creator",
            json={"platform": "tiktok", "username": "testuser", "limit": 5},
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["videos_analyzed"] == 0
        assert len(data["errors"]) == 1
        assert data["success_rate"] == 0.0
        assert data["errors"][0]["video_id"] == "missing_video"
        assert data["errors"][0]["error_code"] == "not_found"


class TestCreatorValidation:
    """Tests for creator endpoint validation — pure HTTP, no service calls."""

    def test_requires_authentication(self, client: TestClient) -> None:
        """Requires API key authentication."""
        response = client.post(
            "/v1/analyze/creator",
            json={"platform": "tiktok", "username": "testuser", "limit": 5},
        )
        assert response.status_code in [401, 403]

    def test_validates_platform(
        self, client: TestClient, valid_api_key: str
    ) -> None:
        """Validates platform value."""
        response = client.post(
            "/v1/analyze/creator",
            json={"platform": "invalid_platform", "username": "testuser"},
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 422

    def test_validates_username_format(
        self, client: TestClient, valid_api_key: str
    ) -> None:
        """Validates username format."""
        response = client.post(
            "/v1/analyze/creator",
            json={"platform": "tiktok", "username": "invalid user name!"},
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 422

    def test_validates_limit_range(
        self, client: TestClient, valid_api_key: str
    ) -> None:
        """Validates limit is within allowed range."""
        response = client.post(
            "/v1/analyze/creator",
            json={"platform": "tiktok", "username": "testuser", "limit": 101},
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 422

        response = client.post(
            "/v1/analyze/creator",
            json={"platform": "tiktok", "username": "testuser", "limit": 0},
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 422


class TestGetCreatorProfile:
    """Tests for GET /v1/creators/{platform}/{username} — validation tests."""

    def test_returns_200_for_cached_creator_profile_in_db_repository(
        self, client: TestClient, valid_api_key: str
    ) -> None:
        """Returns 200 when DB-backed creator profile cache has a matching row."""
        cached_at = datetime.now(timezone.utc)
        last_analyzed = datetime(2026, 2, 1, tzinfo=timezone.utc)
        client.app.state.evolution_repository.get_creator_profile = AsyncMock(
            return_value=SimpleNamespace(
                platform=Platform.TIKTOK,
                username="testuser",
                display_name="Test User",
                follower_count=1234,
                video_count=42,
                last_analyzed_at=last_analyzed,
                cached_at=cached_at,
            )
        )

        response = client.get(
            "/v1/creators/tiktok/testuser",
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["platform"] == "tiktok"
        assert data["username"] == "testuser"
        assert data["display_name"] == "Test User"
        assert data["follower_count"] == 1234
        assert data["video_count"] == 42
        assert data["last_analyzed"] is not None
        assert data["cached_at"] is not None

    def test_returns_404_for_unknown_creator(
        self, client: TestClient, valid_api_key: str
    ) -> None:
        """Returns 404 when creator is not in cache."""
        response = client.get(
            "/v1/creators/tiktok/unknown_user",
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "not_found"

    def test_requires_authentication(self, client: TestClient) -> None:
        """Requires API key authentication."""
        response = client.get("/v1/creators/tiktok/testuser")
        assert response.status_code in [401, 403]

    def test_validates_platform(
        self, client: TestClient, valid_api_key: str
    ) -> None:
        """Validates platform value."""
        response = client.get(
            "/v1/creators/invalid_platform/testuser",
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 422

    def test_validates_username_format(
        self, client: TestClient, valid_api_key: str
    ) -> None:
        """Validates username format."""
        response = client.get(
            "/v1/creators/tiktok/invalid%20username!",
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 422
