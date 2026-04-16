"""Live E2E tests for agent HTTP endpoints.

These tests start the real FastAPI app lifespan (DB, Gemini, tools) and hit:
  - POST /v1/agent/chat
  - POST /v1/agent/chat/stream (SSE)

They seed real billing rows (users/api_keys/subscriptions) so auth + tier gate
exercise the production stack end-to-end.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio

from src.api.main import create_app
from src.api.rate_limit import limiter

pytestmark = pytest.mark.live_api


def _parse_sse_events(body: str) -> list[dict]:
    """Parse SSE body text into list of {event, data} dicts."""
    events: list[dict] = []
    current: dict = {}
    for raw_line in body.split("\n"):
        line = raw_line.strip()
        if not line or line.startswith(":"):
            # Blank line = event separator; comments = keepalive pings.
            if not line and current:
                events.append(current)
                current = {}
            continue
        if line.startswith("event:"):
            current["event"] = line[len("event:"):].strip()
            continue
        if line.startswith("data:"):
            raw = line[len("data:"):].strip()
            try:
                current["data"] = json.loads(raw)
            except json.JSONDecodeError:
                current["data"] = raw
            continue
    if current:
        events.append(current)
    return events


def _month_window(now: datetime) -> tuple[datetime, datetime]:
    period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # Next month
    next_month = (period_start.replace(day=28) + timedelta(days=4)).replace(day=1)
    return period_start, next_month


@pytest_asyncio.fixture(scope="module")
async def live_app():
    app = create_app()
    limiter.enabled = False
    async with app.router.lifespan_context(app):
        yield app
    limiter.enabled = True


@pytest_asyncio.fixture
async def live_client(live_app):
    transport = httpx.ASGITransport(app=live_app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def pro_api_key(live_app):
    """Create a Pro-tier API key in the real DB."""
    raw_key = f"vi_test_{uuid4().hex[:16]}"
    user_id = uuid4()
    email = f"e2e-pro-{user_id.hex[:8]}@example.com"

    key_id = uuid4()
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:12]

    sub_id = uuid4()
    now = datetime.now(timezone.utc)
    period_start, period_end = _month_window(now)

    async with live_app.state.db_pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO users (id, email, stripe_customer_id) VALUES ($1, $2, $3)",
            user_id, email, None,
        )
        await conn.execute(
            "INSERT INTO api_keys (id, user_id, key_hash, key_prefix, name) VALUES ($1, $2, $3, $4, $5)",
            key_id, user_id, key_hash, key_prefix, "e2e-pro",
        )
        await conn.execute(
            """INSERT INTO subscriptions
               (id, user_id, stripe_subscription_id, stripe_price_id, tier, status,
                current_period_start, current_period_end, cancel_at_period_end)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
            sub_id,
            user_id,
            f"sub_{uuid4().hex[:12]}",
            "price_test",
            "pro",
            "active",
            period_start,
            period_end,
            False,
        )

    try:
        yield raw_key
    finally:
        async with live_app.state.db_pool.acquire() as conn:
            await conn.execute("DELETE FROM subscriptions WHERE user_id = $1", user_id)
            await conn.execute("DELETE FROM usage_periods WHERE user_id = $1", user_id)
            await conn.execute("DELETE FROM api_keys WHERE user_id = $1", user_id)
            await conn.execute("DELETE FROM users WHERE id = $1", user_id)


@pytest_asyncio.fixture
async def free_api_key(live_app):
    """Create a Free-tier API key (no subscription)."""
    raw_key = f"vi_test_{uuid4().hex[:16]}"
    user_id = uuid4()
    email = f"e2e-free-{user_id.hex[:8]}@example.com"

    key_id = uuid4()
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:12]

    async with live_app.state.db_pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO users (id, email, stripe_customer_id) VALUES ($1, $2, $3)",
            user_id, email, None,
        )
        await conn.execute(
            "INSERT INTO api_keys (id, user_id, key_hash, key_prefix, name) VALUES ($1, $2, $3, $4, $5)",
            key_id, user_id, key_hash, key_prefix, "e2e-free",
        )

    try:
        yield raw_key
    finally:
        async with live_app.state.db_pool.acquire() as conn:
            await conn.execute("DELETE FROM usage_periods WHERE user_id = $1", user_id)
            await conn.execute("DELETE FROM api_keys WHERE user_id = $1", user_id)
            await conn.execute("DELETE FROM users WHERE id = $1", user_id)


@pytest.mark.db
class TestAgentTierGateLive:
    async def test_chat_free_tier_forbidden(self, live_client, free_api_key) -> None:
        resp = await live_client.post(
            "/v1/agent/chat",
            headers={"Authorization": f"Bearer {free_api_key}"},
            json={"message": "hello"},
        )
        assert resp.status_code == 403
        body = resp.json()
        assert body["error"]["code"] == "tier_required"

    async def test_stream_free_tier_forbidden(self, live_client, free_api_key) -> None:
        resp = await live_client.post(
            "/v1/agent/chat/stream",
            headers={"Authorization": f"Bearer {free_api_key}"},
            json={"message": "hello"},
        )
        assert resp.status_code == 403
        body = resp.json()
        assert body["error"]["code"] == "tier_required"


@pytest.mark.gemini
@pytest.mark.external_api
@pytest.mark.db
@pytest.mark.slow
class TestAgentEndpointsLive:
    async def test_chat_success_real_agent(self, live_client, pro_api_key) -> None:
        resp = await live_client.post(
            "/v1/agent/chat",
            headers={"Authorization": f"Bearer {pro_api_key}"},
            json={"message": "Find 1 fitness video on TikTok and include the video_id in your answer."},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["text"]
        assert body["gemini_calls"] >= 1
        assert isinstance(body.get("tool_results"), list)
        assert any(tr.get("tool") == "search_videos" for tr in body["tool_results"])

    async def test_stream_sse_has_tool_events_and_done(self, live_client, pro_api_key) -> None:
        resp = await live_client.post(
            "/v1/agent/chat/stream",
            headers={"Authorization": f"Bearer {pro_api_key}"},
            json={"message": "Search TikTok for 1 fitness video. Stream tool calls/results and finish with a short summary."},
        )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")

        events = _parse_sse_events(resp.text)
        event_types = [e.get("event") for e in events]

        assert event_types[-1] == "done"
        assert event_types.count("done") == 1
        assert "tool_call" in event_types
        assert "tool_result" in event_types
        assert event_types.index("tool_call") < event_types.index("tool_result")

        tool_calls = [e for e in events if e.get("event") == "tool_call"]
        assert tool_calls[0]["data"]["tool"] == "search_videos"
        assert "args" in tool_calls[0]["data"]

        tool_results = [e for e in events if e.get("event") == "tool_result"]
        assert tool_results[0]["data"]["tool"] == "search_videos"

        done = [e for e in events if e.get("event") == "done"][-1]["data"]
        assert "finish_reason" in done
        assert "cost_usd" in done

        # Basic leakage guard for user-facing SSE body.
        assert "Traceback" not in resp.text
        assert "postgres://" not in resp.text
