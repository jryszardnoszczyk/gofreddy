"""Membership tests — new module in gofreddy, no freddy equivalent.

Covers the single chokepoint for client access:
  - resolve_client_access returns role for member, None for non-member
  - Admin role on any membership grants access to every client
  - list_client_memberships returns all for admin, subset for viewer
"""
from __future__ import annotations

import uuid

import asyncpg
import pytest

from src.api.membership import (
    Membership,
    list_client_memberships,
    resolve_client_access,
)


@pytest.fixture
async def pool(app):
    """Share the app's asyncpg pool with tests."""
    return app.state.db_pool


@pytest.mark.asyncio
async def test_resolve_returns_role_for_member(pool, test_tenant: dict) -> None:
    role = await resolve_client_access(pool, test_tenant["user_id"], test_tenant["client_slug"])
    assert role == "owner"


@pytest.mark.asyncio
async def test_resolve_returns_none_for_non_member(pool, outsider: dict, test_tenant: dict) -> None:
    # outsider has no membership to test_tenant's client
    role = await resolve_client_access(pool, outsider["user_id"], test_tenant["client_slug"])
    assert role is None


@pytest.mark.asyncio
async def test_resolve_returns_none_for_unknown_slug(pool, test_tenant: dict) -> None:
    role = await resolve_client_access(pool, test_tenant["user_id"], "ghost-slug-does-not-exist")
    assert role is None


@pytest.mark.asyncio
async def test_admin_sees_any_client(pool, test_tenant: dict, db: asyncpg.Connection) -> None:
    """Admin role on their home client gates them into every other client too."""
    await db.execute(
        "UPDATE user_client_memberships SET role = 'admin' WHERE user_id = $1",
        test_tenant["user_id"],
    )
    # Create a client the admin has no explicit membership on
    other_slug = f"admin-target-{uuid.uuid4().hex[:6]}"
    other_id = await db.fetchval(
        "INSERT INTO clients (slug, name) VALUES ($1, $2) RETURNING id",
        other_slug, "Admin Target",
    )
    try:
        role = await resolve_client_access(pool, test_tenant["user_id"], other_slug)
        assert role == "admin", "admin should see every client without explicit membership"
    finally:
        await db.execute("DELETE FROM clients WHERE id = $1", other_id)


@pytest.mark.asyncio
async def test_list_memberships_for_member(pool, test_tenant: dict) -> None:
    memberships = await list_client_memberships(pool, test_tenant["user_id"])
    assert len(memberships) == 1
    m = memberships[0]
    assert isinstance(m, Membership)
    assert m.slug == test_tenant["client_slug"]
    assert m.role == "owner"


@pytest.mark.asyncio
async def test_list_memberships_empty_for_outsider(pool, outsider: dict) -> None:
    memberships = await list_client_memberships(pool, outsider["user_id"])
    assert memberships == []


@pytest.mark.asyncio
async def test_list_memberships_admin_sees_all(pool, test_tenant: dict, db: asyncpg.Connection) -> None:
    await db.execute(
        "UPDATE user_client_memberships SET role = 'admin' WHERE user_id = $1",
        test_tenant["user_id"],
    )
    other_slug = f"admin-sees-{uuid.uuid4().hex[:6]}"
    other_id = await db.fetchval(
        "INSERT INTO clients (slug, name) VALUES ($1, $2) RETURNING id",
        other_slug, "Admin Sees This Too",
    )
    try:
        memberships = await list_client_memberships(pool, test_tenant["user_id"])
        slugs = {m.slug for m in memberships}
        assert test_tenant["client_slug"] in slugs
        assert other_slug in slugs
        # Admin sees everything with role=admin
        assert all(m.role == "admin" for m in memberships)
    finally:
        await db.execute("DELETE FROM clients WHERE id = $1", other_id)
