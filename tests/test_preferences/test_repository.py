"""Tests for preferences repository methods on BillingRepository."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.billing.repository import BillingRepository
from src.common.gemini_models import GEMINI_PRO


@pytest.fixture
def mock_pool():
    pool = MagicMock()
    mock_conn = MagicMock()
    mock_conn.fetchrow = AsyncMock()
    mock_conn.execute = AsyncMock()
    pool.acquire = MagicMock()
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
    return pool, mock_conn


@pytest.fixture
def repo(mock_pool):
    pool, _ = mock_pool
    return BillingRepository(pool)


@pytest.mark.mock_required
class TestGetPreferences:
    @pytest.mark.asyncio
    async def test_returns_preferences_dict(self, repo, mock_pool):
        _, conn = mock_pool
        conn.fetchrow.return_value = {"preferences": {"agent_model": GEMINI_PRO}}
        result = await repo.get_preferences(uuid4())
        assert result == {"agent_model": GEMINI_PRO}

    @pytest.mark.asyncio
    async def test_returns_empty_dict_when_user_not_found(self, repo, mock_pool):
        _, conn = mock_pool
        conn.fetchrow.return_value = None
        result = await repo.get_preferences(uuid4())
        assert result == {}

    @pytest.mark.asyncio
    async def test_returns_empty_dict_when_preferences_null(self, repo, mock_pool):
        _, conn = mock_pool
        conn.fetchrow.return_value = {"preferences": None}
        result = await repo.get_preferences(uuid4())
        assert result == {}


@pytest.mark.mock_required
class TestUpdatePreferences:
    @pytest.mark.asyncio
    async def test_returns_updated_preferences(self, repo, mock_pool):
        _, conn = mock_pool
        updated = {"agent_model": GEMINI_PRO}
        conn.fetchrow.return_value = {"preferences": updated}
        result = await repo.update_preferences(uuid4(), updated)
        assert result == updated

    @pytest.mark.asyncio
    async def test_returns_empty_dict_when_user_not_found(self, repo, mock_pool):
        _, conn = mock_pool
        conn.fetchrow.return_value = None
        result = await repo.update_preferences(uuid4(), {"agent_model": GEMINI_PRO})
        assert result == {}
