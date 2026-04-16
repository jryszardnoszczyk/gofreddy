"""Process-level runtime mode startup policy tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import asyncpg
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

STARTUP_SNIPPET = """
import asyncio
from src.api.main import create_app

async def main() -> None:
    app = create_app()
    async with app.router.lifespan_context(app):
        print("STARTUP_OK")

asyncio.run(main())
"""

READY_SNIPPET = """
import asyncio
import json
import httpx
from src.api.main import create_app

async def main() -> None:
    app = create_app()
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url='http://test') as client:
            response = await client.get('/ready')
            print(f"READY_STATUS={response.status_code}")
            print("READY_BODY=" + json.dumps(response.json()))

asyncio.run(main())
"""


def _run_python_snippet(snippet: str, env: dict[str, str], timeout: int = 45) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", snippet],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _base_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    return env


@pytest.mark.slow
def test_production_missing_mode_vars_fails_startup() -> None:
    env = _base_env()
    env["ENVIRONMENT"] = "production"
    env.pop("EXTERNALS_MODE", None)
    env.pop("TASK_CLIENT_MODE", None)

    proc = _run_python_snippet(STARTUP_SNIPPET, env)

    assert proc.returncode != 0
    assert "EXTERNALS_MODE" in (proc.stderr + proc.stdout)


@pytest.mark.slow
def test_production_unsafe_modes_fail_startup() -> None:
    env = _base_env()
    env["ENVIRONMENT"] = "production"
    env["EXTERNALS_MODE"] = "fake"
    env["TASK_CLIENT_MODE"] = "mock"

    proc = _run_python_snippet(STARTUP_SNIPPET, env)

    assert proc.returncode != 0
    output = proc.stderr + proc.stdout
    assert "Unsafe runtime mode" in output
    assert "EXTERNALS_MODE=real" in output


@pytest.mark.slow
def test_production_cloud_mode_without_service_account_fails_startup() -> None:
    env = _base_env()
    env["ENVIRONMENT"] = "production"
    env["EXTERNALS_MODE"] = "real"
    env["TASK_CLIENT_MODE"] = "cloud"
    env.pop("CLOUD_TASKS_SA", None)

    proc = _run_python_snippet(STARTUP_SNIPPET, env)

    assert proc.returncode != 0
    assert "CLOUD_TASKS_SA" in (proc.stderr + proc.stdout)


async def _db_available(database_url: str) -> bool:
    try:
        conn = await asyncpg.connect(database_url, timeout=3)
    except Exception:
        return False
    try:
        await conn.execute("SELECT 1")
    except Exception:
        return False
    finally:
        await conn.close()
    return True


@pytest.mark.slow
@pytest.mark.db
@pytest.mark.asyncio
async def test_non_production_defaults_startup_and_ready_reports_real_mock() -> None:
    env = _base_env()
    database_url = env.get(
        "DATABASE_URL",
        "postgresql://localhost:5432/video_intelligence_test",
    )

    if not await _db_available(database_url):
        pytest.skip(f"Database unavailable for startup policy e2e: {database_url}")

    env["DATABASE_URL"] = database_url
    env["ENVIRONMENT"] = "development"
    env.pop("EXTERNALS_MODE", None)
    env.pop("TASK_CLIENT_MODE", None)

    # Minimal required settings for full app startup in real-externals mode.
    env.setdefault("R2_ACCOUNT_ID", "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
    env.setdefault("R2_ACCESS_KEY_ID", "test_access_key")
    env.setdefault("R2_SECRET_ACCESS_KEY", "test_secret_key")
    env.setdefault("R2_BUCKET_NAME", "test-bucket")
    env.setdefault("GEMINI_API_KEY", "test_gemini_key")
    env.setdefault("SCRAPECREATORS_API_KEY", "test_scrapecreators_key")
    env.setdefault("APIFY_TOKEN", "test_apify_token")
    env.setdefault("SUPABASE_URL", "http://localhost:54321")
    env.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
    env.setdefault("SUPABASE_JWT_SECRET", "smoke-test-jwt-secret-for-local-testing-only")

    proc = _run_python_snippet(READY_SNIPPET, env, timeout=90)

    assert proc.returncode == 0, proc.stderr
    status_line = next(
        line for line in proc.stdout.splitlines() if line.startswith("READY_STATUS=")
    )
    body_line = next(
        line for line in proc.stdout.splitlines() if line.startswith("READY_BODY=")
    )

    assert status_line == "READY_STATUS=200"
    ready_body = json.loads(body_line.removeprefix("READY_BODY="))
    assert ready_body["runtime_modes"]["environment"] == "development"
    assert ready_body["runtime_modes"]["externals_mode"] == "real"
    assert ready_body["runtime_modes"]["task_client_mode"] == "mock"
