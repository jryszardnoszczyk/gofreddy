"""Tests for GET /v1/analysis/{analysis_id}/evidence endpoint."""

from dataclasses import replace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


@pytest.mark.mock_required
class TestGetEvidenceTimeline:
    """Tests for GET /v1/analysis/{id}/evidence — mocks required."""

    def test_happy_path(
        self, client: TestClient, mock_analysis_service, mock_analysis_record, valid_api_key: str
    ) -> None:
        """Returns evidence timeline for a valid analysis."""
        record = replace(
            mock_analysis_record,
            moderation_flags=[
                {
                    "moderation_class": "hate_speech",
                    "severity": "high",
                    "confidence": 0.9,
                    "timestamp_start": "1:00",
                    "timestamp_end": "1:30",
                    "description": "Hate speech detected",
                    "evidence": "Offensive language at 1:00",
                },
            ],
            risks_detected=[
                {
                    "category": "violence",
                    "severity": "medium",
                    "confidence": 0.8,
                    "timestamp_start": "2:00",
                    "timestamp_end": "2:30",
                    "description": "Violence detected",
                    "evidence": "Violent scene at 2:00",
                },
            ],
        )
        mock_analysis_service.get_by_id = AsyncMock(return_value=record)

        # Mock brand service to return None (no brand analysis)
        brand_service = MagicMock()
        brand_service.get_brand_analysis = AsyncMock(return_value=None)
        client.app.state.brand_service = brand_service

        # Mock storage for presigned URL
        storage = MagicMock()
        storage.generate_download_url = AsyncMock(return_value="https://r2.example.com/video.mp4")
        client.app.state.video_storage = storage

        response = client.get(
            f"/v1/analysis/{record.id}/evidence",
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["analysis_id"] == str(record.id)
        assert data["playback_url"] == "https://r2.example.com/video.mp4#t=0"
        assert len(data["timeline"]) == 2  # 1:00 and 2:00
        assert len(data["unanchored_findings"]) == 0
        assert data["excluded_sources"] == ["sponsored_content"]

    def test_not_found(
        self, client: TestClient, mock_analysis_service, valid_api_key: str
    ) -> None:
        """Returns 404 when analysis not found."""
        mock_analysis_service.get_by_id = AsyncMock(return_value=None)

        response = client.get(
            f"/v1/analysis/{uuid4()}/evidence",
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "not_found"

    def test_no_access(
        self, client: TestClient, mock_analysis_service, mock_analysis_record, valid_api_key: str
    ) -> None:
        """Returns 404 when user doesn't have access (IDOR protection)."""
        mock_analysis_service.get_by_id = AsyncMock(return_value=mock_analysis_record)
        # Set user_has_access to False
        client.app.state.analysis_repository.user_has_access = AsyncMock(return_value=False)

        response = client.get(
            f"/v1/analysis/{mock_analysis_record.id}/evidence",
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 404

        # Restore for other tests
        client.app.state.analysis_repository.user_has_access = AsyncMock(return_value=True)

    def test_no_brand_analysis(
        self, client: TestClient, mock_analysis_service, mock_analysis_record, valid_api_key: str
    ) -> None:
        """Returns 200 with empty brand findings when no brand analysis exists."""
        mock_analysis_service.get_by_id = AsyncMock(return_value=mock_analysis_record)

        brand_service = MagicMock()
        brand_service.get_brand_analysis = AsyncMock(return_value=None)
        client.app.state.brand_service = brand_service

        storage = MagicMock()
        storage.generate_download_url = AsyncMock(return_value="https://r2.example.com/video.mp4")
        client.app.state.video_storage = storage

        response = client.get(
            f"/v1/analysis/{mock_analysis_record.id}/evidence",
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 200
        data = response.json()
        # No moderation, no risks, no brands → empty timeline
        assert data["timeline"] == []
        assert data["unanchored_findings"] == []

    def test_storage_error_null_playback_url(
        self, client: TestClient, mock_analysis_service, mock_analysis_record, valid_api_key: str
    ) -> None:
        """Returns 200 with null playback_url when R2 is unavailable."""
        mock_analysis_service.get_by_id = AsyncMock(return_value=mock_analysis_record)

        brand_service = MagicMock()
        brand_service.get_brand_analysis = AsyncMock(return_value=None)
        client.app.state.brand_service = brand_service

        from src.storage.exceptions import StorageError
        storage = MagicMock()
        storage.generate_download_url = AsyncMock(side_effect=StorageError("R2 unavailable"))
        client.app.state.video_storage = storage

        response = client.get(
            f"/v1/analysis/{mock_analysis_record.id}/evidence",
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["playback_url"] is None

    def test_empty_findings(
        self, client: TestClient, mock_analysis_service, mock_analysis_record, valid_api_key: str
    ) -> None:
        """Returns 200 with empty timeline when no findings exist."""
        mock_analysis_service.get_by_id = AsyncMock(return_value=mock_analysis_record)

        brand_service = MagicMock()
        brand_service.get_brand_analysis = AsyncMock(return_value=None)
        client.app.state.brand_service = brand_service

        storage = MagicMock()
        storage.generate_download_url = AsyncMock(return_value="https://r2.example.com/video.mp4")
        client.app.state.video_storage = storage

        response = client.get(
            f"/v1/analysis/{mock_analysis_record.id}/evidence",
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["timeline"] == []
        assert data["unanchored_findings"] == []

    def test_requires_auth(self, client: TestClient) -> None:
        """Returns 401 without auth token."""
        response = client.get(f"/v1/analysis/{uuid4()}/evidence")
        assert response.status_code == 401
