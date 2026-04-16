"""Monitoring service — orchestrates monitor CRUD, mention ingestion, and queries."""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from .alerts.models import AlertEvent, AlertRule, SpikeConfig
from .config import MonitoringSettings
from .discovery import discover_mentions
from .exceptions import (
    AlertRuleLimitError,
    AlertRuleNotFoundError,
    ClassificationCapExceededError,
    MonitorLimitExceededError,
    MonitorNotFoundError,
    MonitoringError,
)
from .fetcher_protocol import MentionFetcher
from .models import (
    DataSource,
    DiscoverResult,
    Mention,
    Monitor,
    MonitorChangelog,
    MonitorRun,
    RawMention,
    SentimentBucket,
    SentimentLabel,
    ShareOfVoiceEntry,
    SourceSentiment,
)
from .repository import PostgresMonitoringRepository

if TYPE_CHECKING:
    from .intelligence.intent import IntentClassifier
    from .intelligence.trends_correlation import TrendsCorrelationResult
    from .workspace_bridge import WorkspaceBridge

logger = logging.getLogger(__name__)


class MonitoringService:
    """Service layer for brand monitoring operations."""

    def __init__(
        self,
        repository: PostgresMonitoringRepository,
        settings: MonitoringSettings | None = None,
        *,
        mention_fetchers: dict[DataSource, MentionFetcher] | None = None,
        intent_classifier: IntentClassifier | None = None,
        workspace_bridge: WorkspaceBridge | None = None,
    ) -> None:
        self._repo = repository
        self._settings = settings or MonitoringSettings()
        self._fetchers = mention_fetchers or {}
        self._intent_classifier = intent_classifier
        self._workspace_bridge = workspace_bridge

    @property
    def available_sources(self) -> frozenset[DataSource]:
        """Sources with a registered runtime adapter."""
        return frozenset(self._fetchers.keys())

    async def create_monitor(
        self,
        user_id: UUID,
        name: str,
        keywords: list[str],
        sources: list[DataSource],
        *,
        boolean_query: str | None = None,
        competitor_brands: list[str] | None = None,
        max_monitors: int | None = None,
        max_sources: int | None = None,
    ) -> Monitor:
        """Create a monitor with quota enforcement.

        Quotas (max_monitors, max_sources) should be passed from the router
        via TierConfig. Falls back to settings if not provided.
        """
        effective_max_monitors = max_monitors if max_monitors is not None else self._settings.max_monitors_per_user
        effective_max_sources = max_sources if max_sources is not None else self._settings.max_sources_per_monitor

        count = await self._repo.count_monitors(user_id)
        if count >= effective_max_monitors:
            raise MonitorLimitExceededError(
                f"Maximum {effective_max_monitors} monitors per user"
            )

        if len(sources) > effective_max_sources:
            raise MonitorLimitExceededError(
                f"Maximum {effective_max_sources} sources per monitor"
            )

        # Source validation: reject sources without a runtime adapter
        unavailable = set(sources) - self.available_sources
        if unavailable:
            raise MonitoringError(
                f"Sources not available: {', '.join(s.value for s in unavailable)}. "
                f"Available: {', '.join(s.value for s in sorted(self.available_sources, key=lambda s: s.value))}"
            )

        return await self._repo.create_monitor(
            user_id=user_id,
            name=name,
            keywords=keywords,
            sources=sources,
            boolean_query=boolean_query,
            competitor_brands=competitor_brands or [],
        )

    async def get_monitor(self, monitor_id: UUID, user_id: UUID) -> Monitor:
        """Get monitor with IDOR check."""
        monitor = await self._repo.get_monitor(monitor_id, user_id)
        if monitor is None:
            raise MonitorNotFoundError(f"Monitor {monitor_id} not found")
        return monitor

    async def list_monitors(self, user_id: UUID) -> list[Monitor]:
        return await self._repo.list_monitors(user_id)

    async def list_monitors_enriched(self, user_id: UUID) -> list[dict]:
        """Enriched monitor list with run status, mention count, alert count."""
        return await self._repo.list_monitors_enriched(user_id)

    async def delete_monitor(self, monitor_id: UUID, user_id: UUID) -> bool:
        return await self._repo.delete_monitor(monitor_id, user_id)

    async def update_monitor(
        self,
        monitor_id: UUID,
        user_id: UUID,
        **fields: Any,
    ) -> Monitor:
        """Update monitor fields with IDOR check."""
        await self.get_monitor(monitor_id, user_id)
        updated = await self._repo.update_monitor(monitor_id, user_id, **fields)
        if updated is None:
            raise MonitorNotFoundError(f"Monitor {monitor_id} not found")
        return updated

    # ── Changelog (V2 self-optimizing refinement) ──

    async def get_changelog(
        self,
        monitor_id: UUID,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[MonitorChangelog], int]:
        """Get changelog entries with IDOR check."""
        await self.get_monitor(monitor_id, user_id)  # IDOR
        return await self._repo.get_changelog(monitor_id, limit=limit, offset=offset)

    _APPROVABLE_FIELDS = frozenset({"boolean_query", "keywords", "sources", "competitor_brands"})

    async def approve_changelog_entry(
        self,
        monitor_id: UUID,
        entry_id: UUID,
        user_id: UUID,
    ) -> MonitorChangelog:
        """Approve a pending changelog entry and apply its change."""
        await self.get_monitor(monitor_id, user_id)  # IDOR
        entry = await self._repo.update_changelog_status(entry_id, monitor_id, "applied")
        if entry is None:
            raise MonitorNotFoundError(f"Changelog entry {entry_id} not found or not pending")

        # Apply the change (only for approved fields)
        field = entry.change_detail.get("field")
        new_value = entry.change_detail.get("new_value")
        if field in self._APPROVABLE_FIELDS and new_value is not None:
            await self._repo.system_update_monitor(monitor_id, **{field: new_value})
            if field == "boolean_query":
                await self._repo.delete_cursors_for_monitor(monitor_id)
        return entry

    async def reject_changelog_entry(
        self,
        monitor_id: UUID,
        entry_id: UUID,
        user_id: UUID,
    ) -> MonitorChangelog:
        """Reject a pending changelog entry."""
        await self.get_monitor(monitor_id, user_id)  # IDOR
        entry = await self._repo.update_changelog_status(entry_id, monitor_id, "rejected")
        if entry is None:
            raise MonitorNotFoundError(f"Changelog entry {entry_id} not found or not pending")
        return entry

    async def ingest_mentions(
        self,
        monitor_id: UUID,
        raw_mentions: list[RawMention],
        source: DataSource,
        *,
        cursor_value: str | None = None,
    ) -> int:
        """System-level: batch ingest mentions with optional cursor advance.

        Callers MUST verify monitor ownership before calling.
        """
        # Cap batch size
        capped = raw_mentions[: self._settings.max_mentions_per_ingest]

        mention_tuples = [
            (
                rm.source.value,
                rm.source_id,
                rm.author_handle,
                rm.author_name,
                rm.content,
                rm.url,
                rm.published_at,
                rm.sentiment_score,
                rm.sentiment_label.value if rm.sentiment_label else None,
                rm.engagement_likes,
                rm.engagement_shares,
                rm.engagement_comments,
                rm.reach_estimate,
                rm.language,
                rm.geo_country,
                rm.media_urls,
                json.dumps(rm.metadata) if rm.metadata else '{}',
            )
            for rm in capped
        ]

        if cursor_value is not None:
            return await self._repo.insert_mentions_and_advance_cursor(
                monitor_id, mention_tuples, source, cursor_value
            )
        return await self._repo.insert_mentions(monitor_id, mention_tuples)

    async def get_mentions(
        self,
        user_id: UUID,
        monitor_id: UUID,
        *,
        source: DataSource | None = None,
        sentiment: SentimentLabel | None = None,
        sentiment_min: float | None = None,
        sentiment_max: float | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Mention]:
        limit = max(1, min(limit, 200))
        offset = max(0, offset)
        return await self._repo.get_mentions(
            user_id, monitor_id,
            source=source, sentiment=sentiment,
            sentiment_min=sentiment_min, sentiment_max=sentiment_max,
            date_from=date_from, date_to=date_to,
            limit=limit, offset=offset,
        )

    async def search_mentions(
        self,
        user_id: UUID,
        monitor_id: UUID,
        query: str,
        *,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Mention], int]:
        limit = max(1, min(limit, 200))
        offset = max(0, offset)
        return await self._repo.search_mentions(
            user_id, monitor_id, query,
            date_from=date_from, date_to=date_to,
            limit=limit, offset=offset,
        )

    async def query_mentions(
        self,
        user_id: UUID,
        monitor_id: UUID,
        *,
        q: str | None = None,
        source: DataSource | None = None,
        sentiment: SentimentLabel | None = None,
        intent: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        sort_by: str = "published_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Mention], int]:
        """Unified mention query with FTS, filters, sorting, and total count."""
        limit = max(1, min(limit, 200))
        offset = max(0, offset)
        # Validate sort_by
        if sort_by not in ("published_at", "engagement", "relevance"):
            sort_by = "published_at"
        if sort_order not in ("asc", "desc"):
            sort_order = "desc"
        return await self._repo.query_mentions(
            monitor_id, user_id,
            q=q, source=source, sentiment=sentiment, intent=intent,
            date_from=date_from, date_to=date_to,
            sort_by=sort_by, sort_order=sort_order,
            limit=limit, offset=offset,
        )

    async def enqueue_run(self, monitor: Monitor, trigger: str = "manual") -> None:
        """Enqueue an immediate monitor run with cooldown enforcement."""
        can_run = await self._repo.check_and_claim_run(
            monitor_id=monitor.id,
            cooldown_minutes=5,
            trigger=trigger,
        )
        if not can_run:
            raise MonitoringError("Monitor was run less than 5 minutes ago. Please wait.")

    async def get_monitor_with_stats(
        self, monitor_id: UUID, user_id: UUID,
    ) -> tuple[Monitor, int]:
        """Get monitor with mention_count populated."""
        monitor = await self._repo.get_monitor(monitor_id, user_id)
        if not monitor:
            raise MonitorNotFoundError(f"Monitor {monitor_id} not found")
        count = await self._repo.count_mentions(monitor_id)
        return monitor, count

    async def check_monitor_quota(self, user_id: UUID, max_monitors: int) -> None:
        """Enforce monitor creation quota. Raises MonitorLimitExceededError."""
        count = await self._repo.count_monitors(user_id)
        if count >= max_monitors:
            raise MonitorLimitExceededError(
                f"Monitor limit reached ({max_monitors})"
            )

    async def get_runs(
        self,
        monitor_id: UUID,
        user_id: UUID,
        limit: int = 25,
        offset: int = 0,
    ) -> list[MonitorRun]:
        """Get run history for a monitor (IDOR-safe)."""
        limit = max(1, min(limit, 100))
        offset = max(0, offset)
        return await self._repo.get_runs(monitor_id, user_id, limit, offset)

    async def check_discover_quota(self, user_id: UUID, daily_limit: int) -> None:
        """Enforce daily discover search quota. Raises MonitorLimitExceededError."""
        count = await self._repo.count_discover_searches_today(user_id)
        if count >= daily_limit:
            raise MonitorLimitExceededError(
                f"Daily discover limit reached ({daily_limit})"
            )
        await self._repo.record_discover_search(user_id)

    async def discover(
        self,
        query: str,
        sources: list[DataSource],
        *,
        limit: int = 25,
    ) -> DiscoverResult:
        """Ad-hoc discovery search routed through service layer.

        Delegates to discover_mentions() with the service's adapter registry.
        """
        return await discover_mentions(query, sources, self._fetchers, limit=limit)

    async def get_mention_aggregates(
        self,
        monitor_id: UUID,
        user_id: UUID,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> dict[str, Any]:
        """Get SQL-aggregated stats for a monitor."""
        return await self._repo.get_mention_aggregates(
            monitor_id, user_id, date_from=date_from, date_to=date_to,
        )

    # ── Alert rules (PR-068) ──

    async def create_alert_rule(
        self,
        monitor_id: UUID,
        user_id: UUID,
        rule_type: str,
        config: dict,
        webhook_url: str,
        cooldown_minutes: int,
        max_rules: int,
    ) -> AlertRule:
        """Create alert rule with quota enforcement."""
        await self.get_monitor(monitor_id, user_id)
        count = await self._repo.count_alert_rules(monitor_id)
        if count >= max_rules:
            raise AlertRuleLimitError(f"Maximum {max_rules} alert rules per monitor")
        validated_config = self._validate_spike_config(config)
        return await self._repo.create_alert_rule(
            monitor_id, user_id, rule_type, validated_config, webhook_url, cooldown_minutes
        )

    async def get_alert_rule(self, rule_id: UUID, user_id: UUID) -> AlertRule:
        """Get alert rule with IDOR check."""
        rule = await self._repo.get_alert_rule(rule_id, user_id)
        if rule is None:
            raise AlertRuleNotFoundError(f"Alert rule {rule_id} not found")
        return rule

    async def list_alert_rules(self, monitor_id: UUID, user_id: UUID) -> list[AlertRule]:
        return await self._repo.list_alert_rules(monitor_id, user_id)

    async def update_alert_rule(
        self, rule_id: UUID, user_id: UUID, **fields: Any,
    ) -> AlertRule:
        """PATCH semantics. Re-validate config if changed."""
        if "config" in fields and fields["config"] is not None:
            fields["config"] = self._validate_spike_config(fields["config"])
        updated = await self._repo.update_alert_rule(rule_id, user_id, **fields)
        if updated is None:
            raise AlertRuleNotFoundError(f"Alert rule {rule_id} not found")
        return updated

    async def delete_alert_rule(self, rule_id: UUID, user_id: UUID) -> bool:
        return await self._repo.delete_alert_rule(rule_id, user_id)

    async def list_alert_events(
        self,
        monitor_id: UUID,
        user_id: UUID,
        limit: int = 25,
        offset: int = 0,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[AlertEvent]:
        limit = max(1, min(limit, 100))
        offset = max(0, offset)
        return await self._repo.list_alert_events(
            monitor_id, user_id, limit, offset,
            date_from=date_from, date_to=date_to,
        )

    def _validate_spike_config(self, config: dict) -> dict:
        """Validate and normalize via SpikeConfig. Strips unknown keys."""
        validated = SpikeConfig(**config)
        return validated.model_dump()

    # ── Intelligence Layer (PR-071) ──

    async def sentiment_time_series(
        self,
        monitor_id: UUID,
        user_id: UUID,
        *,
        window: str = "7d",
        granularity: str = "1d",
    ) -> list[SentimentBucket]:
        """Query-time sentiment aggregation."""
        from .intelligence.sentiment import get_sentiment_time_series

        await self.get_monitor(monitor_id, user_id)  # IDOR check
        return await get_sentiment_time_series(
            self._repo, monitor_id, user_id,
            window=window, granularity=granularity,
        )

    async def get_sentiment_by_source(
        self,
        monitor_id: UUID,
        user_id: UUID,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[SourceSentiment]:
        """Per-source sentiment breakdown for cross-signal anomaly detection."""
        await self.get_monitor(monitor_id, user_id)  # IDOR check
        return await self._repo.get_sentiment_by_source(
            monitor_id, date_from=date_from, date_to=date_to,
        )

    async def classify_intents(
        self,
        monitor_id: UUID,
        user_id: UUID,
        *,
        mention_ids: list[UUID] | None = None,
        limit: int = 100,
    ) -> int:
        """Classify intents for unclassified mentions. Returns count classified."""
        if self._intent_classifier is None:
            raise RuntimeError("Intent classifier not configured")

        await self.get_monitor(monitor_id, user_id)  # IDOR check

        # Check daily cap
        today = date.today()
        daily_count = await self._repo.get_daily_classification_count(monitor_id, today)
        remaining = self._settings.intent_daily_cap - daily_count
        if remaining <= 0:
            raise ClassificationCapExceededError(
                f"Daily classification limit reached ({self._settings.intent_daily_cap}/monitor)"
            )

        if mention_ids:
            mentions = await self._repo.get_mentions_by_ids(monitor_id, mention_ids)
            # Filter to only unclassified
            mentions = [m for m in mentions if m.intent is None]
        else:
            mentions = await self._repo.get_unclassified_mentions(
                monitor_id, user_id, limit=min(limit, remaining)
            )

        if not mentions:
            return 0

        # Classify
        results = await self._intent_classifier.classify_batch(mentions[:remaining])

        if results:
            updates = [(mid, intent) for mid, intent in results.items()]
            await self._repo.update_mention_intents(updates)

        return len(results)

    async def get_share_of_voice(
        self,
        monitor_id: UUID,
        user_id: UUID,
        *,
        window_days: int = 30,
    ) -> list[ShareOfVoiceEntry]:
        """Calculate share of voice vs competitors."""
        from .intelligence.share_of_voice import calculate_sov

        monitor = await self.get_monitor(monitor_id, user_id)
        return await calculate_sov(
            self._repo, monitor_id, user_id,
            monitor_name=monitor.name,
            competitor_brands=monitor.competitor_brands,
            window_days=window_days,
        )

    async def get_trends_correlation(
        self,
        monitor_id: UUID,
        user_id: UUID,
        *,
        window: str = "30d",
    ) -> TrendsCorrelationResult:
        """Correlate Google Trends interest with mention volume."""
        from .intelligence.trends_correlation import get_trends_correlation

        monitor = await self.get_monitor(monitor_id, user_id)  # IDOR check
        keyword = monitor.keywords[0] if monitor.keywords else monitor.name
        return await get_trends_correlation(
            self._repo, monitor_id, user_id,
            keyword=keyword, window=window,
        )

    async def save_mentions_to_workspace(
        self,
        monitor_id: UUID,
        user_id: UUID,
        collection_id: UUID,
        *,
        mention_ids: list[UUID] | None = None,
        annotations: dict[str, str] | None = None,
        limit: int = 500,
    ) -> int:
        """Save mentions to a workspace collection. Returns count saved."""
        if self._workspace_bridge is None:
            raise RuntimeError("Workspace bridge not configured")

        await self.get_monitor(monitor_id, user_id)  # IDOR check

        if mention_ids:
            mentions = await self._repo.get_mentions_by_ids(monitor_id, mention_ids)
        else:
            mentions = await self.get_mentions(
                user_id, monitor_id, limit=min(limit, self._settings.workspace_save_max)
            )

        if not mentions:
            return 0

        # Cap at workspace_save_max
        mentions = mentions[:self._settings.workspace_save_max]
        return await self._workspace_bridge.save_mentions(mentions, collection_id, annotations=annotations)
