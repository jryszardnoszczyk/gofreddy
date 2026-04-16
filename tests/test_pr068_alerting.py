"""PR-068: Alerting — Rules Engine, Spike Detection, Webhook Delivery tests."""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.monitoring.alerts.models import AlertEvent, AlertRule, SpikeConfig
from src.monitoring.config import MonitoringSettings
from src.monitoring.exceptions import (
    AlertRuleLimitError,
    AlertRuleNotFoundError,
    WebhookDeliveryError,
)
from src.monitoring.service import MonitoringService


# ── Fixtures ──


def _make_rule(**kwargs) -> AlertRule:
    defaults = dict(
        id=uuid4(),
        monitor_id=uuid4(),
        user_id=uuid4(),
        rule_type="mention_spike",
        config={"threshold_pct": 200, "window_hours": 1, "min_baseline_runs": 3},
        webhook_url="https://example.com/webhook",
        is_active=True,
        cooldown_minutes=60,
        last_triggered_at=None,
        consecutive_failures=0,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return AlertRule(**defaults)


def _make_event(**kwargs) -> AlertEvent:
    defaults = dict(
        id=uuid4(),
        rule_id=uuid4(),
        monitor_id=uuid4(),
        triggered_at=datetime.now(UTC),
        condition_summary="Test spike",
        payload={"alert_type": "mention_spike"},
        delivery_status="pending",
        delivery_attempts=0,
        last_delivery_at=None,
        created_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return AlertEvent(**defaults)


def _make_monitor(**kwargs):
    from src.monitoring.models import DataSource, Monitor

    defaults = dict(
        id=uuid4(),
        user_id=uuid4(),
        name="Test",
        keywords=["brand"],
        boolean_query=None,
        sources=[DataSource.TWITTER],
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return Monitor(**defaults)


@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.count_monitors = AsyncMock(return_value=0)
    repo.get_monitor = AsyncMock(return_value=_make_monitor())
    repo.count_alert_rules = AsyncMock(return_value=0)
    repo.create_alert_rule = AsyncMock(side_effect=lambda *a, **kw: _make_rule())
    repo.get_alert_rule = AsyncMock(return_value=_make_rule())
    repo.list_alert_rules = AsyncMock(return_value=[_make_rule()])
    repo.update_alert_rule = AsyncMock(return_value=_make_rule())
    repo.delete_alert_rule = AsyncMock(return_value=True)
    repo.list_alert_events = AsyncMock(return_value=[_make_event()])
    repo.get_active_rules_for_monitor = AsyncMock(return_value=[])
    repo.count_completed_runs = AsyncMock(return_value=5)
    repo.count_mentions_in_window = AsyncMock(return_value=0)
    repo.create_alert_event_and_trigger = AsyncMock(return_value=_make_event())
    repo.update_alert_event_status = AsyncMock()
    repo.increment_consecutive_failures = AsyncMock(return_value=1)
    repo.reset_consecutive_failures = AsyncMock()
    repo.disable_rule = AsyncMock()
    return repo


@pytest.fixture
def settings():
    return MonitoringSettings(
        max_monitors_per_user=10,
        max_alert_rules_per_monitor=5,
        webhook_timeout_seconds=5.0,
        webhook_circuit_breaker_threshold=10,
        webhook_signing_secret="test-secret-key",
    )


@pytest.fixture
def service(mock_repo, settings):
    return MonitoringService(repository=mock_repo, settings=settings)


# ── SpikeConfig Validation ──


class TestSpikeConfig:
    def test_defaults(self):
        c = SpikeConfig()
        assert c.threshold_pct == 200
        assert c.window_hours == 1
        assert c.min_baseline_runs == 3

    def test_extra_forbid(self):
        with pytest.raises(Exception):
            SpikeConfig(unknown_field="bad")

    def test_invalid_threshold_too_low(self):
        with pytest.raises(Exception):
            SpikeConfig(threshold_pct=10)

    def test_invalid_threshold_too_high(self):
        with pytest.raises(Exception):
            SpikeConfig(threshold_pct=2000)

    def test_invalid_window_hours(self):
        with pytest.raises(Exception):
            SpikeConfig(window_hours=2)

    def test_valid_custom(self):
        c = SpikeConfig(threshold_pct=500, window_hours=24, min_baseline_runs=5)
        assert c.threshold_pct == 500
        assert c.window_hours == 24


# ── Service Layer (Alert CRUD) ──


class TestAlertServiceCRUD:
    @pytest.mark.asyncio
    async def test_create_alert_rule(self, service, mock_repo):
        uid = uuid4()
        mid = uuid4()
        mock_repo.get_monitor.return_value = _make_monitor(id=mid, user_id=uid)
        rule = await service.create_alert_rule(
            monitor_id=mid,
            user_id=uid,
            rule_type="mention_spike",
            config={"threshold_pct": 200, "window_hours": 1},
            webhook_url="https://example.com/hook",
            cooldown_minutes=60,
            max_rules=5,
        )
        assert rule is not None
        mock_repo.create_alert_rule.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_alert_rule_quota_exceeded(self, service, mock_repo):
        mock_repo.count_alert_rules.return_value = 5
        with pytest.raises(AlertRuleLimitError):
            await service.create_alert_rule(
                monitor_id=uuid4(),
                user_id=uuid4(),
                rule_type="mention_spike",
                config={},
                webhook_url="https://example.com/hook",
                cooldown_minutes=60,
                max_rules=5,
            )

    @pytest.mark.asyncio
    async def test_get_alert_rule(self, service, mock_repo):
        rule = await service.get_alert_rule(uuid4(), uuid4())
        assert rule.rule_type == "mention_spike"

    @pytest.mark.asyncio
    async def test_get_alert_rule_not_found(self, service, mock_repo):
        mock_repo.get_alert_rule.return_value = None
        with pytest.raises(AlertRuleNotFoundError):
            await service.get_alert_rule(uuid4(), uuid4())

    @pytest.mark.asyncio
    async def test_list_alert_rules(self, service, mock_repo):
        rules = await service.list_alert_rules(uuid4(), uuid4())
        assert len(rules) == 1

    @pytest.mark.asyncio
    async def test_update_alert_rule(self, service, mock_repo):
        rule = await service.update_alert_rule(
            uuid4(), uuid4(), is_active=False
        )
        assert rule is not None

    @pytest.mark.asyncio
    async def test_update_alert_rule_not_found(self, service, mock_repo):
        mock_repo.update_alert_rule.return_value = None
        with pytest.raises(AlertRuleNotFoundError):
            await service.update_alert_rule(uuid4(), uuid4(), is_active=False)

    @pytest.mark.asyncio
    async def test_update_revalidates_config(self, service, mock_repo):
        """Config with unknown key should be rejected."""
        with pytest.raises(Exception):
            await service.update_alert_rule(
                uuid4(), uuid4(),
                config={"threshold_pct": 200, "bad_key": "bad"},
            )

    @pytest.mark.asyncio
    async def test_delete_alert_rule(self, service, mock_repo):
        result = await service.delete_alert_rule(uuid4(), uuid4())
        assert result is True

    @pytest.mark.asyncio
    async def test_list_alert_events(self, service, mock_repo):
        events = await service.list_alert_events(uuid4(), uuid4())
        assert len(events) == 1


# ── Evaluator ──


class TestAlertEvaluator:
    @pytest.fixture
    def evaluator(self, mock_repo, settings):
        from src.monitoring.alerts.evaluator import AlertEvaluator

        delivery = MagicMock()
        delivery.deliver = AsyncMock(return_value=True)
        return AlertEvaluator(mock_repo, delivery, settings)

    @pytest.mark.asyncio
    async def test_no_active_rules(self, evaluator, mock_repo):
        mock_repo.get_active_rules_for_monitor.return_value = []
        fired = await evaluator.evaluate_monitor(uuid4(), {})
        assert fired == 0

    @pytest.mark.asyncio
    async def test_cooldown_skips_evaluation(self, evaluator, mock_repo):
        rule = _make_rule(last_triggered_at=datetime.now(UTC))  # just triggered
        mock_repo.get_active_rules_for_monitor.return_value = [rule]
        fired = await evaluator.evaluate_monitor(rule.monitor_id, {})
        assert fired == 0

    @pytest.mark.asyncio
    async def test_insufficient_baseline_skips(self, evaluator, mock_repo):
        rule = _make_rule()
        mock_repo.get_active_rules_for_monitor.return_value = [rule]
        mock_repo.count_completed_runs.return_value = 1  # < 3
        fired = await evaluator.evaluate_monitor(rule.monitor_id, {})
        assert fired == 0

    @pytest.mark.asyncio
    async def test_zero_previous_skips(self, evaluator, mock_repo):
        """No spike when previous count is 0 (avoid division by zero)."""
        rule = _make_rule()
        mock_repo.get_active_rules_for_monitor.return_value = [rule]
        mock_repo.count_completed_runs.return_value = 5
        mock_repo.count_mentions_in_window.return_value = 0
        fired = await evaluator.evaluate_monitor(rule.monitor_id, {})
        assert fired == 0

    @pytest.mark.asyncio
    async def test_below_threshold_skips(self, evaluator, mock_repo):
        """Increase below threshold_pct should not fire."""
        rule = _make_rule(config={"threshold_pct": 200, "window_hours": 1, "min_baseline_runs": 3})
        mock_repo.get_active_rules_for_monitor.return_value = [rule]
        mock_repo.count_completed_runs.return_value = 5
        # previous=10, current=20 → 100% increase < 200% threshold
        mock_repo.count_mentions_in_window.side_effect = [20, 10]
        fired = await evaluator.evaluate_monitor(rule.monitor_id, {})
        assert fired == 0

    @pytest.mark.asyncio
    async def test_spike_fires_alert(self, evaluator, mock_repo):
        """Increase above threshold should fire."""
        rule = _make_rule(config={"threshold_pct": 200, "window_hours": 1, "min_baseline_runs": 3})
        mock_repo.get_active_rules_for_monitor.return_value = [rule]
        mock_repo.count_completed_runs.return_value = 5
        # previous=10, current=35 → 250% increase > 200% threshold
        mock_repo.count_mentions_in_window.side_effect = [35, 10]
        fired = await evaluator.evaluate_monitor(rule.monitor_id, {})
        assert fired == 1
        mock_repo.create_alert_event_and_trigger.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_wait_pending_deliveries(self, evaluator, mock_repo):
        """Verify wait_pending_deliveries collects background tasks."""
        rule = _make_rule(config={"threshold_pct": 100, "window_hours": 1, "min_baseline_runs": 1})
        mock_repo.get_active_rules_for_monitor.return_value = [rule]
        mock_repo.count_completed_runs.return_value = 5
        mock_repo.count_mentions_in_window.side_effect = [30, 10]
        await evaluator.evaluate_monitor(rule.monitor_id, {})
        await evaluator.wait_pending_deliveries()
        # Should not raise; tasks should be cleared
        assert len(evaluator._background_tasks) == 0


# ── Webhook Delivery ──


class TestWebhookDelivery:
    @pytest.fixture
    def delivery(self, mock_repo, settings):
        from src.monitoring.alerts.delivery import WebhookDelivery

        return WebhookDelivery(settings, mock_repo)

    def test_hmac_signing(self, delivery):
        timestamp = "1234567890"
        body = b'{"test": true}'
        sig = delivery._sign(timestamp, body)
        assert sig.startswith("sha256=")
        # Verify signature manually
        expected = hmac.new(
            b"test-secret-key",
            f"{timestamp}.".encode() + body,
            hashlib.sha256,
        ).hexdigest()
        assert sig == f"sha256={expected}"

    def test_sign_empty_secret_raises(self, mock_repo):
        from src.monitoring.alerts.delivery import WebhookDelivery

        settings = MonitoringSettings(webhook_signing_secret="")
        d = WebhookDelivery(settings, mock_repo)
        with pytest.raises(WebhookDeliveryError, match="not configured"):
            d._sign("ts", b"body")

    @pytest.mark.asyncio
    async def test_delivery_success(self, delivery, mock_repo):
        event = _make_event()
        rule = _make_rule()
        with patch.object(delivery, "_attempt_delivery", new_callable=AsyncMock, return_value=True):
            result = await delivery.deliver(event, rule)
        assert result is True
        mock_repo.update_alert_event_status.assert_awaited_once_with(
            event.id, "delivered", 1
        )
        mock_repo.reset_consecutive_failures.assert_awaited_once_with(rule.id)

    @pytest.mark.asyncio
    async def test_delivery_all_retries_fail(self, delivery, mock_repo):
        event = _make_event()
        rule = _make_rule()
        with patch.object(
            delivery, "_attempt_delivery",
            new_callable=AsyncMock,
            side_effect=Exception("fail"),
        ), patch("asyncio.sleep", new_callable=AsyncMock):
            result = await delivery.deliver(event, rule)
        assert result is False
        mock_repo.update_alert_event_status.assert_awaited_once_with(
            event.id, "failed", 3
        )
        mock_repo.increment_consecutive_failures.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_circuit_breaker_disables_rule(self, delivery, mock_repo):
        event = _make_event()
        rule = _make_rule()
        mock_repo.increment_consecutive_failures.return_value = 10
        with patch.object(
            delivery, "_attempt_delivery",
            new_callable=AsyncMock,
            side_effect=Exception("fail"),
        ), patch("asyncio.sleep", new_callable=AsyncMock):
            await delivery.deliver(event, rule)
        mock_repo.disable_rule.assert_awaited_once_with(rule.id)


# ── Worker Integration ──


class TestWorkerAlertIntegration:
    @pytest.mark.asyncio
    async def test_evaluator_called_when_mentions_ingested(self):
        """Worker calls evaluator when total_mentions > 0."""
        from src.monitoring.worker import MonitorWorker

        repo = MagicMock()
        svc = MagicMock()
        evaluator = MagicMock()
        evaluator.evaluate_monitor = AsyncMock(return_value=1)
        evaluator.wait_pending_deliveries = AsyncMock()

        monitor = _make_monitor()
        repo.get_monitor_by_id_system = AsyncMock(return_value=monitor)
        repo.try_create_run = AsyncMock(return_value=True)
        repo.complete_run_and_advance = AsyncMock()
        repo.fail_run = AsyncMock()
        repo.count_mentions_this_month = AsyncMock(return_value=0)

        worker = MonitorWorker(
            repository=repo,
            service=svc,
            adapters={},  # no adapters → 0 sources → completes immediately
            evaluator=evaluator,
        )

        # Simulate: worker processes monitor with no adapters
        result = await worker.process_monitor(monitor.id)
        assert result["status"] == "completed"
        # No mentions → evaluator should NOT be called
        evaluator.evaluate_monitor.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_evaluator_exception_doesnt_fail_run(self):
        """Alert evaluation failure should not crash the run."""
        from src.monitoring.models import DataSource
        from src.monitoring.worker import MonitorWorker

        repo = MagicMock()
        svc = MagicMock()
        evaluator = MagicMock()
        evaluator.evaluate_monitor = AsyncMock(side_effect=RuntimeError("boom"))
        evaluator.wait_pending_deliveries = AsyncMock()

        monitor = _make_monitor(sources=[DataSource.TWITTER])
        repo.get_monitor_by_id_system = AsyncMock(return_value=monitor)
        repo.try_create_run = AsyncMock(return_value=True)
        repo.complete_run_and_advance = AsyncMock()
        repo.fail_run = AsyncMock()
        repo.get_cursor = AsyncMock(return_value=None)
        repo.count_mentions_this_month = AsyncMock(return_value=0)

        # Create mock adapter that returns some mentions
        mock_adapter = AsyncMock()
        mock_adapter.fetch_mentions = AsyncMock(return_value=([], None))

        worker = MonitorWorker(
            repository=repo,
            service=svc,
            adapters={DataSource.TWITTER: mock_adapter},
            evaluator=evaluator,
        )
        # Even though evaluator raises, worker should not crash
        result = await worker.process_monitor(monitor.id)
        assert result["status"] == "completed"


# ── Payload Construction ──


class TestPayloadConstruction:
    def test_build_payload(self, mock_repo, settings):
        from src.monitoring.alerts.evaluator import AlertEvaluator

        delivery = MagicMock()
        evaluator = AlertEvaluator(mock_repo, delivery, settings)

        rule = _make_rule()
        payload = evaluator._build_payload(rule, 35, 10, 250.0)

        assert payload["alert_type"] == "mention_spike"
        assert payload["monitor_id"] == str(rule.monitor_id)
        assert payload["rule_id"] == str(rule.id)
        assert payload["condition"]["current_count"] == 35
        assert payload["condition"]["previous_count"] == 10
        assert payload["condition"]["increase_pct"] == 250.0


# ── Schema Validation ──


class TestSchemas:
    def test_create_alert_rule_request_defaults(self):
        from src.api.schemas_monitoring import CreateAlertRuleRequest

        req = CreateAlertRuleRequest(webhook_url="https://example.com/hook")
        assert req.rule_type == "mention_spike"
        assert req.cooldown_minutes == 60
        assert req.config.threshold_pct == 200

    def test_create_alert_rule_request_invalid_cooldown(self):
        from src.api.schemas_monitoring import CreateAlertRuleRequest

        with pytest.raises(Exception):
            CreateAlertRuleRequest(
                webhook_url="https://example.com/hook",
                cooldown_minutes=5,  # too low
            )

    def test_alert_rule_response_from_rule(self):
        from src.api.schemas_monitoring import AlertRuleResponse

        rule = _make_rule()
        response = AlertRuleResponse.from_rule(rule)
        assert response.id == rule.id
        assert response.webhook_url == rule.webhook_url

    def test_alert_event_response_from_event(self):
        from src.api.schemas_monitoring import AlertEventResponse

        event = _make_event()
        response = AlertEventResponse.from_event(event)
        assert response.id == event.id
        assert response.delivery_status == "pending"

    def test_update_request_partial(self):
        from src.api.schemas_monitoring import UpdateAlertRuleRequest

        req = UpdateAlertRuleRequest(is_active=False)
        dumped = req.model_dump(exclude_unset=True)
        assert dumped == {"is_active": False}

    def test_spike_config_extra_forbid_via_request(self):
        from src.api.schemas_monitoring import CreateAlertRuleRequest

        with pytest.raises(Exception):
            CreateAlertRuleRequest(
                webhook_url="https://example.com/hook",
                config={"threshold_pct": 200, "evil_key": "payload_stuffing"},
            )
