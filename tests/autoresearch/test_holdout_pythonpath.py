"""Regression: holdout's _copy_variant_for_holdout puts run.py at
/tmp/autoresearch-holdouts/.../v007/run.py, which breaks run.py's
self-bootstrap (it computes AUTORESEARCH_DIR=__file__.parent.parent,
which is the temp workspace, not the real autoresearch/).

Fix: _run_fixture_session injects autoresearch/ on PYTHONPATH so
`from harness.agent ...` resolves regardless of variant_dir layout.

Pi v007 finalize on 2026-04-30 surfaced this: every holdout fixture
crashed with `ModuleNotFoundError: No module named 'harness.agent'`,
but the orchestrator caught the per-fixture errors and reported PASS
overall (geo: 0.01 — the all-zero floor). Without this fix the holdout
suite is functionally broken."""

from __future__ import annotations

import sys
from pathlib import Path

# Path-bootstrap matches sibling tests
_repo_root = Path(__file__).resolve().parents[2]
_autoresearch_dir = _repo_root / "autoresearch"
if str(_autoresearch_dir) in sys.path:
    sys.path.remove(str(_autoresearch_dir))
sys.path.insert(0, str(_autoresearch_dir))
for _mod in [m for m in list(sys.modules) if m == "harness" or m.startswith("harness.")]:
    file_attr = getattr(sys.modules[_mod], "__file__", None) or ""
    if not file_attr.startswith(str(_autoresearch_dir)):
        del sys.modules[_mod]

import evaluate_variant  # noqa: E402


def test_runner_session_injects_autoresearch_on_pythonpath(monkeypatch, tmp_path):
    """Spawn must see autoresearch/ on PYTHONPATH so a holdout-temp run.py
    can import harness.agent / runtime / watchdog / workflows."""
    captured: dict[str, dict] = {}

    class _Done:
        def __init__(self): self.returncode = 0
        def communicate(self, timeout=None): return ("", "")
        def wait(self, timeout=None): pass
        def poll(self): return 0
        @property
        def pid(self): return 1234

    def fake_popen(cmd, *, env, **kwargs):
        captured["env"] = env
        return _Done()

    monkeypatch.setattr(evaluate_variant.subprocess, "Popen", fake_popen)
    fake_variant = tmp_path / "v007"
    fake_variant.mkdir()
    (fake_variant / "run.py").write_text("# stub\n")

    target = evaluate_variant.EvalTarget(backend="codex", model="gpt-5.5", reasoning_effort="high")
    fixture = evaluate_variant.Fixture(
        suite_id="holdout-v1",
        domain="geo",
        fixture_id="geo-x",
        client="x",
        context="https://example.com",
        version="1.0",
        max_iter=1,
        timeout=10,
        env={},
    )

    evaluate_variant._run_fixture_session(fake_variant, fixture, target)

    pythonpath = captured["env"].get("PYTHONPATH", "")
    paths = pythonpath.split(":")
    assert str(_autoresearch_dir) in paths, (
        f"autoresearch/ must be on PYTHONPATH so run.py can import harness; "
        f"got: {pythonpath!r}"
    )
    # autoresearch/ must come BEFORE any prior entries that might shadow harness
    assert paths[0] == str(_autoresearch_dir)


def test_runner_session_does_not_duplicate_autoresearch_pythonpath(monkeypatch, tmp_path):
    """Idempotent: pre-set PYTHONPATH containing autoresearch/ stays as-is."""
    captured: dict[str, dict] = {}

    class _Done:
        def __init__(self): self.returncode = 0
        def communicate(self, timeout=None): return ("", "")
        def wait(self, timeout=None): pass
        def poll(self): return 0
        @property
        def pid(self): return 1234

    def fake_popen(cmd, *, env, **kwargs):
        captured["env"] = env
        return _Done()

    monkeypatch.setattr(evaluate_variant.subprocess, "Popen", fake_popen)
    monkeypatch.setenv(
        "PYTHONPATH",
        f"{_autoresearch_dir}:/some/other/path",
    )
    fake_variant = tmp_path / "v007"
    fake_variant.mkdir()
    (fake_variant / "run.py").write_text("# stub\n")

    target = evaluate_variant.EvalTarget(backend="codex", model="gpt-5.5", reasoning_effort="high")
    fixture = evaluate_variant.Fixture(
        suite_id="holdout-v1",
        domain="geo",
        fixture_id="geo-x",
        client="x",
        context="https://example.com",
        version="1.0",
        max_iter=1,
        timeout=10,
        env={},
    )

    evaluate_variant._run_fixture_session(fake_variant, fixture, target)

    pythonpath = captured["env"].get("PYTHONPATH", "")
    # Should not duplicate
    assert pythonpath.count(str(_autoresearch_dir)) == 1
