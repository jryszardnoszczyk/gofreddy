"""Pure re-export shim — harness's Tier C safety primitives now live in src/shared/safety/tier_c.

This module emits a ``DeprecationWarning`` on import and re-exports the four
primitives with the harness-specific allowlist + artifacts regex bound. New
callers should import from :mod:`src.shared.safety.tier_c` directly and pass
``scope=harness.config.SCOPE_ALLOWLIST`` / ``artifacts=harness.config.HARNESS_ARTIFACTS``
explicitly. Removal target: 4 weeks after Phase 3 of refactor 007 lands.
"""
from __future__ import annotations

import warnings
from pathlib import Path

from harness.config import HARNESS_ARTIFACTS, SCOPE_ALLOWLIST
from src.shared.safety import tier_c as _tier_c

warnings.warn(
    "harness.safety is a deprecated shim — import from src.shared.safety.tier_c "
    "(pass scope=harness.config.SCOPE_ALLOWLIST, artifacts=harness.config.HARNESS_ARTIFACTS).",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "SCOPE_ALLOWLIST",
    "HARNESS_ARTIFACTS",
    "check_no_leak",
    "check_scope",
    "snapshot_dirty",
    "working_tree_changes",
]


def working_tree_changes(wt: Path) -> list[str]:
    """Bound to harness's artifacts regex; see src.shared.safety.tier_c.working_tree_changes."""
    return _tier_c.working_tree_changes(wt, artifacts=HARNESS_ARTIFACTS)


def check_scope(wt: Path, pre_sha: str, track: str) -> list[str] | None:
    """Bound to harness's allowlist + artifacts; see src.shared.safety.tier_c.check_scope."""
    return _tier_c.check_scope(
        wt, pre_sha, track, scope=SCOPE_ALLOWLIST, artifacts=HARNESS_ARTIFACTS,
    )


def check_no_leak(
    pre_dirty_set: set[str], main_repo: Path | None = None
) -> list[str] | None:
    """Bound to harness's artifacts regex; see src.shared.safety.tier_c.check_no_leak.

    Any main-repo path that became dirty during the run and doesn't match
    ``HARNESS_ARTIFACTS`` is reported as a leak — including paths outside
    every track's allowlist (``tests/``, ``docs/``, ``.github/`` etc.).
    """
    return _tier_c.check_no_leak(
        pre_dirty_set, artifacts=HARNESS_ARTIFACTS, main_repo=main_repo,
    )


def snapshot_dirty(main_repo: Path | None = None) -> set[str]:
    """Pass-through to src.shared.safety.tier_c.snapshot_dirty."""
    return _tier_c.snapshot_dirty(main_repo)
