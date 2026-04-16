"""Tests for advanced filter routing in SearchService.

Verifies SearchFilters and SearchResult fields for audience/creator filters.
"""

from src.common.enums import Platform
from src.search.service import SearchFilters, SearchResult


class TestSearchFiltersNewFields:
    """Verify new SearchFilters fields exist and default to None."""

    def test_new_fields_default_none(self):
        f = SearchFilters()
        assert f.is_verified is None
        assert f.creator_gender is None
        assert f.creator_language is None
        assert f.creator_location is None
        assert f.audience_location is None
        assert f.audience_gender is None
        assert f.audience_age_min is None
        assert f.audience_age_max is None
        assert f.audience_language is None
        assert f.last_post_timestamp is None

    def test_new_fields_settable(self):
        f = SearchFilters(
            is_verified=True,
            creator_gender="female",
            audience_location="United States",
            audience_age_min=18,
            audience_age_max=34,
        )
        assert f.is_verified is True
        assert f.creator_gender == "female"
        assert f.audience_location == "United States"
        assert f.audience_age_min == 18
        assert f.audience_age_max == 34

    def test_backward_compatible(self):
        """Old-style filter creation still works."""
        f = SearchFilters(
            query="fitness",
            min_followers=1000,
            min_engagement_rate=0.03,
        )
        assert f.query == "fitness"
        assert f.min_followers == 1000


class TestSearchResultNewFields:
    """Verify new SearchResult fields exist and are optional."""

    def test_new_fields_default_none(self):
        r = SearchResult(platform=Platform.INSTAGRAM, creator_handle="test")
        assert r.is_verified is None
        assert r.content_count is None
        assert r.following_count is None

    def test_new_fields_settable(self):
        r = SearchResult(
            platform=Platform.TIKTOK,
            creator_handle="test",
            is_verified=True,
            content_count=500,
            following_count=200,
        )
        assert r.is_verified is True
        assert r.content_count == 500
        assert r.following_count == 200
