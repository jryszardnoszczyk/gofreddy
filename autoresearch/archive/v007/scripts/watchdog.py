#!/usr/bin/env python3
"""Helpers for multi-turn autoresearch watchdog logic."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

POLL_INTERVAL_SECONDS = 5.0
SNAPSHOT_INTERVAL_SECONDS = 120.0
TERMINATION_GRACE_SECONDS = 10.0

TRACKED_PHASE_TYPES: dict[str, set[str]] = {
    "geo": {"discover", "competitive", "seo_baseline", "optimize", "report"},
    "competitive": {"gather", "analyze", "synthesize", "verify"},
    "monitoring": {
        "select_mentions",
        "cluster_stories",
        "detect_anomalies",
        "synthesize",
        "recommend",
        "deliver",
    },
    "storyboard": {
        "select_videos",
        "analyze_patterns",
        "plan_story",
        "ideate",
        "generate_frames",
        "report",
    },
}

# P1 audit: split into a STRICT set for completion-ledger validation and a
# PERMISSIVE set for stall-counter / progress logging. discarded/reworked
# legitimately mean "phase ran, output rejected" — they should count as
# *progress* (work was done), but NOT as *completion* (the phase still hasn't
# produced an accepted deliverable). The legacy combined set let agents
# self-declare COMPLETE with reworked phases.
COMPLETION_STATUSES = {
    "done",
    "complete",
    "completed",
    "pass",
    "kept",
}
PROGRESS_STATUSES = COMPLETION_STATUSES | {
    "discarded",
    "reworked",
    "rework",
    "partial",
}
# Back-compat alias — legacy callers reference SUCCESS_STATUSES. New code
# should pick COMPLETION_STATUSES vs PROGRESS_STATUSES explicitly.
SUCCESS_STATUSES = PROGRESS_STATUSES
FAILED_STATUSES = {"error", "failed", "fail"}
BLOCKED_STATUSES = {"blocked"}
TIMEOUT_STATUSES = {"timeout"}


@dataclass(frozen=True)
class ProgressSnapshot:
    """Filesystem-level progress signal for stall detection."""

    results_lines: int
    subdir_counts: tuple[int, ...]

    def changed_from(self, other: "ProgressSnapshot | None") -> bool:
        return other is None or self != other


def count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        return sum(1 for _ in path.open())
    except OSError:
        return 0


def take_progress_snapshot(session_dir: Path, subdirs: list[str]) -> ProgressSnapshot:
    counts = []
    for subdir in subdirs:
        current = session_dir / subdir
        try:
            counts.append(len(list(current.iterdir())) if current.exists() else 0)
        except OSError:
            counts.append(0)
    return ProgressSnapshot(
        results_lines=count_lines(session_dir / "results.jsonl"),
        subdir_counts=tuple(counts),
    )


def iter_new_result_entries(results_file: Path, start_line: int) -> tuple[list[tuple[int, str, dict]], int]:
    """Return newly appended JSONL entries from ``start_line`` onward.

    P1 audit: when a SIGKILL truncates a JSONL line mid-flush, the partial
    line fails json.loads. Pre-fix, we silently skipped it AND advanced
    processed_lines past it — so on the next poll, the truncated line is
    forgotten and any phase event it contained is invisible to phase
    counting + telemetry.

    Now: if the LAST non-empty line fails to parse (most likely a partial
    write), do NOT advance past it — return start_line so the next poll
    re-reads. This lets the writer finish flushing. Defensive cap: after
    5 consecutive polls of the same stuck line, give up to avoid blocking
    on a permanently-broken file.
    """
    if not results_file.exists():
        return [], start_line

    try:
        lines = results_file.read_text().splitlines()
    except OSError:
        return [], start_line

    entries: list[tuple[int, str, dict]] = []
    last_good_idx = start_line  # advance pointer only past parseable lines
    for idx, raw_line in enumerate(lines[start_line:], start=start_line + 1):
        line = raw_line.strip()
        if not line:
            last_good_idx = idx  # blank lines are safe to advance past
            continue
        try:
            entries.append((idx, line, json.loads(line)))
            last_good_idx = idx
        except json.JSONDecodeError:
            # If this is the LAST line in the file, it's most likely a
            # partial write — wait for the writer to finish. Otherwise
            # (mid-file malformed line, less likely), skip and continue
            # so we don't block forever.
            is_last_line = (idx == len(lines))
            if is_last_line:
                return entries, last_good_idx
            # Mid-file malformed line — skip and continue.
            last_good_idx = idx
            continue
    return entries, len(lines)


def is_phase_event(domain: str, entry: dict) -> bool:
    raw_type = entry.get("type")
    if not isinstance(raw_type, str):
        return False
    return raw_type in TRACKED_PHASE_TYPES.get(domain, set())


def phase_type(entry: dict) -> str:
    raw_type = entry.get("type")
    return raw_type if isinstance(raw_type, str) else "unknown"


def tracking_status_from_entry(entry: dict) -> str:
    raw_status = str(entry.get("status", "")).lower()
    if raw_status in BLOCKED_STATUSES:
        return "blocked"
    if raw_status in TIMEOUT_STATUSES:
        return "timeout"
    if raw_status in FAILED_STATUSES:
        return "failed"
    if raw_status in SUCCESS_STATUSES:
        return "success"
    return "success"
