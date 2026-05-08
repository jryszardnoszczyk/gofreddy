"""marketing_audit fresh-strategy driver tests.

Validates two pieces of the 2026-05-08 evening Unit 3 fix:

1. The default-strategy router in run.py — marketing_audit gets ``fresh``,
   all other lanes get ``multiturn``, and an operator-supplied
   ``--strategy`` always wins.
2. The driver shell script — exits at iter 1 when session.md is already
   COMPLETE/BLOCKED; runs to MAX_ITERS otherwise; bubbles run.py exit code.

The shell script is exercised against a stub run.py that just touches
session.md (or echoes an error) — full end-to-end verification needs a
live agent and is covered by the substrate-validation runbook, not unit
tests.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_PY_PATH = REPO_ROOT / "autoresearch" / "archive" / "v006" / "run.py"
DRIVER_SCRIPT = (
    REPO_ROOT
    / "autoresearch"
    / "archive"
    / "v006"
    / "scripts"
    / "run_marketing_audit_to_complete.sh"
)


# ---------------------------------------------------------------------------
# Default-strategy routing helper
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def run_py_module():
    """Load run.py as a module so we can call ``_default_strategy_for``
    directly without spawning a subprocess. The module has heavy
    side-effecting imports (watchdog, runtime); add the scripts dir to
    sys.path first so its inner ``from runtime ... import ...`` resolves."""
    script_dir = RUN_PY_PATH.parent
    scripts_dir = script_dir / "scripts"
    autoresearch_dir = script_dir.parent.parent
    for entry in (str(scripts_dir), str(autoresearch_dir), str(script_dir)):
        if entry not in sys.path:
            sys.path.insert(0, entry)

    spec = importlib.util.spec_from_file_location("v006_run_py", RUN_PY_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["v006_run_py"] = module
    spec.loader.exec_module(module)
    yield module
    sys.modules.pop("v006_run_py", None)


def test_default_strategy_marketing_audit_is_fresh(run_py_module):
    assert run_py_module._default_strategy_for("marketing_audit") == "fresh"


def test_default_strategy_geo_is_multiturn(run_py_module):
    assert run_py_module._default_strategy_for("geo") == "multiturn"


def test_default_strategy_competitive_is_multiturn(run_py_module):
    assert run_py_module._default_strategy_for("competitive") == "multiturn"


def test_default_strategy_monitoring_is_multiturn(run_py_module):
    assert run_py_module._default_strategy_for("monitoring") == "multiturn"


def test_default_strategy_storyboard_is_multiturn(run_py_module):
    assert run_py_module._default_strategy_for("storyboard") == "multiturn"


def test_fresh_strategy_domains_contains_marketing_audit(run_py_module):
    """Substrate invariant — if a future lane wants fresh-strategy,
    add it to ``_FRESH_STRATEGY_DOMAINS`` rather than overriding the
    default at the call site."""
    assert "marketing_audit" in run_py_module._FRESH_STRATEGY_DOMAINS


# ---------------------------------------------------------------------------
# Driver shell script behaviour
# ---------------------------------------------------------------------------


def _make_stub_run_py(stub_dir: Path, body: str) -> Path:
    """Create a stub `run.py` that the driver can invoke. ``body`` is
    inserted into a ``main()`` body; the stub mirrors run.py's CLI
    enough that the driver's ``python3 run.py …`` call succeeds."""
    stub = stub_dir / "run.py"
    stub.write_text(
        "#!/usr/bin/env python3\n"
        "import os, pathlib, sys\n"
        "args = sys.argv[1:]\n"
        f"{body}\n"
    )
    stub.chmod(0o755)
    return stub


def _run_driver(
    tmp_path: Path,
    *,
    stub_body: str,
    initial_session_md: str | None = None,
    max_iters: int = 3,
    timeout: int = 30,
) -> subprocess.CompletedProcess:
    """Run the real driver script against a fake repo layout in tmp_path.

    Layout:
      tmp_path/
        autoresearch/archive/v006/
          run.py          (stub)
          scripts/run_marketing_audit_to_complete.sh  (real driver)
          sessions/marketing_audit/<CLIENT>/session.md
    """
    archive_dir = tmp_path / "autoresearch" / "archive" / "v006"
    scripts_dir = archive_dir / "scripts"
    sessions_dir = archive_dir / "sessions" / "marketing_audit" / "TestCo"
    scripts_dir.mkdir(parents=True)
    sessions_dir.mkdir(parents=True)

    # Place the stub at archive_dir/run.py so the driver's REPO_ROOT
    # calculation ("$(dirname ${BASH_SOURCE[0]})/../../../..") resolves to
    # tmp_path and finds the stub at the same relative path.
    _make_stub_run_py(archive_dir, stub_body)

    if initial_session_md is not None:
        (sessions_dir / "session.md").write_text(initial_session_md)

    # Copy the real driver into the fake scripts dir so its REPO_ROOT
    # math anchors to tmp_path.
    driver_copy = scripts_dir / DRIVER_SCRIPT.name
    driver_copy.write_text(DRIVER_SCRIPT.read_text())
    driver_copy.chmod(0o755)

    env = {**os.environ, "MAX_ITERS": str(max_iters)}
    return subprocess.run(
        ["bash", str(driver_copy), "TestCo", "https://test.example"],
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
    )


def test_driver_exits_zero_when_status_complete_after_iter_1(tmp_path: Path):
    # Stub writes COMPLETE status to session.md on every invocation.
    stub_body = (
        "session_md = pathlib.Path(__file__).parent / 'sessions/marketing_audit/TestCo/session.md'\n"
        "session_md.write_text('## Status: COMPLETE\\n')\n"
        "sys.exit(0)\n"
    )
    result = _run_driver(tmp_path, stub_body=stub_body, max_iters=5)
    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "terminal" in result.stdout
    assert "iter 1" in result.stdout


def test_driver_runs_to_max_iters_when_status_in_progress(tmp_path: Path):
    # Stub keeps session.md at IN_PROGRESS forever. Driver should hit MAX_ITERS.
    stub_body = (
        "session_md = pathlib.Path(__file__).parent / 'sessions/marketing_audit/TestCo/session.md'\n"
        "session_md.write_text('## Status: IN_PROGRESS\\n')\n"
        "sys.exit(0)\n"
    )
    result = _run_driver(tmp_path, stub_body=stub_body, max_iters=3)
    assert result.returncode == 3, f"expected exit 3 (max iters), got {result.returncode}"
    assert "MAX_ITERS=3" in result.stdout
    # Should have iterated exactly 3 times.
    assert result.stdout.count("driver iter") == 3


def test_driver_propagates_run_py_failure(tmp_path: Path):
    # Stub exits non-zero on first call.
    stub_body = "sys.stderr.write('synthetic failure\\n'); sys.exit(7)\n"
    result = _run_driver(tmp_path, stub_body=stub_body, max_iters=5)
    assert result.returncode == 7, f"expected exit 7 from stub, got {result.returncode}"
    assert "halting" in result.stdout


def test_driver_exits_zero_on_blocked_status(tmp_path: Path):
    stub_body = (
        "session_md = pathlib.Path(__file__).parent / 'sessions/marketing_audit/TestCo/session.md'\n"
        "session_md.write_text('## Status: BLOCKED\\nReason: missing brief\\n')\n"
        "sys.exit(0)\n"
    )
    result = _run_driver(tmp_path, stub_body=stub_body, max_iters=5)
    assert result.returncode == 0
    assert "BLOCKED" in result.stdout
