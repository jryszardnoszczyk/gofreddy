"""Tests for harness.worktree — snapshot, change detection, protected files, process tracker."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from harness.worktree import (
    ProcessTracker,
    _list_protected_files,
    detect_backend_changes,
    snapshot_backend_tree,
    snapshot_protected_files,
    verify_and_restore_protected_files,
)

# The repo root is two levels up from tests/harness/
REPO_ROOT = Path(__file__).resolve().parent.parent.parent


# ---------------------------------------------------------------------------
# snapshot_backend_tree
# ---------------------------------------------------------------------------


class TestSnapshotBackendTree:
    """snapshot_backend_tree on the real repo src/ directory."""

    def test_excludes_pycache(self):
        """No __pycache__ entries should appear in the snapshot."""
        snap = snapshot_backend_tree(REPO_ROOT)
        assert snap, "Snapshot should not be empty (src/ has files)"
        pycache_entries = [k for k in snap if "__pycache__" in k]
        assert pycache_entries == [], f"Found __pycache__ entries: {pycache_entries}"

    def test_all_paths_start_with_known_prefix(self):
        """Every key should be a relative path starting with 'src/' or 'cli/freddy/'."""
        snap = snapshot_backend_tree(REPO_ROOT)
        for key in snap:
            assert key.startswith("src/") or key.startswith("cli/freddy/"), (
                f"Path does not start with src/ or cli/freddy/: {key}"
            )

    def test_hashes_are_hex(self):
        """Every value should be a 40-char hex SHA-1 hash."""
        snap = snapshot_backend_tree(REPO_ROOT)
        for key, val in list(snap.items())[:10]:  # spot-check first 10
            assert len(val) == 40, f"Hash wrong length for {key}: {val}"
            assert all(c in "0123456789abcdef" for c in val), f"Non-hex hash for {key}"

    def test_empty_when_no_src_dir(self, tmp_path):
        """Returns empty dict when src/ does not exist."""
        assert snapshot_backend_tree(tmp_path) == {}


# ---------------------------------------------------------------------------
# detect_backend_changes
# ---------------------------------------------------------------------------


class TestDetectBackendChanges:
    """Diff two snapshots to find changed files."""

    def test_no_changes(self):
        snap = {"src/a.py": "aaa", "src/b.py": "bbb"}
        assert detect_backend_changes(snap, snap.copy()) == []

    def test_one_file_changed(self):
        before = {"src/a.py": "aaa", "src/b.py": "bbb"}
        after = {"src/a.py": "aaa", "src/b.py": "ccc"}
        result = detect_backend_changes(before, after)
        assert result == ["src/b.py"]

    def test_file_added(self):
        before = {"src/a.py": "aaa"}
        after = {"src/a.py": "aaa", "src/new.py": "nnn"}
        result = detect_backend_changes(before, after)
        assert result == ["src/new.py"]

    def test_file_deleted(self):
        before = {"src/a.py": "aaa", "src/gone.py": "ggg"}
        after = {"src/a.py": "aaa"}
        result = detect_backend_changes(before, after)
        assert result == ["src/gone.py"]

    def test_mixed_changes(self):
        before = {"src/a.py": "aaa", "src/b.py": "bbb", "src/c.py": "ccc"}
        after = {"src/a.py": "xxx", "src/c.py": "ccc", "src/d.py": "ddd"}
        result = detect_backend_changes(before, after)
        # a.py modified, b.py deleted, d.py added
        assert sorted(result) == ["src/a.py", "src/b.py", "src/d.py"]

    def test_both_empty(self):
        assert detect_backend_changes({}, {}) == []


# ---------------------------------------------------------------------------
# snapshot_protected_files
# ---------------------------------------------------------------------------


class TestSnapshotProtectedFiles:
    """snapshot_protected_files captures harness infra for the safety net."""

    def test_includes_harness_py_files(self, tmp_path):
        """Backup should contain harness/*.py files."""
        # Set up a fake repo with harness files
        repo = tmp_path / "repo"
        repo.mkdir()
        harness_dir = repo / "harness"
        harness_dir.mkdir()
        (harness_dir / "config.py").write_text("# config")
        (harness_dir / "worktree.py").write_text("# worktree")
        # runs/ should be excluded
        runs_dir = harness_dir / "runs"
        runs_dir.mkdir()
        (runs_dir / "artifact.md").write_text("# artifact")

        run_dir = tmp_path / "run"
        run_dir.mkdir()

        backup = snapshot_protected_files(repo, run_dir, 1)

        assert backup == run_dir / ".harness-backup-1"
        assert (backup / "harness" / "config.py").exists()
        assert (backup / "harness" / "worktree.py").exists()
        # runs/ excluded
        assert not (backup / "harness" / "runs" / "artifact.md").exists()

    def test_includes_scripts(self, tmp_path):
        """Backup should include setup_db.sql and seed_local.py."""
        repo = tmp_path / "repo"
        repo.mkdir()
        scripts_dir = repo / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "setup_db.sql").write_text("-- sql")
        (scripts_dir / "seed_local.py").write_text("# seed")

        run_dir = tmp_path / "run"
        run_dir.mkdir()

        backup = snapshot_protected_files(repo, run_dir, 2)

        assert (backup / "scripts" / "setup_db.sql").exists()
        assert (backup / "scripts" / "seed_local.py").exists()

    def test_includes_tests_harness(self, tmp_path):
        """Backup should include tests/harness/ files."""
        repo = tmp_path / "repo"
        repo.mkdir()
        th = repo / "tests" / "harness"
        th.mkdir(parents=True)
        (th / "test_worktree.py").write_text("# test")

        run_dir = tmp_path / "run"
        run_dir.mkdir()

        backup = snapshot_protected_files(repo, run_dir, 1)
        assert (backup / "tests" / "harness" / "test_worktree.py").exists()

    def test_on_real_repo(self):
        """Snapshot the real repo -- should include harness/*.py files."""
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run"
            run_dir.mkdir()
            backup = snapshot_protected_files(REPO_ROOT, run_dir, 1)

            # Should have at least config.py and worktree.py
            assert (backup / "harness" / "config.py").exists()
            assert (backup / "harness" / "worktree.py").exists()
            # Should NOT have runs/ artifacts
            runs_backup = backup / "harness" / "runs"
            if runs_backup.exists():
                assert list(runs_backup.rglob("*")) == [], (
                    "runs/ artifacts should be excluded"
                )


# ---------------------------------------------------------------------------
# verify_and_restore_protected_files
# ---------------------------------------------------------------------------


class TestVerifyAndRestoreProtectedFiles:
    """Safety net: detect and revert fixer tampering with harness files."""

    def test_restores_modified_file(self, tmp_path):
        """A modified harness file should be restored from backup."""
        repo = tmp_path / "repo"
        repo.mkdir()
        harness_dir = repo / "harness"
        harness_dir.mkdir()
        target = harness_dir / "config.py"
        target.write_text("original content")

        # Create backup
        run_dir = tmp_path / "run"
        run_dir.mkdir()
        backup = snapshot_protected_files(repo, run_dir, 1)

        # Simulate fixer modifying the file
        target.write_text("tampered content")

        violations = verify_and_restore_protected_files(repo, backup)
        assert violations == 1
        assert target.read_text() == "original content"

    def test_restores_deleted_file(self, tmp_path):
        """A deleted harness file should be restored from backup."""
        repo = tmp_path / "repo"
        repo.mkdir()
        harness_dir = repo / "harness"
        harness_dir.mkdir()
        target = harness_dir / "config.py"
        target.write_text("original content")

        run_dir = tmp_path / "run"
        run_dir.mkdir()
        backup = snapshot_protected_files(repo, run_dir, 1)

        # Simulate fixer deleting the file
        target.unlink()

        violations = verify_and_restore_protected_files(repo, backup)
        assert violations == 1
        assert target.exists()
        assert target.read_text() == "original content"

    def test_removes_added_file(self, tmp_path):
        """A file added by the fixer to harness/ should be removed."""
        repo = tmp_path / "repo"
        repo.mkdir()
        harness_dir = repo / "harness"
        harness_dir.mkdir()
        (harness_dir / "config.py").write_text("original")

        run_dir = tmp_path / "run"
        run_dir.mkdir()
        backup = snapshot_protected_files(repo, run_dir, 1)

        # Simulate fixer adding a new file
        added = harness_dir / "sneaky.py"
        added.write_text("injected code")

        violations = verify_and_restore_protected_files(repo, backup)
        assert violations == 1
        assert not added.exists()

    def test_no_violations_when_unchanged(self, tmp_path):
        """Zero violations when nothing was modified."""
        repo = tmp_path / "repo"
        repo.mkdir()
        harness_dir = repo / "harness"
        harness_dir.mkdir()
        (harness_dir / "config.py").write_text("original")

        run_dir = tmp_path / "run"
        run_dir.mkdir()
        backup = snapshot_protected_files(repo, run_dir, 1)

        violations = verify_and_restore_protected_files(repo, backup)
        assert violations == 0

    def test_no_backup_dir(self, tmp_path):
        """Returns 0 when backup directory does not exist."""
        repo = tmp_path / "repo"
        repo.mkdir()
        fake_backup = tmp_path / "nonexistent"
        assert verify_and_restore_protected_files(repo, fake_backup) == 0


# ---------------------------------------------------------------------------
# ProcessTracker
# ---------------------------------------------------------------------------


class TestProcessTracker:
    """ProcessTracker registers PIDs and cleans them up."""

    def test_register_and_cleanup_kills_process(self):
        """A registered process should be killed on cleanup."""
        # Start a long-running subprocess
        proc = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(300)"],
            start_new_session=True,
        )
        assert proc.poll() is None, "Process should be running"

        tracker = ProcessTracker()
        tracker.register(proc.pid)
        tracker.cleanup()

        # Process should be dead now (give it a moment)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            pytest.fail("Process was not killed by tracker")

    def test_register_process_group_and_cleanup(self):
        """A registered process group leader should be killed on cleanup."""
        proc = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(300)"],
            start_new_session=True,
        )
        assert proc.poll() is None

        tracker = ProcessTracker()
        tracker.register(proc.pid, is_process_group=True)
        tracker.cleanup()

        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            pytest.fail("Process group was not killed by tracker")

    def test_cleanup_idempotent(self):
        """Calling cleanup() twice should not raise."""
        tracker = ProcessTracker()
        tracker.cleanup()
        tracker.cleanup()  # Should be a no-op

    def test_context_manager(self):
        """ProcessTracker as a context manager installs and cleans up."""
        with ProcessTracker() as tracker:
            proc = subprocess.Popen(
                [sys.executable, "-c", "import time; time.sleep(300)"],
                start_new_session=True,
            )
            tracker.register(proc.pid)

        # After context exit, process should be dead
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            pytest.fail("Process not killed after context exit")

    def test_install_sets_signal_handlers(self):
        """install() should set SIGINT and SIGTERM handlers."""
        tracker = ProcessTracker()
        old_int = signal.getsignal(signal.SIGINT)
        old_term = signal.getsignal(signal.SIGTERM)

        try:
            tracker.install()
            assert signal.getsignal(signal.SIGINT) == tracker._handle_signal
            assert signal.getsignal(signal.SIGTERM) == tracker._handle_signal
        finally:
            # Restore original handlers
            signal.signal(signal.SIGINT, old_int)
            signal.signal(signal.SIGTERM, old_term)
            tracker._cleaned_up = True  # prevent double-cleanup

    def test_already_dead_process_no_error(self):
        """Cleaning up an already-dead PID should not raise."""
        proc = subprocess.Popen(
            [sys.executable, "-c", "pass"],
        )
        proc.wait()  # Let it finish

        tracker = ProcessTracker()
        tracker.register(proc.pid)
        tracker.cleanup()  # Should not raise
