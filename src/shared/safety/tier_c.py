"""Tier C safety primitives — repo-write + post-hoc scope/leak verification.

Pipelines using Tier C let an agent mutate code in a worktree, then gate the
commit on (a) every dirty path matching the agent's track allowlist (scope
check) and (b) no path outside the worktree becoming dirty since startup
(leak check). The fixer pipeline (harness) is the canonical Tier C consumer;
audit-pipeline auto-fix would be a second consumer if it ever lands.

All four primitives accept the per-pipeline scope allowlist + artifacts-ignore
regex as parameters; the harness's ``SCOPE_ALLOWLIST`` and ``HARNESS_ARTIFACTS``
live in :mod:`harness.config` and are bound by the :mod:`harness.safety` shim.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path


def working_tree_changes(
    wt: Path, *, artifacts: re.Pattern[str]
) -> list[str]:
    """Return every path the agent changed in the worktree (modified + untracked).

    Filters out ``artifacts`` — paths the harness/pipeline itself generates
    inside the worktree (e.g. ``backend.log``, ``sessions/``, blocked-marker
    files). Uses ``git status --porcelain -z -uall`` so paths with spaces don't
    break parsing and untracked files are listed individually instead of
    collapsed to their parent directory.
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
        if not path or artifacts.match(path):
            continue
        paths.append(path)
    return paths


def check_scope(
    wt: Path,
    pre_sha: str,
    track: str,
    *,
    scope: dict[str, re.Pattern[str]],
    artifacts: re.Pattern[str],
) -> list[str] | None:
    """Return paths the agent touched that fall outside ``track``'s allowlist, or None.

    Uses working-tree changes (not commit diff) because the agent leaves its
    edits uncommitted — the orchestrator commits them only after scope + leak
    checks pass.

    Under parallel execution, files matching any OTHER track's allowlist are
    filtered out of this track's violation set — they're assumed to be peer
    agents' in-flight edits, which will be validated by their own track's
    ``check_scope``.

    **The peer-filter is load-bearing, not defensive.** All tracks share one
    worktree, and fixer/verifier agents run concurrently. When track A's
    ``check_scope`` runs, the working tree almost always contains peer B + C
    edits alongside A's. Without the peer-filter, A's ``check_scope`` would
    attribute B's ``src/`` edit and C's ``frontend/`` edit to A and flag them
    as scope violations — causing A's legitimate fix to roll back because
    another track happened to be mid-flight. This is also why finding IDs
    collide harmlessly across tracks (``F-a-1-1`` vs ``F-b-1-1`` with the
    same summary): the peer-filter makes per-track attribution work on a
    shared tree. Removing it would re-introduce the scope-violation-loop
    class of bug seen in smoke run 20260422-174701 and similar runs.
    """
    pattern = scope[track]
    other_patterns = [p for t, p in scope.items() if t != track]
    paths = working_tree_changes(wt, artifacts=artifacts)
    candidates = [p for p in paths if not any(op.match(p) for op in other_patterns)]
    violations = [p for p in candidates if not pattern.match(p)]
    return violations or None


def check_no_leak(
    pre_dirty_set: set[str],
    *,
    artifacts: re.Pattern[str],
    reachable: re.Pattern[str],
    main_repo: Path | None = None,
) -> tuple[list[str], list[str]]:
    """Return (actionable, advisory) leak paths in the main repo since ``pre_dirty_set``.

    ``pre_dirty_set`` is a snapshot of ``git status --porcelain`` lines (stripped
    path tokens), captured once at orchestrator startup. Anything new =
    something changed in the main repo during the run.

    Two output lists so the caller can distinguish plausible-harness-caused leaks
    from concurrent dev activity:

    - **actionable**: new-dirty paths matching ``reachable`` (the union of track
      scope allowlists). Plausibly fixer-caused — rollback-eligible if non-empty.
    - **advisory**: new-dirty paths outside every track's scope AND not in
      ``artifacts``. Typically concurrent dev activity in ``docs/``, ``tests/``,
      etc. — visible but does NOT trigger rollback. Smoke 20260422-224908
      rolled back 5 findings because the user was editing ``docs/plans/*`` in
      a parallel Claude session; that's the scenario advisory preserves against.
    - ``artifacts`` paths are filtered out entirely (e.g. ``backend.log``).
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
    new_dirty = sorted(current - pre_dirty_set)
    actionable = [p for p in new_dirty if reachable.match(p)]
    advisory = [
        p for p in new_dirty
        if not reachable.match(p) and not artifacts.match(p)
    ]
    return actionable, advisory


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
