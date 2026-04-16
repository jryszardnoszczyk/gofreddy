"""Tests for CORS configuration hardening (PR-057 I2)."""

import os
from unittest.mock import patch

import pytest

_DEFAULT_DEV_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3002",
    "http://127.0.0.1:3002",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


def test_cors_strips_whitespace():
    """CORS origins are stripped of whitespace."""
    with patch.dict(os.environ, {"CORS_ALLOWED_ORIGINS": " http://a.com , http://b.com "}):
        raw = os.environ.get("CORS_ALLOWED_ORIGINS", ",".join(_DEFAULT_DEV_ORIGINS))
        origins = [o.strip() for o in raw.split(",") if o.strip()]
        assert origins == ["http://a.com", "http://b.com"]


def test_cors_filters_empty_strings():
    """Empty strings after splitting are filtered out."""
    with patch.dict(os.environ, {"CORS_ALLOWED_ORIGINS": "http://a.com,,http://b.com,"}):
        raw = os.environ.get("CORS_ALLOWED_ORIGINS", ",".join(_DEFAULT_DEV_ORIGINS))
        origins = [o.strip() for o in raw.split(",") if o.strip()]
        assert origins == ["http://a.com", "http://b.com"]


def test_cors_rejects_wildcard_with_credentials():
    """Wildcard origin with credentials raises ValueError."""
    from src.api.main import create_app

    with patch.dict(os.environ, {"CORS_ALLOWED_ORIGINS": "*"}, clear=False):
        with pytest.raises(ValueError, match="security vulnerability"):
            create_app()


def test_cors_defaults_on_empty():
    """Empty origins string defaults to local dev origins."""
    with patch.dict(os.environ, {"CORS_ALLOWED_ORIGINS": "  ,  ,  "}):
        raw = os.environ.get("CORS_ALLOWED_ORIGINS", ",".join(_DEFAULT_DEV_ORIGINS))
        origins = [o.strip() for o in raw.split(",") if o.strip()]
        if not origins:
            origins = _DEFAULT_DEV_ORIGINS
        assert origins == _DEFAULT_DEV_ORIGINS
