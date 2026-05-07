"""Tests for L2-added DataForSEO methods (master plan §4.9 work item #5).

Covers ``serp_features``, ``historical_rank``, ``business_data_gbp`` plus the
shared ``_format_gbp_day`` helper. Mocks the underlying RestClient.post so
no network calls hit DataForSEO's API.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.seo.providers.dataforseo import DataForSeoProvider, _format_gbp_day


# --- _format_gbp_day --------------------------------------------------------


def test_format_gbp_day_none_returns_none() -> None:
    assert _format_gbp_day(None) is None


def test_format_gbp_day_empty_returns_closed() -> None:
    assert _format_gbp_day([]) == "closed"


def test_format_gbp_day_single_slot() -> None:
    raw = [{"open": {"hour": 9, "minute": 0}, "close": {"hour": 17, "minute": 30}}]
    assert _format_gbp_day(raw) == "09:00-17:30"


def test_format_gbp_day_multiple_slots() -> None:
    raw = [
        {"open": {"hour": 9, "minute": 0}, "close": {"hour": 12, "minute": 0}},
        {"open": {"hour": 13, "minute": 0}, "close": {"hour": 17, "minute": 0}},
    ]
    assert _format_gbp_day(raw) == "09:00-12:00,13:00-17:00"


def test_format_gbp_day_malformed_returns_none() -> None:
    assert _format_gbp_day("garbage") is None


# --- serp_features ----------------------------------------------------------


@pytest.fixture
def provider():
    p = DataForSeoProvider(login="u", password="p")
    return p


def _wrap_post(provider, response_dict):
    """Patch the lazily-built client's ``post`` to return ``response_dict``."""
    fake_client = MagicMock()
    fake_client.post = MagicMock(return_value=response_dict)
    provider._client = fake_client


_SERP_FIXTURE = {
    "tasks": [{
        "status_code": 20000,
        "result": [{
            "items_count": 3,
            "items": [
                {"type": "answer_box", "rank_absolute": 0, "url": "https://x.com",
                 "domain": "x.com", "title": "Answer", "description": "..."},
                {"type": "organic", "rank_absolute": 1, "url": "https://a.com",
                 "domain": "a.com", "title": "Page A", "snippet": "snip"},
                {"type": "people_also_ask", "rank_absolute": 2, "url": None,
                 "domain": None, "title": "More questions"},
            ],
        }],
    }],
}


@pytest.mark.asyncio
async def test_serp_features_parses_features_present(provider) -> None:
    _wrap_post(provider, _SERP_FIXTURE)
    result = await provider.serp_features("flowers near me", location_code=2840)
    assert result.keyword == "flowers near me"
    assert result.total_count == 3
    assert set(result.features_present) == {"answer_box", "organic", "people_also_ask"}
    assert result.items[0].feature_type == "answer_box"
    assert result.items[1].description == "snip"
    assert result.items[2].url is None


@pytest.mark.asyncio
async def test_serp_features_records_cost(provider) -> None:
    _wrap_post(provider, _SERP_FIXTURE)
    with patch("src.seo.providers.dataforseo._cost_recorder.record",
               new=AsyncMock()) as mock_rec:
        await provider.serp_features("k")
    mock_rec.assert_awaited_once()
    args, kwargs = mock_rec.call_args
    assert args[0] == "dataforseo" and args[1] == "serp_features"


@pytest.mark.asyncio
async def test_serp_features_empty_response(provider) -> None:
    _wrap_post(provider, {"tasks": []})
    result = await provider.serp_features("k")
    assert result.total_count == 0
    assert result.items == ()


# --- historical_rank --------------------------------------------------------


_HIST_FIXTURE = {
    "tasks": [{
        "status_code": 20000,
        "result": [{
            "items": [
                {"date": "2025-11-01", "rank": 250, "backlinks": 1200, "referring_domains": 80},
                {"date": "2026-01-01", "rank": 280, "backlinks": 1400, "referring_domains": 90},
                {"date": "2026-04-01", "rank": 295, "backlinks": 1500, "referring_domains": 95},
            ],
        }],
    }],
}


@pytest.mark.asyncio
async def test_historical_rank_returns_time_series(provider) -> None:
    _wrap_post(provider, _HIST_FIXTURE)
    result = await provider.historical_rank("example.com",
                                            date_from="2025-11-01",
                                            date_to="2026-04-01")
    assert result.target == "example.com"
    assert result.date_from == "2025-11-01"
    assert len(result.points) == 3
    assert result.points[0].period == "2025-11-01"
    assert result.points[2].rank == 295
    assert result.points[2].referring_domains == 95


@pytest.mark.asyncio
async def test_historical_rank_records_cost(provider) -> None:
    _wrap_post(provider, _HIST_FIXTURE)
    with patch("src.seo.providers.dataforseo._cost_recorder.record",
               new=AsyncMock()) as mock_rec:
        await provider.historical_rank("example.com")
    mock_rec.assert_awaited_once_with(
        "dataforseo", "historical_rank", cost_usd=pytest.approx(0.05)
    )


@pytest.mark.asyncio
async def test_historical_rank_empty_response(provider) -> None:
    _wrap_post(provider, {"tasks": []})
    result = await provider.historical_rank("example.com")
    assert result.points == ()


# --- business_data_gbp ------------------------------------------------------


_GBP_FIXTURE = {
    "tasks": [{
        "status_code": 20000,
        "result": [{
            "items_count": 2,
            "items": [
                {
                    "title": "Joe's Coffee",
                    "place_id": "ChIJtest1",
                    "cid": "1234567890",
                    "address": "123 Main St, NYC",
                    "domain": "joescoffee.com",
                    "phone": "+1-555-1234",
                    "rating": {"value": 4.6, "votes_count": 213},
                    "category": "Coffee shop",
                    "additional_categories": ["Cafe", "Espresso bar"],
                    "latitude": 40.7,
                    "longitude": -74.0,
                    "url": "https://maps.google.com/?cid=1234567890",
                    "is_claimed": True,
                    "work_hours": {
                        "work_time": {
                            "monday": [{"open": {"hour": 7, "minute": 0},
                                        "close": {"hour": 19, "minute": 0}}],
                            "tuesday": [],
                            "sunday": [{"open": {"hour": 8, "minute": 0},
                                        "close": {"hour": 14, "minute": 0}}],
                        },
                    },
                    "attributes": ["wifi", "outdoor_seating"],
                },
                {
                    "title": "Other Coffee",
                    "place_id": None,
                    "address": "456 Side St",
                    "rating": {},
                    "category": None,
                    "is_claimed": False,
                },
            ],
        }],
    }],
}


@pytest.mark.asyncio
async def test_business_data_gbp_parses_full_record(provider) -> None:
    _wrap_post(provider, _GBP_FIXTURE)
    result = await provider.business_data_gbp("coffee shop", location_code=2840)
    assert result.keyword == "coffee shop"
    assert result.total_count == 2

    first = result.items[0]
    assert first.name == "Joe's Coffee"
    assert first.place_id == "ChIJtest1"
    assert first.rating_value == 4.6
    assert first.rating_count == 213
    assert first.is_claimed is True
    assert first.additional_categories == ("Cafe", "Espresso bar")
    assert first.latitude == 40.7
    assert first.attributes == ("wifi", "outdoor_seating")
    assert first.hours is not None
    assert first.hours.monday == "07:00-19:00"
    assert first.hours.tuesday == "closed"
    assert first.hours.sunday == "08:00-14:00"


@pytest.mark.asyncio
async def test_business_data_gbp_handles_partial_records(provider) -> None:
    _wrap_post(provider, _GBP_FIXTURE)
    result = await provider.business_data_gbp("coffee shop")
    second = result.items[1]
    assert second.name == "Other Coffee"
    assert second.place_id is None
    assert second.rating_value is None
    assert second.is_claimed is False


@pytest.mark.asyncio
async def test_business_data_gbp_records_cost(provider) -> None:
    _wrap_post(provider, _GBP_FIXTURE)
    with patch("src.seo.providers.dataforseo._cost_recorder.record",
               new=AsyncMock()) as mock_rec:
        await provider.business_data_gbp("k")
    mock_rec.assert_awaited_once()
    args, _ = mock_rec.call_args
    assert args[1] == "business_data_gbp"


@pytest.mark.asyncio
async def test_business_data_gbp_empty_response(provider) -> None:
    _wrap_post(provider, {"tasks": []})
    result = await provider.business_data_gbp("k")
    assert result.total_count == 0
    assert result.items == ()


# --- error handling ---------------------------------------------------------


@pytest.mark.asyncio
async def test_serp_features_propagates_dataforseo_error(provider) -> None:
    """status_code >= 40000 → DataForSeoError."""
    from src.seo.exceptions import DataForSeoError

    _wrap_post(provider, {"status_code": 40000, "status_message": "auth fail"})
    with pytest.raises(DataForSeoError):
        await provider.serp_features("k")


@pytest.mark.asyncio
async def test_historical_rank_propagates_task_error(provider) -> None:
    from src.seo.exceptions import DataForSeoError

    _wrap_post(provider, {
        "status_code": 20000,
        "tasks": [{"status_code": 40400, "status_message": "rate limit"}],
    })
    with pytest.raises(DataForSeoError):
        await provider.historical_rank("example.com")
