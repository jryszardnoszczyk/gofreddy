"""Tests for SOV batch query refactor (Unit 8)."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.monitoring.intelligence.share_of_voice import calculate_sov
from src.monitoring.models import ShareOfVoiceEntry


class TestSOVBatchQuery:
    def test_empty_brands_no_batch_query(self) -> None:
        """0 competitor brands → empty result, no batch query."""
        repo = MagicMock()
        conn = AsyncMock()
        conn.fetchval = AsyncMock(side_effect=[10, 0.5])  # my_count, my_sentiment
        conn.fetch = AsyncMock()  # Should not be called for batch

        ctx = AsyncMock()
        ctx.__aenter__ = AsyncMock(return_value=conn)
        ctx.__aexit__ = AsyncMock(return_value=False)
        repo._acquire_connection = MagicMock(return_value=ctx)

        result = asyncio.run(calculate_sov(
            repo, uuid4(), uuid4(), "MyBrand", [],
        ))

        assert len(result) == 1
        assert result[0].brand == "MyBrand"
        assert result[0].mention_count == 10
        conn.fetch.assert_not_called()

    def test_batch_query_called_with_brand_list(self) -> None:
        """5 brands → single batch query with brand array."""
        repo = MagicMock()
        conn = AsyncMock()
        conn.fetchval = AsyncMock(side_effect=[100, 0.7])

        # Simulate batch query result
        brands = ["BrandA", "BrandB", "BrandC", "AT&T", "L'Oreal"]
        mock_rows = [
            {"brand": "BrandA", "mention_count": 20, "sentiment_avg": 0.6},
            {"brand": "BrandB", "mention_count": 15, "sentiment_avg": 0.3},
            {"brand": "BrandC", "mention_count": 5, "sentiment_avg": None},
            {"brand": "AT&T", "mention_count": 30, "sentiment_avg": 0.8},
            {"brand": "L'Oreal", "mention_count": 0, "sentiment_avg": None},
        ]
        conn.fetch = AsyncMock(return_value=mock_rows)

        ctx = AsyncMock()
        ctx.__aenter__ = AsyncMock(return_value=conn)
        ctx.__aexit__ = AsyncMock(return_value=False)
        repo._acquire_connection = MagicMock(return_value=ctx)

        monitor_id = uuid4()
        user_id = uuid4()
        result = asyncio.run(calculate_sov(
            repo, monitor_id, user_id, "MyBrand", brands,
        ))

        # Single batch query call instead of 10 individual calls (2 per brand)
        assert conn.fetch.call_count == 1
        call_args = conn.fetch.call_args
        assert brands == call_args[0][4]  # Brand list passed as 5th positional arg ($4 in SQL)

        assert len(result) == 6  # My brand + 5 competitors
        assert result[0].brand == "MyBrand"
        assert result[0].mention_count == 100

        # Verify competitor entries preserve order
        assert result[1].brand == "BrandA"
        assert result[1].mention_count == 20
        assert result[4].brand == "AT&T"
        assert result[4].mention_count == 30
        assert result[5].brand == "L'Oreal"
        assert result[5].mention_count == 0
        assert result[5].sentiment_avg is None

    def test_percentages_computed_correctly(self) -> None:
        """Verify percentage computation with batch results."""
        repo = MagicMock()
        conn = AsyncMock()
        conn.fetchval = AsyncMock(side_effect=[50, 0.5])
        conn.fetch = AsyncMock(return_value=[
            {"brand": "Comp", "mention_count": 50, "sentiment_avg": 0.3},
        ])

        ctx = AsyncMock()
        ctx.__aenter__ = AsyncMock(return_value=conn)
        ctx.__aexit__ = AsyncMock(return_value=False)
        repo._acquire_connection = MagicMock(return_value=ctx)

        result = asyncio.run(calculate_sov(
            repo, uuid4(), uuid4(), "Me", ["Comp"],
        ))

        assert result[0].percentage == 50.0
        assert result[1].percentage == 50.0

    def test_brand_not_in_batch_result(self) -> None:
        """Brand listed but not in batch result → mention_count=0."""
        repo = MagicMock()
        conn = AsyncMock()
        conn.fetchval = AsyncMock(side_effect=[10, 0.5])
        conn.fetch = AsyncMock(return_value=[])  # No rows returned

        ctx = AsyncMock()
        ctx.__aenter__ = AsyncMock(return_value=conn)
        ctx.__aexit__ = AsyncMock(return_value=False)
        repo._acquire_connection = MagicMock(return_value=ctx)

        result = asyncio.run(calculate_sov(
            repo, uuid4(), uuid4(), "Me", ["Ghost"],
        ))

        assert result[1].brand == "Ghost"
        assert result[1].mention_count == 0
        assert result[1].sentiment_avg is None
