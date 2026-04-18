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

SUCCESS_STATUSES = {
    "done",
    "complete",
    "pass",
    "kept",
    "discarded",
    "reworked",
    "rework",
    "partial",
}
FAILED_STATUSES = {"error", "failed"}
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
    """Return newly appended JSONL entries from ``start_line`` onward."""
    if not results_file.exists():
        return [], start_line

    try:
        lines = results_file.read_text().splitlines()
    except OSError:
        return [], start_line

    entries: list[tuple[int, str, dict]] = []
    for idx, raw_line in enumerate(lines[start_line:], start=start_line + 1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            entries.append((idx, line, json.loads(line)))
        except json.JSONDecodeError:
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
