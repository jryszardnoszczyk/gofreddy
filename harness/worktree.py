"""Staging worktree, backend lifecycle, protected-file safety net, and process tracking."""

from __future__ import annotations

import atexit
import hashlib
import logging
import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Iterable

from harness.config import Config

log = logging.getLogger("harness.worktree")

# Health endpoint used by restart_backend to confirm the backend is alive.
HEALTH_ENDPOINT = "/health"


# ---------------------------------------------------------------------------
# Staging worktree management
# ---------------------------------------------------------------------------


def create_staging_worktree(
    config: Config,
    run_ts: str,
    *,
    repo_root: Path | None = None,
) -> tuple[Path, str]:
    """Create (or resume) a git worktree for a harness run.

    Returns ``(worktree_path, branch_name)``.

    * **Resume mode** (``config.resume_branch`` is set): check out the
      existing branch.
    * **Fresh mode**: create ``harness/run-<run_ts>`` from HEAD.

    Symlinks ``.venv``, ``node_modules``, and ``frontend/node_modules``
    from the main checkout so the worktree can run without reinstalling
    dependencies.
    """
    if repo_root is None:
        repo_root = Path(__file__).resolve().parent.parent

    staging_path = Path(config.staging_root) / f"harness-run-{run_ts}"

    if config.resume_branch:
        branch = config.resume_branch
        # Verify the branch exists
        result = subprocess.run(
            ["git", "rev-parse", "--verify", branch],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"HARNESS_RESUME_BRANCH={branch} does not exist"
            )
        log.info("Resuming from existing staging branch %s", branch)

        # Clean up stale worktree at the target path
        if staging_path.exists():
            _force_remove_worktree(staging_path, repo_root)

        result = subprocess.run(
            ["git", "worktree", "add", str(staging_path), branch],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to check out staging branch {branch} into worktree: "
                f"{result.stderr.strip()}"
            )

        # Count commits ahead of main for logging
        ahead_result = subprocess.run(
            ["git", "rev-list", "--count", f"main..{branch}"],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
        )
        ahead = ahead_result.stdout.strip() if ahead_result.returncode == 0 else "0"
        log.info(
            "Resumed staging worktree at %s (%s fixer commit(s) from prior run)",
            staging_path,
            ahead,
        )
    else:
        branch = f"harness/run-{run_ts}"

        # Clean up stale worktree from a prior crashed run
        if staging_path.exists():
            log.warning("Stale staging worktree at %s -- removing", staging_path)
            _force_remove_worktree(staging_path, repo_root)
            subprocess.run(
                ["git", "branch", "-D", branch],
                capture_output=True,
                text=True,
                cwd=str(repo_root),
            )

        log.info(
            "Creating staging worktree at %s (branch: %s)", staging_path, branch
        )
        result = subprocess.run(
            ["git", "worktree", "add", str(staging_path), "-b", branch, "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to create staging worktree: {result.stderr.strip()}"
            )
        log.info("Staging worktree ready: %s", staging_path)

    # Symlink dependencies from main checkout to avoid npm ci / venv creation
    _symlink_if_exists(repo_root / "node_modules", staging_path / "node_modules")
    _symlink_if_exists(
        repo_root / "frontend" / "node_modules",
        staging_path / "frontend" / "node_modules",
    )
    _symlink_if_exists(repo_root / ".venv", staging_path / ".venv")
    _symlink_if_exists(repo_root / "clients", staging_path / "clients")

    return staging_path, branch


def cleanup_staging_worktree(
    worktree_path: Path,
    branch_name: str,
    auto_cleanup: bool,
    *,
    repo_root: Path | None = None,
) -> None:
    """Remove a staging worktree and (optionally) delete the branch."""
    if repo_root is None:
        repo_root = Path(__file__).resolve().parent.parent

    if not worktree_path.exists():
        return

    log.info("Cleaning up staging worktree at %s", worktree_path)
    _force_remove_worktree(worktree_path, repo_root)

    if auto_cleanup and branch_name:
        subprocess.run(
            ["git", "branch", "-D", branch_name],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
        )
        log.info(
            "Staging branch %s deleted (auto_cleanup=true)", branch_name
        )


def _force_remove_worktree(worktree_path: Path, repo_root: Path) -> None:
    """``git worktree remove --force``, falling back to ``rm -rf``."""
    result = subprocess.run(
        ["git", "worktree", "remove", str(worktree_path), "--force"],
        capture_output=True,
        text=True,
        cwd=str(repo_root),
    )
    if result.returncode != 0 and worktree_path.exists():
        shutil.rmtree(worktree_path, ignore_errors=True)


def _symlink_if_exists(src: Path, dst: Path) -> None:
    """Create a symlink at *dst* pointing to *src* if *src* exists."""
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        # Remove existing symlink or dir if present
        if dst.is_symlink() or dst.exists():
            if dst.is_symlink():
                dst.unlink()
            else:
                shutil.rmtree(dst)
        dst.symlink_to(src)


# ---------------------------------------------------------------------------
# Backend snapshot / change detection
# ---------------------------------------------------------------------------


def snapshot_backend_tree(src_root: Path) -> dict[str, str]:
    """Walk ``src/`` and ``cli/freddy/`` under *src_root*, hash each file with SHA-1.

    Excludes ``__pycache__/`` directories.

    Returns ``{relative_path: hex_hash}`` where *relative_path* is
    relative to *src_root* (e.g. ``src/api/main.py``).
    """
    result: dict[str, str] = {}
    for subdir in ("src", "cli/freddy"):
        target = src_root / subdir
        if not target.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(target):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for fname in sorted(filenames):
                fpath = Path(dirpath) / fname
                try:
                    digest = hashlib.sha1(fpath.read_bytes()).hexdigest()  # noqa: S324
                except OSError:
                    continue
                rel = str(fpath.relative_to(src_root))
                result[rel] = digest

    return dict(sorted(result.items()))


def detect_backend_changes(
    before: dict[str, str],
    after: dict[str, str],
) -> list[str]:
    """Return file paths that differ between two backend snapshots.

    Covers modified, added, and deleted files.
    """
    changed: list[str] = []
    all_keys = sorted(set(before) | set(after))
    for key in all_keys:
        if key not in before:
            # Added
            changed.append(key)
        elif key not in after:
            # Deleted
            changed.append(key)
        elif before[key] != after[key]:
            # Modified
            changed.append(key)
    return changed


# ---------------------------------------------------------------------------
# Backend restart
# ---------------------------------------------------------------------------


def restart_backend(config: Config, worktree_path: Path) -> subprocess.Popen:
    """Kill the existing backend on *config.backend_port* and spawn a new one.

    Uses ``lsof -ti :<port>`` to find the current process, SIGTERM with
    5 s escalation to SIGKILL, then spawns the backend command from
    *worktree_path* as CWD.  Waits for the health endpoint before
    returning.

    Returns the ``Popen`` object for the new backend process.
    """
    _kill_backend_by_port(config.backend_port)

    # Spawn new backend. Prepend the worktree's .venv/bin to PATH so a bare
    # `uvicorn` (or any project entry point) resolves without the operator
    # having to activate the venv.
    env = os.environ.copy()
    venv_bin = Path(worktree_path) / ".venv" / "bin"
    if venv_bin.exists():
        env["PATH"] = f"{venv_bin}{os.pathsep}{env.get('PATH', '')}"

    log.info(
        "Restarting backend in %s (cmd=%s, PATH head=%s)",
        worktree_path, config.backend_cmd, env.get("PATH", "").split(os.pathsep)[0],
    )
    log_file = open(config.backend_log, "w")  # noqa: SIM115
    proc = subprocess.Popen(
        config.backend_cmd.split(),
        cwd=str(worktree_path),
        stdout=log_file,
        stderr=log_file,
        start_new_session=True,
        env=env,
    )

    # Wait for health check
    url = f"{config.backend_url}{HEALTH_ENDPOINT}"
    if not _wait_http_quiet(url, max_attempts=40):
        # Diagnostics: exit code + log tail
        exit_code = proc.poll()
        log.error(
            "Backend restart failed (pid=%d, exit=%s) — health check timed out",
            proc.pid, exit_code,
        )
        try:
            tail = Path(config.backend_log).read_text()[-2000:]
            log.error("Backend log tail:\n%s", tail or "(empty)")
        except OSError:
            pass
        raise RuntimeError("Backend restart failed: health check timed out")

    log.info("Backend restarted (pid=%d)", proc.pid)
    return proc


def _kill_backend_by_port(port: int) -> None:
    """Find and kill the uvicorn/python process listening on *port*."""
    try:
        output = subprocess.check_output(
            ["lsof", "-ti", f":{port}"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return  # Nothing listening

    pids = [int(p) for p in output.strip().split("\n") if p.strip()]
    if not pids:
        return

    # Find the first uvicorn/python process
    backend_pid: int | None = None
    for pid in pids:
        try:
            cmd_out = subprocess.check_output(
                ["ps", "-p", str(pid), "-o", "command="],
                text=True,
                stderr=subprocess.DEVNULL,
            )
            if "uvicorn" in cmd_out or "python" in cmd_out:
                backend_pid = pid
                break
        except subprocess.CalledProcessError:
            continue

    if backend_pid is None:
        return

    # SIGTERM first
    try:
        os.kill(backend_pid, signal.SIGTERM)
    except OSError:
        return

    # Wait up to 5 s for port to clear, then SIGKILL
    for i in range(10):
        try:
            subprocess.check_output(
                ["lsof", "-ti", f":{port}"],
                text=True,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            return  # Port is free
        if i == 4:
            try:
                os.kill(backend_pid, signal.SIGKILL)
            except OSError:
                pass
        if i >= 9:
            break
        time.sleep(1)


def _wait_http_quiet(url: str, max_attempts: int = 40) -> bool:
    """Poll *url* until 2xx. Returns True on success, False on timeout."""
    for i in range(max_attempts):
        try:
            resp = urllib.request.urlopen(url, timeout=5)  # noqa: S310
            if 200 <= resp.status < 300:
                return True
        except Exception:
            pass
        if i < max_attempts - 1:
            time.sleep(1)
    return False


# ---------------------------------------------------------------------------
# Protected file safety net (frozen judge)
# ---------------------------------------------------------------------------


def _list_protected_files(repo_root: Path) -> list[Path]:
    """Return the list of protected files (harness infra, test infra, scripts).

    Excludes ``harness/runs/`` (run artifacts).
    """
    files: list[Path] = []

    harness_dir = repo_root / "harness"
    if harness_dir.is_dir():
        for fpath in harness_dir.rglob("*"):
            if fpath.is_file() and "runs" not in fpath.relative_to(harness_dir).parts:
                files.append(fpath)

    tests_harness_dir = repo_root / "tests" / "harness"
    if tests_harness_dir.is_dir():
        for fpath in tests_harness_dir.rglob("*"):
            if fpath.is_file():
                files.append(fpath)

    for script_name in ("setup_db.sql", "seed_local.py"):
        script = repo_root / "scripts" / script_name
        if script.is_file():
            files.append(script)

    return sorted(set(files))


def snapshot_protected_files(
    repo_root: Path,
    run_dir: Path,
    cycle: int,
) -> Path:
    """Copy protected files to a backup directory.

    Returns the backup directory path.
    """
    backup = run_dir / f".harness-backup-{cycle}"
    if backup.exists():
        shutil.rmtree(backup)
    backup.mkdir(parents=True, exist_ok=True)

    for fpath in _list_protected_files(repo_root):
        rel = fpath.relative_to(repo_root)
        dest = backup / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(fpath), str(dest))

    return backup


def verify_and_restore_protected_files(
    repo_root: Path,
    backup_path: Path,
) -> int:
    """Compare current protected files against backup, restore any violations.

    * Modified or deleted files are restored from backup.
    * Files added by the fixer (not in backup) are removed.

    Returns the number of violations found and corrected.
    """
    if not backup_path.is_dir():
        return 0

    total = 0

    # Restore modified / deleted files
    for dest in sorted(backup_path.rglob("*")):
        if not dest.is_file():
            continue
        rel = dest.relative_to(backup_path)
        original = repo_root / rel
        if not original.exists() or not _files_equal(dest, original):
            original.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(dest), str(original))
            total += 1

    # Remove files added by fixer (present in repo but not in backup)
    for fpath in _list_protected_files(repo_root):
        rel = fpath.relative_to(repo_root)
        if not (backup_path / rel).exists():
            fpath.unlink(missing_ok=True)
            total += 1

    if total > 0:
        log.warning(
            "FROZEN JUDGE VIOLATION: fixer touched %d harness file(s) "
            "-- reverted to pre-fixer state",
            total,
        )

    return total


_MAIN_REPO_GUARDED_PREFIXES: tuple[str, ...] = ("src/", "cli/", "frontend/src/")


def _porcelain_dirty_set(repo_root: Path) -> set[str]:
    """Return repo-relative paths that ``git status --porcelain`` reports as
    dirty under the guarded prefixes (``src/`` and ``frontend/src/``).

    If *repo_root* is not inside a git working tree (e.g. during unit tests
    that mock ``_REPO_ROOT`` to a tmpdir), returns an empty set. Real harness
    runs always resolve _REPO_ROOT to the project git root.
    """
    cp = subprocess.run(
        ["git", "status", "--porcelain", "--", "src/", "cli/", "frontend/src/"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    if cp.returncode != 0:
        return set()
    dirty: set[str] = set()
    for raw in cp.stdout.splitlines():
        if len(raw) < 4:
            continue
        rest = raw[3:]
        # Rename syntax: "XY old -> new" — take the right-hand side.
        if " -> " in rest:
            rest = rest.split(" -> ", 1)[1]
        rest = rest.strip().strip('"')
        if rest:
            dirty.add(rest)
    return dirty


def snapshot_main_repo_working_dir(repo_root: Path) -> set[str]:
    """Return repo-relative paths under ``src/`` or ``frontend/src/`` that are
    currently dirty (modified or untracked).

    The returned set is the pre-existing baseline — paths already dirty before
    the harness ran. ``verify_and_restore_main_repo_working_dir`` will preserve
    these and only revert paths that appear *after* this snapshot.
    """
    return _porcelain_dirty_set(repo_root)


def verify_and_restore_main_repo_working_dir(
    repo_root: Path,
    snapshot: set[str],
) -> list[str]:
    """Revert any files under ``src/`` or ``frontend/src/`` that were dirtied
    after *snapshot* was taken.

    Tracked modified files → ``git restore -- <path>``.
    Untracked additions → ``unlink``.
    Paths already present in *snapshot* are preserved.

    Returns the sorted list of reverted paths.
    """
    current = _porcelain_dirty_set(repo_root)
    leaked = sorted(current - snapshot)
    if not leaked:
        return []

    for rel in leaked:
        full = repo_root / rel
        ls = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", rel],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
        )
        if ls.returncode == 0:
            subprocess.run(
                ["git", "restore", "--", rel],
                cwd=str(repo_root),
                check=False,
            )
        else:
            try:
                full.unlink()
            except FileNotFoundError:
                pass

    log.warning(
        "MAIN REPO LEAK GUARD: reverted %d file(s) edited outside the worktree: %s",
        len(leaked),
        ", ".join(leaked),
    )
    return leaked


def _files_equal(a: Path, b: Path) -> bool:
    """Byte-for-byte comparison of two files."""
    try:
        return a.read_bytes() == b.read_bytes()
    except OSError:
        return False


# ---------------------------------------------------------------------------
# Process tracker (cleanup on exit / signal)
# ---------------------------------------------------------------------------


def _supports_process_groups() -> bool:
    return hasattr(os, "setsid") and hasattr(os, "killpg")


def _terminate_pid(pid: int, *, use_pgid: bool = False, grace_seconds: int = 5) -> None:
    """SIGTERM a process (or group), escalate to SIGKILL after *grace_seconds*."""
    try:
        if use_pgid and _supports_process_groups():
            os.killpg(pid, signal.SIGTERM)
        else:
            os.kill(pid, signal.SIGTERM)
    except OSError:
        return  # Already dead

    deadline = time.monotonic() + grace_seconds
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)  # probe
        except OSError:
            return  # Gone
        time.sleep(0.2)

    # Still alive -- SIGKILL
    try:
        if use_pgid and _supports_process_groups():
            os.killpg(pid, signal.SIGKILL)
        else:
            os.kill(pid, signal.SIGKILL)
    except OSError:
        pass


class ProcessTracker:
    """Track child PIDs and clean them up on exit or signal.

    Usage::

        tracker = ProcessTracker()
        tracker.install()           # atexit + signal handlers
        proc = subprocess.Popen(...)
        tracker.register(proc.pid)
        ...
        tracker.cleanup()           # explicit teardown

    When used as a context manager, ``cleanup()`` is called on exit::

        with ProcessTracker() as tracker:
            proc = subprocess.Popen(...)
            tracker.register(proc.pid)
    """

    def __init__(self) -> None:
        self._pids: list[int] = []
        self._pgids: list[int] = []
        self._worktree: tuple[Path, str, bool] | None = None
        self._repo_root: Path | None = None
        self._installed = False
        self._cleaned_up = False
        self._prev_sigint = signal.SIG_DFL
        self._prev_sigterm = signal.SIG_DFL

    # -- registration --

    def register(self, pid: int, *, is_process_group: bool = False) -> None:
        """Register a PID (or process-group leader) for cleanup."""
        if is_process_group:
            self._pgids.append(pid)
        else:
            self._pids.append(pid)

    def set_worktree(
        self,
        worktree_path: Path,
        branch_name: str,
        auto_cleanup: bool,
        repo_root: Path | None = None,
    ) -> None:
        """Register a staging worktree for cleanup on exit."""
        self._worktree = (worktree_path, branch_name, auto_cleanup)
        self._repo_root = repo_root

    # -- lifecycle --

    def install(self) -> None:
        """Install atexit hook and signal handlers (SIGINT, SIGTERM)."""
        if self._installed:
            return
        atexit.register(self.cleanup)
        self._prev_sigint = signal.getsignal(signal.SIGINT)
        self._prev_sigterm = signal.getsignal(signal.SIGTERM)
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
        self._installed = True

    def cleanup(self) -> None:
        """Kill all tracked processes and (optionally) clean up the worktree."""
        if self._cleaned_up:
            return
        self._cleaned_up = True

        # Kill process groups first (SIGTERM -> SIGKILL)
        for pgid in self._pgids:
            _terminate_pid(pgid, use_pgid=True)

        # Kill individual PIDs
        for pid in self._pids:
            _terminate_pid(pid, use_pgid=False)

        # Cleanup worktree
        if self._worktree is not None:
            wt_path, branch, auto = self._worktree
            try:
                cleanup_staging_worktree(
                    wt_path, branch, auto, repo_root=self._repo_root
                )
            except Exception:
                log.exception("Error cleaning up worktree")

    def _handle_signal(self, signum: int, frame: object) -> None:
        """Signal handler: clean up then re-raise."""
        self.cleanup()
        # Restore the previous handler and re-raise so the exit code is correct
        if signum == signal.SIGINT:
            signal.signal(signal.SIGINT, self._prev_sigint)
        elif signum == signal.SIGTERM:
            signal.signal(signal.SIGTERM, self._prev_sigterm)
        os.kill(os.getpid(), signum)

    # -- context manager --

    def __enter__(self) -> ProcessTracker:
        self.install()
        return self

    def __exit__(self, *exc: object) -> None:
        self.cleanup()
