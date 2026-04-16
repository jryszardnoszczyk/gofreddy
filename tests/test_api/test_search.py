"""Tests for the search API endpoint — router-level HTTP behavior."""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.search.exceptions import QueryParseError, SearchError


@pytest.mark.mock_required
class TestSearchEndpoint:
    """Tests for POST /v1/search — mocks required for service responses."""

    def test_search_valid_query(self, client: TestClient, valid_api_key: str) -> None:
        """Search with valid query returns results."""
        response = client.post(
            "/v1/search",
            headers={"Authorization": f"Bearer {valid_api_key}"},
            json={"query": "fitness videos"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "interpretation" in data
        assert "confidence" in data
        assert data["total"] >= 0

    def test_search_with_platforms(self, client: TestClient, valid_api_key: str) -> None:
        """Search with specific platforms."""
        response = client.post(
            "/v1/search",
            headers={"Authorization": f"Bearer {valid_api_key}"},
            json={"query": "fitness", "platforms": ["tiktok", "instagram"]},
        )

        assert response.status_code == 200

    def test_search_with_limit(self, client: TestClient, valid_api_key: str) -> None:
        """Search with custom limit."""
        response = client.post(
            "/v1/search",
            headers={"Authorization": f"Bearer {valid_api_key}"},
            json={"query": "fitness", "limit": 10},
        )

        assert response.status_code == 200

    def test_search_with_structured_query(
        self, client: TestClient, valid_api_key: str
    ) -> None:
        """Search with structured query (agent-native bypass)."""
        response = client.post(
            "/v1/search",
            headers={"Authorization": f"Bearer {valid_api_key}"},
            json={
                "query": "ignored",
                "structured_query": {
                    "scope": "videos",
                    "platforms": ["tiktok"],
                    "search_type": "keyword",
                    "filters": {"query": "fitness"},
                    "confidence": 1.0,
                    "confidence_level": "high",
                },
            },
        )

        assert response.status_code == 200

    def test_search_parse_error_returns_400(
        self,
        client: TestClient,
        valid_api_key: str,
        mock_search_service,
    ) -> None:
        """Search returns 400 on parse error."""
        mock_search_service.search = AsyncMock(
            side_effect=QueryParseError("Failed to parse", "bad query")
        )

        response = client.post(
            "/v1/search",
            headers={"Authorization": f"Bearer {valid_api_key}"},
            json={"query": "bad query"},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "parse_error"

    def test_search_error_returns_500(
        self,
        client: TestClient,
        valid_api_key: str,
        mock_search_service,
    ) -> None:
        """Search returns 500 on search error."""
        mock_search_service.search = AsyncMock(
            side_effect=SearchError("Search failed")
        )

        response = client.post(
            "/v1/search",
            headers={"Authorization": f"Bearer {valid_api_key}"},
            json={"query": "test"},
        )

        assert response.status_code == 500
        data = response.json()
        assert data["error"]["code"] == "search_error"

    def test_search_response_structure(
        self, client: TestClient, valid_api_key: str
    ) -> None:
        """Search response has correct structure."""
        response = client.post(
            "/v1/search",
            headers={"Authorization": f"Bearer {valid_api_key}"},
            json={"query": "fitness"},
        )

        assert response.status_code == 200
        data = response.json()

        # Required fields
        assert "interpretation" in data
        assert "confidence" in data
        assert "results" in data
        assert "total" in data
        assert "platforms_searched" in data
        assert "platforms_failed" in data
        assert "errors" in data

        # Result structure
        if data["results"]:
            result = data["results"][0]
            assert "platform" in result
            assert "creator_handle" in result


class TestSearchValidation:
    """Tests for POST /v1/search validation — pure HTTP, no service calls."""

    def test_search_requires_auth(self, client: TestClient) -> None:
        """Search requires authentication."""
        response = client.post("/v1/search", json={"query": "fitness"})
        assert response.status_code == 401

    def test_search_validates_query_length(
        self, client: TestClient, valid_api_key: str
    ) -> None:
        """Search validates query length."""
        # Empty query
        response = client.post(
            "/v1/search",
            headers={"Authorization": f"Bearer {valid_api_key}"},
            json={"query": ""},
        )
        assert response.status_code == 422

        # Query too long
        long_query = "a" * 501
        response = client.post(
            "/v1/search",
            headers={"Authorization": f"Bearer {valid_api_key}"},
            json={"query": long_query},
        )
        assert response.status_code == 422

    def test_search_validates_limit(
        self, client: TestClient, valid_api_key: str
    ) -> None:
        """Search validates limit bounds."""
        # Limit too low
        response = client.post(
            "/v1/search",
            headers={"Authorization": f"Bearer {valid_api_key}"},
            json={"query": "fitness", "limit": 0},
        )
        assert response.status_code == 422

        # Limit too high
        response = client.post(
            "/v1/search",
            headers={"Authorization": f"Bearer {valid_api_key}"},
            json={"query": "fitness", "limit": 501},
        )
        assert response.status_code == 422
