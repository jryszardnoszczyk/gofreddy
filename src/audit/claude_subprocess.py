"""Three claude-CLI invocation factories + envelope/rate-limit parsers.

Consolidates the three CLI patterns already present in the codebase
(harness Pattern A, autoresearch Pattern B, autoresearch Pattern C) behind
a single audit-side helper so every Bundle A+B caller goes through one
place. Subscription-only billing per Key Decision §Execution model;
multi-provider OpenCode dispatch is deliberately NOT mirrored here.

The three factories all require ``cwd: Path`` to be the audit directory
(``clients/<slug>/audit/<audit_id>/``). Claude maps cwd to a projects/
subdir by replacing ``/`` with ``-`` when persisting the conversation
JSONL; ``--resume <session_id>`` later only finds the JSONL if cwd
matches. Mismatched cwd → silent resume failure → orphan re-run with
fresh session.

References:
- Pattern A: harness/engine.py:228 _build_claude_cmd
- Pattern B: autoresearch/evolve.py:602 _build_meta_command (claude branch)
- Pattern C: autoresearch/compute_metrics.py:259-305 _build_alert_cmd (claude branch)
- parse_rate_limit: harness/engine.py:275 (port verbatim)
- env allowlist: autoresearch/evolve.py:74 _CLAUDE_ENV_KEYS
"""
from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.audit.exceptions import RateLimitHit


# 13-key allowlist copied from autoresearch/evolve.py:74. Subscription billing
# uses CLAUDE_CODE_OAUTH_TOKEN; ANTHROPIC_API_KEY retained as defensive
# fallback. If both are set, claude CLI prefers OAuth (verified empirically).
_CLAUDE_ENV_KEYS: tuple[str, ...] = (
    "PATH", "HOME", "USER", "SHELL", "TERM", "LANG", "TMPDIR",
    "SSH_AUTH_SOCK", "ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN",
    "FREDDY_API_URL", "FREDDY_API_KEY", "OPENAI_API_KEY",
)

# Continuation-prompt seed sent when --resume is in play. Original task is
# already in the conversation JSONL; claude reads it as history. Anything
# substantive here would shift the agent's understanding of the task.
_RESUME_PROMPT = "continue"


# ---------------------------------------------------------------------------
# ResultMessage — typed envelope for `claude -p --output-format json`
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ResultMessage:
    """Structured view of claude's `--output-format json` result envelope.

    Field semantics per Key Decision §Execution model ResultMessage field
    semantics. ``duration_api_ms`` is the API-only time (R29 SLA basis);
    ``duration_ms`` is wall-clock incl. local tool execution. Subscription
    billing typically populates ``total_cost_usd`` (Anthropic's estimate);
    if it's 0 on subscription, cost_ledger falls back to tokens × rates.
    """

    subtype: str  # "success" | "error_max_turns" | "error_during_execution" | "error_max_budget_usd" | "error_max_structured_output_retries"
    session_id: str
    is_error: bool
    duration_ms: int
    duration_api_ms: int
    num_turns: int
    total_cost_usd: float
    stop_reason: str
    result: str | None  # populated on success subtype
    errors: tuple[str, ...]  # populated on error subtypes
    input_tokens: int
    output_tokens: int
    cache_creation_input_tokens: int
    cache_read_input_tokens: int


def parse_result_message(envelope: Any) -> ResultMessage:
    """Parse claude's ``--output-format json`` result envelope into a typed
    ``ResultMessage``.

    Raises ``ValueError`` if the envelope is not a dict or lacks the
    ``subtype`` discriminator. Optional fields default to safe values
    (0 / "" / None / ()) so older claude versions or partial envelopes
    don't crash the parser — the caller reads the typed fields and
    decides what to do."""
    if not isinstance(envelope, dict):
        raise ValueError(f"expected dict envelope, got {type(envelope).__name__}")
    subtype = envelope.get("subtype")
    if not isinstance(subtype, str):
        raise ValueError("envelope missing required 'subtype' field")

    usage = envelope.get("usage") or {}
    if not isinstance(usage, dict):
        usage = {}

    raw_errors = envelope.get("errors") or ()
    if isinstance(raw_errors, str):
        errors: tuple[str, ...] = (raw_errors,)
    else:
        errors = tuple(str(e) for e in raw_errors)

    result_value = envelope.get("result")
    if subtype != "success":
        result_value = None  # contractually empty on error subtypes
    elif not isinstance(result_value, str):
        result_value = None  # tolerate odd success envelopes without result text

    return ResultMessage(
        subtype=subtype,
        session_id=str(envelope.get("session_id", "")),
        is_error=bool(envelope.get("is_error", subtype != "success")),
        duration_ms=int(envelope.get("duration_ms", 0) or 0),
        duration_api_ms=int(envelope.get("duration_api_ms", 0) or 0),
        num_turns=int(envelope.get("num_turns", 0) or 0),
        total_cost_usd=float(envelope.get("total_cost_usd", 0.0) or 0.0),
        stop_reason=str(envelope.get("stop_reason", "")),
        result=result_value,
        errors=errors,
        input_tokens=int(usage.get("input_tokens", 0) or 0),
        output_tokens=int(usage.get("output_tokens", 0) or 0),
        cache_creation_input_tokens=int(usage.get("cache_creation_input_tokens", 0) or 0),
        cache_read_input_tokens=int(usage.get("cache_read_input_tokens", 0) or 0),
    )


# ---------------------------------------------------------------------------
# parse_rate_limit — port verbatim from harness/engine.py:275
# ---------------------------------------------------------------------------


def parse_rate_limit(log_path: Path) -> RateLimitHit | None:
    """Return the FINAL rate-limit state from a claude stream-json log, or None.

    Rate-limit events fire at/near the end of each response stream. Read only
    the last 32 KB of the log — stream events are small (<500 bytes) so this
    covers ~100 recent events while capping memory + CPU at O(1) regardless
    of how long the agent session ran.

    Scans ALL events in the tail and returns the LAST one's state — if a
    prior rejection was followed by an "allowed" event, the agent recovered
    and we shouldn't trigger graceful stop on the stale rejection.

    Port of harness/engine.py:275 with the exception type swapped to the
    audit-side ``src.audit.exceptions.RateLimitHit`` (which has the same
    field shape as ``harness.engine.RateLimitHit``)."""
    log_path = Path(log_path)
    if not log_path.exists():
        return None
    try:
        with open(log_path, "rb") as fp:
            fp.seek(0, 2)  # end
            size = fp.tell()
            fp.seek(max(0, size - 32_000))
            tail = fp.read().decode("utf-8", errors="replace")
    except OSError:
        return None
    if not tail.strip():
        return None
    last_hit: RateLimitHit | None = None
    for raw in tail.splitlines():
        line = raw.strip()
        if not line.startswith("{"):
            continue
        try:
            data = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        if not isinstance(data, dict) or data.get("type") != "rate_limit_event":
            continue
        info = data.get("rate_limit_info") or {}
        if not isinstance(info, dict):
            continue
        status = info.get("status")
        if status == "rejected":
            try:
                resets_at = int(info.get("resetsAt", 0))
            except (TypeError, ValueError):
                resets_at = 0
            last_hit = RateLimitHit(
                resets_at=resets_at,
                rate_limit_type=str(info.get("rateLimitType", "")),
                overage_disabled_reason=str(info.get("overageDisabledReason", "")),
            )
        elif status == "allowed":
            last_hit = None  # agent recovered within this stream — stale rejection is moot
    return last_hit


# ---------------------------------------------------------------------------
# Three CLI factories
# ---------------------------------------------------------------------------


def build_cmd_streaming(
    prompt: str,
    model: str,
    session_id: str,
    cwd: Path,
    resume: bool = False,
    max_turns: int | None = None,
) -> list[str]:
    """Pattern A — long-form streaming with resume, used by Stage 2 lens agents.

    When ``resume=True``, the user-supplied ``prompt`` is replaced by a short
    continuation seed; the actual task lives in the persisted JSONL at
    ``~/.claude/projects/<encoded-cwd>/<session_id>.jsonl``. ``--resume``
    and ``--session-id`` are mutually exclusive (claude rejects both)."""
    assert cwd.is_dir(), f"cwd must be an existing dir: {cwd}"
    cmd = [
        "claude",
        "-p", _RESUME_PROMPT if resume else prompt,
        "--output-format", "stream-json",
        "--include-partial-messages", "--verbose",
    ]
    cmd += ["--resume" if resume else "--session-id", session_id]
    cmd += ["--model", model, "--dangerously-skip-permissions"]
    if max_turns is not None:
        cmd += ["--max-turns", str(max_turns)]
    return cmd


def build_cmd_meta(
    model: str,
    max_turns: int,
    cwd: Path,
    allowed_tools: str | None = None,
) -> list[str]:
    """Pattern B — Stage 1b brief-gen, Stage 3 synthesis, Stage 4 proposal.
    One-shot but long-form; prompt fed via stdin (caller passes prompt as
    subprocess input, NOT as argv)."""
    assert cwd.is_dir(), f"cwd must be an existing dir: {cwd}"
    tools = allowed_tools if allowed_tools is not None else "Bash,Read,Write,Edit,Glob,Grep"
    return [
        "claude", "-p",
        "--model", model,
        "--allowedTools", tools,
        "--max-turns", str(max_turns),
    ]


def build_cmd_short_json(
    prompt: str,
    model: str,
    cwd: Path,
    session_id: str | None = None,
) -> list[str]:
    """Pattern C — critic calls, MA-1..MA-8 rubric judges, R24 redaction pass.
    Short prompt (passed via argv), single-turn, returns JSON envelope."""
    assert cwd.is_dir(), f"cwd must be an existing dir: {cwd}"
    sid = session_id if session_id is not None else str(uuid.uuid4())
    return [
        "claude",
        "-p", prompt,
        "--output-format", "json",
        "--session-id", sid,
        "--model", model,
        "--dangerously-skip-permissions",
    ]


# ---------------------------------------------------------------------------
# Env sanitization
# ---------------------------------------------------------------------------


def build_env() -> dict[str, str]:
    """Build a sanitized env dict with only the 13 allowlisted keys, mirroring
    ``autoresearch/evolve.py:74`` ``_CLAUDE_ENV_KEYS``. Keys absent from the
    parent env are not included in the subprocess env — preserves "unset"
    semantics so claude CLI's auto-detection of OAuth vs API key works."""
    return {key: os.environ[key] for key in _CLAUDE_ENV_KEYS if key in os.environ}
