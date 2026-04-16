"""Tests for GEO detector — pure logic tests (no DB, no external deps).

After refactoring: tests GEO infrastructure checks + SEO technical checks.
Content quality detectors (citations, statistics, etc.) were moved to agent-side evaluation.
"""

import pytest
from bs4 import BeautifulSoup

from src.geo.detector import (
    _detect_canonical_url,
    _detect_https,
    _detect_image_alt_ratio,
    _detect_internal_links,
    _detect_meta_description,
    _detect_mobile_viewport,
    _detect_schema_markup,
    _detect_single_h1,
    _detect_ssr_issues,
    _detect_title_tag,
    detect_factors,
)
from src.geo.models import PageContent, Severity


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def rich_page_content() -> PageContent:
    """PageContent with many factors present."""
    return PageContent(
        url="https://example.com/test",
        final_url="https://example.com/test",
        text="Cloud computing is a technology that delivers computing services.",
        raw_html=(
            "<html><head>"
            "<title>Cloud Computing Guide</title>"
            '<meta name="description" content="Complete guide to cloud computing for enterprises.">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<link rel="canonical" href="https://example.com/test">'
            "</head><body>"
            "<h1>Cloud Computing Guide</h1>"
            "<h2>What is Cloud Computing?</h2>"
            "<p>Cloud computing delivers services over the internet.</p>"
            '<a href="/pricing">Pricing</a>'
            '<a href="/about">About</a>'
            '<a href="/features">Features</a>'
            '<img src="img1.jpg" alt="Cloud diagram">'
            '<img src="img2.jpg" alt="Architecture">'
            '<script type="application/ld+json">{"@type": "FAQPage"}</script>'
            "</body></html>"
        ),
        word_count=1200,
        h1="Cloud Computing Guide",
        h2s=["What is Cloud Computing?"],
        h3s=[],
        title="Cloud Computing Guide",
        meta_description="Complete guide to cloud computing for enterprises.",
        schema_types=["FAQPage"],
        js_rendered=False,
        status_code=200,
        fetch_duration_ms=500,
    )


@pytest.fixture
def minimal_page_content() -> PageContent:
    """PageContent with almost nothing."""
    return PageContent(
        url="http://example.com/thin",
        final_url="http://example.com/thin",
        text="Welcome to our site.",
        raw_html="<html><body><p>Welcome to our site.</p></body></html>",
        word_count=4,
        h1=None,
        h2s=[],
        h3s=[],
        title=None,
        schema_types=[],
        js_rendered=False,
        status_code=200,
        fetch_duration_ms=100,
    )


# =============================================================================
# GEO Infrastructure Tests
# =============================================================================


class TestSchemaMarkup:
    def test_detects_schema(self):
        result = _detect_schema_markup(["Article", "FAQPage"])
        assert result.detected is True
        assert result.count == 2

    def test_no_schema(self):
        result = _detect_schema_markup([])
        assert result.detected is False


class TestSSRIssues:
    def test_ssr_ok(self):
        result = _detect_ssr_issues(js_rendered=False)
        assert result.detected is True

    def test_js_rendered(self):
        result = _detect_ssr_issues(js_rendered=True)
        assert result.detected is False


# =============================================================================
# SEO Technical Check Tests
# =============================================================================


class TestTitleTag:
    def test_optimal_length(self):
        result = _detect_title_tag("Cloud Computing Guide for Enterprises")
        assert result.detected is True
        assert "optimal" in result.details

    def test_too_short(self):
        result = _detect_title_tag("Cloud")
        assert result.detected is True
        assert "too short" in result.details

    def test_too_long(self):
        result = _detect_title_tag("A" * 70)
        assert result.detected is True
        assert "too long" in result.details

    def test_missing(self):
        result = _detect_title_tag(None)
        assert result.detected is False
        assert result.severity == Severity.CRITICAL


class TestMetaDescription:
    def test_optimal(self):
        result = _detect_meta_description("A" * 140)
        assert result.detected is True
        assert "optimal" in result.details

    def test_too_short(self):
        result = _detect_meta_description("Short desc")
        assert result.detected is True
        assert "too short" in result.details

    def test_missing(self):
        result = _detect_meta_description(None)
        assert result.detected is False


class TestCanonicalUrl:
    def test_self_referencing(self):
        html = '<html><head><link rel="canonical" href="https://example.com/page"></head></html>'
        soup = BeautifulSoup(html, "lxml")
        result = _detect_canonical_url(soup, "https://example.com/page")
        assert result.detected is True
        assert "Self-referencing" in result.details

    def test_different_url(self):
        html = '<html><head><link rel="canonical" href="https://example.com/other"></head></html>'
        soup = BeautifulSoup(html, "lxml")
        result = _detect_canonical_url(soup, "https://example.com/page")
        assert result.detected is True
        assert "Points to" in result.details

    def test_missing(self):
        html = "<html><head></head></html>"
        soup = BeautifulSoup(html, "lxml")
        result = _detect_canonical_url(soup, "https://example.com/page")
        assert result.detected is False

    def test_no_soup(self):
        result = _detect_canonical_url(None, "https://example.com")
        assert result.detected is None


class TestSingleH1:
    def test_exactly_one(self):
        html = "<html><body><h1>Title</h1></body></html>"
        soup = BeautifulSoup(html, "lxml")
        result = _detect_single_h1(soup)
        assert result.detected is True
        assert result.count == 1

    def test_no_h1(self):
        html = "<html><body><h2>Subtitle</h2></body></html>"
        soup = BeautifulSoup(html, "lxml")
        result = _detect_single_h1(soup)
        assert result.detected is False
        assert result.count == 0

    def test_multiple_h1s(self):
        html = "<html><body><h1>First</h1><h1>Second</h1></body></html>"
        soup = BeautifulSoup(html, "lxml")
        result = _detect_single_h1(soup)
        assert result.detected is False
        assert result.count == 2


class TestInternalLinks:
    def test_has_internal_links(self):
        html = '<html><body><a href="/page1">1</a><a href="/page2">2</a><a href="/page3">3</a></body></html>'
        soup = BeautifulSoup(html, "lxml")
        result = _detect_internal_links(soup, "https://example.com")
        assert result.detected is True
        assert result.count == 3

    def test_too_few(self):
        html = '<html><body><a href="/page1">1</a></body></html>'
        soup = BeautifulSoup(html, "lxml")
        result = _detect_internal_links(soup, "https://example.com")
        assert result.detected is False
        assert "recommend 3+" in result.details

    def test_absolute_same_domain(self):
        html = '<html><body><a href="https://example.com/a">1</a><a href="https://example.com/b">2</a><a href="https://example.com/c">3</a></body></html>'
        soup = BeautifulSoup(html, "lxml")
        result = _detect_internal_links(soup, "https://example.com/page")
        assert result.detected is True
        assert result.count == 3


class TestImageAltRatio:
    def test_all_have_alt(self):
        html = '<html><body><img src="a.jpg" alt="A"><img src="b.jpg" alt="B"></body></html>'
        soup = BeautifulSoup(html, "lxml")
        result = _detect_image_alt_ratio(soup)
        assert result.detected is True

    def test_none_have_alt(self):
        html = '<html><body><img src="a.jpg"><img src="b.jpg"></body></html>'
        soup = BeautifulSoup(html, "lxml")
        result = _detect_image_alt_ratio(soup)
        assert result.detected is False

    def test_no_images(self):
        html = "<html><body><p>No images</p></body></html>"
        soup = BeautifulSoup(html, "lxml")
        result = _detect_image_alt_ratio(soup)
        assert result.detected is True  # No images = OK


class TestHttps:
    def test_https(self):
        result = _detect_https("https://example.com")
        assert result.detected is True

    def test_http(self):
        result = _detect_https("http://example.com")
        assert result.detected is False
        assert result.severity == Severity.CRITICAL


class TestMobileViewport:
    def test_has_viewport(self):
        html = '<html><head><meta name="viewport" content="width=device-width"></head></html>'
        soup = BeautifulSoup(html, "lxml")
        result = _detect_mobile_viewport(soup)
        assert result.detected is True

    def test_missing(self):
        html = "<html><head></head></html>"
        soup = BeautifulSoup(html, "lxml")
        result = _detect_mobile_viewport(soup)
        assert result.detected is False


# =============================================================================
# Integration: detect_factors
# =============================================================================


class TestDetectFactors:
    @pytest.mark.asyncio
    async def test_rich_page(self, rich_page_content):
        """A well-built page should detect infrastructure + SEO + content quality factors."""
        findings = await detect_factors(rich_page_content)

        # 10 infra/SEO + 2 HTTP + 12 content quality = 24
        assert findings.factors_checked == 24
        assert findings.detection_time_ms >= 0

    @pytest.mark.asyncio
    async def test_minimal_page(self, minimal_page_content):
        """A thin page should miss most factors."""
        findings = await detect_factors(minimal_page_content)

        assert findings.factors_checked == 24
        assert findings.factors_missing >= 3  # missing title, h1, https, etc.

    @pytest.mark.asyncio
    async def test_factor_ids(self, rich_page_content):
        """Verify all expected factor IDs are present."""
        findings = await detect_factors(rich_page_content)

        factor_ids = {f.factor_id for f in findings.findings}
        expected_ids = {
            # GEO infrastructure
            "schema_markup", "ssr_issues",
            # SEO technical
            "title_tag", "meta_description", "canonical_url", "single_h1",
            "internal_links", "image_alt_ratio", "https", "mobile_viewport",
            # HTTP checks
            "ai_bot_access", "llms_txt",
            # Content quality (from patterns.py)
            "heading_hierarchy", "statistics_presence", "authoritative_citations",
            "expert_quotes", "faq_sections", "answer_first_intro",
            "comparison_tables", "list_structures", "eeat_signals",
            "paragraph_focus", "word_count", "content_freshness",
        }
        assert factor_ids == expected_ids

    @pytest.mark.asyncio
    async def test_severity_counts_consistent(self, rich_page_content):
        """Severity counts should match individual finding counts."""
        findings = await detect_factors(rich_page_content)

        actual_critical = sum(
            1 for f in findings.findings
            if f.detected is False and f.severity == Severity.CRITICAL
        )
        assert findings.critical_missing == actual_critical
