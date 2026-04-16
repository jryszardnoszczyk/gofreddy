"""Tests for fraud IC engagement enrichment (PR-097).

Covers: _parse_ic_engagement helper, _fetch_ic_engagement helper,
and IC fallback integration in the fraud router.
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock

import pytest

from src.api.routers.fraud import _fetch_ic_engagement, _parse_ic_engagement


# ── _parse_ic_engagement tests ──────────────────────────────────────────


class TestParseICEngagement:
    """Test IC response parsing into (avg_likes, avg_comments)."""

    def test_valid_instagram_response(self):
        """Standard IC enrich_full response with engagement data."""
        ic_response: dict[str, Any] = {
            "result": {
                "instagram": {
                    "engagement_percent": 4.2,
                    "follower_count": 100000,
                }
            }
        }
        avg_likes, avg_comments = _parse_ic_engagement(ic_response, "instagram")
        assert avg_likes == pytest.approx(4200.0)
        assert avg_comments == 0.0

    def test_valid_tiktok_response(self):
        """TikTok platform key in IC response."""
        ic_response: dict[str, Any] = {
            "result": {
                "tiktok": {
                    "engagement_percent": 8.5,
                    "follower_count": 50000,
                }
            }
        }
        avg_likes, avg_comments = _parse_ic_engagement(ic_response, "tiktok")
        assert avg_likes == pytest.approx(4250.0)
        assert avg_comments == 0.0

    def test_none_response(self):
        """None IC response returns (None, None)."""
        assert _parse_ic_engagement(None, "instagram") == (None, None)

    def test_empty_response(self):
        """Empty dict returns (None, None)."""
        assert _parse_ic_engagement({}, "instagram") == (None, None)

    def test_missing_platform_key(self):
        """Response without the requested platform returns (None, None)."""
        ic_response: dict[str, Any] = {
            "result": {"tiktok": {"engagement_percent": 5.0, "follower_count": 10000}}
        }
        assert _parse_ic_engagement(ic_response, "instagram") == (None, None)

    def test_missing_engagement_percent(self):
        """Missing engagement_percent returns (None, None)."""
        ic_response: dict[str, Any] = {
            "result": {"instagram": {"follower_count": 10000}}
        }
        assert _parse_ic_engagement(ic_response, "instagram") == (None, None)

    def test_zero_engagement_percent(self):
        """engagement_percent=0.0 is valid, not treated as None."""
        ic_response: dict[str, Any] = {
            "result": {
                "instagram": {
                    "engagement_percent": 0.0,
                    "follower_count": 100000,
                }
            }
        }
        avg_likes, avg_comments = _parse_ic_engagement(ic_response, "instagram")
        # 0.0 engagement_percent is not None, but eng_pct is 0.0 which passes `is not None`
        # however follower_count is truthy, so avg_likes = 0.0 * 100000 / 100 = 0.0
        assert avg_likes == 0.0
        assert avg_comments == 0.0

    def test_zero_follower_count(self):
        """follower_count=0 is falsy, returns (None, None)."""
        ic_response: dict[str, Any] = {
            "result": {
                "instagram": {
                    "engagement_percent": 5.0,
                    "follower_count": 0,
                }
            }
        }
        assert _parse_ic_engagement(ic_response, "instagram") == (None, None)

    def test_malformed_engagement_percent(self):
        """Non-numeric engagement_percent returns (None, None)."""
        ic_response: dict[str, Any] = {
            "result": {
                "instagram": {
                    "engagement_percent": "not_a_number",
                    "follower_count": 10000,
                }
            }
        }
        assert _parse_ic_engagement(ic_response, "instagram") == (None, None)

    def test_result_not_dict(self):
        """result is not a dict returns (None, None)."""
        ic_response: dict[str, Any] = {"result": "unexpected_string"}
        assert _parse_ic_engagement(ic_response, "instagram") == (None, None)


# ── _fetch_ic_engagement tests ──────────────────────────────────────────


class TestFetchICEngagement:
    """Test IC fetch helper with timeout."""

    @pytest.mark.asyncio
    async def test_returns_none_when_backend_is_none(self):
        """No IC backend → returns None immediately."""
        result = await _fetch_ic_engagement(None, "instagram", "testuser")
        assert result is None

    @pytest.mark.asyncio
    async def test_calls_enrich_full(self):
        """Calls ic_backend.enrich_full with correct params."""
        mock_backend = AsyncMock()
        mock_backend.enrich_full = AsyncMock(return_value={"result": {"instagram": {}}})
        result = await _fetch_ic_engagement(mock_backend, "instagram", "testuser")
        mock_backend.enrich_full.assert_awaited_once_with(
            "instagram", "testuser", include_audience_data=False
        )
        assert result == {"result": {"instagram": {}}}

    @pytest.mark.asyncio
    async def test_timeout_raises(self):
        """IC call exceeding 15s timeout raises TimeoutError."""

        async def slow_enrich(*args, **kwargs):
            await asyncio.sleep(20)
            return {}

        mock_backend = AsyncMock()
        mock_backend.enrich_full = slow_enrich
        with pytest.raises(asyncio.TimeoutError):
            await _fetch_ic_engagement(mock_backend, "instagram", "testuser")
