"""Unified transient-error detection + retry policy for agent subprocesses.

Three spawn sites (``evolve.py:_run_meta_agent_once``,
``program_prescription_critic._call_critic``,
``harness/agent.py:run_agent_session``) all spawn claude/codex/opencode
subprocesses. Before this module, only opencode had retry logic — claude
and codex were single-shot, on the assumption that "claude/codex retry
internally and don't need wrapping." Empirical evidence from 9 evolution
runs (Apr 27-28) plus the v007 run (Apr 29) refutes this:

- claude can return exit=1 with empty stderr in <2s under rate-limit pressure
- claude `--bare` flag interaction with subscription auth produced "Not logged
  in" errors that look like transient failures (root cause fixed separately)
- codex can return exit=0 with last_agent_message=null on credit exhaustion
  (preflight catches this; transient mid-run cases still possible)

This module unifies the retry decision so all three sites get the same
exponential-backoff treatment. Backoff schedule mirrors the judge HTTP
retry: 2s, 8s, 30s — total worst-case ~40s before giving up.
"""
from __future__ import annotations

import time

# Override-able per-process. Defaults to 3 attempts (initial + 2 retries),
# tuned for transient rate-limit blips at minute scale. Operators can bump
# via OPENCODE_MAX_RETRIES (kept for backwards-compat with existing env).
import os

_MAX_ATTEMPTS = max(1, int(os.environ.get("OPENCODE_MAX_RETRIES", "3")))
_BACKOFF_DELAYS = (2.0, 8.0, 30.0)  # delays BETWEEN attempts

# 2026-05-13 Phase 3 dead-lane post-mortem: when claude/codex CLIs hit
# upstream rate-limit (Claude Max usage cap, codex per-window quota), the
# fast-retry policy above (3 attempts, ~40s) collapses long before the reset
# window (5min-1hr depending on plan + window). When ``is_rate_limit_failure``
# matches, callers should switch to the long-backoff schedule below — same
# pattern as ``evaluate_variant._post_with_retry`` rate-limit promotion.
_RATE_LIMIT_MAX_ATTEMPTS = max(1, int(os.environ.get("AGENT_RATE_LIMIT_MAX_ATTEMPTS", "6")))
_RATE_LIMIT_BACKOFF_DELAYS = (60.0, 120.0, 300.0, 600.0, 900.0)  # ~32min total

# CLI-output markers indicating upstream rate-limit (vs network blip / overload).
# Claude CLI prints "You've hit your limit · resets 1:40pm" on Max-plan caps.
# Codex CLI prints "rate_limit" / "rate_limit_exceeded" / "credits exhausted".
_RATE_LIMIT_MARKERS = (
    "hit your limit",
    "usage limit",
    "rate_limit_exceeded",
    "rate limit",
    "rate_limit",
    "resets at",
    "resets ",
    "quota exceeded",
    "429 ",
    "too many requests",
)


def max_attempts() -> int:
    """Total attempts (initial + retries) before giving up."""
    return _MAX_ATTEMPTS


def rate_limit_max_attempts() -> int:
    """Total attempts under the long-backoff (rate-limit) policy."""
    return _RATE_LIMIT_MAX_ATTEMPTS


def backoff_delay(attempt: int) -> float:
    """Seconds to sleep before retry attempt ``attempt`` (1-indexed).

    For attempt=1 returns 0 (no wait before first retry call).
    """
    if attempt < 1:
        return 0.0
    idx = min(attempt - 1, len(_BACKOFF_DELAYS) - 1)
    return _BACKOFF_DELAYS[idx]


def rate_limit_backoff_delay(attempt: int) -> float:
    """Seconds to sleep before retry attempt ``attempt`` (1-indexed) under
    the rate-limit-detected policy. Schedule: 60s, 120s, 300s, 600s, 900s."""
    if attempt < 1:
        return 0.0
    idx = min(attempt - 1, len(_RATE_LIMIT_BACKOFF_DELAYS) - 1)
    return _RATE_LIMIT_BACKOFF_DELAYS[idx]


def is_rate_limit_failure(
    stdout: bytes | str = b"",
    stderr: bytes | str = b"",
) -> bool:
    """Classify whether a transient failure is upstream rate-limit (CLI cap
    hit, needs long backoff) vs a generic blip (overload, network, fast retry).

    Used by callers in ``evolve.py:_run_meta_agent_once`` etc. to choose
    between ``backoff_delay`` (fast) and ``rate_limit_backoff_delay`` (long).
    Lane-agnostic — applies to every spawn site regardless of which lane
    the meta-agent is mutating.
    """
    combined = (_to_str(stdout) + "\n" + _to_str(stderr)).lower()
    return any(m in combined for m in _RATE_LIMIT_MARKERS)


def is_transient_claude_failure(returncode: int, stdout: bytes | str, stderr: bytes | str) -> bool:
    """Detect transient claude failures worth retrying.

    Patterns observed empirically:
    - Exit non-zero + empty stderr (<2s wall) — silent rate-limit / auth blip
    - Stderr contains rate-limit / overloaded markers
    - Stderr contains 5xx HTTP status

    Does NOT cover: "Not logged in" — that's terminal (auth missing, not
    transient). Caller should let it propagate as a hard error.
    """
    if returncode == 0:
        return False
    stdout_s = _to_str(stdout)
    stderr_s = _to_str(stderr)

    # "Not logged in" is terminal, not transient — bail out so caller can
    # surface it cleanly instead of burning retries.
    if "not logged in" in stdout_s.lower() or "not logged in" in stderr_s.lower():
        return False

    # Empty-stderr exit-1 silent failure pattern (the v3-v9 fingerprint).
    if not stderr_s.strip():
        return True

    # Explicit transient markers in stderr.
    return any(
        marker in stderr_s.lower()
        for marker in (
            "rate_limit", "rate limit",
            "overloaded", "provider_overloaded",
            "503 ", "504 ", "429 ",
            "timeout", "timed out",
            "connection reset", "broken pipe",
            "temporarily unavailable",
        )
    )


_CODEX_TERMINAL_MARKERS = (
    # Content moderation / safety filter — same prompt, same fixture, same
    # block. Retrying just burns credits. Pi v007 rakuten holdout surfaced
    # this with iter 2/3/4 producing identical 23KB outputs of:
    #   "ERROR: This content was flagged for possible cybersecurity risk"
    #   "https://chatgpt.com/cyber"
    "cybersecurity risk",
    "content was flagged",
    "flagged for possible",
)


def is_terminal_codex_failure(returncode: int, stdout: bytes | str, stderr: bytes | str) -> bool:
    """Detect codex failures that retrying CANNOT resolve (terminal).

    Distinct from transient: a terminal failure means the SAME prompt to
    the SAME backend will fail the same way on retry. The orchestrator
    should bail and surface a clear hint, not loop until max_iter.
    """
    combined = (_to_str(stdout) + "\n" + _to_str(stderr)).lower()
    return any(m in combined for m in _CODEX_TERMINAL_MARKERS)


def is_transient_codex_failure(returncode: int, stdout: bytes | str, stderr: bytes | str) -> bool:
    """Detect transient codex failures worth retrying.

    Patterns:
    - Exit non-zero + rate-limit markers in stderr
    - Exit 0 + null last_agent_message (credit exhaustion fingerprint —
      caught at preflight but can also occur mid-run when credits deplete)

    Terminal markers (content moderation, safety filter) explicitly return
    False — see ``is_terminal_codex_failure`` for the bail-fast helper.
    """
    stdout_s = _to_str(stdout)
    stderr_s = _to_str(stderr)
    combined = (stdout_s + "\n" + stderr_s).lower()

    # Terminal markers short-circuit transient classification.
    if any(m in combined for m in _CODEX_TERMINAL_MARKERS):
        return False

    if returncode != 0:
        return any(
            m in combined
            for m in (
                "rate_limit", "rate limit",
                "503 ", "504 ", "429 ",
                "timeout", "timed out",
                "connection reset", "broken pipe",
                "temporarily unavailable",
            )
        )

    # Exit 0 but credit exhaustion or null message — treat as transient
    # (sometimes a backend/quota glitch resolves on retry).
    return (
        "credits.has_credits: false" in combined
        or "rate_limit_exceeded" in combined
    )


def is_transient_opencode_failure(
    returncode: int, log_path_or_stdout: "object",
) -> bool:
    """Wraps the existing opencode-jsonl helpers for parity with the
    claude/codex variants. Accepts either a Path (log file) or stdout str.
    """
    # Two import styles support invocation from (a) the launcher path
    # which adds autoresearch/harness/ to sys.path so `harness` is a
    # top-level package, or (b) test-isolation contexts where the test
    # file imports the autoresearch.harness sub-package directly.
    # Pre-fix the bare import broke isolated test runs of the critic +
    # opencode-retry tests with ModuleNotFoundError.
    try:
        from harness.opencode_jsonl import (
            session_has_transient_error,
            stdout_has_transient_error,
        )
    except ImportError:
        from autoresearch.harness.opencode_jsonl import (  # type: ignore[no-redef]
            session_has_transient_error,
            stdout_has_transient_error,
        )
    from pathlib import Path

    if isinstance(log_path_or_stdout, Path):
        return session_has_transient_error(log_path_or_stdout)
    if isinstance(log_path_or_stdout, str):
        return stdout_has_transient_error(log_path_or_stdout)
    return False


def is_transient_failure(
    backend: str,
    returncode: int,
    stdout: bytes | str = b"",
    stderr: bytes | str = b"",
) -> bool:
    """Unified transient-error detector across all three backends.

    Use this from spawn-site retry loops. Returns True iff the failure
    pattern is worth retrying with backoff. Returns False on success
    (returncode == 0 and no transient signal) or on terminal failures
    (auth missing, malformed input, etc.) — those should propagate.
    """
    if backend == "claude":
        return is_transient_claude_failure(returncode, stdout, stderr)
    if backend == "codex":
        return is_transient_codex_failure(returncode, stdout, stderr)
    if backend == "opencode":
        return is_transient_opencode_failure(returncode, _to_str(stdout))
    return False


def sleep_for_retry(attempt: int) -> None:
    """Wrapper around time.sleep for testability — tests can monkeypatch
    ``time.sleep`` on this module without affecting other code."""
    time.sleep(backoff_delay(attempt))


def _to_str(b: bytes | str) -> str:
    if isinstance(b, bytes):
        return b.decode("utf-8", errors="replace")
    return b or ""
