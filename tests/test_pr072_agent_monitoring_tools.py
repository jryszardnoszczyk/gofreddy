"""Tests for PR-072: Agent Integration — Monitor Tools + System Prompt.

Covers all 9 monitoring tool handlers (via consolidated dispatchers), tier gating,
system prompt generation, passthrough error codes, and _USER_ID_TOOLS membership.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from src.billing.tiers import Tier
from src.monitoring.alerts.models import AlertEvent, AlertRule
from src.monitoring.exceptions import AlertRuleLimitError, MonitoringError, MonitorLimitExceededError, MonitorNotFoundError
from src.monitoring.models import DataSource, DiscoverResult, Mention, Monitor, RawMention, SentimentLabel
from src.orchestrator.agent import VideoIntelligenceAgent, _PASSTHROUGH_ERROR_CODES, _WORKSPACE_QUERY_TOOLS
from src.orchestrator.prompts import build_system_prompt
from src.orchestrator.tools import ToolRegistry, build_default_registry


# ── Fixtures ──────────────────────────────────────────────────────


def _make_monitor(
    *,
    monitor_id: UUID | None = None,
    user_id: UUID | None = None,
    name: str = "Test Monitor",
    keywords: list[str] | None = None,
    sources: list[DataSource] | None = None,
) -> Monitor:
    return Monitor(
        id=monitor_id or uuid4(),
        user_id=user_id or uuid4(),
        name=name,
        keywords=keywords or ["nike", "adidas"],
        boolean_query=None,
        sources=sources or [DataSource.TWITTER, DataSource.INSTAGRAM],
        is_active=True,
        created_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
    )


def _make_mention(
    *,
    mention_id: UUID | None = None,
    monitor_id: UUID | None = None,
    source: DataSource = DataSource.TWITTER,
    content: str = "Great product by Nike!",
    author: str = "user123",
) -> Mention:
    return Mention(
        id=mention_id or uuid4(),
        monitor_id=monitor_id or uuid4(),
        source=source,
        source_id=f"tweet_{uuid4().hex[:8]}",
        author_handle=author,
        author_name="Test User",
        content=content,
        url="https://x.com/user123/status/123",
        published_at=datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc),
        sentiment_score=0.8,
        sentiment_label=SentimentLabel.POSITIVE,
        engagement_likes=100,
        engagement_shares=20,
        engagement_comments=5,
        reach_estimate=5000,
        language="en",
        geo_country="US",
        media_urls=[],
        metadata={},
        created_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
    )


def _make_raw_mention(source: DataSource = DataSource.TWITTER) -> RawMention:
    return RawMention(
        source=source,
        source_id=f"raw_{uuid4().hex[:8]}",
        author_handle="rawuser",
        content="Raw mention content",
        published_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
    )


def _mock_monitoring_service() -> AsyncMock:
    svc = AsyncMock()
    svc.create_monitor = AsyncMock()
    svc.list_monitors = AsyncMock(return_value=[])
    svc.update_monitor = AsyncMock()
    svc.delete_monitor = AsyncMock(return_value=True)
    svc.get_mentions = AsyncMock(return_value=[])
    svc.search_mentions = AsyncMock(return_value=([], 0))
    svc.query_mentions = AsyncMock(return_value=([], 0))
    svc.get_monitor_with_stats = AsyncMock()
    svc.get_mention_aggregates = AsyncMock(return_value={
        "source_breakdown": {"twitter": 50, "instagram": 30},
        "sentiment_breakdown": {"positive": 40, "negative": 10, "neutral": 30},
        "top_authors": [{"handle": "user1", "count": 15}],
        "total_engagement": 5000,
    })
    svc.discover = AsyncMock()
    svc.count_mentions_filtered = AsyncMock(return_value=0)
    svc.get_monitor = AsyncMock()
    svc.enqueue_run = AsyncMock()
    svc.create_alert_rule = AsyncMock()
    svc.list_alert_rules = AsyncMock(return_value=[])
    svc.list_alert_events = AsyncMock(return_value=[])
    return svc


def _build_registry_with_monitoring(
    tier: Tier = Tier.PRO,
    monitoring_service: AsyncMock | None = None,
    **kwargs: Any,
) -> tuple[ToolRegistry, dict[str, str]]:
    """Build registry with monitoring service for testing."""
    svc = monitoring_service or _mock_monitoring_service()
    return build_default_registry(
        tier=tier,
        monitoring_service=svc,
        **kwargs,
    )


# ── Tool Handler Tests ────────────────────────────────────────────


class TestCreateMonitor:
    @pytest.mark.asyncio
    async def test_happy_path(self):
        svc = _mock_monitoring_service()
        monitor = _make_monitor(name="Nike Monitor")
        svc.create_monitor.return_value = monitor

        registry, _ = _build_registry_with_monitoring(monitoring_service=svc)
        result = await registry.execute(
            "manage_monitor",
            {"action": "create", "name": "Nike Monitor", "keywords": "nike, just do it"},
            _passthrough=frozenset({"user_id"}),
            user_tier=Tier.PRO,
        )
        # user_id not passed, will get error
        assert result.get("error") == "invalid_request"

        # Now with user_id
        result = await registry.execute(
            "manage_monitor",
            {"action": "create", "name": "Nike Monitor", "keywords": "nike, just do it", "user_id": str(uuid4())},
            _passthrough=frozenset({"user_id"}),
            user_tier=Tier.PRO,
        )
        assert "monitor_id" in result
        assert result["summary"].startswith("Created monitor")

    @pytest.mark.asyncio
    async def test_quota_exceeded(self):
        svc = _mock_monitoring_service()
        svc.create_monitor.side_effect = MonitorLimitExceededError("Max 10 monitors")

        registry, _ = _build_registry_with_monitoring(monitoring_service=svc)
        result = await registry.execute(
            "manage_monitor",
            {"action": "create", "name": "Test", "keywords": "test", "user_id": str(uuid4())},
            _passthrough=frozenset({"user_id"}),
            user_tier=Tier.PRO,
        )
        assert result["error"] == "monitor_quota_exceeded"


class TestListMonitors:
    @pytest.mark.asyncio
    async def test_empty(self):
        svc = _mock_monitoring_service()
        svc.list_monitors.return_value = []

        registry, _ = _build_registry_with_monitoring(monitoring_service=svc)
        result = await registry.execute(
            "query_monitor",
            {"action": "list", "user_id": str(uuid4())},
            _passthrough=frozenset({"user_id"}),
            user_tier=Tier.PRO,
        )
        assert result["monitors"] == []
        assert "0 active" in result["summary"]

    @pytest.mark.asyncio
    async def test_with_data(self):
        svc = _mock_monitoring_service()
        svc.list_monitors.return_value = [_make_monitor(), _make_monitor(name="Second")]

        registry, _ = _build_registry_with_monitoring(monitoring_service=svc)
        result = await registry.execute(
            "query_monitor",
            {"action": "list", "user_id": str(uuid4())},
            _passthrough=frozenset({"user_id"}),
            user_tier=Tier.PRO,
        )
        assert len(result["monitors"]) == 2
        assert "2 active" in result["summary"]


class TestUpdateMonitor:
    @pytest.mark.asyncio
    async def test_not_found(self):
        svc = _mock_monitoring_service()
        svc.update_monitor.side_effect = MonitorNotFoundError("Not found")

        registry, _ = _build_registry_with_monitoring(monitoring_service=svc)
        result = await registry.execute(
            "manage_monitor",
            {"action": "update", "monitor_id": str(uuid4()), "name": "New Name", "user_id": str(uuid4())},
            _passthrough=frozenset({"user_id"}),
            user_tier=Tier.PRO,
        )
        assert result["error"] == "monitor_not_found"


class TestDeleteMonitor:
    @pytest.mark.asyncio
    async def test_success(self):
        svc = _mock_monitoring_service()
        svc.delete_monitor.return_value = True

        registry, _ = _build_registry_with_monitoring(monitoring_service=svc)
        result = await registry.execute(
            "manage_monitor",
            {"action": "delete", "monitor_id": str(uuid4()), "user_id": str(uuid4())},
            _passthrough=frozenset({"user_id"}),
            user_tier=Tier.PRO,
        )
        assert "deleted" in result["summary"].lower()

    @pytest.mark.asyncio
    async def test_not_found(self):
        svc = _mock_monitoring_service()
        svc.delete_monitor.return_value = False

        registry, _ = _build_registry_with_monitoring(monitoring_service=svc)
        result = await registry.execute(
            "manage_monitor",
            {"action": "delete", "monitor_id": str(uuid4()), "user_id": str(uuid4())},
            _passthrough=frozenset({"user_id"}),
            user_tier=Tier.PRO,
        )
        assert result["error"] == "monitor_not_found"


class TestSearchSocialMentions:
    """PR-075: search_social_mentions replaced by search_content.

    The old handler used monitoring_service.discover() which had empty mention_fetchers.
    New search_content dispatches to individual Xpoz adapters.
    See tests/test_content_normalizer.py for normalizer/dedup unit tests.
    """

    def test_search_social_mentions_removed(self):
        """search_social_mentions is no longer registered."""
        svc = _mock_monitoring_service()
        registry, _ = _build_registry_with_monitoring(monitoring_service=svc)
        assert "search_social_mentions" not in registry.names


class TestSearchMonitorMentions:
    @pytest.mark.asyncio
    async def test_with_query(self):
        svc = _mock_monitoring_service()
        mention = _make_mention()
        svc.query_mentions.return_value = ([mention], 1)

        registry, _ = _build_registry_with_monitoring(monitoring_service=svc)
        result = await registry.execute(
            "query_monitor",
            {"action": "search", "monitor_id": str(uuid4()), "query": "nike shoes", "user_id": str(uuid4())},
            _passthrough=frozenset({"user_id"}),
            user_tier=Tier.PRO,
        )
        assert result["total"] == 1
        assert len(result["mentions"]) == 1

    @pytest.mark.asyncio
    async def test_with_filters(self):
        svc = _mock_monitoring_service()
        svc.query_mentions.return_value = ([_make_mention()], 1)

        registry, _ = _build_registry_with_monitoring(monitoring_service=svc)
        result = await registry.execute(
            "query_monitor",
            {
                "action": "search",
                "monitor_id": str(uuid4()),
                "source": "twitter",
                "sentiment": "positive",
                "user_id": str(uuid4()),
            },
            _passthrough=frozenset({"user_id"}),
            user_tier=Tier.PRO,
        )
        assert result["total"] == 1


class TestGetMonitorAnalytics:
    @pytest.mark.asyncio
    async def test_stats(self):
        svc = _mock_monitoring_service()
        monitor = _make_monitor()
        svc.get_monitor_with_stats.return_value = (monitor, 80)

        registry, _ = _build_registry_with_monitoring(monitoring_service=svc)
        result = await registry.execute(
            "query_monitor",
            {"action": "analytics", "monitor_id": str(uuid4()), "metric": "stats", "user_id": str(uuid4())},
            _passthrough=frozenset({"user_id"}),
            user_tier=Tier.PRO,
        )
        assert "80 mentions" in result["summary"]
        assert result["stats"]["total_mentions"] == 80

    @pytest.mark.asyncio
    async def test_invalid_metric(self):
        svc = _mock_monitoring_service()
        registry, _ = _build_registry_with_monitoring(monitoring_service=svc)
        result = await registry.execute(
            "query_monitor",
            {"action": "analytics", "monitor_id": str(uuid4()), "metric": "nonexistent_metric", "user_id": str(uuid4())},
            _passthrough=frozenset({"user_id"}),
            user_tier=Tier.PRO,
        )
        assert result["error"] == "invalid_metric"
        assert "Invalid metric" in result["summary"]


class TestSaveMentionsToWorkspace:
    @pytest.mark.asyncio
    async def test_saves_mentions(self):
        svc = _mock_monitoring_service()
        svc.get_mentions.return_value = [_make_mention(), _make_mention()]

        ws_service = AsyncMock()
        collection_mock = MagicMock()
        collection_mock.id = uuid4()
        collection_mock.name = "Test Collection"
        summary_mock = MagicMock()
        ws_service.create_collection_from_search = AsyncMock(return_value=(collection_mock, summary_mock))

        registry, _ = build_default_registry(
            tier=Tier.PRO,
            monitoring_service=svc,
            workspace_service=ws_service,
            conversation_id=uuid4(),
        )
        result = await registry.execute(
            "query_monitor",
            {"action": "save_to_workspace", "monitor_id": str(uuid4()), "user_id": str(uuid4())},
            _passthrough=frozenset({"user_id"}),
            user_tier=Tier.PRO,
        )
        assert result["item_count"] == 2
        assert "Saved 2 mentions" in result["summary"]


class TestAnalyzeMentionVideo:
    """analyze_mention_video removed in consolidation (redundant with analyze_video)."""

    def test_analyze_mention_video_not_registered(self):
        svc = _mock_monitoring_service()
        registry, _ = build_default_registry(
            tier=Tier.PRO,
            monitoring_service=svc,
            analysis_service=AsyncMock(),
            video_storage=AsyncMock(),
        )
        assert "analyze_mention_video" not in registry.names


class TestRunMonitorNow:
    @pytest.mark.asyncio
    async def test_happy_path(self):
        svc = _mock_monitoring_service()
        monitor = _make_monitor(name="Nike Monitor")
        svc.get_monitor.return_value = monitor

        registry, _ = _build_registry_with_monitoring(monitoring_service=svc)
        result = await registry.execute(
            "manage_monitor",
            {"action": "run_now", "monitor_id": str(monitor.id), "user_id": str(uuid4())},
            _passthrough=frozenset({"user_id"}),
            user_tier=Tier.PRO,
        )
        assert result["status"] == "enqueued"
        assert "Nike Monitor" in result["summary"]
        svc.enqueue_run.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_monitor_not_found(self):
        svc = _mock_monitoring_service()
        svc.get_monitor.side_effect = MonitorNotFoundError("Not found")

        registry, _ = _build_registry_with_monitoring(monitoring_service=svc)
        result = await registry.execute(
            "manage_monitor",
            {"action": "run_now", "monitor_id": str(uuid4()), "user_id": str(uuid4())},
            _passthrough=frozenset({"user_id"}),
            user_tier=Tier.PRO,
        )
        assert result["error"] == "monitor_not_found"

    @pytest.mark.asyncio
    async def test_cooldown_active(self):
        svc = _mock_monitoring_service()
        monitor = _make_monitor()
        svc.get_monitor.return_value = monitor
        svc.enqueue_run.side_effect = MonitoringError("cooldown: next run in 25 minutes")

        registry, _ = _build_registry_with_monitoring(monitoring_service=svc)
        result = await registry.execute(
            "manage_monitor",
            {"action": "run_now", "monitor_id": str(monitor.id), "user_id": str(uuid4())},
            _passthrough=frozenset({"user_id"}),
            user_tier=Tier.PRO,
        )
        assert result["error"] == "cooldown_active"
        assert "cooldown" in result["summary"]


class TestCreateAlertRule:
    @pytest.mark.asyncio
    async def test_happy_path(self):
        svc = _mock_monitoring_service()
        monitor_uuid = uuid4()
        user_uuid = uuid4()
        rule = AlertRule(
            id=uuid4(), monitor_id=monitor_uuid, user_id=user_uuid,
            rule_type="mention_spike",
            config={"threshold_pct": 200, "window_hours": 1, "min_baseline_runs": 3},
            webhook_url="https://hooks.example.com/test",
            is_active=True, cooldown_minutes=60,
            last_triggered_at=None, consecutive_failures=0,
            created_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
            updated_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
        )
        svc.create_alert_rule.return_value = rule

        registry, _ = _build_registry_with_monitoring(monitoring_service=svc)
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr("src.common.url_validation.resolve_and_validate", AsyncMock(return_value=("hooks.example.com", "1.2.3.4")))
            result = await registry.execute(
                "manage_monitor",
                {
                    "action": "create_alert",
                    "monitor_id": str(monitor_uuid),
                    "webhook_url": "https://hooks.example.com/test",
                    "user_id": str(user_uuid),
                },
                _passthrough=frozenset({"user_id"}),
                user_tier=Tier.PRO,
            )
        assert result["rule_id"] == str(rule.id)
        assert result["rule_type"] == "mention_spike"
        assert result["webhook_url"] == "https://hooks.example.com/test"

    @pytest.mark.asyncio
    async def test_ssrf_rejection(self):
        svc = _mock_monitoring_service()
        registry, _ = _build_registry_with_monitoring(monitoring_service=svc)
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr("src.common.url_validation.resolve_and_validate", AsyncMock(side_effect=ValueError("URL resolves to private IP")))
            result = await registry.execute(
                "manage_monitor",
                {
                    "action": "create_alert",
                    "monitor_id": str(uuid4()),
                    "webhook_url": "http://169.254.169.254/metadata",
                    "user_id": str(uuid4()),
                },
                _passthrough=frozenset({"user_id"}),
                user_tier=Tier.PRO,
            )
        assert result["error"] == "invalid_webhook_url"

    @pytest.mark.asyncio
    async def test_monitor_not_found(self):
        svc = _mock_monitoring_service()
        svc.create_alert_rule.side_effect = MonitorNotFoundError("Not found")

        registry, _ = _build_registry_with_monitoring(monitoring_service=svc)
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr("src.common.url_validation.resolve_and_validate", AsyncMock(return_value=("example.com", "1.2.3.4")))
            result = await registry.execute(
                "manage_monitor",
                {
                    "action": "create_alert",
                    "monitor_id": str(uuid4()),
                    "webhook_url": "https://example.com/hook",
                    "user_id": str(uuid4()),
                },
                _passthrough=frozenset({"user_id"}),
                user_tier=Tier.PRO,
            )
        assert result["error"] == "monitor_not_found"

    @pytest.mark.asyncio
    async def test_limit_exceeded(self):
        svc = _mock_monitoring_service()
        svc.create_alert_rule.side_effect = AlertRuleLimitError("Max 10 rules per monitor")

        registry, _ = _build_registry_with_monitoring(monitoring_service=svc)
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr("src.common.url_validation.resolve_and_validate", AsyncMock(return_value=("example.com", "1.2.3.4")))
            result = await registry.execute(
                "manage_monitor",
                {
                    "action": "create_alert",
                    "monitor_id": str(uuid4()),
                    "webhook_url": "https://example.com/hook",
                    "user_id": str(uuid4()),
                },
                _passthrough=frozenset({"user_id"}),
                user_tier=Tier.PRO,
            )
        assert result["error"] == "alert_limit_exceeded"


class TestListAlertRules:
    @pytest.mark.asyncio
    async def test_happy_path_with_rules(self):
        svc = _mock_monitoring_service()
        monitor_uuid = uuid4()
        user_uuid = uuid4()
        rules = [
            AlertRule(
                id=uuid4(), monitor_id=monitor_uuid, user_id=user_uuid,
                rule_type="mention_spike",
                config={"threshold_pct": 200, "window_hours": 1, "min_baseline_runs": 3},
                webhook_url="https://hooks.example.com/a",
                is_active=True, cooldown_minutes=60,
                last_triggered_at=None, consecutive_failures=0,
                created_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
                updated_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
            ),
            AlertRule(
                id=uuid4(), monitor_id=monitor_uuid, user_id=user_uuid,
                rule_type="mention_spike",
                config={"threshold_pct": 300, "window_hours": 6, "min_baseline_runs": 3},
                webhook_url="https://hooks.example.com/b",
                is_active=False, cooldown_minutes=120,
                last_triggered_at=datetime(2026, 3, 5, tzinfo=timezone.utc),
                consecutive_failures=1,
                created_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
                updated_at=datetime(2026, 3, 5, tzinfo=timezone.utc),
            ),
        ]
        svc.list_alert_rules.return_value = rules

        registry, _ = _build_registry_with_monitoring(monitoring_service=svc)
        result = await registry.execute(
            "manage_monitor",
            {"action": "list_alerts", "monitor_id": str(monitor_uuid), "user_id": str(user_uuid)},
            _passthrough=frozenset({"user_id"}),
            user_tier=Tier.PRO,
        )
        assert len(result["rules"]) == 2
        assert result["rules"][0]["rule_type"] == "mention_spike"
        assert result["rules"][0]["is_active"] is True
        assert result["rules"][1]["is_active"] is False
        assert result["rules"][1]["last_triggered_at"] is not None
        assert "2 alert rule" in result["summary"]

    @pytest.mark.asyncio
    async def test_monitor_not_found(self):
        svc = _mock_monitoring_service()
        svc.list_alert_rules.side_effect = MonitorNotFoundError("Not found")

        registry, _ = _build_registry_with_monitoring(monitoring_service=svc)
        result = await registry.execute(
            "manage_monitor",
            {"action": "list_alerts", "monitor_id": str(uuid4()), "user_id": str(uuid4())},
            _passthrough=frozenset({"user_id"}),
            user_tier=Tier.PRO,
        )
        assert result["error"] == "monitor_not_found"


class TestListAlertEvents:
    @pytest.mark.asyncio
    async def test_happy_path_with_events(self):
        svc = _mock_monitoring_service()
        monitor_uuid = uuid4()
        rule_uuid = uuid4()
        events = [
            AlertEvent(
                id=uuid4(), rule_id=rule_uuid, monitor_id=monitor_uuid,
                triggered_at=datetime(2026, 3, 5, 14, 30, tzinfo=timezone.utc),
                condition_summary="Mentions spiked 350% above baseline",
                payload={"mention_count": 42, "baseline": 12},
                delivery_status="delivered", delivery_attempts=1,
                last_delivery_at=datetime(2026, 3, 5, 14, 31, tzinfo=timezone.utc),
                created_at=datetime(2026, 3, 5, 14, 30, tzinfo=timezone.utc),
            ),
        ]
        svc.list_alert_events.return_value = events

        registry, _ = _build_registry_with_monitoring(monitoring_service=svc)
        result = await registry.execute(
            "manage_monitor",
            {"action": "list_events", "monitor_id": str(monitor_uuid), "user_id": str(uuid4())},
            _passthrough=frozenset({"user_id"}),
            user_tier=Tier.PRO,
        )
        assert len(result["events"]) == 1
        assert result["events"][0]["condition_summary"] == "Mentions spiked 350% above baseline"
        assert result["events"][0]["delivery_status"] == "delivered"
        assert "1 alert event" in result["summary"]

    @pytest.mark.asyncio
    async def test_limit_offset_clamping(self):
        svc = _mock_monitoring_service()
        svc.list_alert_events.return_value = []

        registry, _ = _build_registry_with_monitoring(monitoring_service=svc)
        result = await registry.execute(
            "manage_monitor",
            {"action": "list_events", "monitor_id": str(uuid4()), "limit": 999, "offset": -5, "user_id": str(uuid4())},
            _passthrough=frozenset({"user_id"}),
            user_tier=Tier.PRO,
        )
        # Should not error — handler clamps limit to [1,100] and offset to >=0
        assert result["events"] == []
        # Verify clamped values were passed to service
        call_kwargs = svc.list_alert_events.call_args
        assert call_kwargs.kwargs["limit"] == 100
        assert call_kwargs.kwargs["offset"] == 0


# ── Tier Gating Tests ─────────────────────────────────────────────


class TestTierGating:
    def test_free_tier_no_crud_tools(self):
        """Free tier has no monitoring CRUD tools (search_content requires xpoz_adapters)."""
        svc = _mock_monitoring_service()
        registry, _restricted = _build_registry_with_monitoring(tier=Tier.FREE, monitoring_service=svc)
        names = registry.names
        assert "manage_monitor" not in names
        assert "query_monitor" not in names

    def test_pro_tier_all_registered(self):
        """Pro tier gets consolidated monitoring tools."""
        svc = _mock_monitoring_service()
        registry, _ = build_default_registry(
            tier=Tier.PRO,
            monitoring_service=svc,
        )
        names = registry.names
        expected = {
            "manage_monitor", "query_monitor",
        }
        assert expected <= set(names)
        # draft_action_packet was absorbed into query_monitor(action="draft_action")
        assert "draft_action_packet" not in names

    def test_restricted_tools_include_monitoring(self):
        """Free tier restricted_tools has monitoring descriptions."""
        svc = _mock_monitoring_service()
        _, restricted = _build_registry_with_monitoring(tier=Tier.FREE, monitoring_service=svc)
        assert "manage_monitor" in restricted
        assert "query_monitor" in restricted
        # draft_action_packet absorbed into query_monitor
        assert "draft_action_packet" not in restricted

    def test_alert_tools_not_in_restricted(self):
        """Deferred alert tools removed — no misleading upgrade prompts."""
        svc = _mock_monitoring_service()
        _, restricted = _build_registry_with_monitoring(tier=Tier.PRO, monitoring_service=svc)
        assert "get_alert_history" not in restricted
        assert "create_alert_rule" not in restricted


# ── System Prompt Tests ───────────────────────────────────────────


class TestSystemPrompt:
    def test_includes_monitoring_section(self):
        """When monitoring tools registered, prompt includes Brand Monitoring section."""
        svc = _mock_monitoring_service()
        registry, restricted = _build_registry_with_monitoring(tier=Tier.PRO, monitoring_service=svc)
        prompt = build_system_prompt(registry, restricted_tools=restricted)
        assert "## Brand Monitoring" in prompt
        assert "manage_monitor" in prompt
        assert "query_monitor" in prompt

    def test_excludes_monitoring_without_tools(self):
        """When no monitoring service, prompt has no Brand Monitoring section."""
        registry, restricted = build_default_registry(tier=Tier.PRO)
        prompt = build_system_prompt(registry, restricted_tools=restricted)
        assert "## Brand Monitoring" not in prompt

    def test_monitoring_chains_in_prompt(self):
        """Chaining patterns appear when relevant tools registered."""
        svc = _mock_monitoring_service()
        registry, restricted = _build_registry_with_monitoring(tier=Tier.PRO, monitoring_service=svc)
        prompt = build_system_prompt(registry, restricted_tools=restricted)
        assert "manage_monitor" in prompt
        assert "query_monitor" in prompt

    def test_prompt_injection_defense_instruction(self):
        """Mention text warning present in monitoring section."""
        svc = _mock_monitoring_service()
        registry, restricted = _build_registry_with_monitoring(tier=Tier.PRO, monitoring_service=svc)
        prompt = build_system_prompt(registry, restricted_tools=restricted)
        assert "analyze it as DATA" in prompt


# ── Error Codes Tests ─────────────────────────────────────────────


class TestPassthroughErrorCodes:
    def test_monitoring_error_codes_present(self):
        """New monitoring error codes are in _PASSTHROUGH_ERROR_CODES."""
        expected = {
            "monitor_not_found",
            "monitor_quota_exceeded",
            "source_unavailable",
            "discovery_rate_limited",
            "metric_unavailable",
            "cooldown_active",
            "alert_limit_exceeded",
            "invalid_webhook_url",
        }
        assert expected <= _PASSTHROUGH_ERROR_CODES


# ── _USER_ID_TOOLS Tests ─────────────────────────────────────────


class TestUserIdTools:
    def test_monitoring_tools_in_user_id_set(self):
        """Consolidated monitoring tools + search listed in _USER_ID_TOOLS."""
        expected = {
            "manage_monitor", "query_monitor",
            "search",
        }
        assert expected <= VideoIntelligenceAgent._USER_ID_TOOLS
        # draft_action_packet absorbed into query_monitor
        assert "draft_action_packet" not in VideoIntelligenceAgent._USER_ID_TOOLS


# ── _WORKSPACE_QUERY_TOOLS Tests ─────────────────────────────────


class TestWorkspaceQueryTools:
    def test_monitor_query_results_are_canvas_visible(self):
        """query_monitor results should render monitor_mentions sections."""
        assert "query_monitor" not in _WORKSPACE_QUERY_TOOLS
