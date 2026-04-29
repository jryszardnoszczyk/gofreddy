"""Tests for src/audit/events + the autoresearch.events.log_event path= extension."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from autoresearch.events import EVENTS_LOG, log_event
from src.audit.events import log_global, log_to_audit


def test_log_event_with_path_writes_to_custom_destination(tmp_path: Path):
    target = tmp_path / "custom" / "events.jsonl"
    log_event("test_kind", path=target, foo="bar", n=42)
    assert target.is_file()
    rows = target.read_text(encoding="utf-8").strip().splitlines()
    assert len(rows) == 1
    record = json.loads(rows[0])
    assert record["kind"] == "test_kind"
    assert record["foo"] == "bar"
    assert record["n"] == 42
    assert "timestamp" in record


def test_log_event_without_path_uses_default(monkeypatch, tmp_path: Path):
    """Default destination is autoresearch.events.EVENTS_LOG; redirect via
    monkeypatch so the test doesn't write to the real user dir."""
    fake_default = tmp_path / "default.jsonl"
    monkeypatch.setattr("autoresearch.events.EVENTS_LOG", fake_default)
    log_event("global_kind", marker="default-path")
    assert fake_default.is_file()
    record = json.loads(fake_default.read_text(encoding="utf-8").strip())
    assert record["kind"] == "global_kind"
    assert record["marker"] == "default-path"


def test_log_to_audit_writes_under_audit_dir(tmp_path: Path):
    audit_dir = tmp_path / "audit-001"
    audit_dir.mkdir()
    log_to_audit(audit_dir, "stage_start", stage="stage_1b")
    assert (audit_dir / "events.jsonl").is_file()
    record = json.loads((audit_dir / "events.jsonl").read_text(encoding="utf-8").strip())
    assert record["kind"] == "stage_start"
    assert record["stage"] == "stage_1b"


def test_log_global_writes_to_default(monkeypatch, tmp_path: Path):
    fake_default = tmp_path / "global.jsonl"
    monkeypatch.setattr("autoresearch.events.EVENTS_LOG", fake_default)
    log_global("audit_start", audit_id="a-001")
    assert fake_default.is_file()
    record = json.loads(fake_default.read_text(encoding="utf-8").strip())
    assert record["kind"] == "audit_start"
    assert record["audit_id"] == "a-001"


def test_log_to_audit_appends_multiple_events(tmp_path: Path):
    audit_dir = tmp_path
    log_to_audit(audit_dir, "k1", n=1)
    log_to_audit(audit_dir, "k2", n=2)
    log_to_audit(audit_dir, "k3", n=3)
    rows = (audit_dir / "events.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(rows) == 3
    assert [json.loads(r)["kind"] for r in rows] == ["k1", "k2", "k3"]
