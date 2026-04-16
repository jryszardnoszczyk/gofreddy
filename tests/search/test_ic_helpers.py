"""Tests for shared IC helper functions (build_ic_filters, normalize_ic_account)."""

import pytest

from src.search.ic_helpers import build_ic_filters, normalize_ic_account


class TestBuildIcFilters:
    """Tests for build_ic_filters."""

    def test_empty_filters(self):
        filters, sort = build_ic_filters()
        assert filters == {}
        assert sort == "followers"

    def test_keywords(self):
        filters, _ = build_ic_filters(keywords="fitness influencer")
        assert filters["ai_search"] == "fitness influencer"

    def test_keywords_truncated(self):
        long_kw = "x" * 600
        filters, _ = build_ic_filters(keywords=long_kw)
        assert len(filters["ai_search"]) == 500

    def test_followers_range(self):
        filters, _ = build_ic_filters(min_followers=1000, max_followers=50000)
        assert filters["number_of_followers"] == {"min": 1000, "max": 50000}

    def test_followers_min_only(self):
        filters, _ = build_ic_filters(min_followers=5000)
        assert filters["number_of_followers"] == {"min": 5000}

    def test_engagement_rate_multiplied(self):
        """Engagement rate input is decimal (3.5 = 3.5%), IC API wants 350."""
        filters, _ = build_ic_filters(min_engagement_rate=3.5)
        assert filters["engagement_percent"] == {"min": 350.0}

    def test_hashtags(self):
        filters, _ = build_ic_filters(hashtags=["fitness", "workout"])
        assert filters["hashtags"] == ["fitness", "workout"]

    def test_is_verified(self):
        filters, _ = build_ic_filters(is_verified=True)
        assert filters["is_verified"] is True

    def test_creator_gender_lowered(self):
        filters, _ = build_ic_filters(creator_gender="MALE")
        assert filters["gender"] == "male"

    def test_audience_location(self):
        filters, _ = build_ic_filters(audience_location="United States")
        assert filters["audience"]["location"] == [
            {"name": "United States", "type": "country", "min_pct": 10}
        ]

    def test_audience_credibility(self):
        filters, _ = build_ic_filters(audience_credibility="Good")
        assert filters["audience"]["credibility"] == "good"

    def test_audience_gender(self):
        filters, _ = build_ic_filters(audience_gender="FEMALE")
        assert filters["audience"]["gender"] == {"type": "female", "min_pct": 50}

    def test_audience_age_range(self):
        filters, _ = build_ic_filters(audience_age_min=18, audience_age_max=34)
        assert filters["audience"]["age"] == [{"range": "18-34", "min_pct": 10}]

    def test_audience_age_defaults(self):
        filters, _ = build_ic_filters(audience_age_min=25)
        assert filters["audience"]["age"] == [{"range": "25-65", "min_pct": 10}]

    def test_audience_language(self):
        filters, _ = build_ic_filters(audience_language="en")
        assert filters["audience"]["language"] == [{"language_abbr": "en", "min_pct": 10}]

    def test_multiple_audience_filters_nested(self):
        """Multiple audience filters should all be under the same 'audience' key."""
        filters, _ = build_ic_filters(
            audience_location="US", audience_gender="MALE", audience_language="en",
        )
        aud = filters["audience"]
        assert "location" in aud
        assert "gender" in aud
        assert "language" in aud

    def test_has_sponsored_posts(self):
        filters, _ = build_ic_filters(has_sponsored_posts=True)
        assert filters["has_done_brand_deals"] is True

    def test_topic_relevance(self):
        filters, _ = build_ic_filters(topic_relevance=["fitness", "health"])
        assert filters["keywords_in_captions"] == ["fitness", "health"]

    def test_brand_affinity(self):
        filters, _ = build_ic_filters(brand_affinity=["Nike", "Adidas"])
        assert filters["brands"] == ["Nike", "Adidas"]

    def test_content_count_min(self):
        filters, _ = build_ic_filters(content_count_min=50)
        assert filters["number_of_posts"] == {"min": 50}

    def test_sort_by_relevance(self):
        _, sort = build_ic_filters(sort_by="RELEVANCE")
        assert sort == "relevancy"

    def test_sort_by_follower_count(self):
        _, sort = build_ic_filters(sort_by="FOLLOWER_COUNT")
        assert sort == "followers"

    def test_sort_by_engagement(self):
        _, sort = build_ic_filters(sort_by="ENGAGEMENT_RATE")
        assert sort == "followers"


class TestNormalizeIcAccount:
    """Tests for normalize_ic_account."""

    def test_basic_normalization(self):
        raw = {
            "user_id": "abc-123",
            "profile": {
                "username": "jane_fitness",
                "full_name": "Jane Doe",
                "followers": 50000,
                "engagement_percent": 3.5,
                "is_verified": True,
                "picture": "https://example.com/pic.jpg",
            },
        }
        result = normalize_ic_account(raw, "instagram")

        assert result["username"] == "jane_fitness"
        assert result["platform"] == "instagram"
        assert result["display_name"] == "Jane Doe"
        assert result["follower_count"] == 50000
        assert result["engagement_rate"] == pytest.approx(0.035, abs=1e-4)
        assert result["is_verified"] is True
        assert result["image_url"] == "https://example.com/pic.jpg"
        assert result["external_id"] == "abc-123"
        assert result["data_source"] == "influencersclub"

    def test_missing_profile(self):
        """When profile key is missing, treat raw dict itself as profile."""
        raw = {"username": "test", "followers": 100}
        result = normalize_ic_account(raw, "tiktok")
        assert result["username"] == "test"
        assert result["follower_count"] == 100
        assert result["platform"] == "tiktok"

    def test_missing_engagement(self):
        raw = {"profile": {"username": "noeng"}}
        result = normalize_ic_account(raw, "instagram")
        assert result["engagement_rate"] is None

    def test_external_id_preserved(self):
        """external_id must come from raw['user_id'], not be None."""
        raw = {"user_id": "uid-456", "profile": {"username": "test"}}
        result = normalize_ic_account(raw, "instagram")
        assert result["external_id"] == "uid-456"

    def test_external_id_missing(self):
        raw = {"profile": {"username": "test"}}
        result = normalize_ic_account(raw, "instagram")
        assert result["external_id"] is None

    def test_none_username_becomes_empty_string(self):
        raw = {"profile": {"username": None}}
        result = normalize_ic_account(raw, "instagram")
        assert result["username"] == ""

    def test_all_optional_fields_present(self):
        """All keys expected by _merge_creators should be present."""
        raw = {"profile": {"username": "test"}}
        result = normalize_ic_account(raw, "instagram")
        expected_keys = {
            "username", "platform", "display_name", "follower_count",
            "following_count", "engagement_rate", "average_likes",
            "average_views", "content_count", "is_verified", "bio",
            "profile_url", "image_url", "external_id", "is_inauthentic",
            "inauthentic_prob_score", "relevance_score", "relevant_posts_count",
            "audience_top_country", "data_source",
        }
        assert set(result.keys()) == expected_keys
