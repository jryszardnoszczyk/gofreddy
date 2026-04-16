"""Tests for accounts router OAuth schemas."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.api.routers.accounts import (
    BlueskyConnectRequest,
    ConnectionResponse,
    DeviceInitRequest,
    DeviceInitResponse,
    DeviceVerifyResponse,
)


@pytest.mark.mock_required
def test_device_init_request_schema():
    """Verify DeviceInitRequest validates correctly with a platform string."""
    req = DeviceInitRequest(platform="linkedin")
    assert req.platform == "linkedin"

    # Missing required field
    with pytest.raises(ValidationError):
        DeviceInitRequest()  # type: ignore[call-arg]


@pytest.mark.mock_required
def test_device_verify_response_schema():
    """Verify DeviceVerifyResponse serializes correctly with optional connection_id."""
    # Pending state — no connection_id
    resp_pending = DeviceVerifyResponse(status="pending")
    data = resp_pending.model_dump()
    assert data["status"] == "pending"
    assert data["connection_id"] is None

    # Complete state — with connection_id
    cid = uuid4()
    resp_complete = DeviceVerifyResponse(status="complete", connection_id=cid)
    data = resp_complete.model_dump()
    assert data["status"] == "complete"
    assert data["connection_id"] == cid


@pytest.mark.mock_required
def test_bluesky_connect_request_max_length():
    """Verify max_length=128 on app_password field is enforced."""
    # Valid length
    req = BlueskyConnectRequest(handle="user.bsky.social", app_password="short-pass")
    assert req.app_password == "short-pass"

    # Exceeds max_length (129 characters)
    with pytest.raises(ValidationError, match="app_password"):
        BlueskyConnectRequest(handle="user.bsky.social", app_password="x" * 129)


@pytest.mark.mock_required
def test_connection_response_schema():
    """Verify ConnectionResponse serializes correctly with all required fields."""
    now = datetime.now(tz=timezone.utc)
    cid = uuid4()
    resp = ConnectionResponse(
        id=cid,
        platform="linkedin",
        auth_type="oauth2",
        account_id="acct-123",
        account_name="My LinkedIn",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    data = resp.model_dump()
    assert data["id"] == cid
    assert data["platform"] == "linkedin"
    assert data["auth_type"] == "oauth2"
    assert data["account_id"] == "acct-123"
    assert data["account_name"] == "My LinkedIn"
    assert data["is_active"] is True


@pytest.mark.mock_required
def test_device_init_response_schema():
    """Verify DeviceInitResponse serializes correctly with all fields."""
    resp = DeviceInitResponse(
        device_code="DEV-123",
        user_code="ABCD-EFGH",
        verification_uri="https://example.com/device",
        verification_uri_complete="https://example.com/device?code=ABCD-EFGH",
        expires_in=900,
        interval=5,
    )
    data = resp.model_dump()
    assert data["device_code"] == "DEV-123"
    assert data["user_code"] == "ABCD-EFGH"
    assert data["verification_uri"] == "https://example.com/device"
    assert data["verification_uri_complete"] == "https://example.com/device?code=ABCD-EFGH"
    assert data["expires_in"] == 900
    assert data["interval"] == 5

    # verification_uri_complete is optional
    resp_no_complete = DeviceInitResponse(
        device_code="DEV-456",
        user_code="WXYZ-1234",
        verification_uri="https://example.com/device",
        expires_in=600,
        interval=10,
    )
    assert resp_no_complete.verification_uri_complete is None
