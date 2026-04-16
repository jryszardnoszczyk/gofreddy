"""Tests for PostgresMonitoringRepository with real DB."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
import pytest_asyncio

from src.monitoring.models import DataSource, SentimentLabel
from src.monitoring.repository import PostgresMonitoringRepository
from tests.helpers.pool_adapter import SingleConnectionPool

pytestmark = pytest.mark.db


@pytest_asyncio.fixture
async def repo(db_conn):
    """Repository backed by a single transactional connection."""
    pool = SingleConnectionPool(db_conn)
    return PostgresMonitoringRepository(pool)


@pytest_asyncio.fixture
async def user_id(db_conn):
    """Create a test user and return their ID."""
    uid = uuid4()
    await db_conn.execute(
        "INSERT INTO users (id, email) VALUES ($1, $2)",
        uid,
        f"test-{uid}@example.com",
    )
    return uid


@pytest_asyncio.fixture
async def user_id_2(db_conn):
    """Second test user for IDOR tests."""
    uid = uuid4()
    await db_conn.execute(
        "INSERT INTO users (id, email) VALUES ($1, $2)",
        uid,
        f"test2-{uid}@example.com",
    )
    return uid


@pytest.mark.asyncio
class TestMonitorCRUD:
    async def test_create_and_get(self, repo, user_id):
        monitor = await repo.create_monitor(
            user_id=user_id,
            name="Test Monitor",
            keywords=["brand", "product"],
            sources=[DataSource.TWITTER, DataSource.INSTAGRAM],
            boolean_query="brand AND product",
        )
        assert monitor.name == "Test Monitor"
        assert monitor.keywords == ["brand", "product"]
        assert DataSource.TWITTER in monitor.sources
        assert monitor.is_active is True

        # Retrieve
        fetched = await repo.get_monitor(monitor.id, user_id)
        assert fetched is not None
        assert fetched.name == "Test Monitor"

    async def test_get_wrong_user_returns_none(self, repo, user_id, user_id_2):
        monitor = await repo.create_monitor(
            user_id=user_id,
            name="Private",
            keywords=["secret"],
            sources=[DataSource.TWITTER],
        )
        result = await repo.get_monitor(monitor.id, user_id_2)
        assert result is None

    async def test_list_monitors(self, repo, user_id):
        await repo.create_monitor(
            user_id=user_id, name="Mon 1",
            keywords=["a"], sources=[DataSource.TWITTER],
        )
        await repo.create_monitor(
            user_id=user_id, name="Mon 2",
            keywords=["b"], sources=[DataSource.REDDIT],
        )
        monitors = await repo.list_monitors(user_id)
        assert len(monitors) == 2

    async def test_update_monitor_patch(self, repo, user_id):
        monitor = await repo.create_monitor(
            user_id=user_id, name="Original",
            keywords=["old"], sources=[DataSource.TWITTER],
        )
        updated = await repo.update_monitor(
            monitor.id, user_id, name="Updated", is_active=False
        )
        assert updated is not None
        assert updated.name == "Updated"
        assert updated.is_active is False
        # Keywords should remain unchanged
        assert updated.keywords == ["old"]

    async def test_delete_monitor(self, repo, user_id):
        monitor = await repo.create_monitor(
            user_id=user_id, name="ToDelete",
            keywords=["x"], sources=[DataSource.TWITTER],
        )
        deleted = await repo.delete_monitor(monitor.id, user_id)
        assert deleted is True

        # Should be gone
        fetched = await repo.get_monitor(monitor.id, user_id)
        assert fetched is None

    async def test_delete_wrong_user_fails(self, repo, user_id, user_id_2):
        monitor = await repo.create_monitor(
            user_id=user_id, name="NotYours",
            keywords=["x"], sources=[DataSource.TWITTER],
        )
        deleted = await repo.delete_monitor(monitor.id, user_id_2)
        assert deleted is False

    async def test_count_monitors(self, repo, user_id):
        assert await repo.count_monitors(user_id) == 0
        await repo.create_monitor(
            user_id=user_id, name="A",
            keywords=["a"], sources=[DataSource.TWITTER],
        )
        assert await repo.count_monitors(user_id) == 1

    async def test_get_active_monitors(self, repo, user_id, user_id_2):
        await repo.create_monitor(
            user_id=user_id, name="Active",
            keywords=["x"], sources=[DataSource.TWITTER], is_active=True,
        )
        await repo.create_monitor(
            user_id=user_id_2, name="Active2",
            keywords=["y"], sources=[DataSource.REDDIT], is_active=True,
        )
        await repo.create_monitor(
            user_id=user_id, name="Inactive",
            keywords=["z"], sources=[DataSource.TWITTER], is_active=False,
        )
        active = await repo.get_active_monitors()
        assert len(active) == 2


@pytest.mark.asyncio
class TestMentionInsert:
    def _mention_tuple(
        self,
        source="twitter",
        source_id=None,
        content="test content",
    ):
        return (
            source,
            source_id or str(uuid4()),
            "@author",       # author_handle
            "Author Name",   # author_name
            content,
            "https://example.com",  # url
            datetime.now(timezone.utc),  # published_at
            0.5,             # sentiment_score
            "positive",      # sentiment_label
            10,              # engagement_likes
            2,               # engagement_shares
            1,               # engagement_comments
            500,             # reach_estimate
            "en",            # language
            "US",            # geo_country
            [],              # media_urls
            {},  # metadata
        )

    async def test_insert_mentions(self, repo, user_id):
        monitor = await repo.create_monitor(
            user_id=user_id, name="Test",
            keywords=["x"], sources=[DataSource.TWITTER],
        )
        tuples = [self._mention_tuple() for _ in range(3)]
        inserted = await repo.insert_mentions(monitor.id, tuples)
        assert inserted == 3

    async def test_dedup_on_conflict(self, repo, user_id):
        monitor = await repo.create_monitor(
            user_id=user_id, name="Test",
            keywords=["x"], sources=[DataSource.TWITTER],
        )
        sid = "tweet_123"
        tuples = [self._mention_tuple(source_id=sid)]
        inserted1 = await repo.insert_mentions(monitor.id, tuples)
        assert inserted1 == 1

        # Same source_id: should be deduped
        inserted2 = await repo.insert_mentions(monitor.id, tuples)
        assert inserted2 == 0

    async def test_insert_and_advance_cursor(self, repo, user_id):
        monitor = await repo.create_monitor(
            user_id=user_id, name="Test",
            keywords=["x"], sources=[DataSource.TWITTER],
        )
        tuples = [self._mention_tuple()]
        inserted = await repo.insert_mentions_and_advance_cursor(
            monitor.id, tuples, DataSource.TWITTER, "cursor_page_2"
        )
        assert inserted == 1

        cursor = await repo.get_cursor(monitor.id, DataSource.TWITTER)
        assert cursor is not None
        assert cursor.cursor_value == "cursor_page_2"

    async def test_negative_engagement_rejected(self, repo, user_id, db_conn):
        """CHECK constraint rejects negative engagement values."""
        monitor = await repo.create_monitor(
            user_id=user_id, name="Test",
            keywords=["x"], sources=[DataSource.TWITTER],
        )
        import asyncpg
        with pytest.raises(asyncpg.CheckViolationError):
            await db_conn.execute(
                """INSERT INTO mentions (monitor_id, source, source_id, engagement_likes)
                   VALUES ($1, 'twitter', 'neg_test', -1)""",
                monitor.id,
            )


@pytest.mark.asyncio
class TestMentionQueries:
    async def _setup_mentions(self, repo, user_id):
        monitor = await repo.create_monitor(
            user_id=user_id, name="Query Test",
            keywords=["brand"], sources=[DataSource.TWITTER],
        )
        now = datetime.now(timezone.utc)
        tuples = [
            (
                "twitter", f"t_{i}", f"@user{i}", f"User {i}",
                f"Brand mention {i}", "https://example.com",
                now, 0.5 if i % 2 == 0 else -0.5,
                "positive" if i % 2 == 0 else "negative",
                10 * i, i, i, 100 * i, "en", "US", [], {},
            )
            for i in range(5)
        ]
        await repo.insert_mentions(monitor.id, tuples)
        return monitor

    async def test_get_mentions_idor_safe(self, repo, user_id, user_id_2):
        monitor = await self._setup_mentions(repo, user_id)

        # Owner gets mentions
        mentions = await repo.get_mentions(user_id, monitor.id)
        assert len(mentions) == 5

        # Different user gets nothing
        mentions = await repo.get_mentions(user_id_2, monitor.id)
        assert len(mentions) == 0

    async def test_get_mentions_filter_source(self, repo, user_id):
        monitor = await self._setup_mentions(repo, user_id)
        mentions = await repo.get_mentions(
            user_id, monitor.id, source=DataSource.TWITTER
        )
        assert len(mentions) == 5

        mentions = await repo.get_mentions(
            user_id, monitor.id, source=DataSource.REDDIT
        )
        assert len(mentions) == 0

    async def test_get_mentions_filter_sentiment(self, repo, user_id):
        monitor = await self._setup_mentions(repo, user_id)
        mentions = await repo.get_mentions(
            user_id, monitor.id, sentiment=SentimentLabel.POSITIVE
        )
        # i=0,2,4 are positive
        assert len(mentions) == 3

    async def test_search_mentions_fts(self, repo, user_id):
        monitor = await self._setup_mentions(repo, user_id)
        results = await repo.search_mentions(
            user_id, monitor.id, "brand mention"
        )
        assert len(results) > 0

    async def test_search_mentions_idor(self, repo, user_id, user_id_2):
        monitor = await self._setup_mentions(repo, user_id)
        results = await repo.search_mentions(
            user_id_2, monitor.id, "brand"
        )
        assert len(results) == 0


@pytest.mark.asyncio
class TestCursor:
    async def test_get_cursor_none(self, repo, user_id):
        monitor = await repo.create_monitor(
            user_id=user_id, name="Test",
            keywords=["x"], sources=[DataSource.TWITTER],
        )
        cursor = await repo.get_cursor(monitor.id, DataSource.TWITTER)
        assert cursor is None

    async def test_cursor_advance_and_read(self, repo, user_id):
        monitor = await repo.create_monitor(
            user_id=user_id, name="Test",
            keywords=["x"], sources=[DataSource.NEWSDATA],
        )
        await repo.insert_mentions_and_advance_cursor(
            monitor.id, [], DataSource.NEWSDATA, "page_1"
        )
        cursor = await repo.get_cursor(monitor.id, DataSource.NEWSDATA)
        assert cursor is not None
        assert cursor.cursor_value == "page_1"

        # Advance again
        await repo.insert_mentions_and_advance_cursor(
            monitor.id, [], DataSource.NEWSDATA, "page_2"
        )
        cursor = await repo.get_cursor(monitor.id, DataSource.NEWSDATA)
        assert cursor.cursor_value == "page_2"
