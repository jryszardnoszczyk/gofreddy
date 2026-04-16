"""Tests for PR-067: Scheduled Monitoring — dispatcher, worker, query sanitizer, billing."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.monitoring.models import DataSource, Monitor, MonitorRun, MonitorSourceCursor
from src.monitoring.query_sanitizer import (
    QueryValidationError,
    sanitize_for_apify,
    sanitize_for_newsdata,
    sanitize_for_xpoz,
)


# ── Helpers ──


def _make_monitor(**kwargs):
    defaults = dict(
        id=uuid4(),
        user_id=uuid4(),
        name="Test Monitor",
        keywords=["brand"],
        boolean_query=None,
        sources=[DataSource.TWITTER, DataSource.NEWSDATA],
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        next_run_at=datetime.now(timezone.utc),
    )
    defaults.update(kwargs)
    return Monitor(**defaults)


def _make_run(**kwargs):
    defaults = dict(
        id=uuid4(),
        monitor_id=uuid4(),
        started_at=datetime.now(timezone.utc),
        completed_at=None,
        status="running",
        mentions_ingested=0,
        sources_succeeded=0,
        sources_failed=0,
        error_details=None,
    )
    defaults.update(kwargs)
    return MonitorRun(**defaults)


# ── Query Sanitizer Tests ──


class TestQuerySanitizer:
    def test_empty_raises(self):
        with pytest.raises(QueryValidationError, match="empty"):
            sanitize_for_newsdata("")

    def test_whitespace_only_raises(self):
        with pytest.raises(QueryValidationError, match="empty"):
            sanitize_for_xpoz("   ")

    def test_null_bytes_raises(self):
        with pytest.raises(QueryValidationError, match="null bytes"):
            sanitize_for_apify("hello\x00world")

    def test_over_max_length_raises(self):
        with pytest.raises(QueryValidationError, match="512"):
            sanitize_for_xpoz("x" * 513)

    def test_newsdata_truncates_to_256(self):
        result = sanitize_for_newsdata("a" * 300)
        assert len(result) == 256

    def test_newsdata_strips_boolean_operators(self):
        result = sanitize_for_newsdata("foo AND bar OR baz NOT qux")
        assert "AND" not in result
        assert "OR" not in result
        assert "NOT" not in result
        assert "foo" in result
        assert "bar" in result

    def test_normal_keywords_pass_through(self):
        assert sanitize_for_xpoz("Nike shoes") == "Nike shoes"
        assert sanitize_for_apify("coffee brand") == "coffee brand"
        assert sanitize_for_newsdata("test query") == "test query"

    def test_control_chars_stripped(self):
        result = sanitize_for_xpoz("hello\x01\x02world")
        assert result == "helloworld"


# ── Dispatcher Tests ──


class TestMonitorDispatcher:
    @pytest.fixture
    def mock_repo(self):
        repo = MagicMock()
        repo.mark_stale_runs_failed = AsyncMock(return_value=0)
        repo.get_due_monitors = AsyncMock(return_value=[])
        repo.try_create_run = AsyncMock(return_value=True)
        repo.fail_run = AsyncMock()
        return repo

    @pytest.fixture
    def mock_task_client(self):
        client = MagicMock()
        client.enqueue_monitor_run = AsyncMock(return_value="mock-task")
        return client

    @pytest.fixture
    def dispatcher(self, mock_repo, mock_task_client):
        from src.monitoring.dispatcher import MonitorDispatcher

        return MonitorDispatcher(
            repository=mock_repo, task_client=mock_task_client
        )

    @pytest.mark.asyncio
    async def test_dispatch_no_due_monitors(self, dispatcher, mock_repo):
        result = await dispatcher.dispatch()
        assert result["dispatched"] == 0
        assert result["total_due"] == 0
        mock_repo.mark_stale_runs_failed.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_dispatch_happy_path(
        self, dispatcher, mock_repo, mock_task_client
    ):
        monitors = [_make_monitor(), _make_monitor()]
        mock_repo.get_due_monitors.return_value = monitors
        result = await dispatcher.dispatch()
        assert result["dispatched"] == 2
        assert result["skipped"] == 0
        assert mock_task_client.enqueue_monitor_run.await_count == 2

    @pytest.mark.asyncio
    async def test_dispatch_skips_already_running(
        self, dispatcher, mock_repo, mock_task_client
    ):
        monitors = [_make_monitor()]
        mock_repo.get_due_monitors.return_value = monitors
        mock_repo.try_create_run.return_value = False  # Already running
        result = await dispatcher.dispatch()
        assert result["dispatched"] == 0
        assert result["skipped"] == 1
        mock_task_client.enqueue_monitor_run.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_dispatch_handles_enqueue_failure(
        self, dispatcher, mock_repo, mock_task_client
    ):
        monitors = [_make_monitor()]
        mock_repo.get_due_monitors.return_value = monitors
        mock_task_client.enqueue_monitor_run.side_effect = RuntimeError("nope")
        result = await dispatcher.dispatch()
        assert result["dispatched"] == 0
        assert result["skipped"] == 1
        mock_repo.fail_run.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_stale_recovery(self, dispatcher, mock_repo):
        mock_repo.mark_stale_runs_failed.return_value = 3
        result = await dispatcher.dispatch()
        assert result["stale_recovered"] == 3


# ── Worker Tests ──


class TestMonitorWorker:
    @pytest.fixture
    def mock_repo(self):
        repo = MagicMock()
        repo.get_monitor_by_id_system = AsyncMock()
        repo.fail_run = AsyncMock()
        repo.complete_run_and_advance = AsyncMock()
        repo.get_cursor = AsyncMock(return_value=None)
        repo.count_mentions_this_month = AsyncMock(return_value=0)
        return repo

    @pytest.fixture
    def mock_service(self):
        svc = MagicMock()
        svc.ingest_mentions = AsyncMock(return_value=10)
        return svc

    @pytest.fixture
    def mock_adapter(self):
        adapter = AsyncMock()
        adapter.fetch_mentions = AsyncMock(return_value=([], None))
        return adapter

    @pytest.fixture
    def worker(self, mock_repo, mock_service, mock_adapter):
        from src.monitoring.worker import MonitorWorker

        return MonitorWorker(
            repository=mock_repo,
            service=mock_service,
            adapters={DataSource.TWITTER: mock_adapter},
        )

    @pytest.mark.asyncio
    async def test_monitor_not_found(self, worker, mock_repo):
        mock_repo.get_monitor_by_id_system.return_value = None
        result = await worker.process_monitor(uuid4())
        assert result["status"] == "skipped"
        assert result["reason"] == "not_found"
        mock_repo.fail_run.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_inactive_monitor(self, worker, mock_repo):
        monitor = _make_monitor(is_active=False)
        mock_repo.get_monitor_by_id_system.return_value = monitor
        result = await worker.process_monitor(monitor.id)
        assert result["status"] == "skipped"
        assert result["reason"] == "inactive"

    @pytest.mark.asyncio
    async def test_no_available_adapters(self, worker, mock_repo):
        # Monitor has NEWSDATA source but worker only has TWITTER adapter
        monitor = _make_monitor(sources=[DataSource.NEWSDATA])
        mock_repo.get_monitor_by_id_system.return_value = monitor
        result = await worker.process_monitor(monitor.id)
        assert result["status"] == "completed"
        assert result["reason"] == "no_sources"

    @pytest.mark.asyncio
    async def test_happy_path_with_mentions(
        self, worker, mock_repo, mock_service, mock_adapter
    ):
        from src.monitoring.models import RawMention

        monitor = _make_monitor(sources=[DataSource.TWITTER])
        mock_repo.get_monitor_by_id_system.return_value = monitor
        raw = [RawMention(source=DataSource.TWITTER, source_id="1")]
        mock_adapter.fetch_mentions.return_value = (raw, None)
        mock_service.ingest_mentions.return_value = 1

        result = await worker.process_monitor(monitor.id)
        assert result["status"] == "completed"
        assert result["mentions_ingested"] == 1
        assert result["sources_succeeded"] == 1
        mock_repo.complete_run_and_advance.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_source_failure_isolation(
        self, worker, mock_repo, mock_service
    ):
        """One source failing shouldn't prevent others from completing."""
        failing_adapter = AsyncMock()
        failing_adapter.fetch_mentions.side_effect = RuntimeError("API down")

        ok_adapter = AsyncMock()
        ok_adapter.fetch_mentions.return_value = ([], None)

        from src.monitoring.worker import MonitorWorker

        worker = MonitorWorker(
            repository=mock_repo,
            service=mock_service,
            adapters={
                DataSource.TWITTER: failing_adapter,
                DataSource.INSTAGRAM: ok_adapter,
            },
        )

        monitor = _make_monitor(
            sources=[DataSource.TWITTER, DataSource.INSTAGRAM]
        )
        mock_repo.get_monitor_by_id_system.return_value = monitor

        result = await worker.process_monitor(monitor.id)
        assert result["status"] == "completed"
        assert result["sources_failed"] == 1
        assert result["sources_succeeded"] == 1

        # Error details must contain a safe error code, not the raw exception
        call_kwargs = mock_repo.complete_run_and_advance.call_args
        error_details = call_kwargs.kwargs.get("error_details") or call_kwargs[1].get("error_details")
        assert error_details is not None
        assert error_details["twitter"] == "source_error"
        assert "API down" not in str(error_details)

    @pytest.mark.asyncio
    async def test_quota_exceeded(self, worker, mock_repo):
        monitor = _make_monitor(sources=[DataSource.TWITTER])
        mock_repo.get_monitor_by_id_system.return_value = monitor
        mock_repo.count_mentions_this_month.return_value = 999_999

        result = await worker.process_monitor(monitor.id)
        assert result["status"] == "skipped"
        assert result["reason"] == "quota_exceeded"

    @pytest.mark.asyncio
    async def test_pro_user_gets_pro_quota(self, mock_repo, mock_service, mock_adapter):
        """Pro users should get 500K mention limit, not FREE tier 5K."""
        from src.billing.models import Subscription
        from src.billing.tiers import Tier
        from src.monitoring.worker import MonitorWorker

        mock_billing_repo = MagicMock()
        mock_billing_repo.get_subscription = AsyncMock(
            return_value=Subscription(
                id=uuid4(),
                user_id=uuid4(),
                stripe_subscription_id="sub_123",
                tier=Tier.PRO,
                status="active",
                current_period_start=datetime.now(timezone.utc),
                current_period_end=datetime.now(timezone.utc),
                cancel_at_period_end=False,
            )
        )

        worker = MonitorWorker(
            repository=mock_repo,
            service=mock_service,
            adapters={DataSource.TWITTER: mock_adapter},
            billing_repo=mock_billing_repo,
        )

        monitor = _make_monitor(sources=[DataSource.TWITTER])
        mock_repo.get_monitor_by_id_system.return_value = monitor
        # 10K mentions — exceeds FREE (5K) but within PRO (500K)
        mock_repo.count_mentions_this_month.return_value = 10_000

        result = await worker.process_monitor(monitor.id)
        # Should NOT be quota-exceeded for a Pro user
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_free_user_throttled_at_5k(self, mock_repo, mock_service, mock_adapter):
        """Free users should be stopped at 5K mentions."""
        from src.monitoring.worker import MonitorWorker

        mock_billing_repo = MagicMock()
        mock_billing_repo.get_subscription = AsyncMock(return_value=None)

        worker = MonitorWorker(
            repository=mock_repo,
            service=mock_service,
            adapters={DataSource.TWITTER: mock_adapter},
            billing_repo=mock_billing_repo,
        )

        monitor = _make_monitor(sources=[DataSource.TWITTER])
        mock_repo.get_monitor_by_id_system.return_value = monitor
        mock_repo.count_mentions_this_month.return_value = 5_001

        result = await worker.process_monitor(monitor.id)
        assert result["status"] == "skipped"
        assert result["reason"] == "quota_exceeded"

    @pytest.mark.asyncio
    async def test_tier_lookup_failure_uses_hard_cap(
        self, mock_repo, mock_service, mock_adapter
    ):
        """If billing repo throws, fall back to hard cap without crashing."""
        from src.monitoring.worker import MonitorWorker, _HARD_CAP_MENTIONS

        mock_billing_repo = MagicMock()
        mock_billing_repo.get_subscription = AsyncMock(
            side_effect=RuntimeError("DB connection lost")
        )

        worker = MonitorWorker(
            repository=mock_repo,
            service=mock_service,
            adapters={DataSource.TWITTER: mock_adapter},
            billing_repo=mock_billing_repo,
        )

        monitor = _make_monitor(sources=[DataSource.TWITTER])
        mock_repo.get_monitor_by_id_system.return_value = monitor
        # Under the hard cap (5K) — should proceed
        mock_repo.count_mentions_this_month.return_value = 100

        result = await worker.process_monitor(monitor.id)
        assert result["status"] == "completed"
        # count_mentions_this_month called exactly ONCE (not twice)
        mock_repo.count_mentions_this_month.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_tier_lookup_failure_blocks_above_hard_cap(
        self, mock_repo, mock_service, mock_adapter
    ):
        """When tier lookup fails and count exceeds hard cap, block the run."""
        from src.monitoring.worker import MonitorWorker, _HARD_CAP_MENTIONS

        mock_billing_repo = MagicMock()
        mock_billing_repo.get_subscription = AsyncMock(
            side_effect=RuntimeError("DB connection lost")
        )

        worker = MonitorWorker(
            repository=mock_repo,
            service=mock_service,
            adapters={DataSource.TWITTER: mock_adapter},
            billing_repo=mock_billing_repo,
        )

        monitor = _make_monitor(sources=[DataSource.TWITTER])
        mock_repo.get_monitor_by_id_system.return_value = monitor
        mock_repo.count_mentions_this_month.return_value = _HARD_CAP_MENTIONS + 1

        result = await worker.process_monitor(monitor.id)
        assert result["status"] == "skipped"
        assert result["reason"] == "quota_exceeded"

    @pytest.mark.asyncio
    async def test_no_billing_repo_defaults_to_free_tier(self, worker, mock_repo):
        """Without billing_repo, quota check defaults to FREE tier limits."""
        monitor = _make_monitor(sources=[DataSource.TWITTER])
        mock_repo.get_monitor_by_id_system.return_value = monitor
        # 6K — above FREE (5K) but below PRO (500K)
        mock_repo.count_mentions_this_month.return_value = 6_000

        result = await worker.process_monitor(monitor.id)
        assert result["status"] == "skipped"
        assert result["reason"] == "quota_exceeded"


# ── Error Classification Tests ──


class TestClassifyError:
    def test_timeout_error(self):
        from src.monitoring.worker import _classify_error

        assert _classify_error(TimeoutError("deadline exceeded")) == "source_timeout"

    def test_connection_error(self):
        from src.monitoring.worker import _classify_error

        assert _classify_error(ConnectionError("refused")) == "connection_error"

    def test_rate_limited(self):
        from src.monitoring.worker import _classify_error

        assert _classify_error(RuntimeError("Rate Limit exceeded")) == "rate_limited"

    def test_mention_fetch_error(self):
        from src.monitoring.worker import _classify_error
        from src.monitoring.exceptions import MentionFetchError

        assert _classify_error(MentionFetchError("bad response")) == "fetch_error"

    def test_query_validation_error(self):
        from src.monitoring.worker import _classify_error

        assert _classify_error(QueryValidationError("empty")) == "invalid_query"

    def test_generic_exception_maps_to_source_error(self):
        from src.monitoring.worker import _classify_error

        assert _classify_error(RuntimeError("something broke")) == "source_error"
        assert _classify_error(ValueError("bad value")) == "source_error"

    def test_no_internal_details_leak(self):
        """Ensure raw exception content like hostnames/URLs is never in the code."""
        from src.monitoring.worker import _classify_error

        exc = RuntimeError(
            "ConnectionError: https://service.example.invalid:8443/v2/mentions "
            "user=svc-account password=[REDACTED]"
        )
        code = _classify_error(exc)
        assert code == "source_error"
        assert "internal-api" not in code
        assert "s3cret" not in code


# ── Billing Tier Tests ──


class TestTierMonitoringFields:
    def test_free_tier_defaults(self):
        from src.billing.tiers import Tier, get_tier_config

        cfg = get_tier_config(Tier.FREE)
        assert cfg.max_monitors == 3
        assert cfg.max_mentions_per_month == 5_000
        assert cfg.max_sources_per_monitor == 5

    def test_pro_tier_limits(self):
        from src.billing.tiers import Tier, get_tier_config

        cfg = get_tier_config(Tier.PRO)
        assert cfg.max_monitors == 20
        assert cfg.max_mentions_per_month == 500_000
        assert cfg.max_sources_per_monitor == 10


# ── Model Tests ──


class TestMonitorRunModel:
    def test_dataclass_fields(self):
        run = _make_run(
            status="completed",
            completed_at=datetime.now(timezone.utc),
            mentions_ingested=42,
        )
        assert run.status == "completed"
        assert run.mentions_ingested == 42

    def test_monitor_next_run_at(self):
        now = datetime.now(timezone.utc)
        monitor = _make_monitor(next_run_at=now)
        assert monitor.next_run_at == now

    def test_monitor_next_run_at_default_none(self):
        monitor = _make_monitor(next_run_at=None)
        assert monitor.next_run_at is None


# ── Internal Router Response Models ──


class TestResponseModels:
    def test_dispatch_response(self):
        from src.api.routers.internal import DispatchResponse

        resp = DispatchResponse(
            dispatched=5, skipped=1, stale_recovered=2, total_due=8
        )
        assert resp.dispatched == 5

    def test_worker_response(self):
        from src.api.routers.internal import WorkerResponse

        resp = WorkerResponse(
            status="completed",
            mentions_ingested=10,
            sources_succeeded=2,
            sources_failed=0,
        )
        assert resp.status == "completed"
        assert resp.reason is None


# ── MockMonitorTaskClient Tests ──


class TestMockMonitorTaskClient:
    @pytest.mark.asyncio
    async def test_enqueue(self):
        from src.jobs.task_client import MockMonitorTaskClient

        client = MockMonitorTaskClient()
        mid = uuid4()
        result = await client.enqueue_monitor_run(mid, delay_seconds=10)
        assert f"{mid}" in result
        assert client.enqueued == [(mid, 10)]
