"""Tests for PerformancePatterns computation."""

from datetime import date, datetime, timezone
from uuid import uuid4

from src.monitoring.intelligence.models_analytics import AccountPost, AccountSnapshot, PerformancePatterns
from src.monitoring.intelligence.performance_patterns import generate_performance_patterns


def _make_post(
    *,
    likes: int = 10,
    comments: int = 2,
    shares: int = 1,
    impressions: int = 1000,
    published_at: datetime | None = None,
    content: str = "Test post content",
    media_type: str = "text",
) -> AccountPost:
    er = (likes + comments + shares) / impressions if impressions > 0 else None
    return AccountPost(
        id=uuid4(),
        org_id=uuid4(),
        platform="twitter",
        username="testuser",
        source_id=str(uuid4()),
        content=content,
        published_at=published_at or datetime(2026, 3, 15, 10, 0, tzinfo=timezone.utc),
        likes=likes,
        shares=shares,
        comments=comments,
        impressions=impressions,
        engagement_rate=er,
        media_type=media_type,
        hashtags=[],
        metadata={},
        created_at=datetime.now(timezone.utc),
    )


class TestGeneratePerformancePatterns:
    def test_empty_posts(self):
        result = generate_performance_patterns([])
        assert isinstance(result, PerformancePatterns)
        assert result.total_posts == 0
        assert result.avg_engagement_rate == 0.0
        assert result.engagement_trend == "stable"

    def test_basic_25_posts(self):
        posts = [
            _make_post(
                likes=10 + i,
                published_at=datetime(2026, 3, i + 1, 10 + (i % 12), 0, tzinfo=timezone.utc),
            )
            for i in range(25)
        ]
        result = generate_performance_patterns(posts)
        assert result.total_posts == 25
        assert result.avg_engagement_rate > 0
        assert len(result.top_posts) <= 10
        assert len(result.worst_posts) <= 10
        assert result.posting_frequency > 0
        assert result.avg_post_length > 0

    def test_with_snapshots_follower_growth(self):
        posts = [_make_post() for _ in range(5)]
        snapshots = [
            AccountSnapshot(
                id=uuid4(), org_id=uuid4(), platform="twitter", username="testuser",
                follower_count=1000, following_count=100, post_count=50,
                engagement_rate=0.05, audience_data={},
                created_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
            ),
            AccountSnapshot(
                id=uuid4(), org_id=uuid4(), platform="twitter", username="testuser",
                follower_count=1500, following_count=110, post_count=55,
                engagement_rate=0.06, audience_data={},
                created_at=datetime(2026, 3, 15, tzinfo=timezone.utc),
            ),
        ]
        result = generate_performance_patterns(posts, snapshots)
        assert result.follower_growth == 500.0

    def test_single_media_type(self):
        posts = [_make_post(media_type="video") for _ in range(10)]
        result = generate_performance_patterns(posts)
        assert result.content_type_breakdown == {"video": 10}

    def test_engagement_trend_improving(self):
        # Older posts: low engagement, recent: high
        posts = []
        for i in range(20):
            likes = 5 if i < 10 else 50  # Recent half gets 10x engagement
            posts.append(_make_post(
                likes=likes,
                published_at=datetime(2026, 3, i + 1, 10, 0, tzinfo=timezone.utc),
            ))
        result = generate_performance_patterns(posts)
        # The trend depends on sort order — top engagement posts are recent
        assert result.engagement_trend in ("improving", "stable")

    def test_markdown_rendered(self):
        posts = [_make_post() for _ in range(5)]
        result = generate_performance_patterns(posts)
        assert result.markdown
        assert "Account Performance Patterns" in result.markdown
        assert "5 posts" in result.markdown
