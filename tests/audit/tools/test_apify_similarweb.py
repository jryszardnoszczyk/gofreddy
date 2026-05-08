"""Tests for src/audit/tools/apify_similarweb — Phase-0 W5/W9 traffic data."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.audit.tools.apify_similarweb import (
    DEFAULT_ACTOR_ID,
    ApifySimilarWebFetcher,
)


@pytest.mark.asyncio
async def test_fetch_returns_degraded_when_no_token() -> None:
    f = ApifySimilarWebFetcher(apify_token="")
    result = await f.fetch("example.com")
    assert result["degraded"] is True
    assert "APIFY_TOKEN" in result["degraded_reason"]
    assert result["domain"] == "example.com"
    # Empty-result template stays well-formed.
    assert "channels" in result and "engagement" in result and "geo" in result


@pytest.mark.asyncio
async def test_fetch_returns_degraded_on_actor_404() -> None:
    f = ApifySimilarWebFetcher(apify_token="t")
    fake_client = MagicMock()
    fake_actor = MagicMock()
    fake_actor.call = AsyncMock(side_effect=Exception("Actor not found: 404"))
    fake_client.actor = MagicMock(return_value=fake_actor)
    f._client = fake_client

    result = await f.fetch("example.com")
    assert result["degraded"] is True
    assert "actor not found" in result["degraded_reason"].lower()


@pytest.mark.asyncio
async def test_fetch_returns_degraded_on_empty_dataset() -> None:
    f = ApifySimilarWebFetcher(apify_token="t")
    fake_client = MagicMock()
    fake_actor = MagicMock()
    fake_run = {"defaultDatasetId": "ds_x", "status": "SUCCEEDED"}
    fake_actor.call = AsyncMock(return_value=fake_run)
    fake_client.actor = MagicMock(return_value=fake_actor)
    f._client = fake_client

    with patch(
        "src.monitoring.adapters._common.parse_apify_items",
        new=AsyncMock(return_value=[]),
    ):
        result = await f.fetch("example.com")
    assert result["degraded"] is True
    assert "no dataset items" in result["degraded_reason"]


@pytest.mark.asyncio
async def test_fetch_projects_full_actor_output() -> None:
    f = ApifySimilarWebFetcher(apify_token="t")
    fake_client = MagicMock()
    fake_actor = MagicMock()
    fake_actor.call = AsyncMock(return_value={"defaultDatasetId": "ds"})
    fake_client.actor = MagicMock(return_value=fake_actor)
    f._client = fake_client

    actor_item = {
        "estimatedMonthlyVisits": {
            "total": 4_500_000,
            "uniqueVisitors": 1_800_000,
            "changePct": -3.2,
        },
        "trafficSources": {
            "direct": 0.41,
            "search": 0.28,
            "paidSearch": 0.06,
            "social": 0.10,
            "referrals": 0.08,
            "mail": 0.05,
            "display": 0.02,
        },
        "engagement": {
            "bounceRate": 0.42,
            "avgVisitDuration": 187,
            "pagesPerVisit": 3.4,
        },
        "topCountries": [
            {"countryCode": "US", "share": 0.55},
            {"countryCode": "GB", "share": 0.15},
            {"countryCode": "DE", "share": 0.05},
        ],
        "topKeywords": [
            {"keyword": "example tool", "position": 1},
            {"keyword": "compare", "position": 4},
        ],
    }

    with patch(
        "src.monitoring.adapters._common.parse_apify_items",
        new=AsyncMock(return_value=[actor_item]),
    ):
        result = await f.fetch("example.com")

    assert result["degraded"] is False
    assert result["domain"] == "example.com"
    assert result["actor_id"] == DEFAULT_ACTOR_ID
    assert result["estimated_traffic"]["monthly_visits"] == 4_500_000
    assert result["estimated_traffic"]["unique_visitors"] == 1_800_000
    assert result["channels"]["direct"] == 0.41
    assert result["channels"]["organic"] == 0.28
    assert result["channels"]["paid"] == 0.06
    assert result["channels"]["email"] == 0.05
    assert result["engagement"]["bounce_rate"] == 0.42
    assert result["engagement"]["avg_session_duration_s"] == 187.0
    assert result["engagement"]["pages_per_visit"] == 3.4
    assert result["geo"] == {"US": 0.55, "GB": 0.15, "DE": 0.05}
    assert len(result["top_keywords"]) == 2
    assert result["top_keywords"][0]["keyword"] == "example tool"


@pytest.mark.asyncio
async def test_fetch_handles_minimal_item_shape() -> None:
    """Minimal payload: only monthlyVisits scalar + nothing else."""
    f = ApifySimilarWebFetcher(apify_token="t")
    fake_client = MagicMock()
    fake_actor = MagicMock()
    fake_actor.call = AsyncMock(return_value={"defaultDatasetId": "ds"})
    fake_client.actor = MagicMock(return_value=fake_actor)
    f._client = fake_client

    with patch(
        "src.monitoring.adapters._common.parse_apify_items",
        new=AsyncMock(return_value=[{"monthlyVisits": 1234}]),
    ):
        result = await f.fetch("tiny.com")

    assert result["degraded"] is False
    # Channels dict still well-formed (all None).
    assert all(v is None for v in result["channels"].values())


@pytest.mark.asyncio
async def test_fetch_resilient_to_garbage_floats() -> None:
    """Channel shares may come through as strings — must not raise."""
    f = ApifySimilarWebFetcher(apify_token="t")
    fake_client = MagicMock()
    fake_actor = MagicMock()
    fake_actor.call = AsyncMock(return_value={"defaultDatasetId": "ds"})
    fake_client.actor = MagicMock(return_value=fake_actor)
    f._client = fake_client

    actor_item = {
        "trafficSources": {
            "direct": "0.45",
            "search": "not-a-number",
            "social": None,
        },
    }
    with patch(
        "src.monitoring.adapters._common.parse_apify_items",
        new=AsyncMock(return_value=[actor_item]),
    ):
        result = await f.fetch("example.com")

    assert result["degraded"] is False
    assert result["channels"]["direct"] == 0.45
    assert result["channels"]["organic"] is None  # garbage parsed → None
    assert result["channels"]["social"] is None


def test_default_actor_id_is_explicit() -> None:
    """JR may swap; doc-as-test guards the explicit default."""
    assert DEFAULT_ACTOR_ID == "tri_angle/similarweb-scraper"
