"""Tests for OAuthManager — device flow + token refresh with mocked HTTP."""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest
import respx

from src.publishing.config import PublishingSettings
from src.publishing.oauth_manager import OAuthManager


@pytest.fixture
def settings():
    return PublishingSettings(
        enabled=True,
        encryption_secret="test-secret-key-for-publishing",
        youtube_client_id="yt-client-id",
        youtube_client_secret="yt-client-secret",
        tiktok_client_key="tt-client-key",
        tiktok_client_secret="tt-client-secret",
    )


@pytest.fixture
def mock_service():
    svc = AsyncMock()
    svc.store_oauth_tokens.return_value = uuid4()
    return svc


@pytest.fixture
def oauth_manager(mock_service, settings):
    client = httpx.AsyncClient()
    return OAuthManager(service=mock_service, settings=settings, http=client)


class TestInitDeviceFlow:
    @pytest.mark.asyncio
    @pytest.mark.mock_required
    @respx.mock
    async def test_init_youtube_device_flow(self, oauth_manager):
        """YouTube device flow returns DeviceFlowInit with codes."""
        respx.post("https://oauth2.googleapis.com/device/code").mock(
            return_value=httpx.Response(
                200,
                json={
                    "device_code": "dev-code-123",
                    "user_code": "ABCD-EFGH",
                    "verification_url": "https://www.google.com/device",
                    "expires_in": 1800,
                    "interval": 5,
                },
            )
        )

        org_id = uuid4()
        result = await oauth_manager.init_device_flow(org_id, "youtube")

        assert result.device_code == "dev-code-123"
        assert result.user_code == "ABCD-EFGH"
        assert result.verification_uri == "https://www.google.com/device"
        assert result.expires_in == 1800
        assert result.interval == 5

    @pytest.mark.asyncio
    @pytest.mark.mock_required
    @respx.mock
    async def test_init_tiktok_device_flow(self, oauth_manager):
        """TikTok device flow returns DeviceFlowInit with codes."""
        respx.post(
            "https://open.tiktokapis.com/v2/oauth/device/authorize/"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "device_code": "tt-dev-code",
                        "user_code": "TTCODE",
                        "verification_url": "https://www.tiktok.com/device",
                        "verification_url_complete": "https://www.tiktok.com/device?user_code=TTCODE",
                        "expires_in": 900,
                        "interval": 5,
                    }
                },
            )
        )

        org_id = uuid4()
        result = await oauth_manager.init_device_flow(org_id, "tiktok")

        assert result.device_code == "tt-dev-code"
        assert result.user_code == "TTCODE"
        assert result.verification_uri == "https://www.tiktok.com/device"
        assert result.verification_uri_complete == "https://www.tiktok.com/device?user_code=TTCODE"
        assert result.expires_in == 900
        assert result.interval == 5


class TestPollDeviceFlow:
    @pytest.mark.asyncio
    @pytest.mark.mock_required
    @respx.mock
    async def test_poll_device_flow_pending(self, oauth_manager):
        """Pending status when authorization_pending returned by Google."""
        # First init a flow to register the device_code
        respx.post("https://oauth2.googleapis.com/device/code").mock(
            return_value=httpx.Response(
                200,
                json={
                    "device_code": "pending-code",
                    "user_code": "PEND-CODE",
                    "verification_url": "https://www.google.com/device",
                    "expires_in": 1800,
                    "interval": 5,
                },
            )
        )
        org_id = uuid4()
        await oauth_manager.init_device_flow(org_id, "youtube")

        # Mock the token poll endpoint to return authorization_pending
        respx.post("https://oauth2.googleapis.com/token").mock(
            return_value=httpx.Response(
                428,
                json={"error": "authorization_pending"},
            )
        )

        result = await oauth_manager.poll_device_flow(org_id, "pending-code")
        assert result.status == "pending"
        assert result.connection_id is None

    @pytest.mark.asyncio
    @pytest.mark.mock_required
    async def test_poll_device_flow_expired(self, oauth_manager):
        """Expired status when device_code is not in pending flows."""
        org_id = uuid4()
        result = await oauth_manager.poll_device_flow(
            org_id, "nonexistent-code"
        )
        assert result.status == "expired"
        assert result.connection_id is None


class TestRefreshToken:
    @pytest.mark.asyncio
    @pytest.mark.mock_required
    @respx.mock
    async def test_refresh_youtube_token(self, oauth_manager):
        """YouTube refresh returns OAuthTokens with access_token and scopes."""
        respx.post("https://oauth2.googleapis.com/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "ya29.refreshed-token",
                    "expires_in": 3600,
                    "scope": "https://www.googleapis.com/auth/youtube.upload",
                    "token_type": "Bearer",
                },
            )
        )

        result = await oauth_manager.refresh_token(
            "youtube", "1//old-refresh-token"
        )

        assert result.access_token == "ya29.refreshed-token"
        # Google doesn't always return a new refresh token; original is preserved
        assert result.refresh_token == "1//old-refresh-token"
        assert "https://www.googleapis.com/auth/youtube.upload" in result.scopes
