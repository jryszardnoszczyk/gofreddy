"""L5 cost-observability: $200/$400 threshold alerts + events.jsonl emission."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.audit.cost_observability import (
    COST_THRESHOLDS_USD,
    record_stage_cost,
)


def _events(audit_dir: Path) -> list[dict]:
    p = audit_dir / "events.jsonl"
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


def _kinds(audit_dir: Path) -> list[str]:
    return [e["kind"] for e in _events(audit_dir)]


# ─── events.jsonl emission ───────────────────────────────────────────


def test_record_stage_cost_emits_cost_recorded_event(tmp_path: Path):
    record_stage_cost(tmp_path, "stage_0_intake", 1.25)
    events = _events(tmp_path)
    cost_events = [e for e in events if e["kind"] == "cost_recorded"]
    assert len(cost_events) == 1
    assert cost_events[0]["stage"] == "stage_0_intake"
    assert cost_events[0]["cost_usd"] == 1.25
    assert cost_events[0]["total_so_far"] == 1.25


def test_multiple_stage_records_append_one_event_each(tmp_path: Path):
    record_stage_cost(tmp_path, "stage_0_intake", 1.0)
    record_stage_cost(tmp_path, "stage_1b", 2.5)
    record_stage_cost(tmp_path, "stage_1c", 3.0)
    cost_events = [e for e in _events(tmp_path) if e["kind"] == "cost_recorded"]
    assert len(cost_events) == 3
    assert cost_events[-1]["total_so_far"] == 6.5


# ─── threshold crossing — events ─────────────────────────────────────


def test_threshold_event_fires_when_first_crossing_200(tmp_path: Path):
    record_stage_cost(tmp_path, "stage_2_findability", 250.0)
    crossed = [e for e in _events(tmp_path) if e["kind"] == "cost_threshold_crossed"]
    assert len(crossed) == 1
    assert crossed[0]["threshold_usd"] == 200.0
    assert crossed[0]["total_so_far"] == 250.0


def test_threshold_event_does_not_refire_when_already_crossed(tmp_path: Path):
    record_stage_cost(tmp_path, "stage_2_findability", 250.0)  # crosses 200
    record_stage_cost(tmp_path, "stage_2_narrative", 50.0)     # still under 400
    crossed = [e for e in _events(tmp_path) if e["kind"] == "cost_threshold_crossed"]
    assert len(crossed) == 1
    assert crossed[0]["threshold_usd"] == 200.0


def test_both_thresholds_fire_when_single_jump_crosses_both(tmp_path: Path):
    record_stage_cost(tmp_path, "stage_huge", 500.0)
    crossed = [e for e in _events(tmp_path) if e["kind"] == "cost_threshold_crossed"]
    assert len(crossed) == 2
    assert {c["threshold_usd"] for c in crossed} == set(COST_THRESHOLDS_USD)


def test_thresholds_fire_in_order_across_separate_stages(tmp_path: Path):
    record_stage_cost(tmp_path, "stage_a", 150.0)   # no threshold
    record_stage_cost(tmp_path, "stage_b", 100.0)   # crosses 200
    record_stage_cost(tmp_path, "stage_c", 200.0)   # crosses 400
    crossed = [e for e in _events(tmp_path) if e["kind"] == "cost_threshold_crossed"]
    assert len(crossed) == 2
    assert [c["threshold_usd"] for c in crossed] == [200.0, 400.0]


# ─── threshold crossing — Slack ──────────────────────────────────────


def test_slack_ping_fires_on_threshold_when_url_set(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("SLACK_WEBHOOK_COST", "https://hooks.slack.example/cost")
    with patch("src.audit.cost_observability.httpx.post") as mock_post:
        record_stage_cost(tmp_path, "stage_x", 250.0)
    assert mock_post.call_count == 1
    args, kwargs = mock_post.call_args
    assert args[0] == "https://hooks.slack.example/cost"
    assert "$200" in kwargs["json"]["text"]


def test_slack_ping_fires_twice_for_double_crossing(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("SLACK_WEBHOOK_COST", "https://hooks.slack.example/cost")
    with patch("src.audit.cost_observability.httpx.post") as mock_post:
        record_stage_cost(tmp_path, "stage_x", 500.0)
    # crosses both $200 AND $400 in one jump
    assert mock_post.call_count == 2


def test_slack_ping_skipped_when_url_unset(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("SLACK_WEBHOOK_COST", raising=False)
    with patch("src.audit.cost_observability.httpx.post") as mock_post:
        record_stage_cost(tmp_path, "stage_x", 500.0)
    mock_post.assert_not_called()
    # event log still records the crossing
    crossed = [e for e in _events(tmp_path) if e["kind"] == "cost_threshold_crossed"]
    assert len(crossed) == 2


def test_slack_failure_swallowed_does_not_propagate(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("SLACK_WEBHOOK_COST", "https://hooks.slack.example/cost")
    with patch("src.audit.cost_observability.httpx.post", side_effect=Exception("network down")):
        # must not raise
        result = record_stage_cost(tmp_path, "stage_x", 250.0)
    assert result["total_so_far"] == 250.0
    crossed = [e for e in _events(tmp_path) if e["kind"] == "cost_threshold_crossed"]
    assert len(crossed) == 1  # event still logged despite slack failure
