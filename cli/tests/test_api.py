"""Tests for CLI API client."""

import json

import httpx
import pytest

from freddy.api import CLIError, api_request, log_action_to_session, make_client
from freddy.config import Config


class TestMakeClient:

    def test_creates_client_with_api_key(self):
        config = Config(api_key="vi_sk_test", base_url="http://localhost:8080")
        client = make_client(config)
        assert client.headers["x-api-key"] == "vi_sk_test"
        assert client.headers["user-agent"] == "freddy-cli/0.1"

    def test_base_url_trailing_slash_stripped(self):
        config = Config(api_key="vi_sk_test", base_url="http://localhost:8080/")
        client = make_client(config)
        assert str(client.base_url) == "http://localhost:8080"


class TestApiRequest:

    def test_successful_request(self, httpx_mock):
        config = Config(api_key="vi_sk_test", base_url="http://localhost:8080")
        client = make_client(config)
        httpx_mock.add_response(
            url="http://localhost:8080/v1/usage",
            json={"credits": 100},
        )
        result = api_request(client, "GET", "/v1/usage")
        assert result == {"credits": 100}

    def test_error_response_exits(self, httpx_mock):
        config = Config(api_key="vi_sk_test", base_url="http://localhost:8080")
        client = make_client(config)
        httpx_mock.add_response(
            url="http://localhost:8080/v1/usage",
            status_code=401,
            json={"error": {"code": "unauthorized", "message": "Bad key"}},
        )
        with pytest.raises(SystemExit):
            api_request(client, "GET", "/v1/usage")

    def test_filters_none_params(self, httpx_mock):
        config = Config(api_key="vi_sk_test", base_url="http://localhost:8080")
        client = make_client(config)
        httpx_mock.add_response(
            url="http://localhost:8080/v1/search?platform=tiktok",
            json={"results": []},
        )
        result = api_request(
            client, "GET", "/v1/search",
            params={"platform": "tiktok", "query": None},
        )
        assert result == {"results": []}


class TestLogAction:

    def test_logging_success(self, httpx_mock):
        config = Config(api_key="vi_sk_test", base_url="http://localhost:8080")
        client = make_client(config)
        httpx_mock.add_response(
            url="http://localhost:8080/v1/sessions/abc-123/actions",
            status_code=201,
            json={"id": "action-1"},
        )
        # Should not raise
        log_action_to_session(client, "abc-123", "creator.search")

    def test_logging_failure_is_non_fatal(self, httpx_mock):
        config = Config(api_key="vi_sk_test", base_url="http://localhost:8080")
        client = make_client(config)
        httpx_mock.add_response(
            url="http://localhost:8080/v1/sessions/abc-123/actions",
            status_code=500,
            json={"error": {"code": "internal", "message": "fail"}},
        )
        httpx_mock.add_response(
            url="http://localhost:8080/v1/sessions/abc-123/actions",
            status_code=500,
            json={"error": {"code": "internal", "message": "fail"}},
        )
        # Should not raise — non-fatal
        log_action_to_session(client, "abc-123", "creator.search")
