"""Tests for PR-075 Tier 1 default source changes."""

from src.api.routers.discover import DEFAULT_FREE_SOURCES, SOURCE_METADATA
from src.monitoring.models import DataSource


class TestDefaultFreeSources:
    def test_includes_newsdata(self):
        assert DataSource.NEWSDATA in DEFAULT_FREE_SOURCES

    def test_includes_podcast(self):
        assert DataSource.PODCAST in DEFAULT_FREE_SOURCES

    def test_includes_original_four(self):
        for ds in (DataSource.TWITTER, DataSource.INSTAGRAM, DataSource.REDDIT, DataSource.BLUESKY):
            assert ds in DEFAULT_FREE_SOURCES

    def test_total_count_is_six(self):
        assert len(DEFAULT_FREE_SOURCES) == 6


class TestSourceMetadataCostTiers:
    def test_newsdata_is_free(self):
        assert SOURCE_METADATA[DataSource.NEWSDATA]["cost_tier"] == "free"

    def test_podcast_is_free(self):
        assert SOURCE_METADATA[DataSource.PODCAST]["cost_tier"] == "free"

    def test_twitter_is_free(self):
        assert SOURCE_METADATA[DataSource.TWITTER]["cost_tier"] == "free"

    def test_tiktok_is_not_free(self):
        assert SOURCE_METADATA[DataSource.TIKTOK]["cost_tier"] != "free"
