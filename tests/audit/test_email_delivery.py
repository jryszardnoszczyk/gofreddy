"""L4 #7 Resend email delivery tests."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.audit.email_delivery import DEFAULT_FROM, RESEND_ENDPOINT, send_email


@pytest.fixture
def with_key(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_test_2026")
    monkeypatch.delenv("EMAIL_FROM", raising=False)


@pytest.fixture
def no_key(monkeypatch):
    monkeypatch.delenv("RESEND_API_KEY", raising=False)


def _ok_response(email_id: str = "email_xyz") -> MagicMock:
    r = MagicMock()
    r.json.return_value = {"id": email_id}
    r.raise_for_status.return_value = None
    return r


def test_send_email_returns_id_on_success(with_key):
    with patch("src.audit.email_delivery.httpx.post", return_value=_ok_response()) as mock:
        result = send_email("buyer@example.com", "subj", "<p>hi</p>")
    assert result == "email_xyz"
    args, kwargs = mock.call_args
    assert args[0] == RESEND_ENDPOINT
    assert kwargs["headers"]["Authorization"] == "Bearer re_test_2026"
    payload = kwargs["json"]
    assert payload["from"] == DEFAULT_FROM
    assert payload["to"] == ["buyer@example.com"]
    assert payload["subject"] == "subj"
    assert payload["html"] == "<p>hi</p>"


def test_send_email_accepts_list_of_recipients(with_key):
    with patch("src.audit.email_delivery.httpx.post", return_value=_ok_response()) as mock:
        send_email(["a@x.com", "b@x.com"], "s", "<p>h</p>")
    payload = mock.call_args[1]["json"]
    assert payload["to"] == ["a@x.com", "b@x.com"]


def test_send_email_includes_text_when_provided(with_key):
    with patch("src.audit.email_delivery.httpx.post", return_value=_ok_response()) as mock:
        send_email("a@x.com", "s", "<p>h</p>", text="plain")
    assert mock.call_args[1]["json"]["text"] == "plain"


def test_send_email_omits_text_when_not_provided(with_key):
    with patch("src.audit.email_delivery.httpx.post", return_value=_ok_response()) as mock:
        send_email("a@x.com", "s", "<p>h</p>")
    assert "text" not in mock.call_args[1]["json"]


def test_send_email_honors_from_override(with_key):
    with patch("src.audit.email_delivery.httpx.post", return_value=_ok_response()) as mock:
        send_email("a@x.com", "s", "<p>h</p>", from_addr="Custom <c@x.com>")
    assert mock.call_args[1]["json"]["from"] == "Custom <c@x.com>"


def test_send_email_uses_email_from_env(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    monkeypatch.setenv("EMAIL_FROM", "Override <o@x.com>")
    with patch("src.audit.email_delivery.httpx.post", return_value=_ok_response()) as mock:
        send_email("a@x.com", "s", "<p>h</p>")
    assert mock.call_args[1]["json"]["from"] == "Override <o@x.com>"


def test_send_email_returns_empty_when_api_key_missing(no_key):
    with patch("src.audit.email_delivery.httpx.post") as mock:
        result = send_email("a@x.com", "s", "<p>h</p>")
    assert result == ""
    mock.assert_not_called()


def test_send_email_swallows_http_errors(with_key):
    with patch("src.audit.email_delivery.httpx.post", side_effect=Exception("network down")):
        result = send_email("a@x.com", "s", "<p>h</p>")
    assert result == ""


def test_send_email_handles_4xx_response(with_key):
    bad = MagicMock()
    bad.raise_for_status.side_effect = Exception("422 Unprocessable")
    with patch("src.audit.email_delivery.httpx.post", return_value=bad):
        result = send_email("a@x.com", "s", "<p>h</p>")
    assert result == ""


def test_send_email_returns_empty_when_response_lacks_id(with_key):
    weird = MagicMock()
    weird.json.return_value = {"some_other_field": "value"}
    weird.raise_for_status.return_value = None
    with patch("src.audit.email_delivery.httpx.post", return_value=weird):
        result = send_email("a@x.com", "s", "<p>h</p>")
    assert result == ""
