"""Pure forwarding shim — autoresearch lane ownership now lives in src/shared/safety/tier_b.

This module emits a ``DeprecationWarning`` on import. Autoresearch-specific lane
configuration (the ``LANES`` tuple, the per-lane prefix dict, the harness-prefix
exclusion list) lives here as data; the actual ownership check lives in
:mod:`src.shared.safety.tier_b`. New callers should import from tier_b directly
and pass ``lanes=LANES`` / ``workflow_prefixes=WORKFLOW_PREFIXES`` /
``excluded_prefixes=HARNESS_PREFIXES`` explicitly. Removal target: 4 weeks
after Phase 3 of refactor 007 lands.
"""
from __future__ import annotations

import warnings
from pathlib import Path

# Import via filesystem path so this shim works whether autoresearch is
# imported as a package (`from autoresearch.lane_paths import ...`) or as a
# top-level module (`import lane_paths`, used inside autoresearch/ where
# sys.path is set to the package dir). Compute the repo root from this file's
# location to find src.shared.safety.tier_b without forcing a sys.path edit.
import sys as _sys

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_REPO_ROOT))

from src.shared.safety import tier_b as _tier_b  # noqa: E402

warnings.warn(
    "autoresearch.lane_paths is a deprecated shim — import from "
    "src.shared.safety.tier_b (pass lanes=, workflow_prefixes=, excluded_prefixes=).",
    DeprecationWarning,
    stacklevel=2,
)

LANES: tuple[str, ...] = ("core", "geo", "competitive", "monitoring", "storyboard")
WORKFLOW_LANES: tuple[str, ...] = tuple(lane for lane in LANES if lane != "core")

# Paths owned by the harness infrastructure — excluded from ALL lanes
# (including core) so that the evolution proposer's workspace never contains
# harness code. Added by Unit 10 (R12).
HARNESS_PREFIXES: tuple[str, ...] = ("harness",)

WORKFLOW_PREFIXES: dict[str, tuple[str, ...]] = {
    "geo": (
        "geo-findings.md",
        "programs/geo-session.md",
        "templates/geo",
        "scripts/allocate_gaps.py",
        "scripts/build_geo_report.py",
        "workflows/geo.py",
        "workflows/session_eval_geo.py",
    ),
    "competitive": (
        "competitive-findings.md",
        "programs/competitive-session.md",
        "templates/competitive",
        "scripts/extract_prior_summary.py",
        "scripts/format_report.py",
        "workflows/competitive.py",
        "workflows/session_eval_competitive.py",
    ),
    "monitoring": (
        "monitoring-findings.md",
        "programs/monitoring-session.md",
        "templates/monitoring",
        "workflows/monitoring.py",
        "workflows/session_eval_monitoring.py",
    ),
    "storyboard": (
        "storyboard-findings.md",
        "programs/storyboard-session.md",
        "templates/storyboard",
        "workflows/storyboard.py",
        "workflows/session_eval_storyboard.py",
    ),
}


def normalize_lane(lane: str | None) -> str:
    """Forward to tier_b.normalize_lane with autoresearch's LANES bound."""
    return _tier_b.normalize_lane(lane, lanes=LANES, default="core")


def lane_prefixes(lane: str) -> tuple[str, ...]:
    """Return the prefix tuple owned by ``lane``; empty for the core (default) lane."""
    lane = normalize_lane(lane)
    if lane == "core":
        return ()
    return WORKFLOW_PREFIXES[lane]


def path_owned_by_lane(rel_path: str | Path, lane: str) -> bool:
    """Forward to tier_b.path_owned_by_lane with autoresearch's prefix scheme bound."""
    return _tier_b.path_owned_by_lane(
        rel_path,
        lane,
        lanes=LANES,
        workflow_prefixes=WORKFLOW_PREFIXES,
        excluded_prefixes=HARNESS_PREFIXES,
        default_lane="core",
    )


__all__ = [
    "LANES",
    "WORKFLOW_LANES",
    "WORKFLOW_PREFIXES",
    "HARNESS_PREFIXES",
    "normalize_lane",
    "lane_prefixes",
    "path_owned_by_lane",
]
