"""Post-fix outcome checks. Lightweight replacement for protected-files snapshot + leak guard."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

SCOPE_ALLOWLIST: dict[str, re.Pattern[str]] = {
    "a": re.compile(r"^(cli/freddy/|pyproject\.toml$)"),
    "b": re.compile(r"^(src/|autoresearch/)"),
    "c": re.compile(r"^frontend/"),
}


def check_scope(wt: Path, pre_sha: str, track: str) -> list[str] | None:
    """Return files the fixer touched that fall outside the track's allowlist, or None if clean.

    Diffs `pre_sha..HEAD` inside the worktree.
    """
    pattern = SCOPE_ALLOWLIST[track]
    result = subprocess.run(
        ["git", "diff", "--name-only", pre_sha, "HEAD"],
        cwd=wt,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git diff failed: {result.stderr.strip()}")
    violations = [p.strip() for p in result.stdout.splitlines() if p.strip() and not pattern.match(p.strip())]
    return violations or None


def check_no_leak(pre_dirty_set: set[str], main_repo: Path | None = None) -> list[str] | None:
    """Return files in the main repo that became dirty since `pre_dirty_set` was captured, or None.

    `pre_dirty_set` is a snapshot of `git status --porcelain` lines (stripped path tokens),
    captured once at orchestrator startup. Anything new = fixer leaked outside the worktree.
    """
    repo = main_repo if main_repo is not None else Path.cwd()
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git status failed: {result.stderr.strip()}")
    current = {line[3:].strip() for line in result.stdout.splitlines() if line.strip()}
    leaked = sorted(current - pre_dirty_set)
    return leaked or None


def snapshot_dirty(main_repo: Path | None = None) -> set[str]:
    """Capture the current set of dirty paths in the main repo for later leak comparison."""
    repo = main_repo if main_repo is not None else Path.cwd()
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git status failed: {result.stderr.strip()}")
    return {line[3:].strip() for line in result.stdout.splitlines() if line.strip()}
