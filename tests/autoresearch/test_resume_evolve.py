"""Tests for autoresearch.sessions + evolve.py resume parity helpers.

Mirrors tests/harness/test_sessions.py for the SessionsFile/SessionRecord
contract, then adds resume-specific coverage for ``_resume_search_scored``,
``_resume_parent_id``, and ``viable_resume_id``.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

# Imports resolve via tests/autoresearch/conftest.py which adds
# autoresearch/ + autoresearch/harness/ to sys.path.
import sessions as autoresearch_sessions
from sessions import (
    SessionRecord,
    SessionsFile,
    claude_session_jsonl,
    codex_session_jsonl,
    viable_resume_id,
)


# --------------------------------------------------------------------------
# SessionsFile / SessionRecord — port from tests/harness/test_sessions.py
# --------------------------------------------------------------------------


def test_load_returns_empty_when_file_missing(tmp_path):
    sessions = SessionsFile(tmp_path / ".session_ids.json")
    assert sessions.all() == {}


def test_begin_writes_record_and_creates_file(tmp_path):
    path = tmp_path / ".session_ids.json"
    sessions = SessionsFile(path)
    sessions.begin("meta-v013", "sid-123", engine="claude")
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "meta-v013" in data
    assert data["meta-v013"]["session_id"] == "sid-123"
    assert data["meta-v013"]["status"] == "running"
    assert data["meta-v013"]["engine"] == "claude"


def test_finish_transitions_status(tmp_path):
    sessions = SessionsFile(tmp_path / ".session_ids.json")
    sessions.begin("fixture-v013-geo-semrush", "sid-x", engine="claude")
    sessions.finish("fixture-v013-geo-semrush", "complete")
    record = sessions.get("fixture-v013-geo-semrush")
    assert record is not None
    assert record.status == "complete"
    assert record.finished_at is not None


def test_finish_unknown_key_is_noop(tmp_path, caplog):
    sessions = SessionsFile(tmp_path / ".session_ids.json")
    with caplog.at_level("WARNING", logger="autoresearch.sessions"):
        sessions.finish("ghost", "complete")
    assert "unknown agent_key ghost" in caplog.text


def test_reopen_loads_prior_state(tmp_path):
    """A fresh SessionsFile over the same path sees prior records so resume
    logic can make skip/resume decisions across process restarts."""
    path = tmp_path / ".session_ids.json"
    first = SessionsFile(path)
    first.begin("meta-v013", "sid-1", engine="claude")
    first.finish("meta-v013", "complete")
    first.begin("fixture-v013-geo-semrush", "sid-2", engine="claude")

    second = SessionsFile(path)
    meta_rec = second.get("meta-v013")
    fix_rec = second.get("fixture-v013-geo-semrush")
    assert meta_rec is not None and meta_rec.status == "complete"
    # Interrupted fixture stays "running" so --resume-variant picks it up.
    assert fix_rec is not None and fix_rec.status == "running"


def test_running_returns_only_in_flight_records(tmp_path):
    sessions = SessionsFile(tmp_path / ".session_ids.json")
    sessions.begin("meta-v013", "sid-meta", engine="claude")
    sessions.finish("meta-v013", "complete")
    sessions.begin("fixture-v013-geo-semrush", "sid-fix", engine="claude")
    running = sessions.running()
    assert list(running.keys()) == ["fixture-v013-geo-semrush"]


def test_corrupt_json_starts_empty_with_warning(tmp_path, caplog):
    path = tmp_path / ".session_ids.json"
    path.write_text("not json at all", encoding="utf-8")
    with caplog.at_level("WARNING", logger="autoresearch.sessions"):
        sessions = SessionsFile(path)
    assert sessions.all() == {}
    assert "corrupted" in caplog.text


def test_malformed_entry_is_skipped_not_fatal(tmp_path, caplog):
    path = tmp_path / ".session_ids.json"
    path.write_text(json.dumps({
        "good": {"agent_key": "good", "session_id": "s", "engine": "claude",
                 "status": "complete", "started_at": 1.0, "finished_at": 2.0},
        "bad": {"session_id": "s"},  # missing required fields
    }), encoding="utf-8")
    with caplog.at_level("WARNING", logger="autoresearch.sessions"):
        sessions = SessionsFile(path)
    assert "good" in sessions.all()
    assert "bad" not in sessions.all()
    assert "malformed" in caplog.text


def test_concurrent_begin_and_finish_is_safe(tmp_path):
    """Holdout fan-out writes to .session_ids.json concurrently from a
    ThreadPoolExecutor; the lock + atomic write serialize updates."""
    sessions = SessionsFile(tmp_path / ".session_ids.json")
    barrier = threading.Barrier(6)

    def write_one(key: str, sid: str) -> None:
        barrier.wait()
        sessions.begin(key, sid, engine="claude")
        sessions.finish(key, "complete")

    threads = [
        threading.Thread(target=write_one, args=(f"fixture-{t}", f"sid-{t}"))
        for t in ("a", "b", "c", "d", "e", "f")
    ]
    for th in threads:
        th.start()
    for th in threads:
        th.join()

    all_records = sessions.all()
    assert len(all_records) == 6
    for record in all_records.values():
        assert record.status == "complete"


def test_atomic_write_no_partial_file_on_midwrite_crash(tmp_path, monkeypatch):
    """A failure during os.replace must leave the prior good state intact —
    no half-written JSON, no leftover .session_ids-*.tmp."""
    sessions = SessionsFile(tmp_path / ".session_ids.json")
    sessions.begin("meta-v013", "sid-1", engine="claude")
    prior = (tmp_path / ".session_ids.json").read_text(encoding="utf-8")

    def boom(*args, **kwargs):
        raise OSError("simulated disk full")

    monkeypatch.setattr(autoresearch_sessions.os, "replace", boom)

    with pytest.raises(OSError):
        sessions.begin("fixture-v013-geo", "sid-x", engine="claude")

    # File still in prior state, no orphaned tmp files.
    monkeypatch.undo()
    current = (tmp_path / ".session_ids.json").read_text(encoding="utf-8")
    assert current == prior
    leftovers = list(tmp_path.glob(".session_ids-*.tmp"))
    assert leftovers == [], f"tmp file leaked: {leftovers}"


def test_session_record_dataclass_is_immutable():
    record = SessionRecord(
        agent_key="k", session_id="s", engine="claude",
        status="running", started_at=1.0,
    )
    with pytest.raises(Exception):  # FrozenInstanceError
        record.status = "complete"  # type: ignore[misc]


# --------------------------------------------------------------------------
# viable_resume_id — JSONL existence check
# --------------------------------------------------------------------------


def test_viable_resume_id_returns_none_when_claude_jsonl_missing(tmp_path):
    """The silent-hang case: claude rate-limited before creating its JSONL.
    ``--resume <sid>`` would error out; viable_resume_id should return None
    so the caller falls back to a fresh session."""
    record = SessionRecord(
        agent_key="meta-v013", session_id="sid-x", engine="claude",
        status="running", started_at=1.0,
    )
    # wt_path doesn't exist → encoded JSONL path doesn't exist → None
    assert viable_resume_id(record, wt_path=tmp_path / "nonexistent") is None


def test_viable_resume_id_returns_sid_when_claude_jsonl_exists(tmp_path, monkeypatch):
    """When the local claude JSONL exists for this session, resume is viable."""
    fake_home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    wt = tmp_path / "workdir"
    wt.mkdir(parents=True)
    sid = "abcd-1234"
    jsonl = claude_session_jsonl(wt, sid)
    jsonl.parent.mkdir(parents=True, exist_ok=True)
    jsonl.write_text("{}", encoding="utf-8")

    record = SessionRecord(
        agent_key="meta-v013", session_id=sid, engine="claude",
        status="running", started_at=1.0,
    )
    assert viable_resume_id(record, wt_path=wt) == sid


def test_viable_resume_id_unknown_engine_returns_none():
    """Opencode lacks a stable resume mechanism — viable_resume_id should
    return None for unsupported engines so the caller falls back to fresh."""
    record = SessionRecord(
        agent_key="meta-v013", session_id="sid", engine="opencode",
        status="running", started_at=1.0,
    )
    assert viable_resume_id(record, wt_path=Path("/tmp")) is None


def test_codex_session_jsonl_returns_none_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    assert codex_session_jsonl("nonexistent-sid") is None


def test_codex_session_jsonl_finds_existing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    sessions_dir = tmp_path / ".codex" / "sessions" / "2026" / "04" / "28"
    sessions_dir.mkdir(parents=True)
    sid = "01abcd-12-34-5678"
    rollout = sessions_dir / f"rollout-2026-04-28T14-00-00-{sid}.jsonl"
    rollout.write_text("{}\n", encoding="utf-8")
    assert codex_session_jsonl(sid) == rollout


# --------------------------------------------------------------------------
# evolve.py resume helpers — _resume_search_scored, _resume_parent_id
# --------------------------------------------------------------------------


@pytest.fixture
def evolve_module(monkeypatch):
    """Import autoresearch.evolve with the heavy dependencies stubbed.

    evolve.py drags in evolve_ops + lane_registry + critique_manifest at
    module import. The conftest stubs are not enough — we add minimal
    additional stubs here so the module loads in the test environment.
    """
    # Stub the modules evolve.py imports at module-load time that we don't
    # exercise in these tests. Conftest already stubs archive_index,
    # frontier, and lane_paths.
    import sys, types
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
        regen_program_docs = types.ModuleType("regen_program_docs")
        regen_program_docs.regen = lambda *a, **k: None
        sys.modules["regen_program_docs"] = regen_program_docs
    if "compute_metrics" not in sys.modules:
        compute_metrics = types.ModuleType("compute_metrics")
        compute_metrics.record_generation = lambda *a, **k: None
        sys.modules["compute_metrics"] = compute_metrics

    import importlib
    import evolve as _evolve
    importlib.reload(_evolve)  # ensure fresh state across tests
    return _evolve


def test_resume_search_scored_true_for_real_composite(tmp_path):
    import evolve as ev
    variant_dir = tmp_path / "v013"
    variant_dir.mkdir()
    (variant_dir / "scores.json").write_text(
        json.dumps({"composite": 6.97, "geo": 7.1}),
        encoding="utf-8",
    )
    assert ev._resume_search_scored(variant_dir) is True


def test_resume_search_scored_false_on_zero_composite(tmp_path):
    """The stale-clone case: shutil.copytree preserves scores.json from the
    parent, but the composite is 0 (or absent) until search-scoring runs."""
    import evolve as ev
    variant_dir = tmp_path / "v013"
    variant_dir.mkdir()
    (variant_dir / "scores.json").write_text(
        json.dumps({"composite": 0}),
        encoding="utf-8",
    )
    assert ev._resume_search_scored(variant_dir) is False


def test_resume_search_scored_false_when_file_missing(tmp_path):
    import evolve as ev
    variant_dir = tmp_path / "v013"
    variant_dir.mkdir()
    assert ev._resume_search_scored(variant_dir) is False


def test_resume_search_scored_false_on_corrupt_json(tmp_path):
    import evolve as ev
    variant_dir = tmp_path / "v013"
    variant_dir.mkdir()
    (variant_dir / "scores.json").write_text("not json", encoding="utf-8")
    assert ev._resume_search_scored(variant_dir) is False


def test_resume_parent_id_reads_lineage_jsonl(tmp_path):
    import evolve as ev
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()
    lineage = archive_dir / "lineage.jsonl"
    lineage.write_text(
        json.dumps({"id": "v012", "parent": "v009"}) + "\n"
        + json.dumps({"id": "v013", "parent": "v012"}) + "\n",
        encoding="utf-8",
    )
    assert ev._resume_parent_id(archive_dir, "v013") == "v012"
    assert ev._resume_parent_id(archive_dir, "v012") == "v009"


def test_resume_parent_id_returns_none_when_variant_missing(tmp_path):
    import evolve as ev
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()
    (archive_dir / "lineage.jsonl").write_text(
        json.dumps({"id": "v012", "parent": "v009"}) + "\n",
        encoding="utf-8",
    )
    assert ev._resume_parent_id(archive_dir, "v999") is None


def test_resume_parent_id_returns_none_when_lineage_missing(tmp_path):
    import evolve as ev
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()
    assert ev._resume_parent_id(archive_dir, "v013") is None


# --------------------------------------------------------------------------
# CLI flag wiring — --resume-variant / --resume-fixture / --fixtures-only
# --------------------------------------------------------------------------


def test_run_subcommand_accepts_resume_variant():
    import evolve as ev
    parser = ev.build_parser()
    args = parser.parse_args(["run", "--resume-variant", "v013", "--lane", "geo"])
    assert args.resume_variant == "v013"
    assert args.lane == "geo"


def test_run_subcommand_accepts_resume_fixture_and_implies_variant():
    import evolve as ev
    parser = ev.build_parser()
    args = parser.parse_args(
        ["run", "--resume-fixture", "v013:geo-semrush-pricing", "--lane", "geo"]
    )
    assert args.resume_fixture == "v013:geo-semrush-pricing"
    assert args.resume_variant is None  # --resume-variant default; load_config derives from --resume-fixture


def test_run_subcommand_accepts_fixtures_only():
    import evolve as ev
    parser = ev.build_parser()
    args = parser.parse_args(
        ["run", "--fixtures-only", "--resume-variant", "v013", "--lane", "geo"]
    )
    assert args.fixtures_only is True
    assert args.resume_variant == "v013"


# --------------------------------------------------------------------------
# _force_rerun_one_fixture — wipes session_dir + marks SessionsFile failed
# --------------------------------------------------------------------------


def test_force_rerun_one_fixture_clears_sessions_record_and_dir(tmp_path):
    import evolve as ev
    variant_dir = tmp_path / "v013"
    (variant_dir / "sessions" / "geo" / "semrush").mkdir(parents=True)
    (variant_dir / "sessions" / "geo" / "semrush" / "digest.md").write_text("x")
    (variant_dir / "sessions" / "geo" / "ahrefs").mkdir(parents=True)
    (variant_dir / "sessions" / "geo" / "ahrefs" / "digest.md").write_text("y")

    sessions = SessionsFile(variant_dir / ".session_ids.json")
    sessions.begin("fixture-v013-geo-semrush-pricing", "", engine="claude")
    sessions.finish("fixture-v013-geo-semrush-pricing", "complete")
    sessions.begin("fixture-v013-geo-ahrefs-pricing", "", engine="claude")
    sessions.finish("fixture-v013-geo-ahrefs-pricing", "complete")

    ev._force_rerun_one_fixture(variant_dir, "geo-semrush-pricing", sessions)

    # Targeted fixture's record is no longer 'complete' (now 'failed' so
    # skip-if-complete won't engage on the next run).
    target = sessions.get("fixture-v013-geo-semrush-pricing")
    assert target is not None and target.status == "failed"
    # Targeted client_dir wiped.
    assert not (variant_dir / "sessions" / "geo" / "semrush").exists()
    # Other fixture's record + dir untouched.
    other = sessions.get("fixture-v013-geo-ahrefs-pricing")
    assert other is not None and other.status == "complete"
    assert (variant_dir / "sessions" / "geo" / "ahrefs" / "digest.md").exists()


def test_force_rerun_one_fixture_handles_missing_sessions_dir(tmp_path):
    """No-op when session_dir doesn't exist yet — never raises."""
    import evolve as ev
    variant_dir = tmp_path / "v013"
    variant_dir.mkdir()
    sessions = SessionsFile(variant_dir / ".session_ids.json")
    # Should not raise.
    ev._force_rerun_one_fixture(variant_dir, "geo-semrush-pricing", sessions)


# --------------------------------------------------------------------------
# evaluate_variant._run_and_score_fixture — skip-if-already-complete path
# --------------------------------------------------------------------------


def test_run_and_score_fixture_skips_when_record_complete_and_deliverables_exist(
    tmp_path, monkeypatch,
):
    """Resume scenario: a prior run completed this fixture. The current run
    should skip the session spawn entirely and rescore the cached output."""
    import evaluate_variant as ev_var

    # Build a minimal Fixture using the dataclass shape.
    Fixture = ev_var.Fixture
    EvalTarget = ev_var.EvalTarget
    fixture = Fixture(
        suite_id="search-v1",
        domain="geo",
        fixture_id="geo-semrush-pricing",
        client="semrush",
        context="https://semrush.com",
        version="1.0",
        max_iter=15,
        timeout=1200,
        env={},
        anchor=False,
    )
    eval_target = EvalTarget(backend="codex", model="gpt-5.5", reasoning_effort="high")

    variant_dir = tmp_path / "v013"
    session_dir = variant_dir / "sessions" / "geo" / "semrush"
    session_dir.mkdir(parents=True)
    (session_dir / "digest.md").write_text("digest", encoding="utf-8")
    # Drop an optimized/*.md so _has_deliverables returns True for geo.
    (session_dir / "optimized").mkdir()
    (session_dir / "optimized" / "post.md").write_text("post", encoding="utf-8")

    # Pre-existing 'complete' record in SessionsFile.
    sf = SessionsFile(variant_dir / ".session_ids.json")
    sf.begin("fixture-v013-geo-semrush-pricing", "", engine="codex")
    sf.finish("fixture-v013-geo-semrush-pricing", "complete")

    # Fail the test if _run_fixture_session is called — skip path means
    # we MUST NOT spawn the runner subprocess.
    spawn_called = []
    def fake_spawn(*args, **kwargs):
        spawn_called.append(args)
        raise AssertionError("_run_fixture_session should not be called on skip path")
    monkeypatch.setattr(ev_var, "_run_fixture_session", fake_spawn)

    # Stub _score_session to return a sentinel so we don't hit the real
    # scoring HTTP call.
    monkeypatch.setattr(
        ev_var, "_score_session",
        lambda session_run, **kw: {"composite": 5.5, "fixture_id": session_run.fixture.fixture_id},
    )

    domain, fid, result, produced = ev_var._run_and_score_fixture(
        variant_dir, fixture, eval_target,
        variant_id="v013", campaign_id="c1",
        skip_sessions=False, sessions_file=sf,
    )
    assert spawn_called == []  # skip path engaged
    assert produced is True
    assert result["composite"] == 5.5


def test_run_fixture_session_uses_explicit_agent_key_when_provided(
    tmp_path, monkeypatch,
):
    """Holdout + dryrun callers pass agent_key explicitly to keep their
    records under distinct prefixes (holdout-* / dryrun-*) instead of the
    default fixture-* key. Verifies the override survives begin/finish."""
    import evaluate_variant as ev_var

    Fixture = ev_var.Fixture
    EvalTarget = ev_var.EvalTarget
    fixture = Fixture(
        suite_id="search-v1",
        domain="geo",
        fixture_id="geo-semrush-pricing",
        client="semrush",
        context="https://semrush.com",
        version="1.0",
        max_iter=15, timeout=1200, env={}, anchor=False,
    )
    eval_target = EvalTarget(backend="codex", model="gpt-5.5", reasoning_effort="high")

    variant_dir = tmp_path / "v013"
    variant_dir.mkdir()
    sf = SessionsFile(variant_dir / ".session_ids.json")

    # Stub Popen so we don't actually spawn a runner.
    class FakeProcess:
        returncode = 0
        def communicate(self, timeout=None):
            return ("", "")
        def poll(self):
            return 0
        def wait(self):
            pass

    monkeypatch.setattr(ev_var.subprocess, "Popen", lambda *a, **k: FakeProcess())

    ev_var._run_fixture_session(
        variant_dir, fixture, eval_target,
        sessions_file=sf,
        agent_key="holdout-v013-geo-semrush-pricing",
    )
    # Custom key landed.
    assert sf.get("holdout-v013-geo-semrush-pricing") is not None
    # Default key was NOT used.
    assert sf.get("fixture-v013-geo-semrush-pricing") is None


def test_run_and_score_fixture_runs_session_when_record_failed(
    tmp_path, monkeypatch,
):
    """If the prior run marked the record 'failed' (--resume-fixture path or
    a prior crash), the session should be re-spawned, not skipped."""
    import evaluate_variant as ev_var

    Fixture = ev_var.Fixture
    EvalTarget = ev_var.EvalTarget
    fixture = Fixture(
        suite_id="search-v1",
        domain="geo",
        fixture_id="geo-semrush-pricing",
        client="semrush",
        context="https://semrush.com",
        version="1.0",
        max_iter=15, timeout=1200, env={}, anchor=False,
    )
    eval_target = EvalTarget(backend="codex", model="gpt-5.5", reasoning_effort="high")

    variant_dir = tmp_path / "v013"
    variant_dir.mkdir()

    sf = SessionsFile(variant_dir / ".session_ids.json")
    sf.begin("fixture-v013-geo-semrush-pricing", "", engine="codex")
    sf.finish("fixture-v013-geo-semrush-pricing", "failed")

    spawn_called = []
    SessionRun = ev_var.SessionRun
    def fake_spawn(variant_dir_, fixture_, eval_target_, sessions_file=None):
        spawn_called.append(fixture_.fixture_id)
        return SessionRun(
            fixture=fixture_, session_dir=None,
            produced_output=False, runner_exit_code=0, wall_time_seconds=0.0,
        )
    monkeypatch.setattr(ev_var, "_run_fixture_session", fake_spawn)
    monkeypatch.setattr(
        ev_var, "_score_session",
        lambda session_run, **kw: {"composite": 0, "fixture_id": session_run.fixture.fixture_id},
    )

    ev_var._run_and_score_fixture(
        variant_dir, fixture, eval_target,
        variant_id="v013", campaign_id="c1",
        skip_sessions=False, sessions_file=sf,
    )
    assert spawn_called == ["geo-semrush-pricing"]  # re-spawned, not skipped


# --------------------------------------------------------------------------
# Section 4 — harness/agent.py per-fixture sentinel logic
# --------------------------------------------------------------------------


@pytest.fixture
def harness_agent_module():
    """Import autoresearch/harness/agent.py via the autoresearch/harness
    package. Mirrors test_backend_selection.py's import recipe — flush any
    stale top-level `harness` package from sys.modules so `from harness
    import agent` resolves to autoresearch/harness/agent.py."""
    import sys
    from pathlib import Path
    autoresearch_dir = str(Path(__file__).resolve().parents[2] / "autoresearch")
    if autoresearch_dir in sys.path:
        sys.path.remove(autoresearch_dir)
    sys.path.insert(0, autoresearch_dir)
    for _mod in [m for m in list(sys.modules) if m == "harness" or m.startswith("harness.")]:
        if not getattr(sys.modules[_mod], "__file__", "").startswith(autoresearch_dir):
            del sys.modules[_mod]
    from harness import agent as agent_mod
    return agent_mod


def test_session_id_sentinel_uses_session_dir(tmp_path, harness_agent_module):
    """The sentinel lives next to the session_dir, not next to the log file."""
    agent = harness_agent_module
    session_dir = tmp_path / "v013" / "sessions" / "geo" / "semrush"
    session_dir.mkdir(parents=True)
    log_path = session_dir / "sessions" / "main.log"
    log_path.parent.mkdir(parents=True)
    sentinel = agent._session_id_sentinel(log_path)
    assert sentinel == session_dir / ".session_id"


def test_session_id_sentinel_returns_a_writable_path(tmp_path, harness_agent_module):
    """Helper must return a path whose parent is an existing directory so
    callers can write the sentinel without ENOENT. Never crashes on weird
    directory shapes — the fallback chain (parent.parent → parent → parent)
    always resolves to something writable."""
    agent = harness_agent_module
    log_path = tmp_path / "isolated.log"
    sentinel = agent._session_id_sentinel(log_path)
    assert sentinel.parent.is_dir(), f"sentinel parent must be writable: {sentinel}"
    assert sentinel.name == ".session_id"


def test_read_resume_sid_returns_none_when_sentinel_missing(tmp_path, harness_agent_module):
    agent = harness_agent_module
    log_path = tmp_path / "v013" / "sessions" / "geo" / "semrush" / "main.log"
    log_path.parent.mkdir(parents=True)
    assert agent._read_resume_sid(log_path) is None


def test_read_resume_sid_returns_none_when_jsonl_missing(tmp_path, harness_agent_module, monkeypatch):
    """Sentinel exists but claude's local JSONL doesn't — must return None
    so caller falls back to fresh spawn instead of trying --resume on a
    non-existent session."""
    agent = harness_agent_module
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
    session_dir = tmp_path / "v013" / "sessions" / "geo" / "semrush"
    session_dir.mkdir(parents=True)
    (session_dir / ".session_id").write_text("abcd-1234", encoding="utf-8")
    log_path = session_dir / "sessions" / "main.log"
    log_path.parent.mkdir(parents=True)
    assert agent._read_resume_sid(log_path) is None


def test_read_resume_sid_returns_sid_when_sentinel_and_jsonl_both_exist(
    tmp_path, harness_agent_module, monkeypatch,
):
    """Both sentinel + JSONL present → resume is viable, return the sid."""
    agent = harness_agent_module
    fake_home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    session_dir = tmp_path / "v013" / "sessions" / "geo" / "semrush"
    session_dir.mkdir(parents=True)
    sid = "1111-2222-3333"
    (session_dir / ".session_id").write_text(sid, encoding="utf-8")

    encoded = str(agent.SCRIPT_DIR).replace("/", "-")
    jsonl = fake_home / ".claude" / "projects" / encoded / f"{sid}.jsonl"
    jsonl.parent.mkdir(parents=True)
    jsonl.write_text("{}", encoding="utf-8")

    log_path = session_dir / "sessions" / "main.log"
    log_path.parent.mkdir(parents=True)
    assert agent._read_resume_sid(log_path) == sid


def test_read_resume_sid_returns_none_on_empty_sentinel(tmp_path, harness_agent_module):
    agent = harness_agent_module
    session_dir = tmp_path / "v013" / "sessions" / "geo" / "semrush"
    session_dir.mkdir(parents=True)
    (session_dir / ".session_id").write_text("", encoding="utf-8")
    log_path = session_dir / "sessions" / "main.log"
    log_path.parent.mkdir(parents=True)
    assert agent._read_resume_sid(log_path) is None


def test_run_agent_session_writes_sentinel_before_spawn_for_claude(
    tmp_path, harness_agent_module, monkeypatch,
):
    """Mid-session resume relies on the sentinel being on disk BEFORE claude
    starts. If the spawn dies before the sentinel exists, resume can't find
    the sid. This test asserts sentinel.is_file() at spawn time."""
    agent = harness_agent_module
    monkeypatch.setattr(agent, "session_backend", lambda: "claude")
    monkeypatch.setattr(agent, "session_model", lambda: "opus")

    session_dir = tmp_path / "v013" / "sessions" / "geo" / "semrush"
    session_dir.mkdir(parents=True)
    log_path = session_dir / "sessions" / "main.log"
    log_path.parent.mkdir(parents=True)

    sentinel_state = {"existed_at_spawn": False, "content_at_spawn": ""}

    class FakeProcess:
        returncode = 1  # non-zero → sentinel preserved

        def wait(self, timeout=None):
            sentinel = session_dir / ".session_id"
            sentinel_state["existed_at_spawn"] = sentinel.is_file()
            if sentinel.is_file():
                sentinel_state["content_at_spawn"] = sentinel.read_text().strip()
            return 1

    def fake_popen(cmd, **kwargs):
        return FakeProcess()

    monkeypatch.setattr(agent.subprocess, "Popen", fake_popen)

    agent.run_agent_session("test prompt", timeout=10, log_path=log_path)

    assert sentinel_state["existed_at_spawn"] is True
    # UUID format
    assert len(sentinel_state["content_at_spawn"]) == 36
    # Sentinel preserved on non-zero exit (so next run can resume)
    assert (session_dir / ".session_id").is_file()


def test_run_agent_session_removes_sentinel_on_clean_exit(
    tmp_path, harness_agent_module, monkeypatch,
):
    """Clean exit → sentinel gone, so the next invocation starts fresh
    instead of resuming a completed conversation."""
    agent = harness_agent_module
    monkeypatch.setattr(agent, "session_backend", lambda: "claude")
    monkeypatch.setattr(agent, "session_model", lambda: "opus")

    session_dir = tmp_path / "v013" / "sessions" / "geo" / "semrush"
    session_dir.mkdir(parents=True)
    log_path = session_dir / "sessions" / "main.log"
    log_path.parent.mkdir(parents=True)

    class FakeProcess:
        returncode = 0
        def wait(self, timeout=None):
            return 0

    monkeypatch.setattr(agent.subprocess, "Popen", lambda *a, **k: FakeProcess())

    agent.run_agent_session("test prompt", timeout=10, log_path=log_path)
    assert not (session_dir / ".session_id").is_file()


def test_run_agent_session_removes_stale_sentinel_on_codex_backend(
    tmp_path, harness_agent_module, monkeypatch,
):
    """If a prior claude run left a sentinel and the operator switches to
    codex, the stale sentinel must be removed so it doesn't mislead a
    future invocation. Codex doesn't support pre-mint resume."""
    agent = harness_agent_module
    monkeypatch.setattr(agent, "session_backend", lambda: "codex")
    monkeypatch.setattr(agent, "session_model", lambda: "gpt-5.5")

    session_dir = tmp_path / "v013" / "sessions" / "geo" / "semrush"
    session_dir.mkdir(parents=True)
    (session_dir / ".session_id").write_text("stale-claude-sid", encoding="utf-8")
    log_path = session_dir / "sessions" / "main.log"
    log_path.parent.mkdir(parents=True)

    class FakeProcess:
        returncode = 0
        def wait(self, timeout=None):
            return 0

    monkeypatch.setattr(agent.subprocess, "Popen", lambda *a, **k: FakeProcess())

    agent.run_agent_session("test prompt", timeout=10, log_path=log_path)
    assert not (session_dir / ".session_id").is_file()


def test_agent_command_passes_session_id_for_claude_fresh_spawn(harness_agent_module, monkeypatch):
    agent = harness_agent_module
    monkeypatch.setattr(agent, "session_backend", lambda: "claude")
    sid = "fresh-uuid-123"
    cmd = agent._agent_command(model="opus", max_turns=10, session_id=sid)
    assert "--session-id" in cmd
    assert cmd[cmd.index("--session-id") + 1] == sid


def test_agent_command_passes_resume_for_claude_re_attach(harness_agent_module, monkeypatch):
    agent = harness_agent_module
    monkeypatch.setattr(agent, "session_backend", lambda: "claude")
    sid = "resume-uuid-123"
    cmd = agent._agent_command(model="opus", max_turns=10, resume_sid=sid)
    assert "--resume" in cmd
    assert cmd[cmd.index("--resume") + 1] == sid
    assert "--session-id" not in cmd  # mutually exclusive


def test_agent_command_codex_ignores_session_id(harness_agent_module, monkeypatch):
    """Codex CLI doesn't support pre-mint --session-id; verify our wiring
    doesn't sneak it in (would crash the spawn)."""
    agent = harness_agent_module
    monkeypatch.setattr(agent, "session_backend", lambda: "codex")
    monkeypatch.setattr(agent, "codex_sandbox", lambda: "read-only")
    monkeypatch.setattr(agent, "codex_approval_policy", lambda: "never")
    monkeypatch.setattr(agent, "codex_reasoning_effort", lambda: "high")
    monkeypatch.setattr(agent, "codex_web_search", lambda: "disabled")
    cmd = agent._agent_command(
        model="gpt-5.5", max_turns=10,
        session_id="ignored-uuid", resume_sid="ignored-resume-uuid",
    )
    assert "--session-id" not in cmd
    assert "--resume" not in cmd


# --------------------------------------------------------------------------
# Acceptance criterion #1 — end-to-end mid-meta-agent resume
# --------------------------------------------------------------------------


def test_resume_meta_agent_invokes_claude_resume_with_continue_prompt(
    tmp_path, monkeypatch,
):
    """End-to-end mocked test for the plan's acceptance criterion #1:
    Kill mid-meta-agent → --resume-variant re-invokes claude with
    --resume <sid> + short continue prompt."""
    import evolve as ev

    # Set up a half-baked variant_dir with a meta workspace + a 'running'
    # SessionsFile record + a pretend claude JSONL on disk.
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()
    variant_id = "v013"
    variant_dir = archive_dir / variant_id
    variant_dir.mkdir()
    meta_workspace = variant_dir / ".meta_workspace"
    meta_variant_dir = meta_workspace / variant_id
    meta_variant_dir.mkdir(parents=True)

    sid = "deadbeef-1234-5678-90ab-cdef01234567"
    sf = SessionsFile(variant_dir / ".session_ids.json")
    sf.begin(f"meta-{variant_id}", sid, engine="claude")

    # Pretend claude's local JSONL exists (so viable_resume_id returns sid).
    fake_home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    encoded = str(meta_variant_dir).replace("/", "-")
    jsonl = fake_home / ".claude" / "projects" / encoded / f"{sid}.jsonl"
    jsonl.parent.mkdir(parents=True)
    jsonl.write_text("{}", encoding="utf-8")

    # Capture what _run_meta_agent_once was invoked with.
    captured = {"session_id": None, "resume_sid": None, "prompt_text": None}

    def fake_run_meta_agent_once(
        prompt_file, workdir, config, log_file=None,
        session_id=None, resume_sid=None,
    ):
        captured["session_id"] = session_id
        captured["resume_sid"] = resume_sid
        captured["prompt_text"] = prompt_file.read_text() if prompt_file.is_file() else ""
        return 0

    monkeypatch.setattr(ev, "_run_meta_agent_once", fake_run_meta_agent_once)
    monkeypatch.setattr(ev.evolve_ops, "sync_meta_workspace", lambda *a, **k: None)

    # Build a minimal config — only fields _resume_meta_agent reads.
    config = ev.EvolutionConfig(
        command="run",
        archive_dir=archive_dir,
        lane="geo",
        meta_backend="claude",
        meta_model="opus",
    )

    ev._resume_meta_agent(config, variant_dir, meta_workspace, sid, sf)

    # Acceptance criterion #1: claude was invoked with --resume <sid>
    # (we forwarded resume_sid, not session_id) AND the prompt was a short
    # continue message rather than the full meta-template.
    assert captured["resume_sid"] == sid, "resume_sid not threaded through to subprocess"
    assert captured["session_id"] is None or captured["session_id"] == "", "fresh session_id should be None on resume"
    assert "continue from where you stopped" in captured["prompt_text"], (
        "resume prompt must be a short continue message, not the full meta-template"
    )
    # SessionsFile record updated to terminal status.
    record = sf.get(f"meta-{variant_id}")
    assert record is not None and record.status == "complete"
