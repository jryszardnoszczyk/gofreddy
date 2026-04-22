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

# A "fixer-reachable" leak is a file under any track's scope. Paths outside every
# track's allowlist (docs/, .claude/, harness/, tests/, README, etc.) can't be
# fixer-caused even if they became dirty during a run — concurrent dev activity
# on those paths is not a leak from the harness's perspective.
_FIXER_REACHABLE = re.compile(r"^(cli/freddy/|pyproject\.toml$|src/|autoresearch/|frontend/)")

# Paths the harness itself generates inside the worktree. Not fixer-originated,
# must not count as scope violations or get staged into commits.
# - `harness/blocked-<id>.md`: the fixer prompt tells the agent to write one of
#   these when it can't fix the defect (see prompts/fixer.md). It's a signal, not a fix.
# - `sessions/`: the freddy CLI's default output dir. Any fixer or verifier running
#   a `freddy audit/client/...` command as part of repro writes here as a side effect.
HARNESS_ARTIFACTS = re.compile(
    r"^(backend\.log$|\.venv(/|$)|node_modules(/|$)|clients(/|$)|"
    r"frontend/node_modules(/|$)|harness/blocked-[^/]+\.md$|sessions(/|$))"
)


def working_tree_changes(wt: Path) -> list[str]:
    """Return every path the fixer changed in the worktree (modified + untracked),
    excluding harness-generated artifacts. Uses -z for null-terminated records so
    paths with spaces don't break parsing, and -uall so untracked files are listed
    individually instead of collapsed to their parent directory.
    """
    result = subprocess.run(
        ["git", "status", "--porcelain", "-z", "-uall"],
        cwd=wt, capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git status failed: {result.stderr.strip()}")
    paths: list[str] = []
    for record in result.stdout.split("\x00"):
        if not record:
            continue
        # record is "XY path" where XY is 2-char status code + space
        path = record[3:]
        if not path or HARNESS_ARTIFACTS.match(path):
            continue
        paths.append(path)
    return paths


def check_scope(wt: Path, pre_sha: str, track: str) -> list[str] | None:
    """Return paths the fixer touched that fall outside the track's allowlist, or None if clean.

    Uses working-tree changes (not commit diff), because the fixer leaves its edits
    uncommitted — the orchestrator commits them only after scope + leak checks pass.

    Under parallel execution, files matching any OTHER track's allowlist are assumed
    to be peer fixers' in-flight edits. Those are excluded from this track's
    attribution — they will be validated by their own track's check_scope.
    """
    pattern = SCOPE_ALLOWLIST[track]
    other_patterns = [p for t, p in SCOPE_ALLOWLIST.items() if t != track]
    paths = working_tree_changes(wt)
    candidates = [p for p in paths if not any(op.match(p) for op in other_patterns)]
    violations = [p for p in candidates if not pattern.match(p)]
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
    new_dirty = current - pre_dirty_set
    # Only paths under some track's scope can plausibly be fixer-caused leaks.
    leaked = sorted(p for p in new_dirty if _FIXER_REACHABLE.match(p))
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
