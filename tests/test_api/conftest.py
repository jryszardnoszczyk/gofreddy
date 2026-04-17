"""Integration-test fixtures for the auth + portal API.

These tests hit a real local Supabase stack (spun up via `supabase start`)
and a real asyncpg pool — no service mocks. That's deliberate: we got bitten
by mock/prod divergence on the upstream project and adopted integration-first
as the project standard (see MEMORY.md feedback entry).

To run:
  supabase start               # one-time; leaves the stack running
  pytest tests/test_api/       # tests talk to 127.0.0.1:54321 and :54322
"""
from __future__ import annotations

import os
import uuid
from collections.abc import AsyncIterator
from typing import Any

import asyncpg
import httpx
import pytest
import pytest_asyncio


LOCAL_API = "http://127.0.0.1:54321"
LOCAL_DB = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
LOCAL_ANON = "sb_publishable_ACJWlzQHlZjBrEguHvfOxg_3BJgxAaH"


def _set_test_env() -> None:
    """Seed env vars for the FastAPI app lifespan before import."""
    os.environ.setdefault("SUPABASE_URL", LOCAL_API)
    os.environ.setdefault("SUPABASE_ANON_KEY", LOCAL_ANON)
    os.environ.setdefault("SUPABASE_JWT_SECRET", "unused-locally-via-jwks")
    os.environ.setdefault("DATABASE_URL", LOCAL_DB)
    os.environ.setdefault("GOFREDDY_CLIENTS_DIR", "/tmp/gofreddy-test-clients")


_set_test_env()


def _supabase_reachable() -> bool:
    try:
        r = httpx.get(f"{LOCAL_API}/auth/v1/health", timeout=1.0)
        return r.status_code < 500
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _supabase_reachable(),
    reason="local supabase not running (run `supabase start`)",
)


@pytest_asyncio.fixture(scope="session")
async def app() -> AsyncIterator[Any]:
    """Boot the FastAPI app with a live lifespan against local Supabase.

    Session-scoped so the asyncpg pool + JWKS client stay alive across tests.
    The test config in pyproject.toml sets asyncio_default_fixture_loop_scope = session.
    """
    from src.api.main import app as _app
    async with _app.router.lifespan_context(_app):
        yield _app


@pytest_asyncio.fixture
async def api_client(app) -> AsyncIterator[httpx.AsyncClient]:
    """AsyncClient with ASGI transport — no uvicorn needed."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        yield client


@pytest_asyncio.fixture
async def db() -> AsyncIterator[asyncpg.Connection]:
    """Fresh asyncpg connection per test. Tests manage their own cleanup."""
    conn = await asyncpg.connect(LOCAL_DB)
    try:
        yield conn
    finally:
        await conn.close()


@pytest_asyncio.fixture
async def test_tenant(db: asyncpg.Connection) -> AsyncIterator[dict]:
    """Provision an isolated test tenant: fresh supabase user + app user + client + membership.

    Yields {email, password, token, client_slug, user_id, client_id, role}.
    Cleans up all rows on teardown.
    """
    unique = uuid.uuid4().hex[:8]
    email = f"test-{unique}@gofreddy.test"
    password = "test-pw-2026-supersafe"
    client_slug = f"test-client-{unique}"

    # Sign up user via GoTrue (idempotent enough — UNIQUE email)
    async with httpx.AsyncClient() as c:
        r = await c.post(
            f"{LOCAL_API}/auth/v1/signup",
            headers={"apikey": LOCAL_ANON, "Content-Type": "application/json"},
            json={"email": email, "password": password},
        )
        assert r.status_code in (200, 201), f"signup failed: {r.status_code} {r.text}"
        body = r.json()
        sup_id = body.get("user", {}).get("id") or body.get("id")
        token = body.get("access_token")
        assert sup_id and token, f"unexpected signup body: {body}"

    # Insert app user + client + membership (owner role)
    user_id = await db.fetchval(
        """
        INSERT INTO users (email, supabase_user_id) VALUES ($1, $2)
        ON CONFLICT (email) DO UPDATE SET supabase_user_id = EXCLUDED.supabase_user_id
        RETURNING id
        """,
        email, sup_id,
    )
    client_id = await db.fetchval(
        "INSERT INTO clients (slug, name) VALUES ($1, $2) RETURNING id",
        client_slug, f"Test Client {unique}",
    )
    await db.execute(
        """
        INSERT INTO user_client_memberships (user_id, client_id, role)
        VALUES ($1, $2, 'owner')
        """,
        user_id, client_id,
    )

    yield {
        "email": email,
        "password": password,
        "token": token,
        "client_slug": client_slug,
        "user_id": user_id,
        "client_id": client_id,
        "role": "owner",
    }

    # Cleanup
    await db.execute("DELETE FROM user_client_memberships WHERE user_id = $1", user_id)
    await db.execute("DELETE FROM users WHERE id = $1", user_id)
    await db.execute("DELETE FROM clients WHERE id = $1", client_id)


@pytest_asyncio.fixture
async def outsider(db: asyncpg.Connection) -> AsyncIterator[dict]:
    """A user signed up but with zero memberships. For 403 testing."""
    unique = uuid.uuid4().hex[:8]
    email = f"outsider-{unique}@gofreddy.test"
    password = "test-pw-2026-supersafe"

    async with httpx.AsyncClient() as c:
        r = await c.post(
            f"{LOCAL_API}/auth/v1/signup",
            headers={"apikey": LOCAL_ANON, "Content-Type": "application/json"},
            json={"email": email, "password": password},
        )
        assert r.status_code in (200, 201)
        body = r.json()
        sup_id = body["user"]["id"]
        token = body["access_token"]

    user_id = await db.fetchval(
        """
        INSERT INTO users (email, supabase_user_id) VALUES ($1, $2)
        ON CONFLICT (email) DO UPDATE SET supabase_user_id = EXCLUDED.supabase_user_id
        RETURNING id
        """,
        email, sup_id,
    )

    yield {"email": email, "token": token, "user_id": user_id}

    await db.execute("DELETE FROM users WHERE id = $1", user_id)
