"""Tests for session-events wiring + render section.

Covers:
- _emit_session_event writes to session_dir/events.jsonl via the
  autoresearch.events module.
- AUTORESEARCH_SESSION_EVENTS=0 (and case-insensitive variants) disables
  emission.
- Failures inside log_event are swallowed silently (best-effort).
- build_session_events_timeline renders the JSONL into an HTML table.
- An absent / empty events.jsonl produces no section.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_PATH = REPO_ROOT / "autoresearch" / "harness" / "agent.py"
RENDER_REPORT_PATH = (
    REPO_ROOT
    / "autoresearch"
    / "archive"
    / "v006"
    / "scripts"
    / "render_report.py"
)


@pytest.fixture(scope="module")
def agent_module():
    paths = [
        str(REPO_ROOT / "autoresearch" / "archive" / "v006" / "scripts"),
        str(REPO_ROOT / "autoresearch"),
    ]
    for p in paths:
        sys.path.insert(0, p)
    spec = importlib.util.spec_from_file_location("agent_for_events", AGENT_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["agent_for_events"] = mod
    try:
        spec.loader.exec_module(mod)
    finally:
        for p in paths:
            try:
                sys.path.remove(p)
            except ValueError:
                pass
    return mod


@pytest.fixture(scope="module")
def render_report_module():
    spec = importlib.util.spec_from_file_location(
        "render_report_events_test", RENDER_REPORT_PATH
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["render_report_events_test"] = mod
    spec.loader.exec_module(mod)
    return mod


# ─── _emit_session_event ─────────────────────────────────────────────────────


def test_emit_event_writes_jsonl(agent_module, tmp_path, monkeypatch):
    monkeypatch.delenv("AUTORESEARCH_SESSION_EVENTS", raising=False)
    sd = tmp_path / "session"
    log_path = sd / "logs" / "iteration_001.log"
    log_path.parent.mkdir(parents=True)

    agent_module._emit_session_event(
        log_path, "agent_spawn", backend="codex", model="gpt-5", prompt_bytes=420,
    )

    events = sd / "events.jsonl"
    assert events.is_file()
    line = events.read_text().strip()
    record = json.loads(line)
    assert record["kind"] == "agent_spawn"
    assert record["backend"] == "codex"
    assert record["model"] == "gpt-5"
    assert record["prompt_bytes"] == 420
    assert "timestamp" in record


@pytest.mark.parametrize("value", ["0", "off", "false", "no", "skip", "FALSE", "Off", "Skip"])
def test_emit_event_disabled_via_env(agent_module, tmp_path, monkeypatch, value):
    monkeypatch.setenv("AUTORESEARCH_SESSION_EVENTS", value)
    sd = tmp_path / "session"
    log_path = sd / "logs" / "iteration_001.log"
    log_path.parent.mkdir(parents=True)

    agent_module._emit_session_event(log_path, "agent_spawn", backend="codex")

    assert not (sd / "events.jsonl").exists()


def test_emit_event_silent_on_log_event_error(agent_module, tmp_path, monkeypatch):
    """Failures inside log_event must NOT raise — agent runs cannot block
    on event-log issues."""
    monkeypatch.delenv("AUTORESEARCH_SESSION_EVENTS", raising=False)
    sd = tmp_path / "session"
    log_path = sd / "logs" / "iteration_001.log"
    log_path.parent.mkdir(parents=True)

    # Patch events.log_event to raise — emission should not propagate it
    import sys as _sys
    fake_events = type("M", (), {"log_event": lambda *a, **k: (_ for _ in ()).throw(RuntimeError("disk full"))})
    monkeypatch.setitem(_sys.modules, "events", fake_events)

    # Must not raise
    agent_module._emit_session_event(log_path, "agent_spawn")


def test_emit_event_returns_none_on_bad_layout(agent_module, tmp_path, monkeypatch):
    """If log_path doesn't sit under session_dir/logs/..., the helper bails
    out cleanly (returns without writing)."""
    monkeypatch.delenv("AUTORESEARCH_SESSION_EVENTS", raising=False)
    # log_path with no parent.parent dir — _events_log_path returns None
    bare = tmp_path / "weird.log"
    agent_module._emit_session_event(bare, "agent_spawn")
    # Nothing written
    assert not (tmp_path / "events.jsonl").exists()


# ─── build_session_events_timeline ───────────────────────────────────────────


def test_timeline_renders_events(render_report_module, tmp_path):
    sd = tmp_path / "session"
    sd.mkdir()
    (sd / "events.jsonl").write_text(
        json.dumps({"kind": "agent_spawn", "timestamp": "2026-05-08T20:00:00Z",
                    "backend": "codex", "model": "gpt-5"}) + "\n"
        + json.dumps({"kind": "agent_complete", "timestamp": "2026-05-08T20:01:30Z",
                      "backend": "codex", "exit_code": 0, "duration_ms": 90123}) + "\n"
    )
    html = render_report_module.build_session_events_timeline(sd)
    assert "Session event timeline" in html
    assert "agent_spawn" in html
    assert "agent_complete" in html
    assert "2026-05-08T20:00:00Z" in html
    assert "exit_code" in html


def test_timeline_empty_returns_empty(render_report_module, tmp_path):
    sd = tmp_path / "session"
    sd.mkdir()
    # no events.jsonl
    assert render_report_module.build_session_events_timeline(sd) == ""

    # empty events.jsonl
    (sd / "events.jsonl").write_text("")
    assert render_report_module.build_session_events_timeline(sd) == ""


def test_timeline_skips_malformed_lines(render_report_module, tmp_path):
    sd = tmp_path / "session"
    sd.mkdir()
    (sd / "events.jsonl").write_text(
        json.dumps({"kind": "ok", "timestamp": "t1"}) + "\n"
        + "{not json\n"
        + json.dumps({"kind": "also_ok", "timestamp": "t2"}) + "\n"
    )
    html = render_report_module.build_session_events_timeline(sd)
    assert "ok" in html
    assert "also_ok" in html
    # No crash on the malformed line


def test_emit_then_timeline_round_trip(agent_module, render_report_module,
                                        tmp_path, monkeypatch):
    """End-to-end: helper emits, renderer surfaces."""
    monkeypatch.delenv("AUTORESEARCH_SESSION_EVENTS", raising=False)
    sd = tmp_path / "session"
    log_path = sd / "logs" / "iteration_001.log"
    log_path.parent.mkdir(parents=True)

    agent_module._emit_session_event(
        log_path, "agent_spawn", backend="codex", model="gpt-5",
        prompt_bytes=512, strategy="fresh",
    )
    agent_module._emit_session_event(
        log_path, "agent_complete", backend="codex", exit_code=0,
        duration_ms=12345, strategy="fresh",
    )

    html = render_report_module.build_session_events_timeline(sd)
    assert "agent_spawn" in html
    assert "agent_complete" in html
    assert "duration_ms" in html
    assert "12345" in html
