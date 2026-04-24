"""Tests for src/geo/providers/cloro.py.

Covers two recent bug fixes:
  - Bug #3: CLORO_TIMEOUT_SECONDS env override; default bumped to 180s.
  - Bug #4: CloroInsufficientCreditsError distinguishes 403-credits from
    generic 403-forbidden.
"""
from __future__ import annotations

import os
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from src.geo.providers.cloro import (
    CloroClient,
    CloroClientError,
    CloroError,
    CloroInsufficientCreditsError,
    CloroRateLimitError,
)


# --- timeout default + env override ---------------------------------------


def test_default_timeout_is_180s(monkeypatch):
    monkeypatch.delenv("CLORO_TIMEOUT_SECONDS", raising=False)
    c = CloroClient(api_key="test_key")
    assert c.timeout == 180.0


def test_timeout_honors_env_override(monkeypatch):
    monkeypatch.setenv("CLORO_TIMEOUT_SECONDS", "300")
    c = CloroClient(api_key="test_key")
    assert c.timeout == 300.0


def test_timeout_env_override_must_be_numeric(monkeypatch):
    monkeypatch.setenv("CLORO_TIMEOUT_SECONDS", "not-a-number")
    with pytest.raises(ValueError):
        CloroClient(api_key="test_key")


# --- 403 credit-vs-forbidden distinction ----------------------------------


def _mock_response(status: int, body: dict | None = None) -> Mock:
    r = Mock()
    r.status_code = status
    r.json = Mock(return_value=body or {})

    if status >= 400:
        err = httpx.HTTPStatusError("error", request=Mock(), response=r)
        r.raise_for_status = Mock(side_effect=err)
    else:
        r.raise_for_status = Mock()
    return r


async def _call_make_request(response_mock):
    c = CloroClient(api_key="test_key")
    with patch.object(c._client, "post", new=AsyncMock(return_value=response_mock)):
        return await c._make_request("chatgpt", "test prompt", "US")


@pytest.mark.asyncio
async def test_403_insufficient_credits_raises_dedicated_error():
    resp = _mock_response(
        403,
        {
            "success": False,
            "error": {
                "code": "INSUFFICIENT_CREDITS",
                "message": "Insufficient credits",
            },
        },
    )
    with pytest.raises(CloroInsufficientCreditsError) as excinfo:
        await _call_make_request(resp)
    assert "out of credits" in str(excinfo.value).lower()
    # Subclass relationship preserves existing call-site handling
    assert isinstance(excinfo.value, CloroClientError)


@pytest.mark.asyncio
async def test_403_generic_forbidden_still_raises_plain_client_error():
    """403 without INSUFFICIENT_CREDITS code (e.g., IP-blocked) stays
    CloroClientError — not InsufficientCredits."""
    resp = _mock_response(
        403,
        {"success": False, "error": {"code": "IP_BLOCKED", "message": "IP blocked"}},
    )
    with pytest.raises(CloroClientError) as excinfo:
        await _call_make_request(resp)
    assert not isinstance(excinfo.value, CloroInsufficientCreditsError)
    assert "forbidden" in str(excinfo.value).lower()


@pytest.mark.asyncio
async def test_403_with_unparseable_body_stays_generic_forbidden():
    """If the 403 body isn't JSON or has no .error.code, fall back to generic."""
    resp = Mock()
    resp.status_code = 403
    resp.json = Mock(side_effect=ValueError("not json"))
    err = httpx.HTTPStatusError("error", request=Mock(), response=resp)
    resp.raise_for_status = Mock(side_effect=err)
    with pytest.raises(CloroClientError) as excinfo:
        await _call_make_request(resp)
    assert not isinstance(excinfo.value, CloroInsufficientCreditsError)


@pytest.mark.asyncio
async def test_429_still_raises_rate_limit_error_not_credits():
    """429 must stay CloroRateLimitError (retryable)."""
    resp = _mock_response(429, {"error": {"code": "RATE_LIMIT"}})
    with pytest.raises(CloroRateLimitError):
        await _call_make_request(resp)


@pytest.mark.asyncio
async def test_401_still_raises_generic_client_error():
    """401 path unchanged by the 403 fix."""
    resp = _mock_response(401)
    with pytest.raises(CloroClientError) as excinfo:
        await _call_make_request(resp)
    assert not isinstance(excinfo.value, CloroInsufficientCreditsError)
    assert "invalid api key" in str(excinfo.value).lower()
