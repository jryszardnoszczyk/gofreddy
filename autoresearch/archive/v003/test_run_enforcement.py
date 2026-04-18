"""Runner enforcement tests for Units 10 and 11.

Covers `enforce_iteration_contract`, the harness self-diagnostics helper
that warns on two known agent-compliance drift patterns:
  - results.jsonl did not grow during an iteration (geo LOG skip, run #5)
  - `freddy digest persist` only invoked with --help (monitoring, run #6)
"""

from __future__ import annotations

import sys
from pathlib import Path

# The run.py module lives alongside this test file under archive/v001/.
MODULE_DIR = Path(__file__).resolve().parent
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

import run  # noqa: E402


def test_results_jsonl_no_growth_warning(tmp_path: Path, capsys) -> None:
    """Iteration that completes without extending results.jsonl triggers a
    warning naming the iteration number, schema, and file path. This is
    the exact pattern the geo agent exhibited in run #5 when it skipped
    the OPTIMIZE LOG step."""
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    (session_dir / "results.jsonl").write_text('{"iteration": 1, "type": "discover", "status": "done"}\n')
    log_dir = session_dir / "logs"
    log_dir.mkdir()
    log_path = log_dir / "iteration_002.log"
    log_path.write_text("agent log contents\n")

    # Simulate: before the iteration started, file had 1 line. After the
    # iteration, the file still has 1 line — agent skipped LOG.
    lines_before = 1
    run.enforce_iteration_contract(
        "geo", iteration=2, session_dir=session_dir,
        log_path=log_path, results_lines_before=lines_before,
    )

    captured = capsys.readouterr()
    assert "WARNING" in captured.err
    assert "iteration 2" in captured.err
    assert "results.jsonl" in captured.err
    assert "'iteration': 2" in captured.err  # schema hint


def test_results_jsonl_growth_is_silent(tmp_path: Path, capsys) -> None:
    """No warning when results.jsonl grew — the happy path."""
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    results_file = session_dir / "results.jsonl"
    results_file.write_text(
        '{"iteration": 1, "type": "discover", "status": "done"}\n'
        '{"iteration": 2, "type": "optimize", "status": "done"}\n'
    )
    log_path = tmp_path / "iteration_002.log"
    log_path.write_text("ok\n")

    run.enforce_iteration_contract(
        "geo", iteration=2, session_dir=session_dir,
        log_path=log_path, results_lines_before=1,
    )

    captured = capsys.readouterr()
    assert "WARNING" not in captured.err


def test_monitoring_help_only_digest_persist_warning(tmp_path: Path, capsys) -> None:
    """Monitoring iteration that only invoked `freddy digest persist --help`
    (never the real command) triggers a precise warning. This is the exact
    run #6 iter 2 drift — agent read help output instead of persisting."""
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    (session_dir / "results.jsonl").write_text(
        '{"iteration": 1, "type": "select_mentions", "status": "done"}\n'
        '{"iteration": 2, "type": "deliver", "status": "done"}\n'
    )
    log_path = tmp_path / "iteration_002.log"
    log_path.write_text(
        "Agent ran: freddy digest persist --help\n"
        "Got help output, moved on.\n"
    )

    run.enforce_iteration_contract(
        "monitoring", iteration=2, session_dir=session_dir,
        log_path=log_path, results_lines_before=1,
    )

    captured = capsys.readouterr()
    assert "WARNING" in captured.err
    assert "freddy digest persist --help" in captured.err
    assert "never the actual persist command" in captured.err


def test_monitoring_real_digest_persist_is_silent(tmp_path: Path, capsys) -> None:
    """Monitoring iteration that invoked the real persist command does NOT
    warn — even if it also ran --help at some point."""
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    (session_dir / "results.jsonl").write_text(
        '{"iteration": 1, "type": "select_mentions", "status": "done"}\n'
        '{"iteration": 2, "type": "deliver", "status": "done"}\n'
    )
    log_path = tmp_path / "iteration_002.log"
    log_path.write_text(
        "Agent ran: freddy digest persist --help\n"
        "Then: freddy digest persist shopify --file synthesized/digest-meta.json\n"
        "Persisted successfully.\n"
    )

    run.enforce_iteration_contract(
        "monitoring", iteration=2, session_dir=session_dir,
        log_path=log_path, results_lines_before=1,
    )

    captured = capsys.readouterr()
    assert "persist --help" not in captured.err  # no --help-only warning
