"""Tests for harness.safety — scope allowlist + leak detection."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from harness.safety import SCOPE_ALLOWLIST, check_no_leak, check_scope, snapshot_dirty


def _init_repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q", "-b", "main", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.email", "t@test"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "t"], check=True)
    (tmp_path / "seed.txt").write_text("seed\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-qm", "seed"], check=True)
    return tmp_path


def _commit_file(repo: Path, rel: str, body: str = "x") -> str:
    target = repo / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", rel], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", f"touch {rel}"], check=True)
    return subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()


def _pre_head(repo: Path) -> str:
    return subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()


@pytest.mark.parametrize("track,path", [
    ("a", "cli/freddy/commands/client.py"),
    ("a", "pyproject.toml"),
    ("b", "src/api/main.py"),
    ("b", "autoresearch/evolve.py"),
    ("c", "frontend/package.json"),
    ("c", "frontend/vite.config.ts"),
])
def test_check_scope_allows_matching_paths(tmp_path, track, path):
    repo = _init_repo(tmp_path)
    pre = _pre_head(repo)
    _commit_file(repo, path)
    assert check_scope(repo, pre, track) is None


@pytest.mark.parametrize("track,path", [
    ("a", "tests/harness/test_run.py"),
    ("a", "harness/safety.py"),
    ("a", "src/api/main.py"),
    ("b", "cli/freddy/main.py"),
    ("b", "tests/unit/test_x.py"),
    ("c", "src/api/main.py"),
    ("c", "backend.log"),
])
def test_check_scope_flags_forbidden_paths(tmp_path, track, path):
    repo = _init_repo(tmp_path)
    pre = _pre_head(repo)
    _commit_file(repo, path)
    violations = check_scope(repo, pre, track)
    assert violations == [path]


def test_check_scope_returns_only_violations(tmp_path):
    repo = _init_repo(tmp_path)
    pre = _pre_head(repo)
    _commit_file(repo, "cli/freddy/x.py")
    _commit_file(repo, "harness/forbidden.py")
    violations = check_scope(repo, pre, "a")
    assert violations == ["harness/forbidden.py"]


def test_check_no_leak_clean_main_repo(tmp_path):
    repo = _init_repo(tmp_path)
    snapshot = snapshot_dirty(repo)
    assert check_no_leak(snapshot, main_repo=repo) is None


def test_check_no_leak_detects_new_dirty(tmp_path):
    repo = _init_repo(tmp_path)
    snapshot = snapshot_dirty(repo)
    (repo / "leaked.txt").write_text("leak\n", encoding="utf-8")
    leaks = check_no_leak(snapshot, main_repo=repo)
    assert leaks == ["leaked.txt"]


def test_check_no_leak_ignores_preexisting_dirty(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "already.txt").write_text("a\n", encoding="utf-8")
    snapshot = snapshot_dirty(repo)
    assert "already.txt" in snapshot
    assert check_no_leak(snapshot, main_repo=repo) is None


def test_scope_allowlist_has_three_tracks():
    assert set(SCOPE_ALLOWLIST) == {"a", "b", "c"}
