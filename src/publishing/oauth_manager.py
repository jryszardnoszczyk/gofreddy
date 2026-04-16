"""Multi-platform OAuth2 flow management.

Supports:
1. Device Authorization Grant (RFC 8628) for CLI — TikTok + YouTube only
2. Authorization Code with localhost redirect — LinkedIn
3. App password direct auth — Bluesky (no OAuth)
"""

from __future__ import annotations

import logging
import time
from typing import Any
from uuid import UUID

import httpx

from .config import PublishingSettings
from .exceptions import OAuthFlowError
from .models import DeviceFlowInit, DeviceFlowResult, OAuthTokens

logger = logging.getLogger(__name__)


class OAuthManager:
    """Multi-platform OAuth2 flow management."""

    def __init__(
        self,
        service: Any,  # PublishingService — forward ref to avoid circular import
        settings: PublishingSettings,
        http: httpx.AsyncClient,
    ) -> None:
        self._service = service
        self._settings = settings
        self._http = http
        # In-memory device flow state (acceptable for single-instance Cloud Run)
        self._pending_flows: dict[str, dict[str, Any]] = {}

    # ── Device Flow (RFC 8628) — YouTube + TikTok ─────────────────────────

    async def init_device_flow(
        self, org_id: UUID, platform: str
    ) -> DeviceFlowInit:
        """Start device authorization flow. Returns codes for user to enter."""
        if platform == "youtube":
            return await self._init_youtube_device_flow(org_id)
        elif platform == "tiktok":
            return await self._init_tiktok_device_flow(org_id)
        elif platform == "linkedin":
            raise OAuthFlowError(
                "LinkedIn uses Authorization Code flow, not device flow. "
                "Use the CLI `freddy accounts connect linkedin` command."
            )
        elif platform == "bluesky":
            raise OAuthFlowError(
                "Bluesky uses app passwords, not OAuth. "
                "Use POST /v1/accounts/connect/bluesky with handle + app_password."
            )
        else:
            raise OAuthFlowError(f"Unsupported platform for device flow: {platform}")

    async def poll_device_flow(
        self, org_id: UUID, device_code: str
    ) -> DeviceFlowResult:
        """Poll for device flow completion."""
        flow = self._pending_flows.get(device_code)
        if not flow:
            return DeviceFlowResult(status="expired")

        if flow["org_id"] != org_id:
            return DeviceFlowResult(status="expired")

        if time.monotonic() > flow["expires_at"]:
            self._pending_flows.pop(device_code, None)
            return DeviceFlowResult(status="expired")

        platform = flow["platform"]
        if platform == "youtube":
            return await self._poll_youtube(org_id, device_code, flow)
        elif platform == "tiktok":
            return await self._poll_tiktok(org_id, device_code, flow)

        return DeviceFlowResult(status="expired")

    async def refresh_token(
        self, platform: str, refresh_token: str
    ) -> OAuthTokens:
        """Refresh OAuth tokens for a specific platform."""
        if platform == "youtube":
            return await self._refresh_youtube(refresh_token)
        elif platform == "tiktok":
            return await self._refresh_tiktok(refresh_token)
        elif platform == "linkedin":
            return await self._refresh_linkedin(refresh_token)
        else:
            raise OAuthFlowError(f"Token refresh not supported for {platform}")

    # ── YouTube Device Flow ───────────────────────────────────────────────

    async def _init_youtube_device_flow(self, org_id: UUID) -> DeviceFlowInit:
        client_id = self._settings.youtube_client_id
        if not client_id:
            raise OAuthFlowError("YouTube OAuth not configured (missing client_id)")

        try:
            resp = await self._http.post(
                "https://oauth2.googleapis.com/device/code",
                data={
                    "client_id": client_id,
                    "scope": "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly",
                },
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise OAuthFlowError("YouTube device flow init failed") from exc

        data = resp.json()
        device_code = data["device_code"]
        self._pending_flows[device_code] = {
            "org_id": org_id,
            "platform": "youtube",
            "expires_at": time.monotonic() + data.get("expires_in", 1800),
            "interval": data.get("interval", 5),
        }
        return DeviceFlowInit(
            device_code=device_code,
            user_code=data["user_code"],
            verification_uri=data["verification_url"],
            verification_uri_complete=data.get("verification_url"),
            expires_in=data.get("expires_in", 1800),
            interval=data.get("interval", 5),
        )

    async def _poll_youtube(
        self, org_id: UUID, device_code: str, flow: dict
    ) -> DeviceFlowResult:
        client_id = self._settings.youtube_client_id
        client_secret = self._settings.youtube_client_secret
        if not client_secret:
            raise OAuthFlowError("YouTube OAuth not configured (missing client_secret)")

        try:
            resp = await self._http.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": client_id,
                    "client_secret": client_secret.get_secret_value(),
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                },
            )
        except httpx.HTTPError:
            return DeviceFlowResult(status="pending")

        if resp.status_code == 428 or "authorization_pending" in resp.text:
            return DeviceFlowResult(status="pending")
        if resp.status_code == 403 and "slow_down" in resp.text:
            flow["interval"] = flow.get("interval", 5) + 5
            return DeviceFlowResult(status="pending")

        if resp.status_code == 200:
            data = resp.json()
            connection_id = await self._service.store_oauth_tokens(
                org_id=org_id,
                platform="youtube",
                auth_type="oauth2",
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token"),
                scopes=data.get("scope", "").split(),
                account_id="youtube_user",
                account_name="YouTube Account",
            )
            self._pending_flows.pop(device_code, None)
            return DeviceFlowResult(status="complete", connection_id=connection_id)

        return DeviceFlowResult(status="expired")

    # ── TikTok Device Flow ────────────────────────────────────────────────

    async def _init_tiktok_device_flow(self, org_id: UUID) -> DeviceFlowInit:
        client_key = self._settings.tiktok_client_key
        if not client_key:
            raise OAuthFlowError("TikTok OAuth not configured (missing client_key)")

        try:
            resp = await self._http.post(
                "https://open.tiktokapis.com/v2/oauth/device/authorize/",
                data={
                    "client_key": client_key,
                    "scope": "video.publish,video.upload,video.list",
                },
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise OAuthFlowError("TikTok device flow init failed") from exc

        data = resp.json().get("data", resp.json())
        device_code = data["device_code"]
        self._pending_flows[device_code] = {
            "org_id": org_id,
            "platform": "tiktok",
            "expires_at": time.monotonic() + data.get("expires_in", 900),
            "interval": data.get("interval", 5),
        }
        return DeviceFlowInit(
            device_code=device_code,
            user_code=data["user_code"],
            verification_uri=data.get("verification_url", "https://www.tiktok.com/device"),
            verification_uri_complete=data.get("verification_url_complete"),
            expires_in=data.get("expires_in", 900),
            interval=data.get("interval", 5),
        )

    async def _poll_tiktok(
        self, org_id: UUID, device_code: str, flow: dict
    ) -> DeviceFlowResult:
        client_key = self._settings.tiktok_client_key
        client_secret = self._settings.tiktok_client_secret
        if not client_secret:
            raise OAuthFlowError("TikTok OAuth not configured (missing client_secret)")

        try:
            resp = await self._http.post(
                "https://open.tiktokapis.com/v2/oauth/token/",
                data={
                    "client_key": client_key,
                    "client_secret": client_secret.get_secret_value(),
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                },
            )
        except httpx.HTTPError:
            return DeviceFlowResult(status="pending")

        data = resp.json()
        if data.get("error") == "authorization_pending":
            return DeviceFlowResult(status="pending")
        if data.get("error") == "slow_down":
            flow["interval"] = flow.get("interval", 5) + 5
            return DeviceFlowResult(status="pending")

        if "access_token" in data:
            connection_id = await self._service.store_oauth_tokens(
                org_id=org_id,
                platform="tiktok",
                auth_type="oauth2",
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token"),
                scopes=data.get("scope", "").split(","),
                account_id=data.get("open_id", ""),
                account_name="TikTok Account",
            )
            self._pending_flows.pop(device_code, None)
            return DeviceFlowResult(status="complete", connection_id=connection_id)

        return DeviceFlowResult(status="expired")

    # ── Token Refresh ─────────────────────────────────────────────────────

    async def _refresh_youtube(self, refresh_token: str) -> OAuthTokens:
        client_id = self._settings.youtube_client_id
        client_secret = self._settings.youtube_client_secret
        if not client_secret:
            raise OAuthFlowError("YouTube OAuth not configured")

        resp = await self._http.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret.get_secret_value(),
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
        if resp.status_code != 200:
            raise OAuthFlowError("YouTube token refresh failed")

        data = resp.json()
        return OAuthTokens(
            access_token=data["access_token"],
            refresh_token=refresh_token,  # Google doesn't always return new refresh token
            scopes=data.get("scope", "").split(),
        )

    async def _refresh_tiktok(self, refresh_token: str) -> OAuthTokens:
        client_key = self._settings.tiktok_client_key
        client_secret = self._settings.tiktok_client_secret
        if not client_secret:
            raise OAuthFlowError("TikTok OAuth not configured")

        resp = await self._http.post(
            "https://open.tiktokapis.com/v2/oauth/token/",
            data={
                "client_key": client_key,
                "client_secret": client_secret.get_secret_value(),
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
        if resp.status_code != 200:
            raise OAuthFlowError("TikTok token refresh failed")

        data = resp.json()
        return OAuthTokens(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", refresh_token),
            scopes=data.get("scope", "").split(","),
        )

    async def _refresh_linkedin(self, refresh_token: str) -> OAuthTokens:
        client_id = self._settings.linkedin_client_id
        client_secret = self._settings.linkedin_client_secret
        if not client_secret:
            raise OAuthFlowError("LinkedIn OAuth not configured")

        resp = await self._http.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": client_id,
                "client_secret": client_secret.get_secret_value(),
            },
        )
        if resp.status_code != 200:
            raise OAuthFlowError("LinkedIn token refresh failed")

        data = resp.json()
        return OAuthTokens(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", refresh_token),
            scopes=data.get("scope", "").split(),
        )

    async def refresh_all_expiring(self) -> list[dict[str, Any]]:
        """Refresh all tokens expiring within 60 minutes. For cron use."""
        results: list[dict[str, Any]] = []
        connections = await self._service.get_expiring_tokens(within_minutes=60)

        for conn in connections:
            try:
                creds = await self._service._decrypt_credentials(
                    conn.id, conn.org_id, conn.key_version
                )
                rt = creds.get("refresh_token")
                if not rt:
                    continue

                tokens = await self.refresh_token(conn.platform.value, rt)
                await self._service.refresh_connection_tokens(
                    conn.id,
                    access_token=tokens.access_token,
                    refresh_token=tokens.refresh_token,
                    token_expires_at=tokens.token_expires_at,
                )
                results.append({"connection_id": str(conn.id), "status": "refreshed"})
            except Exception:
                logger.warning(
                    "token_refresh_failed",
                    extra={"connection_id": str(conn.id)},
                    exc_info=True,
                )
                results.append({"connection_id": str(conn.id), "status": "failed"})

        return results
