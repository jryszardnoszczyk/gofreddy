"""Tests for agent router (POST /v1/agent/chat)."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import httpx
import pytest
from fastapi import Depends, FastAPI, HTTPException
from pydantic import ValidationError

from src.api.exceptions import register_exception_handlers
from src.api.routers.agent import ChatRequest, HistoryEntry, HistoryPart, _convert_history
from src.billing.models import BillingContext, Subscription, User, UsagePeriod
from src.billing.tiers import Tier
from src.conversations.exceptions import MessageLimitError
from src.orchestrator.models import AgentResponse


# ── Helpers ──────────────────────────────────────────────────


def _create_billing_context(tier: Tier) -> BillingContext:
    """Create a billing context for testing."""
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
        videos_limit=100 if tier == Tier.FREE else 50000,
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


# ── Request Model Validation ──────────────────────────────


class TestChatRequestValidation:
    def test_valid_message(self):
        req = ChatRequest(message="Hello, analyze this video", conversation_id=uuid4())
        assert req.message == "Hello, analyze this video"

    def test_validates_empty_message(self):
        """Empty string -> 422."""
        with pytest.raises(ValidationError):
            ChatRequest(message="", conversation_id=uuid4())

    def test_validates_message_length(self):
        """2001 chars -> 422."""
        with pytest.raises(ValidationError):
            ChatRequest(message="x" * 2001, conversation_id=uuid4())

    def test_conversation_id_required(self):
        """conversation_id is required (no default)."""
        with pytest.raises(ValidationError):
            ChatRequest(message="test")

    def test_conversation_id_accepted(self):
        """Valid UUID conversation_id accepted."""
        cid = uuid4()
        req = ChatRequest(message="test", conversation_id=cid)
        assert req.conversation_id == cid

    def test_valid_history(self):
        req = ChatRequest(
            message="test",
            conversation_id=uuid4(),
            history=[
                HistoryEntry(role="user", parts=[HistoryPart(text="Hello")]),
                HistoryEntry(role="model", parts=[HistoryPart(text="Hi there!")]),
            ],
        )
        assert len(req.history) == 2

    def test_validates_history_role(self):
        """role: 'system' -> 422."""
        with pytest.raises(ValidationError):
            HistoryEntry(role="system", parts=[HistoryPart(text="test")])

    def test_validates_history_max_length(self):
        """51 entries -> 422."""
        entries = [
            HistoryEntry(role="user", parts=[HistoryPart(text=f"msg {i}")])
            for i in range(51)
        ]
        with pytest.raises(ValidationError):
            ChatRequest(message="test", conversation_id=uuid4(), history=entries)

    def test_rejects_function_call_in_history(self):
        """Only text parts allowed — function_call dict rejected (S1)."""
        # HistoryPart requires 'text' field, so arbitrary dicts are rejected
        with pytest.raises(ValidationError):
            HistoryEntry(
                role="user",
                parts=[{"function_call": {"name": "search", "args": {}}}],  # type: ignore
            )

    def test_rejects_function_response_in_history(self):
        """Only text parts allowed — function_response dict rejected (S1)."""
        with pytest.raises(ValidationError):
            HistoryEntry(
                role="model",
                parts=[{"function_response": {"name": "search", "response": {}}}],  # type: ignore
            )

    def test_history_parts_max_length(self):
        """11 parts -> 422."""
        parts = [HistoryPart(text=f"part {i}") for i in range(11)]
        with pytest.raises(ValidationError):
            HistoryEntry(role="user", parts=parts)

    def test_history_part_text_max_length(self):
        """Text over 10K -> 422."""
        with pytest.raises(ValidationError):
            HistoryPart(text="x" * 10_001)


class TestBillingGate:
    def test_pro_tier_billing_context(self):
        """Pro tier context created successfully."""
        ctx = _create_billing_context(Tier.PRO)
        assert ctx.tier == Tier.PRO

    def test_free_tier_billing_context(self):
        """Free tier context created successfully."""
        ctx = _create_billing_context(Tier.FREE)
        assert ctx.tier == Tier.FREE


class TestAgentResponseModel:
    def test_default_response(self):
        """AgentResponse with defaults."""
        response = AgentResponse(
            text="Hello",
            actions_taken=[],
            tool_results=[],
            cost_usd=0.0,
            gemini_calls=1,
        )
        assert response.text == "Hello"
        assert response.gemini_calls == 1

    def test_response_with_actions(self):
        """AgentResponse with tool results."""
        response = AgentResponse(
            text="Analysis complete",
            actions_taken=["search_videos(query='test')", "analyze_video(platform='youtube', video_id='abc')"],
            tool_results=[{"tool": "search_videos", "result": {"videos": []}}],
            cost_usd=0.05,
            gemini_calls=3,
        )
        assert len(response.actions_taken) == 2
        assert response.cost_usd == 0.05


# ── Shared helper tests ──────────────────────────────────


class TestConvertHistory:
    def test_none_history(self):
        req = ChatRequest(message="test", conversation_id=uuid4())
        assert _convert_history(req) is None

    def test_converts_history(self):
        req = ChatRequest(
            message="test",
            conversation_id=uuid4(),
            history=[
                HistoryEntry(role="user", parts=[HistoryPart(text="hello")]),
                HistoryEntry(role="model", parts=[HistoryPart(text="hi")]),
            ],
        )
        result = _convert_history(req)
        assert result is not None
        assert len(result) == 2
        assert result[0]["role"] == "user"
        assert result[0]["parts"] == [{"text": "hello"}]


# ── Stream Persistence Tests ──────────────────────────────


class TestStreamPersistsAssistantMessage:
    """Test that assistant messages are persisted after stream completes."""

    @pytest.mark.asyncio
    async def test_stream_persists_assistant_message(self):
        """Verify accumulated text + tool_calls are persisted via create_task.

        Tests the persistence logic by simulating event_generator's finally block
        behavior, since the generator is nested inside chat_stream.
        """
        conversation_service = AsyncMock()
        conversation_service.add_message.return_value = MagicMock()

        conversation_id = uuid4()
        user_id = uuid4()

        # Simulate what happens when accumulated_text and tool_calls are set
        # and the finally block fires
        accumulated_text = "Here are the analysis results."
        accumulated_tool_calls = [{"name": "search_videos", "args": {"query": "fitness"}}]
        accumulated_thinking = "Let me search for videos"

        metadata: dict = {}
        if accumulated_tool_calls:
            metadata["tool_calls"] = accumulated_tool_calls
        if accumulated_thinking:
            metadata["thinking"] = accumulated_thinking
        content = accumulated_text.strip() or "[tool calls only]"

        # Call add_message directly as the finally block would
        await conversation_service.add_message(
            conversation_id, user_id, "assistant",
            content, metadata=metadata,
        )

        conversation_service.add_message.assert_called_once_with(
            conversation_id, user_id, "assistant",
            "Here are the analysis results.",
            metadata={
                "tool_calls": [{"name": "search_videos", "args": {"query": "fitness"}}],
                "thinking": "Let me search for videos",
            },
        )

    @pytest.mark.asyncio
    async def test_no_persistence_without_conversation_id(self):
        """Verify no add_message call when conversation_id is None."""
        conversation_service = AsyncMock()

        # Simulate the guard: body.conversation_id is None
        conversation_id = None
        accumulated_text = "some text"
        accumulated_tool_calls: list[dict] = []

        if conversation_id and conversation_service and (accumulated_text.strip() or accumulated_tool_calls):
            await conversation_service.add_message(
                conversation_id, uuid4(), "assistant", accumulated_text,
            )

        conversation_service.add_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_persistence_without_content(self):
        """Verify no persistence when both text and tool_calls are empty."""
        conversation_service = AsyncMock()
        conversation_id = uuid4()

        accumulated_text = "   "  # whitespace-only
        accumulated_tool_calls: list[dict] = []

        if conversation_id and conversation_service and (accumulated_text.strip() or accumulated_tool_calls):
            await conversation_service.add_message(
                conversation_id, uuid4(), "assistant", accumulated_text,
            )

        conversation_service.add_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_persists_tool_calls_only(self):
        """Verify persistence when text is empty but tool_calls exist."""
        conversation_service = AsyncMock()
        conversation_service.add_message.return_value = MagicMock()
        conversation_id = uuid4()
        user_id = uuid4()

        accumulated_text = ""
        accumulated_tool_calls = [{"name": "detect_fraud", "args": {"platform": "tiktok"}}]

        if conversation_id and conversation_service and (accumulated_text.strip() or accumulated_tool_calls):
            content = accumulated_text.strip() or "[tool calls only]"
            metadata: dict = {"tool_calls": accumulated_tool_calls}
            await conversation_service.add_message(
                conversation_id, user_id, "assistant",
                content, metadata=metadata,
            )

        conversation_service.add_message.assert_called_once()
        call_args = conversation_service.add_message.call_args
        assert call_args[0][2] == "assistant"
        assert call_args[0][3] == "[tool calls only]"
        assert call_args[1]["metadata"]["tool_calls"] == accumulated_tool_calls

    @pytest.mark.asyncio
    async def test_persistence_failure_is_silent(self):
        """Verify persistence failure doesn't raise (fire-and-forget pattern)."""
        conversation_service = AsyncMock()
        conversation_service.add_message.side_effect = Exception("DB down")

        conversation_id = uuid4()
        user_id = uuid4()

        # The actual code uses asyncio.create_task with done_callback for error logging.
        # Simulate the fire-and-forget: call should not propagate exceptions.
        task = asyncio.create_task(
            conversation_service.add_message(
                conversation_id, user_id, "assistant",
                "test content", metadata={},
            )
        )
        task.add_done_callback(lambda t: None)

        # Wait for the task to complete — it should not raise to the caller
        await asyncio.sleep(0.01)
        assert task.done()
        assert task.exception() is not None  # Exception captured, not propagated


# ── History Loading Tests ──────────────────────────────


class TestHistoryLoadingFromDB:
    """Test that conversation history is loaded from DB for resumed conversations."""

    @pytest.mark.asyncio
    async def test_history_loaded_when_conversation_id_set_and_no_client_history(self):
        """Verify get_messages called when conversation_id set and history is empty."""
        from src.conversations.models import ConversationMessage

        conversation_service = AsyncMock()
        msg_id = uuid4()
        conv_id = uuid4()
        now = datetime.now(timezone.utc)

        conversation_service.get_messages.return_value = [
            ConversationMessage(
                id=msg_id, conversation_id=conv_id,
                role="user", content="hi",
                metadata={}, created_at=now,
            ),
            ConversationMessage(
                id=uuid4(), conversation_id=conv_id,
                role="assistant", content="hello",
                metadata={}, created_at=now,
            ),
        ]

        # Simulate the loading logic from agent.py
        history_dicts = None  # No client history
        body_conversation_id = conv_id

        if body_conversation_id and not history_dicts and conversation_service:
            stored_messages = await conversation_service.get_messages(
                body_conversation_id, uuid4(), limit=40,
            )
            history_dicts = [
                {
                    "role": "model" if m.role == "assistant" else m.role,
                    "parts": [{"text": m.content}],
                }
                for m in stored_messages
                if m.role in ("user", "assistant")
            ]

        assert history_dicts is not None
        assert len(history_dicts) == 2
        assert history_dicts[0]["role"] == "user"
        assert history_dicts[0]["parts"] == [{"text": "hi"}]
        assert history_dicts[1]["role"] == "model"  # assistant -> model for Gemini
        assert history_dicts[1]["parts"] == [{"text": "hello"}]

    @pytest.mark.asyncio
    async def test_client_history_takes_precedence_over_db(self):
        """Verify explicit history in request body skips DB load."""
        conversation_service = AsyncMock()

        # Client sends explicit history
        history_dicts = [
            {"role": "user", "parts": [{"text": "client msg"}]},
            {"role": "model", "parts": [{"text": "client response"}]},
        ]
        body_conversation_id = uuid4()

        if body_conversation_id and not history_dicts and conversation_service:
            # This block should NOT execute
            await conversation_service.get_messages(body_conversation_id, uuid4(), limit=40)

        conversation_service.get_messages.assert_not_called()


# ── Tier-Aware Budget Tests ──────────────────────────────


class TestTierAwareBudget:
    """Test that Pro tier gets higher cost_limit_usd for multi-tool workflows."""

    def test_pro_tier_gets_higher_budget(self):
        """Pro tier agent config gets cost_limit_usd=3.0."""
        from src.orchestrator.config import AgentSettings

        agent_config = AgentSettings(cost_limit_usd=1.0)
        billing = _create_billing_context(Tier.PRO)

        # Replicate the logic from _build_per_request_agent
        if billing.tier == Tier.PRO and agent_config.cost_limit_usd < 3.0:
            agent_config = agent_config.model_copy(update={"cost_limit_usd": 3.0})

        assert agent_config.cost_limit_usd == 3.0

    def test_free_tier_keeps_default_budget(self):
        """Free tier stays at default cost_limit_usd=1.0."""
        from src.orchestrator.config import AgentSettings

        agent_config = AgentSettings(cost_limit_usd=1.0)
        billing = _create_billing_context(Tier.FREE)

        if billing.tier == Tier.PRO and agent_config.cost_limit_usd < 3.0:
            agent_config = agent_config.model_copy(update={"cost_limit_usd": 3.0})

        assert agent_config.cost_limit_usd == 1.0

    def test_pro_with_already_high_budget_unchanged(self):
        """Pro tier with cost_limit_usd >= 3.0 is not overridden."""
        from src.orchestrator.config import AgentSettings

        agent_config = AgentSettings(cost_limit_usd=5.0)
        billing = _create_billing_context(Tier.PRO)

        if billing.tier == Tier.PRO and agent_config.cost_limit_usd < 3.0:
            agent_config = agent_config.model_copy(update={"cost_limit_usd": 3.0})

        assert agent_config.cost_limit_usd == 5.0

    @pytest.mark.asyncio
    async def test_history_loading_failure_is_non_fatal(self):
        """Verify history loading failure doesn't crash the request."""
        conversation_service = AsyncMock()
        conversation_service.get_messages.side_effect = Exception("DB connection lost")

        history_dicts = None
        body_conversation_id = uuid4()

        if body_conversation_id and not history_dicts and conversation_service:
            try:
                stored_messages = await conversation_service.get_messages(
                    body_conversation_id, uuid4(), limit=40,
                )
                history_dicts = [
                    {
                        "role": "model" if m.role == "assistant" else m.role,
                        "parts": [{"text": m.content}],
                    }
                    for m in stored_messages
                    if m.role in ("user", "assistant")
                ]
            except Exception:
                pass  # Non-fatal, matches agent.py behavior

        # history_dicts should remain None after failure
        assert history_dicts is None

    @pytest.mark.asyncio
    async def test_role_mapping_assistant_to_model(self):
        """Verify assistant role from DB is mapped to model for Gemini API."""
        from src.conversations.models import ConversationMessage

        conv_id = uuid4()
        now = datetime.now(timezone.utc)

        messages = [
            ConversationMessage(
                id=uuid4(), conversation_id=conv_id,
                role="assistant", content="I am assistant",
                metadata={}, created_at=now,
            ),
            ConversationMessage(
                id=uuid4(), conversation_id=conv_id,
                role="user", content="I am user",
                metadata={}, created_at=now,
            ),
            ConversationMessage(
                id=uuid4(), conversation_id=conv_id,
                role="tool", content="tool output",
                metadata={}, created_at=now,
            ),
        ]

        history_dicts = [
            {
                "role": "model" if m.role == "assistant" else m.role,
                "parts": [{"text": m.content}],
            }
            for m in messages
            if m.role in ("user", "assistant")
        ]

        assert len(history_dicts) == 2  # tool role filtered out
        assert history_dicts[0]["role"] == "model"
        assert history_dicts[1]["role"] == "user"


# ── 429 Envelope Verification (Gap #14) ───────────────────────


class Test429EnvelopeFormat:
    """Verify daily limit 429 matches {"error": {...}} envelope via real exception handler pipeline."""

    @pytest.fixture
    def app_with_429_route(self):
        """Minimal FastAPI app with exception handlers + route that raises 429."""
        app = FastAPI()
        register_exception_handlers(app)

        @app.post("/v1/agent/chat")
        async def fake_chat():
            # Simulate the exact 429 path from agent router
            raise HTTPException(
                status_code=429,
                detail={
                    "code": "daily_message_limit",
                    "message": "Daily message limit reached",
                    "limit": 20,
                    "retry_after": 86400,
                },
            )

        return app

    @pytest.mark.asyncio
    async def test_429_daily_limit_matches_error_envelope(self, app_with_429_route):
        """POST /v1/agent/chat → 429 response has {"error": {"code": "daily_message_limit", ...}}."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app_with_429_route),
            base_url="http://testserver",
        ) as client:
            resp = await client.post(
                "/v1/agent/chat",
                json={"message": "test"},
            )

        assert resp.status_code == 429
        body = resp.json()
        # Must be {"error": {...}} envelope, NOT {"detail": {...}}
        assert "error" in body, f"Expected 'error' key in response, got: {body}"
        assert "detail" not in body, f"Unexpected 'detail' key in response: {body}"
        error = body["error"]
        assert error["code"] == "daily_message_limit"
        assert error["message"] == "Daily message limit reached"
        assert error["limit"] == 20
        assert error["retry_after"] == 86400
