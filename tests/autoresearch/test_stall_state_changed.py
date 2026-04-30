"""Stall detection — state_changed must require BOTH a phase event delta AND
subdir growth to call something progress. Pi v007 rakuten audit surfaced the
loophole: cyber-flag stub files dumped under pages/ on iter 2/3/4 bumped
subdir counts without producing any new phase events, but old logic counted
them as progress."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Path bootstrap matches sibling autoresearch tests
_repo_root = Path(__file__).resolve().parents[2]
_autoresearch_dir = _repo_root / "autoresearch"
if str(_autoresearch_dir) in sys.path:
    sys.path.remove(str(_autoresearch_dir))
sys.path.insert(0, str(_autoresearch_dir))
for _mod in [m for m in list(sys.modules) if m == "harness" or m.startswith("harness.")]:
    file_attr = getattr(sys.modules[_mod], "__file__", None) or ""
    if not file_attr.startswith(str(_autoresearch_dir)):
        del sys.modules[_mod]

from harness.stall import snapshot_state, state_changed  # noqa: E402


def _write_results(session_dir: Path, entries: list[dict]) -> None:
    p = session_dir / "results.jsonl"
    p.write_text("\n".join(json.dumps(e) for e in entries) + "\n")


def _make_subdir(session_dir: Path, name: str, file_count: int) -> None:
    d = session_dir / name
    d.mkdir(exist_ok=True)
    for i in range(file_count):
        (d / f"f{i}").write_text("x")


def test_state_changed_returns_true_on_first_call(tmp_path):
    """No snapshot yet → progress is presumed (start of session)."""
    assert state_changed(tmp_path, ["pages"], "geo") is True


def test_state_changed_true_when_new_phase_type(tmp_path):
    _write_results(tmp_path, [
        {"iteration": 1, "type": "discover", "status": "completed"},
    ])
    snapshot_state(tmp_path, ["pages"], "geo")
    _write_results(tmp_path, [
        {"iteration": 1, "type": "discover", "status": "completed"},
        {"iteration": 2, "type": "competitive", "status": "completed"},
    ])
    assert state_changed(tmp_path, ["pages"], "geo") is True


def test_state_changed_FALSE_when_only_subdir_grew_no_phase_event(tmp_path):
    """The rakuten cyber-flag fingerprint: stub file dumped under pages/ but
    no new phase event in results.jsonl. Legacy returned True; we now
    return False so the stall counter advances."""
    _write_results(tmp_path, [
        {"iteration": 1, "type": "discover", "status": "completed"},
    ])
    _make_subdir(tmp_path, "pages", 1)
    snapshot_state(tmp_path, ["pages"], "geo")

    # Iter 2 dumped a stub file but NO new phase event was logged.
    _make_subdir(tmp_path, "pages", 2)
    # results.jsonl unchanged (still 1 phase event)

    assert state_changed(tmp_path, ["pages"], "geo") is False


def test_state_changed_true_when_phase_event_grew_AND_subdir_grew(tmp_path):
    """Real progress: same phase type but a new event landed AND artifacts
    were produced. Both signals = progress."""
    _write_results(tmp_path, [
        {"iteration": 1, "type": "optimize", "status": "kept"},
    ])
    _make_subdir(tmp_path, "pages", 1)
    snapshot_state(tmp_path, ["pages"], "geo")

    _write_results(tmp_path, [
        {"iteration": 1, "type": "optimize", "status": "kept"},
        {"iteration": 2, "type": "optimize", "status": "kept"},
    ])
    _make_subdir(tmp_path, "pages", 2)

    assert state_changed(tmp_path, ["pages"], "geo") is True


def test_state_changed_false_when_phase_event_grew_but_no_subdir_growth(tmp_path):
    """Log-only iteration: phase event recorded but no artifacts produced.
    That's introspection without output — not real progress."""
    _write_results(tmp_path, [
        {"iteration": 1, "type": "optimize", "status": "kept"},
    ])
    _make_subdir(tmp_path, "pages", 1)
    snapshot_state(tmp_path, ["pages"], "geo")

    _write_results(tmp_path, [
        {"iteration": 1, "type": "optimize", "status": "kept"},
        {"iteration": 2, "type": "optimize", "status": "kept"},
    ])
    # No subdir change

    assert state_changed(tmp_path, ["pages"], "geo") is False


def test_state_changed_false_when_only_existing_phase_replayed(tmp_path):
    """Same phase event written again with no new event → not progress."""
    _write_results(tmp_path, [
        {"iteration": 1, "type": "discover", "status": "completed"},
    ])
    _make_subdir(tmp_path, "pages", 1)
    snapshot_state(tmp_path, ["pages"], "geo")

    # Same exact results.jsonl, same subdir count
    assert state_changed(tmp_path, ["pages"], "geo") is False


def test_state_changed_handles_missing_domain(tmp_path):
    """Legacy domain=None path: subdir-only growth is enough (no phase event
    counter applies). Used by unstructured sessions."""
    _make_subdir(tmp_path, "pages", 1)
    snapshot_state(tmp_path, ["pages"], None)
    _make_subdir(tmp_path, "pages", 2)
    assert state_changed(tmp_path, ["pages"], None) is True
