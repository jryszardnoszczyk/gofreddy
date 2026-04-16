"""Tests for discover router — unified search endpoints."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.conversations.exceptions import ConversationNotFoundError
from src.monitoring.exceptions import MonitorLimitExceededError
from src.monitoring.models import DataSource, DiscoverResult, DiscoverSourceError, RawMention


def _make_raw_mention(**overrides):
    defaults = dict(
        source=DataSource.TWITTER,
        source_id="tweet_123",
        author_handle="@user",
        content="test mention content",
        published_at=datetime.now(timezone.utc),
        sentiment_score=0.5,
    )
    defaults.update(overrides)
    return RawMention(**defaults)


@pytest.mark.mock_required
class TestDiscoverMentions:
    def test_discover_mentions_success(self, client):
        result = DiscoverResult(
            mentions=[_make_raw_mention()],
            sources_searched=["twitter"],
            sources_failed=[],
            sources_unavailable=[],
        )
        with patch(
            "src.monitoring.discovery.discover_mentions",
            new_callable=AsyncMock,
            return_value=result,
        ):
            resp = client.post(
                "/v1/discover/mentions",
                json={"query": "test brand"},
                headers={"Authorization": "Bearer test"},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["result_count"] == 1
        assert "twitter" in body["sources_searched"]

    def test_discover_mentions_with_sources(self, client):
        result = DiscoverResult(
            mentions=[],
            sources_searched=["twitter", "reddit"],
            sources_failed=[],
            sources_unavailable=[],
        )
        with patch(
            "src.monitoring.discovery.discover_mentions",
            new_callable=AsyncMock,
            return_value=result,
        ):
            resp = client.post(
                "/v1/discover/mentions",
                json={"query": "brand", "sources": ["twitter", "reddit"]},
                headers={"Authorization": "Bearer test"},
            )
        assert resp.status_code == 200

    def test_discover_mentions_too_many_sources(self, client):
        # Pro tier allows 7 max, but we send 8
        sources = ["twitter", "reddit", "instagram", "bluesky",
                    "facebook", "linkedin", "tiktok", "newsdata"]
        resp = client.post(
            "/v1/discover/mentions",
            json={"query": "brand", "sources": sources},
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "too_many_sources"

    def test_discover_mentions_daily_limit(self, client):
        client.app.state.monitoring_service.check_discover_quota = AsyncMock(
            side_effect=MonitorLimitExceededError("limit reached")
        )
        resp = client.post(
            "/v1/discover/mentions",
            json={"query": "brand"},
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code == 429
        assert resp.json()["error"]["code"] == "daily_limit_reached"

    def test_discover_mentions_with_failed_sources(self, client):
        result = DiscoverResult(
            mentions=[],
            sources_searched=["twitter"],
            sources_failed=[DiscoverSourceError(source="reddit", reason="timeout")],
            sources_unavailable=["facebook"],
        )
        with patch(
            "src.monitoring.discovery.discover_mentions",
            new_callable=AsyncMock,
            return_value=result,
        ):
            resp = client.post(
                "/v1/discover/mentions",
                json={"query": "brand", "sources": ["twitter", "reddit"]},
                headers={"Authorization": "Bearer test"},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["sources_failed"]) == 1
        assert body["sources_failed"][0]["reason"] == "timeout"
        assert "facebook" in body["sources_unavailable"]


@pytest.mark.mock_required
class TestDiscoverCreators:
    def test_creators_success(self, client):
        mock_ic = MagicMock()
        mock_ic.discover = AsyncMock(return_value={
            "accounts": [
                {
                    "profile": {
                        "username": "creator1",
                        "full_name": "Creator One",
                        "followers": 50000,
                        "engagement_percent": 3.5,
                        "is_verified": True,
                    }
                }
            ]
        })
        client.app.state.ic_backend = mock_ic

        resp = client.post(
            "/v1/discover/creators",
            json={"query": "fitness", "platform": "instagram"},
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_count"] == 1

    def test_creators_unavailable(self, client):
        client.app.state.ic_backend = None

        resp = client.post(
            "/v1/discover/creators",
            json={"query": "fitness", "platform": "instagram"},
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code == 503
        assert resp.json()["error"]["code"] == "service_unavailable"


@pytest.mark.mock_required
class TestDiscoverVideos:
    def test_videos_success(self, client):
        mock_search = MagicMock()
        mock_search.search = AsyncMock(return_value={"results": [], "total": 0})
        client.app.state.search_service = mock_search

        resp = client.post(
            "/v1/discover/videos",
            json={"query": "brand safety"},
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code == 200

    def test_videos_unavailable(self, client):
        client.app.state.search_service = None

        resp = client.post(
            "/v1/discover/videos",
            json={"query": "brand safety"},
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code == 503


@pytest.mark.mock_required
class TestDiscoverSources:
    def test_sources_returns_metadata(self, client):
        resp = client.get("/v1/discover/sources", headers={"Authorization": "Bearer test"})
        assert resp.status_code == 200
        sources = resp.json()
        assert isinstance(sources, list)
        assert len(sources) > 0
        # Check structure of first source
        first = sources[0]
        assert "source_id" in first
        assert "display_name" in first
        assert "category" in first
        assert "available" in first


@pytest.mark.mock_required
class TestDiscoverConversationOwnership:
    """IDOR prevention: workspace writes must verify conversation ownership."""

    def _make_conv_service_reject(self, client, conversation_id):
        """Configure conversation_service.get_conversation to raise NotFoundError."""
        client.app.state.conversation_service.get_conversation = AsyncMock(
            side_effect=ConversationNotFoundError(conversation_id)
        )

    def _make_conv_service_accept(self, client):
        """Configure conversation_service.get_conversation to succeed."""
        client.app.state.conversation_service.get_conversation = AsyncMock(
            return_value=MagicMock()
        )

    # ── /mentions IDOR tests ────────────────────────────────────

    def test_mentions_rejects_foreign_conversation(self, client):
        foreign_conv_id = uuid4()
        self._make_conv_service_reject(client, foreign_conv_id)

        with patch(
            "src.api.routers.discover.discover_mentions",
            new_callable=AsyncMock,
            return_value=DiscoverResult(
                mentions=[], sources_searched=["twitter"],
                sources_failed=[], sources_unavailable=[],
            ),
        ):
            resp = client.post(
                "/v1/discover/mentions",
                json={"query": "brand", "conversation_id": str(foreign_conv_id)},
                headers={"Authorization": "Bearer test"},
            )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "conversation_not_found"
        client.app.state.workspace_service.store_tool_result.assert_not_called()

    def test_mentions_allows_own_conversation(self, client):
        own_conv_id = uuid4()
        self._make_conv_service_accept(client)

        with patch(
            "src.api.routers.discover.discover_mentions",
            new_callable=AsyncMock,
            return_value=DiscoverResult(
                mentions=[], sources_searched=["twitter"],
                sources_failed=[], sources_unavailable=[],
            ),
        ):
            resp = client.post(
                "/v1/discover/mentions",
                json={"query": "brand", "conversation_id": str(own_conv_id)},
                headers={"Authorization": "Bearer test"},
            )
        assert resp.status_code == 200
        assert resp.json()["workspace_updated"] is True
        client.app.state.workspace_service.store_tool_result.assert_called_once()

    def test_mentions_no_workspace_write_without_conversation_id(self, client):
        with patch(
            "src.api.routers.discover.discover_mentions",
            new_callable=AsyncMock,
            return_value=DiscoverResult(
                mentions=[], sources_searched=["twitter"],
                sources_failed=[], sources_unavailable=[],
            ),
        ):
            resp = client.post(
                "/v1/discover/mentions",
                json={"query": "brand"},
                headers={"Authorization": "Bearer test"},
            )
        assert resp.status_code == 200
        assert resp.json()["workspace_updated"] is False
        client.app.state.workspace_service.store_tool_result.assert_not_called()

    # ── /creators IDOR tests ────────────────────────────────────

    def test_creators_rejects_foreign_conversation(self, client):
        foreign_conv_id = uuid4()
        self._make_conv_service_reject(client, foreign_conv_id)

        mock_ic = MagicMock()
        mock_ic.discover = AsyncMock(return_value={"accounts": []})
        client.app.state.ic_backend = mock_ic

        resp = client.post(
            "/v1/discover/creators",
            json={"query": "fitness", "platform": "instagram",
                  "conversation_id": str(foreign_conv_id)},
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "conversation_not_found"
        client.app.state.workspace_service.store_tool_result.assert_not_called()

    def test_creators_allows_own_conversation(self, client):
        own_conv_id = uuid4()
        self._make_conv_service_accept(client)

        mock_ic = MagicMock()
        mock_ic.discover = AsyncMock(return_value={"accounts": []})
        client.app.state.ic_backend = mock_ic

        resp = client.post(
            "/v1/discover/creators",
            json={"query": "fitness", "platform": "instagram",
                  "conversation_id": str(own_conv_id)},
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code == 200
        assert resp.json()["workspace_updated"] is True
        client.app.state.workspace_service.store_tool_result.assert_called_once()

    # ── /videos IDOR tests ──────────────────────────────────────

    def test_videos_rejects_foreign_conversation(self, client):
        foreign_conv_id = uuid4()
        self._make_conv_service_reject(client, foreign_conv_id)

        mock_search = MagicMock()
        mock_search.search = AsyncMock(return_value={"results": [], "total": 0})
        client.app.state.search_service = mock_search

        resp = client.post(
            "/v1/discover/videos",
            json={"query": "brand safety",
                  "conversation_id": str(foreign_conv_id)},
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "conversation_not_found"
        client.app.state.workspace_service.store_tool_result.assert_not_called()

    def test_videos_allows_own_conversation(self, client):
        own_conv_id = uuid4()
        self._make_conv_service_accept(client)

        mock_search = MagicMock()
        mock_search.search = AsyncMock(return_value={"results": [], "total": 0})
        client.app.state.search_service = mock_search

        resp = client.post(
            "/v1/discover/videos",
            json={"query": "brand safety",
                  "conversation_id": str(own_conv_id)},
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["workspace_updated"] is True
        client.app.state.workspace_service.store_tool_result.assert_called_once()
