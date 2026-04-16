"""Tests for X-Request-ID trace middleware."""

import re

from fastapi.testclient import TestClient


class TestRequestIDMiddleware:
    """Tests for the RequestIDMiddleware."""

    def test_response_includes_request_id(self, client: TestClient):
        """Response includes X-Request-ID header."""
        resp = client.get("/health")
        assert "X-Request-ID" in resp.headers
        # Should be a valid UUID
        req_id = resp.headers["X-Request-ID"]
        assert re.match(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            req_id,
        )

    def test_client_request_id_echoed(self, client: TestClient):
        """Client-provided X-Request-ID is echoed back."""
        custom_id = "my-custom-trace-id-123"
        resp = client.get("/health", headers={"X-Request-ID": custom_id})
        assert resp.headers["X-Request-ID"] == custom_id

    def test_request_id_on_error(self, client: TestClient):
        """X-Request-ID present on 404 responses."""
        resp = client.get("/v1/analysis/00000000-0000-0000-0000-000000000000",
                          headers={"Authorization": "Bearer test-token"})
        assert "X-Request-ID" in resp.headers

    def test_different_requests_get_different_ids(self, client: TestClient):
        """Each request gets a unique ID when none provided."""
        resp1 = client.get("/health")
        resp2 = client.get("/health")
        assert resp1.headers["X-Request-ID"] != resp2.headers["X-Request-ID"]
