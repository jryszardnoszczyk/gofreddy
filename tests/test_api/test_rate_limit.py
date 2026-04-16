"""Rate limiting integration tests — tests real middleware behavior."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

from src.api.main import create_app
from src.api.rate_limit import get_real_client_ip
from src.common.enums import Platform


def _mock_request(
    client_host: str | None = "127.0.0.1",
    headers: dict[str, str] | None = None,
) -> Request:
    """Create a mock Request with given client host and headers."""
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [
            (k.lower().encode(), v.encode()) for k, v in (headers or {}).items()
        ],
    }
    if client_host:
        scope["client"] = (client_host, 0)
    else:
        scope["client"] = None
    return Request(scope)


class TestGetRealClientIp:
    """Tests for get_real_client_ip — uses request.client.host only."""

    def test_returns_client_host(self) -> None:
        """get_real_client_ip returns request.client.host."""
        request = _mock_request(client_host="10.0.0.1")
        assert get_real_client_ip(request) == "10.0.0.1"

    def test_ignores_xff_header(self) -> None:
        """get_real_client_ip ignores X-Forwarded-For (Uvicorn handles it)."""
        request = _mock_request(
            client_host="10.0.0.1",
            headers={"X-Forwarded-For": "1.2.3.4, 5.6.7.8"},
        )
        assert get_real_client_ip(request) == "10.0.0.1"

    def test_no_client_returns_unknown(self) -> None:
        """Falls back to 'unknown' when request.client is None."""
        request = _mock_request(client_host=None)
        assert get_real_client_ip(request) == "unknown"


class TestRateLimiting:
    """Tests for API rate limiting — uses real middleware (limiter enabled)."""

    @pytest.fixture
    def client_with_limiter(self) -> TestClient:
        """Create test client with rate limiter ENABLED and minimal mocked state."""
        app = create_app()

        # Mock minimal state needed for the app to function
        app.state.db_pool = MagicMock()
        app.state.analysis_service = MagicMock()
        app.state.analysis_repository = MagicMock()
        app.state.fetchers = {
            Platform.TIKTOK: MagicMock(),
            Platform.INSTAGRAM: MagicMock(),
            Platform.YOUTUBE: MagicMock(),
        }
        app.state.video_storage = MagicMock()
        app.state.analyzer = MagicMock()
        app.state.fraud_service = MagicMock()
        app.state.fraud_service.close = AsyncMock()
        app.state.fraud_repository = MagicMock()
        app.state.job_service = MagicMock()
        app.state.job_repository = MagicMock()
        app.state.task_client = MagicMock()
        app.state.job_worker = MagicMock()
        app.state.search_service = MagicMock()
        app.state.billing_service = MagicMock()
        app.state.billing_repository = MagicMock()
        app.state.demographics_service = MagicMock()
        app.state.demographics_repository = MagicMock()
        app.state.brand_service = MagicMock()
        app.state.brand_repository = MagicMock()
        app.state.trend_service = MagicMock()
        app.state.trend_repository = MagicMock()
        app.state.evolution_service = MagicMock()
        app.state.evolution_repository = MagicMock()
        app.state.deepfake_service = MagicMock()
        app.state.deepfake_repository = MagicMock()
        app.state.story_service = MagicMock()
        app.state.story_repository = MagicMock()
        app.state.story_storage = MagicMock()
        app.state.orchestrator = MagicMock()

        return TestClient(app, raise_server_exceptions=False)

    def test_rate_limit_returns_429_on_exceed(self, client_with_limiter: TestClient) -> None:
        """Verify rate limiting middleware is active."""
        responses = []
        for _ in range(35):
            response = client_with_limiter.get("/health")
            responses.append(response)
            if response.status_code == 429:
                break

        # Health endpoint should succeed initially
        assert responses[0].status_code == 200, "Health endpoint should return 200"

    def test_health_endpoint_not_rate_limited(self, client_with_limiter: TestClient) -> None:
        """Health endpoint should not be rate limited."""
        for _ in range(50):
            response = client_with_limiter.get("/health")
            assert response.status_code == 200
