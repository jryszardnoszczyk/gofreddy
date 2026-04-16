"""LinkedIn PDF carousel generator — each slide becomes a PDF page.

LinkedIn has no native organic carousel API. Uploading a PDF document
where each page is a slide is the established workaround used by major
scheduling tools.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from ..exceptions import ContentValidationError

if TYPE_CHECKING:
    from ..models import CarouselSlide

logger = logging.getLogger(__name__)

MAX_SLIDES = 20


def _render_sync(
    slides: list[CarouselSlide],
    *,
    width_mm: float = 210,
    height_mm: float = 210,
    font_size: int = 24,
    bg_color: tuple[int, int, int] = (255, 255, 255),
) -> bytes:
    """Synchronous PDF rendering — called via asyncio.to_thread."""
    from fpdf import FPDF  # fpdf2 package

    pdf = FPDF(unit="mm", format=(width_mm, height_mm))
    pdf.set_auto_page_break(auto=False)

    for slide in slides:
        pdf.add_page()
        # Background
        r, g, b = bg_color
        if slide.bg_color:
            try:
                hex_color = slide.bg_color.lstrip("#")
                r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            except (ValueError, IndexError):
                pass
        pdf.set_fill_color(r, g, b)
        pdf.rect(0, 0, width_mm, height_mm, "F")

        margin = 15.0
        content_width = width_mm - 2 * margin
        y = margin

        # Title
        if slide.title:
            pdf.set_xy(margin, y)
            pdf.set_font("Helvetica", "B", font_size + 4)
            pdf.set_text_color(30, 30, 30)
            pdf.multi_cell(content_width, font_size * 0.5, slide.title, align="C")
            y = pdf.get_y() + 10

        # Body
        pdf.set_xy(margin, y)
        pdf.set_font("Helvetica", "", font_size)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(content_width, font_size * 0.45, slide.body, align="L")

    return bytes(pdf.output())


async def render_carousel_pdf(
    slides: list[CarouselSlide],
    *,
    width_mm: float = 210,
    height_mm: float = 210,
    font_size: int = 24,
    bg_color: tuple[int, int, int] = (255, 255, 255),
) -> bytes:
    """Render carousel slides as a PDF document for LinkedIn upload.

    Each CarouselSlide has: title (optional), body (required), image_url (optional).
    Returns PDF bytes ready for upload.

    fpdf2 is synchronous — wrapped in asyncio.to_thread.
    """
    if not slides:
        raise ContentValidationError(["At least one slide is required"])
    if len(slides) > MAX_SLIDES:
        raise ContentValidationError(
            [f"Maximum {MAX_SLIDES} slides allowed, got {len(slides)}"]
        )

    return await asyncio.to_thread(
        _render_sync,
        slides,
        width_mm=width_mm,
        height_mm=height_mm,
        font_size=font_size,
        bg_color=bg_color,
    )
