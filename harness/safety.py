"""Harness-bound Tier C leak detection.

Per-track SCOPE_ALLOWLIST + check_scope have been REMOVED. The fixer prompt
describes each track's surface; we trust the agent to stay in its lane.
Under the per-worker isolation model, peer fixers cannot interfere with
each other anyway (each worker owns its own worktree), so the regex-based
containment was belt-and-suspenders that caused more false rollbacks than
it prevented real damage.

What remains here: main-repo leak detection (catches fixers writing absolute
paths outside their worktree into the parent repo) + working-tree-changes
for commit staging.
"""
from __future__ import annotations

from pathlib import Path

from harness.config import HARNESS_ARTIFACTS, _FIXER_REACHABLE
from src.shared.safety import tier_c as _tier_c

__all__ = [
    "HARNESS_ARTIFACTS",
    "check_no_leak",
    "snapshot_dirty",
    "working_tree_changes",
]


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
