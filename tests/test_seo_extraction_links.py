"""Unit tests for extract_internal_links()."""

import pytest
from bs4 import BeautifulSoup

from src.geo.extraction import extract_internal_links


def _make_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


class TestExtractInternalLinks:
    """Tests for internal link extraction."""

    def test_extracts_relative_links(self):
        html = '<html><body><a href="/about">About Us</a><a href="/contact">Contact</a></body></html>'
        result = extract_internal_links(_make_soup(html), "https://example.com/page")
        assert len(result) == 2
        assert result[0]["href"] == "/about"
        assert result[0]["anchor_text"] == "About Us"

    def test_extracts_same_domain_absolute_links(self):
        html = '<html><body><a href="https://example.com/about">About</a></body></html>'
        result = extract_internal_links(_make_soup(html), "https://example.com/page")
        assert len(result) == 1
        assert result[0]["href"] == "https://example.com/about"

    def test_excludes_external_links(self):
        html = '<html><body><a href="https://other.com/page">External</a><a href="/internal">Internal</a></body></html>'
        result = extract_internal_links(_make_soup(html), "https://example.com/page")
        assert len(result) == 1
        assert result[0]["href"] == "/internal"

    def test_excludes_anchors_and_special_protocols(self):
        html = """<html><body>
            <a href="#section">Anchor</a>
            <a href="javascript:void(0)">JS</a>
            <a href="mailto:test@test.com">Email</a>
            <a href="tel:+1234567890">Phone</a>
            <a href="/real">Real</a>
        </body></html>"""
        result = extract_internal_links(_make_soup(html), "https://example.com")
        assert len(result) == 1
        assert result[0]["href"] == "/real"

    def test_content_area_detection(self):
        html = """<html><body>
            <nav><a href="/nav-link">Nav</a></nav>
            <header><a href="/header-link">Header</a></header>
            <main><a href="/content-link">Content</a></main>
            <footer><a href="/footer-link">Footer</a></footer>
        </body></html>"""
        result = extract_internal_links(_make_soup(html), "https://example.com")
        nav_link = next(r for r in result if r["href"] == "/nav-link")
        content_link = next(r for r in result if r["href"] == "/content-link")
        footer_link = next(r for r in result if r["href"] == "/footer-link")
        assert nav_link["in_content_area"] is False
        assert content_link["in_content_area"] is True
        assert footer_link["in_content_area"] is False

    def test_truncates_long_anchor_text(self):
        long_text = "A" * 300
        html = f'<html><body><a href="/page">{long_text}</a></body></html>'
        result = extract_internal_links(_make_soup(html), "https://example.com")
        assert len(result[0]["anchor_text"]) <= 200

    def test_caps_at_500_links(self):
        links = "".join(f'<a href="/page-{i}">Link {i}</a>' for i in range(600))
        html = f"<html><body>{links}</body></html>"
        result = extract_internal_links(_make_soup(html), "https://example.com")
        assert len(result) <= 500

    def test_empty_page_returns_empty(self):
        html = "<html><body><p>No links here</p></body></html>"
        result = extract_internal_links(_make_soup(html), "https://example.com")
        assert result == []
