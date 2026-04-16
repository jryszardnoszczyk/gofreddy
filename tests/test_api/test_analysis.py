"""Tests for analysis endpoints — router-level HTTP behavior."""

from dataclasses import replace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.jobs.exceptions import JobNotFoundError
from src.jobs.models import JobStatus


@pytest.mark.mock_required
class TestGetAnalysis:
    """Tests for GET /v1/analysis/{id} — mocks required for service responses."""

    def test_returns_analysis_when_found(
        self, client: TestClient, mock_analysis_service, mock_analysis_record, valid_api_key: str
    ) -> None:
        """Returns analysis result when found."""
        mock_analysis_service.get_by_id = AsyncMock(return_value=mock_analysis_record)

        response = client.get(
            f"/v1/analysis/{mock_analysis_record.id}",
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "complete"
        assert data["id"] == str(mock_analysis_record.id)
        assert data["result"]["overall_safe"] is True
        assert isinstance(data["result"]["overall_confidence"], (int, float))
        assert 0.0 <= data["result"]["overall_confidence"] <= 1.0

    def test_returns_typed_risk_items(
        self,
        client: TestClient,
        mock_analysis_service,
        mock_analysis_record,
        valid_api_key: str,
    ) -> None:
        """Returns typed risk payload for analysis retrieval."""
        mock_analysis_service.get_by_id = AsyncMock(
            return_value=replace(
                mock_analysis_record,
                risks_detected=[
                    {
                        "category": "violence",
                        "severity": "high",
                        "confidence": 0.94,
                        "description": "Fight scene detected",
                        "evidence": "Two individuals striking each other",
                    }
                ],
            )
        )

        response = client.get(
            f"/v1/analysis/{mock_analysis_record.id}",
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 200
        data = response.json()
        risk = data["result"]["risks_detected"][0]
        assert risk["risk_type"] == "violence"
        assert risk["category"] == "violence"
        assert risk["severity"] == "high"
        assert isinstance(risk["confidence"], (int, float))
        assert 0.0 <= risk["confidence"] <= 1.0
        assert isinstance(risk["description"], str)
        assert isinstance(risk["evidence"], str)

    def test_returns_404_when_not_found(
        self, client: TestClient, mock_analysis_service, valid_api_key: str
    ) -> None:
        """Returns 404 when analysis is not found."""
        mock_analysis_service.get_by_id = AsyncMock(return_value=None)
        analysis_id = uuid4()

        response = client.get(
            f"/v1/analysis/{analysis_id}",
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "not_found"


class TestGetAnalysisValidation:
    """Tests for GET /v1/analysis/{id} validation — pure HTTP, no service calls."""

    def test_returns_401_without_api_key(self, client: TestClient) -> None:
        """Returns 401 when no API key provided."""
        analysis_id = uuid4()
        response = client.get(f"/v1/analysis/{analysis_id}")
        assert response.status_code in [401, 403]

    def test_returns_401_with_empty_api_key(self, client: TestClient) -> None:
        """Returns 401 when API key is empty."""
        analysis_id = uuid4()
        response = client.get(
            f"/v1/analysis/{analysis_id}",
            headers={"Authorization": "Bearer "},
        )
        assert response.status_code in [401, 403]

    def test_returns_422_with_invalid_uuid(
        self, client: TestClient, valid_api_key: str
    ) -> None:
        """Returns 422 when analysis ID is not a valid UUID."""
        response = client.get(
            "/v1/analysis/not-a-uuid",
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 422


@pytest.mark.mock_required
class TestAnalysisJobs:
    """Tests for async analysis job endpoints."""

    def test_list_jobs_returns_paginated_results(
        self,
        client: TestClient,
        mock_job_service,
        valid_api_key: str,
    ) -> None:
        """GET /v1/analysis/jobs returns jobs and pagination."""
        response = client.get(
            "/v1/analysis/jobs",
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert "pagination" in data
        assert data["pagination"]["limit"] == 20
        assert data["pagination"]["offset"] == 0
        assert data["pagination"]["total"] == 1
        mock_job_service.list_jobs.assert_awaited_once()

    def test_list_jobs_applies_status_limit_and_offset(
        self,
        client: TestClient,
        mock_job_service,
        valid_api_key: str,
    ) -> None:
        """GET /v1/analysis/jobs passes parsed filters to service."""
        response = client.get(
            "/v1/analysis/jobs?status=running&status=failed&limit=10&offset=5",
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 200

        args, kwargs = mock_job_service.list_jobs.await_args
        assert args[1] == [JobStatus.RUNNING, JobStatus.FAILED]
        assert args[2] == 10
        assert args[3] == 5
        assert kwargs == {}

    def test_list_jobs_status_filter_is_case_insensitive(
        self,
        client: TestClient,
        mock_job_service,
        valid_api_key: str,
    ) -> None:
        """GET /v1/analysis/jobs accepts mixed-case status filters."""
        response = client.get(
            "/v1/analysis/jobs?status=RUNNING&status=Failed",
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 200

        args, kwargs = mock_job_service.list_jobs.await_args
        assert args[1] == [JobStatus.RUNNING, JobStatus.FAILED]
        assert kwargs == {}

    def test_list_jobs_invalid_status_returns_400_client_error(
        self,
        client: TestClient,
        valid_api_key: str,
    ) -> None:
        """Invalid status filter returns client error (not 500)."""
        response = client.get(
            "/v1/analysis/jobs?status=definitely-not-a-status",
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "invalid_status_filter"

    def test_list_jobs_requires_auth(self, client: TestClient) -> None:
        """GET /v1/analysis/jobs requires auth."""
        response = client.get("/v1/analysis/jobs")
        assert response.status_code in [401, 403]

    def test_list_jobs_validates_pagination_params(
        self, client: TestClient, valid_api_key: str
    ) -> None:
        """GET /v1/analysis/jobs validates limit/offset constraints."""
        response = client.get(
            "/v1/analysis/jobs?limit=0",
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "validation_error"

        response = client.get(
            "/v1/analysis/jobs?limit=101",
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "validation_error"

        response = client.get(
            "/v1/analysis/jobs?offset=-1",
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "validation_error"

    def test_get_job_status_returns_results(
        self,
        client: TestClient,
        mock_job_service,
        mock_analysis_job,
        valid_api_key: str,
    ) -> None:
        """GET /v1/analysis/jobs/{job_id} returns status and results."""
        mock_job_service.get_video_results = AsyncMock(
            return_value=[
                {
                    "video_index": 0,
                    "platform": "tiktok",
                    "video_id": "123",
                    "status": "complete",
                    "result": {"overall_safe": True},
                    "error": None,
                }
            ]
        )

        response = client.get(
            f"/v1/analysis/jobs/{mock_analysis_job.id}",
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(mock_analysis_job.id)
        assert data["status"] == mock_analysis_job.status.value
        assert isinstance(data["results"], list)

    def test_get_job_status_not_found_returns_404(
        self,
        client: TestClient,
        mock_job_service,
        valid_api_key: str,
    ) -> None:
        """GET /v1/analysis/jobs/{job_id} returns 404 if job missing."""
        job_id = uuid4()
        mock_job_service.get_job_status = AsyncMock(side_effect=JobNotFoundError(job_id))

        response = client.get(
            f"/v1/analysis/jobs/{job_id}",
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "not_found"

    def test_get_job_status_invalid_uuid_returns_422(
        self, client: TestClient, valid_api_key: str
    ) -> None:
        """GET /v1/analysis/jobs/{job_id} validates UUID."""
        response = client.get(
            "/v1/analysis/jobs/not-a-uuid",
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "validation_error"

    def test_cancel_job_returns_payload(
        self,
        client: TestClient,
        mock_job_service,
        mock_analysis_job,
        valid_api_key: str,
    ) -> None:
        """DELETE /v1/analysis/jobs/{job_id} returns cancellation response."""
        completed_video = type(
            "CompletedVideo",
            (),
            {
                "video_index": 0,
                "platform": "tiktok",
                "video_id": "123",
                "result": {"overall_safe": True},
            },
        )
        mock_job_service.get_completed_videos = AsyncMock(return_value=[completed_video])

        response = client.delete(
            f"/v1/analysis/jobs/{mock_analysis_job.id}",
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == str(mock_analysis_job.id)
        assert data["completed_videos"] == 1
        assert len(data["partial_results"]) == 1

    def test_cancel_job_not_found_returns_404(
        self,
        client: TestClient,
        mock_job_service,
        valid_api_key: str,
    ) -> None:
        """DELETE /v1/analysis/jobs/{job_id} returns 404 if missing."""
        job_id = uuid4()
        mock_job_service.cancel_job = AsyncMock(side_effect=JobNotFoundError(job_id))

        response = client.delete(
            f"/v1/analysis/jobs/{job_id}",
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "not_found"
