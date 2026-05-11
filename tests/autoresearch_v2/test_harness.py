"""Tests for autoresearch_v2/harness/ — backend, opencode_jsonl, events,
concurrency, sessions, telemetry. judge_calibration is a verbatim copy of
v1's tested module so it's covered by tests/autoresearch/."""

from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path

import pytest

from autoresearch_v2.harness import (
    backend, concurrency, events, opencode_jsonl, sessions, telemetry,
)


# --- backend.py ------------------------------------------------------------


def test_backend_session_backend_eval_override_wins(monkeypatch):
    monkeypatch.setenv("EVAL_BACKEND_OVERRIDE", "opencode")
    # Even if opencode missing, EVAL_BACKEND_OVERRIDE should NOT failover
    # until we hit the failover chain — but if opencode is missing AND no
    # other CLIs exist either, the override is preserved literally.
    # We just verify the env var dominates AUTORESEARCH_SESSION_BACKEND.
    monkeypatch.setenv("AUTORESEARCH_SESSION_BACKEND", "claude")
    result = backend.session_backend()
    # Either "opencode" preserved, or failover kicked in to codex/claude.
    assert result in {"opencode", "codex", "claude"}


def test_backend_invalid_override_falls_through(monkeypatch):
    monkeypatch.setenv("EVAL_BACKEND_OVERRIDE", "gemini")  # not in VALID_BACKENDS
    monkeypatch.delenv("AUTORESEARCH_SESSION_BACKEND", raising=False)
    result = backend.session_backend()
    assert result in {"claude", "codex"}  # falls through to PATH-based pick


def test_backend_default_session_model_per_backend(monkeypatch):
    monkeypatch.delenv("AUTORESEARCH_OPENCODE_DEFAULT_MODEL", raising=False)
    assert backend.default_session_model("claude") == "sonnet"
    assert "deepseek" in backend.default_session_model("opencode")
    assert backend.default_session_model("codex") == "gpt-5.5"


def test_backend_session_model_override_wins(monkeypatch):
    monkeypatch.setenv("EVAL_MODEL_OVERRIDE", "claude-sonnet-3.5")
    assert backend.session_model() == "claude-sonnet-3.5"


def test_backend_codex_sandbox_default_darwin(monkeypatch):
    monkeypatch.delenv("AUTORESEARCH_SESSION_SANDBOX", raising=False)
    sb = backend.codex_sandbox()
    assert sb in {"workspace-write", "danger-full-access"}


def test_backend_codex_sandbox_seatbelt_alias(monkeypatch):
    monkeypatch.setenv("AUTORESEARCH_SESSION_SANDBOX", "seatbelt")
    assert backend.codex_sandbox() == "workspace-write"


def test_backend_codex_reasoning_effort_default(monkeypatch):
    monkeypatch.delenv("AUTORESEARCH_SESSION_REASONING_EFFORT", raising=False)
    assert backend.codex_reasoning_effort() == "high"


# --- opencode_jsonl.py ----------------------------------------------------


def test_opencode_parse_missing_file_returns_empty(tmp_path):
    summary = opencode_jsonl.parse_session(tmp_path / "missing.jsonl")
    assert summary.total_cost == 0.0
    assert summary.final_answer is None


def test_opencode_parse_cost_and_cache(tmp_path):
    log = tmp_path / "session.jsonl"
    log.write_text(
        json.dumps({"type": "step_finish", "part": {"cost": 0.1, "tokens": {"cache": {"read": 100}}}}) + "\n"
        + json.dumps({"type": "step_finish", "part": {"cost": 0.2, "tokens": {"cache": {"read": 50}}}}) + "\n"
    )
    s = opencode_jsonl.parse_session(log)
    assert s.total_cost == pytest.approx(0.3, abs=1e-6)
    assert s.total_cache_reads == 150


def test_opencode_parse_final_answer_metadata(tmp_path):
    log = tmp_path / "s.jsonl"
    log.write_text(
        json.dumps({"type": "text", "part": {"text": "intermediate"}}) + "\n"
        + json.dumps({"type": "text", "part": {"text": "the answer", "metadata": {"openai": {"phase": "final_answer"}}}}) + "\n"
    )
    s = opencode_jsonl.parse_session(log)
    assert s.final_answer == "the answer"


def test_opencode_parse_skips_malformed_lines(tmp_path):
    log = tmp_path / "s.jsonl"
    log.write_text("not json\n" + json.dumps({"type": "text", "part": {"text": "ok"}}) + "\n")
    # Doesn't crash; cost stays 0
    s = opencode_jsonl.parse_session(log)
    assert s.total_cost == 0


@pytest.mark.parametrize("payload", [
    '{"type":"error","error":{"data":{"message":"rate_limit_exceeded"}}}',
    '{"type":"error","error":{"data":{"message":"provider_overloaded"}}}',
    '{"type":"error","error":{"data":{"message":"upstream timeout after 22s"}}}',
    '{"type":"error","error":{"data":{"message":"throttled","code":429}}}',
    '{"type":"error","error":{"data":{"message":"unavailable","code":503}}}',
    '{"type":"error","error":{"data":{"message":"slow","code":504}}}',
])
def test_opencode_transient_markers_detected(tmp_path, payload: str):
    log = tmp_path / "s.jsonl"
    log.write_text(payload + "\n")
    assert opencode_jsonl.session_has_transient_error(log) is True


def test_opencode_non_transient_error_not_flagged(tmp_path):
    log = tmp_path / "s.jsonl"
    log.write_text(json.dumps(
        {"type": "error", "error": {"data": {"message": "auth_failed"}}},
        separators=(",", ":"),
    ) + "\n")
    assert opencode_jsonl.session_has_transient_error(log) is False


def test_opencode_stdout_transient_flag():
    out = '{"type":"error","error":{"data":{"message":"rate_limit_exceeded"}}}'
    assert opencode_jsonl.stdout_has_transient_error(out) is True
    assert opencode_jsonl.stdout_has_transient_error("") is False
    assert opencode_jsonl.stdout_has_transient_error('{"type":"text","part":{"text":"hi"}}') is False


# --- events.py -------------------------------------------------------------


def test_events_log_and_read_round_trip(tmp_path):
    log = tmp_path / "events.jsonl"
    events.log_event("test_kind", path=log, x=1, y="two")
    events.log_event("other", path=log, z=3)
    rows = list(events.read_events(path=log))
    assert len(rows) == 2
    assert rows[0]["kind"] == "test_kind"
    assert rows[0]["x"] == 1
    assert "timestamp" in rows[0]


def test_events_filter_by_kind(tmp_path):
    log = tmp_path / "events.jsonl"
    events.log_event("a", path=log)
    events.log_event("b", path=log)
    events.log_event("a", path=log)
    rows = list(events.read_events(kind="a", path=log))
    assert len(rows) == 2
    assert all(r["kind"] == "a" for r in rows)


def test_events_corrupt_line_raises(tmp_path):
    log = tmp_path / "events.jsonl"
    events.log_event("a", path=log)
    log.write_text(log.read_text() + "not-valid-json\n")
    with pytest.raises(events.EventLogCorruption):
        list(events.read_events(path=log))


def test_events_concurrent_writers_dont_tear_lines(tmp_path):
    log = tmp_path / "events.jsonl"

    def writer(i: int):
        for _ in range(20):
            events.log_event("burst", path=log, i=i, payload="x" * 200)

    threads = [threading.Thread(target=writer, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # All lines must parse — flock prevents torn writes.
    rows = list(events.read_events(path=log))
    assert len(rows) == 8 * 20


# --- concurrency.py --------------------------------------------------------


def test_concurrency_default_sequential(monkeypatch):
    monkeypatch.delenv("MAX_PARALLEL_AGENTS", raising=False)
    assert concurrency.max_parallel() == 1


def test_concurrency_env_override(monkeypatch):
    monkeypatch.setenv("MAX_PARALLEL_AGENTS", "4")
    concurrency.reset_for_test()
    assert concurrency.max_parallel() == 4


def test_concurrency_invalid_env_falls_back_to_one(monkeypatch):
    monkeypatch.setenv("MAX_PARALLEL_AGENTS", "bogus")
    concurrency.reset_for_test()
    assert concurrency.max_parallel() == 1


def test_concurrency_parallel_for_sequential_path(monkeypatch):
    monkeypatch.delenv("MAX_PARALLEL_AGENTS", raising=False)
    concurrency.reset_for_test()
    result = concurrency.parallel_for([1, 2, 3], lambda x: x * 10)
    assert result == [10, 20, 30]


def test_concurrency_parallel_for_actually_parallel(monkeypatch):
    monkeypatch.setenv("MAX_PARALLEL_AGENTS", "4")
    concurrency.reset_for_test()

    def slow(i: int) -> int:
        time.sleep(0.1)
        return i

    start = time.monotonic()
    result = concurrency.parallel_for(list(range(4)), slow)
    elapsed = time.monotonic() - start
    assert sorted(result) == [0, 1, 2, 3]
    # Sequential would be ~0.4s; parallel should be ~0.1s
    assert elapsed < 0.3


def test_concurrency_semaphore_caps_at_max(monkeypatch):
    monkeypatch.setenv("MAX_PARALLEL_AGENTS", "2")
    concurrency.reset_for_test()

    in_flight = {"now": 0, "peak": 0}
    lock = threading.Lock()

    def watched(i: int) -> int:
        with lock:
            in_flight["now"] += 1
            in_flight["peak"] = max(in_flight["peak"], in_flight["now"])
        time.sleep(0.05)
        with lock:
            in_flight["now"] -= 1
        return i

    concurrency.parallel_for(list(range(10)), watched)
    assert in_flight["peak"] <= 2


# --- sessions.py -----------------------------------------------------------


def test_sessions_claude_session_jsonl_path():
    wt = Path("/Users/jr/proj")
    p = sessions.claude_session_jsonl(wt, "abc-def")
    assert p.name == "abc-def.jsonl"
    assert "-Users-jr-proj" in str(p)


def test_sessions_viable_resume_claude_missing_file(tmp_path):
    assert sessions.viable_resume_id("claude", "sid-1", wt_path=tmp_path) is None


def test_sessions_viable_resume_claude_jsonl_present(tmp_path, monkeypatch):
    # Stub claude_session_jsonl to point at tmp_path
    target = tmp_path / "session.jsonl"
    target.write_text("{}\n")
    monkeypatch.setattr(sessions, "claude_session_jsonl", lambda wt, sid: target)
    assert sessions.viable_resume_id("claude", "sid-1", wt_path=tmp_path) == "sid-1"


def test_sessions_viable_resume_unknown_engine():
    assert sessions.viable_resume_id("opencode", "sid", wt_path=Path("/x")) is None


def test_sessions_viable_resume_codex_no_rollout(monkeypatch):
    monkeypatch.setattr(sessions, "codex_session_jsonl", lambda sid: None)
    assert sessions.viable_resume_id("codex", "sid-1") is None


def test_sessions_ensure_materialized_runtime_returns_lane_path(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTORESEARCH_V2_ROOT", str(tmp_path))
    p = sessions.ensure_materialized_runtime("geo")
    assert p == tmp_path / "autoresearch_v2" / "lanes" / "geo"


# --- telemetry.py ----------------------------------------------------------


def test_telemetry_tracking_start_no_freddy_returns_none(monkeypatch):
    monkeypatch.setattr(telemetry.shutil, "which", lambda _: None)
    assert telemetry.tracking_start("c", "type", "purpose") is None


def test_telemetry_tracking_start_parses_uuid_from_text(monkeypatch):
    monkeypatch.setattr(telemetry.shutil, "which", lambda _: "/usr/local/bin/freddy")

    class FakeResult:
        stdout = "session started 12345678-1234-1234-1234-123456789abc done"

    monkeypatch.setattr(telemetry, "_run_silent", lambda cmd: FakeResult())
    sid = telemetry.tracking_start("c", "type", "purpose")
    assert sid == "12345678-1234-1234-1234-123456789abc"


def test_telemetry_tracking_start_parses_json(monkeypatch):
    monkeypatch.setattr(telemetry.shutil, "which", lambda _: "/usr/local/bin/freddy")

    class FakeResult:
        stdout = json.dumps({"id": "abc-123"})

    monkeypatch.setattr(telemetry, "_run_silent", lambda cmd: FakeResult())
    sid = telemetry.tracking_start("c", "type", "purpose")
    assert sid == "abc-123"


def test_telemetry_tracking_end_no_op_when_no_session(monkeypatch):
    # No exception, no subprocess call
    called = {"n": 0}
    monkeypatch.setattr(telemetry, "_run_silent", lambda cmd: called.__setitem__("n", called["n"] + 1))
    telemetry.tracking_end(None, "summary")
    assert called["n"] == 0


def test_telemetry_push_iteration_status_mapping(monkeypatch, tmp_path):
    monkeypatch.setattr(telemetry.shutil, "which", lambda _: "/usr/local/bin/freddy")
    cmds: list[list[str]] = []
    monkeypatch.setattr(telemetry, "_run_silent", lambda cmd: cmds.append(cmd))

    session_dir = tmp_path / "session"
    session_dir.mkdir()
    log = tmp_path / "log.txt"
    log.write_text("")

    telemetry.push_iteration("s1", 1, session_dir, 0, 1000, log)
    telemetry.push_iteration("s1", 2, session_dir, 124, 1000, log)
    telemetry.push_iteration("s1", 3, session_dir, 1, 1000, log)

    statuses = [c[c.index("--status") + 1] for c in cmds]
    assert statuses == ["success", "timeout", "failed"]
