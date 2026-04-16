"""Real-service E2E tests exercising all major product workflows through HTTP.

These tests start the real FastAPI app lifespan (DB, Gemini, R2, fetchers,
fraud, search, billing, brands, demographics) and hit endpoints over HTTP.

Zero mocks. Real Gemini API, real fetchers, real DB.

Run:
    RUN_GEMINI=1 RUN_LIVE_EXTERNAL=1 RUN_LIVE_API=1 \
        pytest tests/test_e2e/test_real_services_e2e.py -v -s
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid4

import httpx
import jwt as pyjwt
import pytest
import pytest_asyncio
from pydantic import SecretStr

from src.api.main import create_app
from src.api.rate_limit import limiter
from src.common.enums import Platform
from tests.fixtures.stable_ids import (
    TIKTOK_CREATOR,
    YOUTUBE_CREATOR,
    YOUTUBE_VIDEO_ID,
)

pytestmark = pytest.mark.live_api

_TEST_JWT_SECRET = "live-e2e-test-jwt-secret"
_TEST_SUPABASE_URL = "http://test.supabase.co"

# Skip entire module when real credentials aren't available
_SKIP_REASON = (
    "Real-service E2E tests require RUN_GEMINI=1, RUN_LIVE_EXTERNAL=1, RUN_LIVE_API=1 "
    "and valid credentials in .env"
)
if not (
    os.getenv("RUN_GEMINI") == "1"
    and os.getenv("RUN_LIVE_EXTERNAL") == "1"
    and os.getenv("RUN_LIVE_API") == "1"
):
    pytest.skip(_SKIP_REASON, allow_module_level=True)

# Ensure we're NOT using fake externals
if os.getenv("EXTERNALS_MODE", "real").strip().lower() == "fake":
    pytest.skip(
        "EXTERNALS_MODE=fake is set — these tests require real services",
        allow_module_level=True,
    )

YOUTUBE_VIDEO_URL = f"https://www.youtube.com/watch?v={YOUTUBE_VIDEO_ID}"


# ─── Helpers ────────────────────────────────────────────────────────────────


def _month_window(now: datetime) -> tuple[datetime, datetime]:
    period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    next_month = (period_start.replace(day=28) + timedelta(days=4)).replace(day=1)
    return period_start, next_month


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _make_jwt(supabase_user_id: str, email: str = "test@example.com") -> str:
    """Sign a test JWT matching Supabase token format."""
    payload = {
        "sub": supabase_user_id,
        "email": email,
        "iss": f"{_TEST_SUPABASE_URL}/auth/v1",
        "aud": "authenticated",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    return pyjwt.encode(payload, _TEST_JWT_SECRET, algorithm="HS256")


# ─── Fixtures ───────────────────────────────────────────────────────────────


@pytest_asyncio.fixture(scope="module")
async def live_app():
    """Full app with real lifespan — all services initialized."""
    app = create_app()
    limiter.enabled = False
    async with app.router.lifespan_context(app):
        # Always use test JWT secret so test-signed tokens work
        app.state.supabase_settings = SimpleNamespace(
            supabase_url=_TEST_SUPABASE_URL,
            supabase_anon_key="test-anon-key",
            supabase_jwt_secret=SecretStr(_TEST_JWT_SECRET),
        )
        yield app
    limiter.enabled = True


@pytest_asyncio.fixture
async def live_client(live_app):
    transport = httpx.ASGITransport(app=live_app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def _seed_user(
    live_app, *, tier: str = "pro", prefix: str = "e2e"
) -> tuple[str, UUID]:
    """Seed a user (+ subscription if pro) and return (jwt_token, user_id)."""
    user_id = uuid4()
    supabase_user_id = f"supa_{user_id.hex[:16]}"
    email = f"{prefix}-{tier}-{user_id.hex[:8]}@example.com"

    now = datetime.now(timezone.utc)
    period_start, period_end = _month_window(now)

    async with live_app.state.db_pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO users (id, email, stripe_customer_id, supabase_user_id) "
            "VALUES ($1, $2, $3, $4)",
            user_id, email, None, supabase_user_id,
        )
        if tier == "pro":
            sub_id = uuid4()
            await conn.execute(
                """INSERT INTO subscriptions
                   (id, user_id, stripe_subscription_id, stripe_price_id, tier, status,
                    current_period_start, current_period_end, cancel_at_period_end)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
                sub_id, user_id,
                f"sub_{uuid4().hex[:12]}", "price_test",
                "pro", "active",
                period_start, period_end, False,
            )

    token = _make_jwt(supabase_user_id, email)
    return token, user_id


async def _cleanup_user(live_app, user_id: UUID) -> None:
    """Remove all rows tied to a test user."""
    async with live_app.state.db_pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM video_analysis_access WHERE user_id = $1", user_id
        )
        await conn.execute(
            "DELETE FROM job_videos WHERE job_id IN "
            "(SELECT id FROM analysis_jobs WHERE user_id = $1)", user_id
        )
        await conn.execute(
            "DELETE FROM analysis_jobs WHERE user_id = $1", user_id
        )
        await conn.execute(
            "DELETE FROM subscriptions WHERE user_id = $1", user_id
        )
        await conn.execute(
            "DELETE FROM usage_periods WHERE user_id = $1", user_id
        )
        await conn.execute(
            "DELETE FROM api_keys WHERE user_id = $1", user_id
        )
        await conn.execute("DELETE FROM users WHERE id = $1", user_id)


@pytest_asyncio.fixture
async def pro_api_key(live_app):
    """Pro-tier JWT token backed by real DB rows."""
    token, user_id = await _seed_user(live_app, tier="pro")
    try:
        yield token
    finally:
        await _cleanup_user(live_app, user_id)


@pytest_asyncio.fixture
async def pro_user(live_app):
    """Pro-tier user returning (jwt_token, user_id) for tests that need both."""
    token, user_id = await _seed_user(live_app, tier="pro")
    try:
        yield token, user_id
    finally:
        await _cleanup_user(live_app, user_id)


@pytest_asyncio.fixture
async def free_api_key(live_app):
    """Free-tier JWT token (no subscription)."""
    token, user_id = await _seed_user(live_app, tier="free")
    try:
        yield token
    finally:
        await _cleanup_user(live_app, user_id)


# ─── 1. Video Analysis Full Flow ───────────────────────────────────────────


@pytest.mark.gemini
@pytest.mark.external_api
@pytest.mark.db
@pytest.mark.slow
class TestVideoAnalysisFullFlowE2E:
    """POST /v1/analyze/videos → GET /v1/analysis/{id}."""

    async def test_analyze_youtube_video_and_retrieve(
        self, live_client: httpx.AsyncClient, pro_api_key: str
    ) -> None:
        # Analyze
        resp = await live_client.post(
            "/v1/analyze/videos",
            headers=_bearer(pro_api_key),
            json={"urls": [YOUTUBE_VIDEO_URL]},
            timeout=90,
        )
        assert resp.status_code == 200, f"Analyze failed: {resp.text}"
        body = resp.json()

        assert body["success_rate"] > 0
        assert len(body["results"]) == 1

        result = body["results"][0]
        analysis_id = result["analysis_id"]

        # Structural assertions (non-deterministic AI output)
        assert UUID(analysis_id)
        assert isinstance(result["overall_safe"], bool)
        assert isinstance(result["summary"], str) and len(result["summary"]) > 0
        assert result["platform"] == "youtube"
        assert isinstance(result["content_categories"], list)
        assert isinstance(result["risks_detected"], list)
        assert isinstance(result["cost_usd"], (int, float))
        # Fresh analysis costs money; cached is free
        if not result["cached"]:
            assert result["cost_usd"] > 0
        else:
            assert result["cost_usd"] == 0

        # Retrieve
        resp2 = await live_client.get(
            f"/v1/analysis/{analysis_id}",
            headers=_bearer(pro_api_key),
        )
        assert resp2.status_code == 200, f"Retrieve failed: {resp2.text}"
        body2 = resp2.json()
        assert body2["id"] == analysis_id
        assert body2["status"] == "complete"
        assert body2["result"]["overall_safe"] == result["overall_safe"]
        # video_id in the analysis record is the video_uuid (UUID5), not the platform ID
        vid = body2["result"]["video_id"]
        UUID(vid)  # validates it's a proper UUID string

    async def test_analyze_cached_second_call(
        self, live_client: httpx.AsyncClient, pro_api_key: str
    ) -> None:
        # First call (may already be cached from prior test or prior run)
        resp1 = await live_client.post(
            "/v1/analyze/videos",
            headers=_bearer(pro_api_key),
            json={"urls": [YOUTUBE_VIDEO_URL]},
            timeout=90,
        )
        assert resp1.status_code == 200

        # Second call — should be cached
        resp2 = await live_client.post(
            "/v1/analyze/videos",
            headers=_bearer(pro_api_key),
            json={"urls": [YOUTUBE_VIDEO_URL]},
            timeout=15,
        )
        assert resp2.status_code == 200
        result = resp2.json()["results"][0]
        assert result["cached"] is True
        assert result["cost_usd"] == 0

    async def test_analyze_invalid_domain_rejected(
        self, live_client: httpx.AsyncClient, pro_api_key: str
    ) -> None:
        resp = await live_client.post(
            "/v1/analyze/videos",
            headers=_bearer(pro_api_key),
            json={"urls": ["https://evil.com/video"]},
        )
        assert resp.status_code == 200  # 200 with errors array
        body = resp.json()
        assert body["success_rate"] == 0
        assert len(body["errors"]) == 1
        assert "blocked" in body["errors"][0]["error"].lower() or "unsupported" in body["errors"][0]["error"].lower()


# ─── 2. Analysis → Brands → Demographics ───────────────────────────────────


@pytest.mark.gemini
@pytest.mark.external_api
@pytest.mark.db
@pytest.mark.slow
class TestAnalysisToBrandsDemographicsE2E:
    """Analyze → seed brands/demographics via service → GET /v1/brands/{id} → GET /v1/demographics/{id}.

    Brand and demographics analysis are agent-triggered (not auto-triggered by
    POST /v1/analyze/videos). So we call the services directly to seed real
    Gemini-generated data, then verify the HTTP GET endpoints serve it correctly.
    """

    async def test_analyze_then_get_brands(
        self, live_app, live_client: httpx.AsyncClient, pro_api_key: str
    ) -> None:
        # 1. Analyze video via HTTP
        resp = await live_client.post(
            "/v1/analyze/videos",
            headers=_bearer(pro_api_key),
            json={"urls": [YOUTUBE_VIDEO_URL]},
            timeout=90,
        )
        assert resp.status_code == 200
        analysis_id = resp.json()["results"][0]["analysis_id"]

        # 2. Seed brand analysis via service (real Gemini call)
        storage = live_app.state.video_storage
        brand_service = live_app.state.brand_service
        temp_path = await storage.download_to_temp(Platform.YOUTUBE, YOUTUBE_VIDEO_ID)
        try:
            result = await brand_service.analyze_brands(
                video_path=str(temp_path),
                video_analysis_id=UUID(analysis_id),
                video_id=YOUTUBE_VIDEO_ID,
            )
            assert result.analysis is not None
        finally:
            Path(temp_path).unlink(missing_ok=True)

        # 3. Verify HTTP GET returns the brand data
        resp2 = await live_client.get(
            f"/v1/brands/{analysis_id}",
            headers=_bearer(pro_api_key),
        )
        assert resp2.status_code == 200, f"Brands should be 200 after seeding: {resp2.text}"
        body = resp2.json()
        assert isinstance(body["brand_mentions"], list)
        assert "overall_sentiment" in body
        assert isinstance(body["has_sponsorship_signals"], bool)
        assert isinstance(body["overall_confidence"], (int, float))
        assert 0 <= body["overall_confidence"] <= 1

    async def test_analyze_then_get_demographics(
        self, live_app, live_client: httpx.AsyncClient, pro_api_key: str
    ) -> None:
        # 1. Analyze video via HTTP
        resp = await live_client.post(
            "/v1/analyze/videos",
            headers=_bearer(pro_api_key),
            json={"urls": [YOUTUBE_VIDEO_URL]},
            timeout=90,
        )
        assert resp.status_code == 200
        analysis_id = resp.json()["results"][0]["analysis_id"]

        # 2. Seed demographics via service (real Gemini call)
        storage = live_app.state.video_storage
        demographics_service = live_app.state.demographics_service
        temp_path = await storage.download_to_temp(Platform.YOUTUBE, YOUTUBE_VIDEO_ID)
        try:
            result = await demographics_service.infer_demographics(
                video_path=str(temp_path),
                video_analysis_id=UUID(analysis_id),
                video_id=YOUTUBE_VIDEO_ID,
            )
            assert result.demographics is not None
        finally:
            Path(temp_path).unlink(missing_ok=True)

        # 3. Verify HTTP GET returns the demographics data
        resp2 = await live_client.get(
            f"/v1/demographics/{analysis_id}",
            headers=_bearer(pro_api_key),
        )
        assert resp2.status_code == 200, f"Demographics should be 200 after seeding: {resp2.text}"
        body = resp2.json()
        # age_distribution, gender_distribution, interests are Pydantic models serialized as dicts
        assert isinstance(body["age_distribution"], dict)
        assert isinstance(body["gender_distribution"], dict)
        assert isinstance(body["interests"], dict)
        assert isinstance(body["interests"]["primary"], list) and len(body["interests"]["primary"]) > 0
        assert isinstance(body["overall_confidence"], (int, float))
        assert 0 <= body["overall_confidence"] <= 1

    async def test_brands_demographics_isolated_per_user(
        self, live_app, live_client: httpx.AsyncClient, pro_api_key: str
    ) -> None:
        """IDOR protection: other user can't read your brands/demographics/analysis."""
        # 1. Analyze as primary user
        resp = await live_client.post(
            "/v1/analyze/videos",
            headers=_bearer(pro_api_key),
            json={"urls": [YOUTUBE_VIDEO_URL]},
            timeout=90,
        )
        assert resp.status_code == 200
        analysis_id = resp.json()["results"][0]["analysis_id"]

        # 2. Seed brand data so there IS data to protect (not just empty 404)
        storage = live_app.state.video_storage
        brand_service = live_app.state.brand_service
        temp_path = await storage.download_to_temp(Platform.YOUTUBE, YOUTUBE_VIDEO_ID)
        try:
            await brand_service.analyze_brands(
                video_path=str(temp_path),
                video_analysis_id=UUID(analysis_id),
                video_id=YOUTUBE_VIDEO_ID,
            )
        finally:
            Path(temp_path).unlink(missing_ok=True)

        # 3. Verify primary user CAN access
        resp_check = await live_client.get(
            f"/v1/brands/{analysis_id}",
            headers=_bearer(pro_api_key),
        )
        assert resp_check.status_code == 200, "Primary user should see their brands"

        # 4. Other user should NOT see the first user's data
        other_key, other_user_id = await _seed_user(live_app, tier="pro", prefix="idor")
        try:
            resp_brands = await live_client.get(
                f"/v1/brands/{analysis_id}",
                headers=_bearer(other_key),
            )
            assert resp_brands.status_code == 404

            resp_demo = await live_client.get(
                f"/v1/demographics/{analysis_id}",
                headers=_bearer(other_key),
            )
            assert resp_demo.status_code == 404

            resp_analysis = await live_client.get(
                f"/v1/analysis/{analysis_id}",
                headers=_bearer(other_key),
            )
            assert resp_analysis.status_code == 404
        finally:
            await _cleanup_user(live_app, other_user_id)


# ─── 3. Creator Portfolio ──────────────────────────────────────────────────


@pytest.mark.gemini
@pytest.mark.external_api
@pytest.mark.db
@pytest.mark.slow
class TestCreatorPortfolioE2E:
    """POST /v1/analyze/creator."""

    async def test_analyze_youtube_creator_portfolio(
        self, live_client: httpx.AsyncClient, pro_api_key: str
    ) -> None:
        resp = await live_client.post(
            "/v1/analyze/creator",
            headers=_bearer(pro_api_key),
            json={"platform": "youtube", "username": YOUTUBE_CREATOR, "limit": 2},
            timeout=120,
        )
        assert resp.status_code == 200, f"Creator analysis failed: {resp.text}"
        body = resp.json()

        assert body["creator_username"] == YOUTUBE_CREATOR
        assert body["platform"] == "youtube"
        assert isinstance(body["videos_analyzed"], int) and body["videos_analyzed"] >= 1
        assert isinstance(body["results"], list) and len(body["results"]) >= 1
        assert isinstance(body["aggregate_risk_score"], (int, float))
        assert 0 <= body["success_rate"] <= 1

        # Each result should have analysis fields
        for r in body["results"]:
            assert "analysis_id" in r
            assert isinstance(r["overall_safe"], bool)
            assert isinstance(r["summary"], str)

    async def test_analyze_creator_nonexistent_user(
        self, live_client: httpx.AsyncClient, pro_api_key: str
    ) -> None:
        resp = await live_client.post(
            "/v1/analyze/creator",
            headers=_bearer(pro_api_key),
            json={"platform": "youtube", "username": "nonexistent_user_xyz_99999", "limit": 1},
            timeout=30,
        )
        # yt-dlp returns 404 or the endpoint returns 200 with 0 results
        assert resp.status_code in (200, 404), f"Unexpected: {resp.text}"
        if resp.status_code == 200:
            body = resp.json()
            assert body["videos_analyzed"] == 0
        elif resp.status_code == 404:
            body = resp.json()
            assert body["error"]["code"] == "creator_not_found"


# ─── 4. Async Job Lifecycle ────────────────────────────────────────────────


@pytest.mark.gemini
@pytest.mark.external_api
@pytest.mark.db
@pytest.mark.slow
class TestAsyncJobLifecycleE2E:
    """POST /v1/analyze/videos/async → /internal/process-job → poll → cancel."""

    async def test_submit_process_poll_complete(
        self, live_client: httpx.AsyncClient, pro_user: tuple[str, UUID], monkeypatch
    ) -> None:
        api_key, _ = pro_user

        # Submit async job
        resp = await live_client.post(
            "/v1/analyze/videos/async",
            headers=_bearer(api_key),
            json={"urls": [YOUTUBE_VIDEO_URL]},
        )
        assert resp.status_code == 202, f"Submit failed: {resp.text}"
        job_id = str(resp.json()["job_id"])

        # Poll — should be pending (MockTaskClient doesn't auto-process)
        resp2 = await live_client.get(
            f"/v1/analysis/jobs/{job_id}",
            headers=_bearer(api_key),
        )
        assert resp2.status_code == 200
        assert resp2.json()["status"] in ("pending", "queued", "running")

        # Manually trigger processing (OIDC bypass in development mode)
        monkeypatch.setenv("ENVIRONMENT", "development")
        resp3 = await live_client.post(
            "/internal/process-job",
            json={"job_id": job_id},
            timeout=90,
        )
        assert resp3.status_code == 200, f"Process failed: {resp3.text}"

        # Poll again — should be completed
        resp4 = await live_client.get(
            f"/v1/analysis/jobs/{job_id}",
            headers=_bearer(api_key),
        )
        assert resp4.status_code == 200
        body4 = resp4.json()
        assert body4["status"] == "complete"
        assert body4["completed_videos"] >= 1

        # Results should contain analysis data
        if body4.get("results"):
            for r in body4["results"]:
                assert "result" in r or "video_id" in r

    async def test_list_jobs_shows_user_jobs(
        self, live_client: httpx.AsyncClient, pro_api_key: str
    ) -> None:
        # Submit 2 jobs
        for _ in range(2):
            resp = await live_client.post(
                "/v1/analyze/videos/async",
                headers=_bearer(pro_api_key),
                json={"urls": [YOUTUBE_VIDEO_URL]},
            )
            assert resp.status_code == 202

        # List
        resp2 = await live_client.get(
            "/v1/analysis/jobs",
            headers=_bearer(pro_api_key),
        )
        assert resp2.status_code == 200
        body = resp2.json()
        assert isinstance(body["jobs"], list)
        assert len(body["jobs"]) >= 2
        assert "pagination" in body

    async def test_cancel_pending_job(
        self, live_client: httpx.AsyncClient, pro_api_key: str
    ) -> None:
        # Submit
        resp = await live_client.post(
            "/v1/analyze/videos/async",
            headers=_bearer(pro_api_key),
            json={"urls": [YOUTUBE_VIDEO_URL]},
        )
        assert resp.status_code == 202
        job_id = str(resp.json()["job_id"])

        # Cancel
        resp2 = await live_client.delete(
            f"/v1/analysis/jobs/{job_id}",
            headers=_bearer(pro_api_key),
        )
        assert resp2.status_code == 200
        body = resp2.json()
        assert body["job_id"] == job_id
        assert body["cancellation_requested"] is True

        # Poll — status stays "pending" but cancellation_requested is set
        resp3 = await live_client.get(
            f"/v1/analysis/jobs/{job_id}",
            headers=_bearer(pro_api_key),
        )
        assert resp3.status_code == 200
        # Job status doesn't change to "cancelled" — it remains pending/running
        # but the cancellation flag is what matters (verified via DELETE response above)
        assert resp3.json()["status"] in ("pending", "running")


# ─── 5. Fraud Detection ────────────────────────────────────────────────────


@pytest.mark.external_api
@pytest.mark.db
@pytest.mark.slow
class TestFraudDetectionRealE2E:
    """POST /v1/fraud/analyze → GET /v1/fraud/{id}."""

    async def test_fraud_analyze_tiktok_real_api(
        self, live_client: httpx.AsyncClient, pro_api_key: str
    ) -> None:
        resp = await live_client.post(
            "/v1/fraud/analyze",
            headers=_bearer(pro_api_key),
            json={"platform": "tiktok", "username": TIKTOK_CREATOR},
            timeout=60,
        )
        # External API flakiness: tolerate 429/500/502/503
        if resp.status_code in (429, 500, 502, 503):
            pytest.skip(f"External API unavailable (HTTP {resp.status_code})")

        assert resp.status_code == 200, f"Fraud analysis failed: {resp.text}"
        body = resp.json()

        # Structural checks
        analysis_id = body["analysis_id"]
        assert UUID(analysis_id)
        assert body["creator_username"] == TIKTOK_CREATOR
        assert body["platform"] == "tiktok"
        assert body["risk_level"] in ("low", "medium", "high", "critical")
        assert 0 <= body["risk_score"] <= 100

        fraud = body["fraud_analysis"]
        assert 0 <= fraud["aqs_score"] <= 100
        assert fraud["aqs_grade"] in ("excellent", "very_good", "good", "poor", "critical", "unknown")

        # Retrieve cached result
        resp2 = await live_client.get(
            f"/v1/fraud/{analysis_id}",
            headers=_bearer(pro_api_key),
        )
        assert resp2.status_code == 200
        body2 = resp2.json()
        assert body2["analysis_id"] == analysis_id
        assert body2["status"] == "completed"

    async def test_fraud_analyze_youtube_unsupported(
        self, live_client: httpx.AsyncClient, pro_api_key: str
    ) -> None:
        resp = await live_client.post(
            "/v1/fraud/analyze",
            headers=_bearer(pro_api_key),
            json={"platform": "youtube", "username": YOUTUBE_CREATOR},
        )
        assert resp.status_code == 422  # Pydantic validation rejects youtube


# ─── 6. Full User Journey ──────────────────────────────────────────────────


@pytest.mark.gemini
@pytest.mark.external_api
@pytest.mark.db
@pytest.mark.slow
class TestFullUserJourneyE2E:
    """Complete user workflow across multiple endpoints."""

    async def test_complete_analysis_workflow(
        self, live_app, live_client: httpx.AsyncClient, pro_api_key: str
    ) -> None:
        # 1. Analyze video
        resp = await live_client.post(
            "/v1/analyze/videos",
            headers=_bearer(pro_api_key),
            json={"urls": [YOUTUBE_VIDEO_URL]},
            timeout=90,
        )
        assert resp.status_code == 200
        results = resp.json()["results"]
        assert len(results) >= 1
        analysis_id = results[0]["analysis_id"]

        # 2. Seed + verify brands (brands require service-level trigger)
        storage = live_app.state.video_storage
        brand_service = live_app.state.brand_service
        demographics_service = live_app.state.demographics_service
        temp_path = await storage.download_to_temp(Platform.YOUTUBE, YOUTUBE_VIDEO_ID)
        try:
            await brand_service.analyze_brands(
                video_path=str(temp_path),
                video_analysis_id=UUID(analysis_id),
                video_id=YOUTUBE_VIDEO_ID,
            )
            await demographics_service.infer_demographics(
                video_path=str(temp_path),
                video_analysis_id=UUID(analysis_id),
                video_id=YOUTUBE_VIDEO_ID,
            )
        finally:
            Path(temp_path).unlink(missing_ok=True)

        resp2 = await live_client.get(
            f"/v1/brands/{analysis_id}",
            headers=_bearer(pro_api_key),
        )
        assert resp2.status_code == 200, f"Brands should be 200 after seeding: {resp2.text}"

        # 3. Verify demographics
        resp3 = await live_client.get(
            f"/v1/demographics/{analysis_id}",
            headers=_bearer(pro_api_key),
        )
        assert resp3.status_code == 200, f"Demographics should be 200 after seeding: {resp3.text}"

        # 4. Fraud (TikTok — separate from video analysis)
        resp4 = await live_client.post(
            "/v1/fraud/analyze",
            headers=_bearer(pro_api_key),
            json={"platform": "tiktok", "username": TIKTOK_CREATOR},
            timeout=60,
        )
        # Tolerate external API failures
        assert resp4.status_code in (200, 429, 500, 502, 503)

        # 5. Usage — verify the pro user sees their tier and usage
        resp5 = await live_client.get(
            "/v1/usage",
            headers=_bearer(pro_api_key),
        )
        assert resp5.status_code == 200
        usage = resp5.json()
        assert usage["tier"] == "pro"
        assert isinstance(usage["videos_used"], int)
        assert isinstance(usage["videos_limit"], int)
        assert isinstance(usage["videos_remaining"], int)
        assert 0 <= usage["usage_percent"] <= 100
        assert usage["subscription_status"] == "active"


# ─── 7. Search ────────────────────────────────────────────────────────────


@pytest.mark.gemini
@pytest.mark.external_api
@pytest.mark.db
@pytest.mark.slow
class TestSearchRealE2E:
    """POST /v1/search with real Gemini query parsing + real platform fetchers."""

    async def test_search_tiktok_returns_results(
        self, live_client: httpx.AsyncClient, pro_api_key: str
    ) -> None:
        resp = await live_client.post(
            "/v1/search",
            headers=_bearer(pro_api_key),
            json={"query": "fitness videos", "platforms": ["tiktok"], "limit": 3},
            timeout=30,
        )
        # External API flakiness: tolerate 429/500/502/503
        if resp.status_code in (429, 500, 502, 503):
            pytest.skip(f"External API unavailable (HTTP {resp.status_code})")

        assert resp.status_code == 200, f"Search failed: {resp.text}"
        body = resp.json()

        assert isinstance(body["results"], list) and len(body["results"]) >= 1
        assert body["total"] >= 1
        assert "tiktok" in body["platforms_searched"]
        assert isinstance(body["interpretation"], dict)
        assert body["confidence"] in ("high", "medium", "low")

        # Verify result item structure
        item = body["results"][0]
        assert item["platform"] == "tiktok"
        assert isinstance(item["creator_handle"], str)  # may be empty for keyword results

    async def test_search_cross_platform_tolerates_partial_failure(
        self, live_client: httpx.AsyncClient, pro_api_key: str
    ) -> None:
        resp = await live_client.post(
            "/v1/search",
            headers=_bearer(pro_api_key),
            json={"query": "cooking tutorial", "limit": 5},
            timeout=30,
        )
        if resp.status_code in (429, 500, 502, 503):
            pytest.skip(f"External API unavailable (HTTP {resp.status_code})")

        assert resp.status_code == 200, f"Search failed: {resp.text}"
        body = resp.json()

        assert isinstance(body["results"], list)
        assert isinstance(body["platforms_searched"], list) and len(body["platforms_searched"]) >= 1
        assert isinstance(body["platforms_failed"], list)
        assert isinstance(body["errors"], list)
        # At least one platform should succeed (TikTok or YouTube)
        assert len(body["platforms_searched"]) > len(body["platforms_failed"])


# ─── 8. Agent Multi-Tool Chaining ─────────────────────────────────────────


@pytest.mark.gemini
@pytest.mark.external_api
@pytest.mark.db
@pytest.mark.slow
class TestAgentMultiToolE2E:
    """POST /v1/agent/chat — agent chains search → analyze in a single conversation.

    NOTE: The agent's analyze_video tool calls AnalysisService.analyze() directly,
    which expects the video already in R2. Unlike the HTTP endpoint, it doesn't
    fetch first. So we pre-warm R2 by analyzing the known video via HTTP, then
    direct the agent to analyze that specific video ID.
    """

    async def test_agent_chains_search_and_analyze(
        self, live_client: httpx.AsyncClient, pro_api_key: str
    ) -> None:
        # Pre-warm: ensure YOUTUBE_VIDEO_ID is in R2 (may be cached from earlier tests)
        resp0 = await live_client.post(
            "/v1/analyze/videos",
            headers=_bearer(pro_api_key),
            json={"urls": [YOUTUBE_VIDEO_URL]},
            timeout=90,
        )
        assert resp0.status_code == 200, f"Pre-warm failed: {resp0.text}"

        # Prompt the agent to search AND analyze the known video
        resp = await live_client.post(
            "/v1/agent/chat",
            headers=_bearer(pro_api_key),
            json={
                "message": (
                    "First, search YouTube for a short video about animals. "
                    f"Then analyze the YouTube video with ID {YOUTUBE_VIDEO_ID} "
                    "for brand safety. Tell me the analysis_id."
                ),
            },
            timeout=120,
        )
        assert resp.status_code == 200, f"Agent chat failed: {resp.text}"
        body = resp.json()

        # Response structure
        assert isinstance(body["text"], str) and len(body["text"]) > 0
        assert body["gemini_calls"] >= 2
        assert isinstance(body["tool_results"], list)
        assert isinstance(body["cost_usd"], (int, float))

        # Tool chaining: search_videos was called
        search_calls = [tr for tr in body["tool_results"] if tr["tool"] == "search_videos"]
        assert len(search_calls) >= 1, (
            f"Expected search_videos call, got tools: {[tr['tool'] for tr in body['tool_results']]}"
        )

        # Tool chaining: analyze_video was called AFTER search
        analyze_calls = [tr for tr in body["tool_results"] if tr["tool"] == "analyze_video"]
        assert len(analyze_calls) >= 1, (
            f"Expected analyze_video call, got tools: {[tr['tool'] for tr in body['tool_results']]}"
        )

        # Verify ordering: search appears before analyze in tool_results
        search_idx = next(
            i for i, tr in enumerate(body["tool_results"]) if tr["tool"] == "search_videos"
        )
        analyze_idx = next(
            i for i, tr in enumerate(body["tool_results"]) if tr["tool"] == "analyze_video"
        )
        assert search_idx < analyze_idx, "search_videos should precede analyze_video"

        # Verify analyze_video SUCCEEDED (not errored due to R2 miss)
        analyze_result = analyze_calls[0].get("result", {})
        assert "error" not in str(analyze_result).lower(), (
            f"analyze_video should succeed with pre-warmed R2, got: {analyze_result}"
        )

        # Security: no internal data leaks
        text_lower = body["text"].lower()
        assert "postgres://" not in text_lower
        assert "traceback" not in text_lower


# ─── 9. Creator Evolution ─────────────────────────────────────────────────


@pytest.mark.gemini
@pytest.mark.external_api
@pytest.mark.db
@pytest.mark.slow
class TestCreatorEvolutionRealE2E:
    """POST /v1/analyze/creator → GET /v1/creators/{platform}/{username}/evolution.

    Tests the full data chain: creator analysis creates linked video_analysis
    records, then the evolution endpoint aggregates those records.

    Uses TikTok (khaby.lame) because evolution needs 5+ videos for
    risk_trajectory — YouTube's jawed has only 1 video and always 404s.
    """

    async def test_analyze_creator_then_query_evolution(
        self, live_client: httpx.AsyncClient, pro_api_key: str
    ) -> None:
        # Step 1: Analyze TikTok creator's videos (6 short videos)
        resp1 = await live_client.post(
            "/v1/analyze/creator",
            headers=_bearer(pro_api_key),
            json={"platform": "tiktok", "username": TIKTOK_CREATOR, "limit": 6},
            timeout=240,  # 6 videos × ~30s each
        )
        if resp1.status_code in (429, 500, 502, 503):
            pytest.skip(f"External API unavailable (HTTP {resp1.status_code})")
        assert resp1.status_code == 200, f"Creator analysis failed: {resp1.text}"
        body1 = resp1.json()
        videos_analyzed = body1["videos_analyzed"]

        # Step 2: Query evolution (uses the linked records from step 1)
        resp2 = await live_client.get(
            f"/v1/creators/tiktok/{TIKTOK_CREATOR}/evolution?period=365d",
            headers=_bearer(pro_api_key),
            timeout=15,
        )

        if videos_analyzed >= 5:
            # Should get 200 with real evolution data
            assert resp2.status_code == 200, (
                f"Expected 200 with {videos_analyzed} videos: {resp2.text}"
            )
            body2 = resp2.json()
            assert body2["creator_username"] == TIKTOK_CREATOR
            assert body2["platform"] == "tiktok"
            assert body2["period_days"] == 365
            assert body2["videos_analyzed"] >= 5
            assert body2["confidence_level"] in ("low", "medium", "high")
            assert isinstance(body2["current_topics"], dict)
            if body2.get("risk_trajectory"):
                assert body2["risk_trajectory"]["direction"] in (
                    "improving", "stable", "deteriorating"
                )
                assert 0 <= body2["risk_trajectory"]["current_score"] <= 1
        elif resp2.status_code == 404:
            # Fewer than 5 videos analyzed — insufficient_data is correct
            err = resp2.json()
            assert err["error"]["code"] in ("insufficient_data", "creator_not_found")
        else:
            pytest.fail(f"Unexpected status {resp2.status_code}: {resp2.text}")
