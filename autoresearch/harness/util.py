"""Shared utilities -- locks, subprocess helpers, JSON loading, timeout defaults."""

from __future__ import annotations

import fcntl
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parent
AUTORESEARCH_DIR = HARNESS_DIR.parent
if str(AUTORESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(AUTORESEARCH_DIR))

import harness  # noqa: F401,E402  # ensure package-level path setup runs

from workflows import get_workflow_spec  # type: ignore  # noqa: E402

SCRIPT_DIR = harness.ARCHIVE_CURRENT_DIR


def _lock_path(domain: str, client: str, fixture_id: str | None = None) -> Path:
    fixture_id = fixture_id or os.environ.get("AUTORESEARCH_FIXTURE_ID")
    if fixture_id:
        lock_name = f"{domain}-session-{client}-{fixture_id}.lock"
    else:
        lock_name = f"{domain}-session-{client}.lock"
    return Path(tempfile.gettempdir()) / lock_name


def acquire_lock(domain: str, client: str, fixture_id: str | None = None) -> int | None:
    """Acquire per-client file lock. Returns fd or None on failure.

    When *fixture_id* is provided (or set via ``AUTORESEARCH_FIXTURE_ID``),
    the lock is keyed per-fixture so parallel fixture runs don't collide.
    Callers MUST release via release_lock(fd, domain, client, fixture_id)
    on normal and exceptional exits.
    """
    lock_path = _lock_path(domain, client, fixture_id)
    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_WRONLY)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except (OSError, IOError):
        print(f"Session already running for {client} ({domain})")
        return None


def release_lock(fd: int | None, domain: str, client: str, fixture_id: str | None = None) -> None:
    """Release the lock acquired via acquire_lock. Safe to call with fd=None."""
    if fd is None:
        return
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
    except OSError:
        pass
    try:
        os.close(fd)
    except OSError:
        pass
    try:
        _lock_path(domain, client, fixture_id).unlink(missing_ok=True)
    except OSError:
        pass


def default_timeout_for_strategy(domain: str, strategy: str) -> int:
    cfg = get_workflow_spec(domain).config
    if strategy == "multiturn":
        return cfg.multiturn_timeout or max(cfg.default_timeout, 7200)
    return cfg.default_timeout


def _load_json_output(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError):
        return None


_RUN_SCRIPT_DEFAULT_TIMEOUT = 120

# Per-script timeout overrides for scripts that legitimately exceed the
# default. Keep this list short — most post-session scripts complete in a
# few seconds; the entries here are scripts whose work cost is dominated
# by external subprocess calls (chromium for render, gemini for evals).
_RUN_SCRIPT_TIMEOUTS = {
    # render_report.py: Stage-2 codex enrichment (~30-90s) + html_to_pdf
    # (Chrome ~30-60s) + html_to_screenshot (Chrome ~30-60s) easily clears
    # 120s when RENDER_BACKEND defaults to codex. 360s gives all 3 phases
    # room to complete with a safety margin. Surfaced 2026-05-08 evening
    # when the storyboard auto-render hit the 120s wall after session
    # produced 5 KEEP storyboards.
    "render_report.py": 360,
}


def _run_script(script_name: str, *args, stdout_file: Path | None = None,
                timeout: int | None = None):
    """Run a script. Resolves variant-side first, then live-side fallback. Non-fatal.

    Lookup order:

    1. ``SCRIPT_DIR/scripts/<script_name>`` — the variant's own copy (e.g.
       ``archive/current_runtime/scripts/<script_name>``). A meta-agent that
       mutates a script lives here.
    2. ``AUTORESEARCH_DIR/scripts/<script_name>`` — the live shared copy under
       ``autoresearch/scripts/``. One source of truth for utility scripts the
       evolution loop doesn't need to mutate per variant (summarize_session,
       etc.). Lets us delete the per-archive copies once each variant's local
       script is identical to live.

    Timeout: default 120s, overridable via ``timeout`` arg or per-script
    entries in ``_RUN_SCRIPT_TIMEOUTS``. Render-pipeline scripts that
    invoke chromium + codex are pre-tuned for higher ceilings.

    Returns silently when neither exists (callers tolerate missing scripts —
    e.g. lanes that don't ship a generate_report.py).
    """
    variant_script = SCRIPT_DIR / "scripts" / script_name
    live_script = AUTORESEARCH_DIR / "scripts" / script_name
    script = variant_script if variant_script.exists() else live_script
    if not script.exists():
        return
    effective_timeout = (
        timeout if timeout is not None
        else _RUN_SCRIPT_TIMEOUTS.get(script_name, _RUN_SCRIPT_DEFAULT_TIMEOUT)
    )
    try:
        cmd = ["python3", str(script)] + list(args)
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=effective_timeout,
        )
        if stdout_file:
            stdout_file.write_text(result.stdout)
            # Persist stderr alongside the requested stdout file so warnings
            # from summarize_session / promote_findings / build_geo_report /
            # render_report are recoverable post-hoc. Without this, every
            # helper-script stderr line — including FATAL fabricated-source
            # warnings, reconciliation failures, structural-gate misses —
            # disappeared the moment _run_script returned.
            if result.stderr:
                try:
                    stdout_file.with_suffix(stdout_file.suffix + ".stderr") \
                        .write_text(result.stderr)
                except OSError:
                    pass
        # Always echo non-empty stderr to the parent stream so a watcher /
        # CI log sees it even when no stdout_file was requested. Keep the
        # script-name prefix so multiple parallel _run_script calls
        # interleave readably.
        if result.stderr.strip():
            for line in result.stderr.splitlines()[:120]:
                print(f"  [{script_name} stderr] {line}")
    except Exception as e:
        print(f"WARNING: {script_name} failed: {e}")


def _run_subprocess(cmd: list[str]):
    """Run arbitrary subprocess. Non-fatal."""
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except Exception as e:
        print(f"WARNING: {cmd[0]} failed: {e}")
