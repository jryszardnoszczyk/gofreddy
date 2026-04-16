"""Tests for MentionFetcher protocol and BaseMentionFetcher ABC."""

import asyncio

import pytest

from src.monitoring.config import MonitoringSettings
from src.monitoring.exceptions import MentionFetchError
from src.monitoring.fetcher_protocol import BaseMentionFetcher
from src.monitoring.models import DataSource, RawMention


class _FakeSuccessFetcher(BaseMentionFetcher):
    """Returns mentions successfully."""

    @property
    def source(self) -> DataSource:
        return DataSource.TWITTER

    async def _do_fetch(self, query, *, cursor=None, limit=100):
        return ([RawMention(source=DataSource.TWITTER, source_id="1")], None)


class _FakeTransientErrorFetcher(BaseMentionFetcher):
    """Fails N times then succeeds."""

    def __init__(self, fail_count: int, **kwargs):
        super().__init__(**kwargs)
        self._fails_remaining = fail_count

    @property
    def source(self) -> DataSource:
        return DataSource.REDDIT

    async def _do_fetch(self, query, *, cursor=None, limit=100):
        if self._fails_remaining > 0:
            self._fails_remaining -= 1
            raise RuntimeError("transient error")
        return ([RawMention(source=DataSource.REDDIT, source_id="r1")], "next")


class _FakeUnrecoverableFetcher(BaseMentionFetcher):
    """Raises MentionFetchError (unrecoverable)."""

    @property
    def source(self) -> DataSource:
        return DataSource.NEWSDATA

    async def _do_fetch(self, query, *, cursor=None, limit=100):
        raise MentionFetchError("API key invalid")


class _FakeSlowFetcher(BaseMentionFetcher):
    """Takes too long, triggers timeout."""

    @property
    def source(self) -> DataSource:
        return DataSource.INSTAGRAM

    async def _do_fetch(self, query, *, cursor=None, limit=100):
        await asyncio.sleep(100)
        return ([], None)


@pytest.mark.asyncio
class TestBaseMentionFetcher:
    async def test_success(self):
        settings = MonitoringSettings(adapter_timeout_seconds=5.0)
        fetcher = _FakeSuccessFetcher(settings=settings)
        mentions, cursor = await fetcher.fetch_mentions("brand")
        assert len(mentions) == 1
        assert cursor is None

    async def test_retry_on_transient_error(self):
        settings = MonitoringSettings(adapter_timeout_seconds=5.0)
        fetcher = _FakeTransientErrorFetcher(fail_count=2, settings=settings)
        # Patch out sleep for speed
        fetcher.BASE_DELAY = 0.01
        mentions, cursor = await fetcher.fetch_mentions("query")
        assert len(mentions) == 1
        assert cursor == "next"

    async def test_exhaust_retries(self):
        settings = MonitoringSettings(adapter_timeout_seconds=5.0)
        fetcher = _FakeTransientErrorFetcher(fail_count=10, settings=settings)
        fetcher.BASE_DELAY = 0.01
        with pytest.raises(MentionFetchError, match="failed after 3 attempts"):
            await fetcher.fetch_mentions("query")

    async def test_unrecoverable_not_retried(self):
        settings = MonitoringSettings(adapter_timeout_seconds=5.0)
        fetcher = _FakeUnrecoverableFetcher(settings=settings)
        with pytest.raises(MentionFetchError, match="API key invalid"):
            await fetcher.fetch_mentions("query")

    async def test_timeout_records_failure(self):
        settings = MonitoringSettings(adapter_timeout_seconds=0.01)
        fetcher = _FakeSlowFetcher(settings=settings)
        fetcher.BASE_DELAY = 0.01
        with pytest.raises(MentionFetchError, match="failed after"):
            await fetcher.fetch_mentions("query")
        # Circuit breaker should have recorded failures
        assert fetcher._circuit_breaker._failure_count >= 3

    async def test_circuit_breaker_open_rejects(self):
        settings = MonitoringSettings(
            adapter_timeout_seconds=5.0,
            circuit_breaker_threshold=1,
        )
        fetcher = _FakeSuccessFetcher(settings=settings)
        # Force circuit open
        fetcher._circuit_breaker.record_failure()
        assert fetcher._circuit_breaker.is_open()

        with pytest.raises(MentionFetchError, match="Circuit breaker open"):
            await fetcher.fetch_mentions("query")

    async def test_half_open_allows_probe(self):
        settings = MonitoringSettings(
            adapter_timeout_seconds=5.0,
            circuit_breaker_threshold=1,
            circuit_breaker_reset_seconds=0.01,
        )
        fetcher = _FakeSuccessFetcher(settings=settings)
        fetcher._circuit_breaker.record_failure()
        assert fetcher._circuit_breaker.is_open()

        # Wait for half-open
        await asyncio.sleep(0.02)
        assert fetcher._circuit_breaker.allow_request()

        # Probe succeeds
        mentions, _ = await fetcher.fetch_mentions("query")
        assert len(mentions) == 1
        assert not fetcher._circuit_breaker.is_open()

    async def test_semaphore_limits_concurrency(self):
        settings = MonitoringSettings(
            adapter_timeout_seconds=5.0,
            adapter_concurrency=1,
        )
        fetcher = _FakeSuccessFetcher(settings=settings)

        # Should complete without deadlock
        results = await asyncio.gather(
            fetcher.fetch_mentions("q1"),
            fetcher.fetch_mentions("q2"),
        )
        assert len(results) == 2
