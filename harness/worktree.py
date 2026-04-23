"""Git worktree + backend lifecycle + exit cleanup.

Per-worker pool model: one STAGING worktree on branch `harness/run-<ts>` is
the authoritative branch (cherry-picks land here). N WORKER worktrees on
branches `harness/run-<ts>/w<i>` run fix+verify in parallel, each with its
own backend port. Workers reset to staging between findings via
`reset_worker_to_staging` so each finding sees all previously-merged fixes.

Shared Vite at `frontend_port_base` serves the STAGING worktree; per-worker
Vite is a Phase 2 improvement (Bug #18 warning persists for track-C fixes).
"""
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

# worker_id sentinel — staging is not a numbered worker. Keeps `if wt.worker_id == STAGING`
# readable at call sites.
STAGING: int = -1


@dataclass
class Worktree:
    path: Path
    branch: str
    main_repo: Path
    keep: bool = False
    # worker_id == STAGING (-1) for the staging worktree; 0..N-1 for pool workers.
    worker_id: int = STAGING
    backend_port: int = 8000
    backend_url: str = "http://127.0.0.1:8000"
    backend_proc: "Popen[bytes] | None" = field(default=None)

    @property
    def is_staging(self) -> bool:
        return self.worker_id == STAGING


def create(ts: str, config: "Config") -> Worktree:
    """Create the staging worktree on branch `harness/run-<ts>`.

    Staging holds the cherry-pick target branch: verified fixes from workers
    land here under `staging_lock`. Evaluators and post-cycle tip-smoke also
    run against this worktree's backend.
    """
    main_repo = Path.cwd()
    wt_path = (config.staging_root / ts / "staging").resolve()
    branch = f"harness/run-{ts}"
    wt_path.parent.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        ["git", "worktree", "add", "-b", branch, str(wt_path), "HEAD"],
        cwd=main_repo, check=True,
    )
    _provision_links(wt_path, main_repo)

    wt = Worktree(
        path=wt_path, branch=branch, main_repo=main_repo,
        keep=config.keep_worktree, worker_id=STAGING,
        backend_port=config.backend_port_base,
        backend_url=f"http://127.0.0.1:{config.backend_port_base}",
    )
    _install_exit_handlers()
    _LIVE.append(wt)
    wt.backend_proc = restart_backend(wt, config)
    return wt


def create_workers(ts: str, config: "Config", staging_branch: str) -> list[Worktree]:
    """Create `config.max_workers` worker worktrees cut from staging tip.

    Each worker gets its own branch (`harness/run-<ts>/w<i>`), own worktree
    directory, and own backend port (`backend_port_base + 1 + i`). Backends
    are started immediately so the worker pool is warm when findings arrive.

    Workers isolate file edits (no race with peers) and verification (each
    verifier hits its own backend → sees THIS worker's fix, not staging's).
    """
    main_repo = Path.cwd()
    workers: list[Worktree] = []
    for i in range(config.max_workers):
        wt_path = (config.staging_root / ts / f"w{i}").resolve()
        # Underscore separator (not slash) between staging stem and worker suffix
        # because git refs are hierarchical: a branch named `harness/run-<ts>/w0`
        # cannot coexist with `harness/run-<ts>` (child-path conflict in
        # refs/heads/). Using `-w<i>` keeps the naming flat and grep-friendly.
        branch = f"harness/run-{ts}-w{i}"
        wt_path.parent.mkdir(parents=True, exist_ok=True)
        # Resume: a prior run's worker branch may already exist. `-b` fails with
        # "branch already exists"; without `-b`, we just attach. Decide up front.
        branch_exists = subprocess.run(
            ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"],
            cwd=main_repo, check=False,
        ).returncode == 0
        if branch_exists:
            # Reattach — skip -b, pass existing branch as the worktree ref.
            subprocess.run(
                ["git", "worktree", "add", str(wt_path), branch],
                cwd=main_repo, check=True,
            )
            # Sync to staging tip so resumed worker picks up any fixes landed after
            # its branch was last written (prior run might have crashed mid-reset).
            subprocess.run(
                ["git", "reset", "--hard", staging_branch],
                cwd=wt_path, check=True, capture_output=True,
            )
        else:
            # Fresh: `-b <new-branch> <path> <start-point>` cuts from staging tip.
            subprocess.run(
                ["git", "worktree", "add", "-b", branch, str(wt_path), staging_branch],
                cwd=main_repo, check=True,
            )
        _provision_links(wt_path, main_repo)
        port = config.backend_port_base + 1 + i
        wt = Worktree(
            path=wt_path, branch=branch, main_repo=main_repo,
            keep=config.keep_worktree, worker_id=i,
            backend_port=port,
            backend_url=f"http://127.0.0.1:{port}",
        )
        _LIVE.append(wt)
        wt.backend_proc = restart_backend(wt, config)
        workers.append(wt)
        log.info("worker %d worktree ready at %s (backend :%d)", i, wt_path, port)
    return workers


def reset_worker_to_staging(wt: Worktree, staging_branch: str) -> None:
    """Sync worker's worktree to current staging tip.

    Called between findings so each new finding sees all previously-merged
    fixes. Hard-resets the worker's branch to staging + cleans any leftover
    untracked files (fixer artifacts from the previous finding). Safe because
    worker branches are throwaway — the canonical record is on `staging_branch`
    after cherry-pick.
    """
    if wt.is_staging:
        raise RuntimeError(
            f"reset_worker_to_staging called on staging wt ({wt.path}); "
            "orchestrator manages staging directly"
        )
    subprocess.run(
        ["git", "reset", "--hard", staging_branch],
        cwd=wt.path, check=True, capture_output=True,
    )
    # Drop any untracked residue from a prior finding (e.g. `harness/blocked-<id>.md`,
    # unstaged scratch files). Scoped to common fixer-reachable dirs below.
    subprocess.run(
        ["git", "clean", "-fd",
         "--", "cli/", "src/", "autoresearch/", "frontend/", "harness/", "tests/"],
        cwd=wt.path, check=False, capture_output=True,
    )


def _provision_links(wt_path: Path, main_repo: Path) -> None:
    """Shared symlinks into main repo (venv, node_modules) so every worktree
    reuses the same installed deps. Cheap compared to re-provisioning per
    worktree; safe because these dirs are read-mostly at runtime."""
    os.chmod(wt_path, 0o700)
    for rel in (".venv", "node_modules", "frontend/node_modules"):
        tgt, lnk = main_repo / rel, wt_path / rel
        if tgt.exists() and not (lnk.exists() or lnk.is_symlink()):
            lnk.parent.mkdir(parents=True, exist_ok=True)
            lnk.symlink_to(tgt)
    (wt_path / "clients").mkdir(exist_ok=True)


def attach_to_branch(branch: str, config: "Config") -> Worktree:
    """Resume a stopped run by reattaching to an existing STAGING branch.

    If a worktree directory for the branch already exists, reuse it. Otherwise
    create a fresh `git worktree add` against the branch tip. The caller
    (run.py) treats the returned worktree the same as `create()`'s output.
    """
    main_repo = Path.cwd()
    branch_leaf = branch.rsplit("/", 1)[-1]  # "run-<ts>"
    ts = branch_leaf.removeprefix("run-")    # "<ts>"
    wt_path = (config.staging_root / ts / "staging").resolve()
    # Legacy resume layout: run-<ts>/ was itself the worktree. Fall back if "staging/" absent.
    legacy_wt_path = (config.staging_root / ts).resolve()
    if not wt_path.exists() and legacy_wt_path.exists() and (legacy_wt_path / ".git").exists():
        wt_path = legacy_wt_path
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
    _provision_links(wt_path, main_repo)

    wt = Worktree(
        path=wt_path, branch=branch, main_repo=main_repo,
        keep=config.keep_worktree, worker_id=STAGING,
        backend_port=config.backend_port_base,
        backend_url=f"http://127.0.0.1:{config.backend_port_base}",
    )
    _install_exit_handlers()
    _LIVE.append(wt)
    wt.backend_proc = restart_backend(wt, config)
    return wt


def cleanup(wt: Worktree) -> None:
    """Tear down a worktree and its backend, but preserve the branch.

    Branches are the unit of resumability (--resume-branch) and are nearly free
    (git refs are small). We keep them by default so a user who SIGTERMs a run,
    hits a graceful stop, or crashes mid-fix can always resume.

    Pruning accumulated harness branches is a manual concern:
        git branch | grep 'harness/run-' | xargs git branch -D
    """
    _terminate_backend(wt)
    subprocess.run(
        ["git", "worktree", "remove", "--force", str(wt.path)],
        cwd=wt.main_repo, check=False,
    )
    if wt in _LIVE:
        _LIVE.remove(wt)


def restart_backend(wt: Worktree, config: "Config") -> "Popen[bytes]":
    """Restart this worktree's backend on its dedicated port.

    Each worker owns its own port (`wt.backend_port`); staging uses
    `config.backend_port_base`. The `--port <wt.backend_port>` arg is spliced
    into `config.backend_cmd` so a single base command template drives both
    staging and worker backends.
    """
    _terminate_backend(wt)
    _kill_port(wt.backend_port)

    env = os.environ.copy()
    env["PATH"] = f"{wt.path / '.venv' / 'bin'}:{env.get('PATH', '')}"
    env["PYTHONPATH"] = f"{wt.path}:{env.get('PYTHONPATH', '')}"

    # Replace whatever port the template carries with THIS worktree's port.
    # Template format guaranteed by Config: "... --port <N>".
    cmd_parts = config.backend_cmd.split()
    for idx, tok in enumerate(cmd_parts):
        if tok == "--port" and idx + 1 < len(cmd_parts):
            cmd_parts[idx + 1] = str(wt.backend_port)
            break

    with open(wt.path / "backend.log", "a", encoding="utf-8") as log_fp:
        log_fp.write(
            f"\n=== backend restart {time.strftime('%Y-%m-%d %H:%M:%S')} "
            f"port={wt.backend_port} worker={wt.worker_id} ===\n"
        )
        log_fp.flush()
        proc = subprocess.Popen(
            cmd_parts,
            cwd=wt.path, env=env, stdout=log_fp, stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    wt.backend_proc = proc
    _poll_health(wt.backend_url + "/health", timeout=40)
    log.info("backend up on %s (pid=%s, worker=%s)",
             wt.backend_url, proc.pid, wt.worker_id)
    return proc


def rollback_track_scope(wt: Worktree, track: str) -> None:
    """Revert only files matching this track's allowlist.

    In the per-worker model this is ONLY ever called on a worker worktree
    (never staging). Because worker worktrees are isolated, there are no peer
    tracks to protect — but keep the scoped revert (not `git reset --hard`)
    so the worker's .env / build artifacts / symlinked node_modules survive.

    `git checkout -- <files>` restores modified files to HEAD; `Path.unlink` deletes
    untracked ones.

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
            ["lsof", "-ti", f"tcp:{port}", "-sTCP:LISTEN"],
            text=True, stderr=subprocess.DEVNULL,
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
