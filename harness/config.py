"""Frozen Config for the harness. Builds from CLI args + environment (after loading .env)."""
from __future__ import annotations

import os
import re
from argparse import Namespace
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

REQUIRED_ENV_VARS: tuple[str, ...] = (
    "DATABASE_URL",
    "SUPABASE_URL",
    "SUPABASE_ANON_KEY",
    "SUPABASE_JWT_SECRET",
    "GEMINI_API_KEY",
)

# Fixer-reachable paths — the surface a fixer agent could plausibly have
# mutated inside the main repo (as opposed to inside the worker worktree,
# which is isolated and enforced by filesystem boundaries, not by regex).
#
# Used ONLY by leak detection: if a main-repo path matches this AND was
# absent from the pre-run dirty snapshot, it's plausibly a fixer that
# wrote via an absolute path outside its worktree — actionable leak that
# triggers rollback + cleanup. Paths outside this regex (docs/plans/,
# .github/, memory/) are operator dev activity → advisory only.
#
# Per-track scope enforcement has been REMOVED. The fixer prompt describes
# each track's allowed surface in prose; we trust the agent to stay in lane.
# Historical per-track SCOPE_ALLOWLIST was a shared-worktree safety net —
# obsolete under the per-worker isolation architecture where each worker
# owns its own worktree and peer fixers cannot interfere.
_FIXER_REACHABLE: re.Pattern[str] = re.compile(
    r"^(cli/|src/|autoresearch/|frontend/|tests/|pyproject\.toml$)"
)

# Paths the harness itself generates inside the worktree. Not fixer-originated;
# must not count as scope violations or get staged into commits.
# - `harness/blocked-<id>.md`: the fixer prompt tells the agent to write one
#   of these when it can't fix the defect (see prompts/fixer.md). It's a
#   signal, not a fix.
# - `sessions/`: the freddy CLI's default output dir. Any fixer or verifier
#   running a `freddy audit/client/...` command as part of repro writes here
#   as a side effect.
HARNESS_ARTIFACTS: re.Pattern[str] = re.compile(
    r"^(backend\.log$|\.venv(/|$)|node_modules(/|$)|clients(/|$)|"
    r"frontend/node_modules(/|$)|harness/blocked-[^/]+\.md$|sessions(/|$))"
)


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or malformed."""


@dataclass(frozen=True)
class Config:
    engine: Literal["claude", "codex"] = "claude"
    claude_mode: Literal["oauth", "bare"] = "oauth"
    eval_model: str = "opus"
    fixer_model: str = "opus"
    verifier_model: str = "opus"
    codex_eval_profile: str = "harness-evaluator"
    codex_fixer_profile: str = "harness-fixer"
    codex_verifier_profile: str = "harness-verifier"
    codex_eval_model: str = ""
    codex_fixer_model: str = ""
    codex_verifier_model: str = ""
    resume_branch: str = ""
    # max_walltime must be > _AGENT_TIMEOUT × (1 + len(_RETRY_DELAYS)) so that walltime,
    # not retry-stacked subprocess timeouts, is the authoritative budget. 4h default
    # assumes _AGENT_TIMEOUT=1800s + 3 retries = up to ~2h worst case, leaving 2h slack.
    max_walltime: int = 14400  # 4 hours
    tracks: tuple[str, ...] = ("a", "b", "c")
    # Per-finding worker pool: N isolated worktrees, each with its own backend
    # port. Fixers/verifiers run fully parallel across findings (no shared
    # worktree → no file-edit races; no shared backend → verifier sees THIS
    # fix, not a peer's). 6 matches the evaluator's default "5+ defects"
    # batch size so the post-eval fixer queue rarely idles. Minimum 1 (serial).
    max_workers: int = 6
    # Worker i uses backend_port_base + i. Default pool 8000..8005. Each
    # uvicorn opens its own Supabase connection pool; 6 × pool_size ~= 60
    # connections, well within Supabase local's default.
    backend_port_base: int = 8000
    # Worker i uses frontend_port_base + i for its isolated Vite instance,
    # so frontend fixes are verifiable against the worktree code (not the
    # main-repo /frontend). Default pool 5173..5178.
    frontend_port_base: int = 5173
    backend_cmd: str = ".venv/bin/python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000"
    # Legacy single-port fields — preserved for resume flow + tests that pre-date
    # the worker pool. Workers derive their own port from backend_port_base + i.
    backend_port: int = 8000
    backend_url: str = "http://127.0.0.1:8000"
    frontend_url: str = "http://127.0.0.1:5173"
    staging_root: Path = field(default_factory=lambda: Path.cwd() / "harness" / "runs")
    keep_worktree: bool = False
    jwt_envelope_padding: int = 600  # seconds of slack above max_walltime

    @classmethod
    def from_cli_and_env(cls, args: Namespace, env: dict[str, str] | None = None) -> "Config":
        """Build from argparse Namespace + environment. Loads .env first."""
        try:
            from dotenv import load_dotenv  # noqa: C0415 — optional import kept local
            load_dotenv()
        except ImportError:
            pass

        env_map = env if env is not None else dict(os.environ)
        missing = [v for v in REQUIRED_ENV_VARS if not env_map.get(v)]
        if missing:
            raise ConfigError(f"missing required env vars: {', '.join(missing)}")

        backend_port = int(getattr(args, "backend_port", None) or env_map.get("HARNESS_BACKEND_PORT") or 8000)
        backend_url = env_map.get("HARNESS_BACKEND_URL") or f"http://127.0.0.1:{backend_port}"
        frontend_url = env_map.get("HARNESS_FRONTEND_URL") or "http://127.0.0.1:5173"
        max_workers = int(
            getattr(args, "max_workers", None)
            or env_map.get("HARNESS_MAX_WORKERS") or 6
        )
        if max_workers < 1:
            raise ConfigError(f"--max-workers must be >= 1 (got {max_workers})")
        backend_port_base = int(
            getattr(args, "backend_port_base", None)
            or env_map.get("HARNESS_BACKEND_PORT_BASE") or backend_port
        )
        frontend_port_base = int(
            getattr(args, "frontend_port_base", None)
            or env_map.get("HARNESS_FRONTEND_PORT_BASE") or 5173
        )
        staging_root = Path(
            getattr(args, "staging_root", None)
            or env_map.get("HARNESS_STAGING_ROOT")
            or (Path.cwd() / "harness" / "runs")
        )
        max_walltime = int(getattr(args, "max_walltime", None) or env_map.get("HARNESS_MAX_WALLTIME") or 14400)

        engine = getattr(args, "engine", None) or env_map.get("HARNESS_ENGINE") or "claude"
        if engine not in ("claude", "codex"):
            raise ConfigError(f"--engine must be claude|codex (got {engine!r})")
        claude_mode = getattr(args, "claude_mode", None) or env_map.get("HARNESS_CLAUDE_MODE") or "oauth"
        if claude_mode not in ("oauth", "bare"):
            raise ConfigError(f"--claude-mode must be oauth|bare (got {claude_mode!r})")
        # Reject silent flag ignore: --engine codex doesn't use claude-specific flags.
        # Detect CLI-explicit values (argparse sets None when flag absent).
        if engine == "codex":
            claude_explicit = [
                f"--{name.replace('_', '-')}" for name in
                ("claude_mode", "eval_model", "fixer_model", "verifier_model")
                if getattr(args, name, None) is not None
            ]
            if claude_explicit:
                raise ConfigError(
                    f"--engine codex ignores {', '.join(claude_explicit)}; "
                    "set codex-specific overrides via HARNESS_CODEX_*_MODEL env vars instead"
                )

        return cls(
            engine=engine,
            claude_mode=claude_mode,
            eval_model=getattr(args, "eval_model", None) or env_map.get("HARNESS_EVAL_MODEL") or "opus",
            fixer_model=getattr(args, "fixer_model", None) or env_map.get("HARNESS_FIXER_MODEL") or "opus",
            verifier_model=getattr(args, "verifier_model", None) or env_map.get("HARNESS_VERIFIER_MODEL") or "opus",
            resume_branch=getattr(args, "resume_branch", None) or env_map.get("HARNESS_RESUME_BRANCH") or "",
            max_walltime=max_walltime,
            max_workers=max_workers,
            backend_port=backend_port,
            backend_port_base=backend_port_base,
            frontend_port_base=frontend_port_base,
            backend_cmd=f".venv/bin/python -m uvicorn src.api.main:app --host 127.0.0.1 --port {backend_port}",
            backend_url=backend_url,
            frontend_url=frontend_url,
            staging_root=staging_root.resolve(),
            keep_worktree=bool(getattr(args, "keep_worktree", False)),
        )
