"""HTTP integration tests for agent endpoints (POST /v1/agent/chat, /v1/agent/chat/stream).

All tests use mocked orchestrator and billing — agent logic is tested by
the orchestrator-level tests (tests/test_orchestrator/).
"""

from __future__ import annotations

import asyncio
import json
from contextlib import suppress
from collections.abc import Generator
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.api.dependencies import get_current_user_id, get_billing_context, verify_supabase_token
from src.api.main import create_app
from src.api.rate_limit import limiter
from src.billing.models import BillingContext, Subscription, User, UsagePeriod
from src.billing.service import BillingService
from src.billing.tiers import Tier
from src.common.enums import Platform
from src.orchestrator.exceptions import AgentError
from src.orchestrator.models import AgentResponse


# ── Helpers ──────────────────────────────────────────────────

PRO_KEY = "pro_key_12345"
FREE_KEY = "free_key_12345"
_CONV_ID = str(uuid4())


def _create_billing_context(tier: Tier) -> BillingContext:
    """Create a billing context for the given tier."""
    user_id = uuid4()
    now = datetime.now(timezone.utc)
    user = User(
        id=user_id,
        email="test@example.com",
        stripe_customer_id="cus_test123",
        created_at=now,
    )
    usage_period = UsagePeriod(
        id=uuid4(),
        user_id=user_id,
        period_start=now,
        period_end=now,
        videos_used=0,
        videos_limit=50000 if tier == Tier.PRO else 100,
    )
    subscription = None
    if tier == Tier.PRO:
        subscription = Subscription(
            id=uuid4(),
            user_id=user_id,
            stripe_subscription_id="sub_test123",
            tier=tier,
            status="active",
            current_period_start=now,
            current_period_end=now,
            cancel_at_period_end=False,
        )
    return BillingContext(
        user=user,
        tier=tier,
        usage_period=usage_period,
        subscription=subscription,
    )


def _parse_sse_events(body: str) -> list[dict]:
    """Parse SSE body text into list of {event, data} dicts."""
    events = []
    current: dict = {}
    for line in body.split("\n"):
        line = line.strip()
        if line.startswith("event:"):
            current["event"] = line[len("event:"):].strip()
        elif line.startswith("data:"):
            raw = line[len("data:"):].strip()
            try:
                current["data"] = json.loads(raw)
            except json.JSONDecodeError:
                current["data"] = raw
        elif line == "" and current:
            events.append(current)
            current = {}
    if current:
        events.append(current)
    return events


# ── Fixtures ─────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _reset_sse_state():
    """Reset sse-starlette AppStatus between tests."""
    try:
        from sse_starlette.sse import AppStatus
        import asyncio
        AppStatus.should_exit_event = asyncio.Event()
    except (ImportError, AttributeError):
        pass
    yield


@pytest.fixture
def mock_orchestrator() -> MagicMock:
    """Mock VideoIntelligenceAgent."""
    orch = MagicMock()
    orch.chat = AsyncMock(return_value=AgentResponse(
        text="I found 3 videos about cooking.",
        actions_taken=["search_videos(query='cooking')"],
        tool_results=[{"tool": "search_videos", "result": {"total": 3}}],
        cost_usd=0.002,
        gemini_calls=2,
    ))

    async def _stream_events(*args, **kwargs):
        yield ("text_delta", {"text": "Here are the results."})
        yield ("done", {"finish_reason": "complete", "text": "Here are the results.", "cost_usd": 0.001, "gemini_calls": 1, "actions_taken": []})

    orch.stream_chat = _stream_events
    return orch


@pytest.fixture
def mock_billing_service() -> MagicMock:
    """Mock BillingService that returns Pro billing context."""
    service = MagicMock(spec=BillingService)
    service.get_billing_context_for_user = AsyncMock(
        return_value=_create_billing_context(Tier.PRO)
    )
    return service


@pytest.fixture
def client(
    mock_orchestrator: MagicMock,
    mock_billing_service: MagicMock,
    mock_db_pool,
) -> Generator[TestClient]:
    """TestClient with mocked orchestrator and billing."""
    app = create_app()

    limiter.enabled = False

    # Auth — bypass JWT verification but keep HTTPBearer presence check
    _test_user_id = uuid4()
    _test_claims = {"sub": "test-agent-user", "email": "agent@test.com", "aud": "authenticated"}
    _security = HTTPBearer()

    async def _mock_verify_token(
        credentials: HTTPAuthorizationCredentials = Depends(_security),
    ) -> dict:
        return _test_claims

    async def _mock_get_user_id(
        credentials: HTTPAuthorizationCredentials = Depends(_security),
    ) -> UUID:
        return _test_user_id

    app.dependency_overrides[verify_supabase_token] = _mock_verify_token
    app.dependency_overrides[get_current_user_id] = _mock_get_user_id

    # Core
    app.state.db_pool = mock_db_pool
    app.state.video_storage = MagicMock()
    app.state.analyzer = MagicMock()
    app.state.fetchers = {
        Platform.TIKTOK: MagicMock(),
        Platform.INSTAGRAM: MagicMock(),
        Platform.YOUTUBE: MagicMock(),
    }

    # Analysis
    app.state.analysis_service = MagicMock()
    app.state.analysis_repository = MagicMock()

    # Search
    app.state.search_service = MagicMock()

    # Fraud
    app.state.fraud_service = MagicMock()
    app.state.fraud_service.close = AsyncMock()
    app.state.fraud_repository = MagicMock()

    # Demographics / Brands
    app.state.demographics_service = MagicMock()
    app.state.demographics_repository = MagicMock()
    app.state.brand_service = MagicMock()
    app.state.brand_repository = MagicMock()

    # Billing (agent-specific mock)
    app.state.billing_service = mock_billing_service
    app.state.billing_repository = MagicMock()

    # Jobs
    app.state.job_service = MagicMock()
    app.state.job_repository = MagicMock()
    app.state.task_client = MagicMock()
    app.state.job_worker = MagicMock()

    # Trends / Evolution
    app.state.trend_service = MagicMock()
    app.state.trend_repository = MagicMock()
    app.state.evolution_service = MagicMock()
    app.state.evolution_repository = MagicMock()

    # Deepfake
    app.state.deepfake_service = MagicMock()
    app.state.deepfake_repository = MagicMock()

    # Stories
    app.state.story_service = MagicMock()
    app.state.story_repository = MagicMock()
    app.state.story_storage = MagicMock()

    # Agent (agent-specific mock)
    app.state.orchestrator = mock_orchestrator

    try:
        yield TestClient(app, raise_server_exceptions=False)
    finally:
        limiter.enabled = True


# ── Auth & Billing Gate Tests ────────────────────────────────


@pytest.mark.mock_required
class TestChatAuth:
    def test_chat_no_auth(self, client: TestClient) -> None:
        """No Bearer header -> 401."""
        resp = client.post("/v1/agent/chat", json={"message": "hello"})
        assert resp.status_code == 401

    def test_chat_free_tier_allowed(self, client: TestClient) -> None:
        """Free tier -> 200 (agent available to all tiers since PR-029)."""
        client.app.dependency_overrides[get_billing_context] = lambda: _create_billing_context(Tier.FREE)
        try:
            resp = client.post(
                "/v1/agent/chat",
                headers={"Authorization": "Bearer test"},
                json={"message": "hello", "conversation_id": _CONV_ID},
            )
            assert resp.status_code == 200
        finally:
            client.app.dependency_overrides.pop(get_billing_context, None)

    def test_stream_no_auth(self, client: TestClient) -> None:
        """No Bearer header -> 401."""
        resp = client.post("/v1/agent/chat/stream", json={"message": "hello"})
        assert resp.status_code == 401

    def test_stream_free_tier_allowed(self, client: TestClient) -> None:
        """Free tier -> 200 (agent available to all tiers since PR-029)."""
        client.app.dependency_overrides[get_billing_context] = lambda: _create_billing_context(Tier.FREE)
        try:
            resp = client.post(
                "/v1/agent/chat/stream",
                headers={"Authorization": "Bearer test"},
                json={"message": "hello", "conversation_id": _CONV_ID},
            )
            assert resp.status_code == 200
        finally:
            client.app.dependency_overrides.pop(get_billing_context, None)


@pytest.mark.mock_required
class TestLimiterRegression:
    def test_chat_with_limiter_enabled_no_500(self, client: TestClient) -> None:
        """Enabling limiter must not crash chat endpoint."""
        limiter.enabled = True
        try:
            resp = client.post(
                "/v1/agent/chat",
                headers={"Authorization": f"Bearer {PRO_KEY}"},
                json={"message": "hello", "conversation_id": _CONV_ID},
            )
        finally:
            limiter.enabled = False
        assert resp.status_code == 200, resp.text

    def test_stream_with_limiter_enabled_no_500(self, client: TestClient) -> None:
        """Enabling limiter must not crash stream endpoint."""
        limiter.enabled = True
        try:
            resp = client.post(
                "/v1/agent/chat/stream",
                headers={"Authorization": f"Bearer {PRO_KEY}"},
                json={"message": "hello", "conversation_id": _CONV_ID},
            )
        finally:
            limiter.enabled = False
        assert resp.status_code == 200, resp.text


# ── Validation Tests ─────────────────────────────────────────


@pytest.mark.mock_required
class TestChatValidation:
    def test_chat_empty_message(self, client: TestClient) -> None:
        """Empty string -> 422."""
        resp = client.post(
            "/v1/agent/chat",
            headers={"Authorization": f"Bearer {PRO_KEY}"},
            json={"message": ""},
        )
        assert resp.status_code == 422

    def test_chat_message_too_long(self, client: TestClient) -> None:
        """2001 chars -> 422."""
        resp = client.post(
            "/v1/agent/chat",
            headers={"Authorization": f"Bearer {PRO_KEY}"},
            json={"message": "x" * 2001},
        )
        assert resp.status_code == 422

    def test_chat_invalid_json(self, client: TestClient) -> None:
        """Malformed body -> 422."""
        resp = client.post(
            "/v1/agent/chat",
            headers={"Authorization": f"Bearer {PRO_KEY}", "Content-Type": "application/json"},
            content="not json",
        )
        assert resp.status_code == 422

    def test_stream_empty_message(self, client: TestClient) -> None:
        """Empty string -> 422 (stream endpoint validates request body too)."""
        resp = client.post(
            "/v1/agent/chat/stream",
            headers={"Authorization": f"Bearer {PRO_KEY}"},
            json={"message": ""},
        )
        assert resp.status_code == 422

    def test_stream_message_too_long(self, client: TestClient) -> None:
        """2001 chars -> 422 (stream endpoint validates request body too)."""
        resp = client.post(
            "/v1/agent/chat/stream",
            headers={"Authorization": f"Bearer {PRO_KEY}"},
            json={"message": "x" * 2001},
        )
        assert resp.status_code == 422


# ── Happy Path — Chat ────────────────────────────────────────


@pytest.mark.mock_required
class TestChatHappyPath:
    def test_chat_success(self, client: TestClient, mock_orchestrator: MagicMock) -> None:
        """Pro key + valid message -> 200 with AgentResponse shape."""
        resp = client.post(
            "/v1/agent/chat",
            headers={"Authorization": f"Bearer {PRO_KEY}"},
            json={"message": "Find cooking videos on TikTok", "conversation_id": _CONV_ID},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "text" in body
        assert "cost_usd" in body
        assert "gemini_calls" in body
        assert "actions_taken" in body
        assert "tool_results" in body
        assert body["text"] == "I found 3 videos about cooking."
        assert body["gemini_calls"] == 2

    def test_chat_with_history(self, client: TestClient, mock_orchestrator: MagicMock) -> None:
        """Request with conversation history -> 200, orchestrator receives history."""
        resp = client.post(
            "/v1/agent/chat",
            headers={"Authorization": f"Bearer {PRO_KEY}"},
            json={
                "message": "Tell me more",
                "conversation_id": _CONV_ID,
                "history": [
                    {"role": "user", "parts": [{"text": "Find cooking videos"}]},
                    {"role": "model", "parts": [{"text": "I found 3 cooking videos."}]},
                ],
            },
        )
        assert resp.status_code == 200
        mock_orchestrator.chat.assert_awaited_once()
        call_kwargs = mock_orchestrator.chat.call_args
        assert call_kwargs.kwargs.get("history") is not None or (
            len(call_kwargs.args) > 1 and call_kwargs.args[1] is not None
        )


# ── Error Handling — Chat ────────────────────────────────────


@pytest.mark.mock_required
class TestChatErrors:
    def test_chat_agent_error(self, client: TestClient, mock_orchestrator: MagicMock) -> None:
        """AgentError -> 500 with agent_error code."""
        mock_orchestrator.chat = AsyncMock(side_effect=AgentError("Tool registry unavailable"))
        resp = client.post(
            "/v1/agent/chat",
            headers={"Authorization": f"Bearer {PRO_KEY}"},
            json={"message": "hello", "conversation_id": _CONV_ID},
        )
        assert resp.status_code == 500
        body = resp.json()
        assert body["error"]["code"] == "agent_error"
        assert body["error"]["message"] == "Agent encountered an error"
        assert "Tool registry unavailable" not in json.dumps(body)

    def test_chat_unexpected_error(self, client: TestClient, mock_orchestrator: MagicMock) -> None:
        """Unexpected error -> 500 with internal_error, no detail leakage."""
        mock_orchestrator.chat = AsyncMock(side_effect=RuntimeError("SECRET_DB_PASSWORD"))
        resp = client.post(
            "/v1/agent/chat",
            headers={"Authorization": f"Bearer {PRO_KEY}"},
            json={"message": "hello", "conversation_id": _CONV_ID},
        )
        assert resp.status_code == 500
        body = resp.json()
        assert body["error"]["code"] == "internal_error"
        assert "SECRET_DB_PASSWORD" not in json.dumps(body)


# ── Happy Path — Stream ──────────────────────────────────────


@pytest.mark.mock_required
class TestStreamHappyPath:
    def test_stream_success(self, client: TestClient) -> None:
        """Pro key -> 200, text/event-stream, valid SSE events."""
        resp = client.post(
            "/v1/agent/chat/stream",
            headers={"Authorization": f"Bearer {PRO_KEY}"},
            json={"message": "Search for cooking videos", "conversation_id": _CONV_ID},
        )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")

        events = _parse_sse_events(resp.text)
        event_types = [e.get("event") for e in events]
        assert "text_delta" in event_types
        assert "done" in event_types

        done_events = [e for e in events if e.get("event") == "done"]
        assert len(done_events) >= 1
        done_data = done_events[-1]["data"]
        assert "finish_reason" in done_data
        assert "cost_usd" in done_data

    def test_stream_tool_events(self, client: TestClient, mock_orchestrator: MagicMock) -> None:
        """Orchestrator yields tool_call + tool_result -> body contains them."""

        async def _stream_with_tools(*args, **kwargs):
            yield ("tool_call", {"tool": "search_videos", "args": {"query": "test"}, "iteration": 0})
            yield ("tool_result", {"tool": "search_videos", "summary": "Found 5 results", "iteration": 0})
            yield ("text_delta", {"text": "I found 5 videos."})
            yield ("done", {"finish_reason": "complete", "text": "I found 5 videos.", "cost_usd": 0.003, "gemini_calls": 2, "actions_taken": ["search_videos"]})

        mock_orchestrator.stream_chat = _stream_with_tools

        resp = client.post(
            "/v1/agent/chat/stream",
            headers={"Authorization": f"Bearer {PRO_KEY}"},
            json={"message": "Search for test videos", "conversation_id": _CONV_ID},
        )
        assert resp.status_code == 200
        events = _parse_sse_events(resp.text)
        event_types = [e.get("event") for e in events]
        assert "tool_call" in event_types
        assert "tool_result" in event_types
        assert "done" in event_types

    def test_stream_event_ordering_and_terminal_done(self, client: TestClient, mock_orchestrator: MagicMock) -> None:
        """SSE order: tool_call -> tool_result -> text_delta -> done, with done last."""

        async def _ordered_stream(*args, **kwargs):
            yield ("tool_call", {"tool": "search_videos", "args": {"query": "test"}, "iteration": 0})
            yield ("tool_result", {"tool": "search_videos", "summary": "Found 5 results", "iteration": 0})
            yield ("text_delta", {"text": "I found 5 videos."})
            yield ("done", {"finish_reason": "complete", "text": "I found 5 videos.", "cost_usd": 0.003, "gemini_calls": 2, "actions_taken": ["search_videos"]})

        mock_orchestrator.stream_chat = _ordered_stream

        resp = client.post(
            "/v1/agent/chat/stream",
            headers={"Authorization": f"Bearer {PRO_KEY}"},
            json={"message": "Search for test videos", "conversation_id": _CONV_ID},
        )
        assert resp.status_code == 200
        events = _parse_sse_events(resp.text)
        event_types = [e.get("event") for e in events]
        assert event_types[-1] == "done"
        assert event_types.count("done") == 1
        assert event_types.index("tool_call") < event_types.index("tool_result")
        assert event_types.index("tool_result") < event_types.index("done")


# ── Error Handling — Stream ──────────────────────────────────


@pytest.mark.mock_required
class TestStreamErrors:
    def test_stream_error_yields_error_event(self, client: TestClient, mock_orchestrator: MagicMock) -> None:
        """Exception during streaming -> error + done events."""

        async def _stream_with_error(*args, **kwargs):
            yield ("text_delta", {"text": "Starting..."})
            raise RuntimeError("Something broke")

        mock_orchestrator.stream_chat = _stream_with_error

        resp = client.post(
            "/v1/agent/chat/stream",
            headers={"Authorization": f"Bearer {PRO_KEY}"},
            json={"message": "hello", "conversation_id": _CONV_ID},
        )
        assert resp.status_code == 200  # SSE always returns 200 at start
        events = _parse_sse_events(resp.text)
        event_types = [e.get("event") for e in events]
        assert "error" in event_types
        assert "done" in event_types
        # Verify error event doesn't leak internal details
        error_events = [e for e in events if e.get("event") == "error"]
        if error_events:
            assert "Something broke" not in json.dumps(error_events[0].get("data", {}))

    def test_stream_error_payload_is_sanitized(self, client: TestClient, mock_orchestrator: MagicMock) -> None:
        """Even orchestrator-provided error payloads should not leak internals."""

        async def _stream_with_leaky_error(*args, **kwargs):
            yield ("error", {"message": "DB DSN postgres://user:SECRET_DB_PASSWORD@host/db", "recoverable": False})
            yield ("done", {"finish_reason": "error"})

        mock_orchestrator.stream_chat = _stream_with_leaky_error

        resp = client.post(
            "/v1/agent/chat/stream",
            headers={"Authorization": f"Bearer {PRO_KEY}"},
            json={"message": "hello", "conversation_id": _CONV_ID},
        )
        assert resp.status_code == 200
        events = _parse_sse_events(resp.text)
        error_events = [e for e in events if e.get("event") == "error"]
        assert len(error_events) == 1
        error_payload = error_events[0].get("data", {})
        assert error_payload.get("message") == "Agent encountered an error"
        assert "SECRET_DB_PASSWORD" not in json.dumps(error_payload)

    def test_stream_immediate_failure_yields_error_then_done(self, client: TestClient, mock_orchestrator: MagicMock) -> None:
        """When stream crashes immediately, SSE still guarantees error + done in order."""

        async def _stream_with_immediate_error(*args, **kwargs):
            raise RuntimeError("hard failure")
            yield  # pragma: no cover

        mock_orchestrator.stream_chat = _stream_with_immediate_error

        resp = client.post(
            "/v1/agent/chat/stream",
            headers={"Authorization": f"Bearer {PRO_KEY}"},
            json={"message": "hello", "conversation_id": _CONV_ID},
        )
        assert resp.status_code == 200
        events = _parse_sse_events(resp.text)
        event_types = [e.get("event") for e in events]
        assert event_types[-1] == "done"
        assert "error" in event_types
        assert event_types.index("error") < event_types.index("done")

    def test_stream_unknown_event_type_is_sanitized(self, client: TestClient, mock_orchestrator: MagicMock) -> None:
        """Unexpected event names from orchestrator should be converted to sanitized error events."""

        async def _stream_with_unknown_event(*args, **kwargs):
            yield ("tool_result_v2", {"debug": "SHOULD_NOT_REACH_CLIENT"})
            yield ("done", {"finish_reason": "complete"})

        mock_orchestrator.stream_chat = _stream_with_unknown_event

        resp = client.post(
            "/v1/agent/chat/stream",
            headers={"Authorization": f"Bearer {PRO_KEY}"},
            json={"message": "hello", "conversation_id": _CONV_ID},
        )
        assert resp.status_code == 200
        events = _parse_sse_events(resp.text)
        event_types = [e.get("event") for e in events]
        assert "tool_result_v2" not in event_types
        assert "error" in event_types
        error_payload = [e for e in events if e.get("event") == "error"][0]["data"]
        assert error_payload.get("message") == "Agent encountered an error"
        assert "SHOULD_NOT_REACH_CLIENT" not in json.dumps(error_payload)


@pytest.mark.mock_required
class TestStreamDisconnect:
    @pytest.mark.asyncio
    async def test_stream_disconnect_sets_cancel_event(self, client: TestClient, mock_orchestrator: MagicMock) -> None:
        """Client disconnect during SSE should cancel work and not hang the server."""
        cancel_ref: asyncio.Event | None = None

        async def _slow_stream(*args, **kwargs):
            nonlocal cancel_ref
            cancel_ref = kwargs.get("cancel_event")
            yield ("text_delta", {"text": "hello"})
            # Simulate long-running downstream work (Gemini/tool call).
            await asyncio.sleep(60)
            yield ("done", {"finish_reason": "complete"})  # pragma: no cover

        mock_orchestrator.stream_chat = _slow_stream

        app = client.app

        body = json.dumps({"message": "hello", "conversation_id": _CONV_ID}).encode()
        headers = [
            (b"authorization", f"Bearer {PRO_KEY}".encode()),
            (b"content-type", b"application/json"),
            (b"accept", b"text/event-stream"),
        ]

        first_body_sent = asyncio.Event()
        receive_queue: asyncio.Queue[dict] = asyncio.Queue()
        await receive_queue.put({"type": "http.request", "body": body, "more_body": False})

        async def _send_disconnect_after_first_chunk() -> None:
            await first_body_sent.wait()
            await receive_queue.put({"type": "http.disconnect"})

        disconnect_task = asyncio.create_task(_send_disconnect_after_first_chunk())

        async def receive() -> dict:
            return await receive_queue.get()

        sent_messages: list[dict] = []

        async def send(message: dict) -> None:
            sent_messages.append(message)
            if message.get("type") == "http.response.body" and message.get("body"):
                first_body_sent.set()

        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/v1/agent/chat/stream",
            "raw_path": b"/v1/agent/chat/stream",
            "query_string": b"",
            "headers": headers,
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
        }

        try:
            await asyncio.wait_for(app(scope, receive, send), timeout=2.0)
        finally:
            disconnect_task.cancel()
            with suppress(asyncio.CancelledError):
                await disconnect_task

        assert cancel_ref is not None
        assert cancel_ref.is_set()
        assert any(m.get("type") == "http.response.start" for m in sent_messages)
        assert any(m.get("type") == "http.response.body" and m.get("body") for m in sent_messages)


# ── PR-034: conversation_id Required Tests ──────────────────


@pytest.mark.mock_required
class TestConversationIdRequired:
    """conversation_id is now required — missing → 422."""

    def test_chat_without_conversation_id_returns_422(self, client: TestClient) -> None:
        """POST /v1/agent/chat without conversation_id → 422."""
        resp = client.post(
            "/v1/agent/chat",
            headers={"Authorization": f"Bearer {PRO_KEY}"},
            json={"message": "hello"},
        )
        assert resp.status_code == 422

    def test_stream_without_conversation_id_returns_422(self, client: TestClient) -> None:
        """POST /v1/agent/chat/stream without conversation_id → 422."""
        resp = client.post(
            "/v1/agent/chat/stream",
            headers={"Authorization": f"Bearer {PRO_KEY}"},
            json={"message": "hello"},
        )
        assert resp.status_code == 422

    def test_chat_with_conversation_id_succeeds(self, client: TestClient) -> None:
        """POST /v1/agent/chat with conversation_id → 200."""
        resp = client.post(
            "/v1/agent/chat",
            headers={"Authorization": f"Bearer {PRO_KEY}"},
            json={"message": "hello", "conversation_id": str(uuid4())},
        )
        assert resp.status_code == 200

    def test_stream_with_conversation_id_succeeds(self, client: TestClient) -> None:
        """POST /v1/agent/chat/stream with conversation_id → 200."""
        resp = client.post(
            "/v1/agent/chat/stream",
            headers={"Authorization": f"Bearer {PRO_KEY}"},
            json={"message": "hello", "conversation_id": str(uuid4())},
        )
        assert resp.status_code == 200
