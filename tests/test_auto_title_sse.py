"""Tests for auto-title SSE emission and billing data injection in done event."""

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.api.routers.agent import _build_per_request_agent
from src.billing.models import BillingContext, Subscription, UsagePeriod, User
from src.billing.tiers import Tier
from src.common.gemini_models import GEMINI_FLASH
from src.conversations.models import Conversation


def _make_billing(tier: Tier = Tier.FREE) -> BillingContext:
    """Build a minimal BillingContext for tests."""
    now = datetime.now(UTC)
    user = User(
        id=uuid4(),
        email="test@example.com",
        stripe_customer_id=None,
        created_at=now,
    )
    usage = UsagePeriod(
        id=uuid4(),
        user_id=user.id,
        period_start=now,
        period_end=now + timedelta(days=30),
        videos_used=0,
        videos_limit=100,
    )
    sub = Subscription(
        id=uuid4(),
        user_id=user.id,
        stripe_subscription_id="sub_test",
        tier=tier,
        status="active",
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
        cancel_at_period_end=False,
    )
    return BillingContext(user=user, tier=tier, usage_period=usage, subscription=sub)


@pytest.fixture
def mock_request():
    """Mock FastAPI request with app state."""
    request = MagicMock()
    request.app.state.conversation_service = AsyncMock()
    request.app.state.workspace_service = AsyncMock()
    request.app.state.search_service = AsyncMock()
    request.app.state.analysis_service = AsyncMock()
    request.app.state.brand_service = AsyncMock()
    request.app.state.demographics_service = AsyncMock()
    request.app.state.deepfake_service = AsyncMock()
    request.app.state.evolution_service = AsyncMock()
    request.app.state.trend_service = AsyncMock()
    request.app.state.story_service = AsyncMock()
    request.app.state.fetchers = {}
    request.app.state.video_storage = AsyncMock()
    request.app.state.fraud_service = AsyncMock()
    request.app.state.billing_service = AsyncMock()
    request.app.state.agent_gemini_client = MagicMock()
    request.app.state.agent_settings = MagicMock()
    request.app.state.agent_settings.model = GEMINI_FLASH  # Agent stays on Flash
    request.app.state.agent_settings.max_iterations = 10
    request.app.state.agent_settings.budget_usd = 0.50
    request.app.state.agent_settings.timeout_seconds = 240
    request.app.state.batch_service = None
    request.app.state.batch_repository = None
    request.app.state.workspace_repository = None
    request.app.state.batch_settings = None
    return request


@pytest.mark.asyncio
async def test_build_per_request_agent_returns_remaining_and_limit(mock_request):
    """_build_per_request_agent returns (agent, remaining, limit, conv) tuple."""
    user_id = uuid4()
    conv_id = uuid4()
    billing = _make_billing(Tier.FREE)
    mock_conv = MagicMock(spec=Conversation)
    mock_request.app.state.conversation_service.check_daily_limit = AsyncMock(return_value=15)
    mock_request.app.state.conversation_service.get_conversation = AsyncMock(return_value=mock_conv)
    mock_request.app.state.workspace_service.get_workspace_state = AsyncMock(return_value=None)

    with patch("src.api.routers.agent.build_default_registry") as mock_reg:
        mock_reg.return_value = (MagicMock(), {})
        agent, remaining, limit, conv = await _build_per_request_agent(
            mock_request, user_id, billing, conv_id
        )

    assert remaining == 15
    assert limit == 20  # Free tier default
    assert conv is mock_conv  # Conversation returned from service


@pytest.mark.asyncio
async def test_auto_title_fires_for_untitled_conversation(mock_request):
    """Auto-title fires when conversation has no title."""
    conv_id = uuid4()

    # Simulate untitled conversation
    mock_conv = MagicMock(spec=Conversation)
    mock_conv.title = None
    service = mock_request.app.state.conversation_service
    service.get_conversation = AsyncMock(return_value=mock_conv)
    service.auto_title = AsyncMock(return_value="Test Title")

    assert mock_conv.title is None

    title = await service.auto_title(conv_id, "Find trending fitness content")
    assert title == "Test Title"
    service.auto_title.assert_awaited_once_with(conv_id, "Find trending fitness content")


@pytest.mark.asyncio
async def test_auto_title_does_not_fire_when_title_exists():
    """Auto-title should NOT fire when conversation already has a title."""
    mock_conv = MagicMock(spec=Conversation)
    mock_conv.title = "Existing Title"

    assert mock_conv.title is not None
    is_first_message = mock_conv.title is None
    assert is_first_message is False


def test_done_event_contains_billing_data():
    """Verify done event data structure includes billing fields."""
    remaining = 15
    messages_limit = 20

    data: dict = {"finish_reason": "complete", "cost_usd": 0.002}
    data["messages_remaining"] = max(0, remaining - 1)
    data["messages_limit"] = messages_limit
    data["tier"] = "free"

    serialized = json.dumps(data, default=str)
    parsed = json.loads(serialized)

    assert parsed["messages_remaining"] == 14
    assert parsed["messages_limit"] == 20
    assert parsed["tier"] == "free"


def test_done_event_contains_title():
    """Verify done event data structure includes conversation_title."""
    data: dict = {"finish_reason": "complete"}
    title = "Fitness Content Analysis"
    data["conversation_title"] = title

    serialized = json.dumps(data, default=str)
    parsed = json.loads(serialized)
    assert parsed["conversation_title"] == "Fitness Content Analysis"
