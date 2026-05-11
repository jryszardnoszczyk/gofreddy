"""Tests for autoresearch_v2/tools/run_experiment.py.

The real `archive/v006/run.py` is heavy and slow; instead we drive U2 with
a tiny stub script that mimics the v006/run.py contract just enough to
exercise exit-code, timeout, deliverable, and stdout-tail paths.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

from autoresearch_v2.tools import run_experiment


# --- stub runner helpers -----------------------------------------------------


def _stub_runner(tmp_path: Path, script: str) -> list[str]:
    """Drop a Python stub into tmp_path and return the argv prefix that runs it."""
    stub = tmp_path / "stub_runpy.py"
    stub.write_text(script)
    return [sys.executable, str(stub)]


def _stub_session_root(tmp_path: Path) -> Path:
    root = tmp_path / "sessions"
    root.mkdir(parents=True, exist_ok=True)
    return root


# --- tests -------------------------------------------------------------------


def test_happy_path_exit_zero_with_session_md(tmp_path):
    session_root = _stub_session_root(tmp_path)
    session_dir = session_root / "geo" / "mayoclinic"
    session_dir.mkdir(parents=True)

    runner = _stub_runner(tmp_path, f"""
import sys
from pathlib import Path
print("ran ok")
Path({str(session_dir)!r}, "session.md").write_text("# session\\n## Status: COMPLETE\\n")
sys.exit(0)
""")

    result = run_experiment.run_experiment(
        domain="geo", client="mayoclinic", context="https://example.com",
        max_iter=1, timeout=10, session_root=session_root, runner=runner,
    )
    assert result["exit_code"] == 0
    assert result["deliverable_present"] is True
    assert result["timed_out"] is False
    assert "ran ok" in result["stdout_tail"]
    assert result["strategy"] == "multiturn"


def test_error_path_nonzero_exit_with_tail(tmp_path):
    session_root = _stub_session_root(tmp_path)

    runner = _stub_runner(tmp_path, """
import sys
sys.stderr.write("boom\\n" * 50)
sys.exit(2)
""")

    result = run_experiment.run_experiment(
        domain="geo", client="mayoclinic", context="x",
        max_iter=1, timeout=10, session_root=session_root, runner=runner,
    )
    assert result["exit_code"] == 2
    assert result["deliverable_present"] is False
    assert "boom" in result["stdout_tail"]


def test_variant_generation_failure_exit_zero_no_session_md(tmp_path):
    """Bug 3 class: subprocess exits 0 but produces no session.md."""
    session_root = _stub_session_root(tmp_path)

    runner = _stub_runner(tmp_path, """
import sys
print("(no deliverable)")
sys.exit(0)
""")

    result = run_experiment.run_experiment(
        domain="geo", client="mayoclinic", context="x",
        max_iter=1, timeout=10, session_root=session_root, runner=runner,
    )
    assert result["exit_code"] == 0
    assert result["deliverable_present"] is False, \
        "exit=0 with no session.md must surface as deliverable_present=False"


def test_timeout_returns_124_marker(tmp_path):
    session_root = _stub_session_root(tmp_path)

    runner = _stub_runner(tmp_path, """
import time
time.sleep(60)
""")

    result = run_experiment.run_experiment(
        domain="geo", client="mayoclinic", context="x",
        max_iter=1, timeout=1, session_root=session_root, runner=runner,
    )
    assert result["exit_code"] == 124
    assert result["timed_out"] is True
    assert result["deliverable_present"] is False


@pytest.mark.parametrize("bad_lane", ["", "GEO", "ge0", "marketing-audit", "../escape"])
def test_invalid_lane_raises(bad_lane: str):
    with pytest.raises(ValueError, match="lane"):
        run_experiment.run_experiment(
            domain=bad_lane, client="x", context="y",
            max_iter=1, timeout=1, runner=["/bin/true"],
        )


@pytest.mark.parametrize("bad_client", ["", "with/slash"])
def test_invalid_client_raises(bad_client: str):
    with pytest.raises(ValueError, match="client"):
        run_experiment.run_experiment(
            domain="geo", client=bad_client, context="y",
            max_iter=1, timeout=1, runner=["/bin/true"],
        )


def test_invalid_max_iter_or_timeout_raises():
    with pytest.raises(ValueError, match="max_iter"):
        run_experiment.run_experiment(
            domain="geo", client="x", context="y",
            max_iter=0, timeout=10, runner=["/bin/true"],
        )
    with pytest.raises(ValueError, match="timeout"):
        run_experiment.run_experiment(
            domain="geo", client="x", context="y",
            max_iter=1, timeout=0, runner=["/bin/true"],
        )


def test_marketing_audit_defaults_to_fresh_strategy(tmp_path):
    """Lane-specific strategy default — marketing_audit needs fresh-strategy
    single-phase-per-subprocess mode (the v006 driver convention)."""
    session_root = _stub_session_root(tmp_path)
    captured = tmp_path / "argv.json"

    runner = _stub_runner(tmp_path, f"""
import sys, json
from pathlib import Path
Path({str(captured)!r}).write_text(json.dumps(sys.argv))
sys.exit(0)
""")

    result = run_experiment.run_experiment(
        domain="marketing_audit", client="StripeCo", context="https://stripe.com",
        max_iter=1, timeout=10, session_root=session_root, runner=runner,
    )
    argv = json.loads(captured.read_text())
    assert "--strategy" in argv
    assert argv[argv.index("--strategy") + 1] == "fresh"
    assert result["strategy"] == "fresh"


def test_geo_defaults_to_multiturn(tmp_path):
    session_root = _stub_session_root(tmp_path)
    captured = tmp_path / "argv.json"

    runner = _stub_runner(tmp_path, f"""
import sys, json
from pathlib import Path
Path({str(captured)!r}).write_text(json.dumps(sys.argv))
sys.exit(0)
""")

    result = run_experiment.run_experiment(
        domain="geo", client="mayoclinic", context="x",
        max_iter=1, timeout=10, session_root=session_root, runner=runner,
    )
    argv = json.loads(captured.read_text())
    assert argv[argv.index("--strategy") + 1] == "multiturn"
    assert result["strategy"] == "multiturn"


def test_strategy_override_wins_over_default(tmp_path):
    session_root = _stub_session_root(tmp_path)
    captured = tmp_path / "argv.json"

    runner = _stub_runner(tmp_path, f"""
import sys, json
from pathlib import Path
Path({str(captured)!r}).write_text(json.dumps(sys.argv))
sys.exit(0)
""")

    run_experiment.run_experiment(
        domain="marketing_audit", client="X", context="y",
        max_iter=1, timeout=10, strategy="multiturn",
        session_root=session_root, runner=runner,
    )
    argv = json.loads(captured.read_text())
    assert argv[argv.index("--strategy") + 1] == "multiturn"


def test_env_passthrough_preserved(tmp_path, monkeypatch):
    session_root = _stub_session_root(tmp_path)
    captured = tmp_path / "env.json"

    runner = _stub_runner(tmp_path, f"""
import os, json
from pathlib import Path
Path({str(captured)!r}).write_text(json.dumps({{
    "EVAL_BACKEND_OVERRIDE": os.environ.get("EVAL_BACKEND_OVERRIDE", ""),
    "AUTORESEARCH_CONTEXT": os.environ.get("AUTORESEARCH_CONTEXT", ""),
    "X_ENGINE_ANGLE_ID": os.environ.get("X_ENGINE_ANGLE_ID", ""),
}}))
""")

    monkeypatch.setenv("EVAL_BACKEND_OVERRIDE", "opencode")
    monkeypatch.setenv("AUTORESEARCH_CONTEXT", "126")
    monkeypatch.setenv("X_ENGINE_ANGLE_ID", "126")

    run_experiment.run_experiment(
        domain="x_engine", client="jr", context="126",
        max_iter=1, timeout=10, session_root=session_root, runner=runner,
    )
    env = json.loads(captured.read_text())
    assert env["EVAL_BACKEND_OVERRIDE"] == "opencode"
    assert env["AUTORESEARCH_CONTEXT"] == "126"
    assert env["X_ENGINE_ANGLE_ID"] == "126"


def test_extra_env_overrides_inherited(tmp_path):
    session_root = _stub_session_root(tmp_path)
    captured = tmp_path / "env.json"

    runner = _stub_runner(tmp_path, f"""
import os, json
from pathlib import Path
Path({str(captured)!r}).write_text(json.dumps({{
    "MY_VAR": os.environ.get("MY_VAR", ""),
}}))
""")

    run_experiment.run_experiment(
        domain="geo", client="x", context="y",
        max_iter=1, timeout=10,
        session_root=session_root, runner=runner,
        extra_env={"MY_VAR": "set_by_caller"},
    )
    env = json.loads(captured.read_text())
    assert env["MY_VAR"] == "set_by_caller"


def test_argv_shape_matches_v006_contract(tmp_path):
    session_root = _stub_session_root(tmp_path)
    captured = tmp_path / "argv.json"

    runner = _stub_runner(tmp_path, f"""
import sys, json
from pathlib import Path
Path({str(captured)!r}).write_text(json.dumps(sys.argv))
sys.exit(0)
""")

    run_experiment.run_experiment(
        domain="geo", client="mayoclinic", context="https://example.com",
        max_iter=30, timeout=1800,
        session_root=session_root, runner=runner,
    )
    argv = json.loads(captured.read_text())
    assert "--domain" in argv and argv[argv.index("--domain") + 1] == "geo"
    assert "--strategy" in argv
    assert "--no-confirm" in argv
    # Positionals at the end in order
    assert argv[-4] == "mayoclinic"
    assert argv[-3] == "https://example.com"
    assert argv[-2] == "30"
    assert argv[-1] == "1800"


def test_main_cli_returns_1_when_no_deliverable(tmp_path, capsys, monkeypatch):
    """When v006 exits 0 but produces no session.md, the CLI exits 1 so
    the caller surfaces variant-output-failure as a distinct signal."""
    session_root = _stub_session_root(tmp_path)
    runner = _stub_runner(tmp_path, "import sys; sys.exit(0)")

    monkeypatch.setattr(run_experiment, "_v006_runpy", lambda: Path("dummy"))
    monkeypatch.setattr(run_experiment, "_default_session_root", lambda: session_root)

    # Patch the inner run_experiment to use our stub runner
    real_run = run_experiment.run_experiment
    def patched_run(**kwargs):
        kwargs.setdefault("runner", runner)
        kwargs.setdefault("session_root", session_root)
        return real_run(**kwargs)
    monkeypatch.setattr(run_experiment, "run_experiment", patched_run)

    rc = run_experiment.main([
        "--domain", "geo", "--client", "x", "--context", "y",
        "--max-iter", "1", "--timeout", "10",
    ])
    assert rc == 1
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert parsed["exit_code"] == 0
    assert parsed["deliverable_present"] is False
