"""Tests for PublishDispatcher."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.publishing.config import PublishingSettings
from src.publishing.dispatcher import PublishDispatcher
from src.publishing.models import PublishResult, PublishStatus, QueueItem


@pytest.fixture
def settings():
    return PublishingSettings(
        enabled=True,
        encryption_secret="test-secret-key-for-publishing",
        dispatch_batch_size=10,
        dispatch_deadline_seconds=200,
    )


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def mock_service():
    return AsyncMock()


@pytest.fixture
def dispatcher(mock_service, mock_repo, settings):
    return PublishDispatcher(
        service=mock_service, repository=mock_repo, settings=settings
    )


def _make_item(**kwargs) -> QueueItem:
    defaults = dict(
        id=uuid4(), org_id=uuid4(), client_id=None, platform="wordpress",
        connection_id=uuid4(), content_parts=[{"body": "test"}],
        media=[], first_comment=None, thumbnail_url=None,
        og_title=None, og_description=None, og_image_url=None,
        twitter_card_type=None, canonical_url=None, slug=None,
        labels=[], group_id=None, newsletter_subject=None,
        newsletter_segment=None, status=PublishStatus.PUBLISHING,
        approved_at=datetime.now(timezone.utc), approved_by=uuid4(),
        scheduled_at=datetime.now(timezone.utc), external_id=None,
        external_url=None, error_message=None, retry_count=0,
        metadata={}, created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    defaults.update(kwargs)
    return QueueItem(**defaults)


class TestDispatcher:
    @pytest.mark.asyncio
    async def test_empty_queue(self, dispatcher, mock_repo, mock_service):
        mock_repo.reap_stale_publishing_items.return_value = 0
        mock_repo.claim_scheduled_items.return_value = []

        result = await dispatcher.dispatch()

        assert result == {"dispatched": 0, "published": 0, "failed": 0}

    @pytest.mark.asyncio
    async def test_dispatches_and_publishes(self, dispatcher, mock_repo, mock_service):
        items = [_make_item(), _make_item()]
        mock_repo.reap_stale_publishing_items.return_value = 0
        mock_repo.claim_scheduled_items.return_value = items
        mock_service.publish_item.return_value = PublishResult(success=True, external_id="1")

        result = await dispatcher.dispatch()

        assert result["dispatched"] == 2
        assert result["published"] == 2
        assert result["failed"] == 0
        assert mock_service.publish_item.call_count == 2

    @pytest.mark.asyncio
    async def test_handles_failures(self, dispatcher, mock_repo, mock_service):
        items = [_make_item()]
        mock_repo.reap_stale_publishing_items.return_value = 0
        mock_repo.claim_scheduled_items.return_value = items
        mock_service.publish_item.return_value = PublishResult(
            success=False, error_message="adapter error"
        )

        result = await dispatcher.dispatch()

        assert result["failed"] == 1
        assert result["published"] == 0

    @pytest.mark.asyncio
    async def test_handles_exceptions(self, dispatcher, mock_repo, mock_service):
        items = [_make_item()]
        mock_repo.reap_stale_publishing_items.return_value = 0
        mock_repo.claim_scheduled_items.return_value = items
        mock_service.publish_item.side_effect = RuntimeError("unexpected")

        result = await dispatcher.dispatch()

        assert result["failed"] == 1
        mock_repo.mark_failed.assert_called_once()

    @pytest.mark.asyncio
    async def test_reaps_stale_items(self, dispatcher, mock_repo, mock_service):
        mock_repo.reap_stale_publishing_items.return_value = 3
        mock_repo.claim_scheduled_items.return_value = []

        await dispatcher.dispatch()

        mock_repo.reap_stale_publishing_items.assert_called_once()

    @pytest.mark.asyncio
    async def test_deadline_stops_processing(self, dispatcher, mock_repo, mock_service):
        items = [_make_item() for _ in range(5)]
        mock_repo.reap_stale_publishing_items.return_value = 0
        mock_repo.claim_scheduled_items.return_value = items

        # Set deadline to negative to trigger immediate stop
        dispatcher._settings = PublishingSettings(
            enabled=True,
            encryption_secret="test-secret-key-for-publishing",
            dispatch_deadline_seconds=-1,
        )

        result = await dispatcher.dispatch()

        # Should have stopped before processing all items
        assert result["dispatched"] == 5
        assert mock_service.publish_item.call_count < 5
