"""Mock-based tests for BatchWorker."""

import asyncio
import unittest.mock

import pytest
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.analysis.exceptions import AnalysisError, GeminiRateLimitError
from src.batch.config import BatchSettings
from src.batch.models import BatchItem, BatchJob, BatchStatus, ItemStatus
from src.batch.worker import BatchWorker
from src.common.enums import Platform
from src.fetcher.exceptions import (
    FetcherError,
    RateLimitError,
    VideoUnavailableError,
)


@pytest.mark.mock_required
class TestBatchWorker:

    @pytest.fixture
    def settings(self):
        return BatchSettings(
            concurrency=2,
            rate_limit_per_sec=100,
            max_retries=2,
            backoff_base=0.01,
        )

    @pytest.fixture
    def mock_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_analysis(self):
        return AsyncMock()

    @pytest.fixture
    def mock_ws_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_billing(self):
        return AsyncMock()

    @pytest.fixture
    def worker(self, mock_repo, mock_analysis, mock_ws_repo, mock_billing, settings):
        return BatchWorker(
            batch_repository=mock_repo,
            analysis_service=mock_analysis,
            workspace_repository=mock_ws_repo,
            billing_service=mock_billing,
            settings=settings,
        )

    def _make_batch(self, **kwargs):
        defaults = {
            "id": uuid4(),
            "conversation_id": uuid4(),
            "collection_id": uuid4(),
            "user_id": uuid4(),
            "status": BatchStatus.PENDING,
            "total_items": 10,
            "completed_items": 0,
            "failed_items": 0,
            "flagged_items": 0,
            "analysis_types": ["brand_safety"],
            "idempotency_key": None,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
        defaults.update(kwargs)
        return BatchJob(**defaults)

    def _make_item(self, **kwargs):
        defaults = {
            "id": uuid4(),
            "batch_id": uuid4(),
            "workspace_item_id": uuid4(),
            "status": ItemStatus.RUNNING,
            "error_message": None,
            "claimed_at": datetime.now(UTC),
            "completed_at": None,
        }
        defaults.update(kwargs)
        return BatchItem(**defaults)

    # ── 1. process_batch happy path ───────────────────────────────────────

    async def test_process_batch_happy_path(self, worker, mock_repo):
        batch_id = uuid4()
        user_id = uuid4()
        batch = self._make_batch(id=batch_id, status=BatchStatus.PROCESSING, total_items=2)
        completed_batch = self._make_batch(id=batch_id, status=BatchStatus.COMPLETED, total_items=2, completed_items=2)

        items = [self._make_item(batch_id=batch_id) for _ in range(2)]

        mock_repo.update_batch_status.side_effect = [batch, completed_batch]
        mock_repo.claim_pending_items.side_effect = [items, []]
        mock_repo.complete_item_and_increment.return_value = MagicMock()
        mock_repo.get_items_by_status.return_value = []  # no cancelled items

        worker._analyze_item = AsyncMock(return_value={
            "cached": False, "cost_usd": 0.01, "record_id": str(uuid4()),
            "flagged": False, "risk_score": 0.0,
        })

        result = await worker.process_batch(batch_id, user_id)

        assert result.status == BatchStatus.COMPLETED
        # First call: PROCESSING, second call: COMPLETED
        assert mock_repo.update_batch_status.call_count == 2
        assert mock_repo.update_batch_status.call_args_list[0].args == (batch_id, BatchStatus.PROCESSING)
        assert mock_repo.update_batch_status.call_args_list[1].args == (batch_id, BatchStatus.COMPLETED)

    # ── 2. process_batch batch not found ──────────────────────────────────

    async def test_process_batch_batch_not_found(self, worker, mock_repo):
        batch_id = uuid4()
        mock_repo.update_batch_status.return_value = None

        with pytest.raises(RuntimeError, match="not found"):
            await worker.process_batch(batch_id)

    # ── 3. process_batch no items ─────────────────────────────────────────

    async def test_process_batch_no_items(self, worker, mock_repo):
        batch_id = uuid4()
        batch = self._make_batch(id=batch_id, status=BatchStatus.PROCESSING, total_items=0)
        completed_batch = self._make_batch(id=batch_id, status=BatchStatus.COMPLETED, total_items=0)

        mock_repo.update_batch_status.side_effect = [batch, completed_batch]
        mock_repo.claim_pending_items.return_value = []
        mock_repo.get_items_by_status.return_value = []  # no cancelled items

        result = await worker.process_batch(batch_id)

        assert result.status == BatchStatus.COMPLETED
        mock_repo.claim_pending_items.assert_called_once()

    # ── 4. process_batch cancellation ─────────────────────────────────────

    async def test_process_batch_cancellation(self, worker, mock_repo):
        batch_id = uuid4()
        batch = self._make_batch(id=batch_id, status=BatchStatus.PROCESSING, total_items=5)
        cancelled_batch = self._make_batch(id=batch_id, status=BatchStatus.CANCELLED, total_items=5)

        mock_repo.update_batch_status.side_effect = [batch, cancelled_batch]
        mock_repo.claim_pending_items.side_effect = asyncio.CancelledError()
        mock_repo.cancel_pending_items.return_value = None

        result = await worker.process_batch(batch_id)

        assert result.status == BatchStatus.CANCELLED
        mock_repo.cancel_pending_items.assert_called_once_with(batch_id)

    # ── 5. _process_item success ──────────────────────────────────────────

    async def test_process_item_success(self, worker, mock_repo):
        batch_id = uuid4()
        item = self._make_item(batch_id=batch_id)
        user_id = uuid4()
        record_id = str(uuid4())

        worker._analyze_item = AsyncMock(return_value={
            "cached": False, "cost_usd": 0.01, "record_id": record_id,
            "flagged": False, "risk_score": 0.0,
        })
        mock_repo.complete_item_and_increment.return_value = MagicMock()

        result = await worker._process_item(item, batch_id, user_id)

        assert result == ItemStatus.SUCCEEDED
        mock_repo.complete_item_and_increment.assert_called_once()
        call_kwargs = mock_repo.complete_item_and_increment.call_args
        assert call_kwargs.args == (item.id, batch_id, ItemStatus.SUCCEEDED)
        assert call_kwargs.kwargs["flagged"] is False
        assert call_kwargs.kwargs["workspace_update"]["item_id"] == item.workspace_item_id

    # ── 6. _process_item transient error ──────────────────────────────────

    async def test_process_item_transient_error(self, worker, mock_repo):
        batch_id = uuid4()
        item = self._make_item(batch_id=batch_id)

        worker._retry_with_backoff = AsyncMock(side_effect=GeminiRateLimitError("Rate limited"))
        mock_repo.complete_item_and_increment.return_value = MagicMock()

        result = await worker._process_item(item, batch_id, None)

        assert result == ItemStatus.FAILED
        mock_repo.complete_item_and_increment.assert_called_once()
        call_kwargs = mock_repo.complete_item_and_increment.call_args
        assert call_kwargs.args[2] == ItemStatus.FAILED
        assert "Transient error" in call_kwargs.kwargs["error_message"]

    # ── 7. _process_item permanent skip ───────────────────────────────────

    async def test_process_item_permanent_skip(self, worker, mock_repo):
        batch_id = uuid4()
        item = self._make_item(batch_id=batch_id)

        worker._retry_with_backoff = AsyncMock(
            side_effect=VideoUnavailableError(Platform.TIKTOK, "abc123"),
        )
        mock_repo.complete_item_and_increment.return_value = MagicMock()

        result = await worker._process_item(item, batch_id, None)

        assert result == ItemStatus.SKIPPED
        call_kwargs = mock_repo.complete_item_and_increment.call_args
        assert call_kwargs.args[2] == ItemStatus.SKIPPED
        assert "Video unavailable" in call_kwargs.kwargs["error_message"]

    # ── 8. _process_item fetcher error ────────────────────────────────────

    async def test_process_item_fetcher_error(self, worker, mock_repo):
        batch_id = uuid4()
        item = self._make_item(batch_id=batch_id)

        worker._retry_with_backoff = AsyncMock(
            side_effect=FetcherError(Platform.INSTAGRAM, "some fetcher issue"),
        )
        mock_repo.complete_item_and_increment.return_value = MagicMock()

        result = await worker._process_item(item, batch_id, None)

        assert result == ItemStatus.SKIPPED
        call_kwargs = mock_repo.complete_item_and_increment.call_args
        assert call_kwargs.args[2] == ItemStatus.SKIPPED

    # ── 9. _process_item unknown error ────────────────────────────────────

    async def test_process_item_unknown_error(self, worker, mock_repo):
        batch_id = uuid4()
        item = self._make_item(batch_id=batch_id)

        worker._retry_with_backoff = AsyncMock(side_effect=ValueError("unexpected"))
        mock_repo.complete_item_and_increment.return_value = MagicMock()

        result = await worker._process_item(item, batch_id, None)

        assert result == ItemStatus.FAILED
        call_kwargs = mock_repo.complete_item_and_increment.call_args
        assert call_kwargs.args[2] == ItemStatus.FAILED
        assert "ValueError" in call_kwargs.kwargs["error_message"]

    # ── 10. _process_item cascade deleted ─────────────────────────────────

    async def test_process_item_cascade_deleted(self, worker, mock_repo):
        batch_id = uuid4()
        item = self._make_item(batch_id=batch_id)

        worker._analyze_item = AsyncMock(return_value={
            "cached": False, "cost_usd": 0.01, "record_id": str(uuid4()),
            "flagged": False, "risk_score": 0.0,
        })
        mock_repo.complete_item_and_increment.return_value = None  # CASCADE delete

        result = await worker._process_item(item, batch_id, None)

        assert result == ItemStatus.SUCCEEDED
        mock_repo.complete_item_and_increment.assert_called_once()

    # ── 11. _retry_with_backoff succeeds on retry ─────────────────────────

    async def test_retry_with_backoff_succeeds_on_retry(self, worker):
        func = AsyncMock(side_effect=[GeminiRateLimitError("fail"), {"ok": True}])

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await worker._retry_with_backoff(func, max_retries=2)

        assert result == {"ok": True}
        assert func.call_count == 2

    # ── 12. _retry_with_backoff exhausted ─────────────────────────────────

    async def test_retry_with_backoff_exhausted(self, worker):
        error = GeminiRateLimitError("persistent failure")
        func = AsyncMock(side_effect=error)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(GeminiRateLimitError, match="persistent failure"):
                await worker._retry_with_backoff(func, max_retries=2)

        assert func.call_count == 3  # initial + 2 retries

    # ── 13. billing recorded on success ──────────────────────────────────

    async def test_billing_recorded_on_success(self, worker, mock_repo, mock_ws_repo, mock_analysis, mock_billing):
        batch_id = uuid4()
        item = self._make_item(batch_id=batch_id)
        user_id = uuid4()

        # Mock workspace DB lookup via public method
        mock_ws_repo.get_item_source.return_value = ("video123", "tiktok")

        # Mock analysis result with overall_safe / overall_confidence
        analysis_result = MagicMock()
        analysis_result.cached = False
        analysis_result.cost_usd = 0.05
        analysis_result.record_id = uuid4()
        analysis_result.analysis.overall_safe = True
        analysis_result.analysis.overall_confidence = 0.95
        mock_analysis.analyze.return_value = analysis_result

        # Mock billing
        billing_ctx = MagicMock()
        mock_billing.get_billing_context_for_user.return_value = billing_ctx

        mock_repo.complete_item_and_increment.return_value = MagicMock()

        # Call _analyze_item directly (not through _process_item which wraps with retry)
        result = await worker._analyze_item(item, user_id)

        assert result["cached"] is False
        assert result["cost_usd"] == 0.05
        assert result["flagged"] is False
        assert result["risk_score"] == 0.0
        mock_billing.get_billing_context_for_user.assert_called_once_with(user_id)
        mock_billing.record_usage.assert_called_once_with(billing_ctx, video_count=1, check_thresholds=False)

    # ── 15. billing failure doesn't crash ─────────────────────────────────

    async def test_billing_failure_does_not_crash(self, worker, mock_repo, mock_ws_repo, mock_analysis, mock_billing):
        batch_id = uuid4()
        item = self._make_item(batch_id=batch_id)
        user_id = uuid4()

        # Mock workspace DB lookup via public method
        mock_ws_repo.get_item_source.return_value = ("video456", "youtube")

        # Mock analysis result
        analysis_result = MagicMock()
        analysis_result.cached = False
        analysis_result.cost_usd = 0.03
        analysis_result.record_id = uuid4()
        analysis_result.analysis.overall_safe = True
        analysis_result.analysis.overall_confidence = 0.9
        mock_analysis.analyze.return_value = analysis_result

        # Billing blows up
        mock_billing.get_billing_context_for_user.side_effect = RuntimeError("billing down")

        mock_repo.complete_item_and_increment.return_value = MagicMock()

        # Should NOT raise despite billing failure
        result = await worker._analyze_item(item, user_id)

        assert result["cached"] is False
        assert result["cost_usd"] == 0.03

    # ── 16. process_batch deadline exceeded ────────────────────────────────

    async def test_process_batch_deadline_exceeded(self, worker, mock_repo):
        """process_batch breaks when deadline exceeded, fails remaining PENDING items."""
        batch_id = uuid4()
        batch = self._make_batch(id=batch_id, status=BatchStatus.PROCESSING, total_items=10)
        completed_batch = self._make_batch(
            id=batch_id, status=BatchStatus.COMPLETED, total_items=10, completed_items=5,
        )

        mock_repo.update_batch_status.side_effect = [batch, completed_batch]
        mock_repo.fail_pending_items.return_value = batch
        mock_repo.get_items_by_status.return_value = []  # no cancelled items
        # Always return items so the loop would run forever without deadline
        mock_repo.claim_pending_items.return_value = [self._make_item(batch_id=batch_id)]
        mock_repo.complete_item_and_increment.return_value = MagicMock()
        worker._analyze_item = AsyncMock(
            return_value={
                "cached": False, "cost_usd": 0.01, "record_id": str(uuid4()),
                "flagged": False, "risk_score": 0.0,
            },
        )

        # Patch time.monotonic to simulate deadline exceeded after first worker iteration.
        # With continuous worker pool, monotonic is called many times (once per worker
        # per loop iteration + post-gather check), so use a callable.
        with patch("src.batch.worker.time") as mock_time:
            _calls = 0

            def _fake_monotonic():
                nonlocal _calls
                _calls += 1
                # First 2 calls: deadline set + first worker check pass
                if _calls <= 2:
                    return 0.0
                return 541.0  # All subsequent: past deadline

            mock_time.monotonic.side_effect = _fake_monotonic
            result = await worker.process_batch(batch_id)

        assert result.status == BatchStatus.COMPLETED
        # Should have processed at least one batch of items before deadline
        assert mock_repo.claim_pending_items.call_count >= 1
        # Remaining PENDING items should be failed with deadline reason
        mock_repo.fail_pending_items.assert_called_once_with(batch_id, "deadline exceeded")

    # ── 17. process_batch sets CANCELLED when items were cancelled ────────

    async def test_process_batch_cancelled_via_api(self, worker, mock_repo):
        """When cancel_batch marks items cancelled, worker sets CANCELLED not COMPLETED."""
        batch_id = uuid4()
        batch = self._make_batch(id=batch_id, status=BatchStatus.PROCESSING, total_items=5)
        cancelled_batch = self._make_batch(id=batch_id, status=BatchStatus.CANCELLED, total_items=5)

        mock_repo.update_batch_status.side_effect = [batch, cancelled_batch]
        mock_repo.claim_pending_items.return_value = []  # all items already cancelled
        # Simulate that cancel_batch already marked items as cancelled
        mock_repo.get_items_by_status.return_value = [self._make_item(batch_id=batch_id)]

        result = await worker.process_batch(batch_id)

        assert result.status == BatchStatus.CANCELLED
        mock_repo.update_batch_status.call_args_list[1].args == (batch_id, BatchStatus.CANCELLED)
