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
from .routers import competitive as competitive_router
from .routers import evaluation as evaluation_router
from .routers import geo as geo_router
from .routers import login as login_router
from .routers import monitoring as monitoring_router
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

    # Ensure the 'default' client row exists. The CLI's `--client` flag defaults
    # to "default" and the agent_sessions schema declares `client_name DEFAULT
    # 'default'`, so a fresh deploy that lacks this row will 404 every CLI
    # `session start` run by an admin user. Idempotent via ON CONFLICT.
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO clients (slug, name) VALUES ($1, $2) ON CONFLICT (slug) DO NOTHING",
            "default", "Default",
        )

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

    # ─── Competitive ad intelligence providers (ported from freddy dependencies.py:1353-1383) ─
    from ..competitive import CompetitiveSettings, ForeplayProvider, AdyntelProvider, CompetitiveAdService

    app.state.foreplay_provider = None
    app.state.adyntel_provider = None
    app.state.ad_service = None
    app.state.comp_settings = None
    try:
        comp_settings = CompetitiveSettings()
        app.state.comp_settings = comp_settings
        if comp_settings.foreplay_api_key.get_secret_value():
            app.state.foreplay_provider = ForeplayProvider(
                api_key=comp_settings.foreplay_api_key.get_secret_value(),
                timeout=comp_settings.foreplay_timeout_seconds,
                daily_credit_limit=comp_settings.foreplay_daily_credit_limit,
            )
        if comp_settings.adyntel_api_key.get_secret_value():
            app.state.adyntel_provider = AdyntelProvider(
                api_key=comp_settings.adyntel_api_key.get_secret_value(),
                email=comp_settings.adyntel_email,
                timeout=comp_settings.adyntel_timeout_seconds,
            )
        if app.state.foreplay_provider or app.state.adyntel_provider:
            app.state.ad_service = CompetitiveAdService(
                foreplay_provider=app.state.foreplay_provider,
                adyntel_provider=app.state.adyntel_provider,
                settings=comp_settings,
            )
            logger.info("Competitive ad service enabled")
    except Exception:
        logger.warning("competitive_providers_not_configured", exc_info=True)

    # ─── GEO service (ported from freddy dependencies.py:1385-1399) ────────
    from ..geo import GeoService, GeoSettings
    from ..geo.repository import PostgresGeoRepository

    app.state.geo_service = None
    try:
        geo_settings = GeoSettings()
        if geo_settings.enable_geo:
            geo_repo = PostgresGeoRepository(app.state.db_pool)
            app.state.geo_service = GeoService(
                repository=geo_repo, settings=geo_settings,
            )
            logger.info("GEO service enabled")
    except Exception:
        logger.warning("GEO service not configured — skipping", exc_info=True)

    # ─── Monitoring service (trimmed port of freddy dependencies.py:732-1083) ─
    # Permanently skipped — Path B locked, see docs/plans/2026-04-23-003 Decision #1:
    # MonitorWorker, WorkspaceBridge, AlertEvaluator, CreativePatternService,
    # analytics/deepfake/story/conversation services.
    # Kept: full adapter registry + IntentClassifier + MonitoringService construction.
    from ..monitoring.config import MonitoringSettings
    from ..monitoring.repository import PostgresMonitoringRepository
    from ..monitoring.service import MonitoringService
    from ..monitoring.models import DataSource

    monitoring_settings = MonitoringSettings()
    monitoring_repo = PostgresMonitoringRepository(app.state.db_pool)
    app.state.monitoring_settings = monitoring_settings
    app.state.monitoring_repo = monitoring_repo

    # IC backend (Influencers.club) — required for TikTok/YouTube monitoring adapters.
    # Ported from freddy dependencies.py:707-725.
    app.state.ic_backend = None
    ic_api_key = os.environ.get("IC_API_KEY", "")
    ic_backend = None
    if ic_api_key:
        try:
            from ..search.ic_backend import ICBackend
            ic_backend = ICBackend(
                api_key=ic_api_key,
                base_url=os.environ.get("IC_BASE_URL", "https://api-dashboard.influencers.club"),
            )
            await ic_backend.__aenter__()
            app.state.ic_backend = ic_backend
            logger.info("IC search backend enabled")
        except Exception:
            logger.warning("IC backend initialization failed", exc_info=True)
            ic_backend = None

    mention_fetchers: dict = {}
    try:
        from ..monitoring.adapters import BlueskyMentionFetcher
        mention_fetchers[DataSource.BLUESKY] = BlueskyMentionFetcher(settings=monitoring_settings)
    except (ImportError, Exception) as exc:
        logger.warning("bluesky adapter unavailable: %s", exc)

    if ic_backend:
        try:
            from ..monitoring.adapters import ICContentAdapter
            mention_fetchers[DataSource.TIKTOK] = ICContentAdapter(
                ic_backend, default_source=DataSource.TIKTOK, settings=monitoring_settings,
            )
            mention_fetchers[DataSource.YOUTUBE] = ICContentAdapter(
                ic_backend, default_source=DataSource.YOUTUBE, settings=monitoring_settings,
            )
        except (ImportError, Exception) as exc:
            logger.warning("ic content adapter unavailable: %s", exc)

    xpoz_key = monitoring_settings.xpoz_api_key.get_secret_value() if monitoring_settings.xpoz_api_key else ""
    if xpoz_key:
        try:
            from ..monitoring.adapters import XpozAdapter
            mention_fetchers[DataSource.TWITTER] = XpozAdapter(settings=monitoring_settings, default_source=DataSource.TWITTER)
            mention_fetchers[DataSource.INSTAGRAM] = XpozAdapter(settings=monitoring_settings, default_source=DataSource.INSTAGRAM)
            mention_fetchers[DataSource.REDDIT] = XpozAdapter(settings=monitoring_settings, default_source=DataSource.REDDIT)
        except (ImportError, Exception) as exc:
            logger.warning("xpoz adapter unavailable: %s", exc)

    newsdata_key = monitoring_settings.newsdata_api_key.get_secret_value() if monitoring_settings.newsdata_api_key else ""
    if newsdata_key:
        try:
            from ..monitoring.adapters import NewsDataAdapter
            mention_fetchers[DataSource.NEWSDATA] = NewsDataAdapter(settings=monitoring_settings)
        except (ImportError, Exception) as exc:
            logger.warning("newsdata adapter unavailable: %s", exc)

    apify_token = monitoring_settings.apify_token.get_secret_value() if monitoring_settings.apify_token else ""
    if apify_token:
        try:
            from pydantic import SecretStr as _SecretStr
            from ..monitoring.adapters import (
                FacebookMentionFetcher, LinkedInMentionFetcher,
                GoogleTrendsAdapter, TrustpilotAdapter, AppStoreAdapter, PlayStoreAdapter,
            )
            mention_fetchers[DataSource.FACEBOOK] = FacebookMentionFetcher(_SecretStr(apify_token), settings=monitoring_settings)
            mention_fetchers[DataSource.LINKEDIN] = LinkedInMentionFetcher(_SecretStr(apify_token), settings=monitoring_settings)
            mention_fetchers[DataSource.GOOGLE_TRENDS] = GoogleTrendsAdapter(apify_token, settings=monitoring_settings)
            mention_fetchers[DataSource.TRUSTPILOT] = TrustpilotAdapter(apify_token, settings=monitoring_settings)
            mention_fetchers[DataSource.APP_STORE] = AppStoreAdapter(apify_token, settings=monitoring_settings)
            mention_fetchers[DataSource.PLAY_STORE] = PlayStoreAdapter(apify_token, settings=monitoring_settings)
        except (ImportError, Exception) as exc:
            logger.warning("apify-based adapters unavailable: %s", exc)

    pod_key = monitoring_settings.pod_engine_api_key
    if pod_key:
        try:
            from ..monitoring.adapters import PodEngineAdapter
            mention_fetchers[DataSource.PODCAST] = PodEngineAdapter(pod_key, settings=monitoring_settings)
        except (ImportError, Exception) as exc:
            logger.warning("podcast adapter unavailable: %s", exc)

    cloro_key = os.environ.get("CLORO_API_KEY", "")
    if cloro_key:
        try:
            from ..monitoring.adapters.ai_search import AiSearchAdapter
            mention_fetchers[DataSource.AI_SEARCH] = AiSearchAdapter(
                settings=monitoring_settings,
                cloro_api_key=cloro_key,
            )
        except (ImportError, Exception) as exc:
            logger.warning("ai_search adapter unavailable: %s", exc)

    for source, adapter in list(mention_fetchers.items()):
        if hasattr(adapter, "__aenter__"):
            try:
                await adapter.__aenter__()
            except Exception as exc:
                logger.warning("adapter_init_failed source=%s: %s", source.value, exc)
                del mention_fetchers[source]

    app.state.mention_fetchers = mention_fetchers
    logger.info(
        "mention_adapters_registered",
        extra={"count": len(mention_fetchers), "sources": [s.value for s in mention_fetchers.keys()]},
    )

    # IntentClassifier (Gemini-based) — kept per plan; cheap, used by /classify-intent
    intent_classifier = None
    gemini_key = eval_settings.gemini_api_key.get_secret_value()
    if gemini_key:
        try:
            from google import genai
            from google.genai import types as genai_types
            from ..monitoring.intelligence.intent import IntentClassifier

            gemini_client = genai.Client(
                api_key=gemini_key,
                http_options=genai_types.HttpOptions(timeout=300_000),
            )
            intent_classifier = IntentClassifier(
                client=gemini_client,
                settings=monitoring_settings,
            )
        except Exception:
            logger.warning("IntentClassifier init failed — /classify-intent will 500", exc_info=True)

    # Construct MonitoringService. workspace_bridge=None — WorkspaceBridge
    # permanently not ported (Path B locked, see docs/plans/2026-04-23-003
    # Decision #1; only used for the workspace feature autoresearch doesn't touch).
    app.state.monitoring_service = MonitoringService(
        repository=monitoring_repo,
        settings=monitoring_settings,
        mention_fetchers=mention_fetchers,
        intent_classifier=intent_classifier,
        workspace_bridge=None,
    )
    app.state.webhook_delivery = None  # AlertEvaluator/WebhookDelivery permanently skipped — Path B locked, see docs/plans/2026-04-23-003 Decision #1

    try:
        yield
    finally:
        ic_backend = getattr(app.state, "ic_backend", None)
        if ic_backend is not None:
            try:
                await ic_backend.__aexit__(None, None, None)
            except Exception:
                logger.exception("Error closing ic_backend")
        for svc_name in ("evaluation_service", "geo_service", "ad_service",
                         "monitoring_service", "foreplay_provider", "adyntel_provider"):
            svc = getattr(app.state, svc_name, None)
            if svc is not None:
                try:
                    await svc.close()
                except Exception:
                    logger.exception("Error closing %s", svc_name)
        for source, adapter in list(getattr(app.state, "mention_fetchers", {}).items()):
            if hasattr(adapter, "__aexit__"):
                try:
                    await adapter.__aexit__(None, None, None)
                except Exception:
                    logger.exception("Error closing adapter %s", source)
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
app.include_router(geo_router.router, prefix="/v1")
app.include_router(competitive_router.router, prefix="/v1")
app.include_router(monitoring_router.router, prefix="/v1")
