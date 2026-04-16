"""End-to-end HTTP tests for Pro + operational endpoints.

Goal: exercise real router behavior with real billing/auth (DB-backed Supabase JWT),
and minimal stubbing only where external providers would be required.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from pathlib import Path
from urllib.parse import urlparse, urlunparse
from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import asyncpg
import httpx
import jwt as pyjwt
import pytest
import pytest_asyncio
from fastapi import FastAPI
from pydantic import SecretStr

from src.analysis.repository import PostgresAnalysisRepository
from src.api.dependencies import get_stripe_client
from src.api.exceptions import register_exception_handlers
from src.api.rate_limit import limiter
from src.api.routers import deepfake, evolution, internal, stories, trends, usage, webhooks
from src.billing.config import StripeSettings
from src.billing.credits import BillingFlags, CreditRepository, CreditService, CreditSettings
from src.billing.repository import BillingRepository
from src.billing.service import BillingService
from src.common.enums import Platform
from src.deepfake.repository import PostgresDeepfakeRepository
from src.deepfake.service import DeepfakeService
from src.deepfake.models import Confidence, LipSyncResult, RealityDefenderResult, Verdict
from src.evolution.repository import PostgresEvolutionRepository
from src.evolution.service import EvolutionService
from src.stories.repository import PostgresStoryRepository
from src.stories.service import StoryService
from src.stories.models import StoryResult
from src.stories.storage import StoryStorageResult
from src.trends.repository import PostgresTrendRepository
from src.trends.service import TrendService
from tests.helpers.pool_adapter import SingleConnectionPool

# Test JWT secret for E2E tests
_TEST_JWT_SECRET = "e2e-test-jwt-secret-for-supabase-auth"
_TEST_SUPABASE_URL = "http://test.supabase.co"


# -----------------------------------------------------------------------------
# DB seeding helpers
# -----------------------------------------------------------------------------


async def _insert_user(
    conn,
    *,
    email: str | None = None,
    stripe_customer_id: str | None = None,
    supabase_user_id: str | None = None,
) -> tuple[UUID, str]:
    """Insert a test user. Returns (user_id, supabase_user_id)."""
    user_id = uuid4()
    email = email or f"test-{user_id.hex[:8]}@example.com"
    supabase_user_id = supabase_user_id or f"supa_{user_id.hex[:16]}"
    await conn.execute(
        "INSERT INTO users (id, email, stripe_customer_id, supabase_user_id) VALUES ($1, $2, $3, $4)",
        user_id,
        email,
        stripe_customer_id,
        supabase_user_id,
    )
    return user_id, supabase_user_id


def _make_jwt(supabase_user_id: str, email: str = "test@example.com") -> str:
    """Create a signed JWT for test auth (mimics Supabase access token)."""
    payload = {
        "sub": supabase_user_id,
        "email": email,
        "iss": f"{_TEST_SUPABASE_URL}/auth/v1",
        "aud": "authenticated",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    return pyjwt.encode(payload, _TEST_JWT_SECRET, algorithm="HS256")


def _bearer_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _insert_subscription(conn, user_id: UUID, *, tier: str = "pro", status: str = "active") -> UUID:
    now = datetime.now(timezone.utc)
    sub_id = uuid4()
    await conn.execute(
        """INSERT INTO subscriptions
           (id, user_id, stripe_subscription_id, stripe_price_id, tier, status,
            current_period_start, current_period_end, cancel_at_period_end)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
        sub_id,
        user_id,
        f"sub_{uuid4().hex[:12]}",
        "price_test",
        tier,
        status,
        now.replace(day=1),
        now.replace(day=28),
        False,
    )
    return sub_id


async def _grant_analysis_access(conn, analysis_id: UUID, user_id: UUID) -> None:
    await conn.execute(
        """INSERT INTO video_analysis_access (video_analysis_id, user_id)
           VALUES ($1, $2)
           ON CONFLICT (video_analysis_id, user_id) DO NOTHING""",
        analysis_id,
        user_id,
    )


async def _insert_trend_snapshot(
    conn,
    *,
    platform: Platform = Platform.TIKTOK,
    snapshot_date: date | None = None,
    hashtags: list[dict] | None = None,
    brands: dict[str, int] | None = None,
    sample_size: int = 150,
) -> UUID:
    snapshot_id = uuid4()
    snapshot_date = snapshot_date or date(2026, 2, 5)
    hashtags_data = json.dumps(hashtags or [])
    brands_data = json.dumps(brands or {})
    creators_data = json.dumps([])

    await conn.execute(
        """INSERT INTO trend_snapshots
           (id, snapshot_date, platform, trending_hashtags, emerging_creators,
            brand_mention_volumes, sample_size, confidence_level)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
        snapshot_id,
        snapshot_date,
        platform.value,
        hashtags_data,
        creators_data,
        brands_data,
        sample_size,
        "high" if sample_size >= 100 else "medium",
    )
    return snapshot_id


async def _seed_creator_analyses(
    conn,
    *,
    platform: Platform = Platform.TIKTOK,
    username: str = "testcreator",
    count: int = 10,
    overall_safe: bool = True,
) -> UUID:
    """Insert a creator + N video_analysis rows for evolution endpoint."""
    creator_id = uuid4()
    await conn.execute(
        "INSERT INTO creators (id, platform, username) VALUES ($1, $2, $3)",
        creator_id,
        platform.value,
        username,
    )

    def _cats_to_array(cats: dict[str, int]) -> list[dict]:
        return [{"vertical": k, "sub_category": k, "confidence": v} for k, v in cats.items()]

    for _ in range(count):
        await conn.execute(
            """INSERT INTO video_analysis
               (id, video_id, cache_key, overall_safe, overall_confidence,
                risks_detected, summary, content_categories, moderation_flags,
                model_version, creator_id)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)""",
            uuid4(),
            uuid4(),
            f"test:{uuid4().hex[:8]}:v1",
            overall_safe,
            0.9,
            "[]",
            "Test summary",
            json.dumps(_cats_to_array({"fitness": 10, "lifestyle": 5})),
            "[]",
            "1",
            creator_id,
        )

    return creator_id


def _stripe_signature_header(*, secret: str, payload: bytes, timestamp: int | None = None) -> str:
    """Compute a Stripe-compatible webhook signature header (v1)."""
    ts = timestamp or int(time.time())
    signed_payload = f"{ts}.{payload.decode('utf-8')}".encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


def _assert_tier_required_error(error: dict, *, feature: str, current_tier: str = "free") -> None:
    """Assert standardized Pro tier-gating error contract."""
    assert error["code"] == "tier_required"
    assert error["required_tier"] == "pro"
    assert error["current_tier"] == current_tier
    assert error["feature"] == feature
    assert "upgrade_url" not in error


# -----------------------------------------------------------------------------
# Minimal app builders
# -----------------------------------------------------------------------------


def _replace_db_in_dsn(dsn: str, dbname: str) -> str:
    """Replace the database name in a postgresql:// DSN."""
    parsed = urlparse(dsn)
    # Handle DSNs like postgresql://localhost/test (path="/test")
    new_path = f"/{dbname}"
    return urlunparse(parsed._replace(path=new_path))


async def _ensure_database_and_schema(database_url: str) -> None:
    """Create target database if missing, then apply schema SQL."""
    target = urlparse(database_url)
    target_db = (target.path or "").lstrip("/") or "test"

    # Safety: avoid running CREATE DATABASE against weird names.
    if not all(c.isalnum() or c in ("_", "-") for c in target_db):
        raise RuntimeError(f"Refusing to create unexpected database name: {target_db!r}")

    # Connect to maintenance DB to create the target DB if needed.
    maintenance_dsn = _replace_db_in_dsn(database_url, "postgres")
    try:
        admin_conn = await asyncpg.connect(dsn=maintenance_dsn)
    except Exception:
        # Fallback: some installs don't have "postgres" DB.
        maintenance_dsn = _replace_db_in_dsn(database_url, "template1")
        admin_conn = await asyncpg.connect(dsn=maintenance_dsn)

    try:
        exists = await admin_conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            target_db,
        )
        if not exists:
            await admin_conn.execute(f'CREATE DATABASE "{target_db}"')
    finally:
        await admin_conn.close()

    # Apply schema (idempotent).
    schema_path = Path(__file__).resolve().parents[2] / "scripts" / "setup_test_db.sql"
    sql = schema_path.read_text(encoding="utf-8")
    target_conn = await asyncpg.connect(dsn=database_url)
    try:
        await target_conn.execute(sql)
    finally:
        await target_conn.close()


@pytest_asyncio.fixture(scope="session")
async def db_pool():
    """Override default db_pool to ensure DB exists + schema applied for E2E tests."""
    database_url = os.environ.get(
        "DATABASE_URL",
        os.environ.get("DB_URL", "postgresql://localhost:5432/video_intelligence_test"),
    )
    await _ensure_database_and_schema(database_url)
    pool = await asyncpg.create_pool(dsn=database_url, min_size=2, max_size=10, command_timeout=60)
    yield pool
    await pool.close()


@pytest_asyncio.fixture
async def e2e_db_app(db_conn):
    """ASGI app with DB-backed billing and real services where feasible."""
    app = FastAPI()
    register_exception_handlers(app)

    # Routers under test
    app.include_router(usage.router, prefix="/v1")
    app.include_router(trends.router, prefix="/v1")
    app.include_router(evolution.router, prefix="/v1")
    app.include_router(deepfake.router, prefix="/v1")
    app.include_router(stories.router, prefix="/v1")
    app.include_router(webhooks.router)
    app.include_router(internal.router)

    limiter.enabled = False

    # Supabase auth — test JWT secret for token verification
    app.state.supabase_settings = SimpleNamespace(
        supabase_url=_TEST_SUPABASE_URL,
        supabase_anon_key="test-anon-key",
        supabase_jwt_secret=SecretStr(_TEST_JWT_SECRET),
    )

    pool = SingleConnectionPool(db_conn)

    # Billing (real DB-backed auth + tier)
    app.state.billing_flags = BillingFlags()
    app.state.credit_service = CreditService(
        repository=CreditRepository(pool),
        settings=CreditSettings(),
    )
    app.state.billing_repository = BillingRepository(pool)
    app.state.billing_service = BillingService(
        app.state.billing_repository,
        billing_flags=app.state.billing_flags,
        credit_service=app.state.credit_service,
    )

    # Conversation service stub (for agent message count in usage endpoint)
    app.state.conversation_service = AsyncMock()
    app.state.conversation_service.get_daily_count = AsyncMock(return_value=0)

    # Trends / Evolution (real DB-backed)
    app.state.trend_repository = PostgresTrendRepository(pool)
    app.state.trend_service = TrendService(repository=app.state.trend_repository)
    app.state.evolution_repository = PostgresEvolutionRepository(pool)
    app.state.evolution_service = EvolutionService(repository=app.state.evolution_repository)

    # Stories (DB-backed repository; capture requires external fetcher/storage so keep minimal stubs)
    app.state.story_repository = PostgresStoryRepository(pool)

    class _NoopStoryStorage:
        async def generate_presigned_url(self, r2_key: str, expiration_seconds: int = 3600) -> str:
            return f"https://example.invalid/{r2_key}"

        async def download_and_upload_story(self, *args, **kwargs):  # pragma: no cover
            raise RuntimeError("external storage disabled in e2e tests")

    class _NoopInstagramFetcher:
        async def fetch_stories(self, username: str):  # pragma: no cover
            return []

    app.state.story_service = StoryService(
        repository=app.state.story_repository,
        storage=_NoopStoryStorage(),  # Only used when stories exist
        instagram_fetcher=_NoopInstagramFetcher(),
    )

    # Deepfake endpoints: keep router fully wired but avoid external analyzers.
    app.state.analysis_repository = PostgresAnalysisRepository(pool)
    app.state.deepfake_repository = PostgresDeepfakeRepository(pool)

    class _VideoStorageStub:
        def __init__(self) -> None:
            self.calls: list[tuple[str, str, int]] = []

        async def generate_download_url(
            self,
            platform: Platform,
            video_id: str,
            expires_in_seconds: int = 3600,
        ) -> str:
            self.calls.append((platform.value, video_id, expires_in_seconds))
            return f"https://example.invalid/videos/{platform.value}/{video_id}.mp4"

    class _LipincStub:
        last_cost_usd: float | None = None

        async def analyze(self, video_url: str) -> LipSyncResult:
            return LipSyncResult(
                score=0.95,
                anomaly_detected=False,
                confidence=Confidence.HIGH,
                error=None,
                processing_time_ms=5,
            )

        async def close(self) -> None:  # pragma: no cover
            return None

    class _RealityDefenderStub:
        async def analyze(self, video_url: str) -> RealityDefenderResult:
            return RealityDefenderResult(
                score=0.10,
                verdict=Verdict.AUTHENTIC,
                indicators=[],
                error=None,
                processing_time_ms=7,
                cost_cents=0,
            )

        async def close(self) -> None:  # pragma: no cover
            return None

    app.state.video_storage = _VideoStorageStub()
    app.state.deepfake_service = DeepfakeService(
        repository=app.state.deepfake_repository,
        lipinc=_LipincStub(),
        reality_defender=_RealityDefenderStub(),
    )

    # Internal endpoint worker stub (auth is the primary surface here)
    class _JobWorkerStub:
        def __init__(self):
            self.called_with: list[UUID] = []

        async def process_job(self, job_id: UUID) -> None:
            self.called_with.append(job_id)

    app.state.job_worker = _JobWorkerStub()
    app.state.billing_flags = BillingFlags()

    try:
        yield app
    finally:
        limiter.enabled = True


@pytest_asyncio.fixture
async def e2e_db_client(e2e_db_app):
    transport = httpx.ASGITransport(app=e2e_db_app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def e2e_internal_client():
    """ASGI app for internal endpoint auth tests (no DB required)."""
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(internal.router)
    limiter.enabled = False

    class _JobWorkerStub:
        def __init__(self):
            self.called_with: list[UUID] = []

        async def process_job(self, job_id: UUID) -> None:
            self.called_with.append(job_id)

    app.state.job_worker = _JobWorkerStub()
    app.state.environment = "production"  # enforce OIDC checks in test

    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, app


@pytest_asyncio.fixture
async def e2e_webhooks_client():
    """ASGI app for Stripe webhook error-path tests (no DB required)."""
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(webhooks.router)
    limiter.enabled = False
    app.state.billing_repository = SimpleNamespace()

    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, app


# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------


@pytest.mark.db
class TestProAndOperationalEndpointsE2E:
    @pytest.mark.asyncio
    async def test_free_tier_pro_endpoints_are_gated(self, e2e_db_client, db_conn) -> None:
        user_id, supa_id = await _insert_user(db_conn, email="free-e2e@example.com")
        headers = _bearer_headers(_make_jwt(supa_id, email="free-e2e@example.com"))

        # Deepfake
        resp = await e2e_db_client.post(
            "/v1/deepfake/analyze",
            json={"video_id": str(uuid4())},
            headers=headers,
        )
        assert resp.status_code == 403
        _assert_tier_required_error(resp.json()["error"], feature="deepfake_detection")

        resp = await e2e_db_client.get(f"/v1/deepfake/{uuid4()}", headers=headers)
        assert resp.status_code == 403
        _assert_tier_required_error(resp.json()["error"], feature="deepfake_detection")

        # Trends
        resp = await e2e_db_client.get("/v1/trends?platform=tiktok", headers=headers)
        assert resp.status_code == 403
        _assert_tier_required_error(resp.json()["error"], feature="trend_intelligence")

        # Evolution
        resp = await e2e_db_client.get(
            "/v1/creators/tiktok/testuser/evolution?period=90d",
            headers=headers,
        )
        assert resp.status_code == 403
        _assert_tier_required_error(resp.json()["error"], feature="evolution_tracking")

        # Stories
        resp = await e2e_db_client.post(
            "/v1/stories/instagram/testuser/capture",
            headers=headers,
        )
        assert resp.status_code == 403
        _assert_tier_required_error(resp.json()["error"], feature="stories_capture")

        resp = await e2e_db_client.get(
            "/v1/stories/instagram/testuser",
            headers=headers,
        )
        assert resp.status_code == 403
        _assert_tier_required_error(resp.json()["error"], feature="stories_access")

    @pytest.mark.asyncio
    async def test_usage_is_db_backed(self, e2e_db_client, db_conn) -> None:
        user_id, supa_id = await _insert_user(db_conn, email="usage-e2e@example.com")

        resp = await e2e_db_client.get("/v1/usage", headers=_bearer_headers(_make_jwt(supa_id)))
        assert resp.status_code == 200
        body = resp.json()
        assert body["tier"] == "free"
        assert body["videos_limit"] == 100
        assert body["rate_limit_per_minute"] == 30

    @pytest.mark.asyncio
    async def test_pro_trends_success(self, e2e_db_client, db_conn) -> None:
        user_id, supa_id = await _insert_user(db_conn, email="pro-trends-e2e@example.com", stripe_customer_id="cus_test")
        await _insert_subscription(db_conn, user_id, tier="pro", status="active")

        await _insert_trend_snapshot(
            db_conn,
            platform=Platform.TIKTOK,
            hashtags=[{"hashtag": "#fitness", "volume": 150, "growth_rate": 0.5, "unique_creators": 45}],
            brands={"Nike": 100, "Adidas": 50},
            sample_size=150,
        )

        resp = await e2e_db_client.get(
            "/v1/trends?platform=tiktok",
            headers=_bearer_headers(_make_jwt(supa_id)),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["snapshot"]["platform"] == "tiktok"
        assert body["share_of_voice"]["Nike"] == pytest.approx(66.67, rel=0.01)

    @pytest.mark.asyncio
    async def test_pro_evolution_success(self, e2e_db_client, db_conn) -> None:
        user_id, supa_id = await _insert_user(db_conn, email="pro-evo-e2e@example.com", stripe_customer_id="cus_test")
        await _insert_subscription(db_conn, user_id, tier="pro", status="active")

        await _seed_creator_analyses(db_conn, platform=Platform.TIKTOK, username="fitnessjen", count=10)

        resp = await e2e_db_client.get(
            "/v1/creators/tiktok/fitnessjen/evolution?period=90d",
            headers=_bearer_headers(_make_jwt(supa_id)),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["creator_username"] == "fitnessjen"
        assert body["platform"] == "tiktok"
        assert body["period_days"] == 90
        assert body["videos_analyzed"] == 10

    @pytest.mark.asyncio
    async def test_pro_deepfake_analyze_and_get_is_db_backed(self, e2e_db_client, e2e_db_app, db_conn) -> None:
        user_id, supa_id = await _insert_user(db_conn, email="pro-deepfake-e2e@example.com", stripe_customer_id="cus_test")
        await _insert_subscription(db_conn, user_id, tier="pro", status="active")

        # Seed an analysis row that deepfake endpoints can reference.
        analysis_id = uuid4()
        platform_video_id = "1234567890"
        cache_key = f"{Platform.TIKTOK.value}:{platform_video_id}:v2"

        await db_conn.execute(
            """INSERT INTO video_analysis
               (id, video_id, cache_key, overall_safe, overall_confidence,
                risks_detected, summary, content_categories, moderation_flags,
                model_version)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""",
            analysis_id,
            uuid4(),
            cache_key,
            True,
            0.9,
            "[]",
            "seeded",
            "[]",
            "[]",
            "2",
        )
        await _grant_analysis_access(db_conn, analysis_id, user_id)

        headers = _bearer_headers(_make_jwt(supa_id))

        resp = await e2e_db_client.post(
            "/v1/deepfake/analyze",
            json={"video_id": str(analysis_id)},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["video_id"] == str(analysis_id)
        assert body["cached"] is False
        assert body["is_deepfake"] is False
        assert body["risk_level"] == "none"
        assert body["detection_method"] == "ensemble"

        # Ensure the router derived (platform, video_id) from cache_key to build a download URL.
        assert e2e_db_app.state.video_storage.calls[-1][:2] == ("tiktok", platform_video_id)

        resp = await e2e_db_client.get(f"/v1/deepfake/{analysis_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["cached"] is True

        # Second analyze should hit cache unless force_refresh is set.
        resp = await e2e_db_client.post(
            "/v1/deepfake/analyze",
            json={"video_id": str(analysis_id), "force_refresh": False},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["cached"] is True

    @pytest.mark.asyncio
    async def test_deepfake_daily_spend_limit_is_enforced(self, e2e_db_client, e2e_db_app, db_conn) -> None:
        user_id, supa_id = await _insert_user(db_conn, email="pro-dailylimit-e2e@example.com", stripe_customer_id="cus_test")
        await _insert_subscription(db_conn, user_id, tier="pro", status="active")

        limit = int(e2e_db_app.state.deepfake_service.config.daily_spend_limit_cents)

        # Seed one deepfake_analysis row for "today" so daily cost meets the limit.
        analysis_id = uuid4()
        target_analysis_id = uuid4()
        await db_conn.execute(
            """INSERT INTO video_analysis
               (id, video_id, cache_key, overall_safe, overall_confidence,
                risks_detected, summary, content_categories, moderation_flags,
                model_version)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""",
            analysis_id,
            uuid4(),
            "tiktok:daily-limit:v2",
            True,
            0.9,
            "[]",
            "seeded",
            "[]",
            "[]",
            "2",
        )
        await db_conn.execute(
            """INSERT INTO video_analysis
               (id, video_id, cache_key, overall_safe, overall_confidence,
                risks_detected, summary, content_categories, moderation_flags,
                model_version)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""",
            target_analysis_id,
            uuid4(),
            "tiktok:daily-limit-target:v2",
            True,
            0.9,
            "[]",
            "seeded",
            "[]",
            "[]",
            "2",
        )
        await _grant_analysis_access(db_conn, analysis_id, user_id)
        await _grant_analysis_access(db_conn, target_analysis_id, user_id)

        await db_conn.execute(
            """INSERT INTO deepfake_analysis
               (id, video_analysis_id, user_id, combined_score, is_deepfake, risk_level, detection_method, cost_cents)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
            uuid4(),
            analysis_id,
            user_id,
            0.1,
            False,
            "none",
            "ensemble",
            limit,
        )

        resp = await e2e_db_client.post(
            "/v1/deepfake/analyze",
            json={"video_id": str(target_analysis_id)},
            headers=_bearer_headers(_make_jwt(supa_id)),
        )
        assert resp.status_code == 429
        err = resp.json()["error"]
        assert err["code"] == "daily_limit_reached"
        assert err["current_cost_cents"] >= limit
        assert err["limit_cents"] == limit

    @pytest.mark.asyncio
    async def test_deepfake_analysis_id_isolation_between_users(self, e2e_db_client, db_conn) -> None:
        owner_id, owner_supa = await _insert_user(db_conn, email="deepfake-owner-e2e@example.com", stripe_customer_id="cus_owner")
        await _insert_subscription(db_conn, owner_id, tier="pro", status="active")

        other_id, other_supa = await _insert_user(db_conn, email="deepfake-other-e2e@example.com", stripe_customer_id="cus_other")
        await _insert_subscription(db_conn, other_id, tier="pro", status="active")

        analysis_id = uuid4()
        await db_conn.execute(
            """INSERT INTO video_analysis
               (id, video_id, cache_key, overall_safe, overall_confidence,
                risks_detected, summary, content_categories, moderation_flags,
                model_version)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""",
            analysis_id,
            uuid4(),
            "tiktok:isolation-e2e:v2",
            True,
            0.9,
            "[]",
            "seeded",
            "[]",
            "[]",
            "2",
        )
        await _grant_analysis_access(db_conn, analysis_id, owner_id)

        owner_resp = await e2e_db_client.post(
            "/v1/deepfake/analyze",
            json={"video_id": str(analysis_id)},
            headers=_bearer_headers(_make_jwt(owner_supa)),
        )
        assert owner_resp.status_code == 200

        other_resp = await e2e_db_client.post(
            "/v1/deepfake/analyze",
            json={"video_id": str(analysis_id)},
            headers=_bearer_headers(_make_jwt(other_supa)),
        )
        assert other_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_deepfake_cache_is_user_scoped(self, e2e_db_client, db_conn) -> None:
        user_a, supa_a = await _insert_user(db_conn, email="pro-deepfake-a-e2e@example.com", stripe_customer_id="cus_a")
        await _insert_subscription(db_conn, user_a, tier="pro", status="active")

        user_b, supa_b = await _insert_user(db_conn, email="pro-deepfake-b-e2e@example.com", stripe_customer_id="cus_b")
        await _insert_subscription(db_conn, user_b, tier="pro", status="active")

        analysis_id = uuid4()
        await db_conn.execute(
            """INSERT INTO video_analysis
               (id, video_id, cache_key, overall_safe, overall_confidence,
                risks_detected, summary, content_categories, moderation_flags,
                model_version)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""",
            analysis_id,
            uuid4(),
            "tiktok:user-scope:v2",
            True,
            0.9,
            "[]",
            "seeded",
            "[]",
            "[]",
            "2",
        )
        await _grant_analysis_access(db_conn, analysis_id, user_a)
        await _grant_analysis_access(db_conn, analysis_id, user_b)

        # First user computes and caches.
        first = await e2e_db_client.post(
            "/v1/deepfake/analyze",
            json={"video_id": str(analysis_id)},
            headers=_bearer_headers(_make_jwt(supa_a)),
        )
        assert first.status_code == 200
        assert first.json()["cached"] is False

        # Second user should NOT reuse first user's cache.
        second = await e2e_db_client.post(
            "/v1/deepfake/analyze",
            json={"video_id": str(analysis_id)},
            headers=_bearer_headers(_make_jwt(supa_b)),
        )
        assert second.status_code == 200
        assert second.json()["cached"] is False

        per_user_rows = await db_conn.fetchval(
            "SELECT COUNT(*) FROM deepfake_analysis WHERE video_analysis_id = $1",
            analysis_id,
        )
        assert int(per_user_rows) == 2

    @pytest.mark.asyncio
    async def test_pro_stories_capture_persists_and_lists(self, e2e_db_client, e2e_db_app, db_conn) -> None:
        user_id, supa_id = await _insert_user(db_conn, email="pro-stories-capture-e2e@example.com", stripe_customer_id="cus_test")
        await _insert_subscription(db_conn, user_id, tier="pro", status="active")

        # Override story service to avoid external fetcher/storage, but still exercise router+service+DB.
        class _StubStoryStorage:
            async def download_and_upload_story(
                self,
                *,
                media_url: str,
                platform: Platform,
                username: str,
                story_id: str,
                media_type: str = "video",
            ) -> StoryStorageResult:
                return StoryStorageResult(
                    r2_key=f"stories/{platform.value}/{username}/{story_id}.mp4",
                    platform=platform,
                    story_id=story_id,
                    creator_username=username,
                    media_type=media_type,
                    file_size_bytes=123,
                    captured_at=datetime.now(timezone.utc),
                )

            async def generate_presigned_url(self, r2_key: str, expiration_seconds: int = 3600) -> str:
                return f"https://example.invalid/{r2_key}"

        class _StubInstagramFetcher:
            async def fetch_stories(self, username: str) -> list[StoryResult]:
                return [
                    StoryResult(
                        story_id="story_1",
                        media_url="https://example.invalid/source.mp4",
                        media_type="video",
                        creator_username=username,
                    )
                ]

        e2e_db_app.state.story_service = StoryService(
            repository=e2e_db_app.state.story_repository,
            storage=_StubStoryStorage(),
            instagram_fetcher=_StubInstagramFetcher(),
        )

        headers = _bearer_headers(_make_jwt(supa_id))
        resp = await e2e_db_client.post("/v1/stories/instagram/testuser/capture", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["skipped"] == 0
        assert len(body["captured"]) == 1
        assert body["captured"][0]["story_id"] == "story_1"
        assert body["captured"][0]["media_url"].startswith("https://example.invalid/stories/instagram/testuser/story_1")

        # Second call should skip (idempotent capture).
        resp = await e2e_db_client.post("/v1/stories/instagram/testuser/capture", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["captured"] == []
        assert resp.json()["skipped"] == 1

        # GET should return the persisted captured story for this user.
        resp = await e2e_db_client.get("/v1/stories/instagram/testuser", headers=headers)
        assert resp.status_code == 200
        stories = resp.json()
        assert len(stories) == 1
        assert stories[0]["story_id"] == "story_1"

    @pytest.mark.asyncio
    async def test_pro_stories_get_empty_and_capture_unsupported_platform(self, e2e_db_client, db_conn) -> None:
        user_id, supa_id = await _insert_user(db_conn, email="pro-stories-e2e@example.com", stripe_customer_id="cus_test")
        await _insert_subscription(db_conn, user_id, tier="pro", status="active")

        headers = _bearer_headers(_make_jwt(supa_id))

        resp = await e2e_db_client.get("/v1/stories/instagram/testuser", headers=headers)
        assert resp.status_code == 200
        assert resp.json() == []

        resp = await e2e_db_client.post("/v1/stories/tiktok/testuser/capture", headers=headers)
        assert resp.status_code == 501
        assert resp.json()["error"]["code"] == "platform_not_supported"


class TestInternalProcessJobE2E:
    @pytest.mark.asyncio
    async def test_missing_oidc(self, e2e_internal_client) -> None:
        client, _app = e2e_internal_client
        resp = await client.post("/internal/process-job", json={"job_id": str(uuid4())})
        assert resp.status_code == 401
        assert resp.json()["error"]["message"] == "Missing OIDC token"

    @pytest.mark.asyncio
    async def test_malformed_bearer(self, e2e_internal_client) -> None:
        client, _app = e2e_internal_client
        resp = await client.post(
            "/internal/process-job",
            json={"job_id": str(uuid4())},
            headers={"Authorization": "Token bad"},
        )
        assert resp.status_code == 401
        assert resp.json()["error"]["message"] == "Invalid authorization format"

    @pytest.mark.asyncio
    async def test_invalid_token(self, e2e_internal_client, monkeypatch) -> None:
        client, _app = e2e_internal_client
        monkeypatch.setattr("google.oauth2.id_token.verify_oauth2_token", lambda *_a, **_kw: (_ for _ in ()).throw(ValueError("bad")))

        resp = await client.post(
            "/internal/process-job",
            json={"job_id": str(uuid4())},
            headers={"Authorization": "Bearer invalid"},
        )
        assert resp.status_code == 401
        assert resp.json()["error"]["message"] == "Invalid OIDC token"

    @pytest.mark.asyncio
    async def test_development_bypass(self, e2e_internal_client, monkeypatch) -> None:
        client, app = e2e_internal_client
        app.state.environment = "development"  # override production default for bypass test
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setattr(internal, "_is_development", True)
        monkeypatch.setattr(internal, "ALLOWED_SERVICE_ACCOUNTS", [])

        job_id = uuid4()
        resp = await client.post("/internal/process-job", json={"job_id": str(job_id)})
        assert resp.status_code == 200
        assert resp.json()["status"] == "processed"
        assert job_id in app.state.job_worker.called_with

    @pytest.mark.asyncio
    async def test_unauthorized_service_account(self, e2e_internal_client, monkeypatch) -> None:
        client, app = e2e_internal_client
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setattr(internal, "ALLOWED_SERVICE_ACCOUNTS", ["allowed@service.test"])
        monkeypatch.setattr(
            "google.oauth2.id_token.verify_oauth2_token",
            lambda *_a, **_kw: {"email": "not-allowed@service.test"},
        )

        job_id = uuid4()
        resp = await client.post(
            "/internal/process-job",
            json={"job_id": str(job_id)},
            headers={"Authorization": "Bearer valid-ish-token"},
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["message"] == "Unauthorized service account"
        assert job_id not in app.state.job_worker.called_with

    @pytest.mark.asyncio
    async def test_allowed_service_account(self, e2e_internal_client, monkeypatch) -> None:
        client, app = e2e_internal_client
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setattr(internal, "ALLOWED_SERVICE_ACCOUNTS", ["allowed@service.test"])
        monkeypatch.setattr(
            "google.oauth2.id_token.verify_oauth2_token",
            lambda *_a, **_kw: {"email": "allowed@service.test"},
        )

        job_id = uuid4()
        resp = await client.post(
            "/internal/process-job",
            json={"job_id": str(job_id)},
            headers={"Authorization": "Bearer valid-ish-token"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "processed"
        assert job_id in app.state.job_worker.called_with


class TestStripeWebhookE2E:
    @pytest.mark.asyncio
    async def test_stripe_not_configured(self, e2e_webhooks_client) -> None:
        client, app = e2e_webhooks_client
        app.dependency_overrides[get_stripe_client] = lambda: None

        resp = await client.post(
            "/webhooks/stripe",
            content=b"{}",
            headers={"stripe-signature": "t=1,v1=fake"},
        )
        assert resp.status_code == 503
        assert resp.json()["error"]["code"] == "stripe_not_configured"

    @pytest.mark.asyncio
    async def test_missing_signature_header(self, e2e_webhooks_client) -> None:
        client, _app = e2e_webhooks_client
        resp = await client.post("/webhooks/stripe", content=b"{}")
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "validation_error"

    @pytest.mark.asyncio
    async def test_invalid_signature(self, e2e_webhooks_client) -> None:
        client, app = e2e_webhooks_client
        settings = StripeSettings(
            secret_key="sk_test",
            webhook_secret="whsec_test_secret",
            publishable_key="pk_test",
            price_pro="price_pro_test",
        )
        from stripe import StripeClient
        stripe_client = StripeClient(api_key="sk_test")
        app.dependency_overrides[get_stripe_client] = lambda: stripe_client
        app.state.stripe_settings = settings

        payload = json.dumps({"id": "evt_test", "type": "customer.created", "data": {"object": {}}}).encode("utf-8")
        # Compute signature with the WRONG secret (ensures SignatureVerificationError).
        sig = _stripe_signature_header(secret="whsec_wrong_secret", payload=payload)

        resp = await client.post(
            "/webhooks/stripe",
            content=payload,
            headers={"stripe-signature": sig},
        )
        assert resp.status_code == 400
        body = resp.json()
        assert body["error"]["code"] == "webhook_error"
        assert body["error"]["message"] == "Webhook error"

    @pytest.mark.db
    @pytest.mark.asyncio
    async def test_webhook_idempotency_with_real_db(self, db_conn) -> None:
        app = FastAPI()
        register_exception_handlers(app)
        app.include_router(webhooks.router)
        limiter.enabled = False

        pool = SingleConnectionPool(db_conn)
        app.state.billing_repository = BillingRepository(pool)

        settings = StripeSettings(
            secret_key="sk_test",
            webhook_secret="whsec_test_secret",
            publishable_key="pk_test",
            price_pro="price_pro_test",
        )
        from stripe import StripeClient
        stripe_client = StripeClient(api_key="sk_test")
        app.dependency_overrides[get_stripe_client] = lambda: stripe_client
        app.state.stripe_settings = settings

        # PR-043: webhook endpoint now accesses credit_service + credit_settings from app.state
        from unittest.mock import MagicMock
        app.state.credit_service = MagicMock()
        app.state.credit_settings = MagicMock()

        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            payload = json.dumps(
                {"id": "evt_idempotency_test", "type": "customer.created", "data": {"object": {}}}
            ).encode("utf-8")
            sig = _stripe_signature_header(secret=settings.webhook_secret.get_secret_value(), payload=payload)

            r1 = await client.post("/webhooks/stripe", content=payload, headers={"stripe-signature": sig})
            assert r1.status_code == 200
            assert r1.json()["status"] == "processed"

            r2 = await client.post("/webhooks/stripe", content=payload, headers={"stripe-signature": sig})
            assert r2.status_code == 200
            assert r2.json()["status"] == "already_processed"

    @pytest.mark.db
    @pytest.mark.asyncio
    async def test_webhook_retry_after_failed_processing(self, db_conn, monkeypatch) -> None:
        app = FastAPI()
        register_exception_handlers(app)
        app.include_router(webhooks.router)
        limiter.enabled = False

        pool = SingleConnectionPool(db_conn)
        app.state.billing_repository = BillingRepository(pool)

        settings = StripeSettings(
            secret_key="sk_test",
            webhook_secret="whsec_test_secret",
            publishable_key="pk_test",
            price_pro="price_pro_test",
        )
        from stripe import StripeClient
        stripe_client = StripeClient(api_key="sk_test")
        app.dependency_overrides[get_stripe_client] = lambda: stripe_client
        app.state.stripe_settings = settings

        # PR-043: webhook endpoint now accesses credit_service + credit_settings from app.state
        from unittest.mock import MagicMock
        app.state.credit_service = MagicMock()
        app.state.credit_settings = MagicMock()

        failing_once = AsyncMock(side_effect=[RuntimeError("transient"), None])
        monkeypatch.setattr(webhooks, "process_stripe_event", failing_once)

        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            payload = json.dumps(
                {"id": "evt_retry_after_failure", "type": "customer.created", "data": {"object": {}}}
            ).encode("utf-8")
            sig = _stripe_signature_header(secret=settings.webhook_secret.get_secret_value(), payload=payload)

            r1 = await client.post("/webhooks/stripe", content=payload, headers={"stripe-signature": sig})
            assert r1.status_code == 500
            assert r1.json()["error"]["code"] == "internal_error"

            r2 = await client.post("/webhooks/stripe", content=payload, headers={"stripe-signature": sig})
            assert r2.status_code == 200
            assert r2.json()["status"] == "processed"
