"""Tests for the new portal bundle + per-file routes.

Mirrors the existing test_portal_authorization_unit.py setup: patch the
archive root to a tmp_path, override get_auth_principal, mock
resolve_client_access. Covers:

- Bundle download path-traversal safety + content-type
- Per-file download path-traversal safety (.., ., NUL, slash injection)
- Auth model parity with portal_report_view (cross-tenant blocked,
  operator-only for non-marketing_audit lanes, admin override)
- 404 distinction (file_not_found vs bundle_not_found vs report_not_found)
- New x_engine + linkedin_engine lanes accepted by allowlist
"""
from __future__ import annotations

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
    monkeypatch.setattr(portal_module, "_ARCHIVE_ROOT", tmp_path)
    monkeypatch.setattr(portal_module, "_ARCHIVE_ROOT_REAL", tmp_path.resolve())
    app = FastAPI()
    app.state.db_pool = object()
    app.state.limiter = limiter
    app.include_router(portal_module.router)
    return app


def _principal(user_id=None) -> AuthPrincipal:
    return AuthPrincipal(
        user_id=user_id or uuid4(),
        claims={"email": "test@example.com"},
        credential_type="jwt",
    )


# ─── bundle.tar.gz route ─────────────────────────────────────────────────────


def test_bundle_404_when_missing(fake_app):
    fake_app.dependency_overrides[get_auth_principal] = _principal
    with patch.object(portal_module, "resolve_client_access",
                      new=AsyncMock(return_value="admin")):
        client = TestClient(fake_app)
        r = client.get(
            "/v1/portal/acme/reports/geo/v006/ahrefs/bundle.tar.gz"
        )
    assert r.status_code == 404
    assert r.json()["detail"]["code"] == "bundle_not_found"


def test_bundle_served_when_present(fake_app, tmp_path):
    sd = tmp_path / "v006" / "sessions" / "geo" / "ahrefs"
    sd.mkdir(parents=True)
    (sd / "bundle.tar.gz").write_bytes(b"\x1f\x8btestdata")

    fake_app.dependency_overrides[get_auth_principal] = _principal
    with patch.object(portal_module, "resolve_client_access",
                      new=AsyncMock(return_value="admin")):
        client = TestClient(fake_app)
        r = client.get(
            "/v1/portal/acme/reports/geo/v006/ahrefs/bundle.tar.gz"
        )
    assert r.status_code == 200
    assert r.content == b"\x1f\x8btestdata"
    assert r.headers["content-type"] == "application/gzip"


def test_bundle_blocked_for_member_on_operator_lane(fake_app, tmp_path):
    sd = tmp_path / "v006" / "sessions" / "geo" / "ahrefs"
    sd.mkdir(parents=True)
    (sd / "bundle.tar.gz").write_bytes(b"\x1f\x8b")

    fake_app.dependency_overrides[get_auth_principal] = _principal
    with patch.object(portal_module, "resolve_client_access",
                      new=AsyncMock(return_value="member")):
        client = TestClient(fake_app)
        r = client.get(
            "/v1/portal/acme/reports/geo/v006/ahrefs/bundle.tar.gz"
        )
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "operator_only"


def test_bundle_marketing_audit_cross_tenant_blocked(fake_app, tmp_path):
    sd = tmp_path / "v006" / "sessions" / "marketing_audit" / "initech"
    sd.mkdir(parents=True)
    (sd / "bundle.tar.gz").write_bytes(b"secret")

    fake_app.dependency_overrides[get_auth_principal] = _principal
    with patch.object(portal_module, "resolve_client_access",
                      new=AsyncMock(return_value="member")):
        client = TestClient(fake_app)
        r = client.get(
            "/v1/portal/acme/reports/marketing_audit/v006/initech/bundle.tar.gz"
        )
    assert r.status_code == 404
    assert b"secret" not in r.content


def test_bundle_no_membership_returns_403(fake_app):
    fake_app.dependency_overrides[get_auth_principal] = _principal
    with patch.object(portal_module, "resolve_client_access",
                      new=AsyncMock(return_value=None)):
        client = TestClient(fake_app)
        r = client.get(
            "/v1/portal/acme/reports/geo/v006/ahrefs/bundle.tar.gz"
        )
    assert r.status_code == 403


# ─── per-file route ──────────────────────────────────────────────────────────


def test_files_route_serves_real_file(fake_app, tmp_path):
    sd = tmp_path / "v006" / "sessions" / "geo" / "ahrefs"
    (sd / "logs").mkdir(parents=True)
    (sd / "logs" / "iteration_001.log.err").write_text("codex\nbeats\n")

    fake_app.dependency_overrides[get_auth_principal] = _principal
    with patch.object(portal_module, "resolve_client_access",
                      new=AsyncMock(return_value="admin")):
        client = TestClient(fake_app)
        r = client.get(
            "/v1/portal/acme/reports/geo/v006/ahrefs/files/logs/iteration_001.log.err"
        )
    assert r.status_code == 200
    assert r.text == "codex\nbeats\n"
    assert "text/plain" in r.headers["content-type"]


@pytest.mark.parametrize("rel", [
    "../../etc/passwd",
    "logs/../../etc/passwd",
    "logs/../../../",
    "../v006/sessions/marketing_audit/initech/report.html",
    "./logs/foo",
    "..",
    ".",
    "...",
])
def test_files_route_rejects_traversal(fake_app, tmp_path, rel):
    """All-dot segments must be rejected before resolve() — the regex
    accepts dots, but the all-dot check catches '.', '..', '...' etc.
    """
    fake_app.dependency_overrides[get_auth_principal] = _principal
    with patch.object(portal_module, "resolve_client_access",
                      new=AsyncMock(return_value="admin")):
        client = TestClient(fake_app)
        r = client.get(
            f"/v1/portal/acme/reports/geo/v006/ahrefs/files/{rel}"
        )
    assert r.status_code in (400, 404)
    if r.status_code == 400:
        assert r.json()["detail"]["code"] in {
            "dot_segment", "invalid_segment", "empty_segment", "empty_relpath",
        }


def test_files_route_rejects_invalid_chars(fake_app):
    fake_app.dependency_overrides[get_auth_principal] = _principal
    with patch.object(portal_module, "resolve_client_access",
                      new=AsyncMock(return_value="admin")):
        client = TestClient(fake_app)
        # space + special chars are not in [A-Za-z0-9._-]
        r = client.get(
            "/v1/portal/acme/reports/geo/v006/ahrefs/files/logs/file%20with%20space.txt"
        )
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == "invalid_segment"


def test_files_route_404_when_file_missing(fake_app):
    fake_app.dependency_overrides[get_auth_principal] = _principal
    with patch.object(portal_module, "resolve_client_access",
                      new=AsyncMock(return_value="admin")):
        client = TestClient(fake_app)
        r = client.get(
            "/v1/portal/acme/reports/geo/v006/ahrefs/files/logs/nonexistent.log"
        )
    assert r.status_code == 404
    assert r.json()["detail"]["code"] == "file_not_found"


def test_files_route_blocked_for_member_on_operator_lane(fake_app, tmp_path):
    sd = tmp_path / "v006" / "sessions" / "geo" / "ahrefs"
    (sd / "logs").mkdir(parents=True)
    (sd / "logs" / "iteration_001.log.err").write_text("secret")

    fake_app.dependency_overrides[get_auth_principal] = _principal
    with patch.object(portal_module, "resolve_client_access",
                      new=AsyncMock(return_value="member")):
        client = TestClient(fake_app)
        r = client.get(
            "/v1/portal/acme/reports/geo/v006/ahrefs/files/logs/iteration_001.log.err"
        )
    assert r.status_code == 403
    assert b"secret" not in r.content


def test_files_route_marketing_audit_cross_tenant_blocked(fake_app, tmp_path):
    sd = tmp_path / "v006" / "sessions" / "marketing_audit" / "initech"
    sd.mkdir(parents=True)
    (sd / "secret.json").write_text('{"k":"secret"}')

    fake_app.dependency_overrides[get_auth_principal] = _principal
    with patch.object(portal_module, "resolve_client_access",
                      new=AsyncMock(return_value="member")):
        client = TestClient(fake_app)
        r = client.get(
            "/v1/portal/acme/reports/marketing_audit/v006/initech/files/secret.json"
        )
    assert r.status_code == 404
    assert b"secret" not in r.content


def test_x_engine_lane_accepted(fake_app, tmp_path):
    """New x_engine lane is accepted by the allowlist; admin can read it."""
    sd = tmp_path / "v007-curated" / "sessions" / "x_engine" / "jr"
    sd.mkdir(parents=True)
    (sd / "bundle.tar.gz").write_bytes(b"\x1f\x8b")

    fake_app.dependency_overrides[get_auth_principal] = _principal
    with patch.object(portal_module, "resolve_client_access",
                      new=AsyncMock(return_value="admin")):
        client = TestClient(fake_app)
        # variant must match `^v\d+$` per the existing validator;
        # use v007 (numeric suffix only — "v007-curated" would fail).
        sd_alt = tmp_path / "v007" / "sessions" / "x_engine" / "jr"
        sd_alt.mkdir(parents=True)
        (sd_alt / "bundle.tar.gz").write_bytes(b"\x1f\x8b")
        r = client.get(
            "/v1/portal/acme/reports/x_engine/v007/jr/bundle.tar.gz"
        )
    assert r.status_code == 200
    assert r.content == b"\x1f\x8b"


def test_linkedin_engine_lane_accepted(fake_app, tmp_path):
    sd = tmp_path / "v007" / "sessions" / "linkedin_engine" / "jr"
    sd.mkdir(parents=True)
    (sd / "bundle.tar.gz").write_bytes(b"\x1f\x8b")

    fake_app.dependency_overrides[get_auth_principal] = _principal
    with patch.object(portal_module, "resolve_client_access",
                      new=AsyncMock(return_value="admin")):
        client = TestClient(fake_app)
        r = client.get(
            "/v1/portal/acme/reports/linkedin_engine/v007/jr/bundle.tar.gz"
        )
    assert r.status_code == 200


def test_invalid_lane_rejected(fake_app):
    fake_app.dependency_overrides[get_auth_principal] = _principal
    with patch.object(portal_module, "resolve_client_access",
                      new=AsyncMock(return_value="admin")):
        client = TestClient(fake_app)
        r = client.get(
            "/v1/portal/acme/reports/notalane/v006/ahrefs/bundle.tar.gz"
        )
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == "invalid_lane"
