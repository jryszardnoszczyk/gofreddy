"""Tests for video analysis endpoints — router-level HTTP behavior."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import NAMESPACE_URL, uuid4, uuid5

import pytest
from fastapi.testclient import TestClient

from src.analysis.service import AnalysisResult
from src.billing.exceptions import UserNotFound, UsageLimitExceeded
from src.billing.service import BillingService
from src.api.routers.videos import parse_video_url
from src.common.enums import Platform
from src.jobs.exceptions import JobLimitExceeded
from src.jobs.models import JobStatus
from src.jobs.service import JobSubmission
from src.schemas import RiskCategory, RiskDetection, Severity, VideoAnalysis


class TestParseVideoUrl:
    """Tests for URL parsing — pure logic, no mocks needed."""

    def test_parses_tiktok_url(self) -> None:
        """Parses TikTok video URL correctly."""
        url = "https://www.tiktok.com/@user/video/1234567890123456789"
        platform, video_id = parse_video_url(url)
        assert platform == Platform.TIKTOK
        assert video_id == "1234567890123456789"

    def test_parses_tiktok_vm_url(self) -> None:
        """Parses short TikTok URL correctly."""
        url = "https://vm.tiktok.com/@user/video/1234567890123456789"
        platform, video_id = parse_video_url(url)
        assert platform == Platform.TIKTOK
        assert video_id == "1234567890123456789"

    def test_parses_instagram_reel_url(self) -> None:
        """Parses Instagram reel URL correctly."""
        url = "https://www.instagram.com/reel/ABC123_456/"
        platform, video_id = parse_video_url(url)
        assert platform == Platform.INSTAGRAM
        assert video_id == "ABC123_456"

    def test_parses_instagram_post_url(self) -> None:
        """Parses Instagram post URL correctly."""
        url = "https://www.instagram.com/p/ABC123_456/"
        platform, video_id = parse_video_url(url)
        assert platform == Platform.INSTAGRAM
        assert video_id == "ABC123_456"

    def test_parses_youtube_watch_url(self) -> None:
        """Parses YouTube watch URL correctly."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        platform, video_id = parse_video_url(url)
        assert platform == Platform.YOUTUBE
        assert video_id == "dQw4w9WgXcQ"

    def test_parses_youtube_short_url(self) -> None:
        """Parses YouTube short URL correctly."""
        url = "https://youtu.be/dQw4w9WgXcQ"
        platform, video_id = parse_video_url(url)
        assert platform == Platform.YOUTUBE
        assert video_id == "dQw4w9WgXcQ"

    def test_rejects_blocked_domain(self) -> None:
        """Rejects URLs from blocked domains."""
        url = "https://evil.com/video/123"
        with pytest.raises(ValueError, match="Unsupported or blocked domain"):
            parse_video_url(url)

    def test_rejects_invalid_tiktok_url(self) -> None:
        """Rejects invalid TikTok URL format."""
        url = "https://www.tiktok.com/@user/profile"
        with pytest.raises(ValueError, match="Invalid TikTok URL"):
            parse_video_url(url)

    def test_rejects_invalid_instagram_url(self) -> None:
        """Rejects invalid Instagram URL format."""
        url = "https://www.instagram.com/user/profile"
        with pytest.raises(ValueError, match="Invalid Instagram URL"):
            parse_video_url(url)


@pytest.mark.mock_required
class TestAnalyzeVideos:
    """Tests for POST /v1/analyze/videos — mocks required for service responses."""

    def test_analyzes_single_video(
        self,
        client: TestClient,
        mock_analysis_service,
        valid_api_key: str,
    ) -> None:
        """Analyzes a single video successfully."""
        mock_analysis_service.analyze = AsyncMock(
            return_value=AnalysisResult(
                analysis=VideoAnalysis(
                    video_id="1234567890123456789",
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
            "/v1/analyze/videos",
            json={"urls": ["https://www.tiktok.com/@user/video/1234567890123456789"]},
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1
        assert data["success_rate"] == 1.0
        assert data["results"][0]["overall_safe"] is True
        assert isinstance(data["results"][0]["overall_confidence"], (int, float))
        assert 0.0 <= data["results"][0]["overall_confidence"] <= 1.0

    def test_returns_typed_risk_items(
        self,
        client: TestClient,
        mock_analysis_service,
        valid_api_key: str,
    ) -> None:
        """Ensures risk payloads follow the tightened typed contract."""
        mock_analysis_service.analyze = AsyncMock(
            return_value=AnalysisResult(
                analysis=VideoAnalysis(
                    video_id="1234567890123456789",
                    overall_safe=False,
                    overall_confidence=0.91,
                    risks_detected=[
                        RiskDetection(
                            category=RiskCategory.VIOLENCE,
                            severity=Severity.HIGH,
                            confidence=0.93,
                            description="Physical altercation detected",
                            evidence="Two people visibly fighting on screen",
                        )
                    ],
                    summary="High-severity violence detected",
                ),
                cached=False,
                cost_usd=0.001,
                record_id=uuid4(),
            )
        )

        response = client.post(
            "/v1/analyze/videos",
            json={"urls": ["https://www.tiktok.com/@user/video/1234567890123456789"]},
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 200
        data = response.json()
        risk = data["results"][0]["risks_detected"][0]
        assert risk["risk_type"] == RiskCategory.VIOLENCE.value
        assert risk["category"] == RiskCategory.VIOLENCE.value
        assert risk["severity"] == Severity.HIGH.value
        assert isinstance(risk["confidence"], (int, float))
        assert 0.0 <= risk["confidence"] <= 1.0
        assert isinstance(risk["description"], str)
        assert isinstance(risk["evidence"], str)

    def test_handles_partial_failure(
        self,
        client: TestClient,
        mock_analysis_service,
        valid_api_key: str,
    ) -> None:
        """Handles partial failures gracefully."""
        mock_analysis_service.analyze = AsyncMock(
            side_effect=[
                AnalysisResult(
                    analysis=VideoAnalysis(
                        video_id="1234567890123456789",
                        overall_safe=True,
                        overall_confidence=0.95,
                        risks_detected=[],
                        summary="No risks",
                    ),
                    cached=False,
                    cost_usd=0.001,
                    record_id=uuid4(),
                ),
                Exception("Analysis failed"),
            ]
        )

        response = client.post(
            "/v1/analyze/videos",
            json={
                "urls": [
                    "https://www.tiktok.com/@user/video/1234567890123456789",
                    "https://www.tiktok.com/@user/video/9876543210123456789",
                ]
            },
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1
        assert len(data["errors"]) == 1
        assert data["success_rate"] == 0.5

    def test_returns_402_when_usage_limit_exceeded(
        self,
        client: TestClient,
        valid_api_key: str,
    ) -> None:
        """Sync endpoint enforces billing usage limits."""
        client.app.state.billing_service.check_can_analyze = AsyncMock(
            side_effect=UsageLimitExceeded("Free tier limit reached")
        )

        response = client.post(
            "/v1/analyze/videos",
            json={"urls": ["https://www.tiktok.com/@user/video/1234567890123456789"]},
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )

        assert response.status_code == 402
        assert response.json()["error"]["code"] == "usage_limit_exceeded"


class TestAnalyzeVideosValidation:
    """Tests for POST /v1/analyze/videos validation — pure HTTP."""

    def test_rejects_empty_urls(
        self, client: TestClient, valid_api_key: str
    ) -> None:
        """Rejects request with empty URLs list."""
        response = client.post(
            "/v1/analyze/videos",
            json={"urls": []},
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 422

    def test_rejects_too_many_urls(
        self, client: TestClient, valid_api_key: str
    ) -> None:
        """Rejects request with too many URLs."""
        urls = [f"https://www.tiktok.com/@user/video/{i:019d}" for i in range(51)]
        response = client.post(
            "/v1/analyze/videos",
            json={"urls": urls},
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 422

    def test_requires_authentication(self, client: TestClient) -> None:
        """Requires API key authentication."""
        response = client.post(
            "/v1/analyze/videos",
            json={"urls": ["https://www.tiktok.com/@user/video/1234567890123456789"]},
        )
        assert response.status_code in [401, 403]

    def test_validates_url_format(
        self, client: TestClient, valid_api_key: str
    ) -> None:
        """Validates URL format."""
        response = client.post(
            "/v1/analyze/videos",
            json={"urls": ["not-a-url"]},
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 422


@pytest.mark.mock_required
class TestAnalyzeVideosAsync:
    """Tests for POST /v1/analyze/videos/async."""

    def test_submits_job_and_returns_202(
        self, client: TestClient, mock_job_service, valid_api_key: str
    ) -> None:
        """Async endpoint returns job metadata on success."""
        job_id = uuid4()
        mock_job_service.submit_job = AsyncMock(
            return_value=JobSubmission(job_id=job_id, status=JobStatus.PENDING)
        )

        response = client.post(
            "/v1/analyze/videos/async",
            json={"urls": ["https://www.tiktok.com/@user/video/1234567890123456789"]},
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 202
        data = response.json()
        assert data["job_id"] == str(job_id)
        assert data["status"] == "pending"
        assert data["message"] == "Analysis job queued"

    def test_requires_authentication(self, client: TestClient) -> None:
        """Async endpoint enforces authentication."""
        response = client.post(
            "/v1/analyze/videos/async",
            json={"urls": ["https://www.tiktok.com/@user/video/1234567890123456789"]},
        )
        assert response.status_code in [401, 403]

    def test_rejects_invalid_request_body(
        self, client: TestClient, valid_api_key: str
    ) -> None:
        """Async endpoint validates URL shape in payload."""
        response = client.post(
            "/v1/analyze/videos/async",
            json={"urls": ["not-a-url"]},
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "validation_error"

    def test_submits_deterministic_video_uuid(
        self, client: TestClient, mock_job_service, valid_api_key: str
    ) -> None:
        """Async endpoint submits deterministic UUIDs derived from platform/video_id."""
        response = client.post(
            "/v1/analyze/videos/async",
            json={"urls": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"]},
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 202

        args, kwargs = mock_job_service.submit_job.await_args
        assert args == ()
        submitted = kwargs["videos"]
        assert len(submitted) == 1
        assert submitted[0].platform == "youtube"
        assert submitted[0].video_id == "dQw4w9WgXcQ"
        assert submitted[0].video_uuid == uuid5(
            NAMESPACE_URL, "youtube:dQw4w9WgXcQ"
        )

    def test_returns_429_when_job_limit_exceeded(
        self, client: TestClient, mock_job_service, valid_api_key: str
    ) -> None:
        """Async endpoint maps JobLimitExceeded to 429 envelope."""
        mock_job_service.submit_job = AsyncMock(
            side_effect=JobLimitExceeded("Maximum concurrent jobs exceeded")
        )

        response = client.post(
            "/v1/analyze/videos/async",
            json={"urls": ["https://www.tiktok.com/@user/video/1234567890123456789"]},
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 429
        data = response.json()
        assert data["error"]["code"] == "job_limit_exceeded"

    def test_returns_402_when_usage_limit_exceeded(
        self, client: TestClient, mock_job_service, valid_api_key: str
    ) -> None:
        """Async endpoint enforces billing usage limits before enqueueing."""
        client.app.state.billing_service.check_can_analyze = AsyncMock(
            side_effect=UsageLimitExceeded("Free tier limit reached")
        )

        response = client.post(
            "/v1/analyze/videos/async",
            json={"urls": ["https://www.tiktok.com/@user/video/1234567890123456789"]},
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )

        assert response.status_code == 402
        assert response.json()["error"]["code"] == "usage_limit_exceeded"
        mock_job_service.submit_job.assert_not_awaited()


@pytest.mark.mock_required
class TestAnalyzeVideosAsyncAuth:
    """Auth behavior for POST /v1/analyze/videos/async."""

    def test_user_not_found_returns_401(
        self, client: TestClient, valid_api_key: str
    ) -> None:
        billing_service = BillingService(MagicMock())
        billing_service.get_billing_context_for_user = AsyncMock(
            side_effect=UserNotFound("user not found")
        )
        client.app.state.billing_service = billing_service
        client.app.state.job_service.submit_job = AsyncMock()

        response = client.post(
            "/v1/analyze/videos/async",
            json={"urls": ["https://www.tiktok.com/@user/video/1234567890123456789"]},
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )

        assert response.status_code == 401
        assert response.json()["error"]["code"] == "user_not_found"
        client.app.state.job_service.submit_job.assert_not_called()

    def test_billing_service_failure_returns_503(
        self, client: TestClient, valid_api_key: str
    ) -> None:
        billing_service = BillingService(MagicMock())
        billing_service.get_billing_context_for_user = AsyncMock(
            side_effect=RuntimeError("db unavailable")
        )
        client.app.state.billing_service = billing_service
        client.app.state.job_service.submit_job = AsyncMock(
            return_value=SimpleNamespace(job_id=uuid4(), status=JobStatus.PENDING)
        )

        response = client.post(
            "/v1/analyze/videos/async",
            json={"urls": ["https://www.tiktok.com/@user/video/1234567890123456789"]},
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )

        assert response.status_code == 503
        body = response.json()
        assert body["error"]["code"] == "billing_unavailable"
        assert body["error"]["message"] == "Billing service unavailable"
        client.app.state.job_service.submit_job.assert_not_called()


@pytest.mark.mock_required
class TestAsyncURLValidation:
    """Tests for WS-04.4: pre-submit URL validation returning 400."""

    def test_rejects_mixed_invalid_urls_with_400(
        self, client: TestClient, valid_api_key: str
    ) -> None:
        """Batch with some invalid URLs returns 400 with details."""
        response = client.post(
            "/v1/analyze/videos/async",
            json={"urls": [
                "https://www.tiktok.com/@user/video/1234567890123456789",
                "https://evil.com/bad",
            ]},
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "invalid_urls"
        assert "evil.com" in str(data["error"]["invalid_urls"])

    def test_rejects_all_invalid_urls_with_count(
        self, client: TestClient, valid_api_key: str
    ) -> None:
        """All-invalid batch returns 400 with count."""
        response = client.post(
            "/v1/analyze/videos/async",
            json={"urls": ["https://bad1.com/x", "https://bad2.com/y"]},
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "invalid_urls"
        assert "2 invalid" in data["error"]["message"]

    def test_valid_urls_pass_validation(
        self, client: TestClient, mock_job_service, valid_api_key: str
    ) -> None:
        """Valid URLs pass validation and submit job."""
        mock_job_service.submit_job = AsyncMock(
            return_value=JobSubmission(job_id=uuid4(), status=JobStatus.PENDING)
        )

        response = client.post(
            "/v1/analyze/videos/async",
            json={"urls": ["https://www.tiktok.com/@user/video/1234567890123456789"]},
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 202
