"""Tests for ClientService."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import asyncpg
import pytest

from src.clients.exceptions import ClientError, ClientNotFound
from src.clients.models import Client
from src.clients.service import ClientService


def _make_client(**overrides) -> Client:
    defaults = {
        "id": uuid4(),
        "org_id": uuid4(),
        "name": "Test Client",
        "competitor_brands": ["Brand A", "Brand B"],
        "competitor_domains": ["a.com", "b.com"],
        "brand_context": "Test context",
        "auto_brief": False,
        "created_at": datetime.now(tz=timezone.utc),
        "updated_at": datetime.now(tz=timezone.utc),
    }
    defaults.update(overrides)
    return Client(**defaults)


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    repo._pool = MagicMock()
    return repo


@pytest.fixture
def service(mock_repo):
    return ClientService(repository=mock_repo)


@pytest.mark.asyncio
async def test_create_client_success(service, mock_repo):
    client = _make_client()
    mock_repo.create.return_value = client

    result = await service.create_client(
        org_id=client.org_id,
        name=client.name,
        competitor_brands=client.competitor_brands,
        competitor_domains=client.competitor_domains,
        brand_context=client.brand_context,
    )

    assert result == client
    mock_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_client_duplicate_name(service, mock_repo):
    mock_repo.create.side_effect = asyncpg.UniqueViolationError("")

    with pytest.raises(ClientError, match="already exists"):
        await service.create_client(
            org_id=uuid4(),
            name="Duplicate",
        )


@pytest.mark.asyncio
async def test_get_client_success(service, mock_repo):
    client = _make_client()
    mock_repo.get_by_id_and_org.return_value = client

    result = await service.get_client(
        client_id=client.id, org_id=client.org_id
    )

    assert result == client


@pytest.mark.asyncio
async def test_get_client_not_found(service, mock_repo):
    mock_repo.get_by_id_and_org.return_value = None
    cid = uuid4()

    with pytest.raises(ClientNotFound) as exc_info:
        await service.get_client(client_id=cid, org_id=uuid4())

    assert exc_info.value.client_id == cid


@pytest.mark.asyncio
async def test_get_client_wrong_org(service, mock_repo):
    """IDOR prevention: different org gets ClientNotFound."""
    mock_repo.get_by_id_and_org.return_value = None

    with pytest.raises(ClientNotFound):
        await service.get_client(client_id=uuid4(), org_id=uuid4())


@pytest.mark.asyncio
async def test_list_clients(service, mock_repo):
    clients = [_make_client(), _make_client()]
    mock_repo.list_by_org.return_value = clients

    result = await service.list_clients(org_id=uuid4())

    assert len(result) == 2


@pytest.mark.asyncio
async def test_update_client_propagates_competitors(service, mock_repo):
    """When competitor_brands is in updates, propagation should occur in transaction."""
    client = _make_client()
    mock_repo.get_by_id_and_org.return_value = client

    # Mock the pool.acquire() → conn and conn.transaction() context managers
    mock_conn = MagicMock()
    mock_txn_cm = MagicMock()
    mock_txn_cm.__aenter__ = AsyncMock(return_value=mock_txn_cm)
    mock_txn_cm.__aexit__ = AsyncMock(return_value=False)
    mock_conn.transaction.return_value = mock_txn_cm

    mock_acquire_cm = MagicMock()
    mock_acquire_cm.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_acquire_cm.__aexit__ = AsyncMock(return_value=False)
    mock_repo._pool.acquire.return_value = mock_acquire_cm

    updated_client = _make_client(competitor_brands=["New Brand"])
    mock_repo.update.return_value = updated_client
    mock_repo.propagate_to_monitors.return_value = 2

    result = await service.update_client(
        client_id=client.id,
        org_id=client.org_id,
        competitor_brands=["New Brand"],
    )

    assert result == updated_client
    mock_repo.propagate_to_monitors.assert_called_once()


@pytest.mark.asyncio
async def test_update_client_no_propagation(service, mock_repo):
    """Update without competitor_brands skips propagation."""
    client = _make_client()
    mock_repo.get_by_id_and_org.return_value = client
    updated_client = _make_client(name="New Name")
    mock_repo.update.return_value = updated_client

    result = await service.update_client(
        client_id=client.id,
        org_id=client.org_id,
        name="New Name",
    )

    assert result == updated_client
    mock_repo.propagate_to_monitors.assert_not_called()


@pytest.mark.asyncio
async def test_list_auto_brief_clients(service, mock_repo):
    auto_clients = [_make_client(auto_brief=True)]
    mock_repo.list_auto_brief.return_value = auto_clients

    result = await service.list_auto_brief_clients()

    assert len(result) == 1
    assert result[0].auto_brief is True
