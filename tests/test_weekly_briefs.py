"""Tests for weekly brief scheduling endpoint."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, PropertyMock
from uuid import uuid4

import pytest

from src.competitive.models import CompetitiveBrief

# Stable module path for patching time.monotonic inside the endpoint
_INTERNAL_TIME = "src.api.routers.internal.time"


def _make_client(**kw):
    c = MagicMock()
    c.id = kw.get("id", uuid4())
    c.org_id = kw.get("org_id", uuid4())
    c.name = kw.get("name", "Auto Brief Client")
    return c


def _make_brief(**kw) -> CompetitiveBrief:
    return CompetitiveBrief(
        id=kw.get("id", uuid4()),
        client_id=kw.get("client_id", uuid4()),
        org_id=kw.get("org_id", uuid4()),
        date_range="7d",
        schema_version=1,
        brief_data={"sections": []},
        idempotency_key=kw.get("idempotency_key", None),
        created_at=datetime.now(timezone.utc),
    )


def _make_request(brief_generator=None, client_service=None) -> MagicMock:
    """Create a mock Request with app.state attributes."""
    request = MagicMock()
    state = MagicMock()
    state.brief_generator = brief_generator
    state.client_service = client_service
    request.app.state = state
    return request


@pytest.mark.asyncio
async def test_weekly_briefs_processes_clients():
    """Weekly brief endpoint processes all auto_brief clients."""
    from src.api.routers.internal import run_weekly_briefs

    clients = [_make_client(), _make_client()]
    brief = _make_brief()

    brief_gen = AsyncMock()
    brief_gen.generate.return_value = brief

    client_service = AsyncMock()
    client_service.list_auto_brief_clients.return_value = clients

    request = _make_request(brief_generator=brief_gen, client_service=client_service)

    result = await run_weekly_briefs(request)

    assert result.processed == 2
    assert result.succeeded == 2
    assert result.failed == 0


@pytest.mark.asyncio
async def test_weekly_briefs_one_failure_continues():
    """One client failure doesn't block others."""
    from src.api.routers.internal import run_weekly_briefs

    clients = [_make_client(), _make_client()]
    brief = _make_brief()

    brief_gen = AsyncMock()
    brief_gen.generate.side_effect = [RuntimeError("fail"), brief]

    client_service = AsyncMock()
    client_service.list_auto_brief_clients.return_value = clients

    request = _make_request(brief_generator=brief_gen, client_service=client_service)

    result = await run_weekly_briefs(request)

    assert result.processed == 2
    assert result.succeeded == 1
    assert result.failed == 1


@pytest.mark.asyncio
async def test_weekly_briefs_not_configured():
    """Returns empty when services not configured."""
    from src.api.routers.internal import run_weekly_briefs

    request = _make_request(brief_generator=None, client_service=None)

    result = await run_weekly_briefs(request)

    assert result.processed == 0


@pytest.mark.asyncio
async def test_weekly_briefs_deadline_skips_remaining_clients():
    """Clients beyond the 200s deadline are skipped, not crashed."""
    from unittest.mock import patch

    from src.api.routers.internal import run_weekly_briefs

    clients = [_make_client(), _make_client(), _make_client()]
    brief = _make_brief()

    brief_gen = AsyncMock()
    brief_gen.generate.return_value = brief

    client_service = AsyncMock()
    client_service.list_auto_brief_clients.return_value = clients

    request = _make_request(brief_generator=brief_gen, client_service=client_service)

    # First monotonic() call sets the deadline (returns 1000, so deadline = 1200).
    # Second call (first iteration check) returns 1001 — under deadline, processes client 1.
    # Third call (second iteration check) returns 1201 — over deadline, skips clients 2 and 3.
    monotonic_values = iter([1000, 1001, 1201, 1201])
    with patch(_INTERNAL_TIME) as mock_time:
        mock_time.monotonic.side_effect = lambda: next(monotonic_values)
        result = await run_weekly_briefs(request)

    assert result.processed == 3
    assert result.succeeded == 1
    assert result.failed == 2

    # Verify the skipped clients have the correct status
    statuses = [r["status"] for r in result.results]
    assert statuses == ["ok", "skipped_deadline", "skipped_deadline"]

    # Only one generate() call should have been made (the first client)
    assert brief_gen.generate.call_count == 1
