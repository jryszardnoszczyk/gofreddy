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


def test_commit_fix_stages_only_in_scope_files(tmp_path):
    """Bug #3: Under parallel, track A has peers' dirty files. _commit_fix must
    stage only A's allowlist-matching files so B/C's in-flight edits stay uncommitted."""
    repo = _init_repo(tmp_path)
    wt = Worktree(path=repo, branch="main", main_repo=repo)
    pre = _head(repo)

    # Track A's edit (in-scope)
    (repo / "cli" / "freddy" / "fix.py").write_text("def fix(): pass\n", encoding="utf-8")
    # Peer track B's in-flight edit (must NOT be committed by track A)
    (repo / "src" / "api" / "peer.py").write_text("peer work\n", encoding="utf-8")
    # Peer track C's in-flight edit
    (repo / "frontend" / "peer.js").write_text("peer work\n", encoding="utf-8")

    verdict = Verdict(verified=True, reason="ok", adjacent_checked=())
    commit = run_mod._commit_fix(wt, _finding("a"), pre, verdict)

    assert commit is not None
    assert commit.files == ("cli/freddy/fix.py",)
    # Post-commit: peer files are still dirty (uncommitted).
    status = subprocess.check_output(
        ["git", "-C", str(repo), "status", "--porcelain"], text=True,
    )
    assert "src/api/peer.py" in status
    assert "frontend/peer.js" in status
    assert "cli/freddy/fix.py" not in status


def test_commit_fix_skips_when_no_in_scope_changes(tmp_path):
    """If the fixer only touched peer-track files, there's nothing to commit for this track."""
    repo = _init_repo(tmp_path)
    wt = Worktree(path=repo, branch="main", main_repo=repo)
    pre = _head(repo)
    (repo / "src" / "api" / "peer.py").write_text("peer\n", encoding="utf-8")  # not A's scope

    verdict = Verdict(verified=True, reason="ok", adjacent_checked=())
    commit = run_mod._commit_fix(wt, _finding("a"), pre, verdict)

    assert commit is None
    assert _head(repo) == pre  # No new commit on HEAD


def _state(tmp_path: Path, walltime: int = 14400) -> run_mod.RunState:
    return run_mod.RunState(
        run_dir=tmp_path, staging_branch="harness/test", token="t", ts="20260101-000000",
        pre_dirty=set(),
    )


def _config(walltime: int = 14400) -> Config:
    return Config(max_walltime=walltime)


def test_process_track_queue_stops_on_graceful_stop_flag(tmp_path, monkeypatch):
    """If a peer track sets graceful_stop_requested, this track must stop before the next finding."""
    processed: list[str] = []
    def fake_process(config, wt, finding, state):
        processed.append(finding.id)
        state.graceful_stop_requested = True  # peer track tripped it
    monkeypatch.setattr(run_mod, "_process_finding", fake_process)

    queue = [_finding("a", "F-1"), _finding("a", "F-2"), _finding("a", "F-3")]
    state = _state(tmp_path)
    run_mod._process_track_queue(_config(), object(), queue, state)

    assert processed == ["F-1"]  # only the first was processed; stop flag caught before F-2


def test_process_track_queue_continues_on_generic_exception(tmp_path, monkeypatch):
    """A generic exception from one finding must not kill the track — worker moves to the next."""
    processed: list[str] = []
    rollback_calls: list[str] = []
    def fake_process(config, wt, finding, state):
        processed.append(finding.id)
        if finding.id == "F-2":
            raise RuntimeError("fixer blew up")
    monkeypatch.setattr(run_mod, "_process_finding", fake_process)
    monkeypatch.setattr(run_mod.worktree, "rollback_track_scope",
                        lambda wt, track: rollback_calls.append(track))

    queue = [_finding("a", "F-1"), _finding("a", "F-2"), _finding("a", "F-3")]
    state = _state(tmp_path)
    run_mod._process_track_queue(_config(), object(), queue, state)

    assert processed == ["F-1", "F-2", "F-3"]
    assert state.graceful_stop_requested is False
    assert rollback_calls == ["a"]  # rollback_track_scope fired for the failed finding


def test_process_track_queue_rate_limit_triggers_graceful_stop(tmp_path, monkeypatch):
    """RateLimitHit from one finding sets graceful_stop_requested, rolls back the
    partial finding's edits (success criterion: 'completes current finding cleanly'),
    and stops the track."""
    processed: list[str] = []
    rollback_calls: list[str] = []
    def fake_process(config, wt, finding, state):
        processed.append(finding.id)
        if finding.id == "F-2":
            raise RateLimitHit(resets_at=1776855600, rate_limit_type="five_hour")
    monkeypatch.setattr(run_mod, "_process_finding", fake_process)
    monkeypatch.setattr(run_mod.worktree, "rollback_track_scope",
                        lambda wt, track: rollback_calls.append(track))

    queue = [_finding("a", "F-1"), _finding("a", "F-2"), _finding("a", "F-3")]
    state = _state(tmp_path)
    run_mod._process_track_queue(_config(), object(), queue, state)

    assert processed == ["F-1", "F-2"]
    assert state.graceful_stop_requested is True
    assert "five_hour" in state.graceful_stop_reason
    # The partial fix state for F-2 is rolled back before the worker exits.
    assert rollback_calls == ["a"]


def test_process_track_queue_engine_exhausted_triggers_graceful_stop(tmp_path, monkeypatch):
    """EngineExhausted (transient retries used up) also triggers graceful stop + rollback."""
    processed: list[str] = []
    rollback_calls: list[str] = []
    def fake_process(config, wt, finding, state):
        processed.append(finding.id)
        raise EngineExhausted("out of retries")
    monkeypatch.setattr(run_mod, "_process_finding", fake_process)
    monkeypatch.setattr(run_mod.worktree, "rollback_track_scope",
                        lambda wt, track: rollback_calls.append(track))

    queue = [_finding("a", "F-1"), _finding("a", "F-2")]
    state = _state(tmp_path)
    run_mod._process_track_queue(_config(), object(), queue, state)

    assert processed == ["F-1"]
    assert state.graceful_stop_requested is True
    assert rollback_calls == ["a"]


def test_process_track_queue_respects_walltime(tmp_path, monkeypatch):
    """Walltime exceeded mid-track drops remaining findings."""
    processed: list[str] = []
    def fake_process(config, wt, finding, state):
        processed.append(finding.id)
    monkeypatch.setattr(run_mod, "_process_finding", fake_process)

    queue = [_finding("a", "F-1"), _finding("a", "F-2")]
    state = _state(tmp_path)
    state.start_ts = time.time() - 1_000_000  # simulate already past walltime
    run_mod._process_track_queue(_config(walltime=60), object(), queue, state)

    assert processed == []  # nothing processed — walltime check fires first


def test_evaluate_tracks_preserves_partial_findings_on_rate_limit(tmp_path, monkeypatch):
    """Success criterion: evaluator findings from tracks that DID succeed are still
    written to review.md, not thrown away when a peer track graceful-stops."""
    def fake_evaluate(config, track, wt, cycle, run_dir):
        if track == "a":
            return [_finding("a", "F-a-1"), _finding("a", "F-a-2")]
        if track == "b":
            raise RateLimitHit(resets_at=1776855600, rate_limit_type="five_hour")
        if track == "c":
            return [_finding("c", "F-c-1")]
    monkeypatch.setattr(run_mod.engine, "evaluate", fake_evaluate)

    state = _state(tmp_path)
    results = run_mod._evaluate_tracks(_config(), object(), 1, tmp_path, state)

    assert state.graceful_stop_requested is True
    assert "five_hour" in state.graceful_stop_reason or "evaluator" in state.graceful_stop_reason
    # Track a + c findings preserved, b's raised → empty list.
    assert [f.id for f in results["a"]] == ["F-a-1", "F-a-2"]
    assert results["b"] == []
    assert [f.id for f in results["c"]] == ["F-c-1"]


def test_commit_lock_serializes_concurrent_commits(tmp_path):
    """Two threads holding state.commit_lock + calling _commit_fix on a real git repo
    must not hit .git/index.lock races. The lock itself guarantees serialization."""
    repo = _init_repo(tmp_path)
    wt = Worktree(path=repo, branch="main", main_repo=repo)
    pre = _head(repo)

    # Each thread writes an in-scope file for its track and commits.
    (repo / "cli" / "freddy" / "a_work.py").write_text("a\n", encoding="utf-8")
    (repo / "src" / "api" / "b_work.py").write_text("b\n", encoding="utf-8")

    state = run_mod.RunState(
        run_dir=tmp_path, staging_branch="main", token="t", ts="t", pre_dirty=set(),
    )
    verdict = Verdict(verified=True, reason="ok", adjacent_checked=())
    results: list[object] = []

    def worker(track: str, fid: str) -> None:
        with state.commit_lock:
            c = run_mod._commit_fix(wt, _finding(track, fid), pre, verdict)
            results.append(c)

    t1 = threading.Thread(target=worker, args=("a", "F-A"))
    t2 = threading.Thread(target=worker, args=("b", "F-B"))
    t1.start(); t2.start(); t1.join(); t2.join()

    assert all(r is not None for r in results)
    # Both commits landed on HEAD:
    log_out = subprocess.check_output(
        ["git", "-C", str(repo), "log", "--format=%s", "-n", "3"], text=True,
    )
    assert "F-A" in log_out and "F-B" in log_out


