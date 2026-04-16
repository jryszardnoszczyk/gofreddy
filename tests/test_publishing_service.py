"""Tests for PublishingService — unit tests with mocked repository."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from src.publishing.config import PublishingSettings
from src.publishing.exceptions import (
    ConnectionNotFoundError,
    QueueItemNotFoundError,
    QueueLimitExceededError,
)
from src.publishing.models import (
    AuthType,
    PlatformConnection,
    PublishPlatform,
    PublishStatus,
    QueueItem,
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
def mock_adapter():
    adapter = AsyncMock()
    adapter.platform = PublishPlatform.WORDPRESS
    return adapter


@pytest.fixture
def service(settings, mock_repo, mock_adapter):
    return PublishingService(
        repository=mock_repo,
        settings=settings,
        publishers={PublishPlatform.WORDPRESS: mock_adapter},
    )


def _make_connection(org_id: UUID, **kwargs) -> PlatformConnection:
    defaults = dict(
        id=uuid4(),
        org_id=org_id,
        platform=PublishPlatform.WORDPRESS,
        auth_type=AuthType.APP_PASSWORD,
        account_id="test-site",
        account_name="Test Site",
        is_active=True,
        scopes=[],
        key_version=1,
        token_expires_at=None,
        last_used_at=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    defaults.update(kwargs)
    return PlatformConnection(**defaults)


def _make_queue_item(org_id: UUID, **kwargs) -> QueueItem:
    defaults = dict(
        id=uuid4(),
        org_id=org_id,
        client_id=None,
        platform="wordpress",
        connection_id=uuid4(),
        content_parts=[{"body": "Hello world"}],
        media=[],
        first_comment=None,
        thumbnail_url=None,
        og_title=None,
        og_description=None,
        og_image_url=None,
        twitter_card_type=None,
        canonical_url=None,
        slug=None,
        labels=[],
        group_id=None,
        newsletter_subject=None,
        newsletter_segment=None,
        status=PublishStatus.DRAFT,
        approved_at=None,
        approved_by=None,
        scheduled_at=None,
        external_id=None,
        external_url=None,
        error_message=None,
        retry_count=0,
        metadata={},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    defaults.update(kwargs)
    return QueueItem(**defaults)


class TestCreateDraft:
    @pytest.mark.asyncio
    async def test_enforces_quota(self, service, mock_repo):
        mock_repo.count_queue_items.return_value = 10  # at limit
        with pytest.raises(QueueLimitExceededError):
            await service.create_draft(
                org_id=uuid4(),
                platform="wordpress",
                connection_id=uuid4(),
                content_parts=[{"body": "test"}],
            )

    @pytest.mark.asyncio
    async def test_validates_connection(self, service, mock_repo):
        mock_repo.count_queue_items.return_value = 0
        mock_repo.get_connection.return_value = None
        with pytest.raises(ConnectionNotFoundError):
            await service.create_draft(
                org_id=uuid4(),
                platform="wordpress",
                connection_id=uuid4(),
                content_parts=[{"body": "test"}],
            )

    @pytest.mark.asyncio
    async def test_success(self, service, mock_repo):
        org_id = uuid4()
        conn = _make_connection(org_id)
        item = _make_queue_item(org_id)
        mock_repo.count_queue_items.return_value = 0
        mock_repo.get_connection.return_value = conn
        mock_repo.create_queue_item.return_value = item

        result = await service.create_draft(
            org_id=org_id,
            platform="wordpress",
            connection_id=conn.id,
            content_parts=[{"body": "test"}],
        )
        assert result.id == item.id


class TestSchedule:
    @pytest.mark.asyncio
    async def test_rejects_past_datetime(self, service):
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        with pytest.raises(ValueError, match="future"):
            await service.schedule(uuid4(), uuid4(), past)

    @pytest.mark.asyncio
    async def test_rejects_unapproved(self, service, mock_repo):
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_repo.schedule_item.return_value = None
        with pytest.raises(QueueItemNotFoundError):
            await service.schedule(uuid4(), uuid4(), future)


class TestConnectPlatform:
    @pytest.mark.asyncio
    async def test_encrypts_credentials(self, service, mock_repo, settings):
        org_id = uuid4()
        conn = _make_connection(org_id)
        mock_repo.create_connection.return_value = conn

        await service.connect_platform(
            org_id=org_id,
            platform="wordpress",
            auth_type="app_password",
            credentials={"site_url": "https://example.com", "username": "admin", "app_password": "xxxx"},
            account_id="test",
        )

        # Verify create_connection was called with encrypted bytes
        call_kwargs = mock_repo.create_connection.call_args
        assert call_kwargs.kwargs.get("credential_enc") is not None
        enc_bytes = call_kwargs.kwargs["credential_enc"]
        assert isinstance(enc_bytes, bytes)
        assert len(enc_bytes) > 12  # nonce + ciphertext


class TestCancel:
    @pytest.mark.asyncio
    async def test_cancel_success(self, service, mock_repo):
        org_id = uuid4()
        item = _make_queue_item(org_id, status=PublishStatus.CANCELLED)
        mock_repo.cancel_item.return_value = item

        result = await service.cancel(item.id, org_id)
        assert result.status == PublishStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_not_found(self, service, mock_repo):
        mock_repo.cancel_item.return_value = None
        with pytest.raises(QueueItemNotFoundError):
            await service.cancel(uuid4(), uuid4())
