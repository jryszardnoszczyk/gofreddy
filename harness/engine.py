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

if TYPE_CHECKING:
    from harness.config import Config
    from harness.worktree import Worktree

log = logging.getLogger("harness.engine")

_TRANSIENT_PATTERNS = (
    "429", "stream disconnected", "Reconnecting", "overloaded",
    "rate limit", "503", "502",
    "API Error: 5", "Internal server error",  # claude 5xx surface
    '"type":"error"',  # claude stream-json error events
)
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
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            return cls(verified=False, reason=f"malformed verdict yaml: {exc}")
        verdict_str = str(data.get("verdict", "")).strip()
        adjacent = data.get("adjacent_checked") or []
        if isinstance(adjacent, str):
            adjacent = [adjacent]
        return cls(
            verified=(verdict_str == "verified"),
            reason=str(data.get("reason", "")).strip(),
            adjacent_checked=tuple(str(a) for a in adjacent),
            surface_changes_detected=bool(data.get("surface_changes_detected", False)),
        )


def evaluate(config: "Config", track: str, wt: "Worktree", cycle: int, run_dir: Path) -> list[Finding]:
    cycle_dir = run_dir / f"track-{track}" / f"cycle-{cycle}"
    cycle_dir.mkdir(parents=True, exist_ok=True)
    sentinel = cycle_dir / "sentinel.txt"
    findings_path = cycle_dir / "findings.md"
    output_log = cycle_dir / "agent.log"
    prompt_path = prompts_mod.render_evaluator(track, cycle, run_dir, wt.path)

    _run_agent(config, "eval", prompt_path, sentinel, wt, output_log)
    return findings_mod.parse(findings_path)


def fix(config: "Config", finding: Finding, wt: "Worktree", run_dir: Path) -> Path:
    fix_dir = run_dir / "fixes" / finding.track / finding.id
    fix_dir.mkdir(parents=True, exist_ok=True)
    sentinel = fix_dir / "sentinel.txt"
    output_log = fix_dir / "agent.log"
    prompt_path = prompts_mod.render_fixer(finding, run_dir)
    _run_agent(config, "fix", prompt_path, sentinel, wt, output_log)
    return output_log


def verify(config: "Config", finding: Finding, wt: "Worktree", run_dir: Path) -> Verdict:
    verify_dir = run_dir / "verifies" / finding.track / finding.id
    verify_dir.mkdir(parents=True, exist_ok=True)
    sentinel = verify_dir / "sentinel.txt"
    output_log = verify_dir / "agent.log"
    verdict_dir = run_dir / "verdicts" / finding.track
    verdict_dir.mkdir(parents=True, exist_ok=True)
    verdict_path = verdict_dir / f"{finding.id}.yaml"
    prompt_path = prompts_mod.render_verifier(finding, run_dir)
    _run_agent(config, "verify", prompt_path, sentinel, wt, output_log)
    return Verdict.parse(verdict_path)


def _build_claude_cmd(prompt: str, model: str, mode: str, session_id: str) -> list[str]:
    """Construct the claude CLI command. `--bare` (bare mode) skips user global config."""
    cmd = ["claude"]
    if mode == "bare":
        cmd.append("--bare")
    cmd += [
        "-p", prompt,
        "--output-format", "stream-json",
        "--include-partial-messages", "--verbose",
        "--session-id", session_id,
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


def _is_transient(log_path: Path) -> bool:
    if not log_path.exists():
        return False
    tail = log_path.read_text(encoding="utf-8", errors="replace")[-8000:]
    return any(pat in tail for pat in _TRANSIENT_PATTERNS)


def _run_agent(
    config: "Config",
    role: Role,
    prompt_path: Path,
    sentinel_path: Path,
    wt: "Worktree",
    output_path: Path,
) -> None:
    """Run one agent invocation (claude or codex) with transient-error retry.

    Raises RateLimitHit if claude emits a rejected rate_limit_event (orchestrator → graceful stop).
    Raises EngineExhausted if all retries fail on transient errors.
    Raises RuntimeError on non-transient failures.
    """
    sentinel_path.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["PATH"] = f"{wt.path / '.venv' / 'bin'}:{env.get('PATH', '')}"
    # Worktree path first so `cli.freddy` / `src.api.main` imports resolve from the worktree,
    # not the main-repo-rooted editable install in .venv.
    env["PYTHONPATH"] = f"{wt.path}:{env.get('PYTHONPATH', '')}"

    for attempt, delay in enumerate((0,) + _RETRY_DELAYS):
        if delay:
            # Fix #2: don't retry if the orchestrator's walltime is already exhausted.
            # Without this check, retries extend the run by ~2× _AGENT_TIMEOUT past
            # max_walltime (since _AGENT_TIMEOUT is what triggers retries in the first place).
            if _deadline is not None and time.time() + delay > _deadline:
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
                    cmd = _build_claude_cmd(
                        prompt=prompt_text,
                        model=getattr(config, claude_attr),
                        mode=config.claude_mode,
                        session_id=str(uuid.uuid4()),
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
            return

        # Claude-only: deterministic rate-limit detection via stream-json event.
        if config.engine == "claude":
            hit = parse_rate_limit(output_path)
            if hit is not None:
                raise hit

        if timed_out:
            log.warning("%s (role=%s) timed out; treating as transient", config.engine, role)
            continue

        if returncode == 0:
            return

        if not _is_transient(output_path):
            raise RuntimeError(
                f"{config.engine} exited {returncode} (role={role}); see {output_path}"
            )

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
