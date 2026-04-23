"""Tests for harness.engine — engine conditional, command construction, rate-limit parsing."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from harness.engine import (
    EngineExhausted,
    RateLimitHit,
    _build_claude_cmd,
    _build_codex_cmd,
    _is_transient,
    parse_rate_limit,
)


def test_build_claude_cmd_oauth_mode_excludes_bare():
    cmd = _build_claude_cmd(prompt="hello", model="opus", mode="oauth", session_id="s1")
    assert cmd[0] == "claude"
    assert "--bare" not in cmd
    assert "-p" in cmd
    assert "hello" in cmd
    assert "--output-format" in cmd and "stream-json" in cmd
    assert "--model" in cmd and "opus" in cmd
    assert "--session-id" in cmd and "s1" in cmd
    assert "--dangerously-skip-permissions" in cmd


def test_build_claude_cmd_bare_mode_includes_bare():
    cmd = _build_claude_cmd(prompt="hello", model="opus", mode="bare", session_id="s1")
    assert cmd[0] == "claude"
    assert "--bare" in cmd
    # --bare must come early, before -p, so it's interpreted as a top-level flag
    assert cmd.index("--bare") < cmd.index("-p")


def test_build_claude_cmd_resume_uses_resume_flag_and_continue_prompt():
    """Resume invocations must use --resume <id> (not --session-id <id>) and send
    the short continuation prompt, because the original task is in the JSONL."""
    cmd = _build_claude_cmd(
        prompt="full original task prompt — must NOT be sent on resume",
        model="opus", mode="oauth", session_id="sid-abc", resume=True,
    )
    assert "--resume" in cmd
    assert "--session-id" not in cmd
    assert "sid-abc" in cmd
    # Continue prompt, not the original task prompt.
    idx = cmd.index("-p")
    assert cmd[idx + 1] == "Continue from where you left off."
    assert "full original task prompt" not in " ".join(cmd)


def test_build_claude_cmd_fresh_uses_session_id_and_full_prompt():
    cmd = _build_claude_cmd(
        prompt="full task", model="opus", mode="oauth", session_id="sid-new",
    )
    assert "--session-id" in cmd
    assert "--resume" not in cmd
    assert "sid-new" in cmd
    idx = cmd.index("-p")
    assert cmd[idx + 1] == "full task"


def test_build_codex_cmd_matches_current_shape():
    cmd = _build_codex_cmd(profile="harness-fixer", model_override="")
    assert cmd == ["codex", "exec", "--profile", "harness-fixer", "-"]


def test_build_codex_cmd_with_model_override():
    cmd = _build_codex_cmd(profile="harness-fixer", model_override="gpt-5")
    assert cmd[:4] == ["codex", "exec", "--profile", "harness-fixer"]
    assert "-m" in cmd and "gpt-5" in cmd
    assert cmd[-1] == "-"


def _write_lines(path: Path, lines: list[dict | str]) -> None:
    path.write_text(
        "\n".join(json.dumps(line) if isinstance(line, dict) else line for line in lines),
        encoding="utf-8",
    )


def test_parse_rate_limit_returns_hit_when_rejected(tmp_path):
    log = tmp_path / "agent.log"
    _write_lines(log, [
        {"type": "assistant", "message": {"content": "hi"}},
        {"type": "rate_limit_event", "rate_limit_info": {
            "status": "rejected", "resetsAt": 1776855600, "rateLimitType": "five_hour",
            "overageDisabledReason": "org_level_disabled"}},
    ])
    hit = parse_rate_limit(log)
    assert isinstance(hit, RateLimitHit)
    assert hit.resets_at == 1776855600
    assert hit.rate_limit_type == "five_hour"
    assert hit.overage_disabled_reason == "org_level_disabled"


def test_parse_rate_limit_returns_none_when_allowed(tmp_path):
    log = tmp_path / "agent.log"
    _write_lines(log, [
        {"type": "rate_limit_event", "rate_limit_info": {
            "status": "allowed", "resetsAt": 1776855600, "rateLimitType": "five_hour"}},
    ])
    assert parse_rate_limit(log) is None


def test_parse_rate_limit_skips_malformed_lines(tmp_path):
    log = tmp_path / "agent.log"
    log.write_text(
        "not json at all\n"
        "=== header ===\n"
        + json.dumps({"type": "rate_limit_event", "rate_limit_info": {
            "status": "rejected", "resetsAt": 42, "rateLimitType": "five_hour"}}) + "\n",
        encoding="utf-8",
    )
    hit = parse_rate_limit(log)
    assert isinstance(hit, RateLimitHit)
    assert hit.resets_at == 42


def test_parse_rate_limit_returns_none_for_missing_file(tmp_path):
    assert parse_rate_limit(tmp_path / "nope.log") is None


def test_parse_rate_limit_returns_none_for_empty_file(tmp_path):
    log = tmp_path / "agent.log"
    log.write_text("", encoding="utf-8")
    assert parse_rate_limit(log) is None


def test_parse_rate_limit_returns_none_when_rejected_followed_by_allowed(tmp_path):
    """Agent recovered within the same stream — the stale rejection is moot."""
    log = tmp_path / "agent.log"
    _write_lines(log, [
        {"type": "rate_limit_event", "rate_limit_info": {
            "status": "rejected", "resetsAt": 1776855600, "rateLimitType": "five_hour"}},
        {"type": "assistant", "message": {"content": "retrying..."}},
        {"type": "rate_limit_event", "rate_limit_info": {
            "status": "allowed", "resetsAt": 1776855600, "rateLimitType": "five_hour"}},
    ])
    assert parse_rate_limit(log) is None


def test_parse_rate_limit_reads_only_tail(tmp_path):
    """Verify performance-safety invariant: only the tail of the log is scanned.
    Prepending 100KB of garbage must not affect detection of an event near the end."""
    log = tmp_path / "agent.log"
    garbage = "x" * 100_000 + "\n"
    event = json.dumps({"type": "rate_limit_event", "rate_limit_info": {
        "status": "rejected", "resetsAt": 42, "rateLimitType": "five_hour"}})
    log.write_text(garbage + event + "\n", encoding="utf-8")
    hit = parse_rate_limit(log)
    assert isinstance(hit, RateLimitHit)
    assert hit.resets_at == 42


def test_is_transient_detects_codex_patterns(tmp_path):
    log = tmp_path / "agent.log"
    log.write_text("something\nAPI error: 429\nother\n", encoding="utf-8")
    assert _is_transient(log) is True


def test_is_transient_detects_claude_5xx_pattern(tmp_path):
    log = tmp_path / "agent.log"
    log.write_text("API Error: 503 Service Unavailable\n", encoding="utf-8")
    assert _is_transient(log) is True


def test_is_transient_detects_claude_overloaded(tmp_path):
    log = tmp_path / "agent.log"
    log.write_text("Internal server error: overloaded\n", encoding="utf-8")
    assert _is_transient(log) is True


def test_is_transient_false_for_clean_log(tmp_path):
    log = tmp_path / "agent.log"
    log.write_text("all good here\n", encoding="utf-8")
    assert _is_transient(log) is False


def test_is_transient_detects_claude_json_error_event(tmp_path):
    """Plan: Claude: ... + JSON "type":"error" events — transient detection must fire."""
    log = tmp_path / "agent.log"
    log.write_text(
        '{"type":"assistant","message":{"content":"hi"}}\n'
        '{"type":"error","message":{"code":"stream_error"}}\n',
        encoding="utf-8",
    )
    assert _is_transient(log) is True


def test_rate_limit_hit_is_exception():
    # Must propagate out of _run_agent so orchestrator can catch it.
    assert issubclass(RateLimitHit, Exception)


def test_engine_exhausted_is_exception():
    assert issubclass(EngineExhausted, Exception)


def test_set_deadline_round_trips():
    """Thread-safe deadline setter — getter round-trip via module attr."""
    import harness.engine as engine_mod
    engine_mod.set_deadline(123456789.0)
    assert engine_mod._deadline == 123456789.0
    engine_mod.set_deadline(None)
    assert engine_mod._deadline is None


def test_run_agent_respects_sentinel_on_timeout(tmp_path, monkeypatch):
    """Fix #3: when agent writes sentinel then subprocess times out, treat as success
    (no retry). Without this, a productive agent that ran slightly past budget would
    be retried from scratch, wasting 30+ min of fresh context rebuild."""
    import subprocess as sp
    import harness.engine as engine_mod
    from harness.config import Config
    from harness.worktree import Worktree

    sentinel = tmp_path / "sentinel.txt"
    prompt = tmp_path / "p.md"
    prompt.write_text("hello", encoding="utf-8")
    output = tmp_path / "agent.log"
    wt = Worktree(path=tmp_path, branch="main", main_repo=tmp_path)

    def fake_run(*args, **kwargs):
        # Simulate: agent wrote sentinel during run, then subprocess timed out.
        sentinel.write_text("done reason=agent-signaled-done\n", encoding="utf-8")
        raise sp.TimeoutExpired(cmd=args[0] if args else "claude", timeout=1)
    monkeypatch.setattr(engine_mod.subprocess, "run", fake_run)

    # No exception should be raised — treated as success.
    engine_mod._run_agent(Config(engine="claude"), "eval", prompt, sentinel, wt, output)


def test_run_agent_respects_walltime_in_retry_loop(tmp_path, monkeypatch):
    """Fix #2: if the overall deadline passes during a retry delay, raise
    EngineExhausted instead of waiting + re-spawning. Prevents runs from
    exceeding max_walltime by 2× when subprocess timeouts keep triggering retries."""
    import subprocess as sp
    import harness.engine as engine_mod
    from harness.config import Config
    from harness.worktree import Worktree

    sentinel = tmp_path / "sentinel.txt"
    prompt = tmp_path / "p.md"
    prompt.write_text("hello", encoding="utf-8")
    output = tmp_path / "agent.log"
    wt = Worktree(path=tmp_path, branch="main", main_repo=tmp_path)

    # Agent keeps timing out without writing sentinel — normally would retry 3 times.
    def always_timeout(*args, **kwargs):
        raise sp.TimeoutExpired(cmd="claude", timeout=1)
    monkeypatch.setattr(engine_mod.subprocess, "run", always_timeout)

    # Set deadline 0.5s in the future; after the first timeout the retry check will fire.
    import time as time_mod
    engine_mod.set_deadline(time_mod.time() + 0.5)
    try:
        with pytest.raises(EngineExhausted, match="exceed walltime"):
            engine_mod._run_agent(Config(engine="claude"), "eval", prompt, sentinel, wt, output)
    finally:
        engine_mod.set_deadline(None)


def test_run_agent_walltime_check_noop_when_deadline_unset(tmp_path, monkeypatch):
    """Defensive: if set_deadline was never called (None), retries proceed normally."""
    import subprocess as sp
    import harness.engine as engine_mod
    from harness.config import Config
    from harness.worktree import Worktree

    sentinel = tmp_path / "sentinel.txt"
    prompt = tmp_path / "p.md"
    prompt.write_text("hello", encoding="utf-8")
    output = tmp_path / "agent.log"
    wt = Worktree(path=tmp_path, branch="main", main_repo=tmp_path)

    # After 2 timeouts, the agent "succeeds" (rc=0). Without walltime check, retries proceed.
    call_count = {"n": 0}
    def flaky_run(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] <= 2:
            raise sp.TimeoutExpired(cmd="claude", timeout=1)
        # Third call succeeds.
        class R:
            returncode = 0
        return R()
    monkeypatch.setattr(engine_mod.subprocess, "run", flaky_run)
    # Make retry sleeps instant for the test.
    monkeypatch.setattr(engine_mod.time, "sleep", lambda _: None)

    engine_mod.set_deadline(None)
    engine_mod._run_agent(Config(engine="claude"), "eval", prompt, sentinel, wt, output)
    assert call_count["n"] == 3  # completed the retry chain


def test_run_agent_silent_hang_raises_rate_limit_hit(tmp_path, monkeypatch):
    """Fix #11: When claude times out with <512 bytes of output, treat as silent
    subscription rate-limit and raise RateLimitHit on FIRST occurrence instead
    of retrying 3x. Overnight smoke 20260422-224908 burned 4.5h retrying the
    same silent stall — this detection exits graceful-stop after ~30 min."""
    import subprocess as sp
    import harness.engine as engine_mod
    from harness.config import Config
    from harness.worktree import Worktree

    sentinel = tmp_path / "sentinel.txt"
    prompt = tmp_path / "p.md"
    prompt.write_text("hello", encoding="utf-8")
    output = tmp_path / "agent.log"
    wt = Worktree(path=tmp_path, branch="main", main_repo=tmp_path)

    def fake_run(*args, **kwargs):
        # Simulate a silent hang: write only our 80-byte banner, never stream.
        # _run_agent writes the banner via out_fp before subprocess.run returns.
        raise sp.TimeoutExpired(cmd="claude", timeout=1)
    monkeypatch.setattr(engine_mod.subprocess, "run", fake_run)

    with pytest.raises(engine_mod.RateLimitHit, match="silent-hang"):
        engine_mod._run_agent(Config(engine="claude"), "fix", prompt, sentinel, wt, output)


def test_run_agent_silent_hang_heuristic_does_not_trip_on_codex(tmp_path, monkeypatch):
    """The silent-hang heuristic is claude-specific — codex's hang/error surface
    is different and goes through the existing transient detection path."""
    import subprocess as sp
    import harness.engine as engine_mod
    from harness.config import Config
    from harness.worktree import Worktree

    sentinel = tmp_path / "sentinel.txt"
    prompt = tmp_path / "p.md"
    prompt.write_text("hello", encoding="utf-8")
    output = tmp_path / "agent.log"
    wt = Worktree(path=tmp_path, branch="main", main_repo=tmp_path)

    calls = {"n": 0}
    def fake_run(*args, **kwargs):
        calls["n"] += 1
        raise sp.TimeoutExpired(cmd="codex", timeout=1)
    monkeypatch.setattr(engine_mod.subprocess, "run", fake_run)
    monkeypatch.setattr(engine_mod.time, "sleep", lambda _: None)
    engine_mod.set_deadline(None)

    # Codex silent hangs do NOT raise RateLimitHit — they go through the
    # normal transient-retry chain and eventually raise EngineExhausted.
    with pytest.raises(engine_mod.EngineExhausted):
        engine_mod._run_agent(Config(engine="codex"), "fix", prompt, sentinel, wt, output)
    assert calls["n"] == 4  # 1 initial + 3 retries


def test_run_agent_silent_hang_threshold_allows_sentinel_success(tmp_path, monkeypatch):
    """Ordering check: sentinel-on-timeout (Fix #3) must short-circuit BEFORE
    silent-hang detection (Fix #11). A productive agent that wrote the sentinel
    but produced <512 bytes (tiny test prompt case) should still be treated as
    success, not RateLimitHit."""
    import subprocess as sp
    import harness.engine as engine_mod
    from harness.config import Config
    from harness.worktree import Worktree

    sentinel = tmp_path / "sentinel.txt"
    prompt = tmp_path / "p.md"
    prompt.write_text("hello", encoding="utf-8")
    output = tmp_path / "agent.log"
    wt = Worktree(path=tmp_path, branch="main", main_repo=tmp_path)

    def fake_run(*args, **kwargs):
        sentinel.write_text("done reason=agent-signaled-done\n", encoding="utf-8")
        raise sp.TimeoutExpired(cmd="claude", timeout=1)
    monkeypatch.setattr(engine_mod.subprocess, "run", fake_run)

    # Sentinel wins — no RateLimitHit.
    engine_mod._run_agent(Config(engine="claude"), "fix", prompt, sentinel, wt, output)
