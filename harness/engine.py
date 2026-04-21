"""Thin codex subprocess wrapper for the three agent invocations.

Public surface: evaluate, fix, verify. Each uses _run_codex with shared transient-error retry.
"""
from __future__ import annotations

import logging
import os
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

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
)
_RETRY_DELAYS = (5, 30, 120)
_CODEX_TIMEOUT = 1800  # 30min per codex invocation — bounds hung-agent deadlocks


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
    output_log = cycle_dir / "codex.log"
    prompt_path = prompts_mod.render_evaluator(track, cycle, run_dir, wt.path)

    _run_codex(config.codex_eval_profile, prompt_path, sentinel, wt, output_log)
    return findings_mod.parse(findings_path)


def fix(config: "Config", finding: Finding, wt: "Worktree", run_dir: Path) -> Path:
    fix_dir = run_dir / "fixes" / finding.track / finding.id
    fix_dir.mkdir(parents=True, exist_ok=True)
    sentinel = fix_dir / "sentinel.txt"
    output_log = fix_dir / "codex.log"
    prompt_path = prompts_mod.render_fixer(finding, run_dir)
    _run_codex(config.codex_fixer_profile, prompt_path, sentinel, wt, output_log)
    return output_log


def verify(config: "Config", finding: Finding, wt: "Worktree", run_dir: Path) -> Verdict:
    verify_dir = run_dir / "verifies" / finding.track / finding.id
    verify_dir.mkdir(parents=True, exist_ok=True)
    sentinel = verify_dir / "sentinel.txt"
    output_log = verify_dir / "codex.log"
    verdict_dir = run_dir / "verdicts" / finding.track
    verdict_dir.mkdir(parents=True, exist_ok=True)
    verdict_path = verdict_dir / f"{finding.id}.yaml"
    prompt_path = prompts_mod.render_verifier(finding, run_dir)
    _run_codex(config.codex_verifier_profile, prompt_path, sentinel, wt, output_log)
    return Verdict.parse(verdict_path)


def _run_codex(profile: str, prompt_path: Path, sentinel_path: Path, wt: "Worktree", output_path: Path) -> None:
    sentinel_path.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["PATH"] = f"{wt.path / '.venv' / 'bin'}:{env.get('PATH', '')}"

    for attempt, delay in enumerate((0,) + _RETRY_DELAYS):
        if delay:
            log.warning("transient error — retry %d in %ds", attempt, delay)
            time.sleep(delay)

        timed_out = False
        with open(prompt_path, encoding="utf-8") as prompt_fp, \
             open(output_path, "a", encoding="utf-8") as out_fp:
            out_fp.write(f"\n=== codex exec --profile {profile} attempt={attempt} ===\n")
            out_fp.flush()
            try:
                proc = subprocess.run(
                    ["codex", "exec", "--profile", profile],
                    cwd=wt.path,
                    env=env,
                    stdin=prompt_fp,
                    stdout=out_fp,
                    stderr=subprocess.STDOUT,
                    check=False,
                    timeout=_CODEX_TIMEOUT,
                )
            except subprocess.TimeoutExpired:
                timed_out = True
                out_fp.write(f"\n=== codex timed out after {_CODEX_TIMEOUT}s ===\n")

        if timed_out:
            log.warning("codex (profile=%s) timed out; treating as transient", profile)
            continue

        if proc.returncode == 0:
            return

        log_text = output_path.read_text(encoding="utf-8", errors="replace")[-8000:]
        if not any(pat in log_text for pat in _TRANSIENT_PATTERNS):
            raise RuntimeError(f"codex exited {proc.returncode} (profile={profile}); see {output_path}")

    raise RuntimeError(f"codex exhausted {len(_RETRY_DELAYS)} retries (profile={profile}); see {output_path}")


def read_sentinel(sentinel_path: Path) -> str | None:
    """Return the reason string from a sentinel file if it contains `done reason=<x>`, else None."""
    if not sentinel_path.exists():
        return None
    text = sentinel_path.read_text(encoding="utf-8").strip()
    match = re.match(r"done\s+reason=(\S+)", text)
    return match.group(1) if match else None
