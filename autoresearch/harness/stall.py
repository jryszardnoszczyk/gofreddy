"""Stall detection -- progress snapshots and phase event counting.

Progress is measured by diminishing returns (Meta-Harness §7): a new phase
type in results.jsonl or a net increase in a subdir's file count. Any other
activity — rewriting the same file, logging the same phase type again,
deleting files — is not progress.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parent
AUTORESEARCH_DIR = HARNESS_DIR.parent
if str(AUTORESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(AUTORESEARCH_DIR))

import harness  # noqa: F401,E402  # ensure package-level path setup runs

from watchdog import is_phase_event  # type: ignore  # noqa: E402


def _read_phase_types(session_dir: Path, domain: str | None) -> set[str]:
    """Return the set of phase types recorded in results.jsonl."""
    if not domain:
        return set()
    results = session_dir / "results.jsonl"
    if not results.exists():
        return set()
    types: set[str] = set()
    try:
        lines = results.read_text().splitlines()
    except OSError:
        return types
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if is_phase_event(domain, entry):
            type_val = entry.get("type")
            if isinstance(type_val, str):
                types.add(type_val)
    return types


def _subdir_counts(session_dir: Path, subdirs: list[str]) -> list[int]:
    """Count files inside each subdir, walking one level of nesting.

    Defensive: if a workflow shifts to a nested layout (e.g.
    ``pages/competitor1/snapshot.json``), the top-level iterdir() would
    keep returning 1 forever. Use rglob to count actual file leaves so
    progress signal works regardless of layout.
    """
    counts: list[int] = []
    for subdir in subdirs:
        d = session_dir / subdir
        if not d.exists():
            counts.append(0)
            continue
        try:
            counts.append(sum(1 for p in d.rglob("*") if p.is_file()))
        except OSError:
            counts.append(0)
    return counts


def snapshot_state(
    session_dir: Path, subdirs: list[str], domain: str | None = None
) -> None:
    """Save progress snapshot for stall detection."""
    snapshot = session_dir / ".progress_snapshot"
    payload = {
        "types": sorted(_read_phase_types(session_dir, domain)),
        "counts": _subdir_counts(session_dir, subdirs),
        # Phase-event counter — distinguishes real phase emission from
        # file-only growth (cyber-flag stubs, retry artifacts).
        "phase_count": count_phase_events(domain, session_dir) if domain else 0,
    }
    snapshot.write_text(json.dumps(payload))


def state_changed(
    session_dir: Path, subdirs: list[str], domain: str | None = None
) -> bool:
    """True when the session made forward progress since the last snapshot.

    Forward progress means EITHER a new phase type appeared in results.jsonl,
    OR an existing phase type emitted another event AND a subdir grew. The
    second condition tightens the legacy "any subdir growth = progress" rule
    so cyber-flag stub files dumped under pages/ don't read as progress when
    no actual phase event was logged. Pi v007 rakuten holdout audit finding.
    """
    snapshot = session_dir / ".progress_snapshot"
    if not snapshot.exists():
        return True
    try:
        prev = json.loads(snapshot.read_text())
    except (OSError, json.JSONDecodeError):
        return True

    prev_types = set(prev.get("types", []) or [])
    prev_counts = list(prev.get("counts", []) or [])
    prev_phase_count = int(prev.get("phase_count", 0) or 0)
    curr_types = _read_phase_types(session_dir, domain)

    # New phase type discovered → strong progress signal, no further check.
    if curr_types - prev_types:
        return True

    # Same phase types: require phase-event counter to have grown. Pure
    # file-only growth (write same stub under pages/) is no longer enough.
    if domain:
        curr_phase_count = count_phase_events(domain, session_dir)
        if curr_phase_count <= prev_phase_count:
            return False
    elif not curr_types:
        # No domain, no phase types at all — fall back to subdir-only check
        # (legacy behavior for unstructured sessions, e.g. domain=None).
        curr_counts = _subdir_counts(session_dir, subdirs)
        for idx, curr in enumerate(curr_counts):
            prev_c = prev_counts[idx] if idx < len(prev_counts) else 0
            if curr > prev_c:
                return True
        return False

    # Phase counter grew — require subdir growth too, so a "log-only"
    # iteration (event recorded but no artifacts produced) doesn't read as
    # productive. Both signals = real progress.
    curr_counts = _subdir_counts(session_dir, subdirs)
    for idx, curr in enumerate(curr_counts):
        prev_c = prev_counts[idx] if idx < len(prev_counts) else 0
        if curr > prev_c:
            return True
    return False


def count_phase_events(domain: str, session_dir: Path) -> int:
    results = session_dir / "results.jsonl"
    if not results.exists():
        return 0
    total = 0
    for line in results.read_text().splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if is_phase_event(domain, entry):
            total += 1
    return total


def count_kept_entries(session_dir: Path) -> int:
    results_file = session_dir / "results.jsonl"
    if not results_file.exists():
        return 0
    return sum(1 for line in results_file.read_text().splitlines()
               if '"kept"' in line and '"status"' in line)
