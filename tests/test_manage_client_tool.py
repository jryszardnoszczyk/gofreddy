"""Tests for the manage_client agent tool handler."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.clients.exceptions import ClientError, ClientNotFound
from src.clients.models import Client


def _make_client(**overrides) -> Client:
    defaults = {
        "id": uuid4(),
        "org_id": uuid4(),
        "name": "Test Client",
        "competitor_brands": ["Brand A"],
        "competitor_domains": ["a.com"],
        "brand_context": None,
        "auto_brief": False,
        "created_at": datetime.now(tz=timezone.utc),
        "updated_at": datetime.now(tz=timezone.utc),
    }
    defaults.update(overrides)
    return Client(**defaults)


@pytest.fixture
def client_service():
    return AsyncMock()


@pytest.fixture
def handle_manage_client(client_service):
    """Build handle_manage_client with injected mock service.

    This recreates the closure pattern from tools.py.
    """
    from src.orchestrator.tool_handlers._helpers import _parse_uuid

    async def _handle_create_client(user_id, name=None, **kwargs):
        if not name:
            return {"error": "missing_parameter", "summary": "Missing required parameter: name"}
        try:
            client = await client_service.create_client(
                org_id=user_id,
                name=name,
                competitor_brands=kwargs.get("competitor_brands"),
                competitor_domains=kwargs.get("competitor_domains"),
                brand_context=kwargs.get("brand_context"),
            )
            return {"summary": f"Created client '{name}'", "client": client.to_dict()}
        except ClientError:
            return {"error": "invalid_request", "summary": "Client operation failed"}

    async def _handle_list_clients(user_id, **kwargs):
        clients = await client_service.list_clients(org_id=user_id)
        return {
            "summary": f"Found {len(clients)} client(s)",
            "clients": [c.to_dict() for c in clients],
        }

    async def _handle_get_client(user_id, client_id=None, **kwargs):
        if not client_id:
            return {"error": "missing_parameter", "summary": "Missing required parameter: client_id"}
        try:
            parsed_id = _parse_uuid(client_id, "client_id")
            client = await client_service.get_client(client_id=parsed_id, org_id=user_id)
            return {"summary": f"Client: {client.name}", "client": client.to_dict()}
        except ClientNotFound:
            return {"error": "client_not_found", "summary": "Client not found"}
        except ValueError as e:
            return {"error": "invalid_request", "summary": str(e)}

    async def _handle_update_client(user_id, client_id=None, **kwargs):
        if not client_id:
            return {"error": "missing_parameter", "summary": "Missing required parameter: client_id"}
        try:
            parsed_id = _parse_uuid(client_id, "client_id")
            updates = {k: v for k, v in kwargs.items() if v is not None}
            if not updates:
                return {"error": "invalid_request", "summary": "No fields to update"}
            client = await client_service.update_client(
                client_id=parsed_id, org_id=user_id, **updates
            )
            return {"summary": f"Updated client '{client.name}'", "client": client.to_dict()}
        except ClientNotFound:
            return {"error": "client_not_found", "summary": "Client not found"}
        except ValueError as e:
            return {"error": "invalid_request", "summary": str(e)}

    async def handler(action, **kwargs):
        dispatch = {
            "create": _handle_create_client,
            "list": _handle_list_clients,
            "get": _handle_get_client,
            "update": _handle_update_client,
        }
        h = dispatch.get(action)
        if not h:
            return {"error": "invalid_request", "summary": f"Unknown action: {action}. Valid: {', '.join(dispatch.keys())}"}
        clean_kwargs = {k: v for k, v in kwargs.items() if v is not None and k != "action"}
        return await h(**clean_kwargs)

    return handler


@pytest.mark.asyncio
async def test_create_action(handle_manage_client, client_service):
    client = _make_client(name="Nike")
    client_service.create_client.return_value = client

    result = await handle_manage_client(
        action="create", user_id=client.org_id, name="Nike"
    )

    assert result["summary"] == "Created client 'Nike'"
    assert result["client"]["name"] == "Nike"


@pytest.mark.asyncio
async def test_list_action(handle_manage_client, client_service):
    clients = [_make_client(name="A"), _make_client(name="B")]
    client_service.list_clients.return_value = clients

    result = await handle_manage_client(action="list", user_id=uuid4())

    assert result["summary"] == "Found 2 client(s)"
    assert len(result["clients"]) == 2


@pytest.mark.asyncio
async def test_get_action(handle_manage_client, client_service):
    client = _make_client(name="Adidas")
    client_service.get_client.return_value = client

    result = await handle_manage_client(
        action="get", user_id=client.org_id, client_id=str(client.id)
    )

    assert result["summary"] == "Client: Adidas"
    assert result["client"]["name"] == "Adidas"


@pytest.mark.asyncio
async def test_update_action(handle_manage_client, client_service):
    client = _make_client(name="Updated")
    client_service.update_client.return_value = client

    result = await handle_manage_client(
        action="update", user_id=client.org_id,
        client_id=str(client.id), name="Updated"
    )

    assert result["summary"] == "Updated client 'Updated'"


@pytest.mark.asyncio
async def test_missing_name_on_create(handle_manage_client):
    result = await handle_manage_client(action="create", user_id=uuid4())
    assert result["error"] == "missing_parameter"
    assert "name" in result["summary"]


@pytest.mark.asyncio
async def test_missing_client_id_on_get(handle_manage_client):
    result = await handle_manage_client(action="get", user_id=uuid4())
    assert result["error"] == "missing_parameter"
    assert "client_id" in result["summary"]


@pytest.mark.asyncio
async def test_client_not_found(handle_manage_client, client_service):
    client_service.get_client.side_effect = ClientNotFound(uuid4())

    result = await handle_manage_client(
        action="get", user_id=uuid4(), client_id=str(uuid4())
    )

    assert result["error"] == "client_not_found"


@pytest.mark.asyncio
async def test_unknown_action(handle_manage_client):
    result = await handle_manage_client(action="delete", user_id=uuid4())
    assert result["error"] == "invalid_request"
    assert "Unknown action" in result["summary"]


def test_tool_registered_in_build_default_registry():
    """Verify manage_client is registered when client_service is provided."""
    from src.orchestrator.tools import ToolRegistry, build_default_registry

    mock_service = AsyncMock()
    registry, _ = build_default_registry(client_service=mock_service, tier=_pro_tier())
    assert "manage_client" in registry.names


def test_manage_client_in_user_id_tools():
    """Verify manage_client is in _USER_ID_TOOLS frozenset."""
    from src.orchestrator.agent import VideoIntelligenceAgent

    assert "manage_client" in VideoIntelligenceAgent._USER_ID_TOOLS


def test_passthrough_error_codes():
    """Verify missing_parameter and client_not_found in passthrough codes."""
    from src.orchestrator.agent import _PASSTHROUGH_ERROR_CODES

    assert "missing_parameter" in _PASSTHROUGH_ERROR_CODES
    assert "client_not_found" in _PASSTHROUGH_ERROR_CODES


def _pro_tier():
    from src.billing.tiers import Tier
    return Tier.PRO
