import json
import pytest
import pytest_asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from tests.helpers.pool_adapter import SingleConnectionPool
from src.workspace.repository import PostgresWorkspaceRepository
from src.workspace.models import WorkspaceCollection, WorkspaceItem, CollectionSummary, WorkspaceToolResult
from src.workspace.exceptions import DuplicateCollectionError, CollectionLimitError


@pytest.mark.db
class TestWorkspaceRepository:

    @pytest_asyncio.fixture
    async def repo(self, db_conn):
        return PostgresWorkspaceRepository(SingleConnectionPool(db_conn))

    @pytest_asyncio.fixture
    async def conversation_id(self, db_conn, test_user):
        """Create a test conversation and return its ID."""
        row = await db_conn.fetchrow(
            "INSERT INTO conversations (user_id, title, expires_at) VALUES ($1, $2, $3) RETURNING id",
            test_user["id"], "Test", datetime.now(UTC) + timedelta(days=7),
        )
        return row["id"]

    @pytest_asyncio.fixture
    async def collection(self, repo, conversation_id):
        """Create a test collection."""
        return await repo.create_collection(conversation_id, "Test Collection")

    async def test_create_collection(self, repo, conversation_id):
        coll = await repo.create_collection(conversation_id, "My Collection")
        assert coll.name == "My Collection"
        assert coll.conversation_id == conversation_id
        assert coll.item_count == 0
        assert isinstance(coll, WorkspaceCollection)

    async def test_create_collection_duplicate_name(self, repo, conversation_id):
        await repo.create_collection(conversation_id, "Dupe")
        with pytest.raises(DuplicateCollectionError):
            await repo.create_collection(conversation_id, "Dupe")

    async def test_get_collections_by_conversation(self, repo, conversation_id):
        await repo.create_collection(conversation_id, "First")
        await repo.create_collection(conversation_id, "Second")
        colls = await repo.get_collections_by_conversation(conversation_id)
        assert len(colls) == 2
        names = {c.name for c in colls}
        assert names == {"First", "Second"}

    async def test_update_filters(self, repo, collection):
        updated = await repo.update_filters(collection.id, {"platform": "tiktok"})
        assert updated is not None
        assert updated.active_filters == {"platform": "tiktok"}

    async def test_update_summary(self, repo, collection):
        updated = await repo.update_summary(collection.id, {"total": 50}, 50)
        assert updated is not None
        assert updated.item_count == 50
        assert updated.summary_stats == {"total": 50}

    async def test_set_active(self, repo, conversation_id):
        c1 = await repo.create_collection(conversation_id, "C1")
        c2 = await repo.create_collection(conversation_id, "C2")
        await repo.set_active(conversation_id, c1.id)
        colls = await repo.get_collections_by_conversation(conversation_id)
        active = [c for c in colls if c.is_active]
        assert len(active) == 1
        assert active[0].id == c1.id
        # Now switch to c2
        await repo.set_active(conversation_id, c2.id)
        colls = await repo.get_collections_by_conversation(conversation_id)
        active = [c for c in colls if c.is_active]
        assert len(active) == 1
        assert active[0].id == c2.id

    async def test_count_collections(self, repo, conversation_id):
        await repo.create_collection(conversation_id, "A")
        await repo.create_collection(conversation_id, "B")
        count = await repo.count_collections(conversation_id)
        assert count == 2

    async def test_add_items_bulk(self, repo, collection):
        items = [
            {
                "source_id": f"vid_{i}",
                "platform": "tiktok",
                "title": f"Video {i}",
                "creator_handle": f"creator_{i % 3}",
                "views": i * 1000,
                "engagement_rate": 0.05 + i * 0.01,
                "risk_score": None,
                "payload_json": {},
            }
            for i in range(100)
        ]
        count = await repo.add_items(collection.id, items)
        assert count == 100

    async def test_get_items_with_filters(self, repo, collection):
        items = [
            {"source_id": "v1", "platform": "tiktok", "views": 5000},
            {"source_id": "v2", "platform": "instagram", "views": 50000},
            {"source_id": "v3", "platform": "tiktok", "views": 200000},
        ]
        await repo.add_items(collection.id, items)
        results = await repo.get_items(collection.id, filters={"platform": "tiktok"})
        assert len(results) == 2
        assert all(r.platform == "tiktok" for r in results)

    async def test_get_items_sorting(self, repo, collection):
        items = [
            {"source_id": "v1", "platform": "tiktok", "views": 100},
            {"source_id": "v2", "platform": "tiktok", "views": 50000},
            {"source_id": "v3", "platform": "tiktok", "views": 500},
        ]
        await repo.add_items(collection.id, items)
        results = await repo.get_items(collection.id, sort_by="views", sort_order="DESC")
        assert results[0].views == 50000
        assert results[-1].views == 100

    async def test_aggregate_with_data(self, repo, collection):
        items = [
            {"source_id": f"v{i}", "platform": "tiktok" if i % 2 == 0 else "instagram",
             "views": i * 10000, "engagement_rate": 0.01 * (i + 1),
             "creator_handle": f"creator_{i % 3}"}
            for i in range(10)
        ]
        await repo.add_items(collection.id, items)
        summary = await repo.aggregate(collection.id)
        assert summary.total_count == 10
        assert isinstance(summary, CollectionSummary)
        assert sum(summary.view_distribution.values()) == 10
        assert summary.engagement_percentiles["median"] > 0
        assert len(summary.platform_breakdown) == 2
        assert len(summary.top_creators) <= 10
        assert summary.date_range is not None

    async def test_aggregate_empty_collection(self, repo, collection):
        summary = await repo.aggregate(collection.id)
        assert summary.total_count == 0
        assert summary.view_distribution["unknown"] == 0
        assert summary.engagement_percentiles["median"] == 0.0
        assert summary.top_creators == []
        assert summary.date_range is None

    async def test_store_tool_result(self, repo, conversation_id):
        result = await repo.store_tool_result(
            conversation_id, "search_videos",
            {"query": "makeup tutorials"}, {"results": [1, 2, 3]}
        )
        assert result.tool_name == "search_videos"
        assert result.input_args == {"query": "makeup tutorials"}
        assert result.result_data == {"results": [1, 2, 3]}
        assert isinstance(result, WorkspaceToolResult)

    async def test_get_tool_results_filter_by_name(self, repo, conversation_id):
        await repo.store_tool_result(conversation_id, "search_videos", {}, {"r": 1})
        await repo.store_tool_result(conversation_id, "analyze_video", {}, {"r": 2})
        results = await repo.get_tool_results(conversation_id, tool_name="search_videos")
        assert len(results) == 1
        assert results[0].tool_name == "search_videos"

    async def test_get_tool_results_no_filter(self, repo, conversation_id):
        await repo.store_tool_result(conversation_id, "search_videos", {}, {"r": 1})
        await repo.store_tool_result(conversation_id, "analyze_video", {}, {"r": 2})
        results = await repo.get_tool_results(conversation_id)
        assert len(results) == 2

    async def test_cascade_delete_collection(self, repo, db_conn, conversation_id, collection):
        await repo.add_items(collection.id, [
            {"source_id": "v1", "platform": "tiktok"},
        ])
        # Delete collection directly
        await db_conn.execute("DELETE FROM workspace_collections WHERE id = $1", collection.id)
        # Items should be gone
        items = await repo.get_items(collection.id)
        assert items == []

    async def test_create_collection_with_items(self, repo, conversation_id):
        items_tuples = [
            ("vid_1", "tiktok", "Video 1", "creator_a", 5000, 0.05, None, '{}'),
            ("vid_2", "instagram", "Video 2", "creator_b", 50000, 0.12, None, '{}'),
            ("vid_3", "tiktok", "Video 3", "creator_a", 200000, 0.08, None, '{}'),
        ]
        coll, summary = await repo.create_collection_with_items(
            conversation_id, "Search Results", items_tuples
        )
        assert coll.name == "Search Results"
        assert coll.item_count == 3
        assert summary.total_count == 3
        assert summary.platform_breakdown.get("tiktok", 0) == 2
