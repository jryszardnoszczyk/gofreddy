"""Tests for PostgresPublishingRepository against real PostgreSQL.

Uses SingleConnectionPool adapter for transactional test isolation.
Covers: connections CRUD, queue CRUD, state machine transitions,
claim/dispatch, retry logic, labels (JSONB), and auto-repost.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
import pytest_asyncio

from tests.helpers.pool_adapter import SingleConnectionPool
from src.publishing.models import (
    AuthType,
    PlatformConnection,
    PublishPlatform,
    PublishStatus,
    QueueItem,
)
from src.publishing.repository import PostgresPublishingRepository, RETRY_DELAYS


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def repo(db_conn):
    """Publishing repository backed by transactional single-connection pool."""
    return PostgresPublishingRepository(SingleConnectionPool(db_conn))


@pytest_asyncio.fixture
async def org_id(db_conn):
    """Insert a test user (= org) and return its UUID."""
    uid = uuid4()
    await db_conn.execute(
        "INSERT INTO users (id, email) VALUES ($1, $2)",
        uid, f"org-{uid.hex[:8]}@test.com",
    )
    return uid


@pytest_asyncio.fixture
async def other_org_id(db_conn):
    """A second org for IDOR tests."""
    uid = uuid4()
    await db_conn.execute(
        "INSERT INTO users (id, email) VALUES ($1, $2)",
        uid, f"other-{uid.hex[:8]}@test.com",
    )
    return uid


@pytest_asyncio.fixture
async def connection(repo, org_id):
    """Create a default platform connection for queue-item tests."""
    return await repo.create_connection(
        org_id=org_id,
        platform="linkedin",
        auth_type="oauth2",
        account_id="acct-1",
        account_name="Test LinkedIn",
        credential_enc=b"enc-cred",
        access_token_enc=b"enc-access",
        refresh_token_enc=b"enc-refresh",
        scopes=["w_member_social"],
        key_version=1,
    )


async def _make_queue_item(
    repo: PostgresPublishingRepository,
    org_id,
    connection_id,
    *,
    platform: str = "linkedin",
    labels: list[str] | None = None,
    metadata: dict | None = None,
    og_title: str | None = None,
    client_id=None,
) -> QueueItem:
    """Helper: create a draft queue item with sensible defaults."""
    kwargs: dict = {
        "labels": labels or [],
        "metadata": metadata or {},
    }
    if og_title is not None:
        kwargs["og_title"] = og_title
    if client_id is not None:
        kwargs["client_id"] = client_id
    return await repo.create_queue_item(
        org_id=org_id,
        platform=platform,
        connection_id=connection_id,
        content_parts=[{"type": "text", "body": "Hello world"}],
        **kwargs,
    )


async def _approve_and_schedule(
    repo: PostgresPublishingRepository,
    item_id,
    org_id,
    approver_id,
    scheduled_at: datetime,
) -> QueueItem:
    """Approve then schedule an item — returns the scheduled item."""
    await repo.approve_item(item_id, org_id, approver_id)
    item = await repo.schedule_item(item_id, org_id, scheduled_at)
    assert item is not None
    return item


async def _set_item_status(db_conn, item_id: ..., status: str) -> None:
    """Directly set status in DB (bypass state machine for test setup)."""
    await db_conn.execute(
        "UPDATE publish_queue SET status = $1 WHERE id = $2",
        status, item_id,
    )


async def _set_item_fields(db_conn, item_id, **fields) -> None:
    """Directly update arbitrary fields on a queue item.

    Disables the updated_at trigger so we can backdate timestamps for tests.
    """
    sets = []
    params = []
    for i, (k, v) in enumerate(fields.items(), start=1):
        sets.append(f"{k} = ${i}")
        params.append(v)
    params.append(item_id)
    sql = f"UPDATE publish_queue SET {', '.join(sets)} WHERE id = ${len(params)}"
    await db_conn.execute(
        "ALTER TABLE publish_queue DISABLE TRIGGER set_updated_at"
    )
    try:
        await db_conn.execute(sql, *params)
    finally:
        await db_conn.execute(
            "ALTER TABLE publish_queue ENABLE TRIGGER set_updated_at"
        )


# ===========================================================================
# Priority 1: Dangerous SQL — Claim & Dispatch
# ===========================================================================


@pytest.mark.db
class TestClaimAndDispatch:

    @pytest_asyncio.fixture
    async def approver(self, db_conn):
        uid = uuid4()
        await db_conn.execute(
            "INSERT INTO users (id, email) VALUES ($1, $2)",
            uid, f"approver-{uid.hex[:8]}@test.com",
        )
        return uid

    async def test_claim_scheduled_items_picks_due_items(
        self, repo, org_id, connection, approver, db_conn,
    ):
        past = datetime.now(UTC) - timedelta(minutes=5)
        item1 = await _make_queue_item(repo, org_id, connection.id)
        item2 = await _make_queue_item(repo, org_id, connection.id)
        await _approve_and_schedule(repo, item1.id, org_id, approver, past)
        await _approve_and_schedule(repo, item2.id, org_id, approver, past)

        claimed = await repo.claim_scheduled_items(batch_size=10, now=datetime.now(UTC))

        assert len(claimed) == 2
        ids = {c.id for c in claimed}
        assert item1.id in ids
        assert item2.id in ids
        for c in claimed:
            assert c.status == PublishStatus.PUBLISHING

    async def test_claim_scheduled_items_skips_future(
        self, repo, org_id, connection, approver,
    ):
        future = datetime.now(UTC) + timedelta(hours=2)
        item = await _make_queue_item(repo, org_id, connection.id)
        await _approve_and_schedule(repo, item.id, org_id, approver, future)

        claimed = await repo.claim_scheduled_items(batch_size=10, now=datetime.now(UTC))
        assert len(claimed) == 0

    async def test_claim_scheduled_items_respects_batch_size(
        self, repo, org_id, connection, approver,
    ):
        past = datetime.now(UTC) - timedelta(minutes=5)
        for _ in range(3):
            item = await _make_queue_item(repo, org_id, connection.id)
            await _approve_and_schedule(repo, item.id, org_id, approver, past)

        claimed = await repo.claim_scheduled_items(batch_size=1, now=datetime.now(UTC))
        assert len(claimed) == 1

    async def test_claim_scheduled_items_empty_queue(self, repo):
        claimed = await repo.claim_scheduled_items(batch_size=10, now=datetime.now(UTC))
        assert claimed == []

    async def test_claim_retryable_failed_items(
        self, repo, org_id, connection, approver, db_conn,
    ):
        """Failed items with retry_count < max and next_retry_at in the past are claimed."""
        past = datetime.now(UTC) - timedelta(minutes=10)
        item = await _make_queue_item(repo, org_id, connection.id)
        await _approve_and_schedule(repo, item.id, org_id, approver, past)
        # Claim once, then fail it to get retry scheduling
        claimed = await repo.claim_scheduled_items(batch_size=10, now=datetime.now(UTC))
        assert len(claimed) == 1
        await repo.mark_failed(claimed[0].id, "transient error")
        # Directly set next_retry_at to the past so it's retryable now
        await _set_item_fields(
            db_conn, item.id, next_retry_at=datetime.now(UTC) - timedelta(seconds=1)
        )

        reclaimed = await repo.claim_scheduled_items(batch_size=10, now=datetime.now(UTC))
        assert len(reclaimed) == 1
        assert reclaimed[0].id == item.id
        assert reclaimed[0].status == PublishStatus.PUBLISHING

    async def test_claim_skips_exhausted_retries(
        self, repo, org_id, connection, approver, db_conn,
    ):
        """Failed items with retry_count >= max_retries are NOT claimed."""
        past = datetime.now(UTC) - timedelta(minutes=10)
        item = await _make_queue_item(repo, org_id, connection.id)
        await _approve_and_schedule(repo, item.id, org_id, approver, past)
        # Set to failed with max retries exhausted
        await _set_item_fields(
            db_conn, item.id,
            status="failed",
            retry_count=len(RETRY_DELAYS),
            next_retry_at=datetime.now(UTC) - timedelta(minutes=1),
        )

        claimed = await repo.claim_scheduled_items(batch_size=10, now=datetime.now(UTC))
        assert len(claimed) == 0

    async def test_reap_stale_publishing_items(
        self, repo, org_id, connection, db_conn,
    ):
        item = await _make_queue_item(repo, org_id, connection.id)
        await _set_item_status(db_conn, item.id, "publishing")
        # Backdate updated_at so it looks stale
        await _set_item_fields(
            db_conn, item.id,
            updated_at=datetime.now(UTC) - timedelta(minutes=20),
        )

        reaped = await repo.reap_stale_publishing_items(
            threshold_minutes=15, now=datetime.now(UTC)
        )
        assert reaped == 1

        refreshed = await repo.get_queue_item(item.id, org_id)
        assert refreshed is not None
        assert refreshed.status == PublishStatus.FAILED
        assert refreshed.error_message == "stale_reap"

    async def test_reap_stale_items_skips_fresh(
        self, repo, org_id, connection, db_conn,
    ):
        item = await _make_queue_item(repo, org_id, connection.id)
        await _set_item_status(db_conn, item.id, "publishing")
        # updated_at is recent (just created), so threshold not exceeded

        reaped = await repo.reap_stale_publishing_items(
            threshold_minutes=15, now=datetime.now(UTC)
        )
        assert reaped == 0

    async def test_mark_published(
        self, repo, org_id, connection, db_conn,
    ):
        item = await _make_queue_item(repo, org_id, connection.id)
        await _set_item_status(db_conn, item.id, "publishing")

        ok = await repo.mark_published(item.id, "ext-123", "https://linkedin.com/post/123")
        assert ok is True

        refreshed = await repo.get_queue_item(item.id, org_id)
        assert refreshed is not None
        assert refreshed.status == PublishStatus.PUBLISHED
        assert refreshed.external_id == "ext-123"
        assert refreshed.external_url == "https://linkedin.com/post/123"

    async def test_mark_published_wrong_status(
        self, repo, org_id, connection,
    ):
        """mark_published only works on 'publishing' items."""
        item = await _make_queue_item(repo, org_id, connection.id)
        # Item is in 'draft' status
        ok = await repo.mark_published(item.id, "ext-999", "https://example.com")
        assert ok is False

    async def test_get_publishing_item(
        self, repo, org_id, connection, db_conn,
    ):
        item = await _make_queue_item(repo, org_id, connection.id)
        await _set_item_status(db_conn, item.id, "publishing")

        result = await repo.get_publishing_item(item.id)
        assert result is not None
        assert result.id == item.id
        assert result.status == PublishStatus.PUBLISHING

    async def test_get_publishing_item_wrong_status(
        self, repo, org_id, connection,
    ):
        item = await _make_queue_item(repo, org_id, connection.id)
        result = await repo.get_publishing_item(item.id)
        assert result is None  # draft, not publishing


# ===========================================================================
# Priority 1: Dangerous SQL — Retry & Repost
# ===========================================================================


@pytest.mark.db
class TestRetryAndRepost:

    async def test_mark_failed_first_failure(
        self, repo, org_id, connection, db_conn,
    ):
        item = await _make_queue_item(repo, org_id, connection.id)
        await _set_item_status(db_conn, item.id, "publishing")

        ok = await repo.mark_failed(item.id, "api_timeout")
        assert ok is True

        refreshed = await repo.get_queue_item(item.id, org_id)
        assert refreshed is not None
        assert refreshed.status == PublishStatus.FAILED
        assert refreshed.retry_count == 1
        assert refreshed.error_message == "api_timeout"

    async def test_mark_failed_increments_retry(
        self, repo, org_id, connection, db_conn,
    ):
        item = await _make_queue_item(repo, org_id, connection.id)
        await _set_item_status(db_conn, item.id, "publishing")
        await repo.mark_failed(item.id, "err1")

        # Force back to publishing for second failure
        await _set_item_status(db_conn, item.id, "publishing")
        await repo.mark_failed(item.id, "err2")

        refreshed = await repo.get_queue_item(item.id, org_id)
        assert refreshed is not None
        assert refreshed.retry_count == 2
        assert refreshed.error_message == "err2"

    async def test_mark_failed_exhausts_retries_after_max_plus_one(
        self, repo, org_id, connection, db_conn,
    ):
        """After len(RETRY_DELAYS)+1 failures, next_retry_at is NULL.

        The CASE logic evaluates retry_count BEFORE the increment, so:
        - Fail #1: retry_count=0 -> delay=300s, then count=1
        - Fail #2: retry_count=1 -> delay=600s, then count=2
        - Fail #3: retry_count=2 -> delay=1200s, then count=3
        - Fail #4: retry_count=3 -> ELSE NULL, then count=4
        The claim query filters retry_count < 3, so fail #3's retry
        is the last one that can be claimed.
        """
        item = await _make_queue_item(repo, org_id, connection.id)
        # 3 failures: all get retry scheduling
        for i in range(3):
            await _set_item_status(db_conn, item.id, "publishing")
            await repo.mark_failed(item.id, f"err{i+1}")

        refreshed = await repo.get_queue_item(item.id, org_id)
        assert refreshed is not None
        assert refreshed.retry_count == 3
        # 3rd failure still sets next_retry_at (1200s delay)
        row = await db_conn.fetchrow(
            "SELECT next_retry_at FROM publish_queue WHERE id = $1", item.id,
        )
        assert row["next_retry_at"] is not None

        # 4th failure: retry_count=3 -> ELSE NULL
        await _set_item_status(db_conn, item.id, "publishing")
        await repo.mark_failed(item.id, "err4")

        refreshed2 = await repo.get_queue_item(item.id, org_id)
        assert refreshed2 is not None
        assert refreshed2.retry_count == 4

        row2 = await db_conn.fetchrow(
            "SELECT next_retry_at FROM publish_queue WHERE id = $1", item.id,
        )
        assert row2["next_retry_at"] is None

    async def test_mark_failed_merges_metadata(
        self, repo, org_id, connection, db_conn,
    ):
        item = await _make_queue_item(
            repo, org_id, connection.id, metadata={"source": "rss"},
        )
        await _set_item_status(db_conn, item.id, "publishing")

        await repo.mark_failed(item.id, "rate_limit", {"last_http_status": 429})

        refreshed = await repo.get_queue_item(item.id, org_id)
        assert refreshed is not None
        # Original metadata preserved
        assert refreshed.metadata["source"] == "rss"
        # Patch merged
        assert refreshed.metadata["last_http_status"] == 429

    async def test_mark_failed_wrong_status(
        self, repo, org_id, connection,
    ):
        """mark_failed only works on 'publishing' items."""
        item = await _make_queue_item(repo, org_id, connection.id)
        # Item is draft, not publishing
        ok = await repo.mark_failed(item.id, "should not work")
        assert ok is False

    async def test_mark_for_repost(
        self, repo, org_id, connection, db_conn,
    ):
        item = await _make_queue_item(repo, org_id, connection.id)
        schedule = {"interval_days": 7, "max_reposts": 3, "reposts_done": 0}
        await repo.mark_for_repost(item.id, org_id, schedule)

        refreshed = await repo.get_queue_item(item.id, org_id)
        assert refreshed is not None
        assert "repost_schedule" in refreshed.metadata
        assert refreshed.metadata["repost_schedule"]["interval_days"] == 7
        assert refreshed.metadata["repost_schedule"]["max_reposts"] == 3

    async def test_increment_repost_count(
        self, repo, org_id, connection, db_conn,
    ):
        item = await _make_queue_item(
            repo, org_id, connection.id,
            metadata={"repost_schedule": {"interval_days": 7, "max_reposts": 3, "reposts_done": 0}},
        )
        # Mark as published first (reposts happen on published items)
        await _set_item_status(db_conn, item.id, "published")

        await repo.increment_repost_count(item.id)

        refreshed = await repo.get_queue_item(item.id, org_id)
        assert refreshed is not None
        assert refreshed.metadata["repost_schedule"]["reposts_done"] == 1
        assert "last_reposted_at" in refreshed.metadata

    async def test_increment_repost_count_twice(
        self, repo, org_id, connection, db_conn,
    ):
        item = await _make_queue_item(
            repo, org_id, connection.id,
            metadata={"repost_schedule": {"interval_days": 7, "max_reposts": 3, "reposts_done": 0}},
        )
        await _set_item_status(db_conn, item.id, "published")

        await repo.increment_repost_count(item.id)
        await repo.increment_repost_count(item.id)

        refreshed = await repo.get_queue_item(item.id, org_id)
        assert refreshed is not None
        assert refreshed.metadata["repost_schedule"]["reposts_done"] == 2

    async def test_get_pending_reposts(
        self, repo, org_id, connection, db_conn,
    ):
        """Published items with repost_schedule and reposts_done < max are returned."""
        item = await _make_queue_item(
            repo, org_id, connection.id,
            metadata={
                "repost_schedule": {
                    "interval_days": 1,
                    "max_reposts": 3,
                    "reposts_done": 0,
                },
            },
        )
        await _set_item_status(db_conn, item.id, "published")

        pending = await repo.get_pending_reposts()
        ids = {p.id for p in pending}
        assert item.id in ids

    async def test_get_pending_reposts_skips_exhausted(
        self, repo, org_id, connection, db_conn,
    ):
        """Items where reposts_done >= max_reposts should NOT be returned."""
        item = await _make_queue_item(
            repo, org_id, connection.id,
            metadata={
                "repost_schedule": {
                    "interval_days": 1,
                    "max_reposts": 2,
                    "reposts_done": 2,
                },
            },
        )
        await _set_item_status(db_conn, item.id, "published")

        pending = await repo.get_pending_reposts()
        ids = {p.id for p in pending}
        assert item.id not in ids


# ===========================================================================
# Priority 1: Labels (JSONB operations)
# ===========================================================================


@pytest.mark.db
class TestLabels:

    async def test_add_labels_to_empty(
        self, repo, org_id, connection,
    ):
        item = await _make_queue_item(repo, org_id, connection.id)
        result = await repo.add_labels(item.id, org_id, ["campaign-q1", "urgent"])
        assert sorted(result) == ["campaign-q1", "urgent"]

    async def test_add_labels_deduplicates(
        self, repo, org_id, connection,
    ):
        item = await _make_queue_item(
            repo, org_id, connection.id, labels=["existing"],
        )
        result = await repo.add_labels(item.id, org_id, ["existing", "new"])
        assert sorted(result) == ["existing", "new"]

    async def test_add_labels_wrong_org(
        self, repo, org_id, other_org_id, connection,
    ):
        item = await _make_queue_item(repo, org_id, connection.id)
        result = await repo.add_labels(item.id, other_org_id, ["sneaky"])
        assert result == []

    async def test_remove_labels(
        self, repo, org_id, connection,
    ):
        item = await _make_queue_item(
            repo, org_id, connection.id, labels=["a", "b", "c"],
        )
        result = await repo.remove_labels(item.id, org_id, ["b"])
        assert sorted(result) == ["a", "c"]

    async def test_remove_labels_noop(
        self, repo, org_id, connection,
    ):
        item = await _make_queue_item(
            repo, org_id, connection.id, labels=["a"],
        )
        result = await repo.remove_labels(item.id, org_id, ["x"])
        assert result == ["a"]

    async def test_get_distinct_labels(
        self, repo, org_id, connection,
    ):
        await _make_queue_item(repo, org_id, connection.id, labels=["alpha", "beta"])
        await _make_queue_item(repo, org_id, connection.id, labels=["beta", "gamma"])

        distinct = await repo.get_distinct_labels(org_id)
        assert sorted(distinct) == ["alpha", "beta", "gamma"]

    async def test_list_items_by_label(
        self, repo, org_id, connection,
    ):
        item1 = await _make_queue_item(
            repo, org_id, connection.id, labels=["campaign-q1"],
        )
        await _make_queue_item(repo, org_id, connection.id, labels=["other"])

        results = await repo.list_items_by_label(org_id, "campaign-q1")
        assert len(results) == 1
        assert results[0].id == item1.id

    async def test_list_items_by_label_empty(
        self, repo, org_id, connection,
    ):
        await _make_queue_item(repo, org_id, connection.id, labels=["other"])
        results = await repo.list_items_by_label(org_id, "nonexistent")
        assert results == []


# ===========================================================================
# Priority 2: State Machine
# ===========================================================================


@pytest.mark.db
class TestStateMachine:

    @pytest_asyncio.fixture
    async def approver(self, db_conn):
        uid = uuid4()
        await db_conn.execute(
            "INSERT INTO users (id, email) VALUES ($1, $2)",
            uid, f"approver-{uid.hex[:8]}@test.com",
        )
        return uid

    async def test_approve_draft(
        self, repo, org_id, connection, approver,
    ):
        item = await _make_queue_item(repo, org_id, connection.id)
        approved = await repo.approve_item(item.id, org_id, approver)
        assert approved is not None
        assert approved.approved_at is not None
        assert approved.approved_by == approver

    async def test_approve_failed(
        self, repo, org_id, connection, approver, db_conn,
    ):
        item = await _make_queue_item(repo, org_id, connection.id)
        await _set_item_status(db_conn, item.id, "failed")

        approved = await repo.approve_item(item.id, org_id, approver)
        assert approved is not None
        assert approved.approved_by == approver

    async def test_approve_published_returns_none(
        self, repo, org_id, connection, approver, db_conn,
    ):
        item = await _make_queue_item(repo, org_id, connection.id)
        await _set_item_status(db_conn, item.id, "published")

        result = await repo.approve_item(item.id, org_id, approver)
        assert result is None

    async def test_schedule_approved_item(
        self, repo, org_id, connection, approver,
    ):
        item = await _make_queue_item(repo, org_id, connection.id)
        await repo.approve_item(item.id, org_id, approver)

        future = datetime.now(UTC) + timedelta(hours=1)
        scheduled = await repo.schedule_item(item.id, org_id, future)
        assert scheduled is not None
        assert scheduled.status == PublishStatus.SCHEDULED
        assert scheduled.scheduled_at is not None

    async def test_schedule_unapproved_returns_none(
        self, repo, org_id, connection,
    ):
        """Cannot schedule without approved_at being set."""
        item = await _make_queue_item(repo, org_id, connection.id)
        future = datetime.now(UTC) + timedelta(hours=1)
        result = await repo.schedule_item(item.id, org_id, future)
        assert result is None

    async def test_cancel_draft(
        self, repo, org_id, connection,
    ):
        item = await _make_queue_item(repo, org_id, connection.id)
        cancelled = await repo.cancel_item(item.id, org_id)
        assert cancelled is not None
        assert cancelled.status == PublishStatus.CANCELLED

    async def test_cancel_scheduled(
        self, repo, org_id, connection, approver,
    ):
        item = await _make_queue_item(repo, org_id, connection.id)
        future = datetime.now(UTC) + timedelta(hours=1)
        await _approve_and_schedule(repo, item.id, org_id, approver, future)

        cancelled = await repo.cancel_item(item.id, org_id)
        assert cancelled is not None
        assert cancelled.status == PublishStatus.CANCELLED

    async def test_cancel_publishing_returns_none(
        self, repo, org_id, connection, db_conn,
    ):
        """Cannot cancel an item that's actively publishing."""
        item = await _make_queue_item(repo, org_id, connection.id)
        await _set_item_status(db_conn, item.id, "publishing")

        result = await repo.cancel_item(item.id, org_id)
        assert result is None

    async def test_cancel_failed(
        self, repo, org_id, connection, db_conn,
    ):
        """Failed items can be cancelled."""
        item = await _make_queue_item(repo, org_id, connection.id)
        await _set_item_status(db_conn, item.id, "failed")

        cancelled = await repo.cancel_item(item.id, org_id)
        assert cancelled is not None
        assert cancelled.status == PublishStatus.CANCELLED

    async def test_update_queue_item(
        self, repo, org_id, connection,
    ):
        item = await _make_queue_item(repo, org_id, connection.id)
        updated = await repo.update_queue_item(item.id, org_id, og_title="New Title")
        assert updated is not None
        assert updated.og_title == "New Title"

    async def test_update_disallowed_field_raises(
        self, repo, org_id, connection,
    ):
        item = await _make_queue_item(repo, org_id, connection.id)
        with pytest.raises(ValueError, match="Cannot update fields"):
            await repo.update_queue_item(item.id, org_id, status="published")

    async def test_update_non_draft_returns_none(
        self, repo, org_id, connection, approver, db_conn,
    ):
        """update_queue_item only works on draft items."""
        item = await _make_queue_item(repo, org_id, connection.id)
        await _set_item_status(db_conn, item.id, "scheduled")
        result = await repo.update_queue_item(item.id, org_id, og_title="Nope")
        assert result is None

    async def test_delete_draft(
        self, repo, org_id, connection,
    ):
        item = await _make_queue_item(repo, org_id, connection.id)
        deleted = await repo.delete_queue_item(item.id, org_id)
        assert deleted is True

        result = await repo.get_queue_item(item.id, org_id)
        assert result is None

    async def test_delete_scheduled_returns_false(
        self, repo, org_id, connection, approver,
    ):
        """Cannot delete a scheduled item (must cancel first)."""
        item = await _make_queue_item(repo, org_id, connection.id)
        future = datetime.now(UTC) + timedelta(hours=1)
        await _approve_and_schedule(repo, item.id, org_id, approver, future)

        deleted = await repo.delete_queue_item(item.id, org_id)
        assert deleted is False

    async def test_delete_cancelled(
        self, repo, org_id, connection,
    ):
        """Cancelled items can be deleted."""
        item = await _make_queue_item(repo, org_id, connection.id)
        await repo.cancel_item(item.id, org_id)

        deleted = await repo.delete_queue_item(item.id, org_id)
        assert deleted is True


# ===========================================================================
# Priority 3: CRUD — Platform Connections
# ===========================================================================


@pytest.mark.db
class TestConnections:

    async def test_create_connection(
        self, repo, org_id,
    ):
        conn = await repo.create_connection(
            org_id=org_id,
            platform="bluesky",
            auth_type="app_password",
            account_id="did:plc:abc123",
            account_name="my-bluesky",
            credential_enc=b"encrypted-app-password",
            scopes=[],
            key_version=1,
        )
        assert isinstance(conn, PlatformConnection)
        assert conn.org_id == org_id
        assert conn.platform == PublishPlatform.BLUESKY
        assert conn.auth_type == AuthType.APP_PASSWORD
        assert conn.account_id == "did:plc:abc123"
        assert conn.account_name == "my-bluesky"
        assert conn.is_active is True
        assert conn.key_version == 1

    async def test_get_connection(
        self, repo, org_id, connection,
    ):
        result = await repo.get_connection(connection.id, org_id)
        assert result is not None
        assert result.id == connection.id
        assert result.platform == PublishPlatform.LINKEDIN

    async def test_get_connection_wrong_org(
        self, repo, org_id, other_org_id, connection,
    ):
        """IDOR check: connection belongs to org_id, not other_org_id."""
        result = await repo.get_connection(connection.id, other_org_id)
        assert result is None

    async def test_get_connection_nonexistent(
        self, repo, org_id,
    ):
        result = await repo.get_connection(uuid4(), org_id)
        assert result is None

    async def test_list_connections(
        self, repo, org_id,
    ):
        await repo.create_connection(
            org_id=org_id, platform="linkedin", auth_type="oauth2",
            account_id="acct-list-1", account_name="LI 1",
        )
        await repo.create_connection(
            org_id=org_id, platform="x", auth_type="oauth2",
            account_id="acct-list-2", account_name="X Account",
        )
        conns = await repo.list_connections(org_id)
        assert len(conns) == 2
        platforms = {c.platform for c in conns}
        assert PublishPlatform.LINKEDIN in platforms
        assert PublishPlatform.X in platforms

    async def test_deactivate_connection(
        self, repo, org_id, connection,
    ):
        ok = await repo.deactivate_connection(connection.id, org_id)
        assert ok is True

        # No longer in active list
        conns = await repo.list_connections(org_id)
        ids = {c.id for c in conns}
        assert connection.id not in ids

    async def test_deactivate_connection_wrong_org(
        self, repo, org_id, other_org_id, connection,
    ):
        ok = await repo.deactivate_connection(connection.id, other_org_id)
        assert ok is False

    async def test_get_credentials(
        self, repo, org_id, connection,
    ):
        creds = await repo.get_connection_credentials(connection.id, org_id)
        assert creds["credential_enc"] == b"enc-cred"
        assert creds["access_token_enc"] == b"enc-access"
        assert creds["refresh_token_enc"] == b"enc-refresh"
        assert creds["key_version"] == 1

    async def test_get_credentials_wrong_org(
        self, repo, org_id, other_org_id, connection,
    ):
        creds = await repo.get_connection_credentials(connection.id, other_org_id)
        assert creds == {}

    async def test_update_last_used(
        self, repo, org_id, connection,
    ):
        assert connection.last_used_at is None
        await repo.update_last_used(connection.id)

        refreshed = await repo.get_connection(connection.id, org_id)
        assert refreshed is not None
        assert refreshed.last_used_at is not None

    async def test_get_connections_for_rotation(
        self, repo, org_id,
    ):
        # Create connection with old key_version
        await repo.create_connection(
            org_id=org_id, platform="wordpress", auth_type="app_password",
            account_id="wp-old", account_name="Old WP",
            key_version=1,
        )
        # Create connection with current key_version
        await repo.create_connection(
            org_id=org_id, platform="ghost", auth_type="api_key",
            account_id="ghost-new", account_name="New Ghost",
            key_version=2,
        )

        rows = await repo.get_connections_for_rotation(current_version=2, batch_size=10)
        account_ids = [r["id"] for r in rows]
        # Only the v1 connection should appear
        assert len(rows) == 1

    async def test_count_connections_for_rotation(
        self, repo, org_id,
    ):
        await repo.create_connection(
            org_id=org_id, platform="linkedin", auth_type="oauth2",
            account_id="rot-1", account_name="R1", key_version=1,
        )
        await repo.create_connection(
            org_id=org_id, platform="x", auth_type="oauth2",
            account_id="rot-2", account_name="R2", key_version=1,
        )
        count = await repo.count_connections_for_rotation(current_version=2)
        assert count == 2

    async def test_get_expiring_connections(
        self, repo, org_id,
    ):
        # Create connection with token expiring in 30 minutes
        await repo.create_connection(
            org_id=org_id, platform="linkedin", auth_type="oauth2",
            account_id="exp-soon", account_name="Expiring",
            token_expires_at=datetime.now(UTC) + timedelta(minutes=30),
        )
        # Create connection with token expiring in 2 hours (outside window)
        await repo.create_connection(
            org_id=org_id, platform="x", auth_type="oauth2",
            account_id="exp-later", account_name="Safe",
            token_expires_at=datetime.now(UTC) + timedelta(hours=2),
        )

        expiring = await repo.get_expiring_connections(within_minutes=60)
        account_ids = [c.account_id for c in expiring]
        assert "exp-soon" in account_ids
        assert "exp-later" not in account_ids

    async def test_get_active_connection(
        self, repo, org_id, connection,
    ):
        result = await repo.get_active_connection(connection.id)
        assert result is not None
        assert result.id == connection.id

    async def test_get_active_connection_deactivated(
        self, repo, org_id, connection,
    ):
        await repo.deactivate_connection(connection.id, org_id)
        result = await repo.get_active_connection(connection.id)
        assert result is None

    async def test_update_key_version(
        self, repo, org_id, connection,
    ):
        await repo.update_key_version(
            connection.id,
            credential_enc=b"new-cred",
            access_token_enc=b"new-access",
            refresh_token_enc=b"new-refresh",
            new_key_version=2,
        )
        creds = await repo.get_connection_credentials(connection.id, org_id)
        assert creds["credential_enc"] == b"new-cred"
        assert creds["access_token_enc"] == b"new-access"
        assert creds["refresh_token_enc"] == b"new-refresh"
        assert creds["key_version"] == 2

    async def test_update_connection_token_metadata(
        self, repo, org_id, connection,
    ):
        new_expiry = datetime.now(UTC) + timedelta(hours=1)
        await repo.update_connection_token_metadata(
            connection.id, token_expires_at=new_expiry, scopes=["read", "write"],
        )
        refreshed = await repo.get_connection(connection.id, org_id)
        assert refreshed is not None
        assert refreshed.scopes == ["read", "write"]
        assert refreshed.token_expires_at is not None

    async def test_update_connection_credentials(
        self, repo, org_id, connection,
    ):
        new_expiry = datetime.now(UTC) + timedelta(hours=2)
        await repo.update_connection_credentials(
            connection.id,
            credential_enc=b"refreshed-cred",
            key_version=3,
            token_expires_at=new_expiry,
        )
        creds = await repo.get_connection_credentials(connection.id, org_id)
        assert creds["credential_enc"] == b"refreshed-cred"
        assert creds["key_version"] == 3


# ===========================================================================
# Priority 3: CRUD — Queue Items
# ===========================================================================


@pytest.mark.db
class TestQueueCRUD:

    async def test_create_queue_item(
        self, repo, org_id, connection,
    ):
        item = await repo.create_queue_item(
            org_id=org_id,
            platform="linkedin",
            connection_id=connection.id,
            content_parts=[{"type": "text", "body": "Post content"}],
            labels=["draft"],
            metadata={"source": "manual"},
            og_title="My Post",
            first_comment="First!",
        )
        assert isinstance(item, QueueItem)
        assert item.org_id == org_id
        assert item.platform == "linkedin"
        assert item.connection_id == connection.id
        assert item.content_parts == [{"type": "text", "body": "Post content"}]
        assert item.labels == ["draft"]
        assert item.metadata == {"source": "manual"}
        assert item.og_title == "My Post"
        assert item.first_comment == "First!"
        assert item.status == PublishStatus.DRAFT
        assert item.retry_count == 0

    async def test_get_queue_item(
        self, repo, org_id, connection,
    ):
        item = await _make_queue_item(repo, org_id, connection.id)
        result = await repo.get_queue_item(item.id, org_id)
        assert result is not None
        assert result.id == item.id
        assert result.org_id == org_id

    async def test_get_queue_item_wrong_org(
        self, repo, org_id, other_org_id, connection,
    ):
        item = await _make_queue_item(repo, org_id, connection.id)
        result = await repo.get_queue_item(item.id, other_org_id)
        assert result is None

    async def test_get_queue_item_nonexistent(
        self, repo, org_id,
    ):
        result = await repo.get_queue_item(uuid4(), org_id)
        assert result is None

    async def test_list_queue_items_no_filters(
        self, repo, org_id, connection,
    ):
        await _make_queue_item(repo, org_id, connection.id)
        await _make_queue_item(repo, org_id, connection.id)
        items = await repo.list_queue_items(org_id)
        assert len(items) == 2

    async def test_list_queue_items_filter_by_status(
        self, repo, org_id, connection, db_conn,
    ):
        item1 = await _make_queue_item(repo, org_id, connection.id)
        item2 = await _make_queue_item(repo, org_id, connection.id)
        await _set_item_status(db_conn, item2.id, "cancelled")

        drafts = await repo.list_queue_items(org_id, status="draft")
        assert len(drafts) == 1
        assert drafts[0].id == item1.id

    async def test_list_queue_items_filter_by_platform(
        self, repo, org_id, connection, db_conn,
    ):
        await _make_queue_item(repo, org_id, connection.id, platform="linkedin")
        # Create a second connection for a different platform
        conn2 = await repo.create_connection(
            org_id=org_id, platform="x", auth_type="oauth2",
            account_id="x-acct", account_name="X",
        )
        await _make_queue_item(repo, org_id, conn2.id, platform="x")

        linkedin_items = await repo.list_queue_items(org_id, platform="linkedin")
        assert len(linkedin_items) == 1

    async def test_list_queue_items_label_filter(
        self, repo, org_id, connection,
    ):
        await _make_queue_item(repo, org_id, connection.id, labels=["promo"])
        await _make_queue_item(repo, org_id, connection.id, labels=["other"])

        items = await repo.list_queue_items(org_id, label="promo")
        assert len(items) == 1
        assert "promo" in items[0].labels

    async def test_list_queue_items_pagination(
        self, repo, org_id, connection,
    ):
        for i in range(5):
            await _make_queue_item(repo, org_id, connection.id)

        page1 = await repo.list_queue_items(org_id, limit=2, offset=0)
        page2 = await repo.list_queue_items(org_id, limit=2, offset=2)
        page3 = await repo.list_queue_items(org_id, limit=2, offset=4)
        assert len(page1) == 2
        assert len(page2) == 2
        assert len(page3) == 1
        # No overlap between pages
        all_ids = {i.id for i in page1} | {i.id for i in page2} | {i.id for i in page3}
        assert len(all_ids) == 5

    async def test_count_queue_items(
        self, repo, org_id, connection, db_conn,
    ):
        """Count excludes published and cancelled items."""
        await _make_queue_item(repo, org_id, connection.id)  # draft
        await _make_queue_item(repo, org_id, connection.id)  # draft
        item3 = await _make_queue_item(repo, org_id, connection.id)
        await _set_item_status(db_conn, item3.id, "published")
        item4 = await _make_queue_item(repo, org_id, connection.id)
        await _set_item_status(db_conn, item4.id, "cancelled")

        count = await repo.count_queue_items(org_id)
        assert count == 2

    async def test_find_by_source_url(
        self, repo, org_id, connection,
    ):
        item = await _make_queue_item(
            repo, org_id, connection.id,
            metadata={"source_url": "https://blog.example.com/post-1"},
        )
        result = await repo.find_queue_item_by_source_url(
            org_id, "linkedin", "https://blog.example.com/post-1",
        )
        assert result is not None
        assert result.id == item.id

    async def test_find_by_source_url_not_found(
        self, repo, org_id,
    ):
        result = await repo.find_queue_item_by_source_url(
            org_id, "linkedin", "https://nonexistent.com",
        )
        assert result is None

    async def test_update_queue_item_empty_fields(
        self, repo, org_id, connection,
    ):
        """Passing no fields returns the item unchanged."""
        item = await _make_queue_item(repo, org_id, connection.id, og_title="Original")
        result = await repo.update_queue_item(item.id, org_id)
        assert result is not None
        assert result.og_title == "Original"

    async def test_update_queue_item_jsonb_fields(
        self, repo, org_id, connection,
    ):
        """JSONB fields (content_parts, media, labels, metadata) serialize correctly."""
        item = await _make_queue_item(repo, org_id, connection.id)
        updated = await repo.update_queue_item(
            item.id, org_id,
            content_parts=[{"type": "text", "body": "Updated"}],
            labels=["new-label"],
            metadata={"key": "value"},
        )
        assert updated is not None
        assert updated.content_parts == [{"type": "text", "body": "Updated"}]
        assert updated.labels == ["new-label"]
        assert updated.metadata == {"key": "value"}
