"""Thin agent subprocess wrapper for the three agent invocations.

Public surface: evaluate, fix, verify. Each uses _run_agent with shared transient-error retry.
Supports two engines selected by config.engine: "claude" or "codex".
"""
from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import yaml

from harness import findings as findings_mod
from harness import prompts as prompts_mod
from harness.findings import Finding
from harness.sessions import SessionsFile

if TYPE_CHECKING:
    from harness.config import Config
    from harness.worktree import Worktree

# What we tell an agent when we're resuming its session. The original task is
# already in the conversation history — this short nudge just wakes it back up.
_RESUME_PROMPT = "Continue from where you left off."

log = logging.getLogger("harness.engine")

# Prose substrings — fuzzy matches on human-readable error surface from either CLI.
_TRANSIENT_SUBSTRINGS: tuple[str, ...] = (
    "stream disconnected", "Reconnecting", "overloaded",
    "rate limit", "API Error: 5", "Internal server error",  # claude 5xx surface
)

# Word-bounded regexes — numeric status codes that must not substring-match inside
# unrelated digits (e.g. "429" inside a timestamp or request id).
_TRANSIENT_REGEXES: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b429\b"),
    re.compile(r"\b502\b"),
    re.compile(r"\b503\b"),
)

# The `"type":"error"` stream-json event detection moved into _has_error_event
# below (mirrors parse_rate_limit's JSON-structural approach).
_RETRY_DELAYS = (5, 30, 120)
_AGENT_TIMEOUT = 1800  # 30min per agent invocation — bounds hung-agent deadlocks

# Orchestrator sets this via set_deadline() so _run_agent can short-circuit retries
# when the overall run budget is exhausted. Without this, retries on a timed-out
# subprocess can extend the run by ~2× _AGENT_TIMEOUT past max_walltime.
_deadline: float | None = None


def set_deadline(ts: float | None) -> None:
    """Set the absolute wall-clock deadline (epoch seconds) for all agent invocations.

    `None` disables the check (useful for tests). Thread-safe — all parallel tracks
    share one deadline, and Python assignment is atomic.
    """
    global _deadline
    _deadline = ts


class RateLimitHit(Exception):
    """Raised when Claude emits a rate_limit_event with status=rejected.

    The orchestrator catches this at the per-finding boundary and triggers graceful stop.
    """

    def __init__(self, resets_at: int = 0, rate_limit_type: str = "", overage_disabled_reason: str = "") -> None:
        self.resets_at = resets_at
        self.rate_limit_type = rate_limit_type
        self.overage_disabled_reason = overage_disabled_reason
        suffix = f" overage={overage_disabled_reason}" if overage_disabled_reason else ""
        super().__init__(
            f"rate limit hit (type={rate_limit_type}, resetsAt={resets_at}){suffix}"
        )


class EngineExhausted(Exception):
    """Raised when an agent subprocess exhausts its transient-retry budget."""


# Case-insensitive set of verdict tokens that count as "verified". Kept in sync
# with `harness/prompts/verifier.md` (the verifier is instructed to emit one of
# these). Membership check, not substring — prevents false positives like
# `verdict: "not verified"` matching on the trailing word.
_VERIFIED_TOKENS = frozenset({"verified", "pass", "passed", "ok"})


@dataclass(frozen=True)
class Verdict:
    verified: bool
    reason: str
    adjacent_checked: tuple[str, ...] = ()
    surface_changes_detected: bool = False

    @classmethod
    def parse(cls, path: Path) -> "Verdict":
        if not path.exists():
            return cls(verified=False, reason="no verdict file written")
        # Bug #17: verifier-written YAML has occasionally parsed as malformed
        # (smoke 20260422-224908 F-c-1-2: "mapping values are not allowed here"
        # but the file was valid YAML when inspected seconds later). Likely a
        # mid-write race or a partial-flush between the agent's writes. One
        # retry after 200ms handles both cases.
        data = None
        last_exc: Exception | None = None
        for attempt in (1, 2):
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                last_exc = None
                break
            except yaml.YAMLError as exc:
                last_exc = exc
                if attempt == 1:
                    time.sleep(0.2)
        if last_exc is not None:
            return cls(verified=False, reason=f"malformed verdict yaml: {last_exc}")
        verdict_str = str(data.get("verdict", "")).strip().lower()
        adjacent = data.get("adjacent_checked") or []
        if isinstance(adjacent, str):
            adjacent = [adjacent]
        return cls(
            verified=(verdict_str in _VERIFIED_TOKENS),
            reason=str(data.get("reason", "")).strip(),
            adjacent_checked=tuple(str(a) for a in adjacent),
            surface_changes_detected=bool(data.get("surface_changes_detected", False)),
        )


def evaluate(
    config: "Config", track: str, wt: "Worktree", cycle: int, run_dir: Path,
    sessions: SessionsFile | None = None, resume_session_id: str | None = None,
) -> list[Finding]:
    cycle_dir = run_dir / f"track-{track}" / f"cycle-{cycle}"
    cycle_dir.mkdir(parents=True, exist_ok=True)
    sentinel = cycle_dir / "sentinel.txt"
    findings_path = cycle_dir / "findings.md"
    output_log = cycle_dir / "agent.log"
    prompt_path = prompts_mod.render_evaluator(track, cycle, run_dir, wt.path)

    _run_agent(
        config, "eval", prompt_path, sentinel, wt, output_log,
        agent_key=f"eval-{track}-c{cycle}", sessions=sessions, resume_session_id=resume_session_id,
    )
    return findings_mod.parse(findings_path, cycle=cycle)


def fix(
    config: "Config", finding: Finding, wt: "Worktree", run_dir: Path,
    sessions: SessionsFile | None = None, resume_session_id: str | None = None,
) -> Path:
    fix_dir = run_dir / "fixes" / finding.track / finding.id
    fix_dir.mkdir(parents=True, exist_ok=True)
    sentinel = fix_dir / "sentinel.txt"
    output_log = fix_dir / "agent.log"
    prompt_path = prompts_mod.render_fixer(finding, run_dir, wt.path)
    _run_agent(
        config, "fix", prompt_path, sentinel, wt, output_log,
        agent_key=f"fix-{finding.id}", sessions=sessions, resume_session_id=resume_session_id,
    )
    return output_log


def verify(
    config: "Config", finding: Finding, wt: "Worktree", run_dir: Path,
    sessions: SessionsFile | None = None, resume_session_id: str | None = None,
) -> Verdict:
    verify_dir = run_dir / "verifies" / finding.track / finding.id
    verify_dir.mkdir(parents=True, exist_ok=True)
    sentinel = verify_dir / "sentinel.txt"
    output_log = verify_dir / "agent.log"
    verdict_dir = run_dir / "verdicts" / finding.track
    verdict_dir.mkdir(parents=True, exist_ok=True)
    verdict_path = verdict_dir / f"{finding.id}.yaml"
    prompt_path = prompts_mod.render_verifier(finding, run_dir)
    _run_agent(
        config, "verify", prompt_path, sentinel, wt, output_log,
        agent_key=f"verify-{finding.id}", sessions=sessions, resume_session_id=resume_session_id,
    )
    return Verdict.parse(verdict_path)


def _build_claude_cmd(
    prompt: str, model: str, mode: str, session_id: str, resume: bool = False,
) -> list[str]:
    """Construct the claude CLI command.

    - `--bare` (bare mode) skips user global config.
    - When `resume=True`, use `--resume <session_id>` + a short "continue" prompt:
      the original task is already in the conversation JSONL at
      `~/.claude/projects/<path>/<session_id>.jsonl`; claude reads it as history.
    - Otherwise, a fresh session is created via `--session-id <uuid>` with the full
      prompt as the first user turn.
    """
    cmd = ["claude"]
    if mode == "bare":
        cmd.append("--bare")
    cmd += ["-p", _RESUME_PROMPT if resume else prompt]
    cmd += [
        "--output-format", "stream-json",
        "--include-partial-messages", "--verbose",
    ]
    cmd += ["--resume" if resume else "--session-id", session_id]
    cmd += [
        "--model", model,
        "--dangerously-skip-permissions",
    ]
    return cmd


def _build_codex_cmd(profile: str, model_override: str) -> list[str]:
    """Construct the codex CLI command. Prompt is supplied via stdin (trailing '-')."""
    cmd = ["codex", "exec", "--profile", profile]
    if model_override:
        cmd += ["-m", model_override]
    cmd.append("-")
    return cmd


Role = Literal["eval", "fix", "verify"]

# Role → (claude model attr, codex profile attr, codex model-override attr)
_ROLE_CONFIG: dict[Role, tuple[str, str, str]] = {
    "eval":   ("eval_model",     "codex_eval_profile",     "codex_eval_model"),
    "fix":    ("fixer_model",    "codex_fixer_profile",    "codex_fixer_model"),
    "verify": ("verifier_model", "codex_verifier_profile", "codex_verifier_model"),
}


def parse_rate_limit(log_path: Path) -> RateLimitHit | None:
    """Return the FINAL rate-limit state from a claude stream-json log, or None.

    Rate-limit events fire at/near the end of each response stream. Read only the
    last 32 KB of the log — stream events are small (<500 bytes) so this covers
    ~100 recent events while capping memory + CPU at O(1) regardless of how long
    the agent session ran.

    Scans ALL events in the tail and returns the LAST one's state — if a prior
    rejection was followed by an "allowed" event, the agent recovered and we
    shouldn't trigger graceful stop on the stale rejection.
    """
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


def _has_error_event(tail: str) -> bool:
    """Return True iff the tail contains a claude stream-json event with
    `"type": "error"`. Mirrors `parse_rate_limit`'s JSON-structural approach —
    avoids substring false positives (e.g. a model echoing the literal string
    `"type":"error"` inside assistant content).
    """
    for raw in tail.splitlines():
        line = raw.strip()
        if not line.startswith("{"):
            continue
        try:
            data = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(data, dict) and data.get("type") == "error":
            return True
    return False


def _is_transient(log_path: Path) -> bool:
    if not log_path.exists():
        return False
    tail = log_path.read_text(encoding="utf-8", errors="replace")[-8000:]
    if any(pat in tail for pat in _TRANSIENT_SUBSTRINGS):
        return True
    if any(rx.search(tail) for rx in _TRANSIENT_REGEXES):
        return True
    return _has_error_event(tail)


def _run_agent(
    config: "Config",
    role: Role,
    prompt_path: Path,
    sentinel_path: Path,
    wt: "Worktree",
    output_path: Path,
    agent_key: str | None = None,
    sessions: SessionsFile | None = None,
    resume_session_id: str | None = None,
) -> None:
    """Run one agent invocation (claude or codex) with transient-error retry.

    Raises RateLimitHit if claude emits a rejected rate_limit_event (orchestrator → graceful stop).
    Raises EngineExhausted if all retries fail on transient errors.
    Raises RuntimeError on non-transient failures.

    When `sessions` is provided (and engine == "claude"), writes the session_id +
    status to sessions.json so a later `--resume-branch` invocation can continue
    this agent's conversation via `claude --resume <session_id>`. The session_id
    is stable across retries within a single call (fix for a prior bug where
    each retry regenerated the UUID and broke continuity).

    When `resume_session_id` is set, the first attempt uses `--resume <id>` with
    a short continuation prompt; retries within this call also reuse that ID so
    a rate-limit mid-resume still accumulates progress against the same session.
    """
    sentinel_path.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["PATH"] = f"{wt.path / '.venv' / 'bin'}:{env.get('PATH', '')}"
    # Worktree path first so `cli.freddy` / `src.api.main` imports resolve from the worktree,
    # not the main-repo-rooted editable install in .venv.
    env["PYTHONPATH"] = f"{wt.path}:{env.get('PYTHONPATH', '')}"
    # Route freddy CLI calls (reproductions, paraphrases) at THIS worker's backend,
    # not the operator's shared main-repo backend on 8000. Without this override,
    # `freddy <cmd>` inside the agent subprocess reads FREDDY_API_URL from inherited
    # shell env → hits stale pre-fix code → verifier sees the defect persist →
    # legitimate fix rolled back. Root-caused from run-20260424-131621 verifier log
    # where adding `FREDDY_API_URL=http://127.0.0.1:8003` manually got 200s for a
    # verdict that had just been written as 'failed'.
    if wt.backend_url:
        env["FREDDY_API_URL"] = wt.backend_url
        env["FREDDY_API_BASE_URL"] = wt.backend_url

    # Stable session ID for the whole invocation (was previously regenerated per
    # retry, which silently broke session continuity on the first retry).
    session_id = resume_session_id or str(uuid.uuid4())
    resume = resume_session_id is not None
    # Codex does not support session resume — sessions tracking is claude-only.
    track_sessions = sessions is not None and agent_key is not None and config.engine == "claude"
    if track_sessions:
        sessions.begin(agent_key, session_id, engine=config.engine)  # type: ignore[union-attr]

    def _finish(status: str) -> None:
        if track_sessions:
            sessions.finish(agent_key, status)  # type: ignore[arg-type,union-attr]

    for attempt, delay in enumerate((0,) + _RETRY_DELAYS):
        if delay:
            # Fix #2: don't retry if the orchestrator's walltime is already exhausted.
            # Without this check, retries extend the run by ~2× _AGENT_TIMEOUT past
            # max_walltime (since _AGENT_TIMEOUT is what triggers retries in the first place).
            if _deadline is not None and time.time() + delay > _deadline:
                # Deliberately leave status=running — a future --resume-branch can pick up.
                raise EngineExhausted(
                    f"{config.engine} (role={role}) retry {attempt} would exceed walltime; "
                    f"see {output_path}"
                )
            log.warning("transient error — retry %d in %ds", attempt, delay)
            time.sleep(delay)

        timed_out = False
        returncode = -1
        with open(output_path, "a", encoding="utf-8") as out_fp:
            out_fp.write(f"\n=== engine={config.engine} role={role} attempt={attempt} ===\n")
            out_fp.flush()
            claude_attr, codex_profile_attr, codex_model_attr = _ROLE_CONFIG[role]
            try:
                if config.engine == "claude":
                    prompt_text = prompt_path.read_text(encoding="utf-8")
                    # First attempt honors the caller's resume flag; subsequent retries
                    # always use `--resume` against the same session_id so partial progress
                    # carries across retries.
                    cmd = _build_claude_cmd(
                        prompt=prompt_text,
                        model=getattr(config, claude_attr),
                        mode=config.claude_mode,
                        session_id=session_id,
                        resume=resume or attempt > 0,
                    )
                    proc = subprocess.run(
                        cmd, cwd=wt.path, env=env,
                        stdout=out_fp, stderr=subprocess.STDOUT,
                        check=False, timeout=_AGENT_TIMEOUT,
                    )
                    returncode = proc.returncode
                else:  # codex
                    cmd = _build_codex_cmd(
                        profile=getattr(config, codex_profile_attr),
                        model_override=getattr(config, codex_model_attr),
                    )
                    with open(prompt_path, encoding="utf-8") as prompt_fp:
                        proc = subprocess.run(
                            cmd, cwd=wt.path, env=env,
                            stdin=prompt_fp, stdout=out_fp, stderr=subprocess.STDOUT,
                            check=False, timeout=_AGENT_TIMEOUT,
                        )
                        returncode = proc.returncode
            except subprocess.TimeoutExpired:
                timed_out = True
                out_fp.write(f"\n=== {config.engine} timed out after {_AGENT_TIMEOUT}s ===\n")

        # Fix #3: if the agent wrote the sentinel before the timeout killed its subprocess,
        # treat the timeout as a successful-but-slow run. Retrying would spawn a fresh
        # agent with no memory and waste another 30 min redoing completed work.
        if timed_out and sentinel_path.exists() and sentinel_path.stat().st_size > 0:
            log.info("%s (role=%s) timed out but sentinel was written — treating as success",
                     config.engine, role)
            _finish("complete")
            return

        # Fix #11: silent-hang rate-limit detection. When claude's 5h subscription
        # budget is exhausted AND overage is disabled (org_level_disabled), the
        # CLI hangs waiting for the API instead of emitting a `rate_limit_event`
        # with status=rejected. Overnight smoke run 20260422-224908 burned 4.5h
        # on 3 fixers × 4 retries of this exact stall (agent.log = 320 bytes of
        # our own banner, zero stream-json output, no JSONL created on claude-CLI
        # side). Heuristic cribbed from ralph.sh: if timed_out AND near-zero
        # output, treat as rate limit and graceful-stop on first occurrence.
        # 512-byte threshold is generous above our ~320-byte banner and orders of
        # magnitude below any real agent work (eval logs here are 1.7-2.3 MB).
        if timed_out and config.engine == "claude":
            try:
                output_size = output_path.stat().st_size
            except OSError:
                output_size = 0
            if output_size < 512:
                log.error(
                    "%s (role=%s) timed out with %d bytes output — likely silent "
                    "rate-limit stall; triggering graceful stop instead of retry",
                    config.engine, role, output_size,
                )
                raise RateLimitHit(
                    rate_limit_type="silent-hang",
                    overage_disabled_reason=(
                        "claude CLI produced no stream-json output before timeout"
                    ),
                )

        # Claude-only: deterministic rate-limit detection via stream-json event.
        if config.engine == "claude":
            hit = parse_rate_limit(output_path)
            if hit is not None:
                # Leave status=running so --resume-branch knows to pick this session back up.
                raise hit

        if timed_out:
            log.warning("%s (role=%s) timed out; treating as transient", config.engine, role)
            continue

        if returncode == 0:
            _finish("complete")
            return

        if not _is_transient(output_path):
            _finish("failed")
            raise RuntimeError(
                f"{config.engine} exited {returncode} (role={role}); see {output_path}"
            )

    # Exhausted retries. Leave status=running so --resume-branch can try again.
    raise EngineExhausted(
        f"{config.engine} exhausted {len(_RETRY_DELAYS)} retries (role={role}); see {output_path}"
    )


def read_sentinel(sentinel_path: Path) -> str | None:
    """Return the reason string from a sentinel file if it contains `done reason=<x>`, else None."""
    if not sentinel_path.exists():
        return None
    text = sentinel_path.read_text(encoding="utf-8").strip()
    match = re.match(r"done\s+reason=(\S+)", text)
    return match.group(1) if match else None
