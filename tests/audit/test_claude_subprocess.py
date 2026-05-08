"""Tests for src/audit/claude_subprocess — 3 factories + envelope parser + rate-limit parser."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.audit.claude_subprocess import (
    ResultMessage,
    build_cmd_meta,
    build_cmd_short_json,
    build_cmd_streaming,
    build_env,
    parse_rate_limit,
    parse_result_message,
)
from src.audit.exceptions import RateLimitHit


# ---------------------------------------------------------------------------
# parse_result_message — net-new, the load-bearing capability
# ---------------------------------------------------------------------------


def _success_envelope(**overrides) -> dict:
    """Captured fixture envelope from a successful claude --output-format json run.
    Field shape per Key Decision §Execution model ResultMessage field semantics."""
    base = {
        "type": "result",
        "subtype": "success",
        "session_id": "01J9Z9P0ABCDE-fake-uuid",
        "result": "Hello world",
        "is_error": False,
        "duration_ms": 4567,
        "duration_api_ms": 3210,
        "num_turns": 1,
        "total_cost_usd": 0.0421,
        "stop_reason": "end_turn",
        "usage": {
            "input_tokens": 234,
            "output_tokens": 56,
            "cache_creation_input_tokens": 12,
            "cache_read_input_tokens": 100,
        },
    }
    base.update(overrides)
    return base


def test_parse_success_envelope_extracts_all_fields():
    msg = parse_result_message(_success_envelope())
    assert isinstance(msg, ResultMessage)
    assert msg.subtype == "success"
    assert msg.session_id == "01J9Z9P0ABCDE-fake-uuid"
    assert msg.result == "Hello world"
    assert msg.is_error is False
    assert msg.duration_ms == 4567
    assert msg.duration_api_ms == 3210
    assert msg.num_turns == 1
    assert msg.total_cost_usd == 0.0421
    assert msg.stop_reason == "end_turn"
    assert msg.input_tokens == 234
    assert msg.output_tokens == 56
    assert msg.cache_creation_input_tokens == 12
    assert msg.cache_read_input_tokens == 100
    assert msg.errors == ()


def test_parse_subscription_envelope_with_zero_cost_still_parses_tokens():
    """Subscription billing may set total_cost_usd=0 — token counts must still
    parse so cost_ledger can fall back to tokens × rates inferred cost."""
    envelope = _success_envelope(total_cost_usd=0.0)
    msg = parse_result_message(envelope)
    assert msg.total_cost_usd == 0.0
    assert msg.input_tokens == 234
    assert msg.output_tokens == 56


def test_parse_error_envelope_max_turns():
    envelope = {
        "type": "result",
        "subtype": "error_max_turns",
        "session_id": "sid-err-1",
        "is_error": True,
        "errors": ["max turns exceeded"],
        "duration_ms": 12000,
        "duration_api_ms": 8000,
        "num_turns": 100,
        "total_cost_usd": 0.5,
        "stop_reason": "max_turns",
        "usage": {
            "input_tokens": 1000,
            "output_tokens": 500,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0,
        },
    }
    msg = parse_result_message(envelope)
    assert msg.subtype == "error_max_turns"
    assert msg.is_error is True
    assert msg.errors == ("max turns exceeded",)
    assert msg.result is None
    assert msg.duration_api_ms == 8000


def test_parse_envelope_missing_optional_fields_defaults_safely():
    """An envelope missing duration_api_ms (older claude versions) still parses;
    duration_api_ms defaults to 0 so R29 SLA math doesn't break."""
    envelope = {
        "subtype": "success",
        "session_id": "sid-min",
        "result": "ok",
        "is_error": False,
        "duration_ms": 100,
        # duration_api_ms omitted
        "num_turns": 1,
        "total_cost_usd": 0.001,
        # stop_reason omitted
        # usage omitted
    }
    msg = parse_result_message(envelope)
    assert msg.duration_api_ms == 0
    assert msg.stop_reason == ""
    assert msg.input_tokens == 0
    assert msg.output_tokens == 0


def test_parse_malformed_envelope_raises_value_error():
    """Non-dict envelope is a programmer error — fail loud, don't paper over."""
    with pytest.raises(ValueError):
        parse_result_message("not a dict")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        parse_result_message([1, 2, 3])  # type: ignore[arg-type]


def test_parse_envelope_without_subtype_raises():
    with pytest.raises(ValueError, match="subtype"):
        parse_result_message({"session_id": "x"})


# ---------------------------------------------------------------------------
# parse_rate_limit — port of harness/engine.py:275 (file-based)
# ---------------------------------------------------------------------------


def test_parse_rate_limit_no_file(tmp_path: Path):
    assert parse_rate_limit(tmp_path / "no-such-log.jsonl") is None


def test_parse_rate_limit_empty_file(tmp_path: Path):
    log = tmp_path / "log.jsonl"
    log.write_text("", encoding="utf-8")
    assert parse_rate_limit(log) is None


def test_parse_rate_limit_rejected_event(tmp_path: Path):
    log = tmp_path / "log.jsonl"
    log.write_text(
        json.dumps({
            "type": "rate_limit_event",
            "rate_limit_info": {
                "status": "rejected",
                "resetsAt": 1735689600,
                "rateLimitType": "5h",
                "overageDisabledReason": "account_disabled",
            },
        }) + "\n",
        encoding="utf-8",
    )
    hit = parse_rate_limit(log)
    assert isinstance(hit, RateLimitHit)
    assert hit.resets_at == 1735689600
    assert hit.rate_limit_type == "5h"
    assert hit.overage_disabled_reason == "account_disabled"


def test_parse_rate_limit_recovery_clears_prior_rejection(tmp_path: Path):
    """A prior 'rejected' followed by 'allowed' means agent recovered — stale
    rejection should not trigger graceful stop."""
    log = tmp_path / "log.jsonl"
    log.write_text(
        json.dumps({
            "type": "rate_limit_event",
            "rate_limit_info": {"status": "rejected", "resetsAt": 100, "rateLimitType": "5h"},
        }) + "\n" + json.dumps({
            "type": "rate_limit_event",
            "rate_limit_info": {"status": "allowed"},
        }) + "\n",
        encoding="utf-8",
    )
    assert parse_rate_limit(log) is None


def test_parse_rate_limit_skips_malformed_lines(tmp_path: Path):
    log = tmp_path / "log.jsonl"
    log.write_text(
        "garbage\n" +
        "{not json\n" +
        json.dumps({"type": "other_event"}) + "\n" +
        json.dumps({
            "type": "rate_limit_event",
            "rate_limit_info": {"status": "rejected", "resetsAt": 555, "rateLimitType": "5h"},
        }) + "\n",
        encoding="utf-8",
    )
    hit = parse_rate_limit(log)
    assert hit is not None
    assert hit.resets_at == 555


# ---------------------------------------------------------------------------
# build_cmd_streaming — Pattern A
# ---------------------------------------------------------------------------


def test_build_cmd_streaming_fresh_session(tmp_path: Path):
    cwd = tmp_path
    cmd = build_cmd_streaming(
        prompt="run lens L-A-01",
        model="claude-opus-4-7",
        session_id="11111111-1111-1111-1111-111111111111",
        cwd=cwd,
    )
    assert cmd[0] == "claude"
    assert "-p" in cmd
    # Fresh session uses --session-id, NOT --resume
    assert "--session-id" in cmd
    assert "--resume" not in cmd
    assert "11111111-1111-1111-1111-111111111111" in cmd
    # Streaming flags
    assert "--output-format" in cmd
    assert "stream-json" in cmd
    assert "--include-partial-messages" in cmd
    assert "--verbose" in cmd
    assert "--model" in cmd
    assert "claude-opus-4-7" in cmd
    assert "--dangerously-skip-permissions" in cmd
    # Prompt is the actual user prompt (no _RESUME continue-prompt)
    p_idx = cmd.index("-p")
    assert cmd[p_idx + 1] == "run lens L-A-01"


def test_build_cmd_streaming_resume_uses_resume_flag(tmp_path: Path):
    cwd = tmp_path
    cmd = build_cmd_streaming(
        prompt="DETAILED_LENS_PROMPT_123_should_not_appear_in_resume_cmd",
        model="claude-opus-4-7",
        session_id="22222222-2222-2222-2222-222222222222",
        cwd=cwd,
        resume=True,
    )
    assert "--resume" in cmd
    assert "--session-id" not in cmd
    # The user-supplied prompt is replaced by a short continuation seed;
    # the actual task lives in the persisted conversation JSONL.
    p_idx = cmd.index("-p")
    assert "DETAILED_LENS_PROMPT_123" not in cmd[p_idx + 1]


def test_build_cmd_streaming_max_turns_optional(tmp_path: Path):
    cwd = tmp_path
    cmd = build_cmd_streaming(
        prompt="x", model="m", session_id="s", cwd=cwd, max_turns=42,
    )
    assert "--max-turns" in cmd
    assert "42" in cmd


def test_build_cmd_requires_existing_cwd(tmp_path: Path):
    bogus = tmp_path / "not-a-dir"
    with pytest.raises(AssertionError):
        build_cmd_streaming(prompt="x", model="m", session_id="s", cwd=bogus)


# ---------------------------------------------------------------------------
# build_cmd_meta — Pattern B
# ---------------------------------------------------------------------------


def test_build_cmd_meta_default_tools(tmp_path: Path):
    cmd = build_cmd_meta(model="claude-opus-4-7", max_turns=50, cwd=tmp_path)
    assert cmd[0] == "claude"
    assert "-p" in cmd
    assert "--model" in cmd and "claude-opus-4-7" in cmd
    assert "--max-turns" in cmd and "50" in cmd
    assert "--allowedTools" in cmd
    # Default allowed tools should include filesystem + search
    tools_idx = cmd.index("--allowedTools")
    assert "Read" in cmd[tools_idx + 1]
    assert "Write" in cmd[tools_idx + 1]


def test_build_cmd_meta_custom_tools(tmp_path: Path):
    cmd = build_cmd_meta(
        model="m", max_turns=10, cwd=tmp_path, allowed_tools="Read,Grep",
    )
    tools_idx = cmd.index("--allowedTools")
    assert cmd[tools_idx + 1] == "Read,Grep"


# ---------------------------------------------------------------------------
# build_cmd_short_json — Pattern C
# ---------------------------------------------------------------------------


def test_build_cmd_short_json_includes_session_id(tmp_path: Path):
    cmd = build_cmd_short_json(
        prompt="rate this output", model="claude-opus-4-7", cwd=tmp_path,
    )
    assert cmd[0] == "claude"
    assert "-p" in cmd
    assert "--output-format" in cmd
    assert "json" in cmd
    assert "--session-id" in cmd  # auto-mints UUID if not supplied
    assert "--model" in cmd and "claude-opus-4-7" in cmd
    assert "--dangerously-skip-permissions" in cmd


def test_build_cmd_short_json_explicit_session_id(tmp_path: Path):
    cmd = build_cmd_short_json(
        prompt="x", model="m", cwd=tmp_path, session_id="33333333-3333-3333-3333-333333333333",
    )
    sid_idx = cmd.index("--session-id")
    assert cmd[sid_idx + 1] == "33333333-3333-3333-3333-333333333333"


# ---------------------------------------------------------------------------
# build_env — env sanitization (13-key allowlist)
# ---------------------------------------------------------------------------


def test_build_env_strips_unknown_keys(monkeypatch):
    monkeypatch.setenv("PATH", "/usr/bin")
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "tok-test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "key-test")
    monkeypatch.setenv("RANDOM_LEAKY_VAR", "should-not-leak")
    env = build_env()
    assert env["PATH"] == "/usr/bin"
    assert env["CLAUDE_CODE_OAUTH_TOKEN"] == "tok-test"
    assert env["ANTHROPIC_API_KEY"] == "key-test"
    assert "RANDOM_LEAKY_VAR" not in env


def test_build_env_omits_keys_not_in_parent_env(monkeypatch):
    """Keys in the allowlist that AREN'T set in the parent env should not be
    forced into the subprocess env (subprocess inherits absence)."""
    monkeypatch.delenv("FREDDY_API_URL", raising=False)
    env = build_env()
    assert "FREDDY_API_URL" not in env
