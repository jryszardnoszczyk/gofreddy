"""freddy api_request 1× retry on 5xx + transient network errors.

Archive audit found 2002 lines of `unexpected_error` across 90 logs in
monitoring/Shopify, geo/semrush, competitive/figma. Most were single-call
blips that a 1× retry would catch. This test pins that retry behavior."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

_repo_root = Path(__file__).resolve().parents[2]
_cli_dir = str(_repo_root / "cli")
if _cli_dir not in sys.path:
    sys.path.insert(0, _cli_dir)

from freddy import api  # noqa: E402


class _Resp:
    def __init__(self, status_code: int, body: dict | str = ""):
        self.status_code = status_code
        self._body = body
        self.text = body if isinstance(body, str) else ""

    def json(self):
        if isinstance(self._body, dict):
            return self._body
        raise ValueError("not json")


def test_api_request_retries_once_on_500_then_succeeds(monkeypatch):
    client = MagicMock()
    responses = [_Resp(500, "boom"), _Resp(200, {"ok": True})]
    client.request.side_effect = responses
    monkeypatch.setattr(api.time, "sleep", lambda s: None)

    result = api.api_request(client, "GET", "/v1/foo")
    assert result == {"ok": True}
    assert client.request.call_count == 2


def test_api_request_retries_once_on_connection_error(monkeypatch):
    client = MagicMock()
    client.request.side_effect = [
        httpx.ConnectError("refused"),
        _Resp(200, {"ok": True}),
    ]
    monkeypatch.setattr(api.time, "sleep", lambda s: None)

    result = api.api_request(client, "GET", "/v1/foo")
    assert result == {"ok": True}
    assert client.request.call_count == 2


def test_api_request_retries_once_on_timeout(monkeypatch):
    client = MagicMock()
    client.request.side_effect = [
        httpx.TimeoutException("timed out"),
        _Resp(200, {"ok": True}),
    ]
    monkeypatch.setattr(api.time, "sleep", lambda s: None)

    result = api.api_request(client, "GET", "/v1/foo")
    assert result == {"ok": True}
    assert client.request.call_count == 2


def test_api_request_does_NOT_retry_on_4xx(monkeypatch):
    """Caller-error responses (400, 401, 403, 404, 422) are not transient.
    They surface as CLIError + SystemExit on the first attempt."""
    client = MagicMock()
    client.request.return_value = _Resp(404, {"error": {"code": "not_found", "message": "missing"}})
    monkeypatch.setattr(api.time, "sleep", lambda s: None)

    with pytest.raises(SystemExit):
        api.api_request(client, "GET", "/v1/foo")
    assert client.request.call_count == 1  # no retry


def test_api_request_persists_500_after_one_retry(monkeypatch):
    """Two consecutive 500s → fails. We don't loop indefinitely."""
    client = MagicMock()
    client.request.side_effect = [_Resp(500, "boom"), _Resp(500, "still_boom")]
    monkeypatch.setattr(api.time, "sleep", lambda s: None)

    with pytest.raises(SystemExit):
        api.api_request(client, "GET", "/v1/foo")
    assert client.request.call_count == 2


def test_api_request_persists_connection_error(monkeypatch):
    """Two consecutive connection errors → propagate the second."""
    client = MagicMock()
    client.request.side_effect = [
        httpx.ConnectError("refused"),
        httpx.ConnectError("still refused"),
    ]
    monkeypatch.setattr(api.time, "sleep", lambda s: None)

    with pytest.raises(httpx.ConnectError):
        api.api_request(client, "GET", "/v1/foo")
    assert client.request.call_count == 2
