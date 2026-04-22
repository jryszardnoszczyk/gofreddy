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

# Per-track scope allowlist (Tier C — see src/shared/safety/tier_c.py). Each
# track's fixer is permitted to modify only paths matching its pattern; any
# other dirty path is a scope violation that triggers rollback. Defined here
# (not in harness/safety.py) so the safety module can stay a pure shim that
# re-exports the shared primitives — mixed-logic shims fossilize.
SCOPE_ALLOWLIST: dict[str, re.Pattern[str]] = {
    "a": re.compile(r"^(cli/freddy/|pyproject\.toml$)"),
    "b": re.compile(r"^(src/|autoresearch/)"),
    "c": re.compile(r"^frontend/"),
}

# Auto-derived from SCOPE_ALLOWLIST so the per-track scope and the
# fixer-reachable surface stay in lockstep. A "fixer-reachable" leak is a file
# under any track's scope; paths outside every track's allowlist (docs/,
# .claude/, harness/, tests/, README, etc.) can't be fixer-caused even if
# they became dirty during a run — concurrent dev activity on those paths is
# not a leak from the harness's perspective.
_FIXER_REACHABLE: re.Pattern[str] = re.compile(
    "|".join(p.pattern for p in SCOPE_ALLOWLIST.values())
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
    backend_port: int = 8000
    backend_cmd: str = ".venv/bin/python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000"
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
            backend_port=backend_port,
            backend_cmd=f".venv/bin/python -m uvicorn src.api.main:app --host 127.0.0.1 --port {backend_port}",
            backend_url=backend_url,
            frontend_url=frontend_url,
            staging_root=staging_root.resolve(),
            keep_worktree=bool(getattr(args, "keep_worktree", False)),
        )
