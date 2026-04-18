"""Regression tests for summarize_session.py.

Two tests guard the subtle writer bug that propagated corrupted metadata
into 6 downstream consumers: (1) BLOCKED status recognition, and
(2) iteration arithmetic + categorization that handles all agent status
values in use across the 4 lanes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Make the sibling summarize_session importable when pytest runs from repo root.
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# Patch sys.path for the workflows import inside summarize_session.
ARCHIVE_ROOT = SCRIPTS_DIR.parent
if str(ARCHIVE_ROOT) not in sys.path:
    sys.path.insert(0, str(ARCHIVE_ROOT))

from summarize_session import summarize  # noqa: E402  (path shenanigans above)


def _write_session(
    tmp_path: Path,
    *,
    status_marker: str,
    results: list[dict],
) -> Path:
    """Create a minimal session directory the summarizer can parse."""
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    (session_dir / "session.md").write_text(
        f"# Session\n\n## Status: {status_marker}\n\nNotes here.\n"
    )
    results_path = session_dir / "results.jsonl"
    results_path.write_text("\n".join(json.dumps(r) for r in results) + "\n")
    return session_dir


def test_blocked_status_is_recognized(tmp_path: Path) -> None:
    """A session.md marked BLOCKED must surface as status='BLOCKED',
    not silently fall through to 'UNKNOWN'.

    Prior to the run #6 triage, the parser only recognized COMPLETE /
    IN_PROGRESS / RUNNING. Storyboard's real BLOCKED state propagated as
    UNKNOWN into 6 downstream report generators.
    """
    session_dir = _write_session(
        tmp_path,
        status_marker="BLOCKED",
        results=[{"iteration": 1, "type": "plan_story", "status": "blocked"}],
    )

    summary = summarize(str(session_dir), "storyboard", "test_client")

    assert summary["status"] == "BLOCKED"
    assert summary["exit_reason"] == "BLOCKED"


def test_iteration_arithmetic_handles_all_status_values(tmp_path: Path) -> None:
    """Iteration categorization must reconcile across `done`, `error`,
    `complete`, `kept`, `blocked`, `failed`, `skipped`, and unknown statuses.

    The test fabricates 4 distinct iterations that collectively emit 7
    result rows (multi-entry iterations are legitimate — storyboard iter 4
    in run #6 emitted 3 rows for one blocked iteration). `total` must
    count distinct iterations (4), not rows (7), and the category counts
    must reconcile with the total when uncategorized is included.
    """
    results = [
        {"iteration": 1, "type": "discover", "status": "done"},       # productive
        {"iteration": 2, "type": "optimize", "status": "complete"},   # productive
        {"iteration": 2, "type": "optimize", "status": "kept"},       # productive (same iter)
        {"iteration": 3, "type": "plan_story", "status": "error"},    # failed
        {"iteration": 3, "type": "plan_story", "status": "blocked"},  # blocked (same iter)
        {"iteration": 4, "type": "report", "status": "skipped"},      # skipped
        {"iteration": 4, "type": "report", "status": "weird_value"},  # uncategorized
    ]

    session_dir = _write_session(
        tmp_path,
        status_marker="COMPLETE",
        results=results,
    )

    summary = summarize(str(session_dir), "geo", "test_client")
    iterations = summary["iterations"]

    # total = distinct iteration numbers, not len(results)
    assert iterations["total"] == 4

    # Category counts match row-level categorization (not iteration-level)
    assert iterations["productive"] == 3  # done + complete + kept
    assert iterations["failed"] == 1      # error
    assert iterations["blocked"] == 1     # blocked
    assert iterations["skipped"] == 1     # skipped
    assert iterations["uncategorized"] == 1  # weird_value

    # Internal consistency: category sum equals row count (7).
    category_sum = (
        iterations["productive"]
        + iterations["failed"]
        + iterations["blocked"]
        + iterations["skipped"]
        + iterations["uncategorized"]
    )
    assert category_sum == len(results)
