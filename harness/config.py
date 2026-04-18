"""Typed configuration for the QA eval-fix harness."""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Sequence


def normalize_id(raw: str) -> str:
    """Normalize a capability ID to LETTER-INTEGER form.

    Handles single-letter prefixes [A-C] case-insensitively.
    Examples: "A01" -> "A-1", "b4" -> "B-4", "C12" -> "C-12".
    Returns the input unchanged if no matching prefix is found.
    """
    m = re.match(r"^([A-Ca-c])-?0*(\d+)$", raw.strip())
    if m:
        return f"{m.group(1).upper()}-{m.group(2)}"
    return raw.strip()


# Required env vars for real-mode runs.  Preflight fails if any are empty.
REQUIRED_ENV_VARS = (
    "DATABASE_URL",
    "SUPABASE_URL",
    "SUPABASE_JWT_SECRET",
    "SUPABASE_ANON_KEY",
    "SUPABASE_SERVICE_ROLE_KEY",
    "GEMINI_API_KEY",
    "R2_ACCESS_KEY_ID",
    "R2_SECRET_ACCESS_KEY",
    "SCRAPECREATORS_API_KEY",
    "APIFY_TOKEN",
    "MONITORING_XPOZ_API_KEY",
    "MONITORING_NEWSDATA_API_KEY",
    "DATAFORSEO_LOGIN",
    "DATAFORSEO_PASSWORD",
    "FAL_KEY",
)


@dataclass(frozen=True)
class Config:
    """Immutable run configuration built from CLI args + env vars."""

    # --- CLI args (operator-facing knobs) ---
    max_cycles: int = 5
    dry_run: bool = False
    engine: str = "codex"
    eval_only: bool = False
    only: list[str] = field(default_factory=list)
    phase: str = "all"
    skip: list[str] = field(default_factory=list)
    resume_branch: str = ""
    resume_cycle: int = 1

    # --- Env-var config (infrastructure) ---
    max_retries: int = 3
    retry_delay: int = 30
    tracks: list[str] = field(default_factory=lambda: ["a", "b", "c", "d", "e", "f"])
    staging_root: str = "/tmp"
    auto_cleanup: bool = False
    max_walltime: int = 14400
    jwt_ttl: int = 28800
    max_fix_attempts: int = 2
    keep_state: bool = False
    eval_model: str = "opus"
    fixer_model: str = "opus"
    codex_eval_profile: str = "harness-evaluator"
    codex_fixer_profile: str = "harness-fixer"
    codex_verifier_profile: str = "harness-verifier"
    codex_eval_model: str = ""
    codex_fixer_model: str = ""
    codex_verifier_model: str = ""
    backend_port: int = 8080
    backend_cmd: str = "uvicorn src.api.main:create_app --factory --host 0.0.0.0 --port 8080"
    backend_log: str = "/tmp/freddy-backend.log"
    fixer_workers: int = 1
    fixer_domains: list[str] = field(default_factory=lambda: ["A", "B", "C"])
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8080"

    @classmethod
    def from_cli_and_env(
        cls, argv: Sequence[str] | None = None
    ) -> "Config":
        """Build Config from CLI args overlaid on env-var defaults."""
        args = _parse_args(argv)

        def _env_int(key: str, default: int) -> int:
            return int(os.environ.get(key, default))

        def _env_bool(key: str, default: bool) -> bool:
            return os.environ.get(key, str(default)).lower() in ("true", "1", "yes")

        def _env_str(key: str, default: str) -> str:
            return os.environ.get(key, default)

        # Parse tracks: split on both spaces AND commas for backward compat
        raw_tracks = _env_str("HARNESS_TRACKS", "a b c d e f")
        tracks = re.split(r"[,\s]+", raw_tracks.strip())
        tracks = [t for t in tracks if t]

        # Parse --only: comma-separated, normalize each ID
        only: list[str] = []
        raw_only = args.only or _env_str("HARNESS_ONLY", "")
        if raw_only:
            only = [normalize_id(x) for x in re.split(r"[,\s]+", raw_only) if x]

        # Parse --skip: comma-separated, normalize each ID
        skip: list[str] = []
        raw_skip = args.skip or _env_str("HARNESS_SKIP", "")
        if raw_skip:
            skip = [normalize_id(x) for x in re.split(r"[,\s]+", raw_skip) if x]

        # Engine: CLI overrides env, lowercase
        engine = (args.engine or _env_str("HARNESS_ENGINE", "codex")).lower()
        if engine not in ("claude", "codex"):
            print(f"error: --engine must be 'claude' or 'codex', got '{engine}'", file=sys.stderr)
            sys.exit(1)

        # Resume validation
        resume_branch = args.resume_branch or _env_str("HARNESS_RESUME_BRANCH", "")
        resume_cycle = args.resume_cycle if args.resume_cycle is not None else _env_int("HARNESS_RESUME_CYCLE", 1)
        if resume_cycle > 1 and not resume_branch:
            print("error: --resume-cycle requires --resume-branch", file=sys.stderr)
            sys.exit(1)

        # Fixer workers: CLI overrides env
        fixer_workers = args.fixer_workers if args.fixer_workers is not None else _env_int("FIXER_WORKERS", 1)
        if fixer_workers < 1:
            print(f"error: --fixer-workers must be >= 1, got {fixer_workers}", file=sys.stderr)
            sys.exit(1)

        # Fixer domains: space/comma separated, uppercase
        raw_fixer_domains = _env_str("FIXER_DOMAINS", "A B C")
        fixer_domains = [d.upper() for d in re.split(r"[,\s]+", raw_fixer_domains.strip()) if d]

        return cls(
            max_cycles=args.cycles if args.cycles is not None else _env_int("MAX_CYCLES", 5),
            dry_run=args.dry_run or _env_bool("DRY_RUN", False),
            engine=engine,
            eval_only=args.eval_only or _env_bool("EVAL_ONLY", False),
            only=only,
            phase=args.phase or _env_str("PHASE", "all"),
            skip=skip,
            resume_branch=resume_branch,
            resume_cycle=resume_cycle,
            max_retries=_env_int("MAX_RETRIES", 3),
            retry_delay=_env_int("RETRY_DELAY", 30),
            tracks=tracks,
            staging_root=_env_str("HARNESS_STAGING_ROOT", "/tmp"),
            auto_cleanup=_env_bool("HARNESS_AUTO_CLEANUP", False),
            max_walltime=_env_int("HARNESS_MAX_WALLTIME", 14400),
            jwt_ttl=_env_int("HARNESS_JWT_TTL", 28800),
            max_fix_attempts=_env_int("MAX_FIX_ATTEMPTS", 2),
            keep_state=_env_bool("HARNESS_KEEP_STATE", False),
            eval_model=_env_str("EVAL_MODEL", "opus"),
            fixer_model=_env_str("FIXER_MODEL", "opus"),
            codex_eval_profile=_env_str("CODEX_EVAL_PROFILE", "harness-evaluator"),
            codex_fixer_profile=_env_str("CODEX_FIXER_PROFILE", "harness-fixer"),
            codex_verifier_profile=_env_str("CODEX_VERIFIER_PROFILE", "harness-verifier"),
            codex_eval_model=_env_str("CODEX_EVAL_MODEL", ""),
            codex_fixer_model=_env_str("CODEX_FIXER_MODEL", ""),
            codex_verifier_model=_env_str("CODEX_VERIFIER_MODEL", ""),
            backend_port=_env_int("BACKEND_PORT", 8080),
            backend_cmd=_env_str("BACKEND_CMD", "uvicorn src.api.main:create_app --factory --host 0.0.0.0 --port 8080"),
            backend_log=_env_str("BACKEND_LOG", "/tmp/freddy-backend.log"),
            fixer_workers=fixer_workers,
            fixer_domains=fixer_domains,
            frontend_url=_env_str("FRONTEND_URL", "http://localhost:3000"),
            backend_url=_env_str("BACKEND_URL", "http://localhost:8080"),
        )


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="python -m harness",
        description="QA eval-fix loop orchestrator",
    )
    p.add_argument("--cycles", type=int, default=None, help="Max evaluation-fix cycles (default: 5)")
    p.add_argument("--dry-run", action="store_true", default=False, help="Run 1 track, 1 capability only")
    p.add_argument("--engine", type=str, default=None, help="Engine: claude or codex (default: codex)")
    p.add_argument("--eval-only", action="store_true", default=False, help="Run evaluators, skip fixer, exit after cycle")
    p.add_argument("--only", type=str, default=None, help="Comma-separated capability IDs to test (e.g. A5,B4)")
    p.add_argument("--phase", type=str, default=None, help="Phase filter: all, 1, 2, or 3")
    p.add_argument("--skip", type=str, default=None, help="Comma-separated capability IDs to skip")
    p.add_argument("--resume-branch", type=str, default=None, help="Existing staging branch to resume from")
    p.add_argument("--resume-cycle", type=int, default=None, help="Cycle number to start from when resuming")
    p.add_argument("--fixer-workers", type=int, default=None, help="Parallel fixer workers per domain (default: 1 = sequential)")
    return p.parse_args(argv)
