"""Tests for harness.run — correctness fixes and parallel track-queue semantics.

Bug #3: _commit_fix must stage only this track's allowlist-matching files.
_process_track_queue: worker drains serially, honors graceful-stop, routes RateLimitHit.
"""
from __future__ import annotations

import subprocess
import threading
import time
from pathlib import Path

import pytest

from harness import run as run_mod
from harness.config import Config
from harness.engine import EngineExhausted, RateLimitHit, Verdict
from harness.findings import Finding
from harness.worktree import Worktree


def _init_repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q", "-b", "main", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.email", "t@test"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "t"], check=True)
    # Seed the allowlist directories so new files show under their specific paths.
    for rel in ("cli/freddy/seed.py", "src/api/seed.py", "frontend/seed.js"):
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("seed\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-qm", "seed"], check=True)
    return tmp_path


def _head(repo: Path) -> str:
    return subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()


def _finding(track: str, fid: str = "F-1") -> Finding:
    return Finding(
        id=fid, track=track, category="crash", confidence="high",
        summary="test finding", evidence="", reproduction="", files=(),
    )


def test_capture_patch_writes_to_run_dir_not_worktree(tmp_path):
    """_capture_patch must write to run_dir (outside the worktree) so the patch
    file itself is not visible to the worktree's git status — that's what
    caused the scope-violation loop in smoke run 20260422-174701."""
    wt = _init_repo(tmp_path / "wt")
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    # Fixer makes a tracked-file edit + creates an untracked file.
    (wt / "cli/freddy/seed.py").write_text("modified\n", encoding="utf-8")
    (wt / "cli/freddy/new.py").write_text("brand new\n", encoding="utf-8")

    run_mod._capture_patch(wt, _finding("a", "F-a-1-1"), run_dir)

    patch_path = run_dir / "fix-diffs" / "a" / "F-a-1-1.patch"
    assert patch_path.exists(), "patch file must be written to run_dir"
    content = patch_path.read_text(encoding="utf-8")
    assert "cli/freddy/seed.py" in content, "tracked change missing from patch"
    assert "cli/freddy/new.py" in content, "untracked file missing from patch (git add -N path)"

    # The worktree's git status must NOT show the patch file at any relative path,
    # because the patch lives outside the worktree.
    status = subprocess.check_output(
        ["git", "-C", str(wt), "status", "--porcelain"], text=True,
    )
    assert ".patch" not in status, f"patch leaked into worktree: {status!r}"
    # Intent-to-add reset: untracked file must still be untracked, not staged.
    assert "A  cli/freddy/new.py" not in status
    assert "?? cli/freddy/new.py" in status


def test_capture_patch_handles_clean_worktree(tmp_path):
    """No changes → empty patch file, no crash."""
    wt = _init_repo(tmp_path / "wt")
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    run_mod._capture_patch(wt, _finding("b", "F-b-1-1"), run_dir)
    patch_path = run_dir / "fix-diffs" / "b" / "F-b-1-1.patch"
    assert patch_path.exists()
    assert patch_path.read_text(encoding="utf-8") == ""


# ── Resume-aware dispatch ──────────────────────────────────────────────────


def test_run_dir_for_branch_extracts_timestamp(tmp_path):
    """Branch name and run_dir share a timestamp by construction — the derived
    path must match what run() would have chosen on the original run."""
    staging = tmp_path / "harness" / "runs"
    derived = run_mod._run_dir_for_branch("harness/run-20260422-190507", staging)
    assert derived == staging / "run-20260422-190507"


def test_commit_exists_for_finding_matches_structured_message(tmp_path):
    """Commits use `harness: fix {finding_id}@c{cycle} — {summary}` format. The resume
    skip probe must recognize exactly that prefix and not false-positive.

    Scoped to main..HEAD — so simulate a branch that diverged from main and
    landed a fix commit. Also asserts that a commit ON main (inherited from
    prior runs) does NOT match, which is the actual smoke-e bug.

    Cycle-qualified — evaluators restart numbering from 1 each cycle, so
    `F-c-1-5@c1` and `F-c-1-5@c2` must not cross-match."""
    wt = _init_repo(tmp_path / "wt")
    # First: land an inherited fix commit on main to simulate a previously
    # merged harness run (this is what tripped smoke-e's resume).
    (wt / "cli/freddy/prior.py").write_text("prior run work\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(wt), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(wt), "commit", "-qm",
         "harness: fix F-a-1-1@c1 — from a previously merged run"],
        check=True,
    )
    # Create the staging branch from here and add this run's fix commit.
    subprocess.run(["git", "-C", str(wt), "checkout", "-qb", "harness/run-20260422-ex"], check=True)
    (wt / "cli/freddy/x.py").write_text("change\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(wt), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(wt), "commit", "-qm", "harness: fix F-a-1-7@c1 — this run's defect"],
        check=True,
    )
    # Second fix on cycle 2 with a colliding id-prefix to prove the cycle stamp disambiguates.
    (wt / "cli/freddy/y.py").write_text("change\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(wt), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(wt), "commit", "-qm", "harness: fix F-a-1-7@c2 — cycle 2 defect"],
        check=True,
    )

    # Only the branch-only commits match. The inherited-from-main F-a-1-1 does NOT.
    assert run_mod._commit_exists_for_finding(wt, "F-a-1-7", 1) is True
    assert run_mod._commit_exists_for_finding(wt, "F-a-1-7", 2) is True
    assert run_mod._commit_exists_for_finding(wt, "F-a-1-7", 3) is False
    assert run_mod._commit_exists_for_finding(wt, "F-a-1-1", 1) is False, (
        "inherited commit from main must not falsely skip this run's same-ID finding"
    )
    assert run_mod._commit_exists_for_finding(wt, "F-a-1-8", 1) is False
    # Must NOT match a substring of another finding id (F-a-1 being a prefix of F-a-1-7).
    assert run_mod._commit_exists_for_finding(wt, "F-a-1", 1) is False


def test_resume_starting_cycle_picks_highest_existing(tmp_path):
    run_dir = tmp_path / "run-X"
    # Simulate a prior run that completed cycle 1 and started cycle 2.
    (run_dir / "track-a" / "cycle-1").mkdir(parents=True)
    (run_dir / "track-a" / "cycle-2").mkdir(parents=True)
    (run_dir / "track-b" / "cycle-1").mkdir(parents=True)
    assert run_mod._resume_starting_cycle(run_dir) == 2


def test_resume_starting_cycle_defaults_to_1_for_fresh_run_dir(tmp_path):
    run_dir = tmp_path / "run-Y"
    run_dir.mkdir()
    # No track-*/cycle-* dirs yet — fresh run starts at cycle 1.
    assert run_mod._resume_starting_cycle(run_dir) == 1


def test_resume_starting_cycle_ignores_malformed_cycle_dirs(tmp_path):
    run_dir = tmp_path / "run-Z"
    (run_dir / "track-a" / "cycle-1").mkdir(parents=True)
    (run_dir / "track-a" / "cycle-notanumber").mkdir(parents=True)
    assert run_mod._resume_starting_cycle(run_dir) == 1


def test_commit_fix_stages_all_dirty_files(tmp_path):
    """Worker worktree is isolated — every dirty file IS this fixer's work.
    No per-track filter; commit everything. (Formerly Bug #3 scope-filter test
    — retired along with SCOPE_ALLOWLIST under the per-worker isolation model.)"""
    repo = _init_repo(tmp_path)
    wt = Worktree(path=repo, branch="main", main_repo=repo)
    pre = _head(repo)

    (repo / "cli" / "freddy" / "fix.py").write_text("def fix(): pass\n", encoding="utf-8")
    (repo / "src" / "api" / "also.py").write_text("support change\n", encoding="utf-8")

    commit = run_mod._commit_fix(wt, _finding("a"), pre)

    assert commit is not None
    assert set(commit.files) == {"cli/freddy/fix.py", "src/api/also.py"}
    status = subprocess.check_output(
        ["git", "-C", str(repo), "status", "--porcelain"], text=True,
    )
    assert "cli/freddy/fix.py" not in status
    assert "src/api/also.py" not in status


def test_commit_fix_skips_when_no_changes(tmp_path):
    """If the fixer produced no working-tree changes, there's nothing to commit."""
    repo = _init_repo(tmp_path)
    wt = Worktree(path=repo, branch="main", main_repo=repo)
    pre = _head(repo)
    # No file writes — clean worktree.

    commit = run_mod._commit_fix(wt, _finding("a"), pre)

    assert commit is None
    assert _head(repo) == pre  # No new commit on HEAD


def _state(tmp_path: Path, walltime: int = 14400) -> run_mod.RunState:
    from harness.sessions import SessionsFile
    return run_mod.RunState(
        run_dir=tmp_path, staging_branch="harness/test", token="t", ts="20260101-000000",
        pre_dirty=set(), sessions=SessionsFile(tmp_path / "sessions.json"),
    )


def _config(walltime: int = 14400) -> Config:
    return Config(max_walltime=walltime)


def test_run_one_finding_continues_on_generic_exception(tmp_path, monkeypatch):
    """A generic exception from one finding must NOT kill the worker — the
    worker rolls back and the parallel driver moves on to the next finding."""
    rollback_calls: list[str] = []
    def fake_process(config, wt, staging_wt, finding, state):
        raise RuntimeError("fixer blew up")
    monkeypatch.setattr(run_mod, "_process_finding", fake_process)
    monkeypatch.setattr(run_mod.worktree, "rollback_worker",
                        lambda wt: rollback_calls.append(wt.path.name))

    state = _state(tmp_path)
    wt = Worktree(path=tmp_path, branch="main", main_repo=tmp_path)
    run_mod._run_one_finding(_config(), wt, wt, _finding("a", "F-a-1"), state)

    assert state.graceful_stop_requested is False  # generic error does NOT graceful-stop
    assert len(rollback_calls) == 1


def test_run_one_finding_rate_limit_triggers_graceful_stop(tmp_path, monkeypatch):
    """RateLimitHit from a finding sets graceful_stop_requested and rolls back
    the worker's worktree so partial edits don't leak across findings."""
    rollback_calls: list[str] = []
    def fake_process(config, wt, staging_wt, finding, state):
        raise RateLimitHit(resets_at=1776855600, rate_limit_type="five_hour")
    monkeypatch.setattr(run_mod, "_process_finding", fake_process)
    monkeypatch.setattr(run_mod.worktree, "rollback_worker",
                        lambda wt: rollback_calls.append(wt.path.name))

    state = _state(tmp_path)
    wt = Worktree(path=tmp_path, branch="main", main_repo=tmp_path)
    run_mod._run_one_finding(_config(), wt, wt, _finding("a", "F-a-1"), state)

    assert state.graceful_stop_requested is True
    assert "five_hour" in state.graceful_stop_reason
    assert len(rollback_calls) == 1


def test_run_one_finding_engine_exhausted_skips_finding_continues_run(tmp_path, monkeypatch):
    """EngineExhausted (transient retries used up) rolls back the worker and
    skips THIS finding, but does NOT trigger graceful stop — other findings
    in the queue should still be attempted, and the run continues.

    This intentionally diverges from RateLimitHit (which DOES graceful-stop)
    because transient API throttles ("Server is temporarily limiting requests")
    don't mean the run is doomed — they just mean this one agent invocation
    couldn't complete within the retry budget."""
    rollback_calls: list[str] = []
    def fake_process(config, wt, staging_wt, finding, state):
        raise EngineExhausted("out of retries")
    monkeypatch.setattr(run_mod, "_process_finding", fake_process)
    monkeypatch.setattr(run_mod.worktree, "rollback_worker",
                        lambda wt: rollback_calls.append(wt.path.name))

    state = _state(tmp_path)
    wt = Worktree(path=tmp_path, branch="main", main_repo=tmp_path)
    run_mod._run_one_finding(_config(), wt, wt, _finding("a", "F-a-1"), state)

    assert state.graceful_stop_requested is False  # run continues
    assert len(rollback_calls) == 1  # worker still rolled back to clean slate


def test_process_findings_parallel_single_worker_respects_walltime(tmp_path, monkeypatch):
    """Walltime exceeded drops remaining findings in the single-worker
    (pool is None) fallback path."""
    processed: list[str] = []
    def fake_run_one(config, wt, staging_wt, finding, state):
        processed.append(finding.id)
    monkeypatch.setattr(run_mod, "_run_one_finding", fake_run_one)

    findings = [_finding("a", "F-1"), _finding("a", "F-2")]
    state = _state(tmp_path)
    state.start_ts = time.time() - 1_000_000  # simulate already past walltime
    wt = Worktree(path=tmp_path, branch="main", main_repo=tmp_path)
    run_mod._process_findings_parallel(_config(walltime=60), wt, None, findings, state)

    assert processed == []  # nothing processed — walltime check fires first


def test_process_findings_parallel_single_worker_stops_on_graceful_flag(tmp_path, monkeypatch):
    """If a peer sets graceful_stop_requested, the serial single-worker driver
    must stop before the next finding."""
    processed: list[str] = []
    def fake_run_one(config, wt, staging_wt, finding, state):
        processed.append(finding.id)
        state.graceful_stop_requested = True  # trips on first call
    monkeypatch.setattr(run_mod, "_run_one_finding", fake_run_one)

    findings = [_finding("a", "F-1"), _finding("a", "F-2"), _finding("a", "F-3")]
    state = _state(tmp_path)
    wt = Worktree(path=tmp_path, branch="main", main_repo=tmp_path)
    run_mod._process_findings_parallel(_config(), wt, None, findings, state)

    assert processed == ["F-1"]  # stop flag caught before F-2


def test_evaluate_tracks_preserves_partial_findings_on_rate_limit(tmp_path, monkeypatch):
    """Success criterion: evaluator findings from tracks that DID succeed are still
    written to review.md, not thrown away when a peer track graceful-stops."""
    def fake_evaluate(config, track, wt, cycle, run_dir, sessions=None, resume_session_id=None):
        if track == "a":
            return [_finding("a", "F-a-1"), _finding("a", "F-a-2")]
        if track == "b":
            raise RateLimitHit(resets_at=1776855600, rate_limit_type="five_hour")
        if track == "c":
            return [_finding("c", "F-c-1")]
    monkeypatch.setattr(run_mod.engine, "evaluate", fake_evaluate)

    state = _state(tmp_path)
    # _evaluate_tracks now calls _viable_resume_id(record, wt.path) per track, so wt
    # must have a real .path attribute (previously any object sufficed).
    wt = Worktree(path=tmp_path, branch="main", main_repo=tmp_path)
    results = run_mod._evaluate_tracks(_config(), wt, 1, tmp_path, state)

    assert state.graceful_stop_requested is True
    assert "five_hour" in state.graceful_stop_reason or "evaluator" in state.graceful_stop_reason
    # Track a + c findings preserved, b's raised → empty list.
    assert [f.id for f in results["a"]] == ["F-a-1", "F-a-2"]
    assert results["b"] == []
    assert [f.id for f in results["c"]] == ["F-c-1"]


def test_commit_lock_serializes_concurrent_commits(tmp_path):
    """Two threads holding state.commit_lock + calling _commit_fix on a real git repo
    must not hit .git/index.lock races. The lock itself guarantees serialization.

    Under the per-worker isolation model, each finding runs on its own
    worktree, so contention like this shouldn't happen in production. This
    test remains as a regression guard against accidental removal of the
    lock — it still proves serialized access doesn't race the git index."""
    repo = _init_repo(tmp_path)
    wt = Worktree(path=repo, branch="main", main_repo=repo)
    pre = _head(repo)

    from harness.sessions import SessionsFile
    state = run_mod.RunState(
        run_dir=tmp_path, staging_branch="main", token="t", ts="t", pre_dirty=set(),
        sessions=SessionsFile(tmp_path / "sessions.json"),
    )
    results: list[object] = []
    errors: list[Exception] = []

    def worker(track: str, fid: str, file_rel: str) -> None:
        try:
            with state.staging_lock:
                # Write the worker's file UNDER the lock so concurrent
                # commits can't race on staging. The previous test wrote
                # both files before the lock, which no longer makes sense
                # under "commit all dirty files" semantics.
                (repo / file_rel).parent.mkdir(parents=True, exist_ok=True)
                (repo / file_rel).write_text(f"{track}\n", encoding="utf-8")
                c = run_mod._commit_fix(wt, _finding(track, fid), pre)
                results.append(c)
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    t1 = threading.Thread(target=worker, args=("a", "F-A", "cli/freddy/a.py"))
    t2 = threading.Thread(target=worker, args=("b", "F-B", "src/api/b.py"))
    t1.start(); t2.start(); t1.join(); t2.join()

    assert errors == [], f"workers errored: {errors}"
    assert all(r is not None for r in results)
    log_out = subprocess.check_output(
        ["git", "-C", str(repo), "log", "--format=%s", "-n", "3"], text=True,
    )
    assert "F-A" in log_out and "F-B" in log_out


# ── Post-fix safety probes: agent commit bypass, stash orphan ──────────────


def _branch_off_main(repo: Path, branch: str = "harness/run-test") -> None:
    """Create + check out a branch from current HEAD so main..HEAD scoping works."""
    subprocess.run(["git", "-C", str(repo), "checkout", "-qb", branch], check=True)


def test_copy_inventory_if_present_copies_when_source_exists(tmp_path):
    wt = tmp_path / "wt"
    (wt / "harness").mkdir(parents=True)
    (wt / "harness" / "INVENTORY.md").write_text("# inventory\n", encoding="utf-8")
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    run_mod._copy_inventory_if_present(wt, run_dir)
    dst = run_dir / "inventory.md"
    assert dst.is_file()
    assert "inventory" in dst.read_text(encoding="utf-8")


def test_copy_inventory_if_present_warns_when_missing(tmp_path, caplog):
    """If INVENTORY.md is missing (resume against pre-5dc860b branch), DON'T crash —
    just log a warning. Smoke 20260422-190507 resume crashed on this exact issue."""
    wt = tmp_path / "wt"
    (wt / "harness").mkdir(parents=True)  # dir exists but no INVENTORY.md
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    with caplog.at_level("WARNING", logger="harness.run"):
        run_mod._copy_inventory_if_present(wt, run_dir)
    assert "inventory source missing" in caplog.text
    assert not (run_dir / "inventory.md").exists()


def test_detect_agent_commit_returns_sha_when_head_advances_for_this_finding(tmp_path):
    """Newest commit subject contains THIS finding id → attributable bypass."""
    wt = _init_repo(tmp_path / "wt")
    pre = _head(wt)
    (wt / "cli/freddy/new.py").write_text("x\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(wt), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(wt), "commit", "-qm", "harness: fix F-a-1-1 — test"],
        check=True,
    )
    post = run_mod._detect_agent_commit(wt, pre, "F-a-1-1")
    assert post is not None and post != pre


def test_detect_agent_commit_returns_none_when_head_unchanged(tmp_path):
    wt = _init_repo(tmp_path / "wt")
    pre = _head(wt)
    assert run_mod._detect_agent_commit(wt, pre, "F-a-1-1") is None


def test_detect_agent_commit_returns_none_when_peer_track_committed(tmp_path):
    """Bug #15: HEAD advanced but newest commit subject references a DIFFERENT
    finding id (peer track's legitimate commit under parallel execution). Must
    NOT be treated as this track's bypass — else the rollback path would wipe
    the peer's legitimate commit. Smoke 20260422-224908 lost F-b-1-2 this way."""
    wt = _init_repo(tmp_path / "wt")
    pre = _head(wt)
    # Simulate a peer track (F-b-1-1) legitimately committing during our fix:
    (wt / "src/api/peer.py").parent.mkdir(parents=True, exist_ok=True)
    (wt / "src/api/peer.py").write_text("peer\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(wt), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(wt), "commit", "-qm", "harness: fix F-b-1-1 — peer"],
        check=True,
    )
    # Our track is processing F-a-1-1. Peer's commit must NOT be flagged as ours.
    assert run_mod._detect_agent_commit(wt, pre, "F-a-1-1") is None


def test_pop_orphan_stash_recovers_left_behind_stash(tmp_path, caplog):
    """Agent ran `git stash` but didn't pop. Safety net should pop it + warn."""
    wt = _init_repo(tmp_path / "wt")
    # Create an uncommitted change, stash it (simulating agent's stash leak).
    (wt / "cli/freddy/seed.py").write_text("modified\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(wt), "stash"], check=True, capture_output=True)
    # Confirm stash is actually there.
    list_before = subprocess.check_output(
        ["git", "-C", str(wt), "stash", "list"], text=True,
    ).strip()
    assert list_before, "setup failed — no stash to pop"

    with caplog.at_level("WARNING", logger="harness.run"):
        run_mod._pop_orphan_stash(wt, "F-a-1-1")

    assert "stash entries" in caplog.text
    list_after = subprocess.check_output(
        ["git", "-C", str(wt), "stash", "list"], text=True,
    ).strip()
    assert not list_after, "stash should be popped"


def test_pop_orphan_stash_noop_when_clean(tmp_path, caplog):
    wt = _init_repo(tmp_path / "wt")
    with caplog.at_level("WARNING", logger="harness.run"):
        run_mod._pop_orphan_stash(wt, "F-a-1-1")
    assert "stash entries" not in caplog.text


def test_render_fixer_substitutes_worktree_and_includes_warning(tmp_path):
    """Fix 6: render_fixer now takes wt_path and substitutes {worktree} so the
    prompt can warn the agent that edits outside the worktree are detected as
    leaks. F-b-1-2's fixer in smoke 20260422-190507 attempted to Edit a main
    repo path — this prompt addition is the advisory nudge; safety.check_no_leak
    (widened in Fix 1) is the mechanical backstop."""
    from harness import prompts
    finding = _finding("b", "F-b-1-2")
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    wt_path = tmp_path / "wt" / "run-20260422-190507"
    wt_path.mkdir(parents=True)
    out = prompts.render_fixer(finding, run_dir, wt_path)
    rendered = out.read_text(encoding="utf-8")
    assert str(wt_path) in rendered
    assert "File paths MUST start with" in rendered


def test_reconstruct_commit_record_from_existing_commit(tmp_path):
    """Rebuilding state.commits from an on-disk commit preserves finding_id,
    summary, files, reproduction, and adjacent_checked from the verdict file."""
    wt = _init_repo(tmp_path / "wt")
    _branch_off_main(wt)
    # Land a fix commit on the branch.
    (wt / "cli/freddy/fix.py").write_text("fixed\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(wt), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(wt), "commit", "-qm", "harness: fix F-a-1-1 — test"],
        check=True,
    )
    sha = _head(wt)
    # Write a verdict file that the reconstruction reads.
    run_dir = tmp_path / "run"
    verdict_dir = run_dir / "verdicts" / "a"
    verdict_dir.mkdir(parents=True)
    (verdict_dir / "F-a-1-1.yaml").write_text(
        "verdict: verified\nreason: ok\nadjacent_checked:\n  - foo\n  - bar\n",
        encoding="utf-8",
    )
    finding = _finding("a", "F-a-1-1")
    record = run_mod._reconstruct_commit_record(wt, finding, sha, run_dir)
    assert record.sha == sha
    assert record.finding_id == "F-a-1-1"
    assert record.track == "a"
    assert "cli/freddy/fix.py" in record.files
    assert record.adjacent_checked == ("foo", "bar")


# ── Fix #14: JSONL-existence guards on resume ─────────────────────────────


def test_viable_resume_id_returns_none_when_record_missing(tmp_path):
    assert run_mod._viable_resume_id(None, tmp_path) is None


def test_viable_resume_id_returns_none_when_not_running(tmp_path):
    from harness.sessions import SessionRecord
    r = SessionRecord(
        agent_key="fix-F-a-1-1", session_id="abc", engine="claude",
        status="complete", started_at=0.0,
    )
    assert run_mod._viable_resume_id(r, tmp_path) is None


def test_viable_resume_id_returns_none_when_jsonl_missing(tmp_path, caplog):
    """Overnight smoke 20260422-224908: sessions.json said status=running but the
    claude CLI never created a JSONL because it silent-hung. Resume must fall
    back to fresh instead of passing a dead session_id to --resume."""
    from harness.sessions import SessionRecord
    r = SessionRecord(
        agent_key="fix-F-a-1-1",
        session_id="3f6e5c85-d3d4-4634-bdc9-987fa30db27a",
        engine="claude", status="running", started_at=0.0,
    )
    # tmp_path has no corresponding ~/.claude/projects/<encoded-tmp_path>/<sid>.jsonl
    with caplog.at_level("INFO", logger="harness.run"):
        result = run_mod._viable_resume_id(r, tmp_path)
    assert result is None
    assert "no local JSONL" in caplog.text


def test_post_cycle_failure_still_calls_print_summary(tmp_path, monkeypatch):
    """Fix #12: overnight smoke 20260422-224908 crashed inside post-cycle
    restart_backend, which skipped _write_outputs / _push_and_pr / _print_summary.
    The run returned exit 4 with no summary and no resume command. Wrap each
    post-cycle step so _print_summary ALWAYS runs, even when restart_backend
    explodes."""
    import harness.run as run_mod
    from harness import worktree as worktree_mod
    from harness.config import Config
    from harness.findings import Finding
    from harness.sessions import SessionsFile
    from harness.worktree import Worktree

    repo = _init_repo(tmp_path / "repo")
    subprocess.run(["git", "-C", str(repo), "checkout", "-qb", "harness/test"], check=True)
    wt = Worktree(path=repo, branch="harness/test", main_repo=repo)

    run_dir = tmp_path / "run"
    run_dir.mkdir()
    sessions = SessionsFile(run_dir / "sessions.json")
    state = run_mod.RunState(
        run_dir=run_dir, staging_branch="harness/test", token="t", ts="t",
        pre_dirty=set(), sessions=sessions,
    )
    state.all_findings.append(Finding(
        id="F-x-1-1", track="a", category="crash", confidence="low",
        summary="x", evidence="", reproduction="", files=(),
    ))

    # Stub: preflight pass, inventory pass, smoke pass, cycle returns "graceful-stop",
    # restart_backend raises (simulating backend-died overnight), tip_smoke never
    # reached, _write_outputs OK, push/PR skipped (no commits), _print_summary MUST run.
    monkeypatch.setattr(run_mod, "_copy_inventory_if_present", lambda *a, **k: None)
    monkeypatch.setattr(run_mod.smoke, "check", lambda *a, **k: None)
    monkeypatch.setattr(run_mod, "_cycle_loop", lambda *a, **k: "graceful-stop")
    def boom(*a, **k):
        raise RuntimeError("simulated backend died overnight")
    monkeypatch.setattr(worktree_mod, "restart_backend", boom)
    monkeypatch.setattr(run_mod.preflight, "check_all", lambda cfg: "tok")
    monkeypatch.setattr(worktree_mod, "attach_to_branch", lambda branch, cfg: wt)
    monkeypatch.setattr(worktree_mod, "create", lambda ts, cfg: wt)
    monkeypatch.setattr(worktree_mod, "cleanup", lambda w: None)

    summary_called = {"n": 0}
    def fake_summary(*a, **k):
        summary_called["n"] += 1
    monkeypatch.setattr(run_mod, "_print_summary", fake_summary)

    config = Config(
        resume_branch="harness/test",  # skip worktree.create path
        staging_root=tmp_path / "staging",
        # Pin single-worker mode so run() doesn't try to git-worktree-add N extra
        # worktrees off a non-existent branch. Post-cycle-failure behavior is
        # orthogonal to worker-pool scaling.
        max_workers=1,
    )
    # resume_branch path uses _run_dir_for_branch → harness/test → tmp_path/staging/run-test
    # We want our existing run_dir. Intercept _run_dir_for_branch:
    monkeypatch.setattr(run_mod, "_run_dir_for_branch", lambda b, sr: run_dir)

    rc = run_mod.run(config)

    assert summary_called["n"] == 1, "_print_summary must run even after restart_backend failure"
    assert rc == 0, "run() returns 0 on graceful-stop even when post-cycle step fails"


def test_viable_resume_id_returns_sid_when_jsonl_exists(tmp_path, monkeypatch):
    """Happy path: record is 'running' AND the JSONL exists → resume with it."""
    from harness.sessions import SessionRecord
    from harness import sessions as sessions_mod

    sid = "deadbeef-1234-5678-9abc-def012345678"
    fake_home = tmp_path / "fake-home"
    fake_home.mkdir()
    monkeypatch.setattr(sessions_mod.Path, "home", staticmethod(lambda: fake_home))

    wt_path = tmp_path / "wt"
    wt_path.mkdir()
    jsonl = sessions_mod.claude_session_jsonl(wt_path, sid)
    jsonl.parent.mkdir(parents=True)
    jsonl.write_text("{}\n", encoding="utf-8")

    r = SessionRecord(
        agent_key="fix-F-a-1-1", session_id=sid, engine="claude",
        status="running", started_at=0.0,
    )
    assert run_mod._viable_resume_id(r, wt_path) == sid
