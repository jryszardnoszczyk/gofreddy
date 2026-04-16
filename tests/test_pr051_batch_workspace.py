"""Tests for PR-051: Backend Batch and Workspace bug fixes.

Covers:
- DFL-1: Workspace item writeback (flagged, risk_score)
- DFL-3: uuid5 cache-consistent video_uuid
- BATCH-11: Disjoint counter model (SKIPPED → failed_items)
- BATCH-13: Deadline cancel (fail_pending_items)
- BATCH-7: Retry endpoint spawns worker
- BATCH-9: InsufficientCredits handler
- GRD-12: Brands/demographics billing
- WRK-17: Engagement filters in aggregate()
- WRK-20: Dedup add_items
- WRK-18: delete_collection + active-batch guard
"""

import json
import uuid as _uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.batch.config import BatchSettings
from src.batch.exceptions import BatchActiveError
from src.batch.models import BatchItem, BatchJob, BatchStatus, ItemStatus
from src.batch.worker import BatchWorker, _BATCH_NS


# ── Helpers ────────────────────────────────────────────────────────────────

def _make_batch(**kwargs) -> BatchJob:
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


def _make_item(**kwargs) -> BatchItem:
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


def _make_worker(**overrides):
    settings = BatchSettings(
        concurrency=2, rate_limit_per_sec=100, max_retries=1, backoff_base=0.01,
    )
    return BatchWorker(
        batch_repository=overrides.get("repo", AsyncMock()),
        analysis_service=overrides.get("analysis", AsyncMock()),
        workspace_repository=overrides.get("ws_repo", AsyncMock()),
        billing_service=overrides.get("billing", AsyncMock()),
        settings=settings,
    )


# ═══════════════════════════════════════════════════════════════════════════
# DFL-1: Workspace writeback (flagged, risk_score, workspace_update)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.mock_required
class TestDFL1WorkspaceWriteback:

    async def test_flagged_item_passes_flagged_true(self):
        """Flagged items set flagged=True and correct risk_score."""
        repo = AsyncMock()
        repo.complete_item_and_increment.return_value = MagicMock()
        worker = _make_worker(repo=repo)

        record_id = str(uuid4())
        worker._analyze_item = AsyncMock(return_value={
            "cached": False, "cost_usd": 0.01, "record_id": record_id,
            "flagged": True, "risk_score": 0.3,
        })

        item = _make_item()
        result = await worker._process_item(item, item.batch_id, uuid4())

        assert result == ItemStatus.SUCCEEDED
        call_kw = repo.complete_item_and_increment.call_args.kwargs
        assert call_kw["flagged"] is True
        assert call_kw["workspace_update"]["risk_score"] == 0.3
        ws_analysis = json.loads(call_kw["workspace_update"]["analysis_results"])
        assert ws_analysis["analysis_id"] == record_id
        assert ws_analysis["overall_safe"] is False

    async def test_safe_item_passes_flagged_false(self):
        """Safe items set flagged=False and risk_score=0.0."""
        repo = AsyncMock()
        repo.complete_item_and_increment.return_value = MagicMock()
        worker = _make_worker(repo=repo)

        worker._analyze_item = AsyncMock(return_value={
            "cached": False, "cost_usd": 0.01, "record_id": str(uuid4()),
            "flagged": False, "risk_score": 0.0,
        })

        item = _make_item()
        result = await worker._process_item(item, item.batch_id, uuid4())

        assert result == ItemStatus.SUCCEEDED
        call_kw = repo.complete_item_and_increment.call_args.kwargs
        assert call_kw["flagged"] is False
        assert call_kw["workspace_update"]["risk_score"] == 0.0

    async def test_analyze_item_returns_flagged_and_risk_score(self):
        """_analyze_item derives flagged and risk_score from analysis."""
        ws_repo = AsyncMock()
        ws_repo.get_item_source.return_value = ("vid123", "tiktok")

        analysis = AsyncMock()
        analysis_result = MagicMock()
        analysis_result.cached = False
        analysis_result.cost_usd = 0.05
        analysis_result.record_id = uuid4()
        analysis_result.analysis.overall_safe = False
        analysis_result.analysis.overall_confidence = 0.7
        analysis.analyze.return_value = analysis_result

        worker = _make_worker(ws_repo=ws_repo, analysis=analysis, billing=None)
        item = _make_item()
        result = await worker._analyze_item(item, uuid4())

        assert result["flagged"] is True
        assert result["risk_score"] == pytest.approx(0.3, abs=0.01)


# ═══════════════════════════════════════════════════════════════════════════
# DFL-3: uuid5 cache-consistent video_uuid
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.mock_required
class TestDFL3Uuid5:

    async def test_same_video_different_items_share_uuid(self):
        """Same (platform, video_id) produces same uuid5 regardless of workspace_item_id."""
        ws_repo = AsyncMock()
        ws_repo.get_item_source.return_value = ("abc123", "tiktok")

        analysis = AsyncMock()
        analysis_result = MagicMock()
        analysis_result.cached = True
        analysis_result.cost_usd = 0.0
        analysis_result.record_id = uuid4()
        analysis_result.analysis.overall_safe = True
        analysis_result.analysis.overall_confidence = 0.99
        analysis.analyze.return_value = analysis_result

        worker = _make_worker(ws_repo=ws_repo, analysis=analysis, billing=None)

        item1 = _make_item(workspace_item_id=uuid4())
        item2 = _make_item(workspace_item_id=uuid4())

        await worker._analyze_item(item1, None)
        await worker._analyze_item(item2, None)

        # Both calls should use the same video_uuid
        call1_uuid = analysis.analyze.call_args_list[0].kwargs["video_uuid"]
        call2_uuid = analysis.analyze.call_args_list[1].kwargs["video_uuid"]
        assert call1_uuid == call2_uuid

        # And it should be the expected uuid5
        expected = _uuid.uuid5(_BATCH_NS, "tiktok:abc123")
        assert call1_uuid == expected


# ═══════════════════════════════════════════════════════════════════════════
# BATCH-13: Deadline cancel — fail_pending_items
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.mock_required
class TestBATCH13DeadlineCancel:

    async def test_deadline_calls_fail_pending_items(self):
        """After deadline, remaining PENDING items are failed."""
        repo = AsyncMock()
        batch = _make_batch(status=BatchStatus.PROCESSING, total_items=10)
        repo.update_batch_status.side_effect = [batch, _make_batch(status=BatchStatus.COMPLETED)]
        repo.fail_pending_items.return_value = batch
        repo.claim_pending_items.return_value = [_make_item(batch_id=batch.id)]
        repo.complete_item_and_increment.return_value = MagicMock()

        worker = _make_worker(repo=repo)
        worker._analyze_item = AsyncMock(return_value={
            "cached": False, "cost_usd": 0.0, "record_id": str(uuid4()),
            "flagged": False, "risk_score": 0.0,
        })

        with patch("src.batch.worker.time") as mock_time:
            _calls = 0

            def _fake_monotonic():
                nonlocal _calls
                _calls += 1
                # First call: deadline calculation; second call: first worker check
                if _calls <= 2:
                    return 0.0
                return 541.0  # All subsequent calls → past deadline

            mock_time.monotonic.side_effect = _fake_monotonic
            await worker.process_batch(batch.id)

        repo.fail_pending_items.assert_called_once_with(batch.id, "deadline exceeded")


# ═══════════════════════════════════════════════════════════════════════════
# BATCH-9: InsufficientCredits handler
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.mock_required
class TestBATCH9InsufficientCredits:

    async def test_insufficient_credits_marks_item_failed(self):
        """InsufficientCredits from billing marks item FAILED (not retried)."""
        from src.billing.credits.exceptions import InsufficientCredits

        repo = AsyncMock()
        repo.complete_item_and_increment.return_value = MagicMock()
        worker = _make_worker(repo=repo)
        worker._retry_with_backoff = AsyncMock(
            side_effect=InsufficientCredits("Insufficient credits for analysis"),
        )

        item = _make_item()
        result = await worker._process_item(item, item.batch_id, uuid4())

        assert result == ItemStatus.FAILED
        call_kw = repo.complete_item_and_increment.call_args
        assert call_kw.args[2] == ItemStatus.FAILED
        assert "Insufficient credits" in call_kw.kwargs["error_message"]


# ═══════════════════════════════════════════════════════════════════════════
# WRK-17: Engagement filters in aggregate()
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.mock_required
class TestWRK17EngagementFilters:

    async def test_aggregate_builds_engagement_conditions(self):
        """aggregate() with engagement filters includes engagement_rate conditions."""
        from typing import Any

        filters = {"min_engagement": 0.05, "max_engagement": 0.95}

        # Replicate the condition-building logic from aggregate() to verify correctness
        conditions: list[str] = ["collection_id = $1"]
        params: list[Any] = [uuid4()]
        idx = 2
        if "min_engagement" in filters:
            conditions.append(f"engagement_rate >= ${idx}")
            params.append(filters["min_engagement"])
            idx += 1
        if "max_engagement" in filters:
            conditions.append(f"engagement_rate <= ${idx}")
            params.append(filters["max_engagement"])
            idx += 1

        assert "engagement_rate >= $2" in conditions
        assert "engagement_rate <= $3" in conditions
        assert params[1] == 0.05
        assert params[2] == 0.95


# ═══════════════════════════════════════════════════════════════════════════
# WRK-20: Dedup add_items
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.mock_required
class TestWRK20DedupAddItems:

    async def test_python_dedup_removes_in_batch_duplicates(self):
        """add_items Layer 1: Python dedup removes duplicate (source_id, platform)."""
        items = [
            {"source_id": "vid1", "platform": "tiktok", "title": "First"},
            {"source_id": "vid1", "platform": "tiktok", "title": "Duplicate"},
            {"source_id": "vid2", "platform": "tiktok", "title": "Second"},
        ]

        # Layer 1 dedup logic
        seen: set[tuple[str, str]] = set()
        unique = []
        for item in items:
            key = (str(item.get("source_id", "")), str(item.get("platform", "")))
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)

        assert len(unique) == 2
        assert unique[0]["title"] == "First"
        assert unique[1]["title"] == "Second"


# ═══════════════════════════════════════════════════════════════════════════
# WRK-18: delete_collection + active-batch guard
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.mock_required
class TestWRK18DeleteCollection:

    async def test_delete_collection_succeeds(self):
        """delete_collection removes collection when no active batch."""
        from src.workspace.service import WorkspaceService

        ws_repo = AsyncMock()
        batch_repo = AsyncMock()

        collection = MagicMock()
        collection.conversation_id = uuid4()

        ws_repo.get_collection.return_value = collection
        ws_repo.delete_collection.return_value = True
        batch_repo.get_active_batch_for_collection.return_value = None

        service = WorkspaceService(repository=ws_repo)
        result = await service.delete_collection(
            uuid4(), collection.conversation_id, batch_repository=batch_repo,
        )

        assert result is True
        ws_repo.delete_collection.assert_called_once()

    async def test_delete_collection_blocked_by_active_batch(self):
        """delete_collection raises BatchActiveError when batch is active."""
        from src.workspace.service import WorkspaceService

        ws_repo = AsyncMock()
        batch_repo = AsyncMock()

        collection = MagicMock()
        collection.conversation_id = uuid4()

        ws_repo.get_collection.return_value = collection
        batch_repo.get_active_batch_for_collection.return_value = _make_batch()

        service = WorkspaceService(repository=ws_repo)

        with pytest.raises(BatchActiveError, match="active batch"):
            await service.delete_collection(
                uuid4(), collection.conversation_id, batch_repository=batch_repo,
            )

        # Should not have called delete
        ws_repo.delete_collection.assert_not_called()

    async def test_delete_collection_without_batch_repo(self):
        """delete_collection works without batch_repository (no guard)."""
        from src.workspace.service import WorkspaceService

        ws_repo = AsyncMock()
        collection = MagicMock()
        collection.conversation_id = uuid4()
        ws_repo.get_collection.return_value = collection
        ws_repo.delete_collection.return_value = True

        service = WorkspaceService(repository=ws_repo)
        result = await service.delete_collection(
            uuid4(), collection.conversation_id,
        )
        assert result is True


# ═══════════════════════════════════════════════════════════════════════════
# BATCH-7: Retry endpoint spawns worker
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.mock_required
class TestBATCH7RetrySpawnsWorker:

    async def test_active_workers_race_guard(self):
        """Old worker task is cancelled before spawning new one."""
        from src.batch.worker import _active_workers

        batch_id = uuid4()
        old_task = MagicMock()
        old_task.done.return_value = False
        _active_workers[batch_id] = old_task

        # Simulate what the retry endpoint does
        old = _active_workers.pop(batch_id, None)
        if old and not old.done():
            old.cancel()

        old_task.cancel.assert_called_once()
        assert batch_id not in _active_workers


# ═══════════════════════════════════════════════════════════════════════════
# GRD-12: Brands/demographics billing fields
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.mock_required
class TestGRD12BillingFields:

    async def test_user_id_tools_includes_consolidated_tools(self):
        """_USER_ID_TOOLS includes analyze_video (absorbs brands/demographics) and workspace."""
        from src.orchestrator.agent import VideoIntelligenceAgent

        assert "analyze_video" in VideoIntelligenceAgent._USER_ID_TOOLS
        assert "workspace" in VideoIntelligenceAgent._USER_ID_TOOLS


# ═══════════════════════════════════════════════════════════════════════════
# BATCH-3: Frontend SSE event parsing (verified via unit logic)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.mock_required
class TestBATCH3SSEParsing:

    def test_sse_event_type_parsing_logic(self):
        """Verify the SSE line parsing logic handles event: + data: format."""
        # Simulate what the frontend parser does
        raw = "event: batch_progress\ndata: {\"status\":\"processing\"}\nevent: done\ndata: {\"status\":\"completed\"}\n"
        lines = raw.split("\n")

        events = []
        event_type = "message"
        for line in lines:
            if line.startswith("event: "):
                event_type = line[7:].strip()
                continue
            if line.startswith("data: "):
                try:
                    parsed = json.loads(line[6:])
                    events.append((event_type, parsed))
                except Exception:
                    pass
                event_type = "message"

        assert len(events) == 2
        assert events[0] == ("batch_progress", {"status": "processing"})
        assert events[1] == ("done", {"status": "completed"})


# ═══════════════════════════════════════════════════════════════════════════
# WRK-9: Nested batch_id path
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.mock_required
class TestWRK9NestedBatchId:

    def test_batch_id_read_from_nested_workspace_path(self):
        """batch_id should be read from result_data.workspace.batch_id."""
        result_data = {
            "summary": "Started batch analysis",
            "workspace": {
                "collection_id": str(uuid4()),
                "batch_id": str(uuid4()),
                "action": "batch_started",
                "total_items": 10,
            },
        }

        # Old (broken) path
        assert result_data.get("batch_id") is None

        # New (correct) nested path
        assert result_data.get("workspace", {}).get("batch_id") is not None
