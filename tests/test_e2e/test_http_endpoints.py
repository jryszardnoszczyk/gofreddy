"""End-to-end HTTP endpoint coverage.

This suite is intentionally "real app" testing:
- Runs Uvicorn and hits localhost over HTTP (not FastAPI TestClient).
- Uses a real Postgres database (video_intelligence_test by default).
- Forces deterministic behavior by setting EXTERNALS_MODE=fake and
  TASK_CLIENT_MODE=mock to avoid
  Gemini/R2/Apify/ScrapeCreators/yt-dlp network calls.

Route-to-test matrix (primary endpoints for this agent):
- GET  /health                         -> scripts/smoke_test.sh (200)
- GET  /ready                          -> scripts/smoke_test.sh (200; DB required)
- POST /v1/search                      -> scripts/smoke_test.sh (401/403, 422, 200)
- POST /v1/analyze/videos              -> scripts/smoke_test.sh (401, 422, 200)
- POST /v1/analyze/videos/async         -> scripts/smoke_test.sh (401/403, 422, 202)
- GET  /v1/analysis/{id}               -> scripts/smoke_test.sh (404, 200 via DB lookup)
- GET  /v1/analysis/jobs               -> scripts/smoke_test.sh (401/403, 200, 400 invalid status, 422 bad pagination)
- GET  /v1/analysis/jobs/{job_id}       -> scripts/smoke_test.sh (404, 200)
- DEL  /v1/analysis/jobs/{job_id}       -> scripts/smoke_test.sh (401/403, 200)
- POST /v1/analyze/creator             -> scripts/smoke_test.sh (401/403, 200)
- GET  /v1/creators/{platform}/{user}  -> scripts/smoke_test.sh (401/403, 200 in fake mode)

We keep this thin and delegate the heavy lifting to scripts/smoke_test.sh so
developers can also run it directly while bug-hunting.
"""

from __future__ import annotations

import os
import shutil
import subprocess

import pytest


def _truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _db_prereqs_ok(db_url: str) -> tuple[bool, str]:
    """Return whether smoke-test DB prerequisites are available."""
    if shutil.which("psql") is None:
        return False, "psql is not installed"

    checks = [
        ("SELECT 1", "cannot connect to database"),
        ("SELECT 1 FROM users LIMIT 1", "required schema table 'users' is missing"),
    ]
    for sql, reason in checks:
        proc = subprocess.run(
            ["psql", "-d", db_url, "-Atc", sql],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if proc.returncode != 0:
            return False, reason

    return True, ""


@pytest.mark.db
def test_http_endpoints_smoke_scan() -> None:
    env = os.environ.copy()
    db_url = env.setdefault(
        "DB_URL",
        env.get("DATABASE_URL", "postgresql://localhost:5432/video_intelligence_test"),
    )

    db_ok, reason = _db_prereqs_ok(db_url)
    if not db_ok:
        if _truthy(env.get("CI")):
            pytest.fail(
                f"DB-backed smoke prerequisites unavailable in CI ({reason}): {db_url}",
                pytrace=False,
            )
        pytest.skip(f"DB-backed smoke prerequisites unavailable ({reason}): {db_url}")

    # Deterministic, no external providers.
    env.setdefault("EXTERNALS_MODE", "fake")
    env.setdefault("TASK_CLIENT_MODE", "mock")
    # Avoid fixed-port collisions without opening sockets in the test process.
    env.setdefault("PORT", str(18000 + (os.getpid() % 10000)))
    # Keep CI/local scans resilient on low-disk systems.
    env.setdefault("SMOKE_LOG_FILE", "/dev/null")

    proc = subprocess.run(
        ["bash", "scripts/smoke_test.sh"],
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )

    if proc.returncode != 0:
        raise AssertionError(
            "scripts/smoke_test.sh failed.\n\nSTDOUT:\n"
            + (proc.stdout or "")
            + "\n\nSTDERR:\n"
            + (proc.stderr or "")
        )
