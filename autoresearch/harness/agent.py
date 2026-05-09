"""Session execution -- launch and manage agent subprocess lifecycles."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parent
AUTORESEARCH_DIR = HARNESS_DIR.parent
REPO_ROOT = AUTORESEARCH_DIR.parent
if str(AUTORESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(AUTORESEARCH_DIR))

import harness  # noqa: F401,E402  # ensure package-level path setup runs

from harness.backend import (  # noqa: E402
    codex_approval_policy,
    codex_reasoning_effort,
    codex_sandbox,
    codex_web_search,
    session_backend,
    session_model,
)
from runtime import config as runtime_config  # type: ignore  # noqa: E402
from watchdog import TERMINATION_GRACE_SECONDS  # type: ignore  # noqa: E402

SCRIPT_DIR = harness.ARCHIVE_CURRENT_DIR
FRESH_MAX_TURNS = runtime_config.FRESH_MAX_TURNS

# OpenCode dispatches to OpenRouter, which dispatches to upstream providers
# (Together, DeepSeek-official, etc.). Individual provider hiccups —
# rate_limit_exceeded, provider_overloaded, upstream timeout — surface as
# error events in the JSONL while the opencode subprocess itself exits 0.
# Retry up to this many total attempts; OPENCODE_MAX_RETRIES env override
# lets operators tighten or loosen as upstream availability shifts.
_OPENCODE_MAX_ATTEMPTS = max(1, int(os.environ.get("OPENCODE_MAX_RETRIES", "3")))


def _supports_process_groups() -> bool:
    return hasattr(os, "setsid") and hasattr(os, "killpg")


def _agent_command(
    model: str, max_turns: int,
    prompt_text: str | None = None,
    session_id: str | None = None,
    resume_sid: str | None = None,
) -> list[str]:
    """Build the agent subprocess argv.

    Resume parity (Section 4): when ``session_id`` is supplied, claude is
    invoked with ``--session-id <uuid>`` so the conversation JSONL is keyed
    off a UUID we control. The caller writes the same UUID into the per-
    fixture sentinel file so a future ``--resume <sid>`` can re-attach.
    Codex pre-mint is not supported by the CLI — codex resume is detected
    post-spawn from ``~/.codex/sessions/`` rollouts. OpenCode multi-provider
    routes lack a stable resume mechanism (documented).
    """
    backend = session_backend()
    if backend == "claude":
        if resume_sid:
            cmd = [
                "claude", "-p", "--model", model,
                "--allowedTools", "Bash,Read,Write,Edit,Glob,Grep",
                "--max-turns", str(max_turns),
                "--resume", resume_sid,
            ]
        else:
            cmd = [
                "claude", "-p", "--model", model,
                "--allowedTools", "Bash,Read,Write,Edit,Glob,Grep",
                "--max-turns", str(max_turns),
            ]
            if session_id:
                cmd.extend(["--session-id", session_id])
        if prompt_text is not None:
            cmd.append(prompt_text)
        return cmd
    if backend == "opencode":
        cmd = [
            "opencode", "run",
            "--dangerously-skip-permissions",
            "-m", model,
            "--format", "json",
        ]
        if prompt_text is not None:
            cmd.append(prompt_text)
        return cmd
    cmd = [
        "codex", "exec",
        "--model", model,
        "--sandbox", codex_sandbox(),
        "--color", "never",
        "--ephemeral",
        "-c", f"approval_policy=\"{codex_approval_policy()}\"",
        "-c", f"model_reasoning_effort=\"{codex_reasoning_effort()}\"",
        "-c", f"web_search=\"{codex_web_search()}\"",
        "-c", "otel.exporter=\"none\"",
        "-c", "otel.trace_exporter=\"none\"",
        "-c", "otel.metrics_exporter=\"none\"",
        "-C", str(SCRIPT_DIR),
    ]
    if prompt_text is not None:
        cmd.append(prompt_text)
    return cmd


def _terminate_subprocess(process: subprocess.Popen, reason: str, grace_seconds: int = TERMINATION_GRACE_SECONDS):
    if process.poll() is not None:
        return
    print(f"Stopping agent process ({reason}).")
    try:
        if _supports_process_groups():
            os.killpg(process.pid, signal.SIGTERM)
        else:
            process.terminate()
        process.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        if _supports_process_groups():
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
        process.wait()


def _unbuffered_env() -> dict[str, str]:
    """Force flushed stdout on the agent subprocess so iteration logs
    survive abnormal termination. Matches PYTHONUNBUFFERED=1 for Python
    children; codex/claude wrappers also observe the var.

    For opencode, also pin OPENCODE_CONFIG to the repo's opencode.json so
    OpenRouter provider-routing rules (deepseek-v4 → tools-supporting
    upstreams only) apply regardless of subprocess cwd. opencode discovers
    config by walking up to the nearest .git, but agent subprocesses run
    with cwd=archive_current_dir which has no opencode.json — and worse,
    smoke tests run with cwd in /tmp where the walk never reaches a git
    repo at all. Skip when the operator already set OPENCODE_CONFIG."""
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    if session_backend() == "opencode":
        config_path = REPO_ROOT / "opencode.json"
        if config_path.is_file() and not env.get("OPENCODE_CONFIG"):
            env["OPENCODE_CONFIG"] = str(config_path)
    return env


def _err_path(log_path: Path) -> Path:
    return log_path.with_suffix(log_path.suffix + ".err") if log_path.suffix else log_path.with_suffix(".err")


def _session_id_sentinel(log_path: Path) -> Path:
    """Per-fixture session_id sentinel path. log_path lives at
    ``<variant>/sessions/<domain>/<client>/sessions/main.log`` (or sibling),
    so the sentinel sits at ``<variant>/sessions/<domain>/<client>/.session_id``.
    Falls back to log_path's parent when the layout doesn't match."""
    candidates = [
        log_path.parent.parent,  # standard runner layout: sessions/<d>/<c>/.session_id
        log_path.parent,
    ]
    for cand in candidates:
        if cand.is_dir():
            return cand / ".session_id"
    return log_path.parent / ".session_id"


def _read_resume_sid(log_path: Path) -> str | None:
    """If a sentinel from a prior killed run exists AND the claude JSONL is
    intact, return that session_id so this spawn can ``--resume <sid>``."""
    sentinel = _session_id_sentinel(log_path)
    if not sentinel.is_file():
        return None
    try:
        sid = sentinel.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not sid:
        return None
    # Viability: claude only resumes when its local JSONL exists.
    encoded = str(SCRIPT_DIR).replace("/", "-")
    jsonl = Path.home() / ".claude" / "projects" / encoded / f"{sid}.jsonl"
    return sid if jsonl.is_file() else None


def run_agent_session(prompt_text: str, timeout: int, log_path: Path,
                      model: str | None = None, max_turns: int = FRESH_MAX_TURNS,
                      cwd: Path | None = None) -> tuple[int, int]:
    """Run the configured agent via stdin. Returns (exit_code, duration_ms).

    For opencode, retries transient upstream-provider errors
    (rate_limit_exceeded, provider_overloaded, timeout) up to
    _OPENCODE_MAX_ATTEMPTS times. The subprocess itself usually exits 0 in
    these cases — opencode captures the API failure as an error event in
    the JSONL — so we detect failure by scanning the log, not by exit code.

    Resume parity (Section 4): on claude, mint a UUID, persist it to
    ``<session_dir>/.session_id`` BEFORE spawn so a kill leaves the sid
    discoverable. On a subsequent invocation, if the sentinel exists AND
    claude's local JSONL for that sid is intact, re-attach via
    ``--resume <sid>`` instead of starting fresh. Removes the sentinel on
    successful completion.
    """
    from harness.opencode_jsonl import session_has_transient_error  # local: avoid import cycle on lean codex paths

    start = time.monotonic()
    model = model or session_model()
    backend = session_backend()
    err_path = _err_path(log_path)

    # Mint UUID + persist sentinel for claude only; codex/opencode can't
    # resume by pre-mint, but we still remove any stale sentinel so a
    # later invocation doesn't try to resume the wrong backend.
    session_id: str | None = None
    resume_sid: str | None = None
    sentinel = _session_id_sentinel(log_path)
    if backend == "claude":
        resume_sid = _read_resume_sid(log_path)
        if not resume_sid:
            session_id = str(uuid.uuid4())
            try:
                sentinel.parent.mkdir(parents=True, exist_ok=True)
                sentinel.write_text(session_id, encoding="utf-8")
            except OSError:
                session_id = None  # best-effort; degrade gracefully
    elif sentinel.is_file():
        # Stale sentinel from a prior backend swap; remove so it doesn't
        # mislead a future run.
        try:
            sentinel.unlink()
        except OSError:
            pass

    cmd = _agent_command(
        model, max_turns, prompt_text,
        session_id=session_id, resume_sid=resume_sid,
    )

    # Unified transient-error retry for all backends. agent_retry lives at
    # autoresearch/agent_retry.py and is sys.path-resolvable from the
    # AUTORESEARCH_DIR insert at the top of this module.
    from agent_retry import (  # type: ignore  # noqa: E402
        max_attempts as _max_attempts,
        is_transient_failure as _is_transient,
        sleep_for_retry as _sleep_retry,
        backoff_delay as _backoff_delay,
    )

    attempts = _max_attempts()
    exit_code = 0
    for attempt in range(1, attempts + 1):
        try:
            with open(log_path, "w") as log_file, open(err_path, "w") as err_file:
                process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.DEVNULL,
                    stdout=log_file, stderr=err_file,
                    cwd=str(cwd) if cwd is not None else str(SCRIPT_DIR),
                    text=True,
                    bufsize=0,
                    env=_unbuffered_env(),
                    start_new_session=_supports_process_groups(),
                )
                exit_code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            _terminate_subprocess(process, "timeout")
            exit_code = 124

        # Read log + err for transient-detection.
        log_text = ""
        err_text = ""
        try:
            log_text = log_path.read_text(encoding="utf-8", errors="replace")[-4000:]
        except OSError:
            pass
        try:
            err_text = err_path.read_text(encoding="utf-8", errors="replace")[-4000:]
        except OSError:
            pass
        transient = _is_transient(backend, exit_code, stdout=log_text, stderr=err_text)
        if exit_code == 0 and not transient:
            break
        if attempt == attempts or not transient:
            break
        print(
            f"{backend} session attempt {attempt}/{attempts} hit transient signal "
            f"(exit={exit_code}); retrying in {_backoff_delay(attempt)}s"
        )
        _sleep_retry(attempt)

    # Clean exit on claude → drop the sentinel so future runs don't try to
    # resume a completed session. Failures keep the sentinel so the next
    # run can re-attach.
    if backend == "claude" and exit_code == 0 and sentinel.is_file():
        try:
            sentinel.unlink()
        except OSError:
            pass

    duration_ms = int((time.monotonic() - start) * 1000)
    return exit_code, duration_ms


def spawn_agent_process(prompt_text: str, log_path: Path,
                        model: str | None = None, max_turns: int = 2500,
                        cwd: Path | None = None) -> tuple[subprocess.Popen, object]:
    """Start a long-lived agent process for multi-turn mode.

    ``cwd`` defaults to the live machine's ``ARCHIVE_CURRENT_DIR``, which
    is wrong for holdout runs (the variant is cloned to a temp tree but
    the agent reads ``sessions/<lane>/<client>/session.md`` relative to
    cwd → finds the live machine's stale ``Status: COMPLETE`` from a
    prior real run → declares "session is already complete" → stalls).
    Variant ``run.py`` should pass ``cwd=<variant_dir>`` (its own
    ``SCRIPT_DIR``) so the agent reads variant-local state. Surfaced
    2026-05-07 by stall investigation: 3 of 4 fixture stalls in geo +
    competitive holdouts traced to this exact bug.
    """
    model = model or session_model()
    cmd = _agent_command(model, max_turns, prompt_text)
    log_file = open(log_path, "w")
    err_file = open(_err_path(log_path), "w")
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.DEVNULL,
        stdout=log_file,
        stderr=err_file,
        cwd=str(cwd) if cwd is not None else str(SCRIPT_DIR),
        text=True,
        bufsize=0,
        env=_unbuffered_env(),
        start_new_session=_supports_process_groups(),
    )
    return process, log_file
