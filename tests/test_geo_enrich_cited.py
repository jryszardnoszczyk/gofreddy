"""Tests for _enrich_cited_pages — cited page scraping and enrichment."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.geo.analyzer import calculate_pattern_gaps
from src.geo.models import CitedPageData, PageContent, ScrapeResult
from src.geo.orchestrator import _enrich_cited_pages


# =============================================================================
# Fixtures
# =============================================================================


def _make_stub(url: str = "https://example.com/page", domain: str = "example.com") -> CitedPageData:
    return CitedPageData(
        url_normalized=url,
        domain=domain,
        h2_texts=(),
        schema_types=(),
        has_comparison_table=False,
        publish_date=None,
        last_modified=None,
        scraped_at=datetime.now(timezone.utc),
        query_topic="test query",
    )


def _make_page_content(
    h2s: list[str] | None = None,
    schema_types: list[str] | None = None,
) -> PageContent:
    return PageContent(
        url="https://example.com/page",
        final_url="https://example.com/page",
        text="Some content here.",
        raw_html="<html><body><p>content</p></body></html>",
        word_count=100,
        h2s=h2s or [],
        schema_types=schema_types or [],
    )


def _make_scrape_result(
    success: bool = True,
    h2s: list[str] | None = None,
    schema_types: list[str] | None = None,
    error_code: str | None = None,
) -> ScrapeResult:
    if success:
        return ScrapeResult(
            success=True,
            page_content=_make_page_content(h2s=h2s, schema_types=schema_types),
        )
    return ScrapeResult(success=False, error_code=error_code or "FETCH_FAILED")


# =============================================================================
# Unit tests: field mapping
# =============================================================================


@pytest.mark.asyncio
@patch("src.geo.orchestrator.scrape_page")
async def test_page_content_to_cited_page_data_mapping(mock_scrape: AsyncMock) -> None:
    """PageContent h2s (list) → CitedPageData h2_texts (tuple), schema_types likewise."""
    mock_scrape.return_value = _make_scrape_result(
        h2s=["What is SEO?", "FAQ Section"],
        schema_types=["FAQPage", "Article"],
    )
    stub = _make_stub()
    result = await _enrich_cited_pages([stub], page_url="https://other.com")
    assert len(result) == 1
    page = result[0]
    assert page.h2_texts == ("What is SEO?", "FAQ Section")
    assert page.schema_types == ("FAQPage", "Article")
    assert page.url_normalized == stub.url_normalized
    assert page.domain == stub.domain
    assert page.query_topic == stub.query_topic


@pytest.mark.asyncio
@patch("src.geo.orchestrator.scrape_page")
async def test_none_guard_on_extracted_fields(mock_scrape: AsyncMock) -> None:
    """None values in h2s/schema_types are converted to empty strings.

    Uses MagicMock for page_content since Pydantic validates list[str] —
    but extraction bugs could bypass Pydantic and produce None elements.
    """
    pc = MagicMock()
    pc.h2s = ["Good heading", None]
    pc.schema_types = [None, "Article"]
    mock_scrape.return_value = ScrapeResult.model_construct(success=True, page_content=pc)
    stub = _make_stub()
    result = await _enrich_cited_pages([stub], page_url="https://other.com")
    assert result[0].h2_texts == ("Good heading", "")
    assert result[0].schema_types == ("", "Article")


# =============================================================================
# Unit tests: URL pre-filtering
# =============================================================================


@pytest.mark.asyncio
@patch("src.geo.orchestrator.scrape_page")
async def test_non_https_urls_filtered(mock_scrape: AsyncMock) -> None:
    """HTTP URLs are excluded from scraping."""
    stubs = [_make_stub(url="http://insecure.com/page")]
    result = await _enrich_cited_pages(stubs, page_url="https://other.com")
    assert result == []
    mock_scrape.assert_not_called()


@pytest.mark.asyncio
@patch("src.geo.orchestrator.scrape_page")
async def test_long_urls_filtered(mock_scrape: AsyncMock) -> None:
    """URLs exceeding 2048 chars are excluded."""
    long_url = "https://example.com/" + "a" * 2040
    stubs = [_make_stub(url=long_url)]
    result = await _enrich_cited_pages(stubs, page_url="https://other.com")
    assert result == []
    mock_scrape.assert_not_called()


@pytest.mark.asyncio
@patch("src.geo.orchestrator.scrape_page")
async def test_own_page_url_excluded(mock_scrape: AsyncMock) -> None:
    """User's own page URL is excluded from scraping."""
    own_url = "https://mysite.com/my-page"
    stubs = [_make_stub(url=own_url)]
    result = await _enrich_cited_pages(stubs, page_url=own_url)
    assert result == []
    mock_scrape.assert_not_called()


@pytest.mark.asyncio
@patch("src.geo.orchestrator.scrape_page")
async def test_max_pages_cap(mock_scrape: AsyncMock) -> None:
    """Only first max_pages stubs are processed."""
    mock_scrape.return_value = _make_scrape_result(h2s=["Heading"])
    stubs = [_make_stub(url=f"https://example.com/{i}") for i in range(10)]
    result = await _enrich_cited_pages(stubs, page_url="https://other.com", max_pages=3)
    assert mock_scrape.call_count == 3
    assert len(result) == 3


# =============================================================================
# Unit tests: failure handling
# =============================================================================


@pytest.mark.asyncio
@patch("src.geo.orchestrator.scrape_page")
async def test_failed_scrape_excluded(mock_scrape: AsyncMock) -> None:
    """Pages that fail to scrape are not included in results."""
    mock_scrape.return_value = _make_scrape_result(success=False)
    stubs = [_make_stub()]
    result = await _enrich_cited_pages(stubs, page_url="https://other.com")
    assert result == []


@pytest.mark.asyncio
@patch("src.geo.orchestrator.scrape_page")
async def test_exception_during_scrape_excluded(mock_scrape: AsyncMock) -> None:
    """Exceptions during scraping are caught and the page is excluded."""
    mock_scrape.side_effect = RuntimeError("network down")
    stubs = [_make_stub()]
    result = await _enrich_cited_pages(stubs, page_url="https://other.com")
    assert result == []


@pytest.mark.asyncio
@patch("src.geo.orchestrator.scrape_page")
async def test_partial_success(mock_scrape: AsyncMock) -> None:
    """Mix of success and failure — only successful scrapes returned."""
    mock_scrape.side_effect = [
        _make_scrape_result(h2s=["Good Page"]),
        _make_scrape_result(success=False),
        _make_scrape_result(h2s=["Another Good"]),
    ]
    stubs = [
        _make_stub(url="https://a.com/1"),
        _make_stub(url="https://b.com/2"),
        _make_stub(url="https://c.com/3"),
    ]
    result = await _enrich_cited_pages(stubs, page_url="https://other.com")
    assert len(result) == 2
    urls = {p.url_normalized for p in result}
    assert urls == {"https://a.com/1", "https://c.com/3"}


@pytest.mark.asyncio
@patch("src.geo.orchestrator.scrape_page")
async def test_empty_stubs_returns_empty(mock_scrape: AsyncMock) -> None:
    """Empty input returns empty output without scraping."""
    result = await _enrich_cited_pages([], page_url="https://other.com")
    assert result == []
    mock_scrape.assert_not_called()


@pytest.mark.asyncio
@patch("src.geo.orchestrator.scrape_page")
async def test_timeout_returns_partial_results(mock_scrape: AsyncMock) -> None:
    """When timeout fires, already-completed scrapes are kept."""
    async def _slow_scrape(url: str) -> ScrapeResult:
        if "slow" in url:
            await asyncio.sleep(10)  # will be cancelled by timeout
        return _make_scrape_result(h2s=["Fast Result"])

    mock_scrape.side_effect = _slow_scrape
    stubs = [
        _make_stub(url="https://fast.com/1"),
        _make_stub(url="https://slow.com/2"),
    ]
    result = await _enrich_cited_pages(stubs, page_url="https://other.com", timeout=0.5)
    # At least the fast one should complete
    assert len(result) >= 1
    assert any(p.url_normalized == "https://fast.com/1" for p in result)


# =============================================================================
# Integration test: enriched pages → non-zero pattern gaps
# =============================================================================


@pytest.mark.asyncio
@patch("src.geo.orchestrator.scrape_page")
async def test_enriched_pages_produce_nonzero_pattern_gaps(mock_scrape: AsyncMock) -> None:
    """Enriched cited pages with real content produce non-zero gap percentages."""
    # 5 cited pages with schema and FAQ headings
    mock_scrape.return_value = _make_scrape_result(
        h2s=["FAQ", "Pricing", "How it Works"],
        schema_types=["FAQPage", "Article"],
    )
    stubs = [_make_stub(url=f"https://cited{i}.com/page") for i in range(5)]
    enriched = await _enrich_cited_pages(stubs, page_url="https://mysite.com")
    assert len(enriched) == 5

    # User page has no schema or FAQ
    user_page = _make_page_content(h2s=["About Us"], schema_types=[])

    gaps = calculate_pattern_gaps(enriched, user_page)
    assert gaps.schema_pct > 0, "schema_pct should be non-zero with enriched pages"
    assert gaps.faq_section_pct > 0, "faq_section_pct should be non-zero with enriched pages"
    assert gaps.faqpage_schema_pct > 0, "faqpage_schema_pct should be non-zero with enriched pages"
