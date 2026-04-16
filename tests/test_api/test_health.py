"""Tests for health endpoints — router-level HTTP behavior."""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for /health endpoint — pure HTTP, no service deps."""

    def test_health_returns_200(self, client: TestClient) -> None:
        """Health check returns 200 with healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_health_no_auth_required(self, client: TestClient) -> None:
        """Health check does not require authentication."""
        response = client.get("/health")
        assert response.status_code == 200


@pytest.mark.mock_required
class TestReadyEndpoint:
    """Tests for /ready endpoint — mocks required to control DB state."""

    def test_ready_returns_200_when_db_connected(
        self, client: TestClient, mock_db_pool
    ) -> None:
        """Readiness check returns 200 when DB is connected."""
        mock_conn = mock_db_pool.acquire.return_value.__aenter__.return_value
        mock_conn.execute = AsyncMock(return_value=1)

        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["database"] == "connected"
        assert "runtime_modes" in data
        runtime_modes = data["runtime_modes"]
        assert "environment" in runtime_modes
        assert runtime_modes["externals_mode"] in {"real", "fake"}
        assert runtime_modes["task_client_mode"] in {"cloud", "mock"}

    def test_ready_returns_503_when_db_unavailable(
        self, client: TestClient, mock_db_pool
    ) -> None:
        """Readiness check returns 503 when DB is unavailable."""
        mock_db_pool.acquire.return_value.__aenter__ = AsyncMock(
            side_effect=Exception("Connection failed")
        )

        response = client.get("/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "not_ready"
        assert "runtime_modes" in data
        runtime_modes = data["runtime_modes"]
        assert "environment" in runtime_modes
        assert runtime_modes["externals_mode"] in {"real", "fake"}
        assert runtime_modes["task_client_mode"] in {"cloud", "mock"}

    def test_ready_no_auth_required(self, client: TestClient) -> None:
        """Readiness check does not require authentication."""
        response = client.get("/ready")
        assert response.status_code in [200, 503]
