"""Tests for ContentExtractor service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.extraction.content_extractor import ContentExtractor, ExtractionResult, InputType
from src.extraction.config import ExtractionSettings
from src.extraction.exceptions import ExtractionError


@pytest.fixture
def settings():
    return ExtractionSettings()


@pytest.fixture
def extractor(settings):
    gemini = MagicMock()
    xpoz = MagicMock()
    http = AsyncMock()
    return ContentExtractor(
        gemini_client=gemini,
        xpoz_adapter=xpoz,
        http=http,
        settings=settings,
    )


class TestAutoDetection:
    def test_youtube_url(self, extractor):
        assert extractor._detect_type("https://youtube.com/watch?v=abc") == InputType.YOUTUBE
        assert extractor._detect_type("https://youtu.be/abc") == InputType.YOUTUBE
        assert extractor._detect_type("https://youtube.com/shorts/abc") == InputType.YOUTUBE

    def test_reddit_url(self, extractor):
        assert extractor._detect_type("https://reddit.com/r/python/comments/abc") == InputType.REDDIT

    def test_twitter_url(self, extractor):
        assert extractor._detect_type("https://x.com/user/status/123") == InputType.TWITTER
        assert extractor._detect_type("https://twitter.com/user/status/123") == InputType.TWITTER

    def test_rss_url(self, extractor):
        assert extractor._detect_type("https://example.com/feed") == InputType.RSS
        assert extractor._detect_type("https://example.com/rss") == InputType.RSS

    def test_pdf_url(self, extractor):
        assert extractor._detect_type("https://example.com/doc.pdf") == InputType.PDF

    def test_audio_url(self, extractor):
        assert extractor._detect_type("https://example.com/file.mp3") == InputType.AUDIO
        assert extractor._detect_type("https://example.com/file.wav") == InputType.AUDIO

    def test_image_url(self, extractor):
        assert extractor._detect_type("https://example.com/photo.jpg") == InputType.IMAGE
        assert extractor._detect_type("https://example.com/photo.png") == InputType.IMAGE

    def test_generic_url(self, extractor):
        assert extractor._detect_type("https://example.com/article") == InputType.URL

    def test_plain_text(self, extractor):
        assert extractor._detect_type("This is plain text content") == InputType.TEXT


class TestTextExtraction:
    @pytest.mark.asyncio
    @pytest.mark.mock_required
    async def test_passthrough(self, extractor):
        text = "A" * 150
        result = await extractor.extract(text, InputType.TEXT)
        assert isinstance(result, ExtractionResult)
        assert result.source_type == InputType.TEXT
        assert len(result.text) > 0

    @pytest.mark.asyncio
    @pytest.mark.mock_required
    async def test_min_100_chars(self, extractor):
        with pytest.raises(ExtractionError, match="min 100 chars"):
            await extractor.extract("short text", InputType.TEXT)

    @pytest.mark.asyncio
    @pytest.mark.mock_required
    async def test_empty_source_raises(self, extractor):
        with pytest.raises(ExtractionError, match="Empty source"):
            await extractor.extract("", InputType.TEXT)


class TestRedditExtraction:
    @pytest.mark.asyncio
    @pytest.mark.mock_required
    async def test_parses_json_response(self, extractor):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = [
            {"data": {"children": [{"data": {
                "title": "Test Post",
                "selftext": "Post content here",
                "score": 42,
                "num_comments": 5,
            }}]}},
            {"data": {"children": [
                {"kind": "t1", "data": {"body": "Great post!"}},
            ]}},
        ]

        extractor._http.get = AsyncMock(return_value=mock_resp)

        with patch("src.extraction.content_extractor.resolve_and_validate", new_callable=AsyncMock):
            result = await extractor._extract_reddit("https://reddit.com/r/python/comments/abc/test")

        assert "Test Post" in result.text
        assert result.source_type == InputType.REDDIT

    @pytest.mark.asyncio
    @pytest.mark.mock_required
    async def test_non_reddit_url_raises(self, extractor):
        with patch("src.extraction.content_extractor.resolve_and_validate", new_callable=AsyncMock):
            with pytest.raises(ExtractionError, match="Not a Reddit URL"):
                await extractor._extract_reddit("https://evil.com/r/python")


class TestTwitterExtraction:
    def test_tweet_id_parsing(self, extractor):
        from src.extraction.content_extractor import _TWEET_ID_RE
        match = _TWEET_ID_RE.search("https://x.com/user/status/123456789")
        assert match and match.group(1) == "123456789"

    @pytest.mark.asyncio
    @pytest.mark.mock_required
    async def test_no_xpoz_raises(self, settings):
        extractor = ContentExtractor(
            gemini_client=MagicMock(),
            xpoz_adapter=None,
            http=AsyncMock(),
            settings=settings,
        )
        with pytest.raises(ExtractionError, match="unavailable"):
            await extractor._extract_twitter("https://x.com/user/status/123")

    @pytest.mark.asyncio
    @pytest.mark.mock_required
    async def test_invalid_tweet_url_raises(self, extractor):
        with pytest.raises(ExtractionError, match="Cannot parse tweet ID"):
            await extractor._extract_twitter("https://x.com/user")


class TestPdfExtraction:
    @pytest.mark.asyncio
    @pytest.mark.mock_required
    async def test_rejects_local_path(self, extractor):
        with pytest.raises(ExtractionError, match="must be a URL"):
            await extractor._extract_pdf("/etc/passwd")
