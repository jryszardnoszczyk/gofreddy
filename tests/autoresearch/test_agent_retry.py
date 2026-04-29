"""Tests for autoresearch/agent_retry.py — unified transient-error
detection across claude/codex/opencode subprocess spawns.

Backed by empirical findings from the Apr 27-29 evolution runs:
- claude --bare auth bug surfaced as exit=1 + empty stderr (terminal)
- claude rate-limit pressure surfaces as exit=1 + empty stderr (transient)
- codex credit exhaustion surfaces as last_agent_message: null (transient
  from a single-call POV; preflight catches the persistent case)
"""
from __future__ import annotations


# Import via conftest's autoresearch sys.path setup
import agent_retry


# --------------------------------------------------------------------------
# claude transient detection
# --------------------------------------------------------------------------


def test_claude_success_is_not_transient():
    """Exit 0 with normal output: not transient."""
    assert agent_retry.is_transient_claude_failure(0, "ok", "") is False


def test_claude_empty_stderr_exit1_is_transient():
    """The v3-v9 critic + meta-agent silent-fail fingerprint: exit nonzero
    with empty stderr = rate-limit blip. Retry."""
    assert agent_retry.is_transient_claude_failure(1, "", "") is True


def test_claude_not_logged_in_is_NOT_transient():
    """Auth missing is terminal — retry won't help, propagate immediately."""
    assert agent_retry.is_transient_claude_failure(1, "Not logged in", "") is False
    assert agent_retry.is_transient_claude_failure(1, "", "Not logged in") is False


def test_claude_rate_limit_marker_is_transient():
    assert agent_retry.is_transient_claude_failure(1, "", "rate_limit_exceeded") is True
    assert agent_retry.is_transient_claude_failure(1, "", "Rate limit hit") is True


def test_claude_overloaded_is_transient():
    assert agent_retry.is_transient_claude_failure(1, "", "provider_overloaded") is True


def test_claude_5xx_is_transient():
    assert agent_retry.is_transient_claude_failure(1, "", "API returned 503 ") is True
    assert agent_retry.is_transient_claude_failure(1, "", "504 gateway timeout") is True


def test_claude_429_is_transient():
    assert agent_retry.is_transient_claude_failure(1, "", "got 429 too many requests") is True


def test_claude_timeout_is_transient():
    assert agent_retry.is_transient_claude_failure(124, "", "Request timed out") is True


def test_claude_real_error_with_stderr_is_NOT_transient():
    """Exit nonzero with a real error message that's not a known transient
    marker should propagate, not retry forever."""
    assert agent_retry.is_transient_claude_failure(2, "", "ParseError: malformed JSON") is False
    assert agent_retry.is_transient_claude_failure(1, "", "Permission denied") is False


# --------------------------------------------------------------------------
# codex transient detection
# --------------------------------------------------------------------------


def test_codex_success_is_not_transient():
    assert agent_retry.is_transient_codex_failure(0, "task_complete: ok", "") is False


def test_codex_credit_exhaustion_is_transient():
    """Mid-run credit exhaustion: codex returns exit 0 + null message."""
    assert agent_retry.is_transient_codex_failure(
        0, "task_complete\ncredits.has_credits: false\n", ""
    ) is True


def test_codex_rate_limit_with_nonzero_is_transient():
    assert agent_retry.is_transient_codex_failure(1, "", "rate_limit_exceeded") is True


def test_codex_5xx_with_nonzero_is_transient():
    assert agent_retry.is_transient_codex_failure(1, "", "503 service unavailable") is True


def test_codex_real_error_with_nonzero_is_NOT_transient():
    """Exit nonzero with no transient marker = real error, don't retry."""
    assert agent_retry.is_transient_codex_failure(2, "", "Invalid model name") is False


# --------------------------------------------------------------------------
# unified dispatcher
# --------------------------------------------------------------------------


def test_dispatcher_routes_by_backend():
    # claude path: empty-stderr exit-1 → transient
    assert agent_retry.is_transient_failure("claude", 1, b"", b"") is True
    # codex path: same shape NOT transient (codex isn't tracked the same way)
    assert agent_retry.is_transient_failure("codex", 1, b"", b"") is False


def test_dispatcher_handles_bytes_input():
    """Real subprocess output is bytes; helper must coerce."""
    assert agent_retry.is_transient_failure(
        "claude", 1, stdout=b"", stderr=b"rate_limit_exceeded"
    ) is True


def test_dispatcher_unknown_backend_returns_false():
    """Unknown backend → don't retry (avoid infinite loops on misconfig)."""
    assert agent_retry.is_transient_failure("bogus", 1, b"", b"") is False


# --------------------------------------------------------------------------
# backoff schedule
# --------------------------------------------------------------------------


def test_backoff_delay_schedule():
    """2s/8s/30s — total ~40s before giving up. Mirrors judge HTTP retry."""
    assert agent_retry.backoff_delay(1) == 2.0
    assert agent_retry.backoff_delay(2) == 8.0
    assert agent_retry.backoff_delay(3) == 30.0


def test_backoff_delay_clamps_high_attempts():
    """Beyond the schedule, hold at the largest delay."""
    assert agent_retry.backoff_delay(99) == 30.0


def test_backoff_delay_zero_for_invalid_attempt():
    assert agent_retry.backoff_delay(0) == 0.0
    assert agent_retry.backoff_delay(-1) == 0.0


def test_max_attempts_default():
    assert agent_retry.max_attempts() >= 1


# --------------------------------------------------------------------------
# integration — sleep_for_retry calls time.sleep with right delay
# --------------------------------------------------------------------------


def test_sleep_for_retry_uses_backoff(monkeypatch):
    """sleep_for_retry must read the backoff schedule, not hardcode."""
    sleeps = []
    monkeypatch.setattr(agent_retry.time, "sleep", lambda s: sleeps.append(s))
    agent_retry.sleep_for_retry(1)
    agent_retry.sleep_for_retry(2)
    agent_retry.sleep_for_retry(3)
    assert sleeps == [2.0, 8.0, 30.0]
