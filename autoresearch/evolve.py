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
import uuid
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
from sessions import SessionsFile  # noqa: E402

# Critique-prompt manifest is computed once at module load by importing
# the canonical session_evaluator. Variant clones get a snapshot of these
# hashes; layer1_validate later re-computes inside python3 -I and refuses
# to run any variant whose bundled manifest disagrees. R-#13.
import json  # noqa: E402

_REPO_ROOT = SCRIPT_DIR.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
from autoresearch.critique_manifest import compute_expected_hashes  # noqa: E402

from concurrency import parallel_for  # noqa: E402  (bare import keeps singleton coherent with tests)
from lane_registry import LANES as _LANE_SPECS, all_lane_names  # noqa: E402  (must come after sys.path setup)

META_AGENT_TIMEOUT = 1800  # 30 minutes, matching bash `timeout 1800`

# Tracked Popen handle so the cleanup function can terminate it
# when SIGALRM fires — prevents orphaned agent with API keys.
_running_meta_agent: subprocess.Popen | None = None

# Tracked temp dirs and unsealed variant dir for cleanup on
# exit/signal/exception.
_temp_dirs: list[Path] = []

# Claude backend: build env from scratch with exactly these keys.
# EVOLUTION_SELECTION_RATIONALE is set by _select_parent_deterministic
# and exported via env so the claude meta-agent sees why its parent
# was selected.
_CLAUDE_ENV_KEYS = (
    "PATH", "HOME", "USER", "SHELL", "TERM", "LANG", "TMPDIR",
    "SSH_AUTH_SOCK", "ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN",
    "FREDDY_API_URL", "FREDDY_API_KEY", "OPENAI_API_KEY",
    "EVOLUTION_SELECTION_RATIONALE",
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


def _critic_infra_failures(critic_results: dict) -> dict:
    """Return the subset of critic results whose verdict is ``'error'``.

    A2 (plan 2026-05-06-001): the upstream loop discards variants when ANY
    domain's critic infra-failed (subprocess crash, timeout, malformed
    output, missing CLI), so this predicate is the load-bearing gate.
    Extracted for unit-testability — earlier inline form had no coverage
    and a typo regression (e.g. ``status`` instead of ``verdict``) would
    silently let contaminated variants through.

    Non-dict values in ``critic_results`` are tolerated and skipped — the
    caller's outer ``except`` synthesizes a sentinel ``_uncaught`` entry,
    but a defensive predicate shouldn't crash on legitimate-but-malformed
    domain payloads either.
    """
    return {
        domain: result
        for domain, result in critic_results.items()
        if isinstance(result, dict) and result.get("verdict") == "error"
    }


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
        default=1,
        help=(
            "DEPRECATED. Sequential evolution since Plan B U1 — this arg is "
            "ignored. Each iteration produces exactly one variant. Pass "
            "--iterations N to control total generations."
        ),
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
        "--force-undo",
        action="store_true",
        default=False,
        help=(
            "DEPRECATED NO-OP. Preserved for backward compat with operator "
            "scripts that pass this flag. Since commit f39a7de3 (2026-05-06), "
            "the is_promotable LLM gate is no longer consulted on --undo: "
            "previous_promoted_variant filters lineage to entries with "
            "promoted_at set, and that stored evidence IS the gate. Passing "
            "or omitting --force-undo produces identical behavior. Removed "
            "with v1 in Plan B U14."
        ),
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
    candidates_per_iteration: int = 1
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
    force_undo: bool = False
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
        try:
            lane = evolve_ops.normalize_lane(raw_lane)
        except ValueError:
            from lane_paths import LANES
            valid = ", ".join(LANES)
            print(
                f"ERROR: Unknown lane '{raw_lane}' (valid lanes: {valid})",
                file=sys.stderr,
            )
            sys.exit(1)

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
            meta_model = "gpt-5.5"  # codex

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
        # --candidates-per-iteration is deprecated (Plan B U1); ignore the
        # CLI value and force 1 so any operator script still passing the
        # arg gets sequential evolution semantics rather than silently
        # multiplying iteration count by stale CLI arg.
        if args.candidates_per_iteration != 1:
            print(
                f"WARNING: --candidates-per-iteration={args.candidates_per_iteration} "
                "ignored (deprecated since Plan B U1; sequential evolution only). "
                "Pass --iterations N to control total generations.",
                file=sys.stderr,
            )
        config.candidates_per_iteration = 1
        config.max_turns = args.max_turns

    if args.command == "promote":
        config.promote_undo = args.undo
        config.force_undo = getattr(args, "force_undo", False)
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

    # Validate the holdout suite's eval_target against the same env.
    # Catches the v8-class failure where search-scoring runs successfully
    # then finalize crashes 30+ minutes later because holdout-v1.json
    # declares a different backend/model. Skipped when holdout isn't
    # configured (env var absent) — that's a legitimate run mode.
    if os.environ.get("EVOLUTION_HOLDOUT_MANIFEST", "").strip():
        try:
            import evaluate_variant  # noqa: E402  local import: heavy module
            holdout_manifest = evaluate_variant._load_holdout_manifest(
                os.environ.copy(), config.lane,
            )
        except Exception as exc:  # noqa: BLE001
            print(
                f"ERROR: failed to load holdout manifest "
                f"(EVOLUTION_HOLDOUT_MANIFEST={os.environ.get('EVOLUTION_HOLDOUT_MANIFEST')!r}): {exc}",
                file=sys.stderr,
            )
            sys.exit(1)
        if holdout_manifest is not None:
            try:
                evaluate_variant._require_eval_target(os.environ.copy(), holdout_manifest)
            except RuntimeError as exc:
                print(
                    f"ERROR: holdout suite eval_target mismatch: {exc}\n"
                    f"  Update EVOLUTION_EVAL_BACKEND/EVOLUTION_EVAL_MODEL or "
                    f"the holdout manifest at "
                    f"{os.environ.get('EVOLUTION_HOLDOUT_MANIFEST')}",
                    file=sys.stderr,
                )
                sys.exit(1)


# ---------------------------------------------------------------------------
# Preflight checks
# ---------------------------------------------------------------------------


_AUTH_PROBE_TIMEOUT_SECONDS = 30


def _backend_auth_probe(backend: str, model: str, env: dict[str, str]) -> tuple[bool, str]:
    """Send a one-token prompt to the backend; return (ok, diagnostic_text).

    Tests that the backend CLI is on PATH AND authenticated AND able to
    return a non-empty response, all in ~5-15s. Catches the v6-class silent
    failure where ``shutil.which`` finds the binary but auth is missing.

    Used at preflight only. Probes both meta and eval backends with their
    own configured env so they can have different auth (meta=claude,
    eval=codex is a common pairing).
    """
    if backend == "claude":
        cmd = ["claude", "-p", "--model", model, "--max-turns", "1", "ok"]
        stdin_input: bytes | None = None
    elif backend == "codex":
        cmd = ["codex", "exec", "--model", model, "--sandbox", "read-only",
               "--color", "never", "-c", 'approval_policy="never"', "-"]
        stdin_input = b"reply with the single word: ok"
    elif backend == "opencode":
        cmd = ["opencode", "run", "--dangerously-skip-permissions",
               "-m", model, "--format", "json", "ok"]
        stdin_input = None
    else:
        return False, f"unknown backend {backend!r}"

    # opencode discovers its config by walking up to the nearest .git;
    # subprocess.run with a curated env may not preserve cwd context, so
    # explicitly pin OPENCODE_CONFIG when probing opencode. Mirrors the
    # _build_meta_env opencode handling and harness/agent.py:_unbuffered_env.
    if backend == "opencode" and "OPENCODE_CONFIG" not in env:
        config_path = _REPO_ROOT / "opencode.json"
        if config_path.is_file():
            env = {**env, "OPENCODE_CONFIG": str(config_path)}

    try:
        proc = subprocess.run(
            cmd, input=stdin_input,
            capture_output=True, env=env,
            timeout=_AUTH_PROBE_TIMEOUT_SECONDS, check=False,
        )
    except subprocess.TimeoutExpired:
        return False, f"timeout after {_AUTH_PROBE_TIMEOUT_SECONDS}s"
    except FileNotFoundError:
        return False, f"{backend} CLI not on PATH"

    if proc.returncode != 0:
        stderr_preview = proc.stderr.decode("utf-8", errors="replace")[:300].strip()
        return False, f"exit={proc.returncode} stderr={stderr_preview!r}"
    if not proc.stdout.strip():
        return False, f"empty stdout (likely auth failure — claude/codex shell out silently when not logged in)"
    # Codex credit-exhaustion fingerprint: exit 0 + 3-5s wall + stdout
    # contains "null" (last_agent_message) + sometimes a rate-limit
    # marker. Detected during Apr 27 evolution where 3 judge calls
    # silently produced null-output sessions that the harness treated
    # as score=0. Auth probe shipped 2026-04-29 missed this case.
    if backend == "codex":
        stdout_lower = proc.stdout.decode("utf-8", errors="replace").lower()
        if (
            "credits.has_credits: false" in stdout_lower
            or "credit limit" in stdout_lower
            or "rate_limit_exceeded" in stdout_lower
            or "no credits" in stdout_lower
            or "out of credits" in stdout_lower
        ):
            return False, (
                "codex returned a credit-exhaustion / rate-limit signal. "
                "Top up subscription credits or switch backend before launching."
            )
        # Fingerprint: 3-5s wall + 'null' as the last assistant message.
        # Codex's normal "ok" response is ~10+ tokens of actual text; a
        # null message means the model never produced output despite
        # reaching task_complete cleanly. Match both the structured-log
        # form (``"last_agent_message": null``) and the plain-text
        # CLI-summary form (``last_agent_message: null``).
        import re as _re_local
        if _re_local.search(r'last_agent_message["\s]*:\s*null', stdout_lower):
            return False, (
                "codex returned task_complete with null message — "
                "likely credit exhaustion, quota, or model unavailability. "
                "Check `codex login` status and subscription credits."
            )
    return True, "ok"


def _smoke_test_backend_auth(config: EvolutionConfig) -> None:
    """Probe meta + eval backends; abort cleanly if either is unreachable.

    Mirrors harness/preflight.py:_check_gh_auth's actionable-error pattern
    (subprocess.run with timeout + check=False, then explicit error message
    on failure). Suggests the most-likely fix in the diagnostic.
    """
    meta_env = _build_meta_env(config, config.archive_dir)
    ok, diag = _backend_auth_probe(config.meta_backend, config.meta_model, meta_env)
    if not ok:
        _suggest = {
            "claude": "Run `claude` interactively once to authenticate, or set CLAUDE_CODE_OAUTH_TOKEN.",
            "codex":  "Run `codex login` to authenticate.",
            "opencode": "Run `opencode auth login` and verify ~/.local/share/opencode/auth.json exists.",
        }.get(config.meta_backend, "")
        print(
            f"ERROR: meta backend auth probe failed ({config.meta_backend}/"
            f"{config.meta_model}): {diag}\n  Suggestion: {_suggest}",
            file=sys.stderr,
        )
        sys.exit(1)
    print(f"Auth smoke test passed: {config.meta_backend}/{config.meta_model} (meta)")

    # Eval backend may differ from meta. Skip when eval backend isn't
    # configured (yet) — _init_lane_config sets these; in the "all" lane
    # path they're set per-lane so this preflight runs after that.
    eval_backend = os.environ.get("EVOLUTION_EVAL_BACKEND", "").strip().lower()
    eval_model = os.environ.get("EVOLUTION_EVAL_MODEL", "").strip()
    if not eval_backend or not eval_model:
        return
    if eval_backend == config.meta_backend and eval_model == config.meta_model:
        return  # same probe; already covered above
    # Use the runner-style env for the eval probe (full os.environ.copy()
    # mirrors what _runner_env hands the per-fixture spawn).
    eval_env = os.environ.copy()
    ok, diag = _backend_auth_probe(eval_backend, eval_model, eval_env)
    if not ok:
        _suggest = {
            "claude": "Run `claude` interactively once to authenticate, or set CLAUDE_CODE_OAUTH_TOKEN.",
            "codex":  "Run `codex login` to authenticate.",
            "opencode": "Run `opencode auth login` and verify ~/.local/share/opencode/auth.json exists.",
        }.get(eval_backend, "")
        print(
            f"ERROR: eval backend auth probe failed ({eval_backend}/{eval_model}): "
            f"{diag}\n  Suggestion: {_suggest}",
            file=sys.stderr,
        )
        sys.exit(1)
    print(f"Auth smoke test passed: {eval_backend}/{eval_model} (eval)")


def _smoke_test_judge_auth() -> None:
    """P0-D: Probe the evolution-judge endpoint with the configured token
    so empty/expired tokens fail at preflight, not after holdout has burned
    real time waiting for 401 retries.

    Reads EVOLUTION_JUDGE_URL + EVOLUTION_INVOKE_TOKEN. Sends a
    POST /invoke/score with a minimal payload — we expect a 200, 422
    (validation), or 4xx-other (any 4xx that's NOT 401 means the token
    is valid and the service is reachable). 401 → token bad.
    Connection refused / timeout → service down."""
    judge_url = os.environ.get("EVOLUTION_JUDGE_URL", "").strip()
    token = os.environ.get("EVOLUTION_INVOKE_TOKEN", "").strip()
    if not judge_url:
        print(
            "ERROR: EVOLUTION_JUDGE_URL is unset but EVOLUTION_HOLDOUT_MANIFEST "
            "is set — finalize will need the evolution judge. Set "
            "EVOLUTION_JUDGE_URL (e.g. http://localhost:7200) or unset the "
            "holdout manifest to run search-only.",
            file=sys.stderr,
        )
        sys.exit(1)
    if not token:
        print(
            "ERROR: EVOLUTION_INVOKE_TOKEN is unset/empty but holdout manifest "
            "is configured. The evolution judge will return 401 on every call. "
            "Source ~/.config/gofreddy/judges.env or set the token explicitly.",
            file=sys.stderr,
        )
        sys.exit(1)
    try:
        import httpx  # type: ignore  # noqa: E402
        # Probe a deliberately-nonexistent endpoint with the token. The
        # judge's _require_token middleware runs BEFORE the route handler
        # for valid endpoints, but for a missing path FastAPI returns 404
        # without invoking any handler — bypassing the slow scoring path.
        # This catches:
        #   - service down → ConnectError (caught below)
        #   - service up + bad token → still 404 (auth never checked, but
        #     that's fine because the actual scoring call WILL check)
        #   - service up + good token → 404 (proves reachability)
        # We deliberately use HEAD to avoid sending a body. timeout 10s
        # gives breathing room without blocking preflight noticeably.
        response = httpx.request(
            "GET",
            f"{judge_url.rstrip('/')}/invoke/_preflight_probe",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )
    except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
        print(
            f"ERROR: evolution judge unreachable at {judge_url}: {exc}\n"
            f"  Is the judge service running? Try: "
            f"`curl -fsS {judge_url}/invoke/_preflight_probe -H 'Authorization: Bearer ...'`",
            file=sys.stderr,
        )
        sys.exit(1)
    except httpx.TimeoutException as exc:
        # Service responded slowly but is up. Don't fail preflight on
        # transient slow response — actual scoring calls have their own
        # 30min timeout and 4-attempt retry logic.
        print(
            f"WARN: evolution judge slow at {judge_url} ({exc}); "
            f"continuing anyway (real call has retry).",
            file=sys.stderr,
        )
        return
    except Exception as exc:  # noqa: BLE001
        print(
            f"ERROR: evolution judge probe failed at {judge_url}: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)
    if response.status_code == 401:
        print(
            f"ERROR: evolution judge rejected EVOLUTION_INVOKE_TOKEN (401). "
            f"The token in ~/.config/gofreddy/judges.env doesn't match the "
            f"judge service's INVOKE_TOKEN. Re-source the env file in BOTH "
            f"the judge service shell and this shell.",
            file=sys.stderr,
        )
        sys.exit(1)
    print(f"Auth smoke test passed: evolution-judge @ {judge_url}")


def _smoke_test_session_judge_auth() -> None:
    """Probe the session-judge endpoint at preflight.

    Mirror of ``_smoke_test_judge_auth`` for the *session* judge (port
    7100). The session judge is called by ``freddy evaluate critique``
    during in-session critique inside fixture sessions; if it's down,
    every fixture's inner critique fails silently and quality degrades
    without a clear preflight signal. This check makes the failure
    visible BEFORE we burn 5-15 min × N fixtures running with a
    silently-degraded inner-critique.

    Soft-warn (not exit) when SESSION_JUDGE_URL is unset — search-only
    runs without inner critique still produce scores, just lower-quality
    ones. Hard-exit only when URL is set but unreachable / token wrong.
    """
    judge_url = os.environ.get("SESSION_JUDGE_URL", "").strip()
    token = os.environ.get("SESSION_INVOKE_TOKEN", "").strip()
    if not judge_url:
        # Inner critique is optional — workflows have their own fallbacks.
        # Surface as INFO not ERROR so the operator knows what to expect.
        print(
            "INFO: SESSION_JUDGE_URL unset — fixture sessions will run "
            "without in-session critique. Source ~/.config/gofreddy/judges.env "
            "to enable.",
            file=sys.stderr,
        )
        return
    if not token:
        print(
            "WARN: SESSION_JUDGE_URL set but SESSION_INVOKE_TOKEN empty. "
            "In-session critique calls will return 401 — judges.env "
            "likely partially-loaded. Continuing without inner critique.",
            file=sys.stderr,
        )
        return
    try:
        import httpx  # type: ignore  # noqa: E402
        response = httpx.request(
            "GET",
            f"{judge_url.rstrip('/')}/invoke/_preflight_probe",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )
    except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
        print(
            f"ERROR: session judge unreachable at {judge_url}: {exc}\n"
            f"  Is the session judge running? Start it with:\n"
            f"  tmux new-session -d -s judge-session 'JUDGE_MODE=session "
            f"JUDGE_PORT=7100 INVOKE_TOKEN=\"$SESSION_INVOKE_TOKEN\" "
            f"./scripts/agent-launcher.sh ./.venv/bin/python -m judges.server'",
            file=sys.stderr,
        )
        sys.exit(1)
    except httpx.TimeoutException as exc:
        print(
            f"WARN: session judge slow at {judge_url} ({exc}); "
            f"continuing anyway (real call has retry).",
            file=sys.stderr,
        )
        return
    except Exception as exc:  # noqa: BLE001
        print(
            f"WARN: session judge probe failed at {judge_url}: {exc}; "
            f"continuing — inner critique may be degraded.",
            file=sys.stderr,
        )
        return
    if response.status_code == 401:
        print(
            f"ERROR: session judge rejected SESSION_INVOKE_TOKEN (401). "
            f"Token in ~/.config/gofreddy/judges.env doesn't match the "
            f"judge service's INVOKE_TOKEN. Re-source in both shells.",
            file=sys.stderr,
        )
        sys.exit(1)
    print(f"Auth smoke test passed: session-judge @ {judge_url}")


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

    # P1: when meta_backend=opencode, OPENCODE_CONFIG must be discoverable
    # (provider routing rules live there). Pre-existing fallback walked up
    # to .git which finds the WRONG opencode.json in worktrees. Fail loud
    # at preflight when the canonical $REPO_ROOT/opencode.json is missing.
    if config.meta_backend == "opencode" and not os.environ.get("OPENCODE_CONFIG", "").strip():
        config_path = _REPO_ROOT / "opencode.json"
        if not config_path.is_file():
            print(
                f"ERROR: meta_backend=opencode but {config_path} not found "
                f"and OPENCODE_CONFIG is unset. Without provider routing "
                f"rules, opencode falls back to upstream defaults that may "
                f"not support tool use. Either commit opencode.json to "
                f"repo root or export OPENCODE_CONFIG=/path/to/opencode.json.",
                file=sys.stderr,
            )
            sys.exit(1)

    # Create archive dir
    config.archive_dir.mkdir(parents=True, exist_ok=True)

    # Auto-materialize current_runtime so per-fixture runners don't crash
    # with FileNotFoundError on first launch in a fresh worktree. Idempotent
    # — safe to call when current_runtime is already populated. Skipped when
    # there's no lane manifest yet (legacy single-promoted-variant flow).
    from lane_runtime import (  # noqa: E402  local import keeps top of file lean
        ensure_materialized_runtime,
        has_lane_manifest,
    )
    if has_lane_manifest(config.archive_dir):
        try:
            ensure_materialized_runtime(config.archive_dir)
        except Exception as exc:  # noqa: BLE001
            print(
                f"ERROR: failed to materialize current_runtime: {exc}\n"
                f"  Check that {config.archive_dir / 'current.json'} points "
                f"at valid lane heads.",
                file=sys.stderr,
            )
            sys.exit(1)

    # Smoke-test inner-agent auth — meta + eval backends are real subprocesses
    # the loop will spawn many times. Catching auth failure here avoids
    # the v6-class silent-fail (0-byte iteration logs + 1.85s wall time).
    _smoke_test_backend_auth(config)

    # P0-D: Validate evolution-judge connectivity + token NOW. Empty token
    # surfaces as 401 from the judge service which _post_with_retry burns
    # 4×40s on per fixture before raising JudgeUnreachable mid-run. Catch
    # at preflight when holdout is configured (judge is required for
    # finalize). Skipped when only running search-suite (no judge needed).
    holdout_manifest_set = bool(os.environ.get("EVOLUTION_HOLDOUT_MANIFEST", "").strip())
    if holdout_manifest_set:
        _smoke_test_judge_auth()
    # Always probe the session judge — it's used by every fixture session's
    # in-session critique regardless of whether holdout is configured.
    _smoke_test_session_judge_auth()

    # P1: surface holdout-disabled state explicitly so silent-skip is
    # impossible. If require_holdout=True but no manifest is configured,
    # the run will eventually fail at finalize with "no holdout configured"
    # — abort now with a clear message.
    if config.require_holdout and not holdout_manifest_set:
        print(
            "ERROR: require_holdout=true but EVOLUTION_HOLDOUT_MANIFEST is "
            "unset. Set the env var (e.g. source ~/.config/gofreddy/judges.env) "
            "to point at a valid holdout manifest.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Config summary
    print(f"Meta agent backend: {config.meta_backend}")
    print(f"Meta agent model:   {config.meta_model}")
    print(f"Eval backend:       {os.environ.get('EVOLUTION_EVAL_BACKEND', '')}")
    print(f"Eval model:         {os.environ.get('EVOLUTION_EVAL_MODEL', '')}")
    eval_reasoning = os.environ.get("EVOLUTION_EVAL_REASONING_EFFORT", "")
    if eval_reasoning:
        print(f"Eval reasoning:     {eval_reasoning}")
    print(f"Require holdout:    {str(config.require_holdout).lower()}")
    print(f"Holdout manifest:   {'configured' if holdout_manifest_set else 'DISABLED'}")
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

    Stays serial. The 2026-05-07 review surfaced that ``cmd_run`` is not
    thread-safe: it installs ``signal.signal(SIGALRM, …)`` (only callable from
    the main thread), mutates ``os.environ`` (EVOLUTION_EVAL_BACKEND/MODEL/
    COHORT_ID), and races on ``_next_variant_id`` + ``shutil.copytree`` against
    a shared ``archive_dir``. Cross-lane parallelism here would also nest a
    ``claude``-semaphore acquisition (lane permit) around an inner
    ``parallel_for(claude)`` (critic domains), deadlocking at the default
    cap=4 × 4 lanes. Per-lane parallelism inside the loop (critic domains,
    finalists, fixture fan-out) ships in this PR and preserves most of the
    speedup. A future plan can make ``cmd_run`` thread-safe and revisit.
    """
    for lane in all_lane_names():
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

    # P0-A: prepend project venv bin to PATH so the meta agent's shell-spawned
    # `freddy ...` calls resolve. Critical: every variant in v001..v007 ran
    # without freddy on PATH inside the agent sandbox, silently falling back
    # to direct_http and skipping competitive-intel/visibility features.
    venv_bin = _REPO_ROOT / ".venv" / "bin"
    if venv_bin.is_dir():
        existing_path = env.get("PATH", "")
        if str(venv_bin) not in existing_path.split(os.pathsep):
            env["PATH"] = os.pathsep.join([str(venv_bin), existing_path]) if existing_path else str(venv_bin)

    # Safety: env must never be None when reaching Popen — prevents
    # accidental full-env inheritance.
    assert env is not None, "env dict must not be None for subprocess"
    return env


def _build_meta_command(
    config: EvolutionConfig,
    workdir: Path,
    prompt_text: str | None = None,
    session_id: str | None = None,
    resume_sid: str | None = None,
) -> list[str]:
    """Build the command array for the meta agent subprocess.

    For backends that read prompt from stdin (claude with ``-p``; codex with a
    trailing ``"-"`` argument), ``prompt_text`` is ignored — caller passes
    prompt via stdin pipe. For opencode, ``prompt_text`` is appended as the
    trailing positional argv element because opencode reads prompt from argv,
    not stdin.

    Resume semantics (claude only):
    - ``session_id`` (UUID): fresh spawn; claude records the conversation
      under this ID so a future ``--resume <id>`` can pick it up.
    - ``resume_sid`` (UUID): re-attach to an existing claude conversation;
      claude replays prior turns and the caller-supplied prompt is treated
      as a 'continue' message. ``resume_sid`` wins if both are supplied.

    Codex pre-mint is not supported (the CLI only resumes by an
    already-recorded session id, never a fresh one). The codex path here
    ignores both fields; mid-meta-agent codex resume falls through to a
    fresh spawn. OpenCode multi-provider lacks a stable resume mechanism.
    """
    if config.meta_backend == "claude":
        if resume_sid:
            return [
                "claude", "-p",
                "--model", config.meta_model,
                "--allowedTools", "Bash,Read,Write,Edit,Glob,Grep",
                "--max-turns", str(config.max_turns),
                "--resume", resume_sid,
            ]
        cmd = [
            "claude", "-p",
            "--model", config.meta_model,
            "--allowedTools", "Bash,Read,Write,Edit,Glob,Grep",
            "--max-turns", str(config.max_turns),
        ]
        if session_id:
            cmd.extend(["--session-id", session_id])
        return cmd
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
    session_id: str | None = None,
    resume_sid: str | None = None,
) -> int:
    """Single meta-agent subprocess attempt — no retry. Caller wraps with retry.

    ``session_id`` (fresh) and ``resume_sid`` (re-attach) are claude-only
    and forwarded to ``_build_meta_command``. Pass session_id on a fresh
    spawn so the SessionsFile record points at the same UUID claude records
    internally; pass resume_sid to re-attach to an existing conversation.
    """
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
        cmd = _build_meta_command(
            config, workdir, session_id=session_id, resume_sid=resume_sid,
        )
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
    sessions_file: SessionsFile | None = None,
    agent_key: str | None = None,
    session_id: str | None = None,
    resume_sid: str | None = None,
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

    Per Plan B U2 (2026-05-11): --resume-variant is gone, but
    ``sessions_file`` + ``session_id`` + ``resume_sid`` plumbing kept
    for the SessionsFile no-op shim (U10) — no live consumers, but the
    keyword surface stays so the meta-agent spawn signature doesn't
    churn until callers are migrated.
    """
    # Unified retry for all backends. Empirical Apr 27-29 evidence: claude
    # exit=1 with empty stderr in <2s under rate-limit pressure happened on
    # the program critic AND can happen on meta-agent. Treat all transient
    # signals via the shared agent_retry detector.
    from agent_retry import (
        max_attempts as _max_attempts,
        is_transient_failure as _is_transient,
        sleep_for_retry as _sleep_retry,
        backoff_delay as _backoff_delay,
    )

    if sessions_file is not None and agent_key is not None:
        sid_for_record = resume_sid or session_id or ""
        sessions_file.begin(agent_key, sid_for_record, engine=config.meta_backend)

    attempts = _max_attempts()
    exit_code = 0
    try:
        for attempt in range(1, attempts + 1):
            exit_code = _run_meta_agent_once(
                prompt_file, workdir, config,
                log_file=log_file,
                session_id=session_id,
                resume_sid=resume_sid,
            )
            # Read tail of log to feed transient-detection. log_file holds
            # combined stdout+stderr (subprocess.STDOUT in _run_meta_agent_once).
            log_tail = ""
            if log_file is not None and Path(log_file).is_file():
                try:
                    log_tail = Path(log_file).read_text(encoding="utf-8", errors="replace")[-4000:]
                except OSError:
                    pass
            transient = _is_transient(
                config.meta_backend, exit_code, stdout=log_tail, stderr=""
            )
            # Success or final attempt or non-transient: stop retrying.
            if exit_code == 0 and not transient:
                break
            if attempt == attempts or not transient:
                break
            print(
                f"meta agent {config.meta_backend} attempt {attempt}/{attempts} "
                f"hit transient signal (exit={exit_code}); retrying in "
                f"{_backoff_delay(attempt)}s",
                file=sys.stderr,
            )
            _sleep_retry(attempt)
    finally:
        if sessions_file is not None and agent_key is not None:
            sessions_file.finish(agent_key, "complete" if exit_code == 0 else "failed")

    return exit_code


# ---------------------------------------------------------------------------
# Cleanup and signal handling
# ---------------------------------------------------------------------------


def _render_meta_template(template: str, mapping: dict[str, str]) -> str:
    """Single-pass substitution of ``{placeholder}`` tokens into ``template``.

    Each ``{name}`` in ``template`` is replaced by ``mapping[name]`` if
    ``name`` is present in ``mapping``; otherwise the literal token is
    left untouched. Crucially, substituted values are NEVER re-scanned
    for further placeholder tokens — the regex engine consumes the
    template left-to-right exactly once, so any ``{...}`` token a
    substituted value happens to contain is emitted verbatim into the
    output rather than being re-substituted.

    G2 finding #4 (review of d128a5c): the pre-fix renderer ran 8
    sequential ``str.replace`` calls in a fixed order. ``{parent_critic_review}``
    was substituted before ``{recent_alerts}`` and ``{selection_rationale}``.
    A meta-agent who arranges for the critic to quote a literal
    ``{recent_alerts}`` token would therefore inject operator-sourced
    alert text into a region the next agent reads as "parent critic
    review" — second-order prompt injection.

    Note: a "double-the-braces" escape (``{`` → ``{{``) does NOT close
    this hole against ``str.replace``-based templating, because
    ``{{recent_alerts}}`` literally contains ``{recent_alerts}`` as a
    substring and the next ``str.replace`` call still matches. Single-pass
    regex substitution is the actual fix.

    Operator-controlled platform values (lane / archive_path /
    iterations_remaining / eval_digest_path / parent_sessions_path) are
    just as safe under this engine as untrusted LLM-derived values
    (parent_critic_review / recent_alerts / selection_rationale_text)
    — neither category can leak into another's region — so we don't
    need a separate escape pass.
    """
    import re as _re

    pattern = _re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")

    def _sub(match: "_re.Match[str]") -> str:
        key = match.group(1)
        if key in mapping:
            return mapping[key]
        # Unknown placeholder — leave verbatim so missing-key bugs are
        # visible in the rendered prompt rather than silently emitting
        # an empty string.
        return match.group(0)

    return pattern.sub(_sub, template)


def _collect_meta_template_context(
    *,
    parent_id: str | None,
    meta_archive_root: str,
    lane: str,
    alerts_metrics_dir: Path,
    env: dict[str, str] | None = None,
) -> dict[str, str]:
    """Build the mapping passed to ``_render_meta_template`` from disk + env.

    Extracted from ``cmd_run`` (post-audit 2026-05-07) so the B3/B4/B9
    file-read wiring can be unit-tested without spinning up the full
    evolution loop. Pure function over inputs:

    - **B3**: reads ``<meta_archive_root>/<parent_id>/critic_reviews.md`` if
      present; otherwise emits the explanatory fallback. Closes the
      pre-fix gap where the critic review was write-only.
    - **B4**: reads ``<alerts_metrics_dir>/alerts.jsonl``, filters by
      ``lane``, returns the last 5 lane-matched lines. Pre-fix this file
      was write-only and its location was duplicated between writer
      (compute_metrics.py) and reader (cmd_run); both now read from the
      writer's canonical ``METRICS_DIR`` so they cannot drift.
    - **B9**: reads ``EVOLUTION_SELECTION_RATIONALE`` from ``env`` (or
      ``os.environ`` if env is None). The env-var allowlist hooks live
      in ``_CLAUDE_ENV_KEYS``; the placeholder makes the rationale
      visible in the prompt body rather than only as an inherited env var.

    Also resolves ``eval_digest_path`` and ``parent_sessions_path`` from
    parent_id when present — pure path joins, no I/O failure path.

    Returns a dict suitable for direct passing as the ``mapping`` arg of
    ``_render_meta_template``. Caller is still responsible for adding
    static keys (``archive_path``, ``iterations_remaining``).
    """
    if env is None:
        env = dict(os.environ)

    eval_digest_path = ""
    parent_sessions_path = ""
    parent_critic_review = (
        "No critic review available — first variant in lane, or critic "
        "failed (variant would have been discarded by A2 fail-closed)."
    )
    if parent_id:
        digest = Path(meta_archive_root) / parent_id / "eval_digest.md"
        if digest.is_file():
            eval_digest_path = str(digest)
        sessions = Path(meta_archive_root) / parent_id / "sessions"
        if sessions.is_dir():
            parent_sessions_path = str(sessions)
        critic_path = Path(meta_archive_root) / parent_id / "critic_reviews.md"
        if critic_path.is_file():
            try:
                body = critic_path.read_text(encoding="utf-8").strip()
                if body:
                    parent_critic_review = body
            except OSError:
                pass

    recent_alerts = "No alerts file."
    alerts_path = alerts_metrics_dir / "alerts.jsonl"
    if alerts_path.is_file():
        try:
            raw_lines = alerts_path.read_text(encoding="utf-8").splitlines()
            lane_lines: list[str] = []
            for raw in raw_lines:
                line = raw.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if payload.get("lane") == lane:
                    lane_lines.append(line)
            recent_alerts = (
                "\n".join(lane_lines[-5:])
                or "No alerts recorded for this lane."
            )
        except OSError:
            pass

    selection_rationale_text = env.get(
        "EVOLUTION_SELECTION_RATIONALE", ""
    ).strip() or "(no rationale provided — first variant or selection metadata missing)"

    return {
        "lane": lane,
        "eval_digest_path": (
            eval_digest_path or "No eval digest available for parent."
        ),
        "parent_sessions_path": (
            parent_sessions_path or "No parent sessions available."
        ),
        "parent_critic_review": parent_critic_review,
        "recent_alerts": recent_alerts,
        "selection_rationale": selection_rationale_text,
    }


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


def _discard_variant(variant_dir: Path) -> None:
    """Discard a variant: remove its archive dir AND its private holdout cache.

    Closes the cached-holdout-bypass vector flagged by the adversarial
    reviewer of d128a5c: ``_load_private_result`` keys cached holdout
    scores by ``<private_root>/<variant_id>/holdout_result.json``. After
    a discard via ``_safe_rmtree(variant_dir)``, ``_next_variant_id``
    can re-mint the same number when the loop runs again, and the new
    variant inherits the OLD cached scores — bypassing A0's
    ``candidate_score > 0.0`` gate. Clearing both paths together keeps
    discard semantics aligned with what the loop expects.
    """
    _safe_rmtree(variant_dir)
    try:
        import tempfile  # local import keeps top of file lean
        private_dir_raw = os.environ.get("EVOLUTION_PRIVATE_ARCHIVE_DIR", "").strip()
        private_root = (
            Path(private_dir_raw).resolve()
            if private_dir_raw
            else Path(tempfile.gettempdir()).resolve() / "autoresearch-holdouts"
        )
        per_variant_cache = private_root / variant_dir.name
        if per_variant_cache.is_dir():
            _safe_rmtree(per_variant_cache)
    except Exception as exc:  # noqa: BLE001 — discard must never propagate
        print(
            f"WARN: failed to clear private holdout cache for "
            f"{variant_dir.name}: {exc}",
            file=sys.stderr,
        )


def cleanup() -> None:
    """Clean up temp dirs and the running meta agent."""
    if _running_meta_agent is not None:
        _terminate_process(_running_meta_agent, "cleanup")
    for d in list(_temp_dirs):
        _safe_rmtree(d)
    _temp_dirs.clear()


def _sigalrm_handler(signum: int, frame) -> None:
    """Handle SIGALRM — generation wall-time ceiling reached."""
    print(
        "FATAL: generation wall-time ceiling reached. Terminating.",
        file=sys.stderr,
    )
    raise SystemExit(1)


def _sigterm_handler(signum: int, frame) -> None:
    """Handle SIGINT/SIGTERM — let finally-blocks run."""
    sig_name = "SIGINT" if signum == signal.SIGINT else "SIGTERM"
    print(f"\nReceived {sig_name}. Stopping cleanly.", file=sys.stderr)
    raise SystemExit(130 if signum == signal.SIGINT else 143)


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


def _select_parent_deterministic(
    archive_dir: Path,
    suite_id: str | None,
    lane: str,
) -> tuple[str, str]:
    """Pick the highest-scoring eligible parent for the next generation.

    Per Plan B U5 (2026-05-11): replaces the LLM-based select_parent
    (310 LOC + 221 LOC agent_calls) with a deterministic top-1 picker.
    The anti-drift floor (Finding #118: filter to entries within 50%
    of the best score) is preserved — but with a single deterministic
    output we just keep the best of the anchored pool.

    Returns ``(parent_id, rationale)``. Raises SystemExit if no on-disk
    eligible variants remain (lineage references missing dirs).
    """
    from archive_index import ordered_latest_entries
    from frontier import (
        entry_active_for_lane as _entry_active_for_lane,
        has_search_metrics,
    )
    from lane_paths import normalize_lane
    from lane_registry import default_objective_score_from_entry

    archive_root = Path(archive_dir).resolve()
    lane = normalize_lane(lane)
    all_entries = ordered_latest_entries(archive_root)

    def _score(entry: dict) -> float:
        return float(default_objective_score_from_entry(entry, lane) or 0.0)

    eligible = [
        e for e in all_entries
        if e.get("status") != "discarded"
        and has_search_metrics(e, suite_id=suite_id)
        and (archive_root / str(e.get("id") or "")).is_dir()
    ]
    lane_eligible = [e for e in eligible if _entry_active_for_lane(e, lane)]
    pool = lane_eligible or eligible

    if not pool:
        # Cold start / lineage references missing dirs: fall back to any
        # on-disk entry (earliest by timestamp) at score 0.0.
        existing = [
            e for e in all_entries
            if (archive_root / str(e.get("id") or "")).is_dir()
        ]
        if not existing:
            raise SystemExit(
                "No entries with on-disk archive directories — lineage "
                "entries reference variants that don't exist."
            )
        seed_id = str(existing[0]["id"])
        print(
            f"WARNING: no searchable variants for lane={lane!r}; "
            f"seeding from earliest entry {seed_id!r} at score 0.0",
            file=sys.stderr,
        )
        return seed_id, "cold-start fallback (no searchable variants)"

    pool.sort(key=_score, reverse=True)
    best_score = _score(pool[0])
    if best_score > 0.0:
        floor = best_score * 0.5
        anchored = [e for e in pool if _score(e) >= floor]
        if anchored:
            pool = anchored
    parent = pool[0]
    parent_id = str(parent["id"])
    rationale = (
        f"deterministic top-1 (score={_score(parent):.3f}, "
        f"anti-drift floor={best_score * 0.5:.3f})"
    )
    return parent_id, rationale


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
    """Run holdout on the single best frontier variant and promote if better."""
    if not config.require_holdout:
        return
    if not evolve_ops.holdout_configured():
        print("Finalize step skipped: no holdout manifest configured.")
        return

    refresh_archive(config)

    import evaluate_variant
    from archive_index import ordered_latest_entries
    from frontier import best_variant_in_lane, has_search_metrics

    archive_root = Path(config.archive_dir).resolve()
    entries = [
        entry
        for entry in ordered_latest_entries(archive_root)
        if evolve_ops._entry_active_for_lane(entry, config.lane)
        and entry.get("status") != "discarded"
        and has_search_metrics(entry)
    ]
    baseline_entry = evaluate_variant._promotion_baseline(archive_root, "", config.lane)
    baseline_id = str(baseline_entry["id"]) if baseline_entry else None
    best_entry = best_variant_in_lane(entries, config.lane)
    finalist_id = str(best_entry.get("id") or "") if best_entry else ""
    if (
        not finalist_id
        or finalist_id == baseline_id
        or not (archive_root / finalist_id).is_dir()
    ):
        print("No frontier finalist available for hidden holdout evaluation.")
        return
    finalists = [finalist_id]

    holdout_suite = evolve_ops.holdout_suite_id(config.lane)
    print(f"Finalizing frontier variant {finalist_id} on hidden holdout ({holdout_suite})...")
    _run_holdout(config, str(config.archive_dir / finalist_id))

    baseline_variant_id = baseline_id
    results: list[dict] = []
    record = evaluate_variant._load_private_result(
        finalist_id, "finalize", holdout_suite, lane=config.lane,
    )
    if isinstance(record, dict):
        results.append(record)
    shortlist_path = evaluate_variant._write_finalized_shortlist(
        suite_id=holdout_suite,
        baseline_variant_id=baseline_variant_id,
        lane=config.lane,
        results=results,
    )
    if shortlist_path is not None:
        print(f"Private finalized shortlist written to {shortlist_path}")

    best_record = evaluate_variant._best_finalized_candidate(
        archive_dir=archive_root,
        suite_id=holdout_suite,
        lane=config.lane,
        candidate_ids=finalists,
    )
    best_id = str(best_record["variant_id"]) if isinstance(best_record, dict) else None
    # Capture prior head BEFORE set_current_head overwrites it.
    prior_head = evolve_ops.current_head_variant_id(
        str(config.archive_dir), config.lane,
    )
    if best_id:
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        evolve_ops.promote_atomic(
            str(config.archive_dir), config.lane, best_id, timestamp
        )
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
    ensure_baseline_seed(config)
    refresh_archive(config)
    print("Pre-flight OK.")

    if not os.environ.get("EVOLUTION_COHORT_ID", "").strip():
        os.environ["EVOLUTION_COHORT_ID"] = f"run-{int(time.time())}"

    # Generation ceiling: signal.alarm fires SIGALRM after
    # MAX_GENERATION_SECONDS. SIGINT/SIGTERM raise SystemExit so the
    # finally block runs cleanup().
    #
    # Default 21600 (6hr) sized for ~3 generations × ~50min/gen (meta +
    # 40min parallel fixture sweep + scoring) + holdout finalize for
    # candidate + baseline (~80min sequential). Total ≈ 4hr realistic,
    # with 2hr headroom for slow-stall fixtures.
    max_generation_seconds = int(
        os.environ.get("MAX_GENERATION_SECONDS", "21600")
    )
    old_alrm = signal.signal(signal.SIGALRM, _sigalrm_handler)
    old_int = signal.signal(signal.SIGINT, _sigterm_handler)
    old_term = signal.signal(signal.SIGTERM, _sigterm_handler)
    signal.alarm(max_generation_seconds)

    max_generation = config.iterations

    try:
        from compute_metrics import record_generation

        for gen in range(1, max_generation + 1):
            print(f"=== Generation {gen}/{max_generation} [lane={config.lane}] ===")

            os.environ["EVOLUTION_COHORT_ID"] = str(gen - 1)

            refresh_archive(config)

            parent_id, selection_rationale = _select_parent_deterministic(
                config.archive_dir, config.search_suite_id, config.lane,
            )
            parent = config.archive_dir / parent_id
            if selection_rationale:
                os.environ["EVOLUTION_SELECTION_RATIONALE"] = selection_rationale
            else:
                os.environ.pop("EVOLUTION_SELECTION_RATIONALE", None)
            print(f"Parent: {parent_id} (lane={config.lane}) — {selection_rationale}")

            variant_id = _next_variant_id(config.archive_dir)
            variant_dir = config.archive_dir / variant_id
            shutil.copytree(str(parent), str(variant_dir))
            # Wipe inherited per-variant runtime artifacts so the child starts
            # clean. ``copytree`` brings everything across; the child must not
            # inherit parent's sessions, metrics, scores, or resume records
            # (the latter would cause silent stale-sid resume on next run).
            for stale_dir in ("sessions", "metrics", "archived_sessions", ".meta_workspace"):
                shutil.rmtree(variant_dir / stale_dir, ignore_errors=True)
            for stale_file in (
                "meta-session.log", "scores.json", ".session_ids.json",
                "variant_manifest.json",
            ):
                (variant_dir / stale_file).unlink(missing_ok=True)
            (variant_dir / "sessions").mkdir(parents=True, exist_ok=True)

            print(f"Cloned {parent_id} -> {variant_id}")

            # Per Plan B U6 (2026-05-11): the regen_program_docs AUTOGEN
            # block sync was deleted (caused bug #115 — phantom cross-lane
            # programs edits). Static prompt files in programs/ are now
            # the canonical source; no regeneration step.

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

            # Prepare meta workspace at a stable path under variant_dir.
            # Cleared on success below.
            meta_workspace_root = variant_dir / ".meta_workspace"
            if meta_workspace_root.is_dir():
                shutil.rmtree(meta_workspace_root)
            meta_workspace_root.mkdir(parents=True)
            meta_archive_root, meta_variant_dir = evolve_ops.prepare_meta_workspace(
                str(config.archive_dir),
                variant_id,
                str(meta_workspace_root),
            )
            evolve_ops.write_lane_context(meta_archive_root, config.lane)

            # B3/B4/B9 + eval_digest + parent_sessions: file/env reads
            # extracted into _collect_meta_template_context for testability.
            # See the helper's docstring for the per-key contract.
            from compute_metrics import METRICS_DIR as _ALERTS_METRICS_DIR
            template_context = _collect_meta_template_context(
                parent_id=parent_id,
                meta_archive_root=meta_archive_root,
                lane=config.lane,
                alerts_metrics_dir=_ALERTS_METRICS_DIR,
            )

            # Render meta template via _render_meta_template — single-pass
            # regex substitution that does NOT recursively substitute.
            # G2 finding #4 (review of d128a5c): the pre-fix renderer ran
            # 8 sequential ``str.replace`` calls; ``{parent_critic_review}``
            # was substituted before ``{recent_alerts}`` and
            # ``{selection_rationale}``, so a critic review quoting a
            # literal ``{recent_alerts}`` token would inject operator-sourced
            # alert text into a region the next agent reads as critic
            # output. Single-pass templating closes that hole — see the
            # _render_meta_template docstring for why a brace-escape
            # alone would not.
            meta_template = Path(meta_variant_dir) / "meta.md"
            rendered = _render_meta_template(
                meta_template.read_text(),
                {
                    **template_context,
                    "archive_path": meta_archive_root,
                    "iterations_remaining": str(max_generation - gen),
                },
            )

            rendered_fd, rendered_path_str = tempfile.mkstemp(suffix=".md")
            os.close(rendered_fd)
            rendered_path = Path(rendered_path_str)
            rendered_path.write_text(rendered)

            # Mint a session_id for claude meta-agent so resume can re-attach
            # to the same conversation. Codex/opencode ignore this — codex has
            # no pre-mint flag, and opencode lacks stable resume on
            # multi-provider routes.
            sessions_file = SessionsFile(variant_dir / ".session_ids.json")
            agent_key = f"meta-{variant_id}"
            meta_session_id = (
                str(uuid.uuid4()) if config.meta_backend == "claude" else ""
            )

            # Run meta agent (mutate). Divergent lanes (e.g., harness_fixer
            # invokes harness/engine.py's fix-verify loop) override via
            # LaneSpec.custom_mutate; existing 5 lanes use the default.
            spec = _LANE_SPECS[config.lane]
            if spec.custom_mutate is not None:
                meta_exit = spec.custom_mutate(
                    rendered_path,
                    Path(meta_variant_dir),
                    config,
                    log_file=variant_dir / "meta-session.log",
                )
            else:
                meta_exit = run_meta_agent(
                    rendered_path,
                    Path(meta_variant_dir),
                    config,
                    log_file=variant_dir / "meta-session.log",
                    sessions_file=sessions_file,
                    agent_key=agent_key,
                    session_id=meta_session_id,
                )
            rendered_path.unlink(missing_ok=True)
            print(f"Meta agent exit code: {meta_exit}")

            evolve_ops.sync_meta_workspace(meta_variant_dir, str(variant_dir))
            shutil.rmtree(meta_workspace_root, ignore_errors=True)

            # Pareto-constraint critique agent (R-#15, soft-review only).
            # Reads (old, new) pair of programs/<domain>-session.md and
            # appends an advisory verdict to variant_dir/critic_reviews.md.
            # Never rejects — just logs PRESCRIPTION vs DESCRIPTION drift
            # for operator eyeballing. Env escape:
            # EVOLVE_SKIP_PRESCRIPTION_CRITIC=1.
            if os.environ.get("EVOLVE_SKIP_PRESCRIPTION_CRITIC") != "1":
                try:
                    from program_prescription_critic import critique_all_programs

                    critic_results = critique_all_programs(
                        parent_dir=parent,
                        variant_dir=variant_dir,
                        lane=config.lane,
                        sessions_file=sessions_file,
                    )
                except Exception as exc:  # noqa: BLE001
                    # A2: an exception escaping critique_all_programs is
                    # itself an infra failure — fail closed.
                    print(
                        f"[evolve] WARN: program_prescription_critic failed: {exc}",
                        file=sys.stderr,
                    )
                    critic_results = {
                        "_uncaught": {  # type: ignore[dict-item]
                            "verdict": "error",
                            "reasoning": f"critique_all_programs raised: {exc}",
                        }
                    }
                # A2 (plan 2026-05-06-001): any "error" verdict means the
                # critic could not actually evaluate this variant —
                # subprocess crash, timeout, malformed output, missing CLI.
                # Pre-fix this collapsed into "no-change" and let Pi v007's
                # `completion_guard`-neutering contamination through.
                # Discard the variant rather than score it under unverified
                # mutation gating. Predicate extracted to ``_critic_infra_failures``
                # so a typo regression (e.g. ``status`` instead of ``verdict``)
                # is caught by unit tests.
                error_results = _critic_infra_failures(critic_results)
                if error_results:
                    first = next(iter(error_results.values()))
                    reason = str(first.get("reasoning", "critic infra failure"))[:200]
                    print(
                        f"[evolve] ERROR: critic returned 'error' for "
                        f"{sorted(error_results.keys())}; discarding {variant_id}. "
                        f"Reason: {reason}",
                        file=sys.stderr,
                    )
                    _discard_variant(variant_dir)
                    continue

            # Custom validate hook — divergent lanes (marketing_audit's
            # frozen-content manifest, harness_fixer's verifier.md SHA256)
            # check invariants before scoring. Existing 5 lanes pass through.
            if spec.custom_validate is not None:
                if not spec.custom_validate(variant_dir, parent):
                    print(
                        f"Variant {variant_id} failed custom_validate; "
                        "discarding without scoring."
                    )
                    _discard_variant(variant_dir)
                    continue

            # Score variant. Divergent lanes (marketing_audit weighted-sum +
            # cost penalty; harness_fixer HM-1..HM-8) override via custom_score.
            if spec.custom_score is not None:
                spec.custom_score(config, str(variant_dir), parent_id)
            else:
                _score_variant_search(config, str(variant_dir), parent_id)

            discarded = not evolve_ops.variant_in_lineage(
                str(config.archive_dir), variant_id
            )
            if discarded:
                print(f"Variant {variant_id} was discarded before archival.")
                _discard_variant(variant_dir)
            else:
                refresh_archive(config)

            # Sequential evolution: one variant per generation. Emit the
            # metrics row regardless of discard so the alert agent sees the
            # generation boundary.
            try:
                record_generation(
                    lane=config.lane,
                    gen_id=gen - 1,
                    variant_ids=[] if discarded else [variant_id],
                )
            except Exception as exc:
                print(
                    f"warning: compute_metrics failed for gen {gen - 1}: {exc}",
                    file=sys.stderr,
                )

            if discarded:
                continue

        _do_finalize_step(config)
        print(f"Evolution complete. {max_generation} generations.")

    finally:
        signal.alarm(0)  # Cancel pending alarm
        signal.signal(signal.SIGALRM, old_alrm)
        signal.signal(signal.SIGINT, old_int)
        signal.signal(signal.SIGTERM, old_term)
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
        # A6 v2 (plan 2026-05-06-001 follow-up): rollback target is the
        # previous promoted variant, by definition a variant that passed
        # the gate when it was promoted. ``previous_promoted_variant``
        # filters lineage to entries with ``promoted_at`` set — that
        # stored evidence IS the gate. Pre-fix this also called the
        # LLM-based ``is_promotable`` which (a) cost $0.50-$2 per undo,
        # (b) was non-deterministic (judge could flip on the same
        # input), and (c) could block legitimate rollbacks during a
        # judge-service outage. Trust the stored ``promoted_at``;
        # ``previous_promoted_variant`` raises ``SystemExit`` itself if
        # there's no eligible target. ``--force-undo`` is preserved as
        # a no-op for backward compat with operator scripts.
        prev = evolve_ops.previous_promoted_variant(archive_dir, config.lane)
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        evolve_ops.promote_atomic(archive_dir, config.lane, prev, timestamp)
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
        import evaluate_variant
        best_record = evaluate_variant._best_finalized_candidate(
            archive_dir=Path(archive_dir).resolve(),
            suite_id=holdout_suite,
            lane=config.lane,
        )
        variant_id = str(best_record["variant_id"]) if isinstance(best_record, dict) else None
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

    # Custom promote hook — divergent lanes (marketing_audit pre-promotion
    # smoke test) gate or augment promotion. Existing 5 lanes pass through.
    spec = _LANE_SPECS[config.lane]
    if spec.custom_promote is not None:
        if not spec.custom_promote(archive_dir, variant_id, config.lane):
            print(
                f"ERROR: custom_promote rejected {variant_id} for "
                f"lane={config.lane}",
                file=sys.stderr,
            )
            sys.exit(1)

    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    evolve_ops.promote_atomic(archive_dir, config.lane, variant_id, timestamp)
    refresh_archive(config)
    print(f"Promoted {variant_id} for lane={config.lane}")

    # α5: cross-lane meta-pattern detection. Walks every lane's session dirs
    # and emits clusters of agent reasoning that recur across lanes/fixtures.
    # Non-blocking; gated by AUTORESEARCH_SKIP_META_PATTERNS=1 kill switch.
    # Output lands at archive/meta_patterns.json for the portal route to
    # surface (see src/api/routers/portal.py:portal_meta_patterns).
    if os.environ.get("AUTORESEARCH_SKIP_META_PATTERNS", "").strip() not in ("1", "true", "yes"):
        from lane_runtime import materialized_runtime_dir
        try:
            runtime_dir = materialized_runtime_dir(archive_dir)
            script_path = runtime_dir / "scripts" / "detect_meta_patterns.py"
            if script_path.exists():
                meta_path = archive_dir / "meta_patterns.json"
                subprocess.run(
                    [sys.executable, str(script_path), "--all-lanes",
                     "-o", str(meta_path)],
                    cwd=str(archive_dir.parent),
                    timeout=600,
                    check=False,
                )
                if meta_path.exists():
                    print(f"  ✓ meta-patterns refreshed: {meta_path}")
        except Exception as exc:  # noqa: BLE001
            print(f"  WARNING: detect_meta_patterns failed (non-blocking): {exc}",
                  file=sys.stderr)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Main entry point."""
    args = parse_args()
    config = load_config(args)

    # Drift gate: src/evaluation/models.py:160 keeps a hardcoded Literal of
    # workflow lane names (avoids circular import). Assert it matches the
    # registry on every real evolve invocation so adding a workflow lane
    # without bumping the Literal fails loud. Placed after parse_args so
    # `evolve.py --help` doesn't trigger the import.
    from lane_registry import _assert_models_literal_matches
    _assert_models_literal_matches()

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
