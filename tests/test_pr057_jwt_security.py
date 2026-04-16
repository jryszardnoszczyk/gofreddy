"""Tests for JWT security and OIDC bypass hardening (PR-057 I5)."""

import logging
import os
from unittest.mock import AsyncMock, MagicMock, patch

import jwt as pyjwt
import pytest
from fastapi import HTTPException

from src.api.dependencies import verify_supabase_token, _decode_supabase_jwt


# ── JWT Specific Exception Tests ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_jwt_catches_expired_signature():
    """Expired JWT returns 401 with token_expired code."""
    mock_request = MagicMock()
    mock_settings = MagicMock()
    mock_settings.supabase_url = "https://test.supabase.co"
    mock_request.app.state.supabase_settings = mock_settings
    mock_request.app.state.jwks_client = None

    mock_creds = MagicMock()
    mock_creds.credentials = "expired.jwt.token"

    with patch(
        "src.api.dependencies._decode_supabase_jwt",
        side_effect=pyjwt.ExpiredSignatureError("Token expired"),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await verify_supabase_token(mock_request, mock_creds)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["code"] == "token_expired"


@pytest.mark.asyncio
async def test_jwt_catches_invalid_audience():
    """Invalid audience returns 401 with invalid_token code."""
    mock_request = MagicMock()
    mock_settings = MagicMock()
    mock_settings.supabase_url = "https://test.supabase.co"
    mock_request.app.state.supabase_settings = mock_settings
    mock_request.app.state.jwks_client = None

    mock_creds = MagicMock()
    mock_creds.credentials = "bad.audience.token"

    with patch(
        "src.api.dependencies._decode_supabase_jwt",
        side_effect=pyjwt.InvalidAudienceError("Invalid audience"),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await verify_supabase_token(mock_request, mock_creds)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["code"] == "invalid_token"


@pytest.mark.asyncio
async def test_jwt_catches_invalid_issuer():
    """Invalid issuer returns 401 with invalid_token code."""
    mock_request = MagicMock()
    mock_settings = MagicMock()
    mock_settings.supabase_url = "https://test.supabase.co"
    mock_request.app.state.supabase_settings = mock_settings
    mock_request.app.state.jwks_client = None

    mock_creds = MagicMock()
    mock_creds.credentials = "bad.issuer.token"

    with patch(
        "src.api.dependencies._decode_supabase_jwt",
        side_effect=pyjwt.InvalidIssuerError("Invalid issuer"),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await verify_supabase_token(mock_request, mock_creds)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["code"] == "invalid_token"


@pytest.mark.asyncio
async def test_jwt_catches_malformed_token():
    """Malformed token returns 401 with invalid_token code."""
    mock_request = MagicMock()
    mock_settings = MagicMock()
    mock_settings.supabase_url = "https://test.supabase.co"
    mock_request.app.state.supabase_settings = mock_settings
    mock_request.app.state.jwks_client = None

    mock_creds = MagicMock()
    mock_creds.credentials = "not.a.valid.jwt"

    with patch(
        "src.api.dependencies._decode_supabase_jwt",
        side_effect=pyjwt.InvalidTokenError("Malformed token"),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await verify_supabase_token(mock_request, mock_creds)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["code"] == "invalid_token"


def test_jwt_jwks_fallback_to_hs256():
    """JWKS failure falls through to HS256 decoding."""
    mock_settings = MagicMock()
    mock_settings.supabase_url = "https://test.supabase.co"
    mock_settings.supabase_jwt_secret.get_secret_value.return_value = "test-secret-key-thats-long-enough"

    mock_jwks = MagicMock()
    mock_jwks.get_signing_key_from_jwt.side_effect = pyjwt.exceptions.PyJWKClientError("JWKS fetch failed")

    # Create a valid HS256 token
    token = pyjwt.encode(
        {"sub": "user123", "aud": "authenticated", "iss": "https://test.supabase.co/auth/v1"},
        "test-secret-key-thats-long-enough",
        algorithm="HS256",
    )

    # Should fall through JWKS and succeed with HS256
    claims = _decode_supabase_jwt(token, mock_settings, mock_jwks)
    assert claims["sub"] == "user123"


# ── OIDC Bypass Warning Test ──────────────────────────────────────────────


def test_oidc_bypass_warning_logged(caplog):
    """Verify warning is emitted when ENVIRONMENT=development at module load."""
    with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
        with caplog.at_level(logging.WARNING):
            # Force module reload to trigger module-level warning
            import importlib
            import src.api.routers.internal as internal_mod
            importlib.reload(internal_mod)

    # Check that the warning was logged
    assert any("OIDC bypass active" in record.message for record in caplog.records)
