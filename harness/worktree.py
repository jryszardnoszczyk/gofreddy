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


def cleanup(wt: Worktree) -> None:
    _terminate_backend(wt)
    subprocess.run(["git", "worktree", "remove", "--force", str(wt.path)], cwd=wt.main_repo, check=False)
    subprocess.run(["git", "branch", "-D", wt.branch], cwd=wt.main_repo, check=False)
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


def rollback_to(wt: Worktree, sha: str) -> None:
    subprocess.run(["git", "reset", "--hard", sha], cwd=wt.path, check=False)
    # git clean -fd -e .venv -e node_modules -e clients  (preserves symlinks + per-run clients/)
    subprocess.run(
        ["git", "clean", "-fd", "-e", ".venv", "-e", "node_modules", "-e", "clients"],
        cwd=wt.path, check=False,
    )


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
