"""Tests for PR-073: Intelligence Agent Tools — query_monitor(action='analytics') metric variants.

Covers all 5 metric dispatch branches, parameter validation, empty results,
error handling, trends correlation unit tests, and ToolDefinition schema.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.billing.tiers import Tier
from src.monitoring.exceptions import MonitorNotFoundError, MonitoringError
from src.monitoring.intelligence.trends_correlation import (
    TrendsCorrelationBucket,
    TrendsCorrelationResult,
    safe_pearson,
)
from src.monitoring.models import DataSource, Monitor, SentimentBucket, ShareOfVoiceEntry
from src.orchestrator.tools import ToolRegistry, build_default_registry


# ── Fixtures ──────────────────────────────────────────────────────

_PASSTHROUGH = frozenset({"user_id"})


def _make_monitor(
    *,
    monitor_id=None, user_id=None, name="Test Monitor",
    keywords=None, sources=None,
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


def _mock_monitoring_service() -> AsyncMock:
    svc = AsyncMock()
    svc.create_monitor = AsyncMock()
    svc.list_monitors = AsyncMock(return_value=[])
    svc.update_monitor = AsyncMock()
    svc.delete_monitor = AsyncMock(return_value=True)
    svc.get_mentions = AsyncMock(return_value=[])
    svc.search_mentions = AsyncMock(return_value=([], 0))
    svc.get_monitor_with_stats = AsyncMock()
    svc.get_mention_aggregates = AsyncMock(return_value={
        "source_breakdown": {"twitter": 50, "instagram": 30},
        "sentiment_breakdown": {"positive": 40, "negative": 10, "neutral": 30},
        "top_authors": [{"handle": "user1", "count": 15}],
        "total_engagement": 5000,
    })
    svc.discover = AsyncMock()
    svc.count_mentions_filtered = AsyncMock(return_value=0)
    svc.sentiment_time_series = AsyncMock(return_value=[])
    svc.get_share_of_voice = AsyncMock(return_value=[])
    svc.get_topics = AsyncMock(return_value=[])
    svc.get_trends_correlation = AsyncMock()
    return svc


def _build_registry(
    tier: Tier = Tier.PRO,
    monitoring_service: AsyncMock | None = None,
    **kwargs: Any,
) -> tuple[ToolRegistry, dict[str, str]]:
    svc = monitoring_service or _mock_monitoring_service()
    return build_default_registry(tier=tier, monitoring_service=svc, **kwargs)


_USER_ID = str(uuid4())
_MONITOR_ID = str(uuid4())


# ── Metric Dispatch Tests ──────────────────────────────────────────


class TestSentimentTimeline:
    @pytest.mark.asyncio
    async def test_returns_time_series(self):
        svc = _mock_monitoring_service()
        buckets = [
            SentimentBucket(
                period_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
                avg_sentiment=0.65, mention_count=100,
                positive_count=50, negative_count=10, neutral_count=30, mixed_count=10,
            ),
            SentimentBucket(
                period_start=datetime(2026, 3, 2, tzinfo=timezone.utc),
                avg_sentiment=0.45, mention_count=80,
                positive_count=30, negative_count=20, neutral_count=25, mixed_count=5,
            ),
        ]
        svc.sentiment_time_series.return_value = buckets
        registry, _ = _build_registry(monitoring_service=svc)

        result = await registry.execute(
            "query_monitor",
            {"action": "analytics", "monitor_id": _MONITOR_ID, "metric": "sentiment_timeline", "user_id": _USER_ID},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )

        assert "sentiment_timeline" in result
        assert len(result["sentiment_timeline"]) == 2
        assert result["sentiment_timeline"][0]["avg_sentiment"] == 0.65
        assert result["sentiment_timeline"][0]["mention_count"] == 100
        assert result["sentiment_timeline"][0]["positive"] == 50
        assert "avg sentiment" in result["summary"]

    @pytest.mark.asyncio
    async def test_empty_returns_empty_list(self):
        svc = _mock_monitoring_service()
        svc.sentiment_time_series.return_value = []
        registry, _ = _build_registry(monitoring_service=svc)

        result = await registry.execute(
            "query_monitor",
            {"action": "analytics", "monitor_id": _MONITOR_ID, "metric": "sentiment_timeline", "user_id": _USER_ID},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )

        assert result["sentiment_timeline"] == []
        assert "No sentiment data" in result["summary"]


class TestShareOfVoice:
    @pytest.mark.asyncio
    async def test_returns_competitive_share(self):
        svc = _mock_monitoring_service()
        entries = [
            ShareOfVoiceEntry(brand="Nike", mention_count=200, percentage=60.0, sentiment_avg=0.7),
            ShareOfVoiceEntry(brand="Adidas", mention_count=100, percentage=30.0, sentiment_avg=0.5),
            ShareOfVoiceEntry(brand="Puma", mention_count=33, percentage=10.0, sentiment_avg=None),
        ]
        svc.get_share_of_voice.return_value = entries
        registry, _ = _build_registry(monitoring_service=svc)

        result = await registry.execute(
            "query_monitor",
            {"action": "analytics", "monitor_id": _MONITOR_ID, "metric": "share_of_voice", "user_id": _USER_ID},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )

        assert "share_of_voice" in result
        assert len(result["share_of_voice"]) == 3
        assert result["share_of_voice"][0]["brand"] == "Nike"
        assert result["share_of_voice"][0]["share"] == 60.0
        assert result["share_of_voice"][2]["sentiment_avg"] is None
        assert "Leader: Nike" in result["summary"]

    @pytest.mark.asyncio
    async def test_no_competitors_returns_helpful_message(self):
        svc = _mock_monitoring_service()
        svc.get_share_of_voice.return_value = []
        registry, _ = _build_registry(monitoring_service=svc)

        result = await registry.execute(
            "query_monitor",
            {"action": "analytics", "monitor_id": _MONITOR_ID, "metric": "share_of_voice", "user_id": _USER_ID},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )

        assert result["share_of_voice"] == []
        assert "competitor_brands" in result["summary"]


class TestTrendsCorrelation:
    @pytest.mark.asyncio
    async def test_returns_correlated_data(self):
        svc = _mock_monitoring_service()
        svc.get_trends_correlation.return_value = TrendsCorrelationResult(
            buckets=[
                TrendsCorrelationBucket(
                    period_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
                    mention_count=50, google_trends_score=75.0,
                ),
                TrendsCorrelationBucket(
                    period_start=datetime(2026, 3, 2, tzinfo=timezone.utc),
                    mention_count=80, google_trends_score=90.0,
                ),
                TrendsCorrelationBucket(
                    period_start=datetime(2026, 3, 3, tzinfo=timezone.utc),
                    mention_count=120, google_trends_score=95.0,
                ),
            ],
            correlation_coefficient=0.95,
            keyword="nike",
        )
        registry, _ = _build_registry(monitoring_service=svc)

        result = await registry.execute(
            "query_monitor",
            {"action": "analytics", "monitor_id": _MONITOR_ID, "metric": "trends_correlation", "user_id": _USER_ID},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )

        assert "trends_correlation" in result
        assert result["trends_correlation"]["keyword"] == "nike"
        assert result["trends_correlation"]["correlation_coefficient"] == 0.95
        assert len(result["trends_correlation"]["buckets"]) == 3
        assert "r=0.95" in result["summary"]

    @pytest.mark.asyncio
    async def test_no_google_trends_data(self):
        svc = _mock_monitoring_service()
        svc.get_trends_correlation.return_value = TrendsCorrelationResult(
            buckets=[], correlation_coefficient=None, keyword="nike",
        )
        registry, _ = _build_registry(monitoring_service=svc)

        result = await registry.execute(
            "query_monitor",
            {"action": "analytics", "monitor_id": _MONITOR_ID, "metric": "trends_correlation", "user_id": _USER_ID},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )

        assert result["trends_correlation"]["buckets"] == []
        assert result["trends_correlation"]["correlation_coefficient"] is None
        assert "Google Trends" in result["summary"]


# ── Parameter Validation Tests ─────────────────────────────────────


class TestParameterValidation:
    @pytest.mark.asyncio
    async def test_invalid_metric_returns_error(self):
        registry, _ = _build_registry()
        result = await registry.execute(
            "query_monitor",
            {"action": "analytics", "monitor_id": _MONITOR_ID, "metric": "invalid", "user_id": _USER_ID},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )
        assert result["error"] == "invalid_metric"
        assert "invalid" in result["summary"].lower()

    @pytest.mark.asyncio
    async def test_window_defaults_to_7d(self):
        svc = _mock_monitoring_service()
        svc.sentiment_time_series.return_value = []
        registry, _ = _build_registry(monitoring_service=svc)

        await registry.execute(
            "query_monitor",
            {"action": "analytics", "monitor_id": _MONITOR_ID, "metric": "sentiment_timeline", "user_id": _USER_ID},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )

        svc.sentiment_time_series.assert_called_once()
        call_kwargs = svc.sentiment_time_series.call_args
        assert call_kwargs.kwargs["window"] == "7d"

    @pytest.mark.asyncio
    async def test_granularity_defaults_to_1d(self):
        svc = _mock_monitoring_service()
        svc.sentiment_time_series.return_value = []
        registry, _ = _build_registry(monitoring_service=svc)

        await registry.execute(
            "query_monitor",
            {"action": "analytics", "monitor_id": _MONITOR_ID, "metric": "sentiment_timeline", "user_id": _USER_ID},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )

        svc.sentiment_time_series.assert_called_once()
        call_kwargs = svc.sentiment_time_series.call_args
        assert call_kwargs.kwargs["granularity"] == "1d"

    @pytest.mark.asyncio
    async def test_window_parsed_to_days_for_sov(self):
        svc = _mock_monitoring_service()
        svc.get_share_of_voice.return_value = []
        registry, _ = _build_registry(monitoring_service=svc)

        await registry.execute(
            "query_monitor",
            {"action": "analytics", "monitor_id": _MONITOR_ID, "metric": "share_of_voice", "window": "30d", "user_id": _USER_ID},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )

        svc.get_share_of_voice.assert_called_once()
        call_kwargs = svc.get_share_of_voice.call_args
        assert call_kwargs.kwargs["window_days"] == 30

    @pytest.mark.asyncio
    async def test_invalid_window_returns_error(self):
        registry, _ = _build_registry()
        result = await registry.execute(
            "query_monitor",
            {"action": "analytics", "monitor_id": _MONITOR_ID, "metric": "sentiment_timeline", "window": "999d", "user_id": _USER_ID},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )
        assert result["error"] == "invalid_window"

    @pytest.mark.asyncio
    async def test_invalid_granularity_returns_error(self):
        registry, _ = _build_registry()
        result = await registry.execute(
            "query_monitor",
            {"action": "analytics", "monitor_id": _MONITOR_ID, "metric": "sentiment_timeline", "granularity": "2h", "user_id": _USER_ID},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )
        assert result["error"] == "invalid_granularity"

    @pytest.mark.asyncio
    async def test_missing_user_id_returns_error(self):
        registry, _ = _build_registry()
        result = await registry.execute(
            "query_monitor",
            {"action": "analytics", "monitor_id": _MONITOR_ID, "metric": "stats"},
            user_tier=Tier.PRO,
        )
        assert result["error"] == "invalid_request"
        assert "user_id" in result["summary"]

    @pytest.mark.asyncio
    async def test_topic_clusters_rejects_1d_window(self):
        registry, _ = _build_registry()
        result = await registry.execute(
            "query_monitor",
            {"action": "analytics", "monitor_id": _MONITOR_ID, "metric": "topic_clusters", "window": "1d", "user_id": _USER_ID},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )
        assert result["error"] == "invalid_window"
        assert "topic_clusters" in result["summary"]

    @pytest.mark.asyncio
    async def test_topic_clusters_rejects_90d_window(self):
        registry, _ = _build_registry()
        result = await registry.execute(
            "query_monitor",
            {"action": "analytics", "monitor_id": _MONITOR_ID, "metric": "topic_clusters", "window": "90d", "user_id": _USER_ID},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )
        assert result["error"] == "invalid_window"

    @pytest.mark.asyncio
    async def test_sov_rejects_1d_window(self):
        registry, _ = _build_registry()
        result = await registry.execute(
            "query_monitor",
            {"action": "analytics", "monitor_id": _MONITOR_ID, "metric": "share_of_voice", "window": "1d", "user_id": _USER_ID},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )
        assert result["error"] == "invalid_window"
        assert "share_of_voice" in result["summary"]


# ── Error Handling Tests ───────────────────────────────────────────


class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_monitor_not_found(self):
        svc = _mock_monitoring_service()
        svc.sentiment_time_series.side_effect = MonitorNotFoundError("not found")
        registry, _ = _build_registry(monitoring_service=svc)

        result = await registry.execute(
            "query_monitor",
            {"action": "analytics", "monitor_id": _MONITOR_ID, "metric": "sentiment_timeline", "user_id": _USER_ID},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )

        assert result["error"] == "monitor_not_found"

    @pytest.mark.asyncio
    async def test_monitoring_error_returns_domain_error(self):
        svc = _mock_monitoring_service()
        svc.get_topics.side_effect = MonitoringError("topic clustering failed")
        registry, _ = _build_registry(monitoring_service=svc)

        result = await registry.execute(
            "query_monitor",
            {"action": "analytics", "monitor_id": _MONITOR_ID, "metric": "topic_clusters", "user_id": _USER_ID},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )

        assert result["error"] == "analytics_error"
        assert "topic clustering failed" in result["summary"]

    @pytest.mark.asyncio
    async def test_generic_exception_sanitized(self):
        svc = _mock_monitoring_service()
        svc.get_share_of_voice.side_effect = RuntimeError("connection lost")
        registry, _ = _build_registry(monitoring_service=svc)

        result = await registry.execute(
            "query_monitor",
            {"action": "analytics", "monitor_id": _MONITOR_ID, "metric": "share_of_voice", "user_id": _USER_ID},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )

        assert result["error"] == "analytics_error"
        # Should NOT contain the raw exception message (sanitized)
        assert "connection lost" not in result["summary"]
        assert "Failed to retrieve" in result["summary"]


# ── Trends Correlation Unit Tests ──────────────────────────────────


class TestSafePearson:
    def test_known_correlation(self):
        # Perfectly correlated
        r = safe_pearson([1.0, 2.0, 3.0, 4.0], [2.0, 4.0, 6.0, 8.0])
        assert r is not None
        assert abs(r - 1.0) < 0.001

    def test_insufficient_data_returns_none(self):
        assert safe_pearson([1.0, 2.0], [3.0, 4.0]) is None

    def test_constant_data_returns_none(self):
        # All same values -> StatisticsError
        assert safe_pearson([5.0, 5.0, 5.0], [1.0, 2.0, 3.0]) is None

    def test_empty_returns_none(self):
        assert safe_pearson([], []) is None


# ── ToolDefinition Schema Test ─────────────────────────────────────


class TestToolDefinitionSchema:
    def test_metric_enum_matches_valid_metrics(self):
        """Verify ToolDefinition enum is single source of truth with handler constants."""
        registry, _ = _build_registry()
        tool_def = registry.get("query_monitor")
        assert tool_def is not None

        enum_values = tool_def.parameters["metric"]["enum"]
        expected = ["stats", "sentiment_timeline", "sentiment_by_source", "share_of_voice", "topic_clusters", "trends_correlation"]
        assert enum_values == expected

    def test_window_enum_present(self):
        registry, _ = _build_registry()
        tool_def = registry.get("query_monitor")
        assert tool_def is not None
        assert "window" in tool_def.parameters
        assert tool_def.parameters["window"]["enum"] == ["1d", "7d", "14d", "30d", "90d"]

    def test_granularity_enum_present(self):
        registry, _ = _build_registry()
        tool_def = registry.get("query_monitor")
        assert tool_def is not None
        assert "granularity" in tool_def.parameters
        assert tool_def.parameters["granularity"]["enum"] == ["1h", "6h", "1d"]


# ── Stats Metric (Existing, Regression) ────────────────────────────


class TestStatsMetric:
    @pytest.mark.asyncio
    async def test_stats_still_works(self):
        """Regression: stats metric must still work after handler expansion."""
        svc = _mock_monitoring_service()
        monitor = _make_monitor()
        svc.get_monitor_with_stats.return_value = (monitor, 500)
        registry, _ = _build_registry(monitoring_service=svc)

        result = await registry.execute(
            "query_monitor",
            {"action": "analytics", "monitor_id": str(monitor.id), "metric": "stats", "user_id": str(monitor.user_id)},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )

        assert "stats" in result
        assert result["stats"]["total_mentions"] == 500
        assert "Monitor 'Test Monitor'" in result["summary"]
