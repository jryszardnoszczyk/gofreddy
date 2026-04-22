"""Tests for harness.worktree — create/rollback/cleanup state paths."""
from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

import pytest

from harness import worktree as wt_mod
from harness.config import Config


@pytest.fixture()
def main_repo(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@test"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "t"], check=True)
    (repo / "a.txt").write_text("x\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "seed"], check=True)
    (repo / ".venv").mkdir()
    (repo / ".venv" / "bin").mkdir()
    (repo / ".venv" / "bin" / "marker").write_text("v\n", encoding="utf-8")
    (repo / "node_modules").mkdir()
    monkeypatch.chdir(repo)
    return repo


def _make_config(tmp_path: Path) -> Config:
    return Config(
        backend_cmd="true",
        backend_url="http://127.0.0.1:8000",
        staging_root=tmp_path / "runs",
    )


def test_create_makes_symlinks_and_mode(main_repo, tmp_path, monkeypatch):
    config = _make_config(tmp_path)
    monkeypatch.setattr(wt_mod, "restart_backend", lambda wt, cfg: None)

    wt = wt_mod.create("20260101-000000", config)
    try:
        assert wt.path.is_dir()
        assert (wt.path / ".venv").is_symlink()
        assert (wt.path / "node_modules").is_symlink()
        assert (wt.path / "clients").is_dir()
        assert not (wt.path / "clients").is_symlink()
        mode = stat.S_IMODE(os.stat(wt.path).st_mode)
        assert mode == 0o700
    finally:
        wt_mod.cleanup(wt)


def test_cleanup_removes_worktree_and_branch(main_repo, tmp_path, monkeypatch):
    config = _make_config(tmp_path)
    monkeypatch.setattr(wt_mod, "restart_backend", lambda wt, cfg: None)

    wt = wt_mod.create("20260101-000002", config)
    wt_path = wt.path
    branch = wt.branch

    wt_mod.cleanup(wt)

    assert not wt_path.exists()
    result = subprocess.run(
        ["git", "-C", str(main_repo), "branch", "--list", branch],
        capture_output=True, text=True, check=True,
    )
    assert result.stdout.strip() == ""


def _seed_repo_with_all_track_dirs(repo: Path) -> None:
    """Set up a repo where cli/freddy/, src/api/, and frontend/ are all tracked,
    so new files in them show as specific paths in git status (not as dir-level ??)."""
    for rel in ("cli/freddy/seed.py", "src/api/seed.py", "frontend/seed.js"):
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("seed\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "seed-dirs"], check=True)


def test_rollback_track_scope_leaves_peer_tracks_intact(main_repo, tmp_path, monkeypatch):
    """THE blocking test for Bug #4: under parallel fixers, track A's rollback
    must NOT touch tracks B and C's in-flight working-tree edits."""
    config = _make_config(tmp_path)
    monkeypatch.setattr(wt_mod, "restart_backend", lambda wt, cfg: None)

    wt = wt_mod.create("20260101-000003", config)
    _seed_repo_with_all_track_dirs(wt.path)
    try:
        # Track A (cli/) — will be rolled back
        (wt.path / "cli" / "freddy" / "a_new.py").write_text("a\n", encoding="utf-8")
        (wt.path / "cli" / "freddy" / "seed.py").write_text("modified-A\n", encoding="utf-8")
        # Track B (src/) — peer, must remain intact
        (wt.path / "src" / "api" / "b_new.py").write_text("b\n", encoding="utf-8")
        (wt.path / "src" / "api" / "seed.py").write_text("modified-B\n", encoding="utf-8")
        # Track C (frontend/) — peer, must remain intact
        (wt.path / "frontend" / "c_new.js").write_text("c\n", encoding="utf-8")
        (wt.path / "frontend" / "seed.js").write_text("modified-C\n", encoding="utf-8")

        wt_mod.rollback_track_scope(wt, "a")

        # A's edits are gone:
        assert not (wt.path / "cli" / "freddy" / "a_new.py").exists()
        assert (wt.path / "cli" / "freddy" / "seed.py").read_text() == "seed\n"
        # B's edits intact:
        assert (wt.path / "src" / "api" / "b_new.py").exists()
        assert (wt.path / "src" / "api" / "seed.py").read_text() == "modified-B\n"
        # C's edits intact:
        assert (wt.path / "frontend" / "c_new.js").exists()
        assert (wt.path / "frontend" / "seed.js").read_text() == "modified-C\n"
    finally:
        wt_mod.cleanup(wt)


def test_attach_to_branch_reuses_existing_worktree(main_repo, tmp_path, monkeypatch):
    """Resume: attach_to_branch reconnects to a worktree created by an earlier run."""
    config = _make_config(tmp_path)
    monkeypatch.setattr(wt_mod, "restart_backend", lambda wt, cfg: None)

    wt = wt_mod.create("20260101-000010", config)
    branch = wt.branch
    wt_path = wt.path
    # Simulate the earlier run exiting with --keep-worktree (leaving dir + branch).
    # Clear _LIVE so the follow-up attach is treated as a fresh bootstrap.
    wt_mod._LIVE.clear()
    wt2 = wt_mod.attach_to_branch(branch, config)
    try:
        assert wt2.branch == branch
        assert wt2.path == wt_path
        # Symlinks still wired
        assert (wt2.path / ".venv").is_symlink()
    finally:
        wt_mod.cleanup(wt2)


def test_attach_to_branch_missing_raises(main_repo, tmp_path, monkeypatch):
    config = _make_config(tmp_path)
    monkeypatch.setattr(wt_mod, "restart_backend", lambda wt, cfg: None)
    with pytest.raises(RuntimeError, match="resume branch not found"):
        wt_mod.attach_to_branch("harness/run-nope", config)


def test_rollback_track_scope_raises_on_git_status_failure(main_repo, tmp_path, monkeypatch):
    """Silent return would leave the worktree dirty; next _commit_fix could stage stale edits.
    Now rollback_track_scope raises so the worker's generic-exception handler logs + moves on."""
    config = _make_config(tmp_path)
    monkeypatch.setattr(wt_mod, "restart_backend", lambda wt, cfg: None)

    wt = wt_mod.create("20260101-000005", config)
    _seed_repo_with_all_track_dirs(wt.path)
    try:
        def failing_run(cmd, **kwargs):
            class R:
                returncode = 128
                stdout = ""
                stderr = "fatal: not a git repository"
            return R()
        monkeypatch.setattr(wt_mod.subprocess, "run", failing_run)

        with pytest.raises(RuntimeError, match="git status failed"):
            wt_mod.rollback_track_scope(wt, "a")
    finally:
        monkeypatch.undo()
        wt_mod.cleanup(wt)


def test_rollback_track_scope_ignores_harness_artifacts(main_repo, tmp_path, monkeypatch):
    """backend.log and similar harness artifacts must survive a scoped rollback."""
    config = _make_config(tmp_path)
    monkeypatch.setattr(wt_mod, "restart_backend", lambda wt, cfg: None)

    wt = wt_mod.create("20260101-000004", config)
    _seed_repo_with_all_track_dirs(wt.path)
    try:
        (wt.path / "backend.log").write_text("log\n", encoding="utf-8")
        (wt.path / "cli" / "freddy" / "edited.py").write_text("fix\n", encoding="utf-8")

        wt_mod.rollback_track_scope(wt, "a")

        assert (wt.path / "backend.log").exists()
        assert not (wt.path / "cli" / "freddy" / "edited.py").exists()
    finally:
        wt_mod.cleanup(wt)


def test_kill_port_sigterm_then_sigkill(monkeypatch):
    calls: list[tuple[int, int]] = []

    def fake_kill(pid, sig):
        calls.append((pid, int(sig)))

    monkeypatch.setattr(wt_mod.os, "kill", fake_kill)
    monkeypatch.setattr(wt_mod.subprocess, "check_output", lambda *a, **k: "1234\n")
    monkeypatch.setattr(wt_mod.time, "sleep", lambda _: None)

    wt_mod._kill_port(8000)
    signals = [s for _, s in calls]
    assert 15 in signals  # SIGTERM
    assert 9 in signals  # SIGKILL
    assert signals.index(15) < signals.index(9)
