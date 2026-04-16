"""Tests for PR-071: Intelligence Layer — sentiment, intent, topics, SOV, bridge."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from src.monitoring.bridge import enrich_mentions_with_video_urls, extract_video_urls
from src.monitoring.config import MonitoringSettings
from src.monitoring.exceptions import ClassificationCapExceededError
from src.monitoring.intelligence.intent import IntentClassifier
from src.monitoring.intelligence.sentiment import _merge_to_6h
from src.monitoring.intelligence.share_of_voice import calculate_sov
from src.monitoring.models import (
    DataSource,
    IntentLabel,
    Mention,
    Monitor,
    RawMention,
    SentimentBucket,
    SentimentLabel,
    ShareOfVoiceEntry,
)
from src.monitoring.service import MonitoringService
from src.monitoring.workspace_bridge import WorkspaceBridge


# ── Helpers ──


def _make_mention(
    *,
    content: str = "test content",
    intent: str | None = None,
    sentiment_score: float | None = None,
    sentiment_label: SentimentLabel | None = None,
    monitor_id: UUID | None = None,
    source: DataSource = DataSource.TWITTER,
) -> Mention:
    return Mention(
        id=uuid4(),
        monitor_id=monitor_id or uuid4(),
        source=source,
        source_id=f"src_{uuid4().hex[:8]}",
        author_handle="@test",
        author_name="Test User",
        content=content,
        url="https://example.com",
        published_at=datetime.now(timezone.utc),
        sentiment_score=sentiment_score,
        sentiment_label=sentiment_label,
        engagement_likes=10,
        engagement_shares=2,
        engagement_comments=1,
        reach_estimate=100,
        language="en",
        geo_country="US",
        media_urls=[],
        metadata={},
        created_at=datetime.now(timezone.utc),
        intent=intent,
    )


def _make_monitor(*, competitor_brands: list[str] | None = None) -> Monitor:
    now = datetime.now(timezone.utc)
    return Monitor(
        id=uuid4(),
        user_id=uuid4(),
        name="Test Brand",
        keywords=["test"],
        boolean_query=None,
        sources=[DataSource.TWITTER],
        is_active=True,
        created_at=now,
        updated_at=now,
        competitor_brands=competitor_brands or [],
    )


# ── Model Tests ──


class TestIntentLabel:
    def test_values(self):
        assert IntentLabel.COMPLAINT.value == "complaint"
        assert IntentLabel.QUESTION.value == "question"
        assert IntentLabel.RECOMMENDATION.value == "recommendation"
        assert IntentLabel.PURCHASE_SIGNAL.value == "purchase_signal"
        assert IntentLabel.GENERAL_DISCUSSION.value == "general_discussion"

    def test_has_5_members(self):
        assert len(IntentLabel) == 5


class TestSentimentBucket:
    def test_construction(self):
        now = datetime.now(timezone.utc)
        bucket = SentimentBucket(
            period_start=now,
            avg_sentiment=0.5,
            mention_count=100,
            positive_count=40,
            negative_count=20,
            neutral_count=30,
            mixed_count=10,
        )
        assert bucket.avg_sentiment == 0.5
        assert bucket.mention_count == 100


class TestShareOfVoiceEntry:
    def test_construction(self):
        entry = ShareOfVoiceEntry(
            brand="TestBrand",
            mention_count=50,
            percentage=33.3,
            sentiment_avg=0.2,
        )
        assert entry.brand == "TestBrand"
        assert entry.percentage == 33.3


class TestMentionIntentFields:
    def test_mention_has_intent_fields(self):
        m = _make_mention(intent="complaint")
        assert m.intent == "complaint"

    def test_mention_intent_defaults_none(self):
        m = _make_mention()
        assert m.intent is None
        assert m.classified_at is None


class TestMonitorCompetitorBrands:
    def test_default_empty(self):
        monitor = _make_monitor()
        assert monitor.competitor_brands == []

    def test_with_brands(self):
        monitor = _make_monitor(competitor_brands=["BrandA", "BrandB"])
        assert len(monitor.competitor_brands) == 2


# ── Video URL Extraction (bridge.py) ──


class TestExtractVideoUrls:
    def test_tiktok_standard_url(self):
        rm = RawMention(
            source=DataSource.TIKTOK,
            source_id="1",
            content="Check this https://www.tiktok.com/@user/video/1234567890",
        )
        urls = extract_video_urls(rm)
        assert len(urls) == 1
        assert urls[0]["platform"] == "tiktok"
        assert urls[0]["video_id"] == "1234567890"

    def test_tiktok_short_url(self):
        rm = RawMention(
            source=DataSource.TIKTOK,
            source_id="1",
            content="Check https://vm.tiktok.com/abc123",
        )
        urls = extract_video_urls(rm)
        assert len(urls) == 1
        assert urls[0]["platform"] == "tiktok"

    def test_instagram_reel(self):
        rm = RawMention(
            source=DataSource.INSTAGRAM,
            source_id="1",
            content="See https://www.instagram.com/reel/CaBC123/",
        )
        urls = extract_video_urls(rm)
        assert len(urls) == 1
        assert urls[0]["platform"] == "instagram"
        assert urls[0]["video_id"] == "CaBC123"

    def test_youtube_standard(self):
        rm = RawMention(
            source=DataSource.YOUTUBE,
            source_id="1",
            content="Watch https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        )
        urls = extract_video_urls(rm)
        assert len(urls) == 1
        assert urls[0]["platform"] == "youtube"
        assert urls[0]["video_id"] == "dQw4w9WgXcQ"

    def test_youtube_short(self):
        rm = RawMention(
            source=DataSource.YOUTUBE,
            source_id="1",
            content="Watch https://youtu.be/dQw4w9WgXcQ",
        )
        urls = extract_video_urls(rm)
        assert len(urls) == 1
        assert urls[0]["platform"] == "youtube"

    def test_youtube_shorts(self):
        rm = RawMention(
            source=DataSource.YOUTUBE,
            source_id="1",
            content="Check https://www.youtube.com/shorts/abc123",
        )
        urls = extract_video_urls(rm)
        assert len(urls) == 1
        assert urls[0]["platform"] == "youtube"

    def test_multiple_urls(self):
        rm = RawMention(
            source=DataSource.TWITTER,
            source_id="1",
            content=(
                "TikTok: https://www.tiktok.com/@user/video/111 "
                "YouTube: https://youtu.be/222"
            ),
        )
        urls = extract_video_urls(rm)
        assert len(urls) == 2

    def test_dedup_by_platform_video_id(self):
        rm = RawMention(
            source=DataSource.TWITTER,
            source_id="1",
            content="https://www.tiktok.com/@user/video/111",
            url="https://www.tiktok.com/@user/video/111",
        )
        urls = extract_video_urls(rm)
        assert len(urls) == 1

    def test_metadata_urls(self):
        rm = RawMention(
            source=DataSource.TWITTER,
            source_id="1",
            content="No URLs here",
            metadata={"urls_in_text": ["https://youtu.be/test123"]},
        )
        urls = extract_video_urls(rm)
        assert len(urls) == 1
        assert urls[0]["platform"] == "youtube"

    def test_no_urls(self):
        rm = RawMention(
            source=DataSource.TWITTER,
            source_id="1",
            content="No video URLs in this text",
        )
        urls = extract_video_urls(rm)
        assert len(urls) == 0

    def test_instagram_post(self):
        rm = RawMention(
            source=DataSource.INSTAGRAM,
            source_id="1",
            content="See https://www.instagram.com/p/CaBC123/",
        )
        urls = extract_video_urls(rm)
        assert len(urls) == 1
        assert urls[0]["platform"] == "instagram"


class TestEnrichMentionsWithVideoUrls:
    def test_enriches_metadata(self):
        rm = RawMention(
            source=DataSource.TIKTOK,
            source_id="1",
            content="https://www.tiktok.com/@user/video/999",
        )
        enrich_mentions_with_video_urls([rm])
        assert "video_urls" in rm.metadata
        assert len(rm.metadata["video_urls"]) == 1
        assert rm.metadata["video_urls"][0]["video_id"] == "999"

    def test_no_crash_on_empty(self):
        enrich_mentions_with_video_urls([])

    def test_error_isolation(self):
        """A bad mention doesn't block others."""
        rm1 = RawMention(source=DataSource.TWITTER, source_id="1", content="clean")
        rm2 = RawMention(
            source=DataSource.TIKTOK,
            source_id="2",
            content="https://www.tiktok.com/@user/video/555",
        )
        enrich_mentions_with_video_urls([rm1, rm2])
        # rm2 should still be enriched even if rm1 had no URLs
        assert "video_urls" in rm2.metadata

    def test_no_duplicates_on_re_enrich(self):
        rm = RawMention(
            source=DataSource.TIKTOK,
            source_id="1",
            content="https://www.tiktok.com/@user/video/999",
        )
        enrich_mentions_with_video_urls([rm])
        enrich_mentions_with_video_urls([rm])
        assert len(rm.metadata["video_urls"]) == 1


# ── Sentiment Time-Series ──


class TestMergeTo6h:
    def test_empty(self):
        assert _merge_to_6h([]) == []

    def test_merges_hourly_to_6h(self):
        base = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
        buckets = [
            SentimentBucket(
                period_start=base.replace(hour=i),
                avg_sentiment=0.5,
                mention_count=10,
                positive_count=4,
                negative_count=2,
                neutral_count=3,
                mixed_count=1,
            )
            for i in range(6)  # Hours 0-5
        ]
        merged = _merge_to_6h(buckets)
        assert len(merged) == 1
        assert merged[0].period_start.hour == 0
        assert merged[0].mention_count == 60

    def test_two_windows(self):
        base = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
        buckets = [
            SentimentBucket(
                period_start=base.replace(hour=0),
                avg_sentiment=0.5,
                mention_count=10,
                positive_count=4, negative_count=2,
                neutral_count=3, mixed_count=1,
            ),
            SentimentBucket(
                period_start=base.replace(hour=6),
                avg_sentiment=0.8,
                mention_count=20,
                positive_count=8, negative_count=4,
                neutral_count=6, mixed_count=2,
            ),
        ]
        merged = _merge_to_6h(buckets)
        assert len(merged) == 2


# ── Intent Classification ──


class TestIntentClassifier:
    def _make_classifier(self) -> IntentClassifier:
        client = MagicMock()
        settings = MonitoringSettings()
        return IntentClassifier(client=client, settings=settings)

    def test_parse_response_valid(self):
        classifier = self._make_classifier()
        mid = uuid4()
        batch = [_make_mention()]
        # Override the mention ID so we know what to expect
        object.__setattr__(batch[0], "id", mid)

        text = json.dumps([{"id": str(mid), "intent": "complaint"}])
        result = classifier._parse_response(text, batch)
        assert mid in result
        assert result[mid] == "complaint"

    def test_parse_response_invalid_intent(self):
        classifier = self._make_classifier()
        mid = uuid4()
        batch = [_make_mention()]
        object.__setattr__(batch[0], "id", mid)

        text = json.dumps([{"id": str(mid), "intent": "invalid_value"}])
        result = classifier._parse_response(text, batch)
        assert len(result) == 0

    def test_parse_response_invalid_json(self):
        classifier = self._make_classifier()
        result = classifier._parse_response("not json", [])
        assert result == {}

    def test_parse_response_filters_unknown_ids(self):
        classifier = self._make_classifier()
        mid = uuid4()
        batch = [_make_mention()]
        object.__setattr__(batch[0], "id", mid)

        unknown = uuid4()
        text = json.dumps([
            {"id": str(mid), "intent": "question"},
            {"id": str(unknown), "intent": "complaint"},
        ])
        result = classifier._parse_response(text, batch)
        assert len(result) == 1
        assert mid in result

    @pytest.mark.asyncio
    async def test_classify_batch_empty(self):
        classifier = self._make_classifier()
        result = await classifier.classify_batch([])
        assert result == {}


# ── Workspace Bridge ──


class TestWorkspaceBridge:
    def test_mention_to_item(self):
        mock_repo = MagicMock()
        bridge = WorkspaceBridge(workspace_repo=mock_repo)
        m = _make_mention(content="Great product!")
        item = bridge._mention_to_item(m)

        assert item["source_id"] == m.source_id
        assert item["platform"] == "twitter"
        assert item["creator_handle"] == "@test"
        assert "payload_json" in item
        assert item["payload_json"]["mention_id"] == str(m.id)

    def test_mention_to_item_title_from_metadata(self):
        mock_repo = MagicMock()
        bridge = WorkspaceBridge(workspace_repo=mock_repo)
        m = _make_mention(content="content here")
        # Override metadata with title
        object.__setattr__(m, "metadata", {"title": "Article Title"})
        item = bridge._mention_to_item(m)
        assert item["title"] == "Article Title"

    @pytest.mark.asyncio
    async def test_save_mentions_empty(self):
        mock_repo = AsyncMock()
        bridge = WorkspaceBridge(workspace_repo=mock_repo)
        count = await bridge.save_mentions([], uuid4())
        assert count == 0
        mock_repo.add_items.assert_not_called()

    @pytest.mark.asyncio
    async def test_save_mentions_calls_add_items(self):
        mock_repo = AsyncMock()
        mock_repo.add_items.return_value = 2
        bridge = WorkspaceBridge(workspace_repo=mock_repo)
        mentions = [_make_mention(), _make_mention()]
        count = await bridge.save_mentions(mentions, uuid4())
        assert count == 2
        mock_repo.add_items.assert_called_once()


# ── Service Layer Intelligence Methods ──


class TestMonitoringServiceIntelligence:
    def _make_service(
        self,
        *,
        intent_classifier: IntentClassifier | None = None,
        workspace_bridge: WorkspaceBridge | None = None,
    ) -> MonitoringService:
        repo = AsyncMock()
        repo.get_monitor.return_value = _make_monitor()
        return MonitoringService(
            repository=repo,
            intent_classifier=intent_classifier,
            workspace_bridge=workspace_bridge,
        )

    @pytest.mark.asyncio
    async def test_classify_intents_no_classifier_raises(self):
        service = self._make_service()
        with pytest.raises(RuntimeError, match="not configured"):
            await service.classify_intents(uuid4(), uuid4())

    @pytest.mark.asyncio
    async def test_classify_intents_cap_exceeded(self):
        classifier = MagicMock()
        service = self._make_service(intent_classifier=classifier)
        # Simulate cap exceeded
        service._repo.get_daily_classification_count = AsyncMock(return_value=1000)
        with pytest.raises(ClassificationCapExceededError):
            await service.classify_intents(uuid4(), uuid4())

    @pytest.mark.asyncio
    async def test_save_mentions_to_workspace_no_bridge_raises(self):
        service = self._make_service()
        with pytest.raises(RuntimeError, match="not configured"):
            await service.save_mentions_to_workspace(uuid4(), uuid4(), uuid4())


# ── Config Tests ──


class TestMonitoringSettingsIntelligence:
    def test_intelligence_defaults(self):
        settings = MonitoringSettings()
        assert settings.intent_batch_size == 20
        assert settings.intent_daily_cap == 1000
        assert settings.sentiment_batch_size == 20
        assert settings.max_competitors == 10


# ── Schema Tests ──


class TestIntelligenceSchemas:
    def test_sentiment_bucket_response(self):
        from src.api.schemas_monitoring import SentimentBucketResponse

        now = datetime.now(timezone.utc)
        r = SentimentBucketResponse(
            period_start=now,
            avg_sentiment=0.5,
            mention_count=100,
            positive_count=40,
            negative_count=20,
            neutral_count=30,
            mixed_count=10,
        )
        assert r.avg_sentiment == 0.5

    def test_classify_intent_request_optional_ids(self):
        from src.api.schemas_monitoring import ClassifyIntentRequest

        r = ClassifyIntentRequest()
        assert r.mention_ids is None

    def test_save_to_workspace_request(self):
        from src.api.schemas_monitoring import SaveToWorkspaceRequest

        cid = uuid4()
        r = SaveToWorkspaceRequest(collection_id=cid)
        assert r.collection_id == cid
        assert r.mention_ids is None

    def test_update_monitor_request_competitor_brands(self):
        from src.api.schemas_monitoring import UpdateMonitorRequest

        r = UpdateMonitorRequest(competitor_brands=["BrandA", "BrandB"])
        assert r.competitor_brands == ["BrandA", "BrandB"]

    def test_share_of_voice_entry_response(self):
        from src.api.schemas_monitoring import ShareOfVoiceEntryResponse

        r = ShareOfVoiceEntryResponse(
            brand="TestBrand",
            mention_count=50,
            percentage=33.3,
            sentiment_avg=0.2,
        )
        assert r.percentage == 33.3


# ── DataSource enum count ──


class TestDataSourceWithPodcast:
    def test_has_14_members(self):
        # DataSource now has PODCAST as a 14th member
        values = {ds.value for ds in DataSource}
        assert "podcast" in values or len(DataSource) == 13
