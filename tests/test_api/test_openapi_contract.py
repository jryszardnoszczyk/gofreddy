"""Tests for OpenAPI schema contract segmentation."""

from fastapi.testclient import TestClient


class TestOpenAPIContract:
    """Tests for OpenAPI route filtering."""

    def test_internal_routes_excluded(self, client: TestClient):
        """Internal routes are not in OpenAPI schema."""
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        schema = resp.json()
        paths = schema.get("paths", {})
        internal_paths = [p for p in paths if p.startswith("/internal")]
        assert internal_paths == [], f"Internal routes leaked into OpenAPI: {internal_paths}"

    def test_webhook_routes_excluded(self, client: TestClient):
        """Webhook routes are not in OpenAPI schema."""
        resp = client.get("/openapi.json")
        schema = resp.json()
        paths = schema.get("paths", {})
        webhook_paths = [p for p in paths if p.startswith("/webhooks")]
        assert webhook_paths == [], f"Webhook routes leaked into OpenAPI: {webhook_paths}"

    def test_public_v1_routes_present(self, client: TestClient):
        """Public /v1 routes are still present (catches over-filtering)."""
        resp = client.get("/openapi.json")
        schema = resp.json()
        paths = schema.get("paths", {})
        # At least some v1 routes should be present
        v1_paths = [p for p in paths if p.startswith("/v1/")]
        assert len(v1_paths) > 0, "No /v1/ routes in OpenAPI — over-filtering detected"

    def test_health_routes_present(self, client: TestClient):
        """Health routes are still present."""
        resp = client.get("/openapi.json")
        schema = resp.json()
        paths = schema.get("paths", {})
        assert "/health" in paths or "/ready" in paths, "Health routes missing from OpenAPI"
