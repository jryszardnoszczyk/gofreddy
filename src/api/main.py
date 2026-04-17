"""FastAPI app for gofreddy — auth + client portal.

Lean lifespan (vs freddy's which initializes 20+ services): we need only
the asyncpg pool, the Supabase settings, and the JWKS client.
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import asyncpg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from jwt import PyJWKClient

from ..auth.config import SupabaseSettings
from .users import UserRepo
from .routers import auth as auth_router
from .routers import login as login_router
from .routers import portal as portal_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize the bare minimum to serve auth + portal."""
    supabase_settings = SupabaseSettings()
    app.state.supabase_settings = supabase_settings

    # JWKS client for ES256 tokens (Supabase CLI v2.76+). Cloud Supabase uses
    # HS256 so this may 404 — that's fine, we fall back in _decode_supabase_jwt.
    try:
        jwks_url = f"{supabase_settings.supabase_url}/auth/v1/.well-known/jwks.json"
        app.state.jwks_client = PyJWKClient(jwks_url, cache_keys=True)
    except Exception:
        logger.warning("JWKS client init failed — HS256 fallback only", exc_info=True)
        app.state.jwks_client = None

    # asyncpg pool against Supabase Postgres
    database_url = os.environ["DATABASE_URL"]
    pool = await asyncpg.create_pool(database_url, min_size=1, max_size=10)
    app.state.db_pool = pool
    app.state.user_repo = UserRepo(pool)

    app.state.clients_dir = Path(os.environ.get("GOFREDDY_CLIENTS_DIR", "/data/clients"))

    try:
        yield
    finally:
        await pool.close()


app = FastAPI(
    title="gofreddy",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS: allow the marketing landing to link into the app. Same-origin in prod
# (app.gofreddy.ai), but development runs cross-origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://gofreddy.ai",
        "https://jryszardnoszczyk.github.io",
        "http://localhost:8080",
        "http://localhost:9876",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth_router.router, prefix="/v1")
app.include_router(login_router.router)
app.include_router(portal_router.router)
