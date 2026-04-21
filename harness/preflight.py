"""Fail-loud preflight. check_all(config) returns the minted JWT for smoke-check use."""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import shutil
import subprocess
import time
import tomllib
import urllib.error
import urllib.request
from pathlib import Path
from typing import TYPE_CHECKING

from harness.config import REQUIRED_ENV_VARS

if TYPE_CHECKING:
    from harness.config import Config

log = logging.getLogger("harness.preflight")

_HARNESS_EMAIL = "harness@gofreddy.local"
_HARNESS_PASSWORD = "harness-qa-localonly-2026"
_HARNESS_CLIENT_SLUG = "harness-test"
_HARNESS_CLIENT_NAME = "Harness QA Client"

_PROD_SIGNALS = ("supabase.co", "amazonaws.com", "railway.app", "vercel.app")


class PreflightError(RuntimeError):
    """Raised when a preflight check fails. Single-sentence actionable messages."""


def check_all(config: "Config") -> str:
    """Run every preflight check in order; return minted JWT on success."""
    missing = [v for v in REQUIRED_ENV_VARS if not os.environ.get(v)]
    if missing:
        raise PreflightError(f"missing env vars: {', '.join(missing)} — populate .env before running")
    _check_safety_guards(config)
    _check_codex_profiles(config)
    _check_cli_integrity()
    _check_gh_auth()
    _apply_db_schema()
    token, user_id = _mint_jwt(config)
    _check_jwt_envelope(token, config)
    _wait_stack_healthy(config)
    log.info("preflight complete (user=%s)", user_id[:8])
    return token


def _check_safety_guards(config: "Config") -> None:
    if os.environ.get("ENVIRONMENT", "").lower() == "production":
        raise PreflightError("ENVIRONMENT=production — refusing to run harness against prod")
    db_url = os.environ.get("DATABASE_URL", "")
    if any(sig in db_url for sig in _PROD_SIGNALS):
        raise PreflightError(f"DATABASE_URL looks non-local ({db_url[:40]}...) — harness must run against local Supabase")


def _check_codex_profiles(config: "Config") -> None:
    """Profiles must exist AND each must set shell_environment_policy.inherit = 'all'."""
    cfg_path = Path.home() / ".codex" / "config.toml"
    if not cfg_path.is_file():
        raise PreflightError(f"codex config not found at {cfg_path} — run `codex login` or create profiles")
    try:
        data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise PreflightError(f"codex config at {cfg_path} is not valid TOML: {exc}") from exc

    profiles = data.get("profiles") or {}
    required = (config.codex_eval_profile, config.codex_fixer_profile, config.codex_verifier_profile)
    for name in required:
        prof = profiles.get(name)
        if prof is None:
            raise PreflightError(f"missing codex profile [{name}] in {cfg_path}")
        inherit = prof.get("shell_environment_policy", {}).get("inherit")
        if inherit != "all":
            raise PreflightError(
                f"profile [{name}] must set shell_environment_policy.inherit = \"all\" "
                f"(got {inherit!r}) — PATH prepend survival depends on this"
            )


def _check_cli_integrity() -> None:
    freddy = Path(".venv/bin/freddy")
    if not freddy.is_file():
        raise PreflightError(".venv/bin/freddy not found — run `uv pip install -e .` to install the console script")
    proc = subprocess.run([str(freddy), "--help"], capture_output=True, text=True, check=False, timeout=15)
    if proc.returncode != 0:
        raise PreflightError(
            f".venv/bin/freddy --help exited {proc.returncode} — run `uv pip install -e .` to rebuild the console script"
        )


def _check_gh_auth() -> None:
    if shutil.which("gh") is None:
        raise PreflightError("gh CLI not in PATH — install GitHub CLI (`brew install gh`) before running")
    proc = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True, check=False, timeout=15)
    if proc.returncode != 0:
        raise PreflightError("gh auth status failed — run `gh auth login` before the harness")


def _apply_db_schema() -> None:
    migrations_dir = Path("supabase") / "migrations"
    if not migrations_dir.is_dir():
        raise PreflightError(f"migrations dir not found: {migrations_dir}")
    migrations = sorted(migrations_dir.glob("*.sql"))
    if not migrations:
        raise PreflightError(f"no migration files in {migrations_dir}")

    async def _apply() -> None:
        import asyncpg  # noqa: C0415
        conn = await asyncpg.connect(os.environ["DATABASE_URL"])
        try:
            for mf in migrations:
                await conn.execute(mf.read_text(encoding="utf-8"))
        finally:
            await conn.close()

    try:
        asyncio.run(_apply())
    except Exception as exc:
        raise PreflightError(f"schema apply failed: {exc}") from exc


def _mint_jwt(config: "Config") -> tuple[str, str]:
    """Sign up or sign in the harness user, seed DB rows, return (token, user_id)."""
    url = os.environ["SUPABASE_URL"].rstrip("/")
    headers = {"apikey": os.environ["SUPABASE_ANON_KEY"], "Content-Type": "application/json"}
    body = json.dumps({"email": _HARNESS_EMAIL, "password": _HARNESS_PASSWORD}).encode()

    def _post(path: str) -> dict:
        req = urllib.request.Request(f"{url}{path}", data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310
            return json.loads(resp.read())

    try:
        data = _post("/auth/v1/signup")
    except urllib.error.HTTPError as exc:
        if exc.code not in (400, 422):
            raise PreflightError(f"JWT mint: signup HTTP {exc.code}") from exc
        try: data = _post("/auth/v1/token?grant_type=password")
        except Exception as inner: raise PreflightError(f"JWT mint: signin failed ({inner})") from inner
    except Exception as exc:
        raise PreflightError(f"JWT mint: signup request failed ({exc})") from exc

    token = data.get("access_token", "")
    user_id = (data.get("user") or {}).get("id") or data.get("id", "")
    if not token or not user_id:
        raise PreflightError("JWT mint: response missing access_token or user id")
    _seed_harness_rows(user_id)
    return token, user_id


def _seed_harness_rows(supabase_user_id: str) -> None:
    async def _seed() -> None:
        import asyncpg  # noqa: C0415
        conn = await asyncpg.connect(os.environ["DATABASE_URL"])
        try:
            await conn.execute(
                "INSERT INTO clients (slug, name) VALUES ($1, $2) ON CONFLICT (slug) DO NOTHING",
                _HARNESS_CLIENT_SLUG, _HARNESS_CLIENT_NAME,
            )
            await conn.execute(
                "INSERT INTO users (email, supabase_user_id) VALUES ($1, $2) "
                "ON CONFLICT (email) DO UPDATE SET supabase_user_id = EXCLUDED.supabase_user_id",
                _HARNESS_EMAIL, supabase_user_id,
            )
            await conn.execute(
                "INSERT INTO user_client_memberships (user_id, client_id, role) "
                "SELECT u.id, c.id, 'admin' FROM users u, clients c "
                "WHERE u.email = $1 AND c.slug = $2 "
                "ON CONFLICT (user_id, client_id) DO UPDATE SET role = 'admin'",
                _HARNESS_EMAIL, _HARNESS_CLIENT_SLUG,
            )
        finally:
            await conn.close()

    try:
        asyncio.run(_seed())
    except Exception as exc:
        raise PreflightError(f"JWT mint: DB seed failed ({exc})") from exc


def _check_jwt_envelope(token: str, config: "Config") -> None:
    required = config.max_walltime + config.jwt_envelope_padding
    remaining = _jwt_seconds_remaining(token)
    if remaining < required:
        raise PreflightError(
            f"minted JWT TTL ({remaining}s) < max_walltime+padding ({required}s) "
            f"— raise GoTrue JWT_EXP or reduce --max-walltime"
        )


def _jwt_seconds_remaining(token: str) -> int:
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return -1
        payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return int(payload.get("exp", 0)) - int(time.time())
    except Exception:
        return -1


def _wait_stack_healthy(config: "Config") -> None:
    for url in (config.backend_url + "/health", config.frontend_url + "/"):
        if not _poll(url, timeout=30):
            raise PreflightError(f"stack not healthy: {url} did not return 200 within 30s")


def _poll(url: str, timeout: int) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:  # noqa: S310
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(1)
    return False


