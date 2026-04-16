"""Tests for MonitoringService skeleton."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.monitoring.config import MonitoringSettings
from src.monitoring.exceptions import MonitorLimitExceededError, MonitorNotFoundError, MonitoringError
from src.monitoring.models import DataSource, Monitor, RawMention
from src.monitoring.service import MonitoringService


def _make_monitor(**kwargs):
    from datetime import datetime, timezone

    defaults = dict(
        id=uuid4(),
        user_id=uuid4(),
        name="Test",
        keywords=["x"],
        boolean_query=None,
        sources=[DataSource.TWITTER],
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    defaults.update(kwargs)
    return Monitor(**defaults)


@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.count_monitors = AsyncMock(return_value=0)
    repo.create_monitor = AsyncMock(side_effect=lambda **kw: _make_monitor(**kw))
    repo.get_monitor = AsyncMock(return_value=_make_monitor())
    repo.list_monitors = AsyncMock(return_value=[_make_monitor()])
    repo.delete_monitor = AsyncMock(return_value=True)
    repo.insert_mentions = AsyncMock(return_value=5)
    repo.insert_mentions_and_advance_cursor = AsyncMock(return_value=3)
    repo.get_mentions = AsyncMock(return_value=[])
    repo.search_mentions = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def settings():
    return MonitoringSettings(
        max_monitors_per_user=3,
        max_sources_per_monitor=2,
        max_mentions_per_ingest=5,
    )


@pytest.fixture
def service(mock_repo, settings):
    # Provide fetchers so source validation passes for TWITTER
    from src.monitoring.fetcher_protocol import MentionFetcher
    mock_fetcher = MagicMock(spec=MentionFetcher)
    return MonitoringService(
        repository=mock_repo,
        settings=settings,
        mention_fetchers={DataSource.TWITTER: mock_fetcher},
    )


class TestCreateMonitor:
    @pytest.mark.asyncio
    async def test_create_success(self, service, mock_repo):
        uid = uuid4()
        monitor = await service.create_monitor(
            user_id=uid,
            name="My Monitor",
            keywords=["brand"],
            sources=[DataSource.TWITTER],
        )
        assert monitor is not None
        mock_repo.create_monitor.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_exceeds_monitor_limit(self, service, mock_repo, settings):
        mock_repo.count_monitors.return_value = settings.max_monitors_per_user
        with pytest.raises(MonitorLimitExceededError, match="Maximum 3"):
            await service.create_monitor(
                user_id=uuid4(),
                name="Extra",
                keywords=["x"],
                sources=[DataSource.TWITTER],
            )

    @pytest.mark.asyncio
    async def test_create_exceeds_source_limit(self, service, settings):
        with pytest.raises(MonitorLimitExceededError, match="Maximum 2"):
            await service.create_monitor(
                user_id=uuid4(),
                name="TooManySources",
                keywords=["x"],
                sources=[DataSource.TWITTER, DataSource.REDDIT, DataSource.INSTAGRAM],
            )

    @pytest.mark.asyncio
    async def test_create_rejects_unavailable_source(self, service):
        """Sources without a runtime adapter are rejected."""
        with pytest.raises(MonitoringError, match="Sources not available"):
            await service.create_monitor(
                user_id=uuid4(),
                name="BadSource",
                keywords=["x"],
                sources=[DataSource.REDDIT],  # No fetcher registered for REDDIT
            )


class TestGetMonitor:
    @pytest.mark.asyncio
    async def test_found(self, service):
        monitor = await service.get_monitor(uuid4(), uuid4())
        assert monitor is not None

    @pytest.mark.asyncio
    async def test_not_found_raises(self, service, mock_repo):
        mock_repo.get_monitor.return_value = None
        with pytest.raises(MonitorNotFoundError):
            await service.get_monitor(uuid4(), uuid4())


class TestIngestMentions:
    @pytest.mark.asyncio
    async def test_batch_capping(self, service, mock_repo, settings):
        # Create more mentions than max_mentions_per_ingest
        raw = [
            RawMention(source=DataSource.TWITTER, source_id=str(i))
            for i in range(10)
        ]
        await service.ingest_mentions(
            monitor_id=uuid4(),
            raw_mentions=raw,
            source=DataSource.TWITTER,
        )
        # Should have capped to 5
        call_args = mock_repo.insert_mentions.call_args
        assert len(call_args[0][1]) == settings.max_mentions_per_ingest

    @pytest.mark.asyncio
    async def test_with_cursor_advance(self, service, mock_repo):
        raw = [RawMention(source=DataSource.TWITTER, source_id="1")]
        result = await service.ingest_mentions(
            monitor_id=uuid4(),
            raw_mentions=raw,
            source=DataSource.TWITTER,
            cursor_value="next_page",
        )
        mock_repo.insert_mentions_and_advance_cursor.assert_awaited_once()
        assert result == 3

    @pytest.mark.asyncio
    async def test_without_cursor(self, service, mock_repo):
        raw = [RawMention(source=DataSource.TWITTER, source_id="1")]
        result = await service.ingest_mentions(
            monitor_id=uuid4(),
            raw_mentions=raw,
            source=DataSource.TWITTER,
        )
        mock_repo.insert_mentions.assert_awaited_once()
        assert result == 5


class TestListAndDelete:
    @pytest.mark.asyncio
    async def test_list(self, service, mock_repo):
        result = await service.list_monitors(uuid4())
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_delete(self, service, mock_repo):
        result = await service.delete_monitor(uuid4(), uuid4())
        assert result is True


class TestGetMentionAggregates:
    @pytest.mark.asyncio
    async def test_passes_date_range(self, service, mock_repo):
        from datetime import datetime, timezone
        mock_repo.get_mention_aggregates = AsyncMock(return_value={
            "source_breakdown": {}, "sentiment_breakdown": {},
            "top_authors": [], "total_engagement": 0,
        })
        mid = uuid4()
        uid = uuid4()
        d_from = datetime(2026, 3, 10, tzinfo=timezone.utc)
        d_to = datetime(2026, 3, 17, tzinfo=timezone.utc)
        await service.get_mention_aggregates(mid, uid, date_from=d_from, date_to=d_to)
        mock_repo.get_mention_aggregates.assert_awaited_once_with(
            mid, uid, date_from=d_from, date_to=d_to,
        )


class TestListAlertEvents:
    @pytest.mark.asyncio
    async def test_passes_date_range(self, service, mock_repo):
        from datetime import datetime, timezone
        mock_repo.list_alert_events = AsyncMock(return_value=[])
        mid = uuid4()
        uid = uuid4()
        d_from = datetime(2026, 3, 10, tzinfo=timezone.utc)
        d_to = datetime(2026, 3, 17, tzinfo=timezone.utc)
        await service.list_alert_events(mid, uid, date_from=d_from, date_to=d_to)
        mock_repo.list_alert_events.assert_awaited_once_with(
            mid, uid, 25, 0, date_from=d_from, date_to=d_to,
        )


class TestGetSentimentBySource:
    @pytest.mark.asyncio
    async def test_delegates_with_idor_check(self, service, mock_repo):
        from datetime import datetime, timezone
        from src.monitoring.models import SourceSentiment
        mock_repo.get_sentiment_by_source = AsyncMock(return_value=[])
        mid = uuid4()
        uid = uuid4()
        d_from = datetime(2026, 3, 10, tzinfo=timezone.utc)
        result = await service.get_sentiment_by_source(mid, uid, date_from=d_from)
        mock_repo.get_monitor.assert_awaited()  # IDOR check
        mock_repo.get_sentiment_by_source.assert_awaited_once_with(
            mid, date_from=d_from, date_to=None,
        )


class TestSearchMentions:
    @pytest.mark.asyncio
    async def test_search_delegates_to_repo(self, service, mock_repo):
        mock_repo.search_mentions = AsyncMock(return_value=([], 0))
        mid = uuid4()
        uid = uuid4()
        await service.search_mentions(uid, mid, "query")
        # IDOR enforced by repo JOIN — no separate get_monitor call
        mock_repo.get_monitor.assert_not_awaited()
        mock_repo.search_mentions.assert_awaited_once_with(
            uid, mid, "query",
            date_from=None, date_to=None,
            limit=50, offset=0,
        )
