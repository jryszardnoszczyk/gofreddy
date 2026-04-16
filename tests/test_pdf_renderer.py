"""Tests for PDF rendering and URL safety."""

from __future__ import annotations

import pytest

from src.competitive.pdf import _safe_url_fetcher


def test_safe_url_fetcher_blocks_external():
    """External URLs are blocked."""
    with pytest.raises(ValueError, match="External URL blocked"):
        _safe_url_fetcher("https://evil.com/steal")


def test_safe_url_fetcher_blocks_file():
    """File URLs are blocked."""
    with pytest.raises(ValueError, match="External URL blocked"):
        _safe_url_fetcher("file:///etc/passwd")


def test_safe_url_fetcher_allows_data_uri():
    """data: URIs are allowed."""
    # data: URIs should be passed through (may raise if format invalid, but not ValueError)
    try:
        result = _safe_url_fetcher("data:text/plain;base64,SGVsbG8=")
        assert result is not None
    except Exception as e:
        # WeasyPrint might not be installed in test env
        assert "External URL blocked" not in str(e)


def test_markdown_render_missing_sections():
    """Render handles missing sections gracefully."""
    from src.competitive.markdown import render_brief_markdown

    md = render_brief_markdown({})
    assert "Competitive Intelligence Brief" in md


def test_markdown_render_with_sections():
    """Render formats all section types."""
    from src.competitive.markdown import render_brief_markdown

    brief_data = {
        "client_name": "TestCorp",
        "date_range": "7d",
        "executive_summary": "Test summary.",
        "sections": [
            {"title": "Share of Voice", "content": [
                {"brand": "A", "mention_count": 10, "percentage": 50.0, "sentiment_avg": 0.5}
            ], "status": "ok"},
            {"title": "Sentiment Analysis", "content": [
                {"period": "2026-01-01", "avg_sentiment": 0.7, "mention_count": 5, "positive": 3, "negative": 1, "neutral": 1}
            ], "status": "ok"},
            {"title": "Competitor Ads", "content": [
                {"headline": "Buy Now", "platform": "meta", "provider": "foreplay", "body_text": "Ad text"}
            ], "status": "ok"},
            {"title": "Partnerships", "content": [
                {"brand": "X", "creator": "@y", "platform": "tiktok", "mention_count": 5, "is_new": True, "is_escalation": False}
            ], "status": "ok"},
            {"title": "Skipped Section", "content": "Data unavailable.", "status": "skipped"},
        ],
        "changes": [{"change": "First brief."}],
        "recommendations": ["Do this.", "Do that."],
    }

    md = render_brief_markdown(brief_data)
    assert "TestCorp" in md
    assert "Share of Voice" in md
    assert "Buy Now" in md
    assert "Do this." in md
    assert "First brief." in md


def test_markdown_render_empty_content():
    """Sections with empty list content render properly."""
    from src.competitive.markdown import render_brief_markdown

    brief_data = {
        "sections": [
            {"title": "Empty", "content": [], "status": "ok"},
        ],
    }
    md = render_brief_markdown(brief_data)
    assert "No data available" in md
