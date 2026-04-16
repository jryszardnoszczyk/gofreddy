"""Tests for GEO content quality pattern detectors."""

import pytest
from bs4 import BeautifulSoup

from src.geo.patterns import (
    check_answer_first_intro,
    check_authoritative_citations,
    check_comparison_tables,
    check_eeat_signals,
    check_expert_quotes,
    check_faq_sections,
    check_heading_hierarchy,
    check_list_structures,
    check_paragraph_focus,
    check_statistics_presence,
    check_word_count,
    detect_content_quality,
)


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


class TestHeadingHierarchy:
    def test_proper_hierarchy(self):
        result = check_heading_hierarchy(_soup("<h1>Title</h1><h2>Sub</h2><h3>Detail</h3>"))
        assert result.detected is True

    def test_skipped_level(self):
        result = check_heading_hierarchy(_soup("<h1>Title</h1><h3>Skip</h3>"))
        assert result.detected is False
        assert result.count == 1

    def test_no_headings(self):
        result = check_heading_hierarchy(_soup("<p>text</p>"))
        assert result.detected is False


class TestStatisticsPresence:
    def test_with_stats(self):
        result = check_statistics_presence("Revenue grew 25% to $1,000 with 500 users")
        assert result.detected is True
        assert result.count >= 3

    def test_without_stats(self):
        result = check_statistics_presence("This is a simple paragraph with no numbers.")
        assert result.detected is False


class TestAuthoritativeCitations:
    def test_with_gov_link(self):
        result = check_authoritative_citations(_soup('<a href="https://www.fda.gov/report">FDA</a>'))
        assert result.detected is True

    def test_no_auth_links(self):
        result = check_authoritative_citations(_soup('<a href="https://example.com">link</a>'))
        assert result.detected is False


class TestExpertQuotes:
    def test_attributed_blockquote(self):
        result = check_expert_quotes(_soup('<blockquote>"Great product" — John Smith, CEO</blockquote>'))
        assert result.detected is True

    def test_no_quotes(self):
        result = check_expert_quotes(_soup("<p>Regular text</p>"))
        assert result.detected is False


class TestFaqSections:
    def test_faq_heading(self):
        result = check_faq_sections(_soup("<h2>Frequently Asked Questions</h2>"), [])
        assert result.detected is True

    def test_faq_schema(self):
        result = check_faq_sections(_soup("<p>text</p>"), ["FAQPage"])
        assert result.detected is True

    def test_no_faq(self):
        result = check_faq_sections(_soup("<p>text</p>"), [])
        assert result.detected is False


class TestAnswerFirstIntro:
    def test_good_intro(self):
        result = check_answer_first_intro(_soup("<p>Brand X is the leading analytics tool with 25M users worldwide, offering real-time data processing and visualization across more than 200 global markets today.</p>"))
        assert result.detected is True

    def test_filler_intro(self):
        result = check_answer_first_intro(_soup("<p>In this article, we will explore the many features of our product.</p>"))
        assert result.detected is False


class TestComparisonTables:
    def test_qualifying_table(self):
        html = "<table><tr><th>Feature</th><th>A</th><th>B</th></tr><tr><td>X</td><td>Y</td><td>Z</td></tr><tr><td>X2</td><td>Y2</td><td>Z2</td></tr></table>"
        result = check_comparison_tables(_soup(html))
        assert result.detected is True

    def test_small_table(self):
        html = "<table><tr><td>A</td><td>B</td></tr></table>"
        result = check_comparison_tables(_soup(html))
        assert result.detected is False


class TestListStructures:
    def test_with_lists(self):
        result = check_list_structures(_soup("<ul><li>A</li></ul><ol><li>B</li></ol>"))
        assert result.detected is True

    def test_no_lists(self):
        result = check_list_structures(_soup("<p>text</p>"))
        assert result.detected is False


class TestEeatSignals:
    def test_author_meta(self):
        result = check_eeat_signals(_soup('<meta name="author" content="Jane Doe">'))
        assert result.detected is True

    def test_no_signals(self):
        result = check_eeat_signals(_soup("<p>Anonymous content</p>"))
        assert result.detected is False


class TestParagraphFocus:
    def test_focused(self):
        result = check_paragraph_focus("Short paragraph here. Two sentences.\n\nAnother short one. Also two.")
        assert result.detected is True

    def test_too_long(self):
        text = "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five. Sentence six. Sentence seven."
        result = check_paragraph_focus(text)
        assert result.detected is False


class TestWordCount:
    def test_sufficient(self):
        result = check_word_count(" ".join(["word"] * 1500))
        assert result.detected is True

    def test_insufficient(self):
        result = check_word_count("Short page content")
        assert result.detected is False


class TestCollector:
    def test_returns_all_findings(self):
        html = "<html><body><h1>Title</h1><p>Content here</p></body></html>"
        findings = detect_content_quality(_soup(html), "Content here", [])
        assert len(findings) == 11
        assert all(f.factor_id for f in findings)
