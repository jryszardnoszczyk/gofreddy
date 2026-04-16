"""Content extraction from HTML pages."""

import json
import logging
from datetime import date
from typing import Any

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Content size limits
MAX_TEXT_LENGTH = 100_000  # 100K chars
MAX_HTML_SIZE = 5_000_000  # 5MB
MAX_JSON_LD_SIZE = 100_000  # 100KB limit per script (security)


def extract_page_content(
    html: str,
    url: str,
    final_url: str,
    js_rendered: bool,
    status_code: int,
    fetch_duration_ms: int,
) -> "PageContent":
    """Extract structured content from HTML for the DETECT step."""
    from .models import PageContent

    # Size check
    if len(html) > MAX_HTML_SIZE:
        logger.warning(
            "html_size_exceeded",
            extra={"url": url, "size": len(html), "limit": MAX_HTML_SIZE},
        )
        html = html[:MAX_HTML_SIZE]

    soup = BeautifulSoup(html, "lxml")

    headings = extract_headings(soup)
    meta = extract_metadata(soup)
    json_ld_objects = extract_json_ld(soup)
    json_ld_types = list({
        t for obj in json_ld_objects
        for t in (obj["@type"] if isinstance(obj.get("@type"), list) else [obj.get("@type", "")])
        if t
    })
    text = extract_main_text(soup)

    truncated_text = text[:MAX_TEXT_LENGTH]
    word_count = len(truncated_text.split())

    body_html = _extract_body_html(soup, html)
    truncated_html = body_html[:500_000]

    return PageContent(
        url=url,
        final_url=final_url,
        text=truncated_text,
        raw_html=truncated_html,
        word_count=word_count,
        h1=headings["h1"],
        h2s=headings["h2s"],
        h3s=headings["h3s"],
        title=meta["title"],
        meta_description=meta["description"],
        schema_types=json_ld_types,
        json_ld_objects=json_ld_objects,
        js_rendered=js_rendered,
        status_code=status_code,
        fetch_duration_ms=fetch_duration_ms,
        internal_links=extract_internal_links(soup, url),
    )


def extract_headings(soup: BeautifulSoup) -> dict[str, Any]:
    """Extract heading structure from page."""
    h1_tag = soup.find("h1")
    h1 = h1_tag.get_text(strip=True)[:500] if h1_tag else None

    h2s = [h.get_text(strip=True)[:100] for h in soup.find_all("h2")][:20]
    h3s = [h.get_text(strip=True)[:100] for h in soup.find_all("h3")][:50]

    return {"h1": h1, "h2s": h2s, "h3s": h3s}


def extract_metadata(soup: BeautifulSoup) -> dict[str, str | None]:
    """Extract meta tags and title."""
    title: str | None = None
    if soup.title:
        title = soup.title.string
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        title = title or og_title["content"]
    if title:
        title = title[:200]

    description: str | None = None
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc:
        description = meta_desc.get("content", "")[:500]
    og_desc = soup.find("meta", property="og:description")
    if og_desc and og_desc.get("content"):
        description = description or og_desc["content"][:500]

    return {"title": title, "description": description}


def extract_json_ld(soup: BeautifulSoup) -> list[dict]:
    """Extract full JSON-LD objects from structured data scripts.

    Returns list of parsed JSON-LD dictionaries. Types are derived from
    these objects in extract_page_content() — no separate type extraction needed.
    """
    objects: list[dict] = []

    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            content = script.string
            if not content:
                continue
            if len(content) > MAX_JSON_LD_SIZE:
                logger.warning("json_ld_size_exceeded", extra={"size": len(content)})
                continue

            data = json.loads(content)
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict):
                    objects.append(item)
        except (json.JSONDecodeError, TypeError) as e:
            logger.debug("json_ld_parse_error", extra={"error": str(e)})
            continue

    return objects


def extract_main_text(soup: BeautifulSoup) -> str:
    """Extract main text content, preferring semantic elements."""
    def _get_text_length(element) -> int:
        if not element:
            return 0
        return len(element.get_text(strip=True))

    main_tag = soup.find("main")
    if main_tag and _get_text_length(main_tag) > 100:
        main_element = main_tag
    elif soup.find(attrs={"role": "main"}) and _get_text_length(soup.find(attrs={"role": "main"})) > 100:
        main_element = soup.find(attrs={"role": "main"})
    else:
        articles = soup.find_all("article")
        if articles:
            best_article = max(articles, key=_get_text_length, default=None)
            if best_article and _get_text_length(best_article) > 100:
                main_element = best_article
            else:
                main_element = None
        else:
            main_element = None

    if not main_element or _get_text_length(main_element) < 100:
        main_element = (
            soup.find(id="content")
            or soup.find(class_="content")
            or soup.body
        )

    if not main_element:
        return ""

    # Remove excluded elements first (O(excluded_elements)), then extract text in one pass
    exclude_tags = {"script", "style", "nav", "footer", "header", "aside", "noscript"}
    for tag in main_element.find_all(exclude_tags):
        tag.decompose()

    return main_element.get_text(separator=" ", strip=True)


def extract_internal_links(soup: BeautifulSoup, page_url: str) -> list[dict]:
    """Extract internal links with anchor text and target URL.

    Returns list of {href, anchor_text, in_content_area} dicts.
    Filters nav/footer/header links via in_content_area flag.
    """
    from urllib.parse import urlparse

    parsed_page = urlparse(page_url)
    page_domain = parsed_page.netloc.lower()
    results: list[dict] = []

    for a_tag in soup.find_all("a", href=True)[:500]:
        href = a_tag["href"].strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue

        # Check if internal: relative path or same domain
        is_internal = False
        if href.startswith("/") and not href.startswith("//"):
            is_internal = True
        else:
            try:
                parsed_href = urlparse(href)
                if parsed_href.netloc.lower() == page_domain:
                    is_internal = True
            except Exception:
                continue

        if not is_internal:
            continue

        anchor_text = a_tag.get_text(strip=True)[:200]
        in_content_area = a_tag.find_parent(["nav", "header", "footer", "aside"]) is None

        results.append({
            "href": href,
            "anchor_text": anchor_text,
            "in_content_area": in_content_area,
        })

    return results


def detect_comparison_table(soup: BeautifulSoup) -> bool:
    """Check for a comparison table with >=3 columns and >=3 rows."""
    for table in soup.find_all("table")[:10]:
        rows = table.find_all("tr")
        if len(rows) < 3:
            continue
        # Check column count from first row
        first_row = rows[0]
        cols = first_row.find_all(["th", "td"])
        if len(cols) >= 3:
            return True
    return False


def extract_dates(soup: BeautifulSoup) -> tuple[date | None, date | None]:
    """Extract publish_date and last_modified from JSON-LD and meta tags.

    Returns (publish_date, last_modified) as date objects or None.
    """
    publish_date: date | None = None
    last_modified: date | None = None

    # Try JSON-LD first
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            content = script.string
            if not content or len(content) > MAX_JSON_LD_SIZE:
                continue
            data = json.loads(content)
            items = data if isinstance(data, list) else [data]
            for item in items:
                if not isinstance(item, dict):
                    continue
                if not publish_date and item.get("datePublished"):
                    try:
                        publish_date = date.fromisoformat(str(item["datePublished"])[:10])
                    except (ValueError, TypeError):
                        pass
                if not last_modified and item.get("dateModified"):
                    try:
                        last_modified = date.fromisoformat(str(item["dateModified"])[:10])
                    except (ValueError, TypeError):
                        pass
        except (json.JSONDecodeError, TypeError):
            continue

    # Fallback to meta tags
    if not publish_date:
        meta_pub = soup.find("meta", attrs={"property": "article:published_time"})
        if meta_pub and meta_pub.get("content"):
            try:
                publish_date = date.fromisoformat(str(meta_pub["content"])[:10])
            except (ValueError, TypeError):
                pass

    if not last_modified:
        meta_mod = soup.find("meta", attrs={"property": "article:modified_time"})
        if meta_mod and meta_mod.get("content"):
            try:
                last_modified = date.fromisoformat(str(meta_mod["content"])[:10])
            except (ValueError, TypeError):
                pass

    return publish_date, last_modified


def _extract_body_html(soup: BeautifulSoup, raw_html: str) -> str:
    """Extract just the body HTML for DOM-based detection."""
    body = soup.find("body")
    if body:
        return str(body)
    return raw_html
