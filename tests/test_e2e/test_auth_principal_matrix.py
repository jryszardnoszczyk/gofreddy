"""E2E auth matrix tests for request-scoped AuthPrincipal behavior.

These tests intentionally avoid dependency overrides for auth dependencies.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

import httpx
import jwt as pyjwt
import pytest
import pytest_asyncio
from fastapi import FastAPI
from pydantic import SecretStr

from src.api.exceptions import register_exception_handlers
from src.api.rate_limit import limiter
from src.api.routers import auth, creators, evolution, search, stories, trends
from src.billing.repository import BillingRepository
from src.billing.service import BillingService
from src.common.enums import Platform
from src.evolution.models import EvolutionResponse
from src.evolution.repository import PostgresEvolutionRepository
from src.trends.models import TrendResponse, TrendSnapshot
from tests.helpers.pool_adapter import SingleConnectionPool

_TEST_JWT_SECRET = "cp5-auth-matrix-secret"
_TEST_SUPABASE_URL = "http://cp5.supabase.test"
_PROFILE_USERNAME = "testuser"


class _SearchServiceStub:
    async def search(
        self,
        *,
        query: str,
        structured_query=None,
        platforms=None,
        limit: int = 50,
    ) -> dict:
        return {
            "interpretation": {"query": query},
            "confidence": "high",
            "results": [
                {
                    "platform": "tiktok",
                    "video_id": "123",
                    "creator_handle": "creator_one",
                    "title": "Test video",
                    "description": "Test result",
                    "relevance_score": 1.0,
                }
            ],
            "total": 1,
            "platforms_searched": ["tiktok"],
            "platforms_failed": [],
            "errors": [],
        }


class _TrendServiceStub:
    async def get_trends(self, *, platform: Platform) -> TrendResponse:
        snapshot = TrendSnapshot(
            id=uuid4(),
            snapshot_date=date(2026, 2, 1),
            platform=platform,
            sample_size=120,
            confidence_level="high",
        )
        return TrendResponse(snapshot=snapshot, share_of_voice={"nike": 100.0})


class _EvolutionServiceStub:
    async def get_evolution(
        self,
        platform: Platform,
        username: str,
        period_days: int,
    ) -> EvolutionResponse:
        return EvolutionResponse(
            creator_username=username,
            platform=platform,
            period_days=period_days,
            videos_analyzed=12,
            confidence_level="medium",
            current_topics={"fitness": 1.0},
            current_risk_level="low",
        )


class _StoryServiceStub:
    async def capture_stories_now(self, **kwargs):  # pragma: no cover - not exercised in this suite
        return {"captured": [], "skipped": 0}

    async def get_captured_stories(
        self,
        *,
        user_id: UUID,
        platform: Platform,
        creator_username: str,
    ) -> list[dict]:
        return [
            {
                "id": uuid4(),
                "story_id": "story_1",
                "platform": platform.value,
                "creator_username": creator_username,
                "media_type": "video",
                "media_url": "https://example.invalid/story_1.mp4",
                "duration_seconds": 12,
                "captured_at": datetime.now(timezone.utc),
            }
        ]


@dataclass(frozen=True)
class _SeededCredentials:
    free_jwt: str
    free_api_key: str
    pro_jwt: str
    pro_api_key: str


@dataclass(frozen=True)
class _RouteCase:
    name: str
    method: str
    path: str
    free_status: int
    pro_status: int
    json_body: dict | None = None


_ROUTE_CASES: tuple[_RouteCase, ...] = (
    _RouteCase("auth_me", "GET", "/v1/auth/me", free_status=200, pro_status=200),
    _RouteCase(
        "search",
        "POST",
        "/v1/search",
        free_status=200,
        pro_status=200,
        json_body={"query": "fitness creators"},
    ),
    _RouteCase(
        "trends",
        "GET",
        "/v1/trends?platform=tiktok",
        free_status=403,
        pro_status=200,
    ),
    _RouteCase(
        "evolution",
        "GET",
        f"/v1/creators/tiktok/{_PROFILE_USERNAME}/evolution?period=90d",
        free_status=403,
        pro_status=200,
    ),
    _RouteCase(
        "stories",
        "GET",
        f"/v1/stories/instagram/{_PROFILE_USERNAME}",
        free_status=403,
        pro_status=200,
    ),
    _RouteCase(
        "creator_profile",
        "GET",
        f"/v1/creators/tiktok/{_PROFILE_USERNAME}",
        free_status=200,
        pro_status=200,
    ),
    # auth_logout MUST be last — it revokes the JWT token via blocklist,
    # which would cause subsequent JWT-auth requests to return 401.
    _RouteCase("auth_logout", "POST", "/v1/auth/logout", free_status=204, pro_status=204),
)


def _make_jwt(supabase_user_id: str, *, email: str) -> str:
    payload = {
        "sub": supabase_user_id,
        "email": email,
        "iss": f"{_TEST_SUPABASE_URL}/auth/v1",
        "aud": "authenticated",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    return pyjwt.encode(payload, _TEST_JWT_SECRET, algorithm="HS256")


def _auth_headers(*, jwt_token: str | None = None, api_key: str | None = None) -> dict[str, str]:
    headers: dict[str, str] = {}
    if jwt_token is not None:
        headers["Authorization"] = f"Bearer {jwt_token}"
    if api_key is not None:
        headers["X-API-Key"] = api_key
    return headers


async def _insert_user_with_credentials(db_conn, *, tier: str) -> tuple[str, str]:
    user_id = uuid4()
    supabase_user_id = f"supa_{user_id.hex[:16]}"
    email = f"{tier}-{user_id.hex[:8]}@example.com"

    await db_conn.execute(
        "INSERT INTO users (id, email, supabase_user_id) VALUES ($1, $2, $3)",
        user_id,
        email,
        supabase_user_id,
    )

    if tier == "pro":
        now = datetime.now(timezone.utc)
        await db_conn.execute(
            """INSERT INTO subscriptions
               (id, user_id, stripe_subscription_id, stripe_price_id, tier, status,
                current_period_start, current_period_end, cancel_at_period_end)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
            uuid4(),
            user_id,
            f"sub_{uuid4().hex[:12]}",
            "price_test",
            "pro",
            "active",
            now,
            now + timedelta(days=30),
            False,
        )

    api_key = f"vi_sk_{tier}_{uuid4().hex}"
    await db_conn.execute(
        """INSERT INTO api_keys (id, user_id, key_hash, key_prefix, name)
           VALUES ($1, $2, $3, $4, $5)""",
        uuid4(),
        user_id,
        hashlib.sha256(api_key.encode()).hexdigest(),
        api_key[:12],
        f"{tier}-matrix-key",
    )

    return _make_jwt(supabase_user_id, email=email), api_key


async def _seed_creator_profile_row(db_conn) -> None:
    now = datetime.now(timezone.utc)
    await db_conn.execute(
        """INSERT INTO creators
           (platform, username, display_name, follower_count, video_count, last_analyzed_at, cached_at)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (platform, username) DO UPDATE SET
             display_name = EXCLUDED.display_name,
             follower_count = EXCLUDED.follower_count,
             video_count = EXCLUDED.video_count,
             last_analyzed_at = EXCLUDED.last_analyzed_at,
             cached_at = EXCLUDED.cached_at
        """,
        Platform.TIKTOK.value,
        _PROFILE_USERNAME,
        "Test User",
        3210,
        56,
        now - timedelta(days=1),
        now,
    )


async def _request_case(
    client: httpx.AsyncClient,
    case: _RouteCase,
    headers: dict[str, str],
) -> httpx.Response:
    if case.method == "GET":
        return await client.get(case.path, headers=headers)
    if case.method == "POST":
        if case.json_body is None:
            return await client.post(case.path, headers=headers)
        return await client.post(case.path, headers=headers, json=case.json_body)
    raise AssertionError(f"Unsupported method in test case: {case.method}")


def _assert_route_payload(case: _RouteCase, response: httpx.Response, *, tier: str) -> None:
    if response.status_code == 204:
        return

    body = response.json()
    if case.name == "auth_me":
        assert body["tier"] == tier
        assert "user_id" in body
        return
    if case.name == "search":
        assert body["total"] == 1
        assert body["results"][0]["platform"] == "tiktok"
        return
    if case.name == "trends":
        assert body["snapshot"]["platform"] == "tiktok"
        return
    if case.name == "evolution":
        assert body["creator_username"] == _PROFILE_USERNAME
        return
    if case.name == "stories":
        assert len(body) == 1
        assert body[0]["creator_username"] == _PROFILE_USERNAME
        return
    if case.name == "creator_profile":
        assert body["username"] == _PROFILE_USERNAME
        assert body["display_name"] == "Test User"
        return

    raise AssertionError(f"Unhandled case payload assertion: {case.name}")


def _assert_tier_required(response: httpx.Response, *, expected_tier: str) -> None:
    body = response.json()["error"]
    assert body["code"] == "tier_required"
    assert body["required_tier"] == "pro"
    assert body["current_tier"] == expected_tier
    assert "upgrade_url" not in body


def _normalized_case_body(case: _RouteCase, response: httpx.Response) -> dict | list | None:
    """Normalize volatile response fields before parity comparisons."""
    if response.status_code == 204:
        return None

    body = response.json()

    if case.name == "trends" and response.status_code == 200:
        snapshot = dict(body["snapshot"])
        snapshot.pop("id", None)
        return {**body, "snapshot": snapshot}

    if case.name == "stories" and response.status_code == 200:
        return [
            {
                key: value
                for key, value in item.items()
                if key not in {"id", "captured_at", "original_posted_at", "original_expires_at"}
            }
            for item in body
        ]

    return body


@pytest_asyncio.fixture
async def auth_matrix_app(db_conn):
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(auth.router, prefix="/v1")
    app.include_router(search.router, prefix="/v1")
    app.include_router(trends.router, prefix="/v1")
    app.include_router(evolution.router, prefix="/v1")
    app.include_router(stories.router, prefix="/v1")
    app.include_router(creators.router, prefix="/v1")
    limiter.enabled = False

    pool = SingleConnectionPool(db_conn)
    app.state.billing_repository = BillingRepository(pool)
    app.state.billing_service = BillingService(app.state.billing_repository)
    app.state.search_service = _SearchServiceStub()
    app.state.trend_service = _TrendServiceStub()
    app.state.evolution_service = _EvolutionServiceStub()
    app.state.story_service = _StoryServiceStub()
    app.state.evolution_repository = PostgresEvolutionRepository(pool)
    app.state.supabase_settings = SimpleNamespace(
        supabase_url=_TEST_SUPABASE_URL,
        supabase_anon_key="anon-test",
        supabase_jwt_secret=SecretStr(_TEST_JWT_SECRET),
    )
    app.state.jwks_client = None

    assert app.dependency_overrides == {}
    return app


@pytest_asyncio.fixture
async def auth_matrix_client(auth_matrix_app):
    transport = httpx.ASGITransport(app=auth_matrix_app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def seeded_credentials(db_conn) -> _SeededCredentials:
    free_jwt, free_api_key = await _insert_user_with_credentials(db_conn, tier="free")
    pro_jwt, pro_api_key = await _insert_user_with_credentials(db_conn, tier="pro")
    await _seed_creator_profile_row(db_conn)
    return _SeededCredentials(
        free_jwt=free_jwt,
        free_api_key=free_api_key,
        pro_jwt=pro_jwt,
        pro_api_key=pro_api_key,
    )


@pytest.mark.db
class TestAuthPrincipalMatrix:
    @pytest.mark.asyncio
    async def test_free_tier_jwt_and_api_key_parity(
        self,
        auth_matrix_client: httpx.AsyncClient,
        seeded_credentials: _SeededCredentials,
    ) -> None:
        jwt_headers = _auth_headers(jwt_token=seeded_credentials.free_jwt)
        api_key_headers = _auth_headers(api_key=seeded_credentials.free_api_key)

        for case in _ROUTE_CASES:
            jwt_resp = await _request_case(auth_matrix_client, case, jwt_headers)
            api_key_resp = await _request_case(auth_matrix_client, case, api_key_headers)

            assert jwt_resp.status_code == case.free_status, case.name
            assert api_key_resp.status_code == case.free_status, case.name
            assert jwt_resp.status_code == api_key_resp.status_code, case.name
            assert _normalized_case_body(case, jwt_resp) == _normalized_case_body(
                case, api_key_resp
            ), case.name

            if case.free_status == 403:
                _assert_tier_required(jwt_resp, expected_tier="free")
                _assert_tier_required(api_key_resp, expected_tier="free")
            elif case.free_status in {200, 204}:
                _assert_route_payload(case, jwt_resp, tier="free")
                _assert_route_payload(case, api_key_resp, tier="free")

    @pytest.mark.asyncio
    async def test_pro_tier_jwt_and_api_key_parity(
        self,
        auth_matrix_client: httpx.AsyncClient,
        seeded_credentials: _SeededCredentials,
    ) -> None:
        jwt_headers = _auth_headers(jwt_token=seeded_credentials.pro_jwt)
        api_key_headers = _auth_headers(api_key=seeded_credentials.pro_api_key)

        for case in _ROUTE_CASES:
            jwt_resp = await _request_case(auth_matrix_client, case, jwt_headers)
            api_key_resp = await _request_case(auth_matrix_client, case, api_key_headers)

            assert jwt_resp.status_code == case.pro_status, case.name
            assert api_key_resp.status_code == case.pro_status, case.name
            assert jwt_resp.status_code == api_key_resp.status_code, case.name
            assert _normalized_case_body(case, jwt_resp) == _normalized_case_body(
                case, api_key_resp
            ), case.name

            if case.pro_status in {200, 204}:
                _assert_route_payload(case, jwt_resp, tier="pro")
                _assert_route_payload(case, api_key_resp, tier="pro")

    @pytest.mark.asyncio
    async def test_invalid_and_missing_credentials_return_401(
        self,
        auth_matrix_client: httpx.AsyncClient,
    ) -> None:
        invalid_jwt_headers = _auth_headers(jwt_token="invalid")
        invalid_api_key_headers = _auth_headers(api_key="invalid-key")
        missing_headers: dict[str, str] = {}

        for case in _ROUTE_CASES:
            invalid_jwt_resp = await _request_case(auth_matrix_client, case, invalid_jwt_headers)
            invalid_api_key_resp = await _request_case(auth_matrix_client, case, invalid_api_key_headers)
            missing_resp = await _request_case(auth_matrix_client, case, missing_headers)

            assert invalid_jwt_resp.status_code == 401, case.name
            assert invalid_api_key_resp.status_code == 401, case.name
            assert missing_resp.status_code == 401, case.name

            assert invalid_jwt_resp.json()["error"]["code"] == "invalid_token", case.name
            assert invalid_api_key_resp.json()["error"]["code"] == "invalid_api_key", case.name
            assert missing_resp.json()["error"]["code"] == "missing_credentials", case.name

    @pytest.mark.asyncio
    async def test_bearer_precedence_when_both_headers_present(
        self,
        auth_matrix_client: httpx.AsyncClient,
        seeded_credentials: _SeededCredentials,
    ) -> None:
        headers = _auth_headers(jwt_token="invalid", api_key=seeded_credentials.pro_api_key)
        response = await auth_matrix_client.get("/v1/auth/me", headers=headers)
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "invalid_token"

    @pytest.mark.asyncio
    async def test_malformed_authorization_header_does_not_fallback_to_api_key(
        self,
        auth_matrix_client: httpx.AsyncClient,
        seeded_credentials: _SeededCredentials,
    ) -> None:
        response = await auth_matrix_client.get(
            "/v1/auth/me",
            headers={
                "Authorization": "Bearer",
                "X-API-Key": seeded_credentials.pro_api_key,
            },
        )
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "invalid_token"
