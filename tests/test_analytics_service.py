"""Integration tests for AccountAnalyticsService — mock adapters, mock repo."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.monitoring.analytics_service import AccountAnalyticsService
from src.monitoring.intelligence.models_analytics import AccountPost, AccountSnapshot
from src.monitoring.models import DataSource, RawMention

ORG_ID = uuid4()


def _make_raw_mention(**overrides) -> RawMention:
    defaults = dict(
        source=DataSource.TWITTER,
        source_id=f"tw_{uuid4().hex[:8]}",
        author_handle="testuser",
        content="Hello world #test",
        published_at=datetime(2026, 3, 20, 10, 0, tzinfo=timezone.utc),
        engagement_likes=100,
        engagement_shares=10,
        engagement_comments=5,
        metadata={"impressions": 1000, "media_type": "text", "hashtags": ["test"]},
    )
    defaults.update(overrides)
    return RawMention(**defaults)


def _make_account_post(**overrides) -> AccountPost:
    defaults = dict(
        id=uuid4(),
        org_id=ORG_ID,
        platform="twitter",
        username="testuser",
        source_id=f"tw_{uuid4().hex[:8]}",
        content="Hello world",
        published_at=datetime(2026, 3, 20, 10, 0, tzinfo=timezone.utc),
        likes=100, shares=10, comments=5, impressions=1000,
        engagement_rate=0.115,
        media_type="text",
        hashtags=["test"],
        metadata={},
        created_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return AccountPost(**defaults)


@pytest.mark.mock_required
class TestSyncPosts:
    @pytest.mark.asyncio
    async def test_sync_posts_twitter(self):
        repo = AsyncMock()
        repo.upsert_posts = AsyncMock(return_value=3)
        xpoz = AsyncMock()
        xpoz.get_posts_by_author = AsyncMock(return_value=[_make_raw_mention() for _ in range(3)])

        service = AccountAnalyticsService(repository=repo, xpoz_adapter=xpoz)
        result = await service.sync_posts(ORG_ID, "twitter", "testuser")

        assert result["posts_synced"] == 3
        assert result["error"] is None
        xpoz.get_posts_by_author.assert_awaited_once_with("testuser", platform=DataSource.TWITTER, limit=50)
        repo.upsert_posts.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_sync_posts_tiktok(self):
        repo = AsyncMock()
        repo.upsert_posts = AsyncMock(return_value=2)
        ic = AsyncMock()
        ic.get_content = AsyncMock(return_value={
            "data": {"posts": [
                {"id": "tt1", "caption": "test", "taken_at": 1711000000, "engagement": {"likes": 50}, "play_count": 500},
                {"id": "tt2", "caption": "test2", "taken_at": 1711100000, "engagement": {"likes": 30}, "play_count": 300},
            ]},
        })

        service = AccountAnalyticsService(repository=repo, ic_backend=ic)
        result = await service.sync_posts(ORG_ID, "tiktok", "testuser")

        assert result["posts_synced"] == 2
        assert result["error"] is None
        ic.get_content.assert_awaited_once_with("tiktok", "testuser")

    @pytest.mark.asyncio
    async def test_sync_posts_adapter_error_returns_error(self):
        repo = AsyncMock()
        service = AccountAnalyticsService(repository=repo, xpoz_adapter=None)
        result = await service.sync_posts(ORG_ID, "twitter", "testuser")

        assert result["posts_synced"] == 0
        assert result["error"] is not None


@pytest.mark.mock_required
class TestSyncSnapshot:
    @pytest.mark.asyncio
    async def test_sync_snapshot_twitter(self):
        repo = AsyncMock()
        repo.insert_snapshot = AsyncMock(side_effect=lambda s: s)
        xpoz = AsyncMock()
        profile = MagicMock()
        profile.follower_count = 10000
        profile.following_count = 500
        profile.post_count = 200
        xpoz.get_user_profile = AsyncMock(return_value=profile)

        service = AccountAnalyticsService(repository=repo, xpoz_adapter=xpoz)
        result = await service.sync_snapshot(ORG_ID, "twitter", "testuser")

        assert result is not None
        assert result.follower_count == 10000
        repo.insert_snapshot.assert_awaited_once()


@pytest.mark.mock_required
class TestDashboard:
    @pytest.mark.asyncio
    async def test_dashboard_derived_metrics(self):
        posts = [_make_account_post(likes=100 + i, comments=5, shares=10) for i in range(5)]
        repo = AsyncMock()
        repo.get_posts = AsyncMock(return_value=posts)
        repo.get_latest_snapshot = AsyncMock(return_value=None)
        repo.get_patterns = AsyncMock(return_value=None)

        service = AccountAnalyticsService(repository=repo)
        result = await service.get_dashboard(ORG_ID, "twitter", "testuser")

        assert result["total_posts"] == 5
        assert result["avg_engagement"] > 0
        assert result["platform"] == "twitter"
        assert result["has_patterns"] is False


@pytest.mark.mock_required
class TestRecomputePatterns:
    @pytest.mark.asyncio
    async def test_recompute_patterns_stores_result(self):
        posts = [_make_account_post(
            published_at=datetime(2026, 3, i + 1, 10, 0, tzinfo=timezone.utc),
            likes=50 + i * 10,
        ) for i in range(25)]
        repo = AsyncMock()
        repo.get_posts_for_patterns = AsyncMock(return_value=posts)
        repo.get_snapshots = AsyncMock(return_value=[])
        repo.upsert_patterns = AsyncMock()

        service = AccountAnalyticsService(repository=repo)
        patterns = await service.recompute_patterns(ORG_ID, "twitter", "testuser")

        assert patterns.total_posts == 25
        assert patterns.markdown
        repo.upsert_patterns.assert_awaited_once()
