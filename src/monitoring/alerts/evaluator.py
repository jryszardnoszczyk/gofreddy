"""Alert evaluator — checks rules after each monitor ingestion run."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any
from uuid import UUID

if TYPE_CHECKING:
    from ..config import MonitoringSettings
    from ..repository import PostgresMonitoringRepository
    from .delivery import WebhookDelivery
    from .models import AlertRule

logger = logging.getLogger(__name__)


class AlertEvaluator:
    """Evaluates alert rules after each monitor ingestion run."""

    def __init__(
        self,
        repository: PostgresMonitoringRepository,
        delivery: WebhookDelivery,
        settings: MonitoringSettings,
    ) -> None:
        self._repo = repository
        self._delivery = delivery
        self._settings = settings
        self._background_tasks: set[asyncio.Task] = set()

    async def wait_pending_deliveries(self) -> None:
        """Await all background delivery tasks. Call before worker returns."""
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
            self._background_tasks.clear()

    async def evaluate_monitor(self, monitor_id: UUID, run_summary: dict) -> int:
        """Evaluate all active rules for a monitor. Returns count of alerts fired."""
        rules = await self._repo.get_active_rules_for_monitor(monitor_id)
        fired = 0
        for rule in rules:
            if await self._should_evaluate(rule):
                if await self._evaluate_rule(rule, run_summary):
                    fired += 1
        return fired

    async def _should_evaluate(self, rule: AlertRule) -> bool:
        """Check cooldown and minimum baseline."""
        # 1. Cooldown check
        if rule.last_triggered_at:
            cooldown_end = rule.last_triggered_at + timedelta(minutes=rule.cooldown_minutes)
            if datetime.now(UTC) < cooldown_end:
                return False
        # 2. Minimum baseline check
        min_runs = rule.config.get("min_baseline_runs", 3)
        completed = await self._repo.count_completed_runs(rule.monitor_id)
        return completed >= min_runs

    async def _evaluate_rule(self, rule: AlertRule, run_summary: dict) -> bool:
        """Evaluate spike condition. Returns True if alert was fired."""
        if rule.rule_type != "mention_spike":
            return False

        threshold_pct = rule.config.get("threshold_pct", 200)
        window_hours = rule.config.get("window_hours", 1)

        now = datetime.now(UTC)
        current_start = now - timedelta(hours=window_hours)
        previous_start = current_start - timedelta(hours=window_hours)

        current_count = await self._repo.count_mentions_in_window(
            rule.monitor_id, current_start, now
        )
        previous_count = await self._repo.count_mentions_in_window(
            rule.monitor_id, previous_start, current_start
        )

        # Avoid division by zero — if previous is 0, no spike possible
        if previous_count == 0:
            return False

        increase_pct = ((current_count - previous_count) / previous_count) * 100
        if increase_pct < threshold_pct:
            return False

        # Spike detected — create event + update trigger atomically
        payload = self._build_payload(rule, current_count, previous_count, increase_pct)
        condition_summary = (
            f"Mentions increased {increase_pct:.0f}% "
            f"({previous_count} -> {current_count}) in {window_hours}h window"
        )
        event = await self._repo.create_alert_event_and_trigger(
            rule.id, rule.monitor_id, condition_summary, payload
        )

        # Fire-and-forget delivery — store task to prevent GC
        task = asyncio.create_task(self._delivery.deliver(event, rule))
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        return True

    def _build_payload(
        self,
        rule: AlertRule,
        current_count: int,
        previous_count: int,
        increase_pct: float,
    ) -> dict[str, Any]:
        """Build webhook payload with alert details."""
        return {
            "alert_type": "mention_spike",
            "monitor_id": str(rule.monitor_id),
            "rule_id": str(rule.id),
            "triggered_at": datetime.now(UTC).isoformat(),
            "condition": {
                "threshold_pct": rule.config.get("threshold_pct", 200),
                "window_hours": rule.config.get("window_hours", 1),
                "current_count": current_count,
                "previous_count": previous_count,
                "increase_pct": round(increase_pct, 1),
            },
        }
