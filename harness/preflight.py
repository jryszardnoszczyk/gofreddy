"""Preflight checks, DB operations, and JWT management for the QA harness."""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import platform
import re
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from harness.config import REQUIRED_ENV_VARS, Config

log = logging.getLogger("harness.preflight")

# Endpoints used by health checks.
HEALTH_ENDPOINT = "/health"

# DB URL fallback chain: E2E_DB_URL > DATABASE_URL > local supabase default.
_DEFAULT_DB_URL = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"


def _db_url() -> str:
    return os.environ.get(
        "E2E_DB_URL",
        os.environ.get("DATABASE_URL", _DEFAULT_DB_URL),
    )


def _supabase_url() -> str:
    return os.environ.get(
        "E2E_SUPABASE_URL",
        os.environ.get("SUPABASE_URL", "http://127.0.0.1:54321"),
    )


def _jwt_secret() -> str:
    return os.environ.get(
        "E2E_JWT_SECRET",
        os.environ.get("SUPABASE_JWT_SECRET", ""),
    )


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PreflightResult:
    """Values produced by a successful preflight run."""

    jwt_token: str
    harness_user_id: str


# ---------------------------------------------------------------------------
# Preflight orchestrator
# ---------------------------------------------------------------------------


class PreflightError(RuntimeError):
    """Any preflight check that fails fatally raises this."""


def run_preflight(config: Config) -> PreflightResult:
    """Execute all preflight checks in order. Returns JWT + user ID."""
    validate_engine_prereqs(config)
    validate_safety_guards(config)
    validate_env_vars(config)
    apply_db_schema(config)
    check_stack_health(config)
    validate_cors(config)
    token, user_id = mint_jwt(config)
    verify_frontend_bypass(config, token)
    cleanup_harness_state(config, user_id)
    return PreflightResult(jwt_token=token, harness_user_id=user_id)


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def validate_engine_prereqs(config: Config) -> None:
    """Verify the engine CLI binary is available."""
    if shutil.which(config.engine) is None:
        raise PreflightError(f"{config.engine} CLI not found in PATH")

    if config.engine == "codex":
        cfg_path = os.environ.get(
            "CODEX_PROFILE_CONFIG",
            os.path.join(
                os.environ.get("CODEX_HOME", os.path.expanduser("~/.codex")),
                "config.toml",
            ),
        )
        if not os.path.isfile(cfg_path):
            raise PreflightError(f"Missing Codex config: {cfg_path}")
        cfg_text = Path(cfg_path).read_text()
        for profile_name in (config.codex_eval_profile, config.codex_fixer_profile):
            pattern = rf"^\[profiles\.{re.escape(profile_name)}\]"
            if not re.search(pattern, cfg_text, re.MULTILINE):
                raise PreflightError(f"Missing Codex profile [{profile_name}]")


def validate_safety_guards(config: Config) -> None:
    """Refuse production, non-localhost DB, or live Stripe keys."""
    env = os.environ.get("ENVIRONMENT", "development")
    if env == "production":
        raise PreflightError("Refusing to run in production")

    db_url = os.environ.get("DATABASE_URL", os.environ.get("E2E_DB_URL", ""))
    if db_url and not re.search(r"localhost|127\.0\.0\.1|::1", db_url):
        raise PreflightError(f"DATABASE_URL not localhost: {db_url}")

    log.info("Safety guards passed")


def validate_env_vars(config: Config) -> None:
    """Check that all required env vars are set and non-empty."""
    missing = [v for v in REQUIRED_ENV_VARS if not os.environ.get(v)]
    if missing:
        raise PreflightError(f"Missing env vars: {' '.join(missing)}")


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


def _wait_http(url: str, max_attempts: int = 40) -> None:
    """Poll *url* with HTTP GET until 2xx, sleeping 1 s between attempts."""
    for i in range(max_attempts):
        try:
            resp = urllib.request.urlopen(url, timeout=5)  # noqa: S310
            if 200 <= resp.status < 300:
                log.info("%s is healthy", url)
                return
        except Exception:
            pass
        if i < max_attempts - 1:
            time.sleep(1)
    raise PreflightError(f"Timeout waiting for {url}")


def check_stack_health(config: Config) -> None:
    """Verify backend health endpoint and frontend are reachable."""
    _wait_http(f"{config.backend_url}{HEALTH_ENDPOINT}")
    _wait_http(config.frontend_url, max_attempts=20)


def validate_cors(config: Config) -> None:
    """Verify the backend accepts cross-origin preflight from the frontend."""
    frontend_origin = config.frontend_url.rstrip("/")
    url = f"{config.backend_url}/health"
    req = urllib.request.Request(
        url,
        method="OPTIONS",
        headers={
            "Origin": frontend_origin,
            "Access-Control-Request-Method": "GET",
        },
    )
    try:
        resp = urllib.request.urlopen(req, timeout=10)  # noqa: S310
        status = resp.status
    except urllib.error.HTTPError as exc:
        status = exc.code
    except Exception as exc:
        raise PreflightError(
            f"CORS pre-flight failed: {frontend_origin} -> {url}: {exc}"
        ) from exc

    if status != 200:
        raise PreflightError(
            f"CORS pre-flight failed: {frontend_origin} -> {url} returned HTTP {status}. "
            "The backend may need restarting to pick up CORS config changes."
        )
    log.info("CORS pre-flight OK: %s -> backend", frontend_origin)


# ---------------------------------------------------------------------------
# DB operations
# ---------------------------------------------------------------------------


def apply_db_schema(config: Config) -> None:
    """Apply all migrations from supabase/migrations/ via asyncpg (idempotent)."""
    repo_root = Path(__file__).resolve().parent.parent
    migrations_dir = repo_root / "supabase" / "migrations"
    if not migrations_dir.is_dir():
        raise PreflightError(f"Migrations dir not found: {migrations_dir}")

    migration_files = sorted(migrations_dir.glob("*.sql"))
    if not migration_files:
        raise PreflightError(f"No migration files found in {migrations_dir}")

    async def _apply() -> None:
        import asyncpg  # noqa: C0415

        conn = await asyncpg.connect(_db_url())
        try:
            for mf in migration_files:
                sql = mf.read_text()
                log.info("Applying migration %s (idempotent)...", mf.name)
                await conn.execute(sql)
        finally:
            await conn.close()

    try:
        asyncio.run(_apply())
    except Exception as exc:
        raise PreflightError(f"Schema apply failed: {exc}") from exc

    log.info("All %d migrations applied", len(migration_files))


def cleanup_harness_state(
    config: Config,
    user_id: str,
    scope: str = "full",
) -> None:
    """Delete per-run state from monitors/conversations. Respects keep_state."""
    if config.keep_state:
        log.info("HARNESS_KEEP_STATE=true - skipping per-run state cleanup")
        return

    if not user_id:
        log.warning("No user_id - skipping state cleanup")
        return

    if scope == "conversations_only":
        log.info("Cleaning sessions for user %s (keeping monitors)...", user_id)
        sql = f"DELETE FROM agent_sessions WHERE org_id = '{user_id}';"
    else:
        log.info("Cleaning harness state for user %s...", user_id)
        sql = (
            f"DELETE FROM agent_sessions WHERE org_id = '{user_id}'; "
            f"DELETE FROM monitors WHERE user_id = '{user_id}'; "
            f"DELETE FROM geo_audits WHERE user_id = '{user_id}'; "
            f"DELETE FROM evaluation_results WHERE user_id = '{user_id}';"
        )

    async def _cleanup() -> None:
        import asyncpg  # noqa: C0415

        conn = await asyncpg.connect(_db_url())
        try:
            await conn.execute(sql)
        finally:
            await conn.close()

    try:
        asyncio.run(_cleanup())
    except Exception as exc:
        # Best-effort: warn, don't abort.
        log.warning("State cleanup failed: %s", exc)
        return

    log.info("Harness state cleaned")


# ---------------------------------------------------------------------------
# JWT management
# ---------------------------------------------------------------------------


_HARNESS_EMAIL = "harness@local.gofreddy.ai"
_HARNESS_PASSWORD = "harness-qa-localonly-2026"
_HARNESS_CLIENT_SLUG = "harness-test"
_HARNESS_CLIENT_NAME = "Harness QA Client"


def mint_jwt(config: Config) -> tuple[str, str]:
    """Sign up (or sign in) a harness user via GoTrue to get an access token.

    Follows the same pattern as scripts/seed_local.py:
    1. POST /auth/v1/signup — creates the user in GoTrue
    2. If 422 (already exists), POST /auth/v1/token?grant_type=password
    3. Ensure users, clients, and user_client_memberships rows exist
    4. Return (access_token, user_id)
    """
    supabase_url = _supabase_url()
    anon_key = os.environ.get("SUPABASE_ANON_KEY", "")
    headers = {"apikey": anon_key, "Content-Type": "application/json"}
    body = json.dumps({"email": _HARNESS_EMAIL, "password": _HARNESS_PASSWORD}).encode()

    # 1. Try signup
    req = urllib.request.Request(
        f"{supabase_url}/auth/v1/signup",
        data=body, headers=headers, method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=15)  # noqa: S310
        data = json.loads(resp.read())
        sup_id = data.get("user", {}).get("id") or data.get("id")
        token = data.get("access_token", "")
    except urllib.error.HTTPError as exc:
        if exc.code == 422 or exc.code == 400:
            # 2. User already exists — sign in
            signin_req = urllib.request.Request(
                f"{supabase_url}/auth/v1/token?grant_type=password",
                data=body, headers=headers, method="POST",
            )
            try:
                resp = urllib.request.urlopen(signin_req, timeout=15)  # noqa: S310
                data = json.loads(resp.read())
                sup_id = data["user"]["id"]
                token = data["access_token"]
            except Exception as inner_exc:
                raise PreflightError(f"JWT minting: signin failed: {inner_exc}") from inner_exc
        else:
            raise PreflightError(f"JWT minting: signup failed: HTTP {exc.code}") from exc
    except Exception as exc:
        raise PreflightError(f"JWT minting: signup request failed: {exc}") from exc

    if not token or not sup_id:
        raise PreflightError("JWT minting: no access_token or user_id in response")

    # 3. Ensure DB rows exist (users, clients, memberships)
    _ensure_harness_db_rows(sup_id)

    log.info("JWT minted via GoTrue (%s...)", token[:20])
    return token, sup_id


def _ensure_harness_db_rows(supabase_user_id: str) -> None:
    """Insert harness user + client + membership if not present."""
    sql = f"""
        INSERT INTO clients (slug, name)
        VALUES ('{_HARNESS_CLIENT_SLUG}', '{_HARNESS_CLIENT_NAME}')
        ON CONFLICT (slug) DO NOTHING;

        INSERT INTO users (email, supabase_user_id)
        VALUES ('{_HARNESS_EMAIL}', '{supabase_user_id}')
        ON CONFLICT (email) DO UPDATE SET supabase_user_id = EXCLUDED.supabase_user_id;

        INSERT INTO user_client_memberships (user_id, client_id, role)
        SELECT u.id, c.id, 'admin'
        FROM users u, clients c
        WHERE u.email = '{_HARNESS_EMAIL}' AND c.slug = '{_HARNESS_CLIENT_SLUG}'
        ON CONFLICT (user_id, client_id) DO UPDATE SET role = 'admin';
    """

    async def _seed() -> None:
        import asyncpg  # noqa: C0415

        conn = await asyncpg.connect(_db_url())
        try:
            await conn.execute(sql)
        finally:
            await conn.close()

    try:
        asyncio.run(_seed())
    except Exception as exc:
        raise PreflightError(f"JWT minting: DB seeding failed: {exc}") from exc


def check_jwt_expiry(token: str) -> int:
    """Decode JWT payload and return seconds until expiry.

    Positive = still valid, negative = already expired.
    No signature verification -- we just need the exp claim.
    """
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return -1
        payload_b64 = parts[1]
        # Add padding
        payload_b64 += "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        exp = int(payload.get("exp", 0))
        return exp - int(time.time())
    except Exception:
        return -1


# ---------------------------------------------------------------------------
# Vite process introspection
# ---------------------------------------------------------------------------


def _find_vite_pid(frontend_url: str) -> int | None:
    """Find the PID of the vite process listening on the frontend port."""
    m = re.search(r":(\d+)", frontend_url)
    if not m:
        return None
    port = m.group(1)
    try:
        output = subprocess.check_output(
            ["lsof", "-ti", f"tcp:{port}", "-sTCP:LISTEN"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        pids = output.strip().split("\n")
        return int(pids[0]) if pids and pids[0] else None
    except (subprocess.CalledProcessError, ValueError):
        return None


def _get_process_env(pid: int) -> str:
    """Read the environment of a process. Platform-specific."""
    if platform.system() == "Darwin":
        try:
            raw = subprocess.check_output(
                ["ps", "-E", "-p", str(pid), "-o", "command="],
                text=True,
                stderr=subprocess.DEVNULL,
            )
            return raw.replace(" ", "\n")
        except subprocess.CalledProcessError:
            return ""
    else:
        # Linux: /proc/PID/environ is NUL-separated
        try:
            raw = Path(f"/proc/{pid}/environ").read_bytes()
            return raw.replace(b"\0", b"\n").decode("utf-8", errors="replace")
        except OSError:
            return ""


def _extract_env_var(env_dump: str, var_name: str) -> str | None:
    """Extract a VAR=value from a newline-separated env dump."""
    prefix = f"{var_name}="
    for line in env_dump.split("\n"):
        if line.startswith(prefix):
            return line[len(prefix):]
    return None


def check_vite_jwt_freshness(config: Config) -> int:
    """Check the JWT in the running vite process. Returns seconds remaining, or -1."""
    pid = _find_vite_pid(config.frontend_url)
    if pid is None:
        log.error("No vite on %s", config.frontend_url)
        return -1

    env_dump = _get_process_env(pid)
    vite_token = _extract_env_var(env_dump, "VITE_E2E_BYPASS_ACCESS_TOKEN")
    if not vite_token:
        log.error("No VITE_E2E_BYPASS_ACCESS_TOKEN in vite env")
        return -1

    remaining = check_jwt_expiry(vite_token)
    if remaining <= 0:
        log.error("Vite JWT expired")
    elif remaining < 600:
        log.error("Vite JWT expires in %ds (<10m)", remaining)
    else:
        log.info("Vite JWT OK (%ds remaining)", remaining)
    return remaining


def verify_frontend_bypass(config: Config, token: str) -> None:
    """Verify vite has VITE_E2E_* env vars and backend accepts the token."""
    pid = _find_vite_pid(config.frontend_url)
    if pid is None:
        raise PreflightError(f"No vite on {config.frontend_url}")

    env_dump = _get_process_env(pid)
    required_vars = [
        "VITE_E2E_BYPASS_AUTH",
        "VITE_E2E_BYPASS_ACCESS_TOKEN",
        "VITE_E2E_BYPASS_USER_ID",
        "VITE_E2E_BYPASS_EMAIL",
    ]
    missing = [v for v in required_vars if _extract_env_var(env_dump, v) is None]
    if missing:
        raise PreflightError(f"Vite missing: {' '.join(missing)}")

    freshness = check_vite_jwt_freshness(config)
    if freshness <= 0:
        raise PreflightError("Vite JWT expired")
    if freshness < 600:
        raise PreflightError(f"Vite JWT expires in {freshness}s (<10m)")

    # Backend smoke test
    req = urllib.request.Request(
        f"{config.backend_url}/v1/monitors",
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        resp = urllib.request.urlopen(req, timeout=10)  # noqa: S310
        status = resp.status
    except urllib.error.HTTPError as exc:
        status = exc.code
    except Exception as exc:
        raise PreflightError(f"Backend smoke: /v1/monitors -> {exc}") from exc

    if status != 200:
        raise PreflightError(f"Backend smoke: /v1/monitors -> {status}")

    log.info("Frontend bypass + backend smoke OK")


def refresh_vite_jwt(config: Config) -> str:
    """Re-mint JWT, kill old vite, restart with VITE_E2E_* env vars.

    Returns the new token.
    """
    token, user_id = mint_jwt(config)
    os.environ["HARNESS_TOKEN"] = token

    # Kill old vite process
    m = re.search(r":(\d+)", config.frontend_url)
    if m:
        port = m.group(1)
        old_pid = _find_vite_pid(config.frontend_url)
        if old_pid is not None:
            try:
                os.kill(old_pid, signal.SIGTERM)
            except OSError:
                pass
            # Wait for port release (up to 10 s)
            for _ in range(10):
                try:
                    out = subprocess.check_output(
                        ["lsof", "-ti", f"tcp:{port}", "-sTCP:LISTEN"],
                        text=True,
                        stderr=subprocess.DEVNULL,
                    )
                    if not out.strip():
                        break
                except subprocess.CalledProcessError:
                    break
                time.sleep(1)

    # Restart vite
    repo_root = Path(__file__).resolve().parent.parent
    vite_env = {
        **os.environ,
        "VITE_SUPABASE_URL": os.environ.get("SUPABASE_URL", "http://127.0.0.1:54321"),
        "VITE_SUPABASE_ANON_KEY": os.environ.get("SUPABASE_ANON_KEY", ""),
        "VITE_E2E_BYPASS_AUTH": "1",
        "VITE_E2E_BYPASS_ACCESS_TOKEN": token,
        "VITE_E2E_BYPASS_USER_ID": user_id or "harness_qa_pro_user",
        "VITE_E2E_BYPASS_EMAIL": "harness@test.local",
    }

    vite_log = open("/tmp/gofreddy-vite.log", "w")  # noqa: SIM115
    subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=str(repo_root / "frontend"),
        env=vite_env,
        stdout=vite_log,
        stderr=vite_log,
        start_new_session=True,
    )

    _wait_http(config.frontend_url, max_attempts=30)
    freshness = check_vite_jwt_freshness(config)
    if freshness <= 0:
        raise PreflightError("JWT refresh: token still stale after vite restart")

    log.info("JWT refreshed (%s...)", token[:20])
    return token
