"""Lane ownership boundaries for workflow-decoupled autoresearch evolution."""

from __future__ import annotations

from pathlib import Path

LANES = ("core", "geo", "competitive", "monitoring", "storyboard")
WORKFLOW_LANES = tuple(lane for lane in LANES if lane != "core")

# Paths owned by the harness infrastructure — excluded from ALL lanes
# (including core) so that the evolution proposer's workspace never contains
# harness code.  Added by Unit 10 (R12).
_HARNESS_PREFIXES = (
    "harness",
)

_WORKFLOW_PREFIXES = {
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
    normalized = (lane or "core").strip().lower()
    if normalized not in LANES:
        raise ValueError(f"Unknown lane: {lane}")
    return normalized


def lane_prefixes(lane: str) -> tuple[str, ...]:
    lane = normalize_lane(lane)
    if lane == "core":
        return ()
    return _WORKFLOW_PREFIXES[lane]


def _matches_prefix(rel_path: str, prefix: str) -> bool:
    normalized = prefix.strip("/")
    if not normalized:
        return False
    return rel_path == normalized or rel_path.startswith(f"{normalized}/")


def path_owned_by_lane(rel_path: str | Path, lane: str) -> bool:
    lane = normalize_lane(lane)
    rel_value = Path(rel_path).as_posix().lstrip("./")
    # Harness infrastructure is excluded from every lane, including core.
    if any(_matches_prefix(rel_value, prefix) for prefix in _HARNESS_PREFIXES):
        return False
    if lane == "core":
        return not any(
            _matches_prefix(rel_value, prefix)
            for workflow_lane in WORKFLOW_LANES
            for prefix in _WORKFLOW_PREFIXES[workflow_lane]
        )
    return any(_matches_prefix(rel_value, prefix) for prefix in _WORKFLOW_PREFIXES[lane])
