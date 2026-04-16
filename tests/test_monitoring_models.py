"""Tests for monitoring domain models."""

from datetime import datetime, timezone
from uuid import uuid4

from src.monitoring.models import (
    DataSource,
    DigestStory,
    Mention,
    Monitor,
    MonitorSourceCursor,
    RawMention,
    SentimentLabel,
    SourceSentiment,
    WeeklyDigestRecord,
    platform_to_datasource,
)


class TestDataSource:
    def test_has_15_members(self):
        assert len(DataSource) == 15

    def test_threads_not_present(self):
        values = [ds.value for ds in DataSource]
        assert "threads" not in values

    def test_values_are_lowercase(self):
        for ds in DataSource:
            assert ds.value == ds.value.lower()

    def test_specific_members(self):
        expected = {
            "twitter", "instagram", "reddit", "tiktok", "youtube",
            "facebook", "linkedin", "bluesky", "newsdata",
            "trustpilot", "app_store", "play_store", "google_trends",
            "podcast", "ai_search",
        }
        actual = {ds.value for ds in DataSource}
        assert actual == expected


class TestSentimentLabel:
    def test_values(self):
        assert SentimentLabel.POSITIVE.value == "positive"
        assert SentimentLabel.NEGATIVE.value == "negative"
        assert SentimentLabel.NEUTRAL.value == "neutral"
        assert SentimentLabel.MIXED.value == "mixed"


class TestPlatformToDatasource:
    def test_known_mappings(self):
        assert platform_to_datasource("tiktok") == DataSource.TIKTOK
        assert platform_to_datasource("instagram") == DataSource.INSTAGRAM
        assert platform_to_datasource("youtube") == DataSource.YOUTUBE

    def test_unknown_returns_none(self):
        assert platform_to_datasource("twitter") is None
        assert platform_to_datasource("unknown") is None


class TestMonitor:
    def test_construction(self):
        now = datetime.now(timezone.utc)
        monitor = Monitor(
            id=uuid4(),
            user_id=uuid4(),
            name="Test Monitor",
            keywords=["brand", "product"],
            boolean_query="brand AND product",
            sources=[DataSource.TWITTER, DataSource.INSTAGRAM],
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        assert monitor.name == "Test Monitor"
        assert len(monitor.sources) == 2
        assert monitor.is_active is True

    def test_client_id_default_none(self):
        now = datetime.now(timezone.utc)
        monitor = Monitor(
            id=uuid4(), user_id=uuid4(), name="Test",
            keywords=[], boolean_query=None,
            sources=[], is_active=True,
            created_at=now, updated_at=now,
        )
        assert monitor.client_id is None

    def test_client_id_set(self):
        now = datetime.now(timezone.utc)
        cid = uuid4()
        monitor = Monitor(
            id=uuid4(), user_id=uuid4(), name="Test",
            keywords=[], boolean_query=None,
            sources=[], is_active=True,
            created_at=now, updated_at=now,
            client_id=cid,
        )
        assert monitor.client_id == cid

    def test_frozen(self):
        now = datetime.now(timezone.utc)
        monitor = Monitor(
            id=uuid4(), user_id=uuid4(), name="Test",
            keywords=[], boolean_query=None,
            sources=[], is_active=True,
            created_at=now, updated_at=now,
        )
        try:
            monitor.name = "New Name"  # type: ignore[misc]
            assert False, "Should raise"
        except AttributeError:
            pass


class TestMention:
    def test_construction(self):
        now = datetime.now(timezone.utc)
        mention = Mention(
            id=uuid4(),
            monitor_id=uuid4(),
            source=DataSource.TWITTER,
            source_id="tweet_123",
            author_handle="@user",
            author_name="User Name",
            content="Brand mentioned here",
            url="https://twitter.com/user/status/123",
            published_at=now,
            sentiment_score=0.8,
            sentiment_label=SentimentLabel.POSITIVE,
            engagement_likes=100,
            engagement_shares=10,
            engagement_comments=5,
            reach_estimate=1000,
            language="en",
            geo_country="US",
            media_urls=["https://example.com/img.jpg"],
            metadata={"retweet_count": 10},
            created_at=now,
        )
        assert mention.source == DataSource.TWITTER
        assert mention.engagement_likes == 100
        assert mention.sentiment_label == SentimentLabel.POSITIVE

    def test_frozen(self):
        now = datetime.now(timezone.utc)
        mention = Mention(
            id=uuid4(), monitor_id=uuid4(),
            source=DataSource.TWITTER, source_id="1",
            author_handle=None, author_name=None,
            content="", url=None, published_at=None,
            sentiment_score=None, sentiment_label=None,
            engagement_likes=0, engagement_shares=0, engagement_comments=0,
            reach_estimate=None, language="en", geo_country=None,
            media_urls=[], metadata={}, created_at=now,
        )
        try:
            mention.content = "new"  # type: ignore[misc]
            assert False, "Should raise"
        except AttributeError:
            pass


class TestMonitorSourceCursor:
    def test_construction(self):
        now = datetime.now(timezone.utc)
        cursor = MonitorSourceCursor(
            monitor_id=uuid4(),
            source=DataSource.NEWSDATA,
            cursor_value="page_2_token",
            updated_at=now,
        )
        assert cursor.cursor_value == "page_2_token"
        assert cursor.source == DataSource.NEWSDATA


class TestRawMention:
    def test_defaults(self):
        rm = RawMention(source=DataSource.TWITTER, source_id="1")
        assert rm.content == ""
        assert rm.engagement_likes == 0
        assert rm.engagement_shares == 0
        assert rm.engagement_comments == 0
        assert rm.language == "en"
        assert rm.media_urls == []
        assert rm.metadata == {}
        assert rm.author_handle is None

    def test_mutable(self):
        rm = RawMention(source=DataSource.REDDIT, source_id="abc")
        rm.content = "updated content"
        rm.sentiment_score = 0.5
        rm.sentiment_label = SentimentLabel.POSITIVE
        assert rm.content == "updated content"
        assert rm.sentiment_score == 0.5

    def test_no_shared_defaults(self):
        """Ensure list/dict defaults are not shared between instances."""
        rm1 = RawMention(source=DataSource.TWITTER, source_id="1")
        rm2 = RawMention(source=DataSource.TWITTER, source_id="2")
        rm1.media_urls.append("https://example.com")
        assert rm2.media_urls == []
        rm1.metadata["key"] = "value"
        assert rm2.metadata == {}


class TestDigestStory:
    def test_construction(self):
        story = DigestStory(
            story_label="pricing-backlash",
            daily_clusters=[uuid4(), uuid4()],
            mention_ids=[uuid4(), uuid4(), uuid4()],
            total_mention_count=47,
            days_active=5,
            significance_score=12.5,
            sentiment_trajectory=[-0.2, -0.4, -0.6],
            sources=["reddit", "twitter", "newsdata"],
            linked_alerts=[uuid4()],
        )
        assert story.total_mention_count == 47
        assert len(story.sources) == 3
        assert story.days_active == 5

    def test_frozen(self):
        story = DigestStory(
            story_label="test", daily_clusters=[], mention_ids=[],
            total_mention_count=0, days_active=0, significance_score=0.0,
            sentiment_trajectory=[], sources=[], linked_alerts=[],
        )
        try:
            story.story_label = "new"  # type: ignore[misc]
            assert False, "Should raise"
        except AttributeError:
            pass


class TestSourceSentiment:
    def test_construction(self):
        now = datetime.now(timezone.utc)
        ss = SourceSentiment(
            source=DataSource.REDDIT,
            avg_sentiment=-0.35,
            mention_count=42,
            bucket=now,
        )
        assert ss.source == DataSource.REDDIT
        assert ss.avg_sentiment == -0.35


class TestWeeklyDigestRecord:
    def test_construction(self):
        from datetime import date as date_type
        now = datetime.now(timezone.utc)
        record = WeeklyDigestRecord(
            id=uuid4(),
            monitor_id=uuid4(),
            client_id=uuid4(),
            week_ending=date_type(2026, 3, 17),
            stories=[{"story_label": "test", "mentions": 10}],
            executive_summary="Summary of the week.",
            action_items=[{"action": "respond to Reddit thread", "owner": "social team"}],
            dqs_score=0.72,
            iteration_count=15,
            avg_story_delta=0.38,
            generated_at=now,
        )
        assert record.iteration_count == 15
        assert record.dqs_score == 0.72
        assert record.client_id is not None
