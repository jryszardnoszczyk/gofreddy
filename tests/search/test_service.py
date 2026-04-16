"""Tests for the search service module — real Gemini for integration, pure logic for others.

Tests marked @pytest.mark.external_api use real Gemini + real platform APIs.
Pure logic tests (CircuitBreaker, normalization, filters) run without external services.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.common.enums import Platform
from src.search.exceptions import QueryParseError, SearchError
from src.search.service import (
    CircuitBreaker,
    ConfidenceLevel,
    GeminiQueryParser,
    ParsedSearchQuery,
    SearchConfig,
    SearchFilters,
    SearchResult,
    SearchScope,
    SearchService,
    SearchType,
)

# Reliability matrix (degraded mode expectations):
# - TikTok: provider errors/429/timeouts -> platform marked failed; other platforms still return.
# - Instagram: malformed/non-dict payload rows are skipped during normalization.
# - YouTube: malformed/non-dict payload rows are skipped during normalization.
# - Aggregation contract: successful providers must still return results with 200-level service response.


# === Circuit Breaker Tests ===


class TestCircuitBreaker:
    """Tests for CircuitBreaker class — pure logic."""

    def test_initial_state_closed(self) -> None:
        """Circuit breaker starts in closed state."""
        cb = CircuitBreaker(failure_threshold=3, reset_timeout=60)
        assert cb.is_open() is False

    def test_opens_after_threshold_failures(self) -> None:
        """Circuit breaker opens after threshold failures."""
        cb = CircuitBreaker(failure_threshold=3, reset_timeout=60)
        cb.record_failure()
        cb.record_failure()
        assert cb.is_open() is False
        cb.record_failure()
        assert cb.is_open() is True

    def test_success_resets_failures(self) -> None:
        """Recording success resets failure count."""
        cb = CircuitBreaker(failure_threshold=3, reset_timeout=60)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert cb.is_open() is False
        cb.record_failure()
        cb.record_failure()
        assert cb.is_open() is False

    def test_resets_after_timeout(self) -> None:
        """Circuit breaker resets after timeout (enters HALF_OPEN)."""
        import time

        cb = CircuitBreaker(failure_threshold=3, reset_timeout=0)
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        cb._last_failure_time = time.monotonic() - 1
        assert cb.is_open() is False


# === Parser Tests ===


class TestGeminiQueryParser:
    """Tests for GeminiQueryParser class — pure logic methods."""

    def test_sanitize_query_removes_control_chars(self) -> None:
        """Sanitize removes control characters."""
        parser = GeminiQueryParser(api_key="test")
        result = parser._sanitize_query("hello\x00world\x1ftest")
        assert result == "helloworldtest"

    def test_sanitize_query_truncates_long_input(self) -> None:
        """Sanitize truncates queries over 500 chars."""
        parser = GeminiQueryParser(api_key="test")
        long_query = "a" * 600
        result = parser._sanitize_query(long_query)
        assert len(result) == 500

    def test_sanitize_query_strips_whitespace(self) -> None:
        """Sanitize strips leading/trailing whitespace."""
        parser = GeminiQueryParser(api_key="test")
        result = parser._sanitize_query("  hello world  ")
        assert result == "hello world"

    def test_compute_confidence_level_high(self) -> None:
        """High confidence computed correctly."""
        parser = GeminiQueryParser(api_key="test")
        assert parser._compute_confidence_level(0.90) == ConfidenceLevel.HIGH
        assert parser._compute_confidence_level(0.85) == ConfidenceLevel.HIGH

    def test_compute_confidence_level_medium(self) -> None:
        """Medium confidence computed correctly."""
        parser = GeminiQueryParser(api_key="test")
        assert parser._compute_confidence_level(0.70) == ConfidenceLevel.MEDIUM
        assert parser._compute_confidence_level(0.60) == ConfidenceLevel.MEDIUM

    def test_compute_confidence_level_low(self) -> None:
        """Low confidence computed correctly."""
        parser = GeminiQueryParser(api_key="test")
        assert parser._compute_confidence_level(0.50) == ConfidenceLevel.LOW
        assert parser._compute_confidence_level(0.30) == ConfidenceLevel.LOW

    def test_fallback_parse_keyword(self) -> None:
        """Fallback parse returns keyword search for regular queries."""
        parser = GeminiQueryParser(api_key="test")
        result = parser._fallback_parse("fitness videos")
        assert result.search_type == SearchType.KEYWORD
        assert result.filters.query == "fitness videos"
        assert result.confidence == 0.3
        assert result.confidence_level == ConfidenceLevel.LOW

    def test_fallback_parse_hashtag(self) -> None:
        """Fallback parse detects hashtag queries."""
        parser = GeminiQueryParser(api_key="test")
        result = parser._fallback_parse("#fitness")
        assert result.search_type == SearchType.HASHTAG
        assert result.filters.hashtags == ["fitness"]
        assert result.confidence == 0.3

    async def test_parse_uses_circuit_breaker_fallback(self) -> None:
        """Parser uses fallback when circuit breaker is open."""
        parser = GeminiQueryParser(api_key="test")
        parser._circuit_breaker._failures = 3
        parser._circuit_breaker._last_failure_time = 9999999999

        result = await parser.parse("fitness videos")
        assert result.confidence == 0.3
        assert "AI parsing unavailable" in result.unsupported_aspects[0]


# === Real Search Integration Tests ===


@pytest.mark.external_api
class TestSearchServiceIntegration:
    """Real Gemini + real platform API search tests."""

    async def test_search_real_keyword(self, search_service):
        """Search with real Gemini parser and real platform fetchers."""
        result = await search_service.search(query="fitness workout videos")
        assert "results" in result
        assert "total" in result
        assert "platforms_searched" in result
        assert isinstance(result["results"], list)

    async def test_search_real_hashtag(self, search_service):
        """Search with hashtag query via real services."""
        result = await search_service.search(query="#dance")
        assert "results" in result
        assert isinstance(result["results"], list)


# === Mock Search Service Tests ===


@pytest.mark.mock_required
class TestSearchServiceMocked:
    """Tests for SearchService with mocked dependencies — for controlled behavior."""

    @pytest.fixture
    def mock_parser(self) -> MagicMock:
        parser = MagicMock(spec=GeminiQueryParser)
        parser.parse = AsyncMock(
            return_value=ParsedSearchQuery(
                scope=SearchScope.VIDEOS,
                platforms=[Platform.TIKTOK],
                search_type=SearchType.KEYWORD,
                filters=SearchFilters(query="fitness"),
                confidence=0.9,
                confidence_level=ConfidenceLevel.HIGH,
            )
        )
        return parser

    @pytest.fixture
    def mock_tiktok_fetcher(self) -> MagicMock:
        fetcher = MagicMock()
        fetcher.search_keyword = AsyncMock(
            return_value=[
                {
                    "aweme_id": "123",
                    "desc": "Fitness video",
                    "author": {"unique_id": "fitness_user", "uid": "456"},
                    "statistics": {"play_count": 1000, "digg_count": 100},
                }
            ]
        )
        fetcher.search_hashtag = AsyncMock(return_value=[])
        return fetcher

    @pytest.fixture
    def mock_instagram_fetcher(self) -> MagicMock:
        fetcher = MagicMock()
        fetcher.search_keyword = AsyncMock(return_value=[])
        fetcher.search_hashtag = AsyncMock(return_value=[])
        return fetcher

    @pytest.fixture
    def mock_youtube_fetcher(self) -> MagicMock:
        fetcher = MagicMock()
        fetcher.search = AsyncMock(return_value=[])
        return fetcher

    @pytest.fixture
    def mock_search_service(
        self,
        mock_parser,
        mock_tiktok_fetcher,
        mock_instagram_fetcher,
        mock_youtube_fetcher,
    ) -> SearchService:
        return SearchService(
            parser=mock_parser,
            tiktok_fetcher=mock_tiktok_fetcher,
            instagram_fetcher=mock_instagram_fetcher,
            youtube_fetcher=mock_youtube_fetcher,
            config=SearchConfig(),
        )

    async def test_search_parses_query(
        self, mock_search_service, mock_parser
    ) -> None:
        """Search calls parser with query."""
        await mock_search_service.search(query="fitness videos")
        mock_parser.parse.assert_called_once_with("fitness videos")

    async def test_search_uses_structured_query_bypass(
        self, mock_search_service, mock_parser
    ) -> None:
        """Search uses structured query when provided, skipping parser."""
        structured = ParsedSearchQuery(
            scope=SearchScope.VIDEOS,
            platforms=[Platform.TIKTOK],
            search_type=SearchType.KEYWORD,
            filters=SearchFilters(query="test"),
            confidence=1.0,
            confidence_level=ConfidenceLevel.HIGH,
        )
        await mock_search_service.search(query="ignored", structured_query=structured)
        mock_parser.parse.assert_not_called()

    async def test_search_returns_results(
        self, mock_search_service, mock_tiktok_fetcher
    ) -> None:
        """Search returns normalized results."""
        result = await mock_search_service.search(query="fitness videos")
        assert result["total"] >= 1
        assert len(result["results"]) >= 1
        assert result["platforms_searched"] == ["tiktok"]

    async def test_search_caches_results(
        self, mock_search_service, mock_tiktok_fetcher
    ) -> None:
        """Search caches results."""
        await mock_search_service.search(query="fitness videos")
        await mock_search_service.search(query="fitness videos")
        mock_tiktok_fetcher.search_keyword.assert_called_once()

    async def test_search_handles_platform_failure(
        self, mock_search_service, mock_tiktok_fetcher
    ) -> None:
        """Search handles platform failures gracefully."""
        mock_tiktok_fetcher.search_keyword = AsyncMock(side_effect=Exception("API Error"))

        result = await mock_search_service.search(query="fitness videos")
        assert "tiktok" in result["platforms_failed"]
        assert len(result["errors"]) > 0

    async def test_search_partial_provider_failure_still_returns_success(
        self,
        mock_search_service,
        mock_parser,
        mock_tiktok_fetcher,
        mock_instagram_fetcher,
        mock_youtube_fetcher,
    ) -> None:
        """One platform can fail while others still return aggregated results."""
        mock_parser.parse = AsyncMock(
            return_value=ParsedSearchQuery(
                scope=SearchScope.VIDEOS,
                platforms=[Platform.TIKTOK, Platform.INSTAGRAM, Platform.YOUTUBE],
                search_type=SearchType.KEYWORD,
                filters=SearchFilters(query="resilience check"),
                confidence=0.9,
                confidence_level=ConfidenceLevel.HIGH,
            )
        )
        # Instagram keyword search falls back to search_hashtag internally
        mock_instagram_fetcher.search_hashtag = AsyncMock(
            side_effect=Exception("429 Too Many Requests")
        )
        mock_youtube_fetcher.search = AsyncMock(
            return_value=[{"id": "yt1", "uploader_id": "channel1"}]
        )

        result = await mock_search_service.search(query="resilience check")
        assert result["total"] >= 2
        assert "instagram" in result["platforms_failed"]
        assert "tiktok" not in result["platforms_failed"]
        assert "youtube" not in result["platforms_failed"]

    async def test_search_timeout_isolated_to_single_platform(
        self,
        mock_search_service,
        mock_parser,
        mock_instagram_fetcher,
        mock_youtube_fetcher,
    ) -> None:
        """Provider timeout should not break successful providers."""
        mock_parser.parse = AsyncMock(
            return_value=ParsedSearchQuery(
                scope=SearchScope.VIDEOS,
                platforms=[Platform.TIKTOK, Platform.INSTAGRAM, Platform.YOUTUBE],
                search_type=SearchType.KEYWORD,
                filters=SearchFilters(query="timeout-check"),
                confidence=0.9,
                confidence_level=ConfidenceLevel.HIGH,
            )
        )
        # Instagram keyword search falls back to search_hashtag internally
        mock_instagram_fetcher.search_hashtag = AsyncMock(
            side_effect=TimeoutError("provider timed out")
        )
        mock_youtube_fetcher.search = AsyncMock(
            return_value=[{"id": "yt-timeout-ok", "uploader_id": "channel2"}]
        )

        result = await mock_search_service.search(query="timeout-check")
        assert "instagram" in result["platforms_failed"]
        assert result["total"] >= 1

    async def test_search_ignores_malformed_payload_entries(
        self,
        mock_search_service,
        mock_parser,
        mock_instagram_fetcher,
    ) -> None:
        """Malformed provider entries are skipped instead of failing the whole search."""
        mock_parser.parse = AsyncMock(
            return_value=ParsedSearchQuery(
                scope=SearchScope.VIDEOS,
                platforms=[Platform.INSTAGRAM],
                search_type=SearchType.KEYWORD,
                filters=SearchFilters(query="malformed-check"),
                confidence=0.9,
                confidence_level=ConfidenceLevel.HIGH,
            )
        )
        # Instagram keyword search falls back to search_hashtag internally
        mock_instagram_fetcher.search_hashtag = AsyncMock(
            return_value=[
                "bad-row",
                {"id": "ig-ok-1", "owner": {"username": "creator_a"}},
                None,
            ]
        )

        result = await mock_search_service.search(query="malformed-check")
        assert result["platforms_failed"] == []
        assert result["total"] == 1
        assert len(result["results"]) == 1


# === Normalization Tests ===


class TestSearchResultNormalization:
    """Tests for result normalization — pure logic."""

    @pytest.fixture
    def search_service(self) -> SearchService:
        return SearchService(
            parser=MagicMock(spec=GeminiQueryParser),
            tiktok_fetcher=MagicMock(),
            instagram_fetcher=MagicMock(),
            youtube_fetcher=MagicMock(),
            config=SearchConfig(),
        )

    def test_normalize_tiktok_result(self, search_service) -> None:
        """TikTok results are normalized correctly with all fields."""
        raw = {
            "aweme_id": "123",
            "desc": "Test video",
            "author": {"unique_id": "user123", "uid": "456", "follower_count": 50000, "nickname": "Test User"},
            "statistics": {"play_count": 1000, "digg_count": 100, "comment_count": 10, "share_count": 50, "collect_count": 200},
            "create_time_utc": "2026-01-15T12:00:00Z",
            "url": "https://www.tiktok.com/@user123/video/123",
            "video": {"cover": {"url_list": ["https://p16.tiktok.com/cover.jpg"]}},
            "music": {"title": "original sound - testuser"},
            "cha_list": [{"cha_name": "fitness"}, {"cha_name": "dance"}],
        }
        result = search_service._normalize_tiktok(raw)
        assert result.platform == Platform.TIKTOK
        assert result.video_id == "123"
        assert result.creator_handle == "user123"
        assert result.view_count == 1000
        assert result.description == "Test video"
        assert result.created_at == "2026-01-15T12:00:00Z"
        assert result.thumbnail_url == "https://p16.tiktok.com/cover.jpg"
        assert result.video_url == "https://www.tiktok.com/@user123/video/123"
        assert result.follower_count == 50000
        assert result.engagement_rate == 0.11  # (100 + 10) / 1000
        assert result.share_count == 50
        assert result.collect_count == 200
        assert result.creator_nickname == "Test User"
        assert result.hashtags == ["fitness", "dance"]
        assert result.music_title == "original sound - testuser"

    def test_normalize_instagram_result(self, search_service) -> None:
        """Instagram results are normalized correctly with all fields."""
        raw = {
            "id": "abc123",
            "caption": "Check this out! #fitness #cooking #healthy",
            "owner": {"username": "ig_user", "id": "789", "full_name": "Insta Creator"},
            "likesCount": 500,
            "timestamp": "2026-01-20T08:30:00Z",
            "displayUrl": "https://instagram.com/p/abc123/media",
            "videoDuration": 45000,  # 45 seconds in ms
        }
        result = search_service._normalize_instagram(raw)
        assert result.platform == Platform.INSTAGRAM
        assert result.video_id == "abc123"
        assert result.creator_handle == "ig_user"
        assert result.like_count == 500
        assert result.created_at == "2026-01-20T08:30:00Z"
        assert result.thumbnail_url == "https://instagram.com/p/abc123/media"
        assert result.creator_nickname == "Insta Creator"
        assert result.hashtags == ["fitness", "cooking", "healthy"]
        assert result.duration == 45

    def test_normalize_youtube_result(self, search_service) -> None:
        """YouTube results are normalized correctly with all fields."""
        raw = {
            "id": "yt123",
            "title": "YouTube Video",
            "uploader_id": "yt_user",
            "channel": "YouTube Creator",
            "view_count": 5000,
            "url": "https://www.youtube.com/watch?v=yt123",
            "thumbnails": [{"url": "https://i.ytimg.com/vi/yt123/hqdefault.jpg"}],
            "timestamp": 1737388800,  # 2025-01-20T16:00:00Z
            "tags": ["tutorial", "cooking"],
        }
        result = search_service._normalize_youtube(raw)
        assert result.platform == Platform.YOUTUBE
        assert result.video_id == "yt123"
        assert result.creator_handle == "yt_user"
        assert result.view_count == 5000
        assert result.thumbnail_url == "https://i.ytimg.com/vi/yt123/hqdefault.jpg"
        assert result.video_url == "https://www.youtube.com/watch?v=yt123"
        assert result.created_at is not None
        assert result.creator_nickname == "YouTube Creator"
        assert result.hashtags == ["tutorial", "cooking"]


# === Filter Tests ===


class TestSearchFilters:
    """Tests for search result filtering — pure logic."""

    @pytest.fixture
    def search_service(self) -> SearchService:
        return SearchService(
            parser=MagicMock(spec=GeminiQueryParser),
            tiktok_fetcher=MagicMock(),
            instagram_fetcher=MagicMock(),
            youtube_fetcher=MagicMock(),
            config=SearchConfig(),
        )

    def test_apply_filters_min_views(self, search_service) -> None:
        """Filter by minimum views works."""
        results = [
            SearchResult(platform=Platform.TIKTOK, creator_handle="a", view_count=100),
            SearchResult(platform=Platform.TIKTOK, creator_handle="b", view_count=500),
            SearchResult(platform=Platform.TIKTOK, creator_handle="c", view_count=1000),
        ]
        filters = SearchFilters(min_views=500)
        filtered = search_service._apply_filters(results, filters)
        assert len(filtered) == 2
        assert all(r.view_count >= 500 for r in filtered)

    def test_apply_filters_max_views(self, search_service) -> None:
        """Filter by maximum views works."""
        results = [
            SearchResult(platform=Platform.TIKTOK, creator_handle="a", view_count=100),
            SearchResult(platform=Platform.TIKTOK, creator_handle="b", view_count=500),
            SearchResult(platform=Platform.TIKTOK, creator_handle="c", view_count=1000),
        ]
        filters = SearchFilters(max_views=500)
        filtered = search_service._apply_filters(results, filters)
        assert len(filtered) == 2
        assert all(r.view_count <= 500 for r in filtered)

    def test_apply_filters_min_followers(self, search_service) -> None:
        """Filter by minimum followers works."""
        results = [
            SearchResult(platform=Platform.TIKTOK, creator_handle="a", follower_count=1000),
            SearchResult(platform=Platform.TIKTOK, creator_handle="b", follower_count=50000),
            SearchResult(platform=Platform.TIKTOK, creator_handle="c", follower_count=100000),
        ]
        filters = SearchFilters(min_followers=50000)
        filtered = search_service._apply_filters(results, filters)
        assert len(filtered) == 2


# === Exception Tests ===


class TestSearchExceptions:
    """Tests for search exceptions — pure logic."""

    def test_query_parse_error_stores_raw_query(self) -> None:
        """QueryParseError stores the raw query."""
        error = QueryParseError("Failed to parse", "bad query")
        assert error.raw_query == "bad query"
        assert str(error) == "Failed to parse"

    def test_search_error_is_base_exception(self) -> None:
        """SearchError is the base exception."""
        error = SearchError("Something went wrong")
        assert isinstance(error, Exception)
        assert str(error) == "Something went wrong"


# === Type Conversion Tests ===


class TestStructuredQueryConversion:
    """Tests for structured query type conversion — pure logic."""

    @pytest.fixture
    def search_service(self) -> SearchService:
        parser = MagicMock(spec=GeminiQueryParser)
        return SearchService(
            parser=parser,
            tiktok_fetcher=MagicMock(),
            instagram_fetcher=MagicMock(),
            youtube_fetcher=MagicMock(),
            config=SearchConfig(),
        )

    def test_convert_parsed_search_query_passthrough(self, search_service) -> None:
        """ParsedSearchQuery objects pass through unchanged."""
        original = ParsedSearchQuery(
            scope=SearchScope.VIDEOS,
            platforms=[Platform.TIKTOK],
            search_type=SearchType.KEYWORD,
            confidence_level=ConfidenceLevel.HIGH,
        )
        result = search_service._convert_structured_query(original)
        assert result is original

    def test_convert_dict_with_string_platforms(self, search_service) -> None:
        """Dict with string platforms converts correctly."""
        input_data = MagicMock()
        input_data.model_dump.return_value = {
            "scope": "videos",
            "platforms": ["tiktok", "instagram"],
            "search_type": "hashtag",
            "filters": {"query": "fitness"},
            "confidence_level": "high",
            "confidence": 0.95,
        }
        result = search_service._convert_structured_query(input_data)

        assert result.scope == SearchScope.VIDEOS
        assert result.platforms == [Platform.TIKTOK, Platform.INSTAGRAM]
        assert result.search_type == SearchType.HASHTAG
        assert result.confidence_level == ConfidenceLevel.HIGH
        assert result.filters.query == "fitness"

    def test_convert_filters_invalid_platforms_ignored(self, search_service) -> None:
        """Invalid platform strings are filtered out."""
        input_data = MagicMock()
        input_data.model_dump.return_value = {
            "scope": "videos",
            "platforms": ["tiktok", "invalid_platform", "youtube"],
            "search_type": "keyword",
            "filters": {},
            "confidence_level": "medium",
        }
        result = search_service._convert_structured_query(input_data)

        assert len(result.platforms) == 2
        assert Platform.TIKTOK in result.platforms
        assert Platform.YOUTUBE in result.platforms

    def test_convert_defaults_for_invalid_enums(self, search_service) -> None:
        """Invalid enum strings fall back to defaults."""
        input_data = MagicMock()
        input_data.model_dump.return_value = {
            "scope": "invalid_scope",
            "platforms": [],
            "search_type": "invalid_type",
            "filters": {},
            "confidence_level": "invalid_level",
        }
        result = search_service._convert_structured_query(input_data)

        assert result.scope == SearchScope.VIDEOS
        assert result.search_type == SearchType.KEYWORD
        assert result.confidence_level == ConfidenceLevel.MEDIUM
