"""Tests for GET /v1/analysis/{analysis_id}/evaluate endpoint."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.analysis.models import VideoAnalysisRecord
from src.policies.models import BrandPolicyResponse, PolicyRule
from src.policies.service import PolicyNotFoundError, PolicyService
from src.schemas import ModerationClass, Severity


TEST_USER_ID = uuid4()
TEST_ANALYSIS_ID = uuid4()
TEST_POLICY_ID = uuid4()


def _make_analysis_record(**overrides):
    defaults = {
        "id": TEST_ANALYSIS_ID,
        "video_id": uuid4(),
        "cache_key": "tiktok:123456:v1",
        "overall_safe": True,
        "overall_confidence": 0.95,
        "risks_detected": [],
        "summary": "Test summary",
        "content_categories": [],
        "moderation_flags": [
            {
                "moderation_class": "hate_speech",
                "severity": "high",
                "confidence": 0.9,
                "timestamp_start": None,
                "timestamp_end": None,
                "description": "Hate speech",
                "evidence": "Offensive language",
            }
        ],
        "sponsored_content": None,
        "processing_time_seconds": 1.5,
        "token_count": 1000,
        "error": None,
        "model_version": "1",
        "analyzed_at": datetime.now(UTC),
        "analysis_cost_usd": 0.001,
    }
    defaults.update(overrides)
    return VideoAnalysisRecord(**defaults)


def _make_policy_response(**kwargs) -> BrandPolicyResponse:
    now = datetime.now(UTC)
    defaults = {
        "id": TEST_POLICY_ID,
        "user_id": TEST_USER_ID,
        "policy_name": "Test Policy",
        "rules": [PolicyRule(
            moderation_class=ModerationClass.HATE_SPEECH,
            max_severity=Severity.NONE,
            action="block",
        )],
        "is_preset": False,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(kwargs)
    return BrandPolicyResponse(**defaults)


@pytest.fixture
def mock_analysis_repo():
    repo = MagicMock()
    repo.get_by_id = AsyncMock(return_value=_make_analysis_record())
    repo.user_has_access = AsyncMock(return_value=True)
    return repo


@pytest.fixture
def mock_policy_service():
    service = AsyncMock(spec=PolicyService)
    service.get_policy.return_value = _make_policy_response()
    return service


@pytest.fixture
def app(mock_analysis_repo, mock_policy_service):
    """Create a test FastAPI app with the analysis router."""
    from src.api.routers.analysis import router
    from src.api.rate_limit import limiter
    from src.api.exceptions import register_exception_handlers

    test_app = FastAPI()
    test_app.state.limiter = limiter
    test_app.state.analysis_repository = mock_analysis_repo
    register_exception_handlers(test_app)

    async def override_user_id():
        return TEST_USER_ID

    async def override_analysis_service():
        return MagicMock()

    async def override_policy_service():
        return mock_policy_service

    from src.api.dependencies import get_current_user_id, get_analysis_service, get_policy_service

    test_app.dependency_overrides[get_current_user_id] = override_user_id
    test_app.dependency_overrides[get_analysis_service] = override_analysis_service
    test_app.dependency_overrides[get_policy_service] = override_policy_service

    test_app.include_router(router, prefix="/v1")
    return test_app


@pytest.fixture
def client(app):
    return TestClient(app)


class TestEvaluateHappyPath:
    def test_returns_evaluation_response(self, client, mock_analysis_repo, mock_policy_service):
        """Returns EvaluationResponse with all fields."""
        resp = client.get(
            f"/v1/analysis/{TEST_ANALYSIS_ID}/evaluate",
            params={"policy_id": str(TEST_POLICY_ID)},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["analysis_id"] == str(TEST_ANALYSIS_ID)
        assert data["policy_id"] == str(TEST_POLICY_ID)
        assert data["policy_name"] == "Test Policy"
        assert data["overall_verdict"] == "block"
        assert len(data["rules"]) == 1
        assert data["rules"][0]["passed"] is False
        assert data["disclaimer"]
        assert "evaluated_at" in data


class TestMissingPolicyIdParam:
    def test_missing_policy_id_422(self, client):
        """422 validation error when policy_id query param missing."""
        resp = client.get(f"/v1/analysis/{TEST_ANALYSIS_ID}/evaluate")
        assert resp.status_code == 422


class TestAnalysisNotFound:
    def test_analysis_not_found_404(self, client, mock_analysis_repo):
        """404 when analysis_id doesn't exist."""
        mock_analysis_repo.get_by_id = AsyncMock(return_value=None)
        resp = client.get(
            f"/v1/analysis/{uuid4()}/evaluate",
            params={"policy_id": str(TEST_POLICY_ID)},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "not_found"


class TestPolicyNotFound:
    def test_policy_not_found_404(self, client, mock_policy_service):
        """404 when policy_id doesn't exist or user can't access."""
        mock_policy_service.get_policy.side_effect = PolicyNotFoundError()
        resp = client.get(
            f"/v1/analysis/{TEST_ANALYSIS_ID}/evaluate",
            params={"policy_id": str(uuid4())},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "policy_not_found"


class TestNoAnalysisAccess:
    def test_no_access_404(self, client, mock_analysis_repo):
        """404 when user doesn't have access to analysis."""
        mock_analysis_repo.user_has_access = AsyncMock(return_value=False)
        resp = client.get(
            f"/v1/analysis/{TEST_ANALYSIS_ID}/evaluate",
            params={"policy_id": str(TEST_POLICY_ID)},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "not_found"


class TestErroredAnalysis:
    def test_errored_analysis_422(self, client, mock_analysis_repo):
        """422 with code 'analysis_errored'."""
        mock_analysis_repo.get_by_id = AsyncMock(
            return_value=_make_analysis_record(error="gemini_timeout")
        )
        resp = client.get(
            f"/v1/analysis/{TEST_ANALYSIS_ID}/evaluate",
            params={"policy_id": str(TEST_POLICY_ID)},
        )
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "analysis_errored"


class TestIncompleteAnalysis:
    def test_incomplete_analysis_422(self, client, mock_analysis_repo):
        """422 with code 'analysis_not_complete' when analyzed_at is None."""
        mock_analysis_repo.get_by_id = AsyncMock(
            return_value=_make_analysis_record(analyzed_at=None)
        )
        resp = client.get(
            f"/v1/analysis/{TEST_ANALYSIS_ID}/evaluate",
            params={"policy_id": str(TEST_POLICY_ID)},
        )
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "analysis_not_complete"


class TestPresetPolicyAllowed:
    def test_preset_policy_usable(self, client, mock_policy_service):
        """Preset policy (user_id=NULL) usable by any authenticated user."""
        preset = _make_policy_response(user_id=None, is_preset=True, policy_name="Family Safe")
        mock_policy_service.get_policy.return_value = preset
        resp = client.get(
            f"/v1/analysis/{TEST_ANALYSIS_ID}/evaluate",
            params={"policy_id": str(TEST_POLICY_ID)},
        )
        assert resp.status_code == 200
        assert resp.json()["policy_name"] == "Family Safe"
