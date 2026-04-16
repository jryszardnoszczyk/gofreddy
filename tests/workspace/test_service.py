import pytest
from dataclasses import asdict
from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

from src.workspace.exceptions import CollectionNotFoundError, CollectionLimitError
from src.workspace.models import CollectionSummary, WorkspaceCollection, WorkspaceToolResult
from src.workspace.service import WorkspaceService


class TestWorkspaceService:

    @pytest.fixture
    def mock_repo(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_repo):
        return WorkspaceService(repository=mock_repo)

    def _make_collection(self, **kwargs):
        return WorkspaceCollection(
            id=kwargs.get("id", uuid4()),
            conversation_id=kwargs.get("conversation_id", uuid4()),
            name=kwargs.get("name", "Test"),
            item_count=kwargs.get("item_count", 0),
            active_filters={},
            summary_stats={},
            payload_ref=None,
            is_active=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    def _make_summary(self):
        return CollectionSummary(
            total_count=10,
            view_distribution={"<10k": 5, "10k-100k": 3, "100k-500k": 1, ">500k": 0, "unknown": 1},
            engagement_percentiles={"p25": 0.02, "median": 0.05, "p75": 0.1},
            top_creators=[{"handle": "alice", "count": 5}],
            platform_breakdown={"tiktok": 7, "instagram": 3},
            date_range={"earliest": "2026-01-01T00:00:00", "latest": "2026-02-01T00:00:00"},
        )

    async def test_create_collection_from_search(self, service, mock_repo):
        coll = self._make_collection(item_count=3)
        summary = self._make_summary()
        mock_repo.create_collection_with_items.return_value = (coll, summary)

        items = [
            {"source_id": "v1", "platform": "tiktok", "title": "Vid 1"},
            {"source_id": "v2", "platform": "instagram", "title": "Vid 2"},
            {"source_id": "v1", "platform": "tiktok", "title": "Vid 1 dupe"},  # duplicate
        ]
        result_coll, result_summary = await service.create_collection_from_search(
            uuid4(), "  My Search  ", items
        )
        # Name should be stripped + have UUID suffix
        call_args = mock_repo.create_collection_with_items.call_args
        import re
        assert re.match(r"My Search-[0-9a-f]{8}$", call_args.kwargs["name"])
        # Duplicates removed -- 2 unique items
        assert len(call_args.kwargs["items_tuples"]) == 2

    # ── create_collection (empty) ──────────────────────────────────

    async def test_create_collection_enforces_limit(self, service, mock_repo):
        """create_collection should raise CollectionLimitError when limit reached."""
        mock_repo.create_collection_checked.side_effect = CollectionLimitError(10)
        with pytest.raises(CollectionLimitError):
            await service.create_collection(uuid4(), "New Collection")

    async def test_create_collection_adds_uuid_suffix(self, service, mock_repo):
        """create_collection should strip name and append UUID suffix."""
        import re
        coll = self._make_collection(name="My Collection-abcd1234")
        mock_repo.create_collection_checked.return_value = coll
        mock_repo.set_active.return_value = None

        await service.create_collection(uuid4(), "  My Collection  ")

        call_args = mock_repo.create_collection_checked.call_args
        assert re.match(r"My Collection-[0-9a-f]{8}$", call_args[0][1])

    async def test_create_collection_sets_active(self, service, mock_repo):
        """create_collection should set the new collection as active."""
        conv_id = uuid4()
        coll = self._make_collection(conversation_id=conv_id)
        mock_repo.create_collection_checked.return_value = coll
        mock_repo.set_active.return_value = None

        await service.create_collection(conv_id, "Test")

        mock_repo.set_active.assert_called_once_with(conv_id, coll.id)

    async def test_create_collection_passes_max_collections(self, service, mock_repo):
        """create_collection should pass MAX_COLLECTIONS_PER_CONVERSATION to repo."""
        coll = self._make_collection()
        mock_repo.create_collection_checked.return_value = coll
        mock_repo.set_active.return_value = None

        await service.create_collection(uuid4(), "Test")

        call_args = mock_repo.create_collection_checked.call_args
        assert call_args[1]["max_collections"] == 10

    # ── find_collection_by_name ──────────────────────────────────────

    async def test_find_collection_by_name_exact_match(self, service, mock_repo):
        conv_id = uuid4()
        coll = self._make_collection(conversation_id=conv_id, name="Beauty Q3")
        mock_repo.get_collections_by_conversation.return_value = [coll]
        result = await service.find_collection_by_name(conv_id, "Beauty Q3")
        assert result is not None
        assert result.name == "Beauty Q3"

    async def test_find_collection_by_name_with_uuid_suffix(self, service, mock_repo):
        conv_id = uuid4()
        coll = self._make_collection(conversation_id=conv_id, name="Beauty Q3-a1b2c3d4")
        mock_repo.get_collections_by_conversation.return_value = [coll]
        result = await service.find_collection_by_name(conv_id, "Beauty Q3")
        assert result is not None
        assert result.name == "Beauty Q3-a1b2c3d4"

    async def test_find_collection_by_name_hyphenated_base(self, service, mock_repo):
        conv_id = uuid4()
        coll = self._make_collection(conversation_id=conv_id, name="cross-platform-abcdef12")
        mock_repo.get_collections_by_conversation.return_value = [coll]
        result = await service.find_collection_by_name(conv_id, "cross-platform")
        assert result is not None
        assert result.name == "cross-platform-abcdef12"

    async def test_find_collection_by_name_no_false_positive_non_hex(self, service, mock_repo):
        """8-char suffix that isn't hex should NOT match."""
        conv_id = uuid4()
        coll = self._make_collection(conversation_id=conv_id, name="test-abc-xxxxxxxx")
        mock_repo.get_collections_by_conversation.return_value = [coll]
        result = await service.find_collection_by_name(conv_id, "test-abc")
        assert result is None

    async def test_find_collection_by_name_no_false_positive_wrong_length(self, service, mock_repo):
        """Suffix that isn't 8 chars should NOT match."""
        conv_id = uuid4()
        coll = self._make_collection(conversation_id=conv_id, name="test-abc12")
        mock_repo.get_collections_by_conversation.return_value = [coll]
        result = await service.find_collection_by_name(conv_id, "test")
        assert result is None

    async def test_find_collection_by_name_not_found(self, service, mock_repo):
        conv_id = uuid4()
        mock_repo.get_collections_by_conversation.return_value = []
        result = await service.find_collection_by_name(conv_id, "nonexistent")
        assert result is None

    async def test_find_collection_by_name_strips_whitespace(self, service, mock_repo):
        conv_id = uuid4()
        coll = self._make_collection(conversation_id=conv_id, name="Beauty Q3-a1b2c3d4")
        mock_repo.get_collections_by_conversation.return_value = [coll]
        result = await service.find_collection_by_name(conv_id, "  Beauty Q3  ")
        assert result is not None

    async def test_filter_collection(self, service, mock_repo):
        coll = self._make_collection(item_count=10)
        summary = self._make_summary()
        mock_repo.update_filters.return_value = coll
        mock_repo.aggregate.return_value = summary
        mock_repo.update_summary.return_value = coll

        result_coll, result_summary = await service.filter_collection(
            coll.id, {"platform": "tiktok"}
        )
        mock_repo.update_filters.assert_called_once()
        mock_repo.aggregate.assert_called_once()
        # item_count should be preserved (not filtered count)
        mock_repo.update_summary.assert_called_once()
        call_args = mock_repo.update_summary.call_args
        assert call_args[0][2] == 10  # original item_count preserved

    async def test_get_workspace_state(self, service, mock_repo):
        conv_id = uuid4()
        colls = [
            self._make_collection(conversation_id=conv_id, name="Results"),
        ]
        mock_repo.get_collections_by_conversation.return_value = colls
        state = await service.get_workspace_state(conv_id)
        assert "collections" in state
        assert len(state["collections"]) == 1
        assert state["collections"][0]["name"] == "Results"

    async def test_validate_ownership_success(self, service, mock_repo):
        conv_id = uuid4()
        coll = self._make_collection(conversation_id=conv_id)
        mock_repo.get_collection.return_value = coll
        result = await service.validate_ownership(coll.id, conv_id)
        assert result.id == coll.id

    async def test_validate_ownership_failure(self, service, mock_repo):
        mock_repo.get_collection.return_value = None
        with pytest.raises(CollectionNotFoundError):
            await service.validate_ownership(uuid4(), uuid4())

    async def test_validate_ownership_wrong_conversation(self, service, mock_repo):
        coll = self._make_collection(conversation_id=uuid4())
        mock_repo.get_collection.return_value = coll
        with pytest.raises(CollectionNotFoundError):
            await service.validate_ownership(coll.id, uuid4())  # different conversation

    async def test_store_tool_result(self, service, mock_repo):
        conv_id = uuid4()
        tool_result = WorkspaceToolResult(
            id=uuid4(),
            conversation_id=conv_id,
            tool_name="search_videos",
            input_args={"query": "test"},
            result_data={"videos": []},
            workspace_item_id=None,
            created_at=datetime.now(UTC),
        )
        mock_repo.store_tool_result.return_value = tool_result
        result = await service.store_tool_result(
            conv_id, "search_videos", {"query": "test"}, {"videos": []},
        )
        assert result.tool_name == "search_videos"
        mock_repo.store_tool_result.assert_called_once_with(
            conversation_id=conv_id,
            tool_name="search_videos",
            input_args={"query": "test"},
            result_data={"videos": []},
            workspace_item_id=None,
        )
