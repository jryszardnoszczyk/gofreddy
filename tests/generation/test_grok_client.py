"""Tests for GrokImagineClient."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.generation.grok_client import (
    ClipResult,
    GrokAPIUnavailableError,
    GrokImagineClient,
    GrokModerationBlockedError,
)
from src.generation.config import GenerationSettings
from src.generation.exceptions import GenerationError, GenerationTimeoutError


def _make_settings(**overrides) -> GenerationSettings:
    defaults = {
        "xai_api_key": "test-key",
        "generation_enabled": True,
        "poll_interval_seconds": 0.01,
        "poll_timeout_seconds": 1.0,
        "max_generation_deadline_seconds": 10,
    }
    defaults.update(overrides)
    return GenerationSettings(**defaults)


class TestClipResult:
    def test_fields(self):
        r = ClipResult(url="https://test.x.ai/video.mp4", request_id="req-123")
        assert r.url == "https://test.x.ai/video.mp4"
        assert r.request_id == "req-123"


class TestCircuitBreaker:
    def test_reset(self):
        client = GrokImagineClient(_make_settings())
        client._consecutive_failures = 5
        client.reset_circuit_breaker()
        assert client._consecutive_failures == 0

    def test_trips_at_threshold(self):
        client = GrokImagineClient(_make_settings())
        client._consecutive_failures = 3
        with pytest.raises(GrokAPIUnavailableError):
            client._check_circuit_breaker()

    def test_ok_below_threshold(self):
        client = GrokImagineClient(_make_settings())
        client._consecutive_failures = 2
        client._check_circuit_breaker()  # Should not raise


class TestSSRFValidation:
    """Test download_video SSRF protection layers."""

    @pytest.fixture
    def client(self):
        c = GrokImagineClient(_make_settings())
        c._http = AsyncMock()
        return c

    @pytest.mark.asyncio
    async def test_rejects_non_allowlisted_domain(self, client, tmp_path):
        dest = tmp_path / "out.mp4"
        with pytest.raises(GenerationError, match="not in allowlist"):
            await client.download_video("https://evil.com/video.mp4", dest)

    @pytest.mark.asyncio
    async def test_rejects_private_ip(self, client, tmp_path):
        dest = tmp_path / "out.mp4"
        with patch("src.common.url_validation.resolve_and_validate") as mock_resolve:
            mock_resolve.side_effect = ValueError("All resolved IPs are in blocked ranges")
            with pytest.raises(GenerationError, match="SSRF"):
                await client.download_video("https://cdn.x.ai/video.mp4", dest)

    @pytest.mark.asyncio
    async def test_rejects_redirect(self, client, tmp_path):
        dest = tmp_path / "out.mp4"
        with patch("src.common.url_validation.resolve_and_validate") as mock_resolve:
            mock_resolve.return_value = ("1.2.3.4", "cdn.x.ai")
            mock_response = AsyncMock()
            mock_response.status_code = 302
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            client._http.stream = MagicMock(return_value=mock_response)
            with pytest.raises(GenerationError, match="status"):
                await client.download_video("https://cdn.x.ai/video.mp4", dest)

    @pytest.mark.asyncio
    async def test_rejects_wrong_content_type(self, client, tmp_path):
        dest = tmp_path / "out.mp4"
        with patch("src.common.url_validation.resolve_and_validate") as mock_resolve:
            mock_resolve.return_value = ("1.2.3.4", "cdn.x.ai")
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "text/html", "content-length": "100"}
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            client._http.stream = MagicMock(return_value=mock_response)
            with pytest.raises(GenerationError, match="content-type"):
                await client.download_video("https://cdn.x.ai/video.mp4", dest)

    @pytest.mark.asyncio
    async def test_rejects_oversized_content_length(self, client, tmp_path):
        dest = tmp_path / "out.mp4"
        with patch("src.common.url_validation.resolve_and_validate") as mock_resolve:
            mock_resolve.return_value = ("1.2.3.4", "cdn.x.ai")
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.headers = {
                "content-type": "video/mp4",
                "content-length": str(200 * 1024 * 1024),  # 200MB
            }
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            client._http.stream = MagicMock(return_value=mock_response)
            with pytest.raises(GenerationError, match="exceeds max"):
                await client.download_video("https://cdn.x.ai/video.mp4", dest)

    @pytest.mark.asyncio
    async def test_falls_back_to_hostname_on_tls_handshake_failure(self, client, tmp_path):
        dest = tmp_path / "out.mp4"
        with patch("src.common.url_validation.resolve_and_validate") as mock_resolve:
            mock_resolve.return_value = ("1.2.3.4", "cdn.x.ai")

            async def _chunks():
                yield b"test"

            ok_response = AsyncMock()
            ok_response.status_code = 200
            ok_response.headers = {"content-type": "video/mp4", "content-length": "4"}
            ok_response.aiter_bytes = MagicMock(return_value=_chunks())
            ok_response.__aenter__ = AsyncMock(return_value=ok_response)
            ok_response.__aexit__ = AsyncMock(return_value=None)

            ssl_error = httpx.ConnectError(
                "[SSL: SSLV3_ALERT_HANDSHAKE_FAILURE] sslv3 alert handshake failure",
                request=httpx.Request("GET", "https://1.2.3.4/video.mp4"),
            )
            client._http.stream = MagicMock(side_effect=[ssl_error, ok_response])

            await client.download_video("https://cdn.x.ai/video.mp4", dest)

            assert client._http.stream.call_count == 2
            first_url = client._http.stream.call_args_list[0].args[1]
            second_url = client._http.stream.call_args_list[1].args[1]
            assert first_url.startswith("https://1.2.3.4/")
            assert second_url.startswith("https://cdn.x.ai/")
            assert dest.read_bytes() == b"test"


class TestDomainAllowlist:
    def test_allows_x_ai_domain(self):
        assert GrokImagineClient._ALLOWED_DOMAINS_RE.match("https://cdn.x.ai/video.mp4")

    def test_allows_subdomain(self):
        assert GrokImagineClient._ALLOWED_DOMAINS_RE.match("https://video-gen.x.ai/output/123.mp4")

    def test_rejects_non_x_ai(self):
        assert not GrokImagineClient._ALLOWED_DOMAINS_RE.match("https://evil.com/video.mp4")

    def test_rejects_partial_domain(self):
        assert not GrokImagineClient._ALLOWED_DOMAINS_RE.match("https://notx.ai/video.mp4")

    def test_rejects_http(self):
        assert not GrokImagineClient._ALLOWED_DOMAINS_RE.match("http://cdn.x.ai/video.mp4")
