"""Harness-bound Tier C leak detection + static surface-preservation check.

Per-track SCOPE_ALLOWLIST + check_scope have been REMOVED. The fixer prompt
describes each track's surface; we trust the agent to stay in its lane.
Under the per-worker isolation model, peer fixers cannot interfere with
each other anyway (each worker owns its own worktree), so the regex-based
containment was belt-and-suspenders that caused more false rollbacks than
it prevented real damage.

What remains here: main-repo leak detection (catches fixers writing absolute
paths outside their worktree into the parent repo), working-tree-changes
for commit staging, and `surface_check` — static detection of public-surface
breaks (removed function signatures, CLI flag deletions) that replaces the
verifier's probe #4 agent invocation with a ~10ms Python check.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from harness.config import HARNESS_ARTIFACTS, _FIXER_REACHABLE
from src.shared.safety import tier_c as _tier_c

__all__ = [
    "HARNESS_ARTIFACTS",
    "check_no_leak",
    "snapshot_dirty",
    "surface_check",
    "working_tree_changes",
]


# Patterns flagged by `surface_check`. Conservative — false positives here
# just mean the fixer gets a "re-review manually" signal; false negatives
# mean the verifier agent has to catch it via probe 5/6. Bias toward recall.
_SIGNATURE_REMOVAL = re.compile(
    r"^-\s*(?:async\s+)?(?:def|class|function|export\s+(?:function|const|default|class))\s+"
)
_CLI_FLAG_REMOVAL = re.compile(r'^-.*(?:add_argument|argparse)\s*\(\s*"(--[a-z0-9-]+)"')
_ROUTE_REMOVAL = re.compile(
    r'^-\s*@(?:app|router)\.(?:get|post|put|patch|delete)\s*\(\s*"([^"]+)"'
)


def surface_check(wt_path: Path, base_sha: str, head_sha: str) -> list[str]:
    """Return list of public-surface break violations between two commits.

    Replaces verifier probe #4 ("Surface preserved") with a static git-diff
    scan — an agent invocation costs ~100s + 37K preamble tokens; this
    Python scan is ~10ms and catches the same structural patterns. The
    verifier can still catch semantic surface changes (renames, type
    shifts) via probes #5 and #6, so missing those patterns here is fine.

    Flags:
    - Removed `def`/`class`/`function`/`export` signatures (regardless of
      whether the name is re-added with a different signature — that's
      still a break for callers).
    - Removed `add_argument("--flag-name"...)` — CLI contract change.
    - Removed `@app.get("/path"...)` or `@router.post(...)` — HTTP route change.

    Does NOT flag:
    - Additions (new signatures, new routes, new flags) — those are
      non-breaking.
    - Body changes within an existing signature — semantic, not surface.

    Returns an empty list on clean diff.
    """
    try:
        diff = subprocess.check_output(
            ["git", "diff", f"{base_sha}..{head_sha}", "--unified=0", "--no-color"],
            cwd=wt_path, text=True, stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return []
    violations: list[str] = []
    current_file = ""
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:]
            continue
        if line.startswith("---"):
            continue
        sig = _SIGNATURE_REMOVAL.match(line)
        if sig:
            violations.append(f"{current_file}: removed {line[1:].strip()[:120]}")
            continue
        flag = _CLI_FLAG_REMOVAL.search(line)
        if flag:
            violations.append(f"{current_file}: CLI flag removed: {flag.group(1)}")
            continue
        route = _ROUTE_REMOVAL.search(line)
        if route:
            violations.append(f"{current_file}: HTTP route removed: {route.group(1)}")
            continue
    return violations


def working_tree_changes(wt: Path) -> list[str]:
    """Bound to harness's artifacts regex; see src.shared.safety.tier_c.working_tree_changes."""
    return _tier_c.working_tree_changes(wt, artifacts=HARNESS_ARTIFACTS)


def check_no_leak(
    pre_dirty_set: set[str], main_repo: Path | None = None
) -> tuple[list[str], list[str]]:
    """Main-repo leak detection — (actionable, advisory) tuple.

    Actionable: new-dirty paths matching `_FIXER_REACHABLE` (codebase
    roots a fixer could have written to via absolute paths). Triggers
    rollback + cleanup.

    Advisory: new-dirty paths outside `_FIXER_REACHABLE` and outside
    `HARNESS_ARTIFACTS` — almost always operator dev activity
    (docs/plans, .github/, memory/). Logged but never rollback.
    """
    return _tier_c.check_no_leak(
        pre_dirty_set,
        artifacts=HARNESS_ARTIFACTS,
        reachable=_FIXER_REACHABLE,
        main_repo=main_repo,
    )


def snapshot_dirty(main_repo: Path | None = None) -> set[str]:
    """Pass-through to src.shared.safety.tier_c.snapshot_dirty."""
    return _tier_c.snapshot_dirty(main_repo)
