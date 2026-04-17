"""Portal route tests — new module in gofreddy.

Covers:
  - /portal/<slug> HTML shell renders without auth (200, any slug)
  - /v1/portal/<slug>/summary requires auth (401 no token, 401 bad token)
  - /v1/portal/<slug>/summary returns 403 for non-members (no_membership code)
  - /v1/portal/<slug>/summary returns payload for members
"""
from __future__ import annotations

import httpx
import pytest


@pytest.mark.asyncio
async def test_portal_shell_renders_without_auth(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    """The HTML shell itself is unauthenticated — client-side JS handles session."""
    r = await api_client.get(f"/portal/{test_tenant['client_slug']}")
    assert r.status_code == 200
    assert "<!DOCTYPE html>" in r.text or "<html" in r.text
    # Should contain the slug somewhere (page personalization)
    assert test_tenant["client_slug"] in r.text


@pytest.mark.asyncio
async def test_portal_summary_requires_token(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    r = await api_client.get(f"/v1/portal/{test_tenant['client_slug']}/summary")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_portal_summary_rejects_invalid_token(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    r = await api_client.get(
        f"/v1/portal/{test_tenant['client_slug']}/summary",
        headers={"Authorization": "Bearer not-a-real-jwt"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_portal_summary_403_for_non_member(
    api_client: httpx.AsyncClient, test_tenant: dict, outsider: dict
) -> None:
    """Outsider has a valid token but no membership → 403, not 401."""
    r = await api_client.get(
        f"/v1/portal/{test_tenant['client_slug']}/summary",
        headers={"Authorization": f"Bearer {outsider['token']}"},
    )
    assert r.status_code == 403
    payload = r.json()
    assert payload["error"]["code"] == "no_membership"


@pytest.mark.asyncio
async def test_portal_summary_returns_payload_for_member(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    r = await api_client.get(
        f"/v1/portal/{test_tenant['client_slug']}/summary",
        headers={"Authorization": f"Bearer {test_tenant['token']}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["slug"] == test_tenant["client_slug"]
    assert data["role"] == "owner"
    assert data["email"] == test_tenant["email"]


@pytest.mark.asyncio
async def test_portal_summary_unknown_slug_is_403(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    """A slug the user has no membership on — whether it exists or not — is 403."""
    r = await api_client.get(
        "/v1/portal/ghost-does-not-exist/summary",
        headers={"Authorization": f"Bearer {test_tenant['token']}"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_health_is_public(api_client: httpx.AsyncClient) -> None:
    r = await api_client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
