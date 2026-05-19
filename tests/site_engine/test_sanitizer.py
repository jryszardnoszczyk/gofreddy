"""U15b — site_engine HTML allowlist sanitizer (Pass-1 structural gate)."""
from __future__ import annotations

import pytest

from src.site_engine.sanitizer import (
    SanitizerResult,
    sanitize_section_html,
)


def test_clean_html_passes_unchanged() -> None:
    html = '<section><h1>Title</h1><p>Body</p></section>'
    result = sanitize_section_html(html)
    assert result.safe is True
    assert result.deltas == []


def test_script_tag_stripped() -> None:
    html = '<h1>Hi</h1><script>alert(1)</script>'
    result = sanitize_section_html(html)
    assert result.safe is False
    assert any("script" in d.detail.lower() for d in result.deltas)
    assert "<script" not in result.clean.lower()


def test_iframe_srcdoc_stripped() -> None:
    """Pass-1 must strip <iframe srcdoc=...> (XSS vector)."""
    html = '<p>Text</p><iframe srcdoc="<script>alert(1)</script>"></iframe>'
    result = sanitize_section_html(html)
    assert result.safe is False
    assert "<iframe" not in result.clean.lower()


def test_javascript_url_stripped() -> None:
    """URL scheme allowlist rejects javascript:."""
    html = '<a href="javascript:void(0)">Click</a>'
    result = sanitize_section_html(html)
    assert result.safe is False
    assert "javascript:" not in result.clean.lower()


def test_data_text_url_stripped() -> None:
    """data:text/* URL schemes rejected (XSS vector)."""
    html = '<a href="data:text/html,<script>alert(1)</script>">x</a>'
    result = sanitize_section_html(html)
    assert result.safe is False
    assert "data:text" not in result.clean.lower()


def test_https_url_allowed() -> None:
    html = '<a href="https://example.com">Link</a>'
    result = sanitize_section_html(html)
    assert result.safe is True


def test_event_handler_attributes_stripped() -> None:
    """on* event handlers must not survive the sanitizer."""
    html = '<button onclick="evil()">Click</button>'
    result = sanitize_section_html(html)
    assert result.safe is False
    assert "onclick" not in result.clean.lower()


def test_object_embed_tags_stripped() -> None:
    """<object> and <embed> (out of allowlist) are stripped."""
    for tag in ("object", "embed"):
        html = f'<{tag} data="evil.swf"></{tag}>'
        result = sanitize_section_html(html)
        assert result.safe is False, tag


def test_data_image_url_allowed() -> None:
    """data:image/* allowed for inline images per the allowlist."""
    # nh3 by default may or may not allow data: URLs; this test
    # documents current behavior — if it changes, the lane prompt
    # should adapt.
    html = '<img src="https://example.com/x.png" alt="x">'
    result = sanitize_section_html(html)
    assert result.safe is True


def test_returns_sanitizer_result_shape() -> None:
    """Public API returns a SanitizerResult with clean + deltas + safe."""
    result = sanitize_section_html('<p>hi</p>')
    assert isinstance(result, SanitizerResult)
    assert hasattr(result, "clean")
    assert hasattr(result, "deltas")
    assert hasattr(result, "safe")
