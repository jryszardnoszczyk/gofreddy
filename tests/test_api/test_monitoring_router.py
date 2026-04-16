"""Tests for monitoring router — Monitor CRUD + mention listing + FTS search."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.monitoring.exceptions import MonitorLimitExceededError, MonitorNotFoundError
from src.monitoring.models import DataSource, Mention, Monitor, SentimentLabel


def _make_monitor(**overrides):
    defaults = dict(
        id=uuid4(),
        user_id=uuid4(),
        name="Test Monitor",
        keywords=["brand", "keyword"],
        boolean_query=None,
        sources=[DataSource.TWITTER, DataSource.REDDIT],
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return Monitor(**defaults)


def _make_mention(**overrides):
    defaults = dict(
        id=uuid4(),
        monitor_id=uuid4(),
        source=DataSource.TWITTER,
        source_id="tweet_123",
        author_handle="@user",
        author_name="User Name",
        content="Great brand mention",
        url="https://x.com/user/status/123",
        published_at=datetime.now(timezone.utc),
        sentiment_score=0.8,
        sentiment_label=SentimentLabel.POSITIVE,
        engagement_likes=10,
        engagement_shares=2,
        engagement_comments=1,
        reach_estimate=None,
        language="en",
        geo_country=None,
        media_urls=[],
        metadata={},
        created_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return Mention(**defaults)


@pytest.mark.mock_required
class TestCreateMonitor:
    def test_create_success(self, client):
        monitor = _make_monitor(name="My Monitor")
        client.app.state.monitoring_service.create_monitor = AsyncMock(return_value=monitor)

        resp = client.post(
            "/v1/monitors/",
            json={"name": "My Monitor", "keywords": "brand, keyword", "sources": ["twitter", "reddit"]},
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "My Monitor"
        assert body["id"] == str(monitor.id)

    def test_create_empty_keywords_rejected(self, client):
        resp = client.post(
            "/v1/monitors/",
            json={"name": "Empty", "keywords": "  , , ", "sources": ["twitter"]},
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "invalid_keywords"

    def test_create_quota_exceeded(self, client):
        client.app.state.monitoring_service.create_monitor = AsyncMock(
            side_effect=MonitorLimitExceededError("Maximum 3 monitors allowed")
        )
        resp = client.post(
            "/v1/monitors/",
            json={"name": "Over Limit", "keywords": "brand", "sources": ["twitter"]},
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code == 429
        assert resp.json()["error"]["code"] == "monitor_limit_exceeded"

    def test_create_too_many_sources(self, client):
        # Pydantic allows max 10 sources, but Pro tier allows 10. Use exactly 10+1
        # to hit Pydantic validation. For router-level check, we'd need a Free tier test.
        sources = ["twitter", "reddit", "instagram", "bluesky", "facebook", "linkedin",
                    "tiktok", "newsdata", "trustpilot", "app_store", "play_store"]
        resp = client.post(
            "/v1/monitors/",
            json={"name": "Many Sources", "keywords": "brand", "sources": sources},
            headers={"Authorization": "Bearer test"},
        )
        # 11 sources exceeds Pydantic max_length=10, returns 422 validation error
        assert resp.status_code == 422


@pytest.mark.mock_required
class TestListMonitors:
    def test_list_returns_monitors(self, client):
        enriched = [
            {
                "id": str(uuid4()), "name": "A",
                "keywords": ["x"], "boolean_query": None, "sources": ["twitter"],
                "competitor_brands": [], "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "next_run_at": None, "last_run_status": None,
                "last_run_completed_at": None, "last_run_error": None,
                "alert_count_24h": 0, "mention_count": 5,
            },
            {
                "id": str(uuid4()), "name": "B",
                "keywords": ["y"], "boolean_query": None, "sources": ["reddit"],
                "competitor_brands": [], "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "next_run_at": None, "last_run_status": None,
                "last_run_completed_at": None, "last_run_error": None,
                "alert_count_24h": 0, "mention_count": 3,
            },
        ]
        client.app.state.monitoring_service.list_monitors_enriched = AsyncMock(return_value=enriched)

        resp = client.get("/v1/monitors/", headers={"Authorization": "Bearer test"})
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_list_empty(self, client):
        client.app.state.monitoring_service.list_monitors_enriched = AsyncMock(return_value=[])
        resp = client.get("/v1/monitors/", headers={"Authorization": "Bearer test"})
        assert resp.status_code == 200
        assert resp.json() == []


@pytest.mark.mock_required
class TestGetMonitor:
    def test_get_with_stats(self, client):
        monitor = _make_monitor()
        client.app.state.monitoring_service.get_monitor_with_stats = AsyncMock(
            return_value=(monitor, 42)
        )

        resp = client.get(
            f"/v1/monitors/{monitor.id}",
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["mention_count"] == 42

    def test_get_not_found(self, client):
        client.app.state.monitoring_service.get_monitor_with_stats = AsyncMock(
            side_effect=MonitorNotFoundError("not found")
        )
        resp = client.get(
            f"/v1/monitors/{uuid4()}",
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "monitor_not_found"


@pytest.mark.mock_required
class TestUpdateMonitor:
    def test_update_name(self, client):
        monitor = _make_monitor(name="Updated")
        client.app.state.monitoring_service.update_monitor = AsyncMock(return_value=monitor)

        resp = client.put(
            f"/v1/monitors/{monitor.id}",
            json={"name": "Updated"},
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated"

    def test_update_not_found(self, client):
        client.app.state.monitoring_service.update_monitor = AsyncMock(
            side_effect=MonitorNotFoundError("not found")
        )
        resp = client.put(
            f"/v1/monitors/{uuid4()}",
            json={"name": "X"},
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code == 404

    def test_update_name_only_does_not_enqueue_backfill(self, client):
        """Name-only update should NOT trigger a backfill Cloud Task."""
        monitor = _make_monitor(name="Renamed")
        client.app.state.monitoring_service.update_monitor = AsyncMock(return_value=monitor)
        mock_task = MagicMock()
        mock_task.enqueue_monitor_run = AsyncMock()
        client.app.state.monitor_task_client = mock_task

        resp = client.put(
            f"/v1/monitors/{monitor.id}",
            json={"name": "Renamed"},
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code == 200
        mock_task.enqueue_monitor_run.assert_not_awaited()

    def test_update_is_active_only_does_not_enqueue_backfill(self, client):
        """is_active-only update should NOT trigger a backfill Cloud Task."""
        monitor = _make_monitor(is_active=False)
        client.app.state.monitoring_service.update_monitor = AsyncMock(return_value=monitor)
        mock_task = MagicMock()
        mock_task.enqueue_monitor_run = AsyncMock()
        client.app.state.monitor_task_client = mock_task

        resp = client.put(
            f"/v1/monitors/{monitor.id}",
            json={"is_active": False},
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code == 200
        mock_task.enqueue_monitor_run.assert_not_awaited()

    def test_update_keywords_triggers_backfill(self, client):
        """Changing keywords SHOULD trigger a backfill Cloud Task."""
        monitor = _make_monitor()
        client.app.state.monitoring_service.update_monitor = AsyncMock(return_value=monitor)
        mock_task = MagicMock()
        mock_task.enqueue_monitor_run = AsyncMock(return_value="mock-task-id")
        client.app.state.monitor_task_client = mock_task

        resp = client.put(
            f"/v1/monitors/{monitor.id}",
            json={"keywords": "new, terms"},
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code == 200
        mock_task.enqueue_monitor_run.assert_awaited_once_with(
            monitor_id=monitor.id, delay_seconds=0,
        )

    def test_update_sources_triggers_backfill(self, client):
        """Changing sources SHOULD trigger a backfill Cloud Task."""
        monitor = _make_monitor()
        client.app.state.monitoring_service.update_monitor = AsyncMock(return_value=monitor)
        mock_task = MagicMock()
        mock_task.enqueue_monitor_run = AsyncMock(return_value="mock-task-id")
        client.app.state.monitor_task_client = mock_task

        resp = client.put(
            f"/v1/monitors/{monitor.id}",
            json={"sources": ["twitter", "reddit", "instagram"]},
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code == 200
        mock_task.enqueue_monitor_run.assert_awaited_once()

    def test_update_boolean_query_triggers_backfill(self, client):
        """Changing boolean_query SHOULD trigger a backfill Cloud Task."""
        monitor = _make_monitor()
        client.app.state.monitoring_service.update_monitor = AsyncMock(return_value=monitor)
        mock_task = MagicMock()
        mock_task.enqueue_monitor_run = AsyncMock(return_value="mock-task-id")
        client.app.state.monitor_task_client = mock_task

        resp = client.put(
            f"/v1/monitors/{monitor.id}",
            json={"boolean_query": "brand AND launch"},
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code == 200
        mock_task.enqueue_monitor_run.assert_awaited_once()


@pytest.mark.mock_required
class TestDeleteMonitor:
    def test_delete_success(self, client):
        resp = client.delete(
            f"/v1/monitors/{uuid4()}",
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code == 204

    def test_delete_not_found(self, client):
        client.app.state.monitoring_service.delete_monitor = AsyncMock(return_value=False)

        resp = client.delete(
            f"/v1/monitors/{uuid4()}",
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code == 404


@pytest.mark.mock_required
class TestListMentions:
    def test_list_mentions_empty(self, client):
        mid = uuid4()
        client.app.state.monitoring_service.query_mentions = AsyncMock(return_value=([], 0))
        resp = client.get(
            f"/v1/monitors/{mid}/mentions",
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"] == []
        assert body["total"] == 0

    def test_list_mentions_with_data(self, client):
        mention = _make_mention()
        client.app.state.monitoring_service.query_mentions = AsyncMock(return_value=([mention], 1))

        resp = client.get(
            f"/v1/monitors/{uuid4()}/mentions",
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) == 1
        assert body["data"][0]["source"] == "twitter"
        assert body["data"][0]["engagement_total"] == 13  # 10+2+1
        assert body["total"] == 1

    def test_list_mentions_with_filters(self, client):
        client.app.state.monitoring_service.query_mentions = AsyncMock(return_value=([], 0))

        resp = client.get(
            f"/v1/monitors/{uuid4()}/mentions?source=twitter&sentiment=positive&limit=10",
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code == 200


@pytest.mark.mock_required
class TestSearchMentions:
    """FTS is now integrated into the unified /mentions endpoint via ?q= param."""

    def test_search_returns_results(self, client):
        mention = _make_mention()
        client.app.state.monitoring_service.query_mentions = AsyncMock(
            return_value=([mention], 1)
        )

        resp = client.get(
            f"/v1/monitors/{uuid4()}/mentions?q=brand",
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert len(body["data"]) == 1

    def test_search_with_intent_filter(self, client):
        """Verify intent filter is accepted."""
        client.app.state.monitoring_service.query_mentions = AsyncMock(
            return_value=([], 0)
        )
        resp = client.get(
            f"/v1/monitors/{uuid4()}/mentions?q=brand&intent=complaint",
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code == 200
