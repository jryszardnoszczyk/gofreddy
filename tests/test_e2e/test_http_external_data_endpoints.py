"""Live HTTP endpoint tests (no mocks) for external-provider integrations."""

from __future__ import annotations

import json
import os
import threading
import time
from collections.abc import Generator
from contextlib import asynccontextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
from urllib.parse import urlparse

import asyncpg
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from src.api.dependencies import verify_supabase_token
from src.api.main import create_app
from src.analysis.config import DatabaseSettings
from src.common.enums import Platform
from src.fraud.config import FraudDetectionConfig
from src.fraud.repository import PostgresFraudRepository
from src.fraud.service import FraudDetectionService
from src.search.service import SearchConfig, SearchService
from tests.fixtures.stable_ids import INSTAGRAM_CREATOR, TIKTOK_CREATOR

LIVE_API_KEY = "live_e2e_key"
_TEST_CLAIMS = {"sub": "test-e2e-user", "email": "e2e@test.com", "aud": "authenticated"}


def _noop_lifespan():
    @asynccontextmanager
    async def _lifespan(_app):
        yield

    return _lifespan


@pytest.fixture
def live_search_client(search_service, fetchers) -> Generator[TestClient]:
    """Real HTTP app for /v1/search wired to real services/fetchers."""
    with patch("src.api.main.lifespan", _noop_lifespan()):
        app = create_app()
    app.dependency_overrides[verify_supabase_token] = lambda: _TEST_CLAIMS
    app.state.search_service = search_service
    app.state.fetchers = fetchers
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


@pytest.fixture
def fake_scrapecreators_server() -> Generator[tuple[str, dict[str, str]], None, None]:
    """Local provider emulator for deterministic TikTok failure injection."""
    state = {"mode": "ok"}

    class Handler(BaseHTTPRequestHandler):
        server_version = "FakeScrapeCreators/1.0"

        def log_message(self, _format: str, *args) -> None:  # pragma: no cover
            return

        def _send_json(self, status_code: int, payload: dict) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path != "/v1/tiktok/search/keyword":
                self._send_json(404, {"error": "not_found"})
                return

            mode = state["mode"]
            if mode == "rate_limit":
                self.send_response(429)
                self.send_header("Content-Type", "application/json")
                self.send_header("Retry-After", "1")
                self.end_headers()
                self.wfile.write(b'{"error":"rate_limited"}')
                return
            if mode == "timeout":
                # Search service timeout should cut this call off.
                time.sleep(2.0)
                self._send_json(200, {"aweme_list": []})
                return
            if mode == "malformed":
                self._send_json(
                    200,
                    {
                        "aweme_list": [
                            None,
                            "bad_row",
                            {
                                "aweme_id": "ok123",
                                "desc": "ok",
                                "author": {"unique_id": "creator_ok", "uid": "u1"},
                                "statistics": {"play_count": 10, "digg_count": 1},
                            },
                        ]
                    },
                )
                return

            self._send_json(
                200,
                {
                    "aweme_list": [
                        {
                            "aweme_id": "ok-default",
                            "desc": "default",
                            "author": {"unique_id": "creator_default", "uid": "u2"},
                            "statistics": {"play_count": 20, "digg_count": 2},
                        }
                    ]
                },
            )

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", state
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.fixture
def live_search_client_fault_injection(
    search_service,
    fetchers,
    fake_scrapecreators_server: tuple[str, dict[str, str]],
) -> Generator[tuple[TestClient, dict[str, str]], None, None]:
    """Real HTTP app using local TikTok provider emulator for failure modes."""
    fake_base_url, state = fake_scrapecreators_server
    tiktok = fetchers[Platform.TIKTOK]
    original_base_url = tiktok.settings.scrapecreators_base_url
    original_timeout = search_service._config.platform_timeout_ms
    tiktok.settings.scrapecreators_base_url = fake_base_url
    search_service._config.platform_timeout_ms = 500

    with patch("src.api.main.lifespan", _noop_lifespan()):
        app = create_app()
    app.dependency_overrides[verify_supabase_token] = lambda: _TEST_CLAIMS
    app.state.search_service = search_service
    app.state.fetchers = fetchers

    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            yield client, state
    finally:
        tiktok.settings.scrapecreators_base_url = original_base_url
        search_service._config.platform_timeout_ms = original_timeout


@pytest.fixture
def live_search_client_fault_injection_partial(
    search_service,
    fetchers,
    fake_scrapecreators_server: tuple[str, dict[str, str]],
) -> Generator[tuple[TestClient, dict[str, str]], None, None]:
    """Real HTTP app with deterministic local success provider for partial-failure checks."""

    class DeterministicYouTubeFetcher:
        async def search(self, query: str, max_results: int = 50) -> list[dict]:
            return [{
                "id": "yt-local-1",
                "title": f"Local result for {query}",
                "uploader_id": "local_channel",
                "channel": "local_channel",
                "channel_id": "local_channel_id",
                "view_count": 123,
                "like_count": 12,
                "comment_count": 3,
            }]

    fake_base_url, state = fake_scrapecreators_server
    tiktok = fetchers[Platform.TIKTOK]
    original_base_url = tiktok.settings.scrapecreators_base_url
    tiktok.settings.scrapecreators_base_url = fake_base_url

    deterministic_service = SearchService(
        parser=search_service._parser,
        tiktok_fetcher=fetchers[Platform.TIKTOK],
        instagram_fetcher=fetchers[Platform.INSTAGRAM],
        youtube_fetcher=DeterministicYouTubeFetcher(),
        config=SearchConfig(platform_timeout_ms=500),
    )

    with patch("src.api.main.lifespan", _noop_lifespan()):
        app = create_app()
    app.dependency_overrides[verify_supabase_token] = lambda: _TEST_CLAIMS
    app.state.search_service = deterministic_service
    app.state.fetchers = fetchers

    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            yield client, state
    finally:
        tiktok.settings.scrapecreators_base_url = original_base_url


@pytest_asyncio.fixture
async def live_fraud_service() -> FraudDetectionService:
    """Real fraud service backed by a real DB when available."""
    db_config = DatabaseSettings()
    try:
        pool = await asyncpg.create_pool(
            dsn=db_config.database_url.get_secret_value(),
            min_size=1,
            max_size=2,
            command_timeout=60,
        )
    except Exception as exc:
        pytest.skip(f"Live fraud endpoint requires reachable DB: {exc}")

    repository = PostgresFraudRepository(pool)
    service = FraudDetectionService(
        repository=repository,
        config=FraudDetectionConfig(),
    )
    try:
        yield service
    finally:
        await service.close()
        await pool.close()


@pytest.fixture
def live_fraud_client(
    live_fraud_service: FraudDetectionService,
    fetchers,
) -> Generator[TestClient]:
    """Real HTTP app for /v1/fraud/analyze wired to real services/fetchers."""
    with patch("src.api.main.lifespan", _noop_lifespan()):
        app = create_app()
    app.dependency_overrides[verify_supabase_token] = lambda: _TEST_CLAIMS
    app.state.fraud_service = live_fraud_service
    app.state.fetchers = fetchers
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


@pytest.fixture
def fake_scrapecreators_fraud_server() -> Generator[tuple[str, dict[str, str]], None, None]:
    """Local TikTok provider emulator for deterministic fraud endpoint failures."""
    state = {
        "followers_mode": "ok",
        "profile_mode": "ok",
    }

    class Handler(BaseHTTPRequestHandler):
        server_version = "FakeScrapeCreatorsFraud/1.0"

        def log_message(self, _format: str, *args) -> None:  # pragma: no cover
            return

        def _send_json(self, status_code: int, payload: dict) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)

            if parsed.path == "/v1/tiktok/user/followers":
                followers_mode = state["followers_mode"]
                if followers_mode == "error":
                    self._send_json(500, {"error": "followers_failed"})
                    return
                if followers_mode == "malformed":
                    self._send_json(
                        200,
                        {"users": [None, "bad", {"unique_id": "fan_ok", "aweme_count": "3"}]},
                    )
                    return
                self._send_json(
                    200,
                    {
                        "users": [
                            {
                                "unique_id": "fan1",
                                "avatar_thumb": "https://example.com/pic.jpg",
                                "aweme_count": 1,
                                "follower_count": 10,
                                "following_count": 5,
                            }
                        ]
                    },
                )
                return

            if parsed.path == "/v1/tiktok/profile":
                profile_mode = state["profile_mode"]
                if profile_mode == "rate_limit":
                    self.send_response(429)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Retry-After", "1")
                    self.end_headers()
                    self.wfile.write(b'{"error":"rate_limited"}')
                    return
                if profile_mode == "not_found":
                    self._send_json(404, {"error": "not_found"})
                    return
                if profile_mode == "malformed":
                    self._send_json(200, {"user": "bad", "stats": "bad"})
                    return
                self._send_json(
                    200,
                    {
                        "user": {
                            "unique_id": "testcreator",
                            "nickname": "Test Creator",
                            "verified": False,
                        },
                        "stats": {
                            "follower_count": 12000,
                            "following_count": 150,
                            "video_count": 42,
                            "heart_count": 99999,
                        },
                    },
                )
                return

            if parsed.path == "/v3/tiktok/profile/videos":
                self._send_json(200, {"aweme_list": []})
                return

            if parsed.path == "/v1/tiktok/video/comments":
                self._send_json(200, {"comments": []})
                return

            self._send_json(404, {"error": "not_found"})

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", state
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.fixture
def live_fraud_client_fault_injection_tiktok(
    fake_scrapecreators_fraud_server: tuple[str, dict[str, str]],
) -> Generator[tuple[TestClient, dict[str, str]], None, None]:
    """Real HTTP app (full lifespan) with local TikTok provider emulator."""
    fake_base_url, state = fake_scrapecreators_fraud_server
    original_base_url = os.environ.get("SCRAPECREATORS_BASE_URL")
    os.environ["SCRAPECREATORS_BASE_URL"] = fake_base_url
    try:
        app = create_app()
        app.dependency_overrides[verify_supabase_token] = lambda: _TEST_CLAIMS
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                yield client, state
        except Exception as exc:
            # Full app lifespan requires DB startup. Skip cleanly in environments
            # where the configured DB is not reachable.
            if "Connect call failed" in str(exc) or "Connection refused" in str(exc):
                pytest.skip(f"Fraud fault-injection requires reachable DB: {exc}")
            raise
    finally:
        if original_base_url is None:
            os.environ.pop("SCRAPECREATORS_BASE_URL", None)
        else:
            os.environ["SCRAPECREATORS_BASE_URL"] = original_base_url


@pytest.mark.external_api
@pytest.mark.gemini
class TestPostSearch:
    """Live tests for POST /v1/search with multiple real examples."""

    @pytest.mark.parametrize(
        ("query", "platforms"),
        [
            ("fitness workout videos", None),
            ("#dance", ["tiktok", "instagram"]),
            ("python tutorial", ["youtube"]),
        ],
    )
    def test_search_live_multiple_queries(
        self,
        live_search_client: TestClient,
        query: str,
        platforms: list[str] | None,
    ) -> None:
        payload: dict[str, object] = {"query": query, "limit": 10}
        if platforms is not None:
            payload["platforms"] = platforms

        response = live_search_client.post(
            "/v1/search",
            headers={"Authorization": f"Bearer {LIVE_API_KEY}"},
            json=payload,
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "platforms_searched" in data
        assert "platforms_failed" in data
        assert "errors" in data
        assert isinstance(data["results"], list)
        assert isinstance(data["platforms_searched"], list)
        assert isinstance(data["platforms_failed"], list)


@pytest.mark.external_api
class TestPostSearchProviderFailureInjection:
    """E2E provider fault injection with real API stack and local provider emulator."""

    def test_search_provider_429_degrades_gracefully(
        self,
        live_search_client_fault_injection: tuple[TestClient, dict[str, str]],
    ) -> None:
        client, state = live_search_client_fault_injection
        state["mode"] = "rate_limit"

        response = client.post(
            "/v1/search",
            headers={"Authorization": f"Bearer {LIVE_API_KEY}"},
            json={
                "query": "ignored",
                "limit": 10,
                "structured_query": {
                    "scope": "videos",
                    "platforms": ["tiktok"],
                    "search_type": "keyword",
                    "filters": {"query": "resilience-429"},
                    "confidence": 1.0,
                    "confidence_level": "high",
                },
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "tiktok" in data["platforms_failed"]
        assert isinstance(data["errors"], list)

    def test_search_provider_timeout_degrades_gracefully(
        self,
        live_search_client_fault_injection: tuple[TestClient, dict[str, str]],
    ) -> None:
        client, state = live_search_client_fault_injection
        state["mode"] = "timeout"

        response = client.post(
            "/v1/search",
            headers={"Authorization": f"Bearer {LIVE_API_KEY}"},
            json={
                "query": "ignored",
                "limit": 10,
                "structured_query": {
                    "scope": "videos",
                    "platforms": ["tiktok"],
                    "search_type": "keyword",
                    "filters": {"query": "resilience-timeout"},
                    "confidence": 1.0,
                    "confidence_level": "high",
                },
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "tiktok" in data["platforms_failed"]
        assert any("timed out" in err.lower() for err in data["errors"])

    def test_search_malformed_provider_payload_keeps_success_response(
        self,
        live_search_client_fault_injection: tuple[TestClient, dict[str, str]],
    ) -> None:
        client, state = live_search_client_fault_injection
        state["mode"] = "malformed"

        response = client.post(
            "/v1/search",
            headers={"Authorization": f"Bearer {LIVE_API_KEY}"},
            json={
                "query": "ignored",
                "limit": 10,
                "structured_query": {
                    "scope": "videos",
                    "platforms": ["tiktok"],
                    "search_type": "keyword",
                    "filters": {"query": "resilience-malformed"},
                    "confidence": 1.0,
                    "confidence_level": "high",
                },
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["platforms_failed"] == []
        assert data["total"] == 1

    def test_search_partial_platform_failure_still_returns_overall_success(
        self,
        live_search_client_fault_injection_partial: tuple[TestClient, dict[str, str]],
    ) -> None:
        client, state = live_search_client_fault_injection_partial
        state["mode"] = "rate_limit"

        response = client.post(
            "/v1/search",
            headers={"Authorization": f"Bearer {LIVE_API_KEY}"},
            json={
                "query": "ignored",
                "limit": 10,
                "structured_query": {
                    "scope": "videos",
                    "platforms": ["tiktok", "youtube"],
                    "search_type": "keyword",
                    "filters": {"query": "python tutorial"},
                    "confidence": 1.0,
                    "confidence_level": "high",
                },
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "tiktok" in data["platforms_failed"]
        assert "youtube" in data["platforms_searched"]
        assert "youtube" not in data["platforms_failed"]


@pytest.mark.external_api
class TestPostFraudAnalyzeProviderFailureInjection:
    """Reliability matrix for fraud degraded behavior:
    - TikTok followers provider error -> 200 with analysis (degraded followers input).
    - TikTok profile provider 429 -> 429 with rate_limited code.
    - TikTok malformed profile payload -> 200 with degraded/minimal stats.
    """

    def test_fraud_followers_error_still_returns_success(
        self,
        live_fraud_client_fault_injection_tiktok: tuple[TestClient, dict[str, str]],
    ) -> None:
        client, state = live_fraud_client_fault_injection_tiktok
        state["followers_mode"] = "error"
        state["profile_mode"] = "ok"

        response = client.post(
            "/v1/fraud/analyze",
            headers={"Authorization": f"Bearer {LIVE_API_KEY}"},
            json={
                "platform": "tiktok",
                "username": "testcreator",
                "options": {"sample_size": 50, "force_refresh": True},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["platform"] == "tiktok"
        assert "analysis_id" in data
        assert "fraud_analysis" in data

    def test_fraud_profile_rate_limit_maps_to_429(
        self,
        live_fraud_client_fault_injection_tiktok: tuple[TestClient, dict[str, str]],
    ) -> None:
        client, state = live_fraud_client_fault_injection_tiktok
        state["followers_mode"] = "ok"
        state["profile_mode"] = "rate_limit"

        response = client.post(
            "/v1/fraud/analyze",
            headers={"Authorization": f"Bearer {LIVE_API_KEY}"},
            json={
                "platform": "tiktok",
                "username": "testcreator",
                "options": {"sample_size": 50, "force_refresh": True},
            },
        )

        assert response.status_code == 429
        data = response.json()
        assert data["error"]["code"] == "rate_limited"

    def test_fraud_profile_malformed_payload_still_returns_success(
        self,
        live_fraud_client_fault_injection_tiktok: tuple[TestClient, dict[str, str]],
    ) -> None:
        client, state = live_fraud_client_fault_injection_tiktok
        state["followers_mode"] = "ok"
        state["profile_mode"] = "malformed"

        response = client.post(
            "/v1/fraud/analyze",
            headers={"Authorization": f"Bearer {LIVE_API_KEY}"},
            json={
                "platform": "tiktok",
                "username": "testcreator",
                "options": {"sample_size": 50, "force_refresh": True},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["platform"] == "tiktok"
        assert "analysis_id" in data


@pytest.mark.external_api
@pytest.mark.gemini
class TestPostFraudAnalyze:
    """Live tests for POST /v1/fraud/analyze with multiple creator examples."""

    @pytest.mark.parametrize(
        ("platform", "username"),
        [
            ("tiktok", TIKTOK_CREATOR),
            ("instagram", INSTAGRAM_CREATOR),
        ],
    )
    def test_fraud_analyze_live_multiple_platforms(
        self,
        live_fraud_client: TestClient,
        platform: str,
        username: str,
    ) -> None:
        response = live_fraud_client.post(
            "/v1/fraud/analyze",
            headers={"Authorization": f"Bearer {LIVE_API_KEY}"},
            json={
                "platform": platform,
                "username": username,
                "options": {"sample_size": 50, "force_refresh": True},
            },
        )

        # 200 = full live success, 500 = provider failure path (e.g. auth/quota)
        # 429 = API layer rate-limit / upstream rate-limit propagation.
        # 404 = creator handle no longer exists/available on provider.
        assert response.status_code in {200, 404, 429, 500}
        data = response.json()

        if response.status_code == 200:
            assert data["platform"] == platform
            assert data["creator_username"] == username
            assert "fraud_analysis" in data
            assert "risk_level" in data
            assert "risk_score" in data
            assert data["status"] in {"completed", "cached"}
        else:
            assert "error" in data
            assert data["error"]["code"] in {
                "fetch_error",
                "analysis_error",
                "rate_limited",
                "creator_not_found",
            }
