"""P2 wiring tests: cost_recorder.record mirrors to autoresearch.events log.

Verifies that every cost_recorder.record() call emits a canonical kind="cost"
event in addition to writing to its own JSONL. Mirroring is best-effort —
failure in the events emission must not prevent the cost_recorder write
from succeeding.

See docs/brainstorms/2026-05-13-client-portal-telemetry-design.md §A.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolate_events_log(tmp_path, monkeypatch):
    """Redirect EVENTS_LOG to a temp file so tests don't pollute the operator
    default at ~/.local/share/gofreddy/events.jsonl."""
    import autoresearch.events as events
    monkeypatch.setattr(events, "EVENTS_LOG", tmp_path / "events.jsonl")
    return tmp_path


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro) if not asyncio.get_event_loop().is_running() else asyncio.run(coro)


def test_cost_record_writes_own_jsonl_and_mirrors_to_events(tmp_path, isolate_events_log):
    """End-to-end: cost_recorder.record() writes BOTH its own cost JSONL AND
    the canonical events.jsonl (mirror)."""
    from src.common.cost_recorder import CostRecorder

    cost_log = tmp_path / "cost-ledger.jsonl"
    recorder = CostRecorder()
    recorder.init(cost_log)

    asyncio.run(recorder.record(
        provider="anthropic",
        operation="claude_call",
        cost_usd=0.0234,
        tokens_in=1500,
        tokens_out=420,
        model="claude-opus-4-7",
    ))

    # Cost JSONL written (source of truth for cost-ledger math)
    assert cost_log.exists()
    cost_entry = json.loads(cost_log.read_text().splitlines()[0])
    assert cost_entry["provider"] == "anthropic"
    assert cost_entry["cost_usd"] == 0.0234

    # Mirror to operator-internal events log (client_id was None)
    events_log = isolate_events_log / "events.jsonl"
    assert events_log.exists()
    event_entry = json.loads(events_log.read_text().splitlines()[0])
    assert event_entry["kind"] == "cost"
    assert event_entry["source"] == "autoresearch"
    assert event_entry["action"] == "anthropic.claude_call"
    assert event_entry["status"] == "complete"
    assert event_entry["cost_usd"] == 0.0234
    assert event_entry["tokens_in"] == 1500
    assert event_entry["tokens_out"] == 420
    assert event_entry["model"] == "claude-opus-4-7"
    assert "timestamp" in event_entry


def test_cost_record_with_client_id_writes_to_per_client_path(tmp_path):
    """When client_id is supplied, the mirror event lands at the per-client
    path (clients/<slug>/audit/events.jsonl), NOT the operator-internal log."""
    from src.common.cost_recorder import CostRecorder

    cost_log = tmp_path / "cost-ledger.jsonl"
    recorder = CostRecorder()
    recorder.init(cost_log)

    # client_events_path returns RELATIVE paths (clients/<slug>/audit/...).
    # Change cwd to tmp_path so the relative path resolves inside isolated test.
    import os
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        asyncio.run(recorder.record(
            provider="anthropic",
            operation="claude_call",
            cost_usd=0.0234,
            tokens_in=1500,
            tokens_out=420,
            model="claude-opus-4-7",
            client_id="klinika-melitus",
            session_id="run-abc123",
            lane="site_engine",
            variant="v123",
            fixture="klinika_hero",
        ))
    finally:
        os.chdir(old_cwd)

    # Cost-ledger JSONL still written
    assert cost_log.exists()

    # Per-client events log written at canonical path
    per_client = tmp_path / "clients/klinika-melitus/audit/events.jsonl"
    assert per_client.exists()
    payload = json.loads(per_client.read_text().splitlines()[0])
    assert payload["kind"] == "cost"
    assert payload["client_id"] == "klinika-melitus"
    assert payload["session_id"] == "run-abc123"
    assert payload["lane"] == "site_engine"
    assert payload["variant"] == "v123"
    assert payload["fixture"] == "klinika_hero"


def test_cost_record_event_emission_failure_does_not_break_cost_write(tmp_path, monkeypatch, isolate_events_log):
    """If the events.jsonl mirror fails (e.g., disk full, permission denied),
    the cost_recorder's own JSONL MUST still be written — cost-ledger math
    is the source of truth and cannot depend on the optional event-stream
    mirror succeeding."""
    from src.common.cost_recorder import CostRecorder
    import autoresearch.events as events

    cost_log = tmp_path / "cost-ledger.jsonl"
    recorder = CostRecorder()
    recorder.init(cost_log)

    # Sabotage events.log_event to always raise
    def explode(*args, **kwargs):
        raise OSError("simulated disk-full on events log")
    monkeypatch.setattr(events, "log_event", explode)

    # Must not raise
    asyncio.run(recorder.record(
        provider="gemini",
        operation="vision_score",
        cost_usd=0.0012,
        model="gemini-2.5",
    ))

    # Cost log still written despite events emission failure
    assert cost_log.exists()
    cost_entry = json.loads(cost_log.read_text().splitlines()[0])
    assert cost_entry["provider"] == "gemini"
    assert cost_entry["cost_usd"] == 0.0012
