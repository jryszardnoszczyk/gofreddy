"""PDF rendering for competitive briefs via WeasyPrint."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Semaphore to limit concurrent PDF renders (CPU-bound)
_render_semaphore = asyncio.Semaphore(2)

# Allowed HTML tags after sanitization
_ALLOWED_TAGS = {
    "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "br", "hr",
    "strong", "em", "b", "i", "u", "code", "pre",
    "ul", "ol", "li",
    "table", "thead", "tbody", "tr", "th", "td",
    "blockquote", "a", "img",
    "div", "span",
}

_ALLOWED_ATTRIBUTES: dict[str, set[str]] = {
    "a": {"href"},
    "img": {"src", "alt"},
    "td": {"colspan", "rowspan"},
    "th": {"colspan", "rowspan"},
}


def _safe_url_fetcher(url: str, timeout: int = 10) -> dict[str, Any]:
    """Block ALL external URLs except data: URIs. SSRF prevention."""
    if url.startswith("data:"):
        # Allow data: URIs for inline images/fonts
        from weasyprint import default_url_fetcher
        return default_url_fetcher(url, timeout=timeout)
    # Block everything else
    raise ValueError(f"External URL blocked: {url}")


def _get_template() -> Any:
    """Load Jinja2 template for PDF rendering."""
    from jinja2 import Environment, PackageLoader

    env = Environment(
        loader=PackageLoader("src.competitive", "templates"),
        autoescape=True,
    )
    return env.get_template("competitive_brief.html")


async def render_brief_pdf(brief_markdown: str, client_name: str) -> bytes:
    """Render a brief markdown string to PDF bytes.

    Security:
    - HTML sanitized via nh3 (strips scripts, event handlers)
    - base_url="about:blank" prevents CWD file resolution
    - url_fetcher blocks all external URLs except data: URIs
    """
    import markdown as md
    import nh3

    # Markdown -> HTML
    html_body = md.markdown(
        brief_markdown,
        extensions=["tables", "fenced_code", "toc"],
    )

    # Sanitize HTML (XSS prevention — monitoring data may contain scripts)
    sanitized_html = nh3.clean(
        html_body,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
    )

    # Render template
    template = _get_template()
    from datetime import datetime, timezone

    full_html = template.render(
        body=sanitized_html,
        client_name=client_name,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )

    # Render PDF (CPU-bound — run in thread with semaphore)
    async with _render_semaphore:
        pdf_bytes = await asyncio.to_thread(_render_pdf_sync, full_html)

    return pdf_bytes


def _render_pdf_sync(html_string: str) -> bytes:
    """Synchronous PDF rendering. Called via asyncio.to_thread()."""
    from weasyprint import HTML
    from weasyprint.text.fonts import FontConfiguration

    font_config = FontConfiguration()
    result = HTML(
        string=html_string,
        base_url="about:blank",
        url_fetcher=_safe_url_fetcher,
    ).write_pdf(
        font_config=font_config,
        presentational_hints=True,
    )
    return result or b""
