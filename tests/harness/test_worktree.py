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


def test_rollback_preserves_symlinks(main_repo, tmp_path, monkeypatch):
    config = _make_config(tmp_path)
    monkeypatch.setattr(wt_mod, "restart_backend", lambda wt, cfg: None)

    wt = wt_mod.create("20260101-000001", config)
    pre_sha = subprocess.check_output(["git", "-C", str(wt.path), "rev-parse", "HEAD"], text=True).strip()
    try:
        (wt.path / "untracked.txt").write_text("u\n", encoding="utf-8")
        (wt.path / "clients" / "keepme").write_text("k\n", encoding="utf-8")
        assert (wt.path / ".venv").is_symlink()

        wt_mod.rollback_to(wt, pre_sha)

        assert not (wt.path / "untracked.txt").exists()
        assert (wt.path / ".venv").is_symlink()
        assert (wt.path / "node_modules").is_symlink()
        assert (wt.path / "clients" / "keepme").exists()
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
