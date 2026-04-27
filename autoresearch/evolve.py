#!/usr/bin/env python3
"""Evolution loop orchestrator — candidate selection, variant mutation, search scoring.

Replaces evolve.sh. Units 2-3 will fill in run_meta_agent(), cmd_run(), and
cmd_promote(); this module provides the entry point, argument parsing,
environment config, and preflight checks.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime
import os
import select
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import NoReturn

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

_HARNESS_DIR = SCRIPT_DIR / "harness"
if _HARNESS_DIR.is_dir() and str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))

import evolve_ops  # noqa: E402  (must come after sys.path setup)
import regen_program_docs  # noqa: E402  (must come after sys.path setup)

# Critique-prompt manifest is computed once at module load by importing
# the canonical session_evaluator. Variant clones get a snapshot of these
# hashes; layer1_validate later re-computes inside python3 -I and refuses
# to run any variant whose bundled manifest disagrees. R-#13.
import json  # noqa: E402

_REPO_ROOT = SCRIPT_DIR.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
from autoresearch.critique_manifest import compute_expected_hashes  # noqa: E402

ALL_LANES = ("core", "geo", "competitive", "monitoring", "storyboard")

META_AGENT_TIMEOUT = 1800  # 30 minutes, matching bash `timeout 1800`

# Mirrors harness/agent.py — OpenRouter upstream provider hiccups manifest as
# error events in the JSONL while the opencode subprocess exits 0. Retry the
# whole subprocess up to this many total attempts on detection. Operators can
# override via OPENCODE_MAX_RETRIES.
_OPENCODE_MAX_ATTEMPTS = max(1, int(os.environ.get("OPENCODE_MAX_RETRIES", "3")))

# Tracked Popen handle so the cleanup function can terminate it
# when SIGALRM fires — prevents orphaned agent with API keys.
_running_meta_agent: subprocess.Popen | None = None

# Tracked temp dirs and unsealed variant dir for cleanup on
# exit/signal/exception.
_temp_dirs: list[Path] = []
_unsealed_variant_dir: Path | None = None

# Claude backend: build env from scratch with exactly these keys.
_CLAUDE_ENV_KEYS = (
    "PATH", "HOME", "USER", "SHELL", "TERM", "LANG", "TMPDIR",
    "SSH_AUTH_SOCK", "ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN",
    "FREDDY_API_URL", "FREDDY_API_KEY", "OPENAI_API_KEY",
)

# Codex backend: remove these holdout keys from the inherited env.
_CODEX_HOLDOUT_KEYS = (
    "EVOLUTION_HOLDOUT_MANIFEST",
    "EVOLUTION_HOLDOUT_JSON",
    "EVOLUTION_PRIVATE_ARCHIVE_DIR",
)


# ---------------------------------------------------------------------------
# Subprocess helpers (follows evaluate_variant.py:400-473 pattern)
# ---------------------------------------------------------------------------


def _supports_process_groups() -> bool:
    """Check if the OS supports process groups (Unix-only)."""
    return hasattr(os, "setsid") and hasattr(os, "killpg")


def _terminate_process(
    process: subprocess.Popen, reason: str, grace_seconds: int = 10
) -> None:
    """SIGTERM -> wait -> SIGKILL. Follows evaluate_variant.py:404-419."""
    if process.poll() is not None:
        return
    print(f"  Stopping meta agent ({reason}).", file=sys.stderr)
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


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the argparse parser with run/promote subcommands."""
    parser = argparse.ArgumentParser(
        description="Evolution loop orchestrator for autoresearch.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # --- run subcommand ---
    run_parser = subparsers.add_parser("run", help="Run the evolution loop.")
    run_parser.add_argument(
        "--iterations", type=int, default=100, help="Max iterations (default 100)."
    )
    run_parser.add_argument(
        "--candidates-per-iteration",
        type=int,
        default=3,
        help="Candidates per iteration (default 3).",
    )
    run_parser.add_argument(
        "--archive-dir", type=str, default=None, help="Archive directory."
    )
    run_parser.add_argument(
        "--backend", type=str, default=None, help="Meta agent backend (claude|codex|opencode)."
    )
    run_parser.add_argument(
        "--model", type=str, default=None, help="Meta agent model."
    )
    run_parser.add_argument(
        "--max-turns", type=int, default=100, help="Max turns for meta agent (default 100)."
    )
    run_parser.add_argument(
        "--lane",
        type=str,
        default=os.environ.get("EVOLUTION_LANE", "core"),
        help="Evolution lane (default from EVOLUTION_LANE or 'core').",
    )

    # --- promote subcommand ---
    promote_parser = subparsers.add_parser("promote", help="Promote a variant.")
    promote_parser.add_argument(
        "--undo", action="store_true", default=False, help="Undo the last promotion."
    )
    promote_parser.add_argument(
        "variant_id", nargs="?", default=None, help="Variant ID to promote."
    )
    promote_parser.add_argument(
        "--archive-dir", type=str, default=None, help="Archive directory."
    )
    promote_parser.add_argument(
        "--lane",
        type=str,
        default=os.environ.get("EVOLUTION_LANE", "core"),
        help="Evolution lane (default from EVOLUTION_LANE or 'core').",
    )

    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse arguments from argv (or sys.argv if None)."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    return args


# ---------------------------------------------------------------------------
# Config dataclass
# ---------------------------------------------------------------------------


@dataclass
class EvolutionConfig:
    """Resolved configuration for an evolution run."""

    command: str
    script_dir: Path = field(default_factory=lambda: SCRIPT_DIR)
    repo_root: Path = field(default_factory=lambda: SCRIPT_DIR.parent)
    archive_dir: Path = field(default_factory=lambda: SCRIPT_DIR / "archive")
    lane: str = "core"
    iterations: int = 100
    candidates_per_iteration: int = 3
    max_turns: int = 100
    meta_backend: str = ""
    meta_model: str = ""

    # Search suite config (populated by load_search_config)
    search_suite_path: str = ""
    search_suite_id: str = ""
    search_eval_backend: str = ""
    search_eval_model: str = ""
    search_eval_reasoning: str = ""

    # Holdout
    require_holdout: bool = True

    # Codex-specific config
    codex_sandbox: str = "danger-full-access"
    codex_approval_policy: str = "never"
    codex_web_search: str = "disabled"
    codex_reasoning_effort: str = "high"

    # Derived paths
    cli_pythonpath: str = ""

    # Promote-specific
    promote_undo: bool = False
    command_arg: str | None = None


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------


def load_config(args: argparse.Namespace) -> EvolutionConfig:
    """Resolve all configuration from args, environment, and suite manifests."""
    repo_root = SCRIPT_DIR.parent

    # Archive dir: CLI flag > ARCHIVE_DIR env var > default
    cli_archive = getattr(args, "archive_dir", None)
    if cli_archive is not None:
        archive_dir = Path(cli_archive).resolve()
    elif os.environ.get("ARCHIVE_DIR"):
        archive_dir = Path(os.environ["ARCHIVE_DIR"]).resolve()
    else:
        archive_dir = SCRIPT_DIR / "archive"

    # Load .env defaults — only set keys that are NOT already in os.environ.
    for key, value in evolve_ops.load_repo_env_defaults(repo_root / ".env"):
        if key not in os.environ:
            os.environ[key] = value

    # Normalize lane — intercept "all" and "system" before calling
    # evolve_ops.normalize_lane (which delegates to lane_paths and
    # would reject "all" as unknown).
    raw_lane = getattr(args, "lane", "core") or "core"
    if raw_lane.strip().lower() in ("all", "system"):
        lane = "all"
    else:
        lane = evolve_ops.normalize_lane(raw_lane)

    # Meta backend: CLI flag > META_BACKEND env var > default (claude)
    meta_backend = getattr(args, "backend", None) or os.environ.get("META_BACKEND", "")
    if not meta_backend:
        meta_backend = "claude"
    meta_backend = meta_backend.lower()
    if meta_backend not in ("claude", "codex", "opencode"):
        print(f"ERROR: Unsupported meta backend '{meta_backend}' (must be claude, codex, or opencode)", file=sys.stderr)
        sys.exit(1)

    # Meta model: CLI flag > META_MODEL env var > backend-specific default
    meta_model = getattr(args, "model", None) or os.environ.get("META_MODEL", "")
    if not meta_model:
        if meta_backend == "claude":
            meta_model = "opus"
        elif meta_backend == "opencode":
            meta_model = os.environ.get(
                "AUTORESEARCH_OPENCODE_DEFAULT_MODEL",
                "openrouter/deepseek/deepseek-v4-pro",
            )
        else:
            meta_model = "gpt-5.4"  # codex

    # Codex config variables from env with defaults
    codex_sandbox = os.environ.get("AR_CODEX_SANDBOX",
                                   os.environ.get("CODEX_SANDBOX", "danger-full-access"))
    if codex_sandbox == "seatbelt":
        codex_sandbox = "workspace-write"
    codex_approval_policy = os.environ.get("CODEX_APPROVAL_POLICY", "never")
    codex_web_search = os.environ.get("CODEX_WEB_SEARCH", "disabled")
    codex_reasoning_effort = os.environ.get("CODEX_REASONING_EFFORT", "high")

    # CLI_PYTHONPATH — repo_root/cli prepended to existing PYTHONPATH
    existing_pythonpath = os.environ.get("PYTHONPATH", "")
    cli_pythonpath = str(repo_root / "cli")
    if existing_pythonpath:
        cli_pythonpath = cli_pythonpath + ":" + existing_pythonpath

    # Build config
    config = EvolutionConfig(
        command=args.command,
        script_dir=SCRIPT_DIR,
        repo_root=repo_root,
        archive_dir=archive_dir,
        lane=lane,
        meta_backend=meta_backend,
        meta_model=meta_model,
        codex_sandbox=codex_sandbox,
        codex_approval_policy=codex_approval_policy,
        codex_web_search=codex_web_search,
        codex_reasoning_effort=codex_reasoning_effort,
        cli_pythonpath=cli_pythonpath,
        require_holdout=True,
    )

    if args.command == "run":
        config.iterations = args.iterations
        config.candidates_per_iteration = args.candidates_per_iteration
        config.max_turns = args.max_turns

    if args.command == "promote":
        config.promote_undo = args.undo
        config.command_arg = args.variant_id

    # Early return for "all" lane — per-lane init happens in run_all_lanes()
    if lane == "all":
        return config

    # Initialize lane-specific config (search suite, lane heads, eval target)
    _init_lane_config(config)

    return config


def _init_lane_config(config: EvolutionConfig) -> None:
    """Initialize lane-specific config: search suite, lane heads, eval target env.

    Called once for single-lane execution, or per-lane inside run_all_lanes().
    """
    default_suite_path = os.environ.get(
        "EVOLUTION_SEARCH_SUITE",
        str(SCRIPT_DIR / "eval_suites" / "search-v1.json"),
    )
    suite_config = evolve_ops.load_search_config(default_suite_path, config.lane)
    config.search_suite_path = suite_config[0]
    config.search_suite_id = suite_config[1]
    config.search_eval_backend = suite_config[2]
    config.search_eval_model = suite_config[3]
    config.search_eval_reasoning = suite_config[4]

    # F-b-5-5: surface "missing archive dir" as a clean ERROR line on stderr,
    # matching the contract every other startup-validation failure uses
    # (e.g. EVOLUTION_EVAL_BACKEND below). Without this, ensure_lane_heads
    # raises a bare FileNotFoundError with a multi-line traceback and exits 1
    # — same exit code as a clean error but visually noisy, and inconsistent
    # with the sibling stderr-line contract used elsewhere in this module.
    if not config.archive_dir.exists():
        print(
            f"ERROR: --archive-dir does not exist: {config.archive_dir}",
            file=sys.stderr,
        )
        sys.exit(1)

    evolve_ops.ensure_lane_heads(config.archive_dir)

    if not (config.command == "promote" and config.promote_undo):
        configure_eval_target_env(config)


# ---------------------------------------------------------------------------
# Eval target environment validation
# ---------------------------------------------------------------------------


def configure_eval_target_env(config: EvolutionConfig) -> None:
    """Validate and export eval target environment variables."""
    eval_backend = os.environ.get("EVOLUTION_EVAL_BACKEND", "")
    eval_model = os.environ.get("EVOLUTION_EVAL_MODEL", "")

    if not eval_backend:
        print("ERROR: EVOLUTION_EVAL_BACKEND must be set explicitly.", file=sys.stderr)
        sys.exit(1)
    if not eval_model:
        print("ERROR: EVOLUTION_EVAL_MODEL must be set explicitly.", file=sys.stderr)
        sys.exit(1)

    eval_backend = eval_backend.lower()

    # Cross-check against suite config
    if config.search_eval_backend and eval_backend != config.search_eval_backend:
        print(
            f"ERROR: EVOLUTION_EVAL_BACKEND={eval_backend} does not match "
            f"suite backend {config.search_eval_backend}.",
            file=sys.stderr,
        )
        sys.exit(1)
    if config.search_eval_model and eval_model != config.search_eval_model:
        print(
            f"ERROR: EVOLUTION_EVAL_MODEL={eval_model} does not match "
            f"suite model {config.search_eval_model}.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Set reasoning effort from suite if not already set
    eval_reasoning = os.environ.get("EVOLUTION_EVAL_REASONING_EFFORT", "")
    if not eval_reasoning and config.search_eval_reasoning:
        eval_reasoning = config.search_eval_reasoning

    # Export to os.environ
    os.environ["EVOLUTION_EVAL_BACKEND"] = eval_backend
    os.environ["EVOLUTION_EVAL_MODEL"] = eval_model
    if eval_reasoning:
        os.environ["EVOLUTION_EVAL_REASONING_EFFORT"] = eval_reasoning


# ---------------------------------------------------------------------------
# Preflight checks
# ---------------------------------------------------------------------------


def preflight_checks(config: EvolutionConfig) -> None:
    """Verify prerequisites and print config summary."""
    # Check freddy is on PATH
    if not shutil.which("freddy"):
        print("ERROR: freddy CLI not found", file=sys.stderr)
        sys.exit(1)

    # Diagnostic: verify freddy evaluate variant works
    diag = subprocess.run(
        ["freddy", "evaluate", "variant", "--help"],
        capture_output=True,
        env={**os.environ, "PYTHONPATH": config.cli_pythonpath},
    )
    if diag.returncode != 0:
        print("WARNING: freddy evaluate variant --help failed", file=sys.stderr)

    # Check meta backend CLI is on PATH
    if not shutil.which(config.meta_backend):
        print(f"ERROR: {config.meta_backend} CLI not found", file=sys.stderr)
        sys.exit(1)

    # Create archive dir
    config.archive_dir.mkdir(parents=True, exist_ok=True)

    # Config summary
    print(f"Meta agent backend: {config.meta_backend}")
    print(f"Meta agent model:   {config.meta_model}")
    print(f"Eval backend:       {os.environ.get('EVOLUTION_EVAL_BACKEND', '')}")
    print(f"Eval model:         {os.environ.get('EVOLUTION_EVAL_MODEL', '')}")
    eval_reasoning = os.environ.get("EVOLUTION_EVAL_REASONING_EFFORT", "")
    if eval_reasoning:
        print(f"Eval reasoning:     {eval_reasoning}")
    print(f"Require holdout:    {str(config.require_holdout).lower()}")
    print(f"Candidates/iter:    {config.candidates_per_iteration}")

    # Codex sandbox warning
    if config.codex_sandbox == "danger-full-access":
        print("\u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510")
        print("\u2502  WARNING: CODEX_SANDBOX=danger-full-access               \u2502")
        print("\u2502  The meta agent has full host access. It can read, write, \u2502")
        print("\u2502  and execute anything on this machine.                    \u2502")
        print("\u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518")


# ---------------------------------------------------------------------------
# run_all_lanes
# ---------------------------------------------------------------------------


def run_all_lanes(config: EvolutionConfig, command_func) -> None:
    """Run a command across all lanes with per-lane error isolation.

    Each lane gets a full config initialization (search suite, lane heads,
    eval target env) and preflight — matching bash's behavior of re-invoking
    the script per lane.
    """
    for lane in ALL_LANES:
        print(f"=== Running lane={lane} ===")
        try:
            lane_config = dataclasses.replace(config, lane=lane)
            _init_lane_config(lane_config)
            preflight_checks(lane_config)
            command_func(lane_config)
        except Exception as exc:
            print(f"ERROR: lane={lane} failed: {exc}", file=sys.stderr)
            continue


# ---------------------------------------------------------------------------
# Command stubs (Units 2-3)
# ---------------------------------------------------------------------------


def _build_meta_env(config: EvolutionConfig, workdir: Path) -> dict[str, str]:
    """Build the environment dict for the meta agent subprocess.

    Claude: fresh env with exactly 11 allowlisted keys (security-critical).
    Codex: os.environ copy minus holdout keys (asymmetric trust model).
    OpenCode: same as codex (multi-provider routing requires arbitrary provider
    API keys — OPENROUTER_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY, etc. —
    that an explicit allowlist cannot enumerate without breaking on new providers).
    """
    if config.meta_backend == "claude":
        env: dict[str, str] = {}
        for key in _CLAUDE_ENV_KEYS:
            val = os.environ.get(key, "")
            if not val:
                # Reasonable defaults for display/locale vars
                defaults = {"TERM": "xterm", "LANG": "en_US.UTF-8", "TMPDIR": "/tmp"}
                val = defaults.get(key, "")
            env[key] = val
        env["PYTHONPATH"] = str(workdir)
    elif config.meta_backend in ("codex", "opencode"):
        env = os.environ.copy()
        for key in _CODEX_HOLDOUT_KEYS:
            env.pop(key, None)
        env["PYTHONPATH"] = str(workdir)
        if config.meta_backend == "opencode":
            config_path = _REPO_ROOT / "opencode.json"
            if config_path.is_file():
                env["OPENCODE_CONFIG"] = str(config_path)
    else:
        raise ValueError(f"Unknown meta backend: {config.meta_backend!r}")

    # Safety: env must never be None when reaching Popen — prevents
    # accidental full-env inheritance.
    assert env is not None, "env dict must not be None for subprocess"
    return env


def _build_meta_command(
    config: EvolutionConfig,
    workdir: Path,
    prompt_text: str | None = None,
) -> list[str]:
    """Build the command array for the meta agent subprocess.

    For backends that read prompt from stdin (claude with ``-p``; codex with a
    trailing ``"-"`` argument), ``prompt_text`` is ignored — caller passes
    prompt via stdin pipe. For opencode, ``prompt_text`` is appended as the
    trailing positional argv element because opencode reads prompt from argv,
    not stdin.
    """
    if config.meta_backend == "claude":
        return [
            "claude", "-p",
            "--model", config.meta_model,
            "--allowedTools", "Bash,Read,Write,Edit,Glob,Grep",
            "--max-turns", str(config.max_turns),
        ]
    if config.meta_backend == "codex":
        return [
            "codex", "exec",
            "--model", config.meta_model,
            "--sandbox", config.codex_sandbox,
            "--color", "never",
            "-c", f'approval_policy="{config.codex_approval_policy}"',
            "-c", f'model_reasoning_effort="{config.codex_reasoning_effort}"',
            "-c", f'web_search="{config.codex_web_search}"',
            "-C", str(workdir),
            "-",
        ]
    if config.meta_backend == "opencode":
        cmd = [
            "opencode", "run",
            "--dangerously-skip-permissions",
            "-m", config.meta_model,
            "--format", "json",
        ]
        if prompt_text is not None:
            cmd.append(prompt_text)
        return cmd
    raise ValueError(f"Unknown meta backend: {config.meta_backend!r}")


def _run_meta_agent_once(
    prompt_file: Path,
    workdir: Path,
    config: EvolutionConfig,
    log_file: Path | None = None,
) -> int:
    """Single meta-agent subprocess attempt — no retry. Caller wraps with retry."""
    global _running_meta_agent

    env = _build_meta_env(config, workdir)

    if config.meta_backend == "opencode":
        # opencode reads prompt from positional argv, not stdin. Read the
        # prompt file once into argv and pass DEVNULL to subprocess stdin.
        prompt_text = prompt_file.read_text()
        cmd = _build_meta_command(config, workdir, prompt_text=prompt_text)
        process = subprocess.Popen(
            cmd,
            env=env,
            cwd=str(workdir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=_supports_process_groups(),
        )
    else:
        # claude (with -p) and codex (with trailing "-") both read prompt
        # from stdin.
        cmd = _build_meta_command(config, workdir)
        stdin_handle = open(prompt_file, "rb")
        try:
            process = subprocess.Popen(
                cmd,
                env=env,
                cwd=str(workdir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=stdin_handle,
                start_new_session=_supports_process_groups(),
            )
        finally:
            stdin_handle.close()

    _running_meta_agent = process
    log_handle = None
    if log_file is not None:
        log_handle = open(log_file, "w")

    try:
        started = time.monotonic()
        fd = process.stdout.fileno()

        while True:
            elapsed = time.monotonic() - started
            remaining = META_AGENT_TIMEOUT - elapsed
            if remaining <= 0:
                _terminate_process(process, f"timeout ({META_AGENT_TIMEOUT}s)")
                break

            ready, _, _ = select.select([fd], [], [], min(remaining, 1.0))
            if ready:
                line = process.stdout.readline()
                if not line:
                    break  # EOF — process closed stdout
                decoded = line.decode("utf-8", errors="replace")
                sys.stdout.write(decoded)
                sys.stdout.flush()
                if log_handle is not None:
                    log_handle.write(decoded)
                    log_handle.flush()
            elif process.poll() is not None:
                # Process exited — drain remaining output
                for tail_line in process.stdout:
                    decoded = tail_line.decode("utf-8", errors="replace")
                    sys.stdout.write(decoded)
                    sys.stdout.flush()
                    if log_handle is not None:
                        log_handle.write(decoded)
                        log_handle.flush()
                break
    except BaseException:
        _terminate_process(process, "exception")
        raise
    finally:
        process.wait()
        _running_meta_agent = None
        if log_handle is not None:
            log_handle.close()

    return process.returncode


def run_meta_agent(
    prompt_file: Path,
    workdir: Path,
    config: EvolutionConfig,
    log_file: Path | None = None,
) -> int:
    """Run the meta agent. For opencode, retry on transient upstream errors.

    Uses select.select() for incremental line-by-line reads (ISSUE-5: avoids
    buffered stdout loss on kill) and time.monotonic() for timeout tracking.
    Returns the subprocess exit code.

    OpenCode-only retry: when the captured log contains rate_limit_exceeded,
    provider_overloaded, or upstream timeout markers, retry up to
    OPENCODE_MAX_RETRIES (default 3) times. claude/codex paths retry
    internally and are unwrapped. The log_file is truncated on each retry
    so it always reflects the final attempt — adopting the same trade-off
    harness/agent.py:run_agent_session makes.
    """
    # Import via direct path: autoresearch/harness/ is added to sys.path at
    # module init below so ``opencode_jsonl`` resolves to autoresearch's
    # helper, not the unrelated harness/ package at the repo root.
    from opencode_jsonl import session_has_transient_error  # noqa: E402

    attempts = _OPENCODE_MAX_ATTEMPTS if config.meta_backend == "opencode" else 1
    exit_code = 0
    for attempt in range(1, attempts + 1):
        exit_code = _run_meta_agent_once(prompt_file, workdir, config, log_file=log_file)
        if config.meta_backend != "opencode" or attempt == attempts:
            break
        # Without a log_file we can't detect transient JSONL errors —
        # only retry on non-zero exit (timeout, kill, etc.).
        if log_file is None:
            if exit_code == 0:
                break
        else:
            if exit_code == 0 and not session_has_transient_error(log_file):
                break
        print(f"meta agent opencode attempt {attempt}/{attempts} hit transient error (exit={exit_code}); retrying", file=sys.stderr)

    return exit_code


# ---------------------------------------------------------------------------
# Cleanup and signal handling
# ---------------------------------------------------------------------------


def _safe_rmtree(path: Path) -> None:
    """Remove a directory tree, handling macOS immutable flags."""
    if not path.is_dir():
        return
    if sys.platform == "darwin":
        subprocess.run(
            ["chflags", "-R", "nouchg", str(path)],
            capture_output=True,
        )
    try:
        shutil.rmtree(path)
    except OSError as exc:
        print(
            f"ERROR: cleanup failed to remove {path} ({exc})",
            file=sys.stderr,
        )


def cleanup() -> None:
    """Clean up temp dirs, unsealed variant dir, and running meta agent."""
    global _unsealed_variant_dir

    # 1. Terminate running meta agent if any.
    if _running_meta_agent is not None:
        _terminate_process(_running_meta_agent, "cleanup")

    # 2. Remove all tracked temp dirs.
    for d in list(_temp_dirs):
        _safe_rmtree(d)
    _temp_dirs.clear()

    # 3. Remove unsealed variant dir if it exists.
    if _unsealed_variant_dir is not None:
        _safe_rmtree(_unsealed_variant_dir)
        _unsealed_variant_dir = None


def _sigalrm_handler(signum: int, frame) -> None:
    """Handle SIGALRM — generation wall-time ceiling reached."""
    print(
        "FATAL: generation wall-time ceiling reached. Terminating.",
        file=sys.stderr,
    )
    raise SystemExit(1)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def refresh_archive(config: EvolutionConfig) -> None:
    """Refresh archive index via subprocess call to archive_index.py."""
    subprocess.run(
        [
            "python3",
            str(SCRIPT_DIR / "archive_index.py"),
            str(config.archive_dir),
            "--suite-manifest",
            config.search_suite_path,
        ],
        check=True,
    )


def _score_variant_search(
    config: EvolutionConfig,
    variant_dir: str,
    parent_id: str = "",
) -> None:
    """Score a variant on the search suite via subprocess to evaluate_variant.py."""
    cmd = [
        "python3",
        str(SCRIPT_DIR / "evaluate_variant.py"),
        variant_dir,
        str(config.archive_dir),
        "--mode", "search",
        "--lane", config.lane,
        "--search-suite", config.search_suite_path,
    ]
    if config.require_holdout:
        cmd.append("--require-holdout")

    env = os.environ.copy()
    env["EVOLUTION_PARENT_ID"] = parent_id
    env["EVOLUTION_LANE"] = config.lane
    env.setdefault("EVOLUTION_META_BACKEND", config.meta_backend)
    env.setdefault("EVOLUTION_META_MODEL", config.meta_model)

    subprocess.run(cmd, env=env, check=True)


def _run_holdout(config: EvolutionConfig, variant_dir: str) -> None:
    """Run holdout evaluation via subprocess to evaluate_variant.py."""
    env = os.environ.copy()
    env.setdefault("EVOLUTION_META_BACKEND", config.meta_backend)
    env.setdefault("EVOLUTION_META_MODEL", config.meta_model)

    subprocess.run(
        [
            "python3",
            str(SCRIPT_DIR / "evaluate_variant.py"),
            variant_dir,
            str(config.archive_dir),
            "--mode", "holdout",
            "--lane", config.lane,
            "--search-suite", config.search_suite_path,
        ],
        env=env,
        check=True,
    )


def _score_current(config: EvolutionConfig) -> None:
    """Score the current promoted variant."""
    current_id = evolve_ops.current_head_variant_id(
        str(config.archive_dir), config.lane
    )
    if not current_id:
        print("ERROR: No current head variant to score.", file=sys.stderr)
        sys.exit(1)
    current_dir = str(config.archive_dir / current_id)
    _score_variant_search(config, current_dir)


def ensure_baseline_seed(config: EvolutionConfig) -> None:
    """Ensure baseline is seeded — score current variant if needed."""
    if evolve_ops.baseline_seeded(
        str(config.archive_dir), config.search_suite_id, config.lane
    ):
        return
    print(
        f"Baseline is not measured for suite {config.search_suite_id}. "
        "Scoring current promoted variant..."
    )
    _score_current(config)


def _next_variant_id(archive_dir: Path) -> str:
    """Compute the next variant ID (v002, v003, ...) from existing v??? dirs."""
    existing = sorted(archive_dir.glob("v???"))
    if not existing:
        # No dirs → default to 1, then add 1 → v002 (matches bash
        # `10#${NEXT_NUM:-1} + 1`)
        return "v002"
    max_num = max(int(d.name[1:]) for d in existing)
    return f"v{max_num + 1:03d}"


def _do_finalize_step(config: EvolutionConfig) -> None:
    """Run holdout on frontier variants and promote the best (if configured)."""
    if not config.require_holdout:
        return
    if not evolve_ops.holdout_configured():
        print("Finalize step skipped: no holdout manifest configured.")
        return

    refresh_archive(config)

    finalists = evolve_ops.finalize_candidate_ids(
        str(config.archive_dir), config.search_suite_path, config.lane
    )
    if not finalists:
        print("No frontier finalists available for hidden holdout evaluation.")
        return

    holdout_suite = evolve_ops.holdout_suite_id(config.lane)
    print(
        f"Finalizing {len(finalists)} frontier variants "
        f"on hidden holdout ({holdout_suite})..."
    )

    for finalist_id in finalists:
        print(f"Finalizing {finalist_id}...")
        _run_holdout(config, str(config.archive_dir / finalist_id))

    shortlist_path = evolve_ops.write_finalized_shortlist(
        str(config.archive_dir), holdout_suite, config.lane, finalists
    )
    if shortlist_path:
        print(f"Private finalized shortlist written to {shortlist_path}")

    best_id = evolve_ops.best_finalized_variant(
        str(config.archive_dir), holdout_suite, config.lane, finalists
    )
    # Capture prior head BEFORE set_current_head overwrites it.
    prior_head = evolve_ops.current_head_variant_id(
        str(config.archive_dir), config.lane,
    )
    if best_id:
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        evolve_ops.mark_promoted(str(config.archive_dir), best_id, timestamp)
        evolve_ops.set_current_head(str(config.archive_dir), config.lane, best_id)
        refresh_archive(config)
        print(f"Promoted best finalized candidate {best_id} for lane={config.lane}")
        _record_head_and_check_rollback(config, best_id, timestamp, prior_head)
    else:
        print("No finalized candidate beat the current promoted baseline.")


def _record_head_and_check_rollback(
    config: EvolutionConfig, head_id: str, promoted_at: str,
    prior_head: str | None = None,
) -> None:
    """Plan B Phase 6 Step 6 + acceptance-criterion #13 wiring:
      - emit kind="head_score" for the new head (rollback agent input)
      - emit kind="saturation_cycle" per public fixture beaten/lost against prior head
      - ask the rollback agent whether to revert

    Failures here must not break the finalize loop — emit a stderr warning
    and continue. Each bookkeeping call is wrapped independently so one
    failure doesn't skip the others.
    """
    import evaluate_variant

    try:
        latest = evolve_ops._load_latest_lineage(str(config.archive_dir))
        entry = latest.get(head_id)
        if isinstance(entry, dict):
            public_score = evaluate_variant._objective_score_from_scores(
                entry.get("scores"), config.lane,
            )
            holdout_score = evolve_ops._holdout_composite(entry)
            evolve_ops.record_head_score(
                lane=config.lane, head_id=head_id,
                public_score=float(public_score),
                holdout_score=holdout_score,
                promoted_at=promoted_at,
            )
        else:
            print(
                f"record_head_score: no lineage entry for {head_id!r}; skipping",
                file=sys.stderr,
            )
    except Exception as exc:  # noqa: BLE001
        print(
            f"⚠️  record_head_score failed ({type(exc).__name__}): {exc}",
            file=sys.stderr,
        )

    try:
        evolve_ops.emit_saturation_cycle_events(
            str(config.archive_dir), config.lane, head_id, prior_head,
        )
    except Exception as exc:  # noqa: BLE001
        print(
            f"⚠️  emit_saturation_cycle_events failed ({type(exc).__name__}): {exc}",
            file=sys.stderr,
        )

    try:
        evolve_ops.check_and_rollback_regressions(str(config.archive_dir), config.lane)
    except Exception as exc:  # noqa: BLE001
        print(
            f"⚠️  check_and_rollback_regressions failed ({type(exc).__name__}): {exc}",
            file=sys.stderr,
        )


# ---------------------------------------------------------------------------
# cmd_run — generation loop
# ---------------------------------------------------------------------------


def cmd_run(config: EvolutionConfig) -> None:
    """Execute the evolution run loop."""
    global _unsealed_variant_dir

    ensure_baseline_seed(config)
    refresh_archive(config)
    print("Pre-flight OK.")

    # Generation ceiling: signal.alarm fires SIGALRM after
    # MAX_GENERATION_SECONDS.
    max_generation_seconds = int(
        os.environ.get("MAX_GENERATION_SECONDS", "7200")
    )
    old_handler = signal.signal(signal.SIGALRM, _sigalrm_handler)
    signal.alarm(max_generation_seconds)

    max_generation = config.iterations * config.candidates_per_iteration

    try:
        from compute_metrics import record_generation

        cohort_variant_ids: dict[int, list[str]] = {}

        for gen in range(1, max_generation + 1):
            print(f"=== Generation {gen}/{max_generation} [lane={config.lane}] ===")

            cohort_id = (gen - 1) // max(config.candidates_per_iteration, 1)
            os.environ["EVOLUTION_COHORT_ID"] = str(cohort_id)

            refresh_archive(config)

            # Select parent (R-#29: agent picks + emits rationale; no sigmoid fallback)
            from select_parent import select_parent

            snapshot_parent, selection_rationale = select_parent(
                str(config.archive_dir),
                config.search_suite_id,
                config.lane,
                return_rationale=True,
            )
            parent_id = Path(snapshot_parent).name
            parent = config.archive_dir / parent_id
            if selection_rationale:
                os.environ["EVOLUTION_SELECTION_RATIONALE"] = selection_rationale
            else:
                os.environ.pop("EVOLUTION_SELECTION_RATIONALE", None)
            print(f"Parent: {parent_id} (lane={config.lane})")
            if selection_rationale:
                print(f"Selection rationale: {selection_rationale}")

            # Next variant ID
            variant_id = _next_variant_id(config.archive_dir)
            variant_dir = config.archive_dir / variant_id
            shutil.copytree(str(parent), str(variant_dir))
            _unsealed_variant_dir = variant_dir
            shutil.rmtree(variant_dir / "sessions", ignore_errors=True)
            (variant_dir / "sessions").mkdir(parents=True, exist_ok=True)
            print(f"Cloned {parent_id} -> {variant_id}")

            # Regenerate structural-validator doc sections from structural.py
            # so program docs never drift from the code (R-#12). Runs on
            # the cloned variant's programs/ dir before the meta agent sees
            # any of the files. runtime_bootstrap.py does NOT call this —
            # it execs per session and would fire regen inside the frozen
            # variant (see plan Unit 2).
            programs_dir = variant_dir / "programs"
            if programs_dir.is_dir():
                regen_program_docs.regen(programs_dir)

            # Snapshot the critique-prompt SHA256 manifest into the variant
            # at clone time. layer1_validate re-computes hashes inside a
            # python3 -I subprocess and refuses to run if the bundled
            # manifest doesn't match what the freshly imported symbols
            # produce. Converts the honor-system note in meta.md into a
            # gated invariant. R-#13.
            manifest_path = variant_dir / "critique_manifest.json"
            manifest_path.write_text(
                json.dumps(compute_expected_hashes(), indent=2, sort_keys=True),
                encoding="utf-8",
            )

            # Prepare meta workspace
            meta_workspace_root = Path(tempfile.mkdtemp())
            _temp_dirs.append(meta_workspace_root)
            meta_archive_root, meta_variant_dir = evolve_ops.prepare_meta_workspace(
                str(config.archive_dir),
                variant_id,
                str(meta_workspace_root),
                config.lane,
            )
            evolve_ops.write_lane_context(meta_archive_root, config.lane)

            # Resolve eval digest and parent sessions for template
            eval_digest_path = ""
            parent_sessions_path = ""
            if parent_id:
                digest = Path(meta_archive_root) / parent_id / "eval_digest.md"
                if digest.is_file():
                    eval_digest_path = str(digest)
                sessions = Path(meta_archive_root) / parent_id / "sessions"
                if sessions.is_dir():
                    parent_sessions_path = str(sessions)

            # Render meta template (5 sed placeholders)
            meta_template = Path(meta_variant_dir) / "meta.md"
            rendered = meta_template.read_text()
            rendered = rendered.replace("{archive_path}", meta_archive_root)
            rendered = rendered.replace(
                "{iterations_remaining}", str(max_generation - gen)
            )
            rendered = rendered.replace("{lane}", config.lane)
            rendered = rendered.replace(
                "{eval_digest_path}",
                eval_digest_path or "No eval digest available for parent.",
            )
            rendered = rendered.replace(
                "{parent_sessions_path}",
                parent_sessions_path or "No parent sessions available.",
            )

            rendered_fd, rendered_path_str = tempfile.mkstemp(suffix=".md")
            os.close(rendered_fd)
            rendered_path = Path(rendered_path_str)
            rendered_path.write_text(rendered)

            # Run meta agent
            meta_exit = run_meta_agent(
                rendered_path,
                Path(meta_variant_dir),
                config,
                log_file=variant_dir / "meta-session.log",
            )
            rendered_path.unlink(missing_ok=True)
            print(f"Meta agent exit code: {meta_exit}")

            # Sync workspace back
            evolve_ops.sync_meta_workspace(
                meta_variant_dir, str(variant_dir), config.lane
            )
            shutil.rmtree(meta_workspace_root, ignore_errors=True)
            if meta_workspace_root in _temp_dirs:
                _temp_dirs.remove(meta_workspace_root)

            # Pareto-constraint critique agent (R-#15, soft-review only).
            # Reads (old, new) pair of programs/<domain>-session.md and
            # appends an advisory verdict to variant_dir/critic_reviews.md.
            # Never rejects — just logs PRESCRIPTION vs DESCRIPTION drift
            # for operator eyeballing. Env escape:
            # EVOLVE_SKIP_PRESCRIPTION_CRITIC=1.
            if os.environ.get("EVOLVE_SKIP_PRESCRIPTION_CRITIC") != "1":
                try:
                    from program_prescription_critic import critique_all_programs

                    critique_all_programs(
                        parent_dir=parent,
                        variant_dir=variant_dir,
                        lane=config.lane,
                    )
                except Exception as exc:  # noqa: BLE001 — never block evolution
                    print(
                        f"[evolve] WARN: program_prescription_critic failed: {exc}",
                        file=sys.stderr,
                    )

            # Score variant
            _score_variant_search(config, str(variant_dir), parent_id)

            # Check lineage.  Discarded variants don't enter the cohort row
            # (they have no scores.json to aggregate), but the cohort still
            # closes on its gen-boundary so observability survives the discard.
            discarded = not evolve_ops.variant_in_lineage(
                str(config.archive_dir), variant_id
            )
            if discarded:
                print(f"Variant {variant_id} was discarded before archival.")
                _unsealed_variant_dir = None
                _safe_rmtree(variant_dir)
            else:
                _unsealed_variant_dir = None
                refresh_archive(config)
                cohort_variant_ids.setdefault(cohort_id, []).append(variant_id)

            # Fix 8 + 9: emit the cohort metrics row on the gen boundary
            # regardless of whether THIS variant was discarded.  Skipping the
            # emission when the boundary variant fails loses observability
            # for every prior variant that did archive in this cohort.
            if gen % max(config.candidates_per_iteration, 1) == 0:
                try:
                    record_generation(
                        lane=config.lane,
                        gen_id=cohort_id,
                        variant_ids=cohort_variant_ids.get(cohort_id, []),
                    )
                except Exception as exc:
                    print(
                        f"warning: compute_metrics failed for cohort {cohort_id}: {exc}",
                        file=sys.stderr,
                    )

            if discarded:
                continue

        # Finalize step after loop completes
        _do_finalize_step(config)
        print(f"Evolution complete. {max_generation} generations.")

    finally:
        signal.alarm(0)  # Cancel pending alarm
        signal.signal(signal.SIGALRM, old_handler)
        cleanup()


# ---------------------------------------------------------------------------
# cmd_promote — promotion / rollback
# ---------------------------------------------------------------------------


def cmd_promote(config: EvolutionConfig) -> None:
    """Execute the promote command."""
    archive_dir = str(config.archive_dir)

    if config.promote_undo:
        if config.command_arg:
            print("Usage: evolve.py promote --undo", file=sys.stderr)
            sys.exit(1)
        prev = evolve_ops.previous_promoted_variant(archive_dir, config.lane)
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        evolve_ops.mark_promoted(archive_dir, prev, timestamp)
        evolve_ops.set_current_head(archive_dir, config.lane, prev)
        refresh_archive(config)
        print(f"Rolled back lane={config.lane} to {prev}")
        return

    if config.require_holdout:
        if config.command_arg:
            print("Usage: evolve.py promote", file=sys.stderr)
            sys.exit(1)
        if not evolve_ops.holdout_configured():
            print(
                "ERROR: Hidden holdout is required for promotion, but no "
                "holdout manifest is configured.",
                file=sys.stderr,
            )
            sys.exit(1)
        holdout_suite = evolve_ops.holdout_suite_id(config.lane)
        variant_id = evolve_ops.best_finalized_variant(
            archive_dir, holdout_suite, config.lane
        )
        if not variant_id:
            print(
                f"ERROR: No promotable finalized candidate is available "
                f"for suite {holdout_suite}.",
                file=sys.stderr,
            )
            sys.exit(1)
    else:
        variant_id = config.command_arg
        if not variant_id:
            print(
                "Usage: evolve.py promote <variant_id>", file=sys.stderr
            )
            sys.exit(1)
        if not (config.archive_dir / variant_id).is_dir():
            print(
                f"ERROR: {config.archive_dir / variant_id} not found",
                file=sys.stderr,
            )
            sys.exit(1)
        if not evolve_ops.variant_has_search_metrics(
            archive_dir, variant_id, config.lane
        ):
            print(
                f"ERROR: {variant_id} has not been search-scored and "
                "cannot be promoted.",
                file=sys.stderr,
            )
            sys.exit(1)
        if not evolve_ops.is_promotable(archive_dir, variant_id, config.lane):
            reason = evolve_ops.promotion_reason(archive_dir, variant_id)
            print(
                f"ERROR: {variant_id} is not eligible for promotion. "
                f"Current status: {reason or 'unknown'}.",
                file=sys.stderr,
            )
            sys.exit(1)

    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    evolve_ops.mark_promoted(archive_dir, variant_id, timestamp)
    evolve_ops.set_current_head(archive_dir, config.lane, variant_id)
    refresh_archive(config)
    print(f"Promoted {variant_id} for lane={config.lane}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Main entry point."""
    args = parse_args()
    config = load_config(args)

    # Dispatch --lane all
    if config.lane == "all":
        if config.command == "run":
            run_all_lanes(config, cmd_run)
        elif config.command == "promote":
            run_all_lanes(config, cmd_promote)
        return

    preflight_checks(config)

    if config.command == "run":
        cmd_run(config)
    elif config.command == "promote":
        cmd_promote(config)


if __name__ == "__main__":
    main()
