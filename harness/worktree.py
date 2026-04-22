"""Git worktree + backend lifecycle + exit cleanup."""
from __future__ import annotations

import atexit
import logging
import os
import signal
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from subprocess import Popen
    from harness.config import Config

log = logging.getLogger("harness.worktree")

_LIVE: list["Worktree"] = []
_HANDLERS_INSTALLED = False


@dataclass
class Worktree:
    path: Path
    branch: str
    main_repo: Path
    keep: bool = False
    backend_proc: "Popen[bytes] | None" = field(default=None)


def create(ts: str, config: "Config") -> Worktree:
    main_repo = Path.cwd()
    wt_path = (config.staging_root / ts).resolve()
    branch = f"harness/run-{ts}"
    wt_path.parent.mkdir(parents=True, exist_ok=True)

    subprocess.run(["git", "worktree", "add", "-b", branch, str(wt_path), "HEAD"], cwd=main_repo, check=True)
    os.chmod(wt_path, 0o700)

    for rel in (".venv", "node_modules", "frontend/node_modules"):
        tgt, lnk = main_repo / rel, wt_path / rel
        if tgt.exists() and not (lnk.exists() or lnk.is_symlink()):
            lnk.parent.mkdir(parents=True, exist_ok=True)
            lnk.symlink_to(tgt)

    (wt_path / "clients").mkdir(exist_ok=True)

    wt = Worktree(path=wt_path, branch=branch, main_repo=main_repo, keep=config.keep_worktree)
    _install_exit_handlers()
    _LIVE.append(wt)
    wt.backend_proc = restart_backend(wt, config)
    return wt


def attach_to_branch(branch: str, config: "Config") -> Worktree:
    """Resume a stopped run by reattaching to an existing harness branch.

    If a worktree directory for the branch already exists, reuse it. Otherwise create
    a fresh `git worktree add` against the branch tip. The caller (run.py) treats the
    returned worktree the same as `create()`'s output — the orchestrator starts a fresh
    cycle from the branch's current state; anything already committed stays committed.
    """
    main_repo = Path.cwd()
    # Mirror create()'s path convention: branch is "harness/run-<ts>", worktree dir is "<staging_root>/<ts>".
    branch_leaf = branch.rsplit("/", 1)[-1]  # "run-<ts>"
    ts = branch_leaf.removeprefix("run-")    # "<ts>"
    wt_path = (config.staging_root / ts).resolve()
    wt_path.parent.mkdir(parents=True, exist_ok=True)

    verify = subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"],
        cwd=main_repo, check=False,
    )
    if verify.returncode != 0:
        raise RuntimeError(f"resume branch not found: {branch}")

    if not wt_path.exists():
        subprocess.run(
            ["git", "worktree", "add", str(wt_path), branch],
            cwd=main_repo, check=True,
        )
    os.chmod(wt_path, 0o700)

    for rel in (".venv", "node_modules", "frontend/node_modules"):
        tgt, lnk = main_repo / rel, wt_path / rel
        if tgt.exists() and not (lnk.exists() or lnk.is_symlink()):
            lnk.parent.mkdir(parents=True, exist_ok=True)
            lnk.symlink_to(tgt)

    (wt_path / "clients").mkdir(exist_ok=True)

    wt = Worktree(path=wt_path, branch=branch, main_repo=main_repo, keep=config.keep_worktree)
    _install_exit_handlers()
    _LIVE.append(wt)
    wt.backend_proc = restart_backend(wt, config)
    return wt


def cleanup(wt: Worktree) -> None:
    """Tear down the per-run worktree and backend, but preserve the branch.

    Branches are the unit of resumability (--resume-branch) and are nearly free
    (git refs are small). We keep them by default so a user who SIGTERMs a run,
    hits a graceful stop, or crashes mid-fix can always resume — and so the
    graceful-stop log message ("to resume: --resume-branch X") is never a lie.

    Pruning accumulated harness branches is a manual concern:
        git branch | grep 'harness/run-' | xargs git branch -D
    """
    _terminate_backend(wt)
    subprocess.run(["git", "worktree", "remove", "--force", str(wt.path)], cwd=wt.main_repo, check=False)
    if wt in _LIVE:
        _LIVE.remove(wt)


def restart_backend(wt: Worktree, config: "Config") -> "Popen[bytes]":
    _terminate_backend(wt)
    _kill_port(config.backend_port)

    env = os.environ.copy()
    env["PATH"] = f"{wt.path / '.venv' / 'bin'}:{env.get('PATH', '')}"
    # Worktree path first on PYTHONPATH so `src.api.main` resolves to the worktree's source,
    # not the main repo (the editable install in .venv points at the main repo).
    env["PYTHONPATH"] = f"{wt.path}:{env.get('PYTHONPATH', '')}"

    # The child inherits a dup'd fd; parent can close log_fp after Popen returns.
    with open(wt.path / "backend.log", "a", encoding="utf-8") as log_fp:
        log_fp.write(f"\n=== backend restart {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        log_fp.flush()
        proc = subprocess.Popen(
            config.backend_cmd.split(),
            cwd=wt.path, env=env, stdout=log_fp, stderr=subprocess.STDOUT, start_new_session=True,
        )
    wt.backend_proc = proc
    _poll_health(config.backend_url + "/health", timeout=40)
    log.info("backend up on %s (pid=%s)", config.backend_url, proc.pid)
    return proc


def rollback_track_scope(wt: Worktree, track: str) -> None:
    """Revert only files matching this track's allowlist. Parallel-safe.

    `git checkout -- <files>` restores modified files to HEAD; `Path.unlink` deletes
    untracked ones. Never calls `git reset --hard` or `git clean -fd` — those would
    destroy peer tracks' in-flight working-tree edits in parallel mode.

    Raises RuntimeError if `git status` fails — silent return would leave the
    worktree dirty, and the next `_commit_fix` could then stage stale edits.
    """
    from harness import safety  # noqa: C0415 — keeps worktree import-safe at top level
    pattern = safety.SCOPE_ALLOWLIST[track]
    result = subprocess.run(
        ["git", "status", "--porcelain", "-z", "-uall"],
        cwd=wt.path, capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"rollback_track_scope: git status failed (rc={result.returncode}): "
            f"{result.stderr.strip() or '(no stderr)'}"
        )

    modified: list[str] = []
    untracked: list[str] = []
    for record in result.stdout.split("\x00"):
        if not record:
            continue
        status = record[:2]
        path = record[3:]
        if not path or safety.HARNESS_ARTIFACTS.match(path) or not pattern.match(path):
            continue
        if status.startswith("?"):  # "??" = untracked
            untracked.append(path)
        else:
            modified.append(path)

    if modified:
        # `git reset HEAD --` unstages anything accidentally left in the index
        # (e.g., if a prior commit failed after `git add`). `git checkout --` then
        # restores the working tree to HEAD. Both are no-ops in the common case.
        subprocess.run(["git", "reset", "HEAD", "--", *modified], cwd=wt.path, check=False)
        subprocess.run(["git", "checkout", "--", *modified], cwd=wt.path, check=False)
    for rel in untracked:
        (wt.path / rel).unlink(missing_ok=True)


def _terminate_backend(wt: Worktree) -> None:
    if wt.backend_proc is None:
        return
    try:
        os.killpg(os.getpgid(wt.backend_proc.pid), signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        pass
    try:
        wt.backend_proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(wt.backend_proc.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
    wt.backend_proc = None


def _kill_port(port: int) -> None:
    try:
        output = subprocess.check_output(
            ["lsof", "-ti", f"tcp:{port}", "-sTCP:LISTEN"], text=True, stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return
    pids = [int(p) for p in output.strip().split("\n") if p.strip()]
    for sig, wait in ((signal.SIGTERM, 5), (signal.SIGKILL, 0)):
        for pid in pids:
            try: os.kill(pid, sig)
            except ProcessLookupError: pass
        if wait: time.sleep(wait)


def _poll_health(url: str, timeout: int = 40) -> None:
    deadline = time.time() + timeout
    last_err: Exception | None = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:  # noqa: S310
                if resp.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last_err = exc
        time.sleep(1)
    raise RuntimeError(f"backend failed to become healthy at {url} within {timeout}s: {last_err}")


def _install_exit_handlers() -> None:
    global _HANDLERS_INSTALLED
    if _HANDLERS_INSTALLED:
        return

    def _handler(*_: object) -> None:
        for wt in list(_LIVE):
            try:
                if not wt.keep:
                    cleanup(wt)
                else:
                    _terminate_backend(wt)
            except Exception as exc:  # noqa: BLE001 — best effort on exit
                log.warning("exit handler: cleanup failed for %s: %s", wt.path, exc)

    atexit.register(_handler)
    signal.signal(signal.SIGTERM, lambda *_: (_handler(), os._exit(143)))
    signal.signal(signal.SIGINT, lambda *_: (_handler(), os._exit(130)))
    _HANDLERS_INSTALLED = True
