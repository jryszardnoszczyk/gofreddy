"""Tests for PublishingService OAuth + label + thumbnail methods."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.publishing.config import PublishingSettings
from src.publishing.encryption import decrypt_token, derive_key
from src.publishing.models import (
    AuthType,
    PlatformConnection,
    PublishPlatform,
)
from src.publishing.service import PublishingService


@pytest.fixture
def settings():
    return PublishingSettings(
        enabled=True,
        encryption_secret="test-secret-key-for-publishing",
        max_queue_items_per_org=10,
    )


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    repo._pool = MagicMock()
    return repo


@pytest.fixture
def service(settings, mock_repo):
    return PublishingService(
        repository=mock_repo,
        settings=settings,
    )


def _make_connection(org_id, **kwargs):
    defaults = dict(
        id=uuid4(),
        org_id=org_id,
        platform=PublishPlatform.YOUTUBE,
        auth_type=AuthType.OAUTH2,
        account_id="yt-user",
        account_name="YouTube Account",
        is_active=True,
        scopes=["youtube.upload"],
        key_version=1,
        token_expires_at=None,
        last_used_at=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    defaults.update(kwargs)
    return PlatformConnection(**defaults)


class TestStoreOAuthTokens:
    @pytest.mark.asyncio
    @pytest.mark.mock_required
    async def test_store_oauth_tokens_creates_connection(
        self, service, mock_repo
    ):
        """store_oauth_tokens calls connect_platform and update_connection_token_metadata."""
        org_id = uuid4()
        conn = _make_connection(org_id)
        mock_repo.create_connection.return_value = conn

        expires = datetime.now(timezone.utc) + timedelta(hours=1)
        connection_id = await service.store_oauth_tokens(
            org_id=org_id,
            platform="youtube",
            auth_type="oauth2",
            access_token="ya29.access",
            refresh_token="1//refresh",
            token_expires_at=expires,
            scopes=["youtube.upload"],
            account_id="yt-user",
            account_name="YouTube Account",
        )

        assert connection_id == conn.id
        mock_repo.create_connection.assert_awaited_once()
        mock_repo.update_connection_token_metadata.assert_awaited_once_with(
            conn.id, expires, ["youtube.upload"],
        )

    @pytest.mark.asyncio
    @pytest.mark.mock_required
    async def test_store_oauth_tokens_roundtrip_encryption(
        self, service, mock_repo, settings
    ):
        """Tokens are encrypted via connect_platform and can be decrypted."""
        org_id = uuid4()
        conn = _make_connection(org_id)
        mock_repo.create_connection.return_value = conn

        await service.store_oauth_tokens(
            org_id=org_id,
            platform="youtube",
            auth_type="oauth2",
            access_token="ya29.secret-access",
            refresh_token="1//secret-refresh",
        )

        call_kwargs = mock_repo.create_connection.call_args.kwargs
        enc_blob = call_kwargs["credential_enc"]
        assert isinstance(enc_blob, bytes)

        key = derive_key(settings.encryption_secret.get_secret_value())
        plaintext = decrypt_token(enc_blob, key)
        creds = json.loads(plaintext)
        assert creds["access_token"] == "ya29.secret-access"
        assert creds["refresh_token"] == "1//secret-refresh"


class TestGetExpiringTokens:
    @pytest.mark.asyncio
    @pytest.mark.mock_required
    async def test_get_expiring_tokens(self, service, mock_repo):
        """get_expiring_tokens delegates to repository."""
        conn = _make_connection(uuid4())
        mock_repo.get_expiring_connections.return_value = [conn]

        result = await service.get_expiring_tokens(within_minutes=30)

        assert result == [conn]
        mock_repo.get_expiring_connections.assert_awaited_once_with(30)


class TestRefreshConnectionTokens:
    @pytest.mark.asyncio
    @pytest.mark.mock_required
    async def test_refresh_connection_tokens(self, service, mock_repo, settings):
        """Re-encrypts tokens and calls repository update."""
        conn_id = uuid4()
        expires = datetime.now(timezone.utc) + timedelta(hours=1)

        await service.refresh_connection_tokens(
            connection_id=conn_id,
            access_token="ya29.new-access",
            refresh_token="1//new-refresh",
            token_expires_at=expires,
        )

        mock_repo.update_connection_credentials.assert_awaited_once()
        call_args = mock_repo.update_connection_credentials.call_args
        # connection_id is passed as the first positional arg
        assert call_args[0][0] == conn_id
        call_kwargs = call_args.kwargs
        assert call_kwargs["key_version"] == 1
        assert call_kwargs["token_expires_at"] == expires

        # Verify the encrypted blob decrypts correctly
        key = derive_key(settings.encryption_secret.get_secret_value())
        plaintext = decrypt_token(call_kwargs["credential_enc"], key)
        creds = json.loads(plaintext)
        assert creds["access_token"] == "ya29.new-access"
        assert creds["refresh_token"] == "1//new-refresh"


class TestAddLabels:
    @pytest.mark.asyncio
    @pytest.mark.mock_required
    async def test_add_labels_cleans_input(self, service, mock_repo):
        """Labels are lowercased, stripped, and truncated to 50 chars."""
        item_id = uuid4()
        org_id = uuid4()
        mock_repo.add_labels.return_value = ["campaign", "urgent"]

        result = await service.add_labels(
            item_id, org_id, ["  Campaign  ", "URGENT", "  ", ""]
        )

        assert result == ["campaign", "urgent"]
        # Verify cleaned labels were passed to repo
        call_args = mock_repo.add_labels.call_args
        assert call_args[0][2] == ["campaign", "urgent"]


class TestSetThumbnail:
    @pytest.mark.asyncio
    @pytest.mark.mock_required
    async def test_set_thumbnail_validates_url(self, service, mock_repo):
        """set_thumbnail calls resolve_and_validate for SSRF protection."""
        item_id = uuid4()
        org_id = uuid4()
        mock_repo.update_queue_item.return_value = MagicMock()

        with patch(
            "src.common.url_validation.resolve_and_validate",
            new_callable=AsyncMock,
        ) as mock_validate:
            await service.set_thumbnail(
                item_id, org_id, "https://cdn.example.com/thumb.jpg"
            )

            mock_validate.assert_awaited_once_with(
                "https://cdn.example.com/thumb.jpg"
            )
            mock_repo.update_queue_item.assert_awaited_once_with(
                item_id, org_id, thumbnail_url="https://cdn.example.com/thumb.jpg",
            )
