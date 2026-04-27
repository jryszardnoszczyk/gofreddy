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
    children; codex/claude wrappers also observe the var."""
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    return env


def _err_path(log_path: Path) -> Path:
    return log_path.with_suffix(log_path.suffix + ".err") if log_path.suffix else log_path.with_suffix(".err")


def run_agent_session(prompt_text: str, timeout: int, log_path: Path,
                      model: str | None = None, max_turns: int = FRESH_MAX_TURNS) -> tuple[int, int]:
    """Run the configured agent via stdin. Returns (exit_code, duration_ms)."""
    start = time.monotonic()
    model = model or session_model()
    cmd = _agent_command(model, max_turns, prompt_text)
    err_path = _err_path(log_path)
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
