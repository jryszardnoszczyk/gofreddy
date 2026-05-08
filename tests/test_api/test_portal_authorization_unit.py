"""Unit tests for portal_report_view + portal_meta_patterns authorization.

Mocks the auth principal + membership lookup so these tests run without a
live Supabase / Postgres stack. Covers the cross-tenant authorization fix
(2026-05-08 review): a user with membership in client A must NOT be able to
read client B's reports or the global meta-patterns aggregate (unless they
are admin).
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.dependencies import AuthPrincipal, get_auth_principal
from src.api.routers import portal as portal_module
from src.api.rate_limit import limiter


@pytest.fixture
def fake_app(tmp_path, monkeypatch):
    """Boot a minimal FastAPI app with the portal router mounted.

    Patches _ARCHIVE_ROOT to tmp_path so we control filesystem layout.
    Overrides get_auth_principal so tests inject the user directly.
    Patches resolve_client_access to return whatever role the test wants.
    """
    monkeypatch.setattr(portal_module, "_ARCHIVE_ROOT", tmp_path)
    monkeypatch.setattr(portal_module, "_ARCHIVE_ROOT_REAL", tmp_path.resolve())

    app = FastAPI()
    app.state.db_pool = object()  # opaque — resolve_client_access is patched
    app.state.limiter = limiter
    app.include_router(portal_module.router)
    return app


def _principal(user_id=None) -> AuthPrincipal:
    return AuthPrincipal(
        user_id=user_id or uuid4(),
        claims={"email": "test@example.com"},
        credential_type="jwt",
    )


# ─── portal_report_view ──────────────────────────────────────────────────────


def test_no_membership_returns_403(fake_app):
    fake_app.dependency_overrides[get_auth_principal] = _principal
    with patch.object(portal_module, "resolve_client_access",
                      new=AsyncMock(return_value=None)):
        client = TestClient(fake_app)
        r = client.get("/v1/portal/acme/reports/marketing_audit/v006/acme")
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "no_membership"


def test_marketing_audit_cross_tenant_blocked(fake_app, tmp_path):
    """User with membership in 'acme' must NOT read 'initech's marketing_audit
    report just by passing fixture=initech in the URL. P0 #1 from review."""
    # Plant a report for 'initech'
    initech_dir = tmp_path / "v006" / "sessions" / "marketing_audit" / "initech"
    initech_dir.mkdir(parents=True)
    (initech_dir / "report.html").write_text("<h1>INITECH SECRET AUDIT</h1>")

    fake_app.dependency_overrides[get_auth_principal] = _principal
    with patch.object(portal_module, "resolve_client_access",
                      new=AsyncMock(return_value="member")):  # acme member
        client = TestClient(fake_app)
        r = client.get("/v1/portal/acme/reports/marketing_audit/v006/initech")

    assert r.status_code == 404, (
        f"cross-tenant marketing_audit read should be 404, got {r.status_code}"
    )
    assert "INITECH SECRET AUDIT" not in r.text


def test_marketing_audit_own_tenant_allowed(fake_app, tmp_path):
    acme_dir = tmp_path / "v006" / "sessions" / "marketing_audit" / "acme"
    acme_dir.mkdir(parents=True)
    (acme_dir / "report.html").write_text("<h1>acme audit</h1>")

    fake_app.dependency_overrides[get_auth_principal] = _principal
    with patch.object(portal_module, "resolve_client_access",
                      new=AsyncMock(return_value="member")):
        client = TestClient(fake_app)
        r = client.get("/v1/portal/acme/reports/marketing_audit/v006/acme")

    assert r.status_code == 200
    assert "acme audit" in r.text


def test_operator_lane_blocked_for_member(fake_app, tmp_path):
    """geo / competitive / monitoring / storyboard are operator-only.
    A member-role user must get 403, even for their own slug. P0 #1 from review."""
    geo_dir = tmp_path / "v007" / "sessions" / "geo" / "mayoclinic"
    geo_dir.mkdir(parents=True)
    (geo_dir / "report.html").write_text("<h1>geo report</h1>")

    fake_app.dependency_overrides[get_auth_principal] = _principal
    with patch.object(portal_module, "resolve_client_access",
                      new=AsyncMock(return_value="member")):
        client = TestClient(fake_app)
        r = client.get("/v1/portal/acme/reports/geo/v007/mayoclinic")

    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "operator_only"


def test_operator_lane_allowed_for_admin(fake_app, tmp_path):
    geo_dir = tmp_path / "v007" / "sessions" / "geo" / "mayoclinic"
    geo_dir.mkdir(parents=True)
    (geo_dir / "report.html").write_text("<h1>geo report</h1>")

    fake_app.dependency_overrides[get_auth_principal] = _principal
    with patch.object(portal_module, "resolve_client_access",
                      new=AsyncMock(return_value="admin")):
        client = TestClient(fake_app)
        r = client.get("/v1/portal/acme/reports/geo/v007/mayoclinic")

    assert r.status_code == 200
    assert "geo report" in r.text


def test_invalid_lane_400(fake_app):
    fake_app.dependency_overrides[get_auth_principal] = _principal
    with patch.object(portal_module, "resolve_client_access",
                      new=AsyncMock(return_value="admin")):
        client = TestClient(fake_app)
        r = client.get("/v1/portal/acme/reports/notalane/v007/foo")
    assert r.status_code == 400


def test_invalid_variant_400(fake_app):
    fake_app.dependency_overrides[get_auth_principal] = _principal
    with patch.object(portal_module, "resolve_client_access",
                      new=AsyncMock(return_value="admin")):
        client = TestClient(fake_app)
        r = client.get("/v1/portal/acme/reports/geo/notavariant/foo")
    assert r.status_code == 400


def test_traversal_in_fixture_400(fake_app):
    """``..`` in fixture must be rejected by the allowlist regex BEFORE
    the safe-path check ever runs."""
    fake_app.dependency_overrides[get_auth_principal] = _principal
    with patch.object(portal_module, "resolve_client_access",
                      new=AsyncMock(return_value="admin")):
        client = TestClient(fake_app)
        # FastAPI URL routing won't let raw ".." into a path segment, but the
        # route param can still receive crafted forms. Test via TestClient.
        r = client.get("/v1/portal/acme/reports/geo/v007/foo..bar")
    # The ``.`` was removed from the allowlist — even non-traversal dots
    # are rejected now.
    assert r.status_code in (400, 404)


def test_symlink_in_archive_blocked(fake_app, tmp_path):
    """A symlinked report.html → outside-archive path must NOT be served."""
    geo_dir = tmp_path / "v007" / "sessions" / "geo" / "mayoclinic"
    geo_dir.mkdir(parents=True)
    secret = tmp_path.parent / "secret.html"
    secret.write_text("<h1>SECRET</h1>")
    (geo_dir / "report.html").symlink_to(secret)

    fake_app.dependency_overrides[get_auth_principal] = _principal
    with patch.object(portal_module, "resolve_client_access",
                      new=AsyncMock(return_value="admin")):
        client = TestClient(fake_app)
        r = client.get("/v1/portal/acme/reports/geo/v007/mayoclinic")

    assert r.status_code == 404, (
        f"symlinked report.html should not be served, got {r.status_code}"
    )
    assert "SECRET" not in r.text


# ─── portal_meta_patterns ────────────────────────────────────────────────────


def test_meta_patterns_blocks_member(fake_app, tmp_path):
    """Member role must NOT see global cross-tenant meta-patterns. P0 #2."""
    (tmp_path / "meta_patterns.json").write_text(
        json.dumps({"meta_patterns": [{"representative_text": "secret-from-other-tenant"}]})
    )
    fake_app.dependency_overrides[get_auth_principal] = _principal
    with patch.object(portal_module, "resolve_client_access",
                      new=AsyncMock(return_value="member")):
        client = TestClient(fake_app)
        r = client.get("/v1/portal/acme/meta-patterns")

    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "operator_only"


def test_meta_patterns_admin_sees_data(fake_app, tmp_path):
    (tmp_path / "meta_patterns.json").write_text(
        json.dumps({
            "meta_patterns": [{
                "representative_text": "I'll read the session ledger first",
                "kind": "first_move",
                "occurrences": 214,
                "distinct_lanes": 5,
                "distinct_fixtures": 41,
                "lanes": ["geo", "competitive", "monitoring", "storyboard", "marketing_audit"],
            }],
            "stats": {"sessions": 42, "beats": 2134},
        })
    )
    fake_app.dependency_overrides[get_auth_principal] = _principal
    with patch.object(portal_module, "resolve_client_access",
                      new=AsyncMock(return_value="admin")):
        client = TestClient(fake_app)
        r = client.get("/v1/portal/acme/meta-patterns")

    assert r.status_code == 200
    assert "session ledger" in r.text
    assert "214" in r.text


def test_meta_patterns_corrupt_json_renders_empty(fake_app, tmp_path):
    """Malformed JSON should NOT crash the route — degrade gracefully."""
    (tmp_path / "meta_patterns.json").write_text("not valid json {[}")
    fake_app.dependency_overrides[get_auth_principal] = _principal
    with patch.object(portal_module, "resolve_client_access",
                      new=AsyncMock(return_value="admin")):
        client = TestClient(fake_app)
        r = client.get("/v1/portal/acme/meta-patterns")
    assert r.status_code == 200
    assert "No patterns surfaced yet" in r.text


def test_meta_patterns_string_int_does_not_500(fake_app, tmp_path):
    """A poisoned cluster with string occurrences must NOT crash the route."""
    (tmp_path / "meta_patterns.json").write_text(
        json.dumps({"meta_patterns": [{
            "representative_text": "x",
            "kind": "first_move",
            "occurrences": "many",       # ← attacker-shaped
            "distinct_lanes": "loads",
            "distinct_fixtures": None,
            "lanes": "not-a-list",       # ← attacker-shaped
        }]})
    )
    fake_app.dependency_overrides[get_auth_principal] = _principal
    with patch.object(portal_module, "resolve_client_access",
                      new=AsyncMock(return_value="admin")):
        client = TestClient(fake_app)
        r = client.get("/v1/portal/acme/meta-patterns")
    assert r.status_code == 200  # not 500
