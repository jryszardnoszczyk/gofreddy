"""Tests for AI Search monitoring adapter — verify RawMention mapping per citation."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.geo.providers.cloro import AIResponse, Citation, QueryResult
from src.monitoring.adapters.ai_search import AiSearchAdapter
from src.monitoring.models import DataSource, RawMention


@pytest.fixture
def adapter():
    return AiSearchAdapter(cloro_api_key="test-key")


class TestAiSearchAdapterSource:
    def test_source_is_ai_search(self, adapter):
        assert adapter.source == DataSource.AI_SEARCH


class TestAiSearchAdapterLifecycle:
    @pytest.mark.asyncio
    async def test_aenter_creates_client(self, adapter):
        async with adapter:
            assert adapter._client is not None

    @pytest.mark.asyncio
    async def test_aexit_closes_client(self, adapter):
        async with adapter:
            pass
        assert adapter._client is None

    @pytest.mark.asyncio
    async def test_no_key_means_no_client(self):
        a = AiSearchAdapter(cloro_api_key="")
        async with a:
            assert a._client is None


class TestDoFetch:
    @pytest.mark.asyncio
    async def test_maps_citations_to_raw_mentions(self, adapter):
        mock_result = QueryResult(
            results={
                "chatgpt": AIResponse(
                    platform="chatgpt",
                    text="According to our research...",
                    citations=[
                        Citation(url="https://example.com/page1", title="Example Page", source="example.com"),
                        Citation(url="https://other.com/page2", title="Other Page", source="other.com"),
                    ],
                ),
                "perplexity": AIResponse(
                    platform="perplexity",
                    text="Here are some results...",
                    citations=[
                        Citation(url="https://example.com/page1", title="Example", source="example.com"),
                    ],
                ),
            },
            errors={"gemini": "Rate limited"},
        )

        mock_client = MagicMock()
        mock_client.is_available = True
        mock_client.query = AsyncMock(return_value=mock_result)
        mock_client.close = AsyncMock()

        adapter._client = mock_client
        mentions, cursor = await adapter._do_fetch("test brand")

        assert cursor is None  # No pagination
        assert len(mentions) == 3  # 2 from chatgpt + 1 from perplexity

        # Verify RawMention structure
        m = mentions[0]
        assert isinstance(m, RawMention)
        assert m.source == DataSource.AI_SEARCH
        assert m.author_handle == "chatgpt"
        assert "chatgpt" in m.source_id
        assert "https://example.com/page1" in m.url
        assert m.metadata["ai_platform"] == "chatgpt"
        assert m.metadata["citation_index"] == 0

    @pytest.mark.asyncio
    async def test_no_citations_returns_empty(self, adapter):
        mock_result = QueryResult(
            results={
                "chatgpt": AIResponse(
                    platform="chatgpt",
                    text="I don't have specific information about that.",
                    citations=[],
                ),
            },
            errors={},
        )

        mock_client = MagicMock()
        mock_client.is_available = True
        mock_client.query = AsyncMock(return_value=mock_result)
        mock_client.close = AsyncMock()

        adapter._client = mock_client
        mentions, cursor = await adapter._do_fetch("obscure brand")

        assert mentions == []
        assert cursor is None

    @pytest.mark.asyncio
    async def test_raises_when_not_initialized(self):
        adapter = AiSearchAdapter(cloro_api_key="")
        async with adapter:
            from src.monitoring.exceptions import MentionFetchError
            with pytest.raises(MentionFetchError, match="missing Cloro API key"):
                await adapter._do_fetch("test")

    @pytest.mark.asyncio
    async def test_raises_when_circuit_open(self, adapter):
        mock_client = MagicMock()
        mock_client.is_available = False
        mock_client.close = AsyncMock()
        adapter._client = mock_client

        from src.monitoring.exceptions import MentionFetchError
        with pytest.raises(MentionFetchError, match="circuit breaker"):
            await adapter._do_fetch("test")

    @pytest.mark.asyncio
    async def test_all_platforms_error_returns_empty(self, adapter):
        mock_result = QueryResult(
            results={},
            errors={
                "chatgpt": "Rate limited",
                "perplexity": "Timeout",
                "gemini": "Server error",
            },
        )

        mock_client = MagicMock()
        mock_client.is_available = True
        mock_client.query = AsyncMock(return_value=mock_result)
        mock_client.close = AsyncMock()

        adapter._client = mock_client
        mentions, cursor = await adapter._do_fetch("test")

        assert mentions == []
        assert cursor is None


class TestDataSourceEnum:
    def test_ai_search_in_datasource(self):
        assert DataSource.AI_SEARCH == "ai_search"
        assert DataSource("ai_search") == DataSource.AI_SEARCH
