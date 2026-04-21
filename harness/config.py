"""Frozen Config for the harness. Builds from CLI args + environment (after loading .env)."""
from __future__ import annotations

import os
from argparse import Namespace
from dataclasses import dataclass, field
from pathlib import Path

REQUIRED_ENV_VARS: tuple[str, ...] = (
    "DATABASE_URL",
    "SUPABASE_URL",
    "SUPABASE_ANON_KEY",
    "SUPABASE_JWT_SECRET",
    "GEMINI_API_KEY",
)


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or malformed."""


@dataclass(frozen=True)
class Config:
    codex_eval_profile: str = "harness-evaluator"
    codex_fixer_profile: str = "harness-fixer"
    codex_verifier_profile: str = "harness-verifier"
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

        return cls(
            max_walltime=max_walltime,
            backend_port=backend_port,
            backend_cmd=f".venv/bin/python -m uvicorn src.api.main:app --host 127.0.0.1 --port {backend_port}",
            backend_url=backend_url,
            frontend_url=frontend_url,
            staging_root=staging_root.resolve(),
            keep_worktree=bool(getattr(args, "keep_worktree", False)),
        )
