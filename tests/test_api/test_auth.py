"""Auth router tests — adapted from freddy/tests/test_api/test_auth_router.py.

Ported tests:
  - test_get_me_requires_auth              (freddy: same)
  - test_get_me_returns_client_slugs       (freddy: test_get_me_with_auth_returns_profile_shape; response schema differs)
  - test_logout_requires_auth              (freddy: same)
  - test_logout_with_auth_returns_204      (freddy: same)

New gofreddy-specific tests:
  - test_me_empty_client_slugs_for_non_member
  - test_me_admin_sees_all_clients
"""
from __future__ import annotations

import uuid

import httpx
import pytest


def _assert_error_envelope(body: dict) -> None:
    assert "error" in body, body
    assert isinstance(body["error"], dict)
    assert "code" in body["error"]
    assert "message" in body["error"]


@pytest.mark.asyncio
async def test_get_me_requires_auth(api_client: httpx.AsyncClient) -> None:
    r = await api_client.get("/v1/auth/me")
    assert r.status_code == 401
    _assert_error_envelope(r.json())


@pytest.mark.asyncio
async def test_get_me_returns_client_slugs_for_member(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    r = await api_client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {test_tenant['token']}"},
    )
    assert r.status_code == 200
    payload = r.json()
    assert payload["email"] == test_tenant["email"]
    assert payload["role"] == "owner"
    assert payload["client_slugs"] == [test_tenant["client_slug"]]
    # user_id is a UUID
    uuid.UUID(payload["user_id"])


@pytest.mark.asyncio
async def test_me_empty_client_slugs_for_non_member(
    api_client: httpx.AsyncClient, outsider: dict
) -> None:
    r = await api_client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {outsider['token']}"},
    )
    assert r.status_code == 200
    payload = r.json()
    assert payload["client_slugs"] == []
    assert payload["role"] == "viewer"


@pytest.mark.asyncio
async def test_me_admin_sees_all_clients(
    api_client: httpx.AsyncClient, test_tenant: dict, db,
) -> None:
    """Admin role on any membership bumps effective role to admin + exposes every client."""
    # Promote test_tenant's user to admin
    await db.execute(
        "UPDATE user_client_memberships SET role = 'admin' WHERE user_id = $1",
        test_tenant["user_id"],
    )
    # Add a second client they have no explicit membership on
    other_slug = f"other-{uuid.uuid4().hex[:6]}"
    other_id = await db.fetchval(
        "INSERT INTO clients (slug, name) VALUES ($1, $2) RETURNING id",
        other_slug, "Other Client",
    )
    try:
        r = await api_client.get(
            "/v1/auth/me",
            headers={"Authorization": f"Bearer {test_tenant['token']}"},
        )
        assert r.status_code == 200
        payload = r.json()
        assert payload["role"] == "admin"
        # Admin sees both clients
        assert test_tenant["client_slug"] in payload["client_slugs"]
        assert other_slug in payload["client_slugs"]
    finally:
        await db.execute("DELETE FROM clients WHERE id = $1", other_id)


@pytest.mark.asyncio
async def test_logout_requires_auth(api_client: httpx.AsyncClient) -> None:
    r = await api_client.post("/v1/auth/logout")
    assert r.status_code == 401
    _assert_error_envelope(r.json())


@pytest.mark.asyncio
async def test_logout_with_auth_returns_204(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    r = await api_client.post(
        "/v1/auth/logout",
        headers={"Authorization": f"Bearer {test_tenant['token']}"},
    )
    assert r.status_code == 204
    assert r.content == b""


@pytest.mark.asyncio
async def test_logout_revokes_token_blocklist(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    """After logout, the same token hits the in-memory blocklist and returns 401."""
    headers = {"Authorization": f"Bearer {test_tenant['token']}"}

    # Warmup — token works
    r = await api_client.get("/v1/auth/me", headers=headers)
    assert r.status_code == 200

    # Logout
    r = await api_client.post("/v1/auth/logout", headers=headers)
    assert r.status_code == 204

    # Same token now rejected
    r = await api_client.get("/v1/auth/me", headers=headers)
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "token_revoked"


@pytest.mark.asyncio
async def test_bad_token_returns_401(api_client: httpx.AsyncClient) -> None:
    r = await api_client.get(
        "/v1/auth/me",
        headers={"Authorization": "Bearer not-a-real-jwt"},
    )
    assert r.status_code == 401
    _assert_error_envelope(r.json())
