"""Tests for LinkedIn carousel PDF generator."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from src.publishing.adapters._carousel import MAX_SLIDES, render_carousel_pdf
from src.publishing.exceptions import ContentValidationError
from src.publishing.models import CarouselSlide


def _fake_render_sync(slides, *, width_mm=210, height_mm=210, font_size=24, bg_color=(255, 255, 255)):
    """Return synthetic PDF bytes whose size scales with slide count."""
    header = b"%PDF-1.4 fake"
    body = b"x" * 200 * len(slides)
    return header + body


@pytest.mark.asyncio
@pytest.mark.mock_required
async def test_single_slide_pdf():
    """Render one slide, verify output starts with %PDF bytes and is non-empty."""
    slide = CarouselSlide(body="Hello World", title="Test Slide")
    with patch(
        "src.publishing.adapters._carousel._render_sync",
        side_effect=_fake_render_sync,
    ):
        pdf_bytes = await render_carousel_pdf([slide])
    assert pdf_bytes[:4] == b"%PDF"
    assert len(pdf_bytes) > 100


@pytest.mark.asyncio
@pytest.mark.mock_required
async def test_multi_slide_pdf():
    """Render 3 slides, verify output is larger than single slide."""
    single_slide = [CarouselSlide(body="Slide one")]
    multi_slides = [
        CarouselSlide(body="First slide", title="Intro"),
        CarouselSlide(body="Second slide with more content to ensure size difference"),
        CarouselSlide(body="Third slide wrapping up", title="Conclusion"),
    ]
    with patch(
        "src.publishing.adapters._carousel._render_sync",
        side_effect=_fake_render_sync,
    ):
        single_pdf = await render_carousel_pdf(single_slide)
        multi_pdf = await render_carousel_pdf(multi_slides)

    assert multi_pdf[:4] == b"%PDF"
    assert len(multi_pdf) > len(single_pdf)


@pytest.mark.asyncio
@pytest.mark.mock_required
async def test_max_slides_validation():
    """Verify ContentValidationError when slide count exceeds MAX_SLIDES (20)."""
    slides = [CarouselSlide(body=f"Slide {i}") for i in range(MAX_SLIDES + 1)]
    with pytest.raises(ContentValidationError, match="Maximum 20 slides allowed"):
        await render_carousel_pdf(slides)
