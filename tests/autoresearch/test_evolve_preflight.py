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
        require_holdout=False,  # search-only: skip judge/holdout preflight
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
        require_holdout=False,  # search-only: skip judge/holdout preflight
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


def test_opencode_probe_pins_opencode_config_when_missing(monkeypatch, evolve_module):
    """opencode discovers config by walking up to .git; a probe with a
    curated env that lacks OPENCODE_CONFIG would mis-route. Probe must
    auto-pin the repo's opencode.json when the env doesn't have it."""
    captured_env = {}
    def fake_run(cmd, **kwargs):
        captured_env.update(kwargs.get("env") or {})
        return SimpleNamespace(returncode=0, stdout=b"ok\n", stderr=b"")

    monkeypatch.setattr(evolve_module.subprocess, "run", fake_run)
    # _REPO_ROOT/opencode.json must exist for the pin to fire.
    config_path = evolve_module._REPO_ROOT / "opencode.json"
    if not config_path.is_file():
        pytest.skip("opencode.json missing in repo — pin would no-op")
    evolve_module._backend_auth_probe(
        "opencode", "openrouter/deepseek/deepseek-v4-pro", env={},
    )
    assert captured_env.get("OPENCODE_CONFIG") == str(config_path)


def test_codex_probe_detects_credit_exhaustion_signal(monkeypatch, evolve_module):
    """Codex with no credits returns exit 0 + stdout containing
    'credits.has_credits: false' or similar. Killed 3 judge calls in v8.
    Probe must surface this loudly, not pass it as auth-OK."""
    monkeypatch.setattr(
        evolve_module.subprocess, "run",
        lambda cmd, **k: SimpleNamespace(
            returncode=0,
            stdout=b"task_complete: ok\nrate_limits.credits.has_credits: false\n",
            stderr=b"",
        ),
    )
    ok, diag = evolve_module._backend_auth_probe("codex", "gpt-5.5", env={})
    assert ok is False
    assert "credit" in diag.lower()


def test_codex_probe_detects_null_last_agent_message(monkeypatch, evolve_module):
    """Codex's task_complete with null last_agent_message = silently
    produced no output. Common when subscription is rate-limited or the
    model is briefly unavailable. Treat as auth failure."""
    monkeypatch.setattr(
        evolve_module.subprocess, "run",
        lambda cmd, **k: SimpleNamespace(
            returncode=0,
            stdout=b'task_complete: {"last_agent_message": null, "ok": true}\n',
            stderr=b"",
        ),
    )
    ok, diag = evolve_module._backend_auth_probe("codex", "gpt-5.5", env={})
    assert ok is False
    assert "null" in diag.lower()


def test_codex_probe_passes_on_real_response(monkeypatch, evolve_module):
    """Healthy codex: exit 0 + non-trivial stdout. Should NOT trigger
    the credit/null detection."""
    monkeypatch.setattr(
        evolve_module.subprocess, "run",
        lambda cmd, **k: SimpleNamespace(
            returncode=0,
            stdout=b"codex\nok\ntokens used\n1.667\n",
            stderr=b"",
        ),
    )
    ok, diag = evolve_module._backend_auth_probe("codex", "gpt-5.5", env={})
    assert ok is True
    assert diag == "ok"


def test_opencode_probe_preserves_caller_set_opencode_config(
    monkeypatch, evolve_module, tmp_path,
):
    """If the operator already set OPENCODE_CONFIG, the probe must NOT
    overwrite it with the repo default."""
    captured_env = {}
    def fake_run(cmd, **kwargs):
        captured_env.update(kwargs.get("env") or {})
        return SimpleNamespace(returncode=0, stdout=b"ok\n", stderr=b"")

    monkeypatch.setattr(evolve_module.subprocess, "run", fake_run)
    operator_path = str(tmp_path / "operator-opencode.json")
    evolve_module._backend_auth_probe(
        "opencode", "openrouter/deepseek/deepseek-v4-pro",
        env={"OPENCODE_CONFIG": operator_path},
    )
    assert captured_env.get("OPENCODE_CONFIG") == operator_path


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


# --------------------------------------------------------------------------
# Judge retry-with-backoff (Fix #1 follow-up)
# --------------------------------------------------------------------------


def test_post_with_retry_returns_response_on_first_success(monkeypatch):
    """Happy path: judge returns 200 on first attempt, no retries needed."""
    import sys
    from pathlib import Path
    autoresearch_dir = str(Path(__file__).resolve().parents[2] / "autoresearch")
    if autoresearch_dir not in sys.path:
        sys.path.insert(0, autoresearch_dir)
    # Earlier holdout-validation tests use sys.modules.setdefault to inject
    # a stub `evaluate_variant`; that stub may persist across tests. Force
    # a fresh import of the REAL module by removing the stub first.
    if "evaluate_variant" in sys.modules and not getattr(
        sys.modules["evaluate_variant"], "_post_with_retry", None
    ):
        del sys.modules["evaluate_variant"]
    import evaluate_variant as ev_var
    import httpx as real_httpx
    import time as real_time
    ev_var.httpx = real_httpx
    ev_var.time = real_time
    ev_var.log_event = lambda **kw: None

    class FakeResponse:
        status_code = 200
        text = '{"score": 7.0}'

    calls = []
    def fake_post(url, **kwargs):
        calls.append(url)
        return FakeResponse()

    monkeypatch.setattr(ev_var.httpx, "post", fake_post)
    monkeypatch.setattr(ev_var, "log_event", lambda **kw: None)

    response = ev_var._post_with_retry(
        endpoint="http://judge/invoke/score",
        request_body={},
        token="t",
        fixture_id="geo-x",
        domain="geo",
        variant_id="v013",
    )
    assert response.status_code == 200
    assert len(calls) == 1


def test_post_with_retry_retries_on_500_then_succeeds(monkeypatch):
    """v3/v5 fingerprint: judge returns 500 once, succeeds on retry."""
    import sys
    from pathlib import Path
    autoresearch_dir = str(Path(__file__).resolve().parents[2] / "autoresearch")
    if autoresearch_dir not in sys.path:
        sys.path.insert(0, autoresearch_dir)
    # Earlier holdout-validation tests use sys.modules.setdefault to inject
    # a stub `evaluate_variant`; that stub may persist across tests. Force
    # a fresh import of the REAL module by removing the stub first.
    if "evaluate_variant" in sys.modules and not getattr(
        sys.modules["evaluate_variant"], "_post_with_retry", None
    ):
        del sys.modules["evaluate_variant"]
    import evaluate_variant as ev_var
    import httpx as real_httpx
    import time as real_time
    ev_var.httpx = real_httpx
    ev_var.time = real_time
    ev_var.log_event = lambda **kw: None

    responses = [
        type("R", (), {"status_code": 500, "text": "boom"})(),
        type("R", (), {"status_code": 200, "text": "{}"})(),
    ]
    monkeypatch.setattr(ev_var.httpx, "post", lambda url, **kw: responses.pop(0))
    monkeypatch.setattr(ev_var, "log_event", lambda **kw: None)
    monkeypatch.setattr(ev_var.time, "sleep", lambda s: None)  # skip backoff

    response = ev_var._post_with_retry(
        endpoint="http://judge/invoke/score",
        request_body={},
        token="t",
        fixture_id="geo-x",
        domain="geo",
        variant_id="v013",
    )
    assert response.status_code == 200
    assert responses == []  # both consumed


def test_post_with_retry_retries_on_timeout_then_succeeds(monkeypatch):
    """v4 fingerprint: httpx.ConnectTimeout, retry succeeds."""
    import sys
    from pathlib import Path
    autoresearch_dir = str(Path(__file__).resolve().parents[2] / "autoresearch")
    if autoresearch_dir not in sys.path:
        sys.path.insert(0, autoresearch_dir)
    # Earlier holdout-validation tests use sys.modules.setdefault to inject
    # a stub `evaluate_variant`; that stub may persist across tests. Force
    # a fresh import of the REAL module by removing the stub first.
    if "evaluate_variant" in sys.modules and not getattr(
        sys.modules["evaluate_variant"], "_post_with_retry", None
    ):
        del sys.modules["evaluate_variant"]
    import evaluate_variant as ev_var
    import httpx as real_httpx
    import time as real_time
    ev_var.httpx = real_httpx
    ev_var.time = real_time
    ev_var.log_event = lambda **kw: None

    state = {"attempts": 0}
    def fake_post(url, **kwargs):
        state["attempts"] += 1
        if state["attempts"] == 1:
            raise ev_var.httpx.ConnectTimeout("timed out")
        return type("R", (), {"status_code": 200, "text": "{}"})()

    monkeypatch.setattr(ev_var.httpx, "post", fake_post)
    monkeypatch.setattr(ev_var, "log_event", lambda **kw: None)
    monkeypatch.setattr(ev_var.time, "sleep", lambda s: None)

    response = ev_var._post_with_retry(
        endpoint="http://judge/invoke/score",
        request_body={},
        token="t",
        fixture_id="geo-x",
        domain="geo",
        variant_id="v013",
    )
    assert response.status_code == 200


def test_post_with_retry_raises_after_max_attempts_on_500(monkeypatch):
    """When 500s persist beyond all retries, raise JudgeUnreachable so the
    caller can propagate (and _hint_on_failure prints the resume command)."""
    import sys
    from pathlib import Path
    autoresearch_dir = str(Path(__file__).resolve().parents[2] / "autoresearch")
    if autoresearch_dir not in sys.path:
        sys.path.insert(0, autoresearch_dir)
    # Earlier holdout-validation tests use sys.modules.setdefault to inject
    # a stub `evaluate_variant`; that stub may persist across tests. Force
    # a fresh import of the REAL module by removing the stub first.
    if "evaluate_variant" in sys.modules and not getattr(
        sys.modules["evaluate_variant"], "_post_with_retry", None
    ):
        del sys.modules["evaluate_variant"]
    import evaluate_variant as ev_var
    import httpx as real_httpx
    import time as real_time
    ev_var.httpx = real_httpx
    ev_var.time = real_time
    ev_var.log_event = lambda **kw: None

    monkeypatch.setattr(
        ev_var.httpx, "post",
        lambda url, **kw: type("R", (), {"status_code": 500, "text": "boom"})(),
    )
    monkeypatch.setattr(ev_var, "log_event", lambda **kw: None)
    monkeypatch.setattr(ev_var.time, "sleep", lambda s: None)

    with pytest.raises(ev_var.JudgeUnreachable, match="returned 500"):
        ev_var._post_with_retry(
            endpoint="http://judge/invoke/score",
            request_body={}, token="t",
            fixture_id="geo-x", domain="geo", variant_id="v013",
        )


def test_judge_auth_preflight_fails_on_empty_token(monkeypatch):
    """P0-D: empty EVOLUTION_INVOKE_TOKEN must abort before holdout starts."""
    import sys
    from pathlib import Path
    autoresearch_dir = str(Path(__file__).resolve().parents[2] / "autoresearch")
    if autoresearch_dir not in sys.path:
        sys.path.insert(0, autoresearch_dir)
    import importlib
    if "evolve" in sys.modules:
        importlib.reload(sys.modules["evolve"])
    import evolve
    monkeypatch.setenv("EVOLUTION_JUDGE_URL", "http://localhost:7200")
    monkeypatch.setenv("EVOLUTION_INVOKE_TOKEN", "")
    with pytest.raises(SystemExit) as exc_info:
        evolve._smoke_test_judge_auth()
    assert exc_info.value.code == 1


def test_judge_auth_preflight_fails_on_unset_url(monkeypatch):
    """Holdout configured but EVOLUTION_JUDGE_URL unset → bail."""
    import sys
    from pathlib import Path
    autoresearch_dir = str(Path(__file__).resolve().parents[2] / "autoresearch")
    if autoresearch_dir not in sys.path:
        sys.path.insert(0, autoresearch_dir)
    import importlib
    if "evolve" in sys.modules:
        importlib.reload(sys.modules["evolve"])
    import evolve
    monkeypatch.delenv("EVOLUTION_JUDGE_URL", raising=False)
    monkeypatch.setenv("EVOLUTION_INVOKE_TOKEN", "x")
    with pytest.raises(SystemExit):
        evolve._smoke_test_judge_auth()


def test_judge_auth_preflight_fails_on_401(monkeypatch):
    """Bad token surfaces as 401 from the judge → preflight aborts.
    NOTE: only fires if the probe path actually hits an authed handler.
    Today's preflight uses a deliberately-nonexistent path so 401 is
    impossible from this probe — but if the judge ever wires the probe
    to a real auth-checked handler, this test pins the bail."""
    import sys
    from pathlib import Path
    autoresearch_dir = str(Path(__file__).resolve().parents[2] / "autoresearch")
    if autoresearch_dir not in sys.path:
        sys.path.insert(0, autoresearch_dir)
    import importlib
    if "evolve" in sys.modules:
        importlib.reload(sys.modules["evolve"])
    import evolve
    import httpx as real_httpx
    monkeypatch.setenv("EVOLUTION_JUDGE_URL", "http://localhost:7200")
    monkeypatch.setenv("EVOLUTION_INVOKE_TOKEN", "wrong-token")

    class FakeResp:
        status_code = 401

    monkeypatch.setattr(real_httpx, "request", lambda method, url, **kw: FakeResp())
    with pytest.raises(SystemExit):
        evolve._smoke_test_judge_auth()


def test_judge_auth_preflight_passes_on_404(monkeypatch, capsys):
    """Probe path is deliberately nonexistent. 404 = service reachable;
    that's the success criterion (we don't validate token via probe —
    real scoring call has its own retry on 401)."""
    import sys
    from pathlib import Path
    autoresearch_dir = str(Path(__file__).resolve().parents[2] / "autoresearch")
    if autoresearch_dir not in sys.path:
        sys.path.insert(0, autoresearch_dir)
    import importlib
    if "evolve" in sys.modules:
        importlib.reload(sys.modules["evolve"])
    import evolve
    import httpx as real_httpx
    monkeypatch.setenv("EVOLUTION_JUDGE_URL", "http://localhost:7200")
    monkeypatch.setenv("EVOLUTION_INVOKE_TOKEN", "valid")

    class FakeResp:
        status_code = 404

    monkeypatch.setattr(real_httpx, "request", lambda method, url, **kw: FakeResp())
    evolve._smoke_test_judge_auth()  # should NOT raise
    out = capsys.readouterr().out
    assert "Auth smoke test passed: evolution-judge" in out


def test_judge_auth_preflight_fails_on_connection_refused(monkeypatch):
    """Service down → bail with operator-friendly message."""
    import sys
    from pathlib import Path
    autoresearch_dir = str(Path(__file__).resolve().parents[2] / "autoresearch")
    if autoresearch_dir not in sys.path:
        sys.path.insert(0, autoresearch_dir)
    import importlib
    if "evolve" in sys.modules:
        importlib.reload(sys.modules["evolve"])
    import evolve
    import httpx as real_httpx
    monkeypatch.setenv("EVOLUTION_JUDGE_URL", "http://localhost:7200")
    monkeypatch.setenv("EVOLUTION_INVOKE_TOKEN", "x")

    def fake_request(method, url, **kw):
        raise real_httpx.ConnectError("Connection refused")

    monkeypatch.setattr(real_httpx, "request", fake_request)
    with pytest.raises(SystemExit):
        evolve._smoke_test_judge_auth()


def test_judge_auth_preflight_warns_but_passes_on_timeout(monkeypatch, capsys):
    """Service slow but up — don't fail preflight, the real call has retry."""
    import sys
    from pathlib import Path
    autoresearch_dir = str(Path(__file__).resolve().parents[2] / "autoresearch")
    if autoresearch_dir not in sys.path:
        sys.path.insert(0, autoresearch_dir)
    import importlib
    if "evolve" in sys.modules:
        importlib.reload(sys.modules["evolve"])
    import evolve
    import httpx as real_httpx
    monkeypatch.setenv("EVOLUTION_JUDGE_URL", "http://localhost:7200")
    monkeypatch.setenv("EVOLUTION_INVOKE_TOKEN", "x")

    def fake_request(method, url, **kw):
        raise real_httpx.ReadTimeout("read timed out")

    monkeypatch.setattr(real_httpx, "request", fake_request)
    evolve._smoke_test_judge_auth()  # should NOT raise
    err = capsys.readouterr().err
    assert "WARN: evolution judge slow" in err


def test_post_with_retry_short_circuits_on_codex_credit_exhaustion(monkeypatch):
    """When the judge returns 500 with a codex-credit-exhausted marker, fail
    fast: retry won't refill credits. The body-marker comes from
    judges/invoke_cli.py:invoke_codex which raises a tagged RuntimeError."""
    import sys
    from pathlib import Path
    autoresearch_dir = str(Path(__file__).resolve().parents[2] / "autoresearch")
    if autoresearch_dir not in sys.path:
        sys.path.insert(0, autoresearch_dir)
    if "evaluate_variant" in sys.modules and not getattr(
        sys.modules["evaluate_variant"], "_post_with_retry", None
    ):
        del sys.modules["evaluate_variant"]
    import evaluate_variant as ev_var
    import httpx as real_httpx
    import time as real_time
    ev_var.httpx = real_httpx
    ev_var.time = real_time
    ev_var.log_event = lambda **kw: None

    state = {"attempts": 0}

    def fake_post(url, **kw):
        state["attempts"] += 1
        body = (
            '{"detail": "codex CLI exit 0: codex credits exhausted: '
            'refresh ChatGPT credits"}'
        )
        return type("R", (), {"status_code": 500, "text": body})()

    monkeypatch.setattr(ev_var.httpx, "post", fake_post)
    monkeypatch.setattr(ev_var, "log_event", lambda **kw: None)
    monkeypatch.setattr(ev_var.time, "sleep", lambda s: None)

    with pytest.raises(ev_var.JudgeUnreachable, match="codex credits exhausted"):
        ev_var._post_with_retry(
            endpoint="http://judge/invoke/score",
            request_body={}, token="t",
            fixture_id="geo-x", domain="geo", variant_id="v013",
        )
    # Must short-circuit on first 500 — no retry waste.
    assert state["attempts"] == 1, "credit-exhaustion should not retry"


def test_post_with_retry_short_circuits_on_legacy_credit_marker(monkeypatch):
    """Legacy fingerprint without the wrapped message: raw
    `credits.has_credits: false` line in the body still trips short-circuit."""
    import sys
    from pathlib import Path
    autoresearch_dir = str(Path(__file__).resolve().parents[2] / "autoresearch")
    if autoresearch_dir not in sys.path:
        sys.path.insert(0, autoresearch_dir)
    if "evaluate_variant" in sys.modules and not getattr(
        sys.modules["evaluate_variant"], "_post_with_retry", None
    ):
        del sys.modules["evaluate_variant"]
    import evaluate_variant as ev_var
    import httpx as real_httpx
    import time as real_time
    ev_var.httpx = real_httpx
    ev_var.time = real_time
    ev_var.log_event = lambda **kw: None

    state = {"attempts": 0}

    def fake_post(url, **kw):
        state["attempts"] += 1
        body = '{"detail": "task_complete\\ncredits.has_credits: false"}'
        return type("R", (), {"status_code": 500, "text": body})()

    monkeypatch.setattr(ev_var.httpx, "post", fake_post)
    monkeypatch.setattr(ev_var, "log_event", lambda **kw: None)
    monkeypatch.setattr(ev_var.time, "sleep", lambda s: None)

    with pytest.raises(ev_var.JudgeUnreachable, match="codex credits exhausted"):
        ev_var._post_with_retry(
            endpoint="http://judge/invoke/score",
            request_body={}, token="t",
            fixture_id="geo-x", domain="geo", variant_id="v013",
        )
    assert state["attempts"] == 1


def test_post_with_retry_does_not_retry_on_4xx(monkeypatch):
    """4xx = caller error (bad token, malformed payload). Don't retry; let
    the caller surface the error."""
    import sys
    from pathlib import Path
    autoresearch_dir = str(Path(__file__).resolve().parents[2] / "autoresearch")
    if autoresearch_dir not in sys.path:
        sys.path.insert(0, autoresearch_dir)
    # Earlier holdout-validation tests use sys.modules.setdefault to inject
    # a stub `evaluate_variant`; that stub may persist across tests. Force
    # a fresh import of the REAL module by removing the stub first.
    if "evaluate_variant" in sys.modules and not getattr(
        sys.modules["evaluate_variant"], "_post_with_retry", None
    ):
        del sys.modules["evaluate_variant"]
    import evaluate_variant as ev_var
    import httpx as real_httpx
    import time as real_time
    ev_var.httpx = real_httpx
    ev_var.time = real_time
    ev_var.log_event = lambda **kw: None

    calls = []
    def fake_post(url, **kw):
        calls.append(url)
        return type("R", (), {"status_code": 401, "text": "unauthorized"})()

    monkeypatch.setattr(ev_var.httpx, "post", fake_post)
    monkeypatch.setattr(ev_var, "log_event", lambda **kw: None)
    monkeypatch.setattr(ev_var.time, "sleep", lambda s: None)

    response = ev_var._post_with_retry(
        endpoint="http://judge/invoke/score",
        request_body={}, token="t",
        fixture_id="geo-x", domain="geo", variant_id="v013",
    )
    assert response.status_code == 401
    assert len(calls) == 1  # no retry


# --------------------------------------------------------------------------
# Resume hint on CalledProcessError (Fix #3 follow-up)
# --------------------------------------------------------------------------


def test_hint_on_failure_prints_resume_hint_on_exception(
    tmp_path, monkeypatch, evolve_module, capsys,
):
    """When a wrapped call raises a non-SystemExit exception, the resume
    hint must fire before propagation."""
    variant_dir = tmp_path / "v013"
    variant_dir.mkdir()
    monkeypatch.setattr(evolve_module, "_unsealed_variant_dir", variant_dir)

    with pytest.raises(RuntimeError, match="boom"):
        with evolve_module._hint_on_failure("test-failure"):
            raise RuntimeError("boom")

    err = capsys.readouterr().err
    assert "Graceful stop (test-failure)" in err
    assert "--resume-variant v013" in err


def test_hint_on_failure_does_not_print_on_systemexit(
    tmp_path, monkeypatch, evolve_module, capsys,
):
    """SystemExit means a signal handler already printed the hint; don't
    double-print."""
    variant_dir = tmp_path / "v013"
    variant_dir.mkdir()
    monkeypatch.setattr(evolve_module, "_unsealed_variant_dir", variant_dir)

    with pytest.raises(SystemExit):
        with evolve_module._hint_on_failure("test-systemexit"):
            raise SystemExit(1)

    err = capsys.readouterr().err
    assert "Graceful stop" not in err


def test_hint_on_failure_no_print_on_clean_exit(
    tmp_path, monkeypatch, evolve_module, capsys,
):
    """Happy path: no exception, no hint printed."""
    variant_dir = tmp_path / "v013"
    variant_dir.mkdir()
    monkeypatch.setattr(evolve_module, "_unsealed_variant_dir", variant_dir)

    with evolve_module._hint_on_failure("test-clean"):
        pass

    err = capsys.readouterr().err
    assert "Graceful stop" not in err
