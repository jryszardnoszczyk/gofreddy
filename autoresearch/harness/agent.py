"""Session execution -- launch and manage agent subprocess lifecycles."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
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


def _agent_command(model: str, max_turns: int, prompt_text: str | None = None) -> list[str]:
    backend = session_backend()
    if backend == "claude":
        cmd = [
            "claude", "-p", "--model", model,
            "--allowedTools", "Bash,Read,Write,Edit,Glob,Grep",
            "--max-turns", str(max_turns),
        ]
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


def run_agent_session(prompt_text: str, timeout: int, log_path: Path,
                      model: str | None = None, max_turns: int = FRESH_MAX_TURNS) -> tuple[int, int]:
    """Run the configured agent via stdin. Returns (exit_code, duration_ms).

    For opencode, retries transient upstream-provider errors
    (rate_limit_exceeded, provider_overloaded, timeout) up to
    _OPENCODE_MAX_ATTEMPTS times. The subprocess itself usually exits 0 in
    these cases — opencode captures the API failure as an error event in
    the JSONL — so we detect failure by scanning the log, not by exit code.
    """
    from harness.opencode_jsonl import session_has_transient_error  # local: avoid import cycle on lean codex paths

    start = time.monotonic()
    model = model or session_model()
    backend = session_backend()
    cmd = _agent_command(model, max_turns, prompt_text)
    err_path = _err_path(log_path)

    attempts = _OPENCODE_MAX_ATTEMPTS if backend == "opencode" else 1
    exit_code = 0
    for attempt in range(1, attempts + 1):
        try:
            with open(log_path, "w") as log_file, open(err_path, "w") as err_file:
                process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.DEVNULL,
                    stdout=log_file, stderr=err_file,
                    cwd=str(SCRIPT_DIR),
                    text=True,
                    bufsize=0,
                    env=_unbuffered_env(),
                    start_new_session=_supports_process_groups(),
                )
                exit_code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            _terminate_subprocess(process, "timeout")
            exit_code = 124

        if backend != "opencode" or attempt == attempts:
            break
        if exit_code == 0 and not session_has_transient_error(log_path):
            break
        print(f"opencode session attempt {attempt}/{attempts} hit transient error; retrying")

    duration_ms = int((time.monotonic() - start) * 1000)
    return exit_code, duration_ms


def spawn_agent_process(prompt_text: str, log_path: Path,
                        model: str | None = None, max_turns: int = 2500) -> tuple[subprocess.Popen, object]:
    """Start a long-lived agent process for multi-turn mode."""
    model = model or session_model()
    cmd = _agent_command(model, max_turns, prompt_text)
    log_file = open(log_path, "w")
    err_file = open(_err_path(log_path), "w")
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.DEVNULL,
        stdout=log_file,
        stderr=err_file,
        cwd=str(SCRIPT_DIR),
        text=True,
        bufsize=0,
        env=_unbuffered_env(),
        start_new_session=_supports_process_groups(),
    )
    return process, log_file
