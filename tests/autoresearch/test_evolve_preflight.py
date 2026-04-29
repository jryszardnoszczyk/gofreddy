"""Preflight reliability tests — current_runtime materialization, auth
smoke test, and holdout manifest validation.

Closes the v1/v6/v8-class failures from the Apr 27-28 evolution runs
where preflight passed but the run died mid-flight from issues that
should have been caught at startup.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def evolve_module(monkeypatch):
    """Import autoresearch.evolve with heavy dependencies stubbed.

    Mirrors test_resume_evolve.py's evolve_module fixture so preflight
    helpers are testable in isolation without the full runtime."""
    import sys
    import types

    if "evolve_ops" not in sys.modules:
        evolve_ops = types.ModuleType("evolve_ops")
        evolve_ops.load_repo_env_defaults = lambda *a, **k: []
        evolve_ops.normalize_lane = lambda x: x
        evolve_ops.load_search_config = lambda *a, **k: ("", "", "", "", "")
        evolve_ops.holdout_configured = lambda *a, **k: False
        evolve_ops.holdout_suite_id = lambda lane: "holdout"
        evolve_ops.finalize_candidate_ids = lambda *a, **k: []
        evolve_ops.write_finalized_shortlist = lambda *a, **k: ""
        evolve_ops.best_finalized_variant = lambda *a, **k: None
        evolve_ops.current_head_variant_id = lambda *a, **k: ""
        evolve_ops.mark_promoted = lambda *a, **k: None
        evolve_ops.set_current_head = lambda *a, **k: None
        evolve_ops.previous_promoted_variant = lambda *a, **k: None
        evolve_ops.baseline_seeded = lambda *a, **k: True
        evolve_ops.prepare_meta_workspace = lambda *a, **k: ("", "")
        evolve_ops.write_lane_context = lambda *a, **k: None
        evolve_ops.sync_meta_workspace = lambda *a, **k: None
        evolve_ops.variant_in_lineage = lambda *a, **k: True
        evolve_ops._load_latest_lineage = lambda *a, **k: {}
        evolve_ops._holdout_composite = lambda *a, **k: None
        evolve_ops.record_head_score = lambda *a, **k: None
        evolve_ops.emit_saturation_cycle_events = lambda *a, **k: None
        evolve_ops.check_and_rollback_regressions = lambda *a, **k: None
        sys.modules["evolve_ops"] = evolve_ops
    if "regen_program_docs" not in sys.modules:
        m = types.ModuleType("regen_program_docs")
        m.regen = lambda *a, **k: None
        sys.modules["regen_program_docs"] = m
    if "compute_metrics" not in sys.modules:
        m = types.ModuleType("compute_metrics")
        m.record_generation = lambda *a, **k: None
        sys.modules["compute_metrics"] = m

    import importlib
    import evolve as ev
    importlib.reload(ev)
    return ev


# --------------------------------------------------------------------------
# current_runtime auto-materialization (Fix 3)
# --------------------------------------------------------------------------


def test_preflight_calls_ensure_materialized_runtime_when_lane_manifest_present(
    tmp_path, monkeypatch, evolve_module,
):
    """v1 wipeout: every fixture crashed because current_runtime was missing.
    Preflight must materialize it when a lane manifest is present, before
    any per-fixture spawn touches the filesystem."""
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()
    # Lane manifest present → materialization should run.
    (archive_dir / "current.json").write_text(
        json.dumps({"core": "v001", "geo": "v001"}),
        encoding="utf-8",
    )

    materialize_calls = []
    monkeypatch.setattr(
        "lane_runtime.ensure_materialized_runtime",
        lambda d: materialize_calls.append(Path(d)),
    )
    monkeypatch.setattr("lane_runtime.has_lane_manifest", lambda d: True)
    # Skip the auth smoke test in this preflight test — covered separately.
    monkeypatch.setattr(evolve_module, "_smoke_test_backend_auth", lambda c: None)
    # Skip the freddy + meta backend PATH checks.
    monkeypatch.setattr(evolve_module.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(
        evolve_module.subprocess, "run",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout=b"", stderr=b""),
    )

    config = evolve_module.EvolutionConfig(
        command="run",
        archive_dir=archive_dir,
        lane="geo",
        meta_backend="claude",
        meta_model="opus",
        cli_pythonpath="",
    )
    evolve_module.preflight_checks(config)
    assert len(materialize_calls) == 1
    assert materialize_calls[0] == archive_dir


def test_preflight_skips_materialize_when_no_lane_manifest(
    tmp_path, monkeypatch, evolve_module,
):
    """Legacy archives without current.json shouldn't trigger
    materialization; the legacy single-promoted-variant path handles them."""
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()
    materialize_calls = []
    monkeypatch.setattr(
        "lane_runtime.ensure_materialized_runtime",
        lambda d: materialize_calls.append(Path(d)),
    )
    monkeypatch.setattr("lane_runtime.has_lane_manifest", lambda d: False)
    monkeypatch.setattr(evolve_module, "_smoke_test_backend_auth", lambda c: None)
    monkeypatch.setattr(evolve_module.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(
        evolve_module.subprocess, "run",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout=b"", stderr=b""),
    )

    config = evolve_module.EvolutionConfig(
        command="run",
        archive_dir=archive_dir,
        lane="geo",
        meta_backend="claude",
        meta_model="opus",
        cli_pythonpath="",
    )
    evolve_module.preflight_checks(config)
    assert materialize_calls == []


# --------------------------------------------------------------------------
# Inner-agent auth smoke test (Fix 4)
# --------------------------------------------------------------------------


def test_backend_auth_probe_returns_ok_on_clean_response(monkeypatch, evolve_module):
    """Successful probe: exit 0, non-empty stdout."""
    captured_cmd = []

    def fake_run(cmd, **kwargs):
        captured_cmd.append(cmd)
        return SimpleNamespace(returncode=0, stdout=b"ok\n", stderr=b"")

    monkeypatch.setattr(evolve_module.subprocess, "run", fake_run)

    ok, diag = evolve_module._backend_auth_probe("claude", "opus", env={})
    assert ok is True
    assert diag == "ok"
    assert captured_cmd[0][0] == "claude"
    assert "--max-turns" in captured_cmd[0]


def test_backend_auth_probe_fails_on_nonzero_exit(monkeypatch, evolve_module):
    """v6-class silent fail surfacing: exit nonzero must produce a clean
    diagnostic, not a swallowed warning."""
    monkeypatch.setattr(
        evolve_module.subprocess, "run",
        lambda cmd, **k: SimpleNamespace(
            returncode=1, stdout=b"", stderr=b"auth required",
        ),
    )
    ok, diag = evolve_module._backend_auth_probe("claude", "opus", env={})
    assert ok is False
    assert "exit=1" in diag
    assert "auth required" in diag


def test_backend_auth_probe_fails_on_empty_stdout(monkeypatch, evolve_module):
    """The exact v6 fingerprint: exit 0 but no stdout (claude/codex
    sometimes shell out silently when not authenticated)."""
    monkeypatch.setattr(
        evolve_module.subprocess, "run",
        lambda cmd, **k: SimpleNamespace(returncode=0, stdout=b"", stderr=b""),
    )
    ok, diag = evolve_module._backend_auth_probe("claude", "opus", env={})
    assert ok is False
    assert "empty stdout" in diag


def test_backend_auth_probe_fails_on_missing_cli(monkeypatch, evolve_module):
    """FileNotFoundError → friendly 'CLI not on PATH' error."""
    def boom(cmd, **kwargs):
        raise FileNotFoundError(2, "No such file", cmd[0])

    monkeypatch.setattr(evolve_module.subprocess, "run", boom)
    ok, diag = evolve_module._backend_auth_probe("claude", "opus", env={})
    assert ok is False
    assert "not on PATH" in diag


def test_backend_auth_probe_fails_on_timeout(monkeypatch, evolve_module):
    import subprocess as real_subprocess
    def boom(cmd, **kwargs):
        raise real_subprocess.TimeoutExpired(cmd, kwargs.get("timeout", 30))

    monkeypatch.setattr(evolve_module.subprocess, "run", boom)
    ok, diag = evolve_module._backend_auth_probe("claude", "opus", env={})
    assert ok is False
    assert "timeout" in diag


def test_smoke_test_aborts_when_meta_backend_unauthenticated(
    monkeypatch, evolve_module, capsys,
):
    """v6 fingerprint: meta agent silently shells out. Preflight should
    print an actionable error naming the suggested fix, then exit 1."""
    monkeypatch.setattr(
        evolve_module, "_backend_auth_probe",
        lambda backend, model, env: (False, "exit=1"),
    )
    config = evolve_module.EvolutionConfig(
        command="run", lane="geo",
        meta_backend="claude", meta_model="opus",
        cli_pythonpath="",
    )
    monkeypatch.setattr(evolve_module, "_build_meta_env", lambda c, w: {})

    with pytest.raises(SystemExit) as exc:
        evolve_module._smoke_test_backend_auth(config)
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "meta backend auth probe failed" in err
    assert "claude" in err
    assert "Suggestion:" in err  # actionable hint present


def test_smoke_test_probes_eval_backend_when_different_from_meta(
    monkeypatch, evolve_module,
):
    """Meta=claude + eval=codex is the default operator config; the
    smoke test must probe both. When same backend+model, probe once."""
    probes = []

    def fake_probe(backend, model, env):
        probes.append((backend, model))
        return (True, "ok")

    monkeypatch.setattr(evolve_module, "_backend_auth_probe", fake_probe)
    monkeypatch.setattr(evolve_module, "_build_meta_env", lambda c, w: {})
    monkeypatch.setenv("EVOLUTION_EVAL_BACKEND", "codex")
    monkeypatch.setenv("EVOLUTION_EVAL_MODEL", "gpt-5.5")

    config = evolve_module.EvolutionConfig(
        command="run", lane="geo",
        meta_backend="claude", meta_model="opus",
        cli_pythonpath="",
    )
    evolve_module._smoke_test_backend_auth(config)
    assert probes == [("claude", "opus"), ("codex", "gpt-5.5")]


def test_smoke_test_skips_eval_probe_when_same_as_meta(
    monkeypatch, evolve_module,
):
    """If meta and eval are identical, only one probe (avoids redundant
    paid CLI calls during preflight)."""
    probes = []
    monkeypatch.setattr(
        evolve_module, "_backend_auth_probe",
        lambda b, m, e: (probes.append((b, m)), (True, "ok"))[1],
    )
    monkeypatch.setattr(evolve_module, "_build_meta_env", lambda c, w: {})
    monkeypatch.setenv("EVOLUTION_EVAL_BACKEND", "claude")
    monkeypatch.setenv("EVOLUTION_EVAL_MODEL", "opus")

    config = evolve_module.EvolutionConfig(
        command="run", lane="geo",
        meta_backend="claude", meta_model="opus",
        cli_pythonpath="",
    )
    evolve_module._smoke_test_backend_auth(config)
    assert probes == [("claude", "opus")]


# --------------------------------------------------------------------------
# Holdout manifest validation (Fix 5)
# --------------------------------------------------------------------------


def test_configure_eval_target_validates_holdout_manifest(
    tmp_path, monkeypatch, evolve_module, capsys,
):
    """v8 fingerprint: search-scoring runs successfully, then finalize
    crashes after 30+ min because the holdout manifest's eval_target
    declares a different backend/model. Catch this at preflight.

    Mock _load_holdout_manifest + _require_eval_target so the test
    focuses on the new preflight wiring rather than the existing
    normalization chain (which has its own tests)."""
    holdout_path = tmp_path / "holdout-v1.json"
    holdout_path.write_text("{}", encoding="utf-8")

    monkeypatch.setenv("EVOLUTION_HOLDOUT_MANIFEST", str(holdout_path))
    monkeypatch.setenv("EVOLUTION_EVAL_BACKEND", "codex")
    monkeypatch.setenv("EVOLUTION_EVAL_MODEL", "gpt-5.5")

    import sys
    fake_evaluate_variant = sys.modules.setdefault(
        "evaluate_variant", type(sys)("evaluate_variant"),
    )
    fake_evaluate_variant._load_holdout_manifest = lambda env, lane: {"_": "ok"}

    def fake_require(env, manifest):
        raise RuntimeError(
            "EVOLUTION_EVAL_MODEL='gpt-5.5' does not match suite "
            "eval_target.model='gpt-5.4'."
        )
    fake_evaluate_variant._require_eval_target = fake_require

    config = evolve_module.EvolutionConfig(
        command="run", lane="geo",
        meta_backend="claude", meta_model="opus",
        search_eval_backend="codex",
        search_eval_model="gpt-5.5",
        cli_pythonpath="",
    )

    with pytest.raises(SystemExit) as exc:
        evolve_module.configure_eval_target_env(config)
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "holdout suite eval_target mismatch" in err
    assert "gpt-5.4" in err  # name of the bad value surfaced to operator


def test_configure_eval_target_passes_when_holdout_not_configured(
    monkeypatch, evolve_module,
):
    """When EVOLUTION_HOLDOUT_MANIFEST is absent, holdout validation
    should be a clean no-op — operators run search-only without
    configuring holdout."""
    monkeypatch.delenv("EVOLUTION_HOLDOUT_MANIFEST", raising=False)
    monkeypatch.setenv("EVOLUTION_EVAL_BACKEND", "codex")
    monkeypatch.setenv("EVOLUTION_EVAL_MODEL", "gpt-5.5")

    config = evolve_module.EvolutionConfig(
        command="run", lane="geo",
        meta_backend="claude", meta_model="opus",
        search_eval_backend="codex",
        search_eval_model="gpt-5.5",
        cli_pythonpath="",
    )
    # Should not raise; should not exit.
    evolve_module.configure_eval_target_env(config)


def test_configure_eval_target_passes_when_holdout_matches(
    tmp_path, monkeypatch, evolve_module,
):
    """Holdout manifest with matching eval_target passes preflight."""
    holdout_path = tmp_path / "holdout-v1.json"
    holdout_path.write_text("{}", encoding="utf-8")

    monkeypatch.setenv("EVOLUTION_HOLDOUT_MANIFEST", str(holdout_path))
    monkeypatch.setenv("EVOLUTION_EVAL_BACKEND", "codex")
    monkeypatch.setenv("EVOLUTION_EVAL_MODEL", "gpt-5.5")

    import sys
    fake_evaluate_variant = sys.modules.setdefault(
        "evaluate_variant", type(sys)("evaluate_variant"),
    )
    fake_evaluate_variant._load_holdout_manifest = lambda env, lane: {"_": "ok"}
    fake_evaluate_variant._require_eval_target = lambda env, manifest: None  # pass

    config = evolve_module.EvolutionConfig(
        command="run", lane="geo",
        meta_backend="claude", meta_model="opus",
        search_eval_backend="codex",
        search_eval_model="gpt-5.5",
        cli_pythonpath="",
    )
    evolve_module.configure_eval_target_env(config)
