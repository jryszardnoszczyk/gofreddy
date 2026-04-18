"""FastAPI app for gofreddy — auth + client portal.

Hardening ported from freddy/src/api/main.py:
  - RequestIDMiddleware   (trace correlation)
  - SlowAPI rate limiter  (30/min default, tighter on auth)
  - Exception handlers    (normalized error envelopes)
  - Request body limit    (1MB, DoS guard)
  - Explicit CORS headers (no "*")
  - Hardened asyncpg pool (timeouts, max_queries, max_inactive)
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

import aioboto3
import asyncpg
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from jwt import PyJWKClient
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from ..auth.config import SupabaseSettings
from ..sessions.log_storage import R2SessionLogStorage
from ..sessions.repository import PostgresSessionRepository
from ..sessions.service import SessionService
from ..storage.config import R2Settings
from ..storage.r2_storage import R2VideoStorage
from .exceptions import register_exception_handlers
from .middleware import RequestIDMiddleware, limit_request_body
from .rate_limit import get_real_client_ip, limiter
from .routers import api_keys as api_keys_router
from .routers import auth as auth_router
from .routers import evaluation as evaluation_router
from .routers import login as login_router
from .routers import portal as portal_router
from .routers import sessions as sessions_router
from .users import ApiKeyRepo, UserRepo

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize the bare minimum to serve auth + portal."""
    supabase_settings = SupabaseSettings()
    app.state.supabase_settings = supabase_settings

    try:
        jwks_url = f"{supabase_settings.supabase_url}/auth/v1/.well-known/jwks.json"
        app.state.jwks_client = PyJWKClient(jwks_url, cache_keys=True, timeout=10)
    except Exception:
        logger.warning("JWKS client init failed — HS256 fallback only", exc_info=True)
        app.state.jwks_client = None

    # Hardened pool config (matches freddy dependencies.py L404-411)
    database_url = os.environ["DATABASE_URL"]
    pool = await asyncpg.create_pool(
        database_url,
        min_size=int(os.environ.get("DB_POOL_MIN_SIZE", "5")),
        max_size=int(os.environ.get("DB_POOL_MAX_SIZE", "20")),
        command_timeout=60.0,
        max_inactive_connection_lifetime=300,
        max_queries=50000,
    )
    app.state.db_pool = pool
    app.state.user_repo = UserRepo(pool)
    app.state.api_key_repo = ApiKeyRepo(pool)
    app.state.clients_dir = Path(os.environ.get("GOFREDDY_CLIENTS_DIR", "/data/clients"))

    # R2 is best-effort — if unconfigured, session log uploads fall back to Postgres.
    try:
        r2_config = R2Settings()
        aws_session = aioboto3.Session()
        app.state.r2_storage = R2VideoStorage(aws_session, r2_config)
        app.state.session_log_storage = R2SessionLogStorage(app.state.r2_storage, r2_config)
    except Exception:
        logger.warning("R2 init failed — session log uploads disabled", exc_info=True)
        app.state.r2_storage = None
        app.state.session_log_storage = None

    session_repo = PostgresSessionRepository(pool)
    app.state.session_service = SessionService(session_repo)

    # ─── EvaluationService (ported from freddy dependencies.py:528-601) ─────
    from ..evaluation.config import EvaluationSettings
    from ..evaluation.judges.gemini import GeminiJudge
    from ..evaluation.judges.openai import OpenAIJudge
    from ..evaluation.repository import PostgresEvaluationRepository
    from ..evaluation.service import EvaluationService

    eval_settings = EvaluationSettings()
    app.state.evaluation_repository = PostgresEvaluationRepository(app.state.db_pool)

    # Build the multi-model judge ensemble from the config.
    # Each entry in judge_models is a dict with at minimum {provider, model}.
    # If openai_api_key is missing, OpenAI entries are skipped with a warning
    # and the ensemble degrades gracefully to whichever providers are reachable.
    eval_judges: list[Any] = []
    _openai_key = eval_settings.openai_api_key.get_secret_value()
    for entry in eval_settings.judge_models:
        provider = entry.get("provider", "gemini").lower()
        model = entry.get("model")
        if not model:
            logger.warning("Skipping judge entry with missing model: %r", entry)
            continue
        entry_temp = entry.get("temperature", eval_settings.judge_temperature)
        if provider == "gemini":
            eval_judges.append(GeminiJudge(
                api_key=eval_settings.gemini_api_key.get_secret_value(),
                model=model,
                temperature=entry_temp,
                timeout=eval_settings.judge_timeout,
                max_retries=eval_settings.judge_max_retries,
                retry_base_delay=eval_settings.judge_retry_base_delay,
            ))
        elif provider == "openai":
            if not _openai_key:
                logger.warning(
                    "OpenAI judge %r configured but OPENAI_API_KEY is unset — "
                    "skipping. Ensemble will run with remaining judges only.",
                    model,
                )
                continue
            eval_judges.append(OpenAIJudge(
                api_key=_openai_key,
                model=model,
                temperature=entry_temp,
                timeout=eval_settings.judge_timeout,
                max_retries=eval_settings.judge_max_retries,
                retry_base_delay=eval_settings.judge_retry_base_delay,
                reasoning_effort=entry.get("reasoning_effort"),
            ))
        else:
            logger.warning("Unknown judge provider %r — skipping entry %r", provider, entry)

    if not eval_judges:
        raise RuntimeError(
            "No judges could be instantiated from eval_settings.judge_models. "
            "Check that at least one provider's API key is set."
        )
    if len(eval_judges) < len(eval_settings.judge_models):
        logger.warning(
            "evaluator_ensemble_degraded: %d/%d judges available — multi-model "
            "ensemble is running below configured capacity",
            len(eval_judges), len(eval_settings.judge_models),
        )
    if len(eval_judges) < 2:
        logger.critical(
            "evaluator_single_judge_mode: only 1 judge available — cross-model "
            "variance check is disabled; evaluator scores may be unreliable"
        )

    app.state.evaluation_service = EvaluationService(
        judges=eval_judges,
        repository=app.state.evaluation_repository,
        replicates_per_judge=eval_settings.judge_replicates_per_model,
    )

    try:
        yield
    finally:
        evaluation_service = getattr(app.state, "evaluation_service", None)
        if evaluation_service is not None:
            try:
                await evaluation_service.close()
            except Exception:
                logger.exception("Error closing evaluation_service")
        if app.state.r2_storage is not None:
            await app.state.r2_storage.close()
        await pool.close()


def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    logger.warning(
        "rate_limit_exceeded path=%s ip=%s",
        request.url.path,
        get_real_client_ip(request),
    )
    retry_after = getattr(exc, "retry_after", 60) or 60
    return JSONResponse(
        status_code=429,
        content={"error": {"code": "rate_limited", "message": str(exc.detail)}},
        headers={"Retry-After": str(retry_after)},
    )


is_production = os.environ.get("ENVIRONMENT", "development").strip().lower() == "production"

app = FastAPI(
    title="gofreddy",
    version="0.1.0",
    lifespan=lifespan,
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
)

# 1. Request ID first — every downstream log + error gets correlated
app.add_middleware(RequestIDMiddleware)

# 2. CORS — explicit origins, explicit headers
_DEFAULT_CORS_ORIGINS = [
    "https://app.gofreddy.ai",
    "https://gofreddy.ai",
    "https://jryszardnoszczyk.github.io",
    "http://localhost:5173",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:9876",
]
_raw_origins = os.environ.get("CORS_ALLOWED_ORIGINS", ",".join(_DEFAULT_CORS_ORIGINS))
allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]
if "*" in allowed_origins:
    raise ValueError(
        "CORS_ALLOWED_ORIGINS contains '*' with allow_credentials=True. Use explicit origins."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Request-ID"],
    expose_headers=["Retry-After", "X-Request-ID"],
)

# 3. Rate limiter — per-IP, 30/min default
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
app.add_middleware(SlowAPIMiddleware)

# 4. Exception handlers — normalize to {"error": {...}}
register_exception_handlers(app)

# 5. Body size limit — 1MB
app.middleware("http")(limit_request_body)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth_router.router, prefix="/v1")
app.include_router(login_router.router)
app.include_router(portal_router.router)
app.include_router(sessions_router.router, prefix="/v1")
app.include_router(api_keys_router.router, prefix="/v1")
app.include_router(evaluation_router.router, prefix="/v1")
