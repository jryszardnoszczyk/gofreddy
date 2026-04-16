"""DETECT step: Deterministic GEO infrastructure + SEO technical detection.

Analyzes PageContent for infrastructure facts (schema, SSR, bot access, llms.txt)
and SEO technical checks (title, meta, canonical, h1, links, alt, https, viewport).
Content quality patterns (heading hierarchy, statistics, citations, etc.) are
detected via patterns.py.
All detection is deterministic (regex, DOM parsing, counting) - NO LLM calls.
"""

import asyncio
import logging
import time
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from .models import AuditFindings, Finding, PageContent, Severity

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    import httpx

# Maximum text length for regex patterns (security)
MAX_TEXT_LENGTH = 50_000


async def detect_factors(
    page_content: PageContent,
    http_client: "httpx.AsyncClient | None" = None,
) -> AuditFindings:
    """Run all GEO infrastructure + SEO technical detectors on page content."""
    start_time = time.monotonic()

    html_for_soup = page_content.raw_html if page_content.raw_html else (
        page_content.text[:MAX_TEXT_LENGTH] if page_content.text else ""
    )
    soup = BeautifulSoup(html_for_soup, "lxml") if html_for_soup else None

    from .http_checks import detect_http_factors

    try:
        async with asyncio.timeout(30.0):
            content_findings, http_findings = await asyncio.gather(
                _detect_infrastructure_and_seo(page_content, soup),
                detect_http_factors(page_content.final_url, http_client),
                return_exceptions=True,
            )
    except asyncio.TimeoutError:
        try:
            async with asyncio.timeout(10.0):
                content_findings = await _detect_infrastructure_and_seo(
                    page_content, soup
                )
        except (asyncio.TimeoutError, Exception):
            content_findings = []
        http_findings = [
            Finding(
                factor_id="ai_bot_access",
                factor_name="AI Bot Access (robots.txt)",
                detected=None,
                severity=Severity.CRITICAL,
                details="Aggregate timeout (30s)",
            ),
            Finding(
                factor_id="llms_txt",
                factor_name="llms.txt Presence",
                detected=None,
                severity=Severity.OPTIONAL,
                details="Aggregate timeout (30s)",
            ),
        ]

    if isinstance(content_findings, Exception):
        content_findings = []
    if isinstance(http_findings, Exception):
        error_name = type(http_findings).__name__
        http_findings = [
            Finding(
                factor_id="ai_bot_access",
                factor_name="AI Bot Access (robots.txt)",
                detected=None,
                severity=Severity.CRITICAL,
                details=f"Unable to check: {error_name}",
            ),
            Finding(
                factor_id="llms_txt",
                factor_name="llms.txt Presence",
                detected=None,
                severity=Severity.OPTIONAL,
                details=f"Unable to check: {error_name}",
            ),
        ]

    all_findings = list(content_findings) + list(http_findings)

    # Content quality patterns (from patterns.py)
    from .patterns import detect_content_quality
    try:
        quality_findings = detect_content_quality(
            soup=soup if soup else BeautifulSoup("", "lxml"),
            text=page_content.text[:MAX_TEXT_LENGTH] if page_content.text else "",
            schema_types=page_content.schema_types,
            json_ld_objects=getattr(page_content, "json_ld_objects", None),
        )
        all_findings.extend(quality_findings)
    except Exception as e:
        logger.warning("Content quality detection failed: %s", e)

    factors_detected = sum(1 for f in all_findings if f.detected is True)
    factors_missing = sum(1 for f in all_findings if f.detected is False)
    factors_unable = sum(1 for f in all_findings if f.detected is None)

    critical_missing = sum(
        1 for f in all_findings if f.detected is False and f.severity == Severity.CRITICAL
    )
    important_missing = sum(
        1 for f in all_findings if f.detected is False and f.severity == Severity.IMPORTANT
    )
    recommended_missing = sum(
        1 for f in all_findings if f.detected is False and f.severity == Severity.RECOMMENDED
    )
    optional_missing = sum(
        1 for f in all_findings if f.detected is False and f.severity == Severity.OPTIONAL
    )

    detection_time_ms = int((time.monotonic() - start_time) * 1000)

    return AuditFindings(
        findings=tuple(all_findings),
        factors_checked=len(all_findings),
        factors_detected=factors_detected,
        factors_missing=factors_missing,
        factors_unable_to_check=factors_unable,
        detection_time_ms=detection_time_ms,
        critical_missing=critical_missing,
        important_missing=important_missing,
        recommended_missing=recommended_missing,
        optional_missing=optional_missing,
    )


# =============================================================================
# GEO Infrastructure Checks (kept from original)
# =============================================================================


async def _detect_infrastructure_and_seo(
    page_content: PageContent,
    soup: BeautifulSoup | None,
) -> list[Finding]:
    """Detect GEO infrastructure facts + SEO technical checks (no I/O)."""
    findings: list[Finding] = []

    # GEO infrastructure (binary facts)
    findings.append(_detect_schema_markup(page_content.schema_types))
    findings.append(_detect_ssr_issues(page_content.js_rendered))

    # SEO technical checks (DOM-based)
    findings.append(_detect_title_tag(page_content.title))
    findings.append(_detect_meta_description(page_content.meta_description))
    findings.append(_detect_canonical_url(soup, page_content.final_url))
    findings.append(_detect_single_h1(soup))
    findings.append(_detect_internal_links(soup, page_content.final_url))
    findings.append(_detect_image_alt_ratio(soup))
    findings.append(_detect_https(page_content.final_url))
    findings.append(_detect_mobile_viewport(soup))

    return findings


# === GEO Infrastructure ===


def _detect_schema_markup(schema_types: list[str]) -> Finding:
    priority_types = ["FAQPage", "HowTo", "Article", "NewsArticle", "BlogPosting"]
    found_priority = [t for t in priority_types if t in schema_types]

    detected = len(schema_types) >= 1

    if found_priority:
        details = f"Found: {', '.join(found_priority)}"
    elif schema_types:
        details = f"Found: {', '.join(schema_types[:3])}"
    else:
        details = "No JSON-LD schema found"

    return Finding(
        factor_id="schema_markup",
        factor_name="Schema Markup (JSON-LD)",
        detected=detected,
        severity=Severity.CRITICAL,
        count=len(schema_types),
        evidence=tuple(schema_types[:5]),
        details=details,
    )


def _detect_ssr_issues(js_rendered: bool) -> Finding:
    if js_rendered:
        return Finding(
            factor_id="ssr_issues",
            factor_name="Server-Side Rendering",
            detected=False,
            severity=Severity.RECOMMENDED,
            details="Page requires JavaScript - AI crawlers may not execute JS",
        )

    return Finding(
        factor_id="ssr_issues",
        factor_name="Server-Side Rendering",
        detected=True,
        severity=Severity.RECOMMENDED,
        details="Content renders without JavaScript",
    )


# =============================================================================
# SEO Technical Checks (new — free, HTTP/DOM-based)
# =============================================================================


def _detect_title_tag(title: str | None) -> Finding:
    if not title:
        return Finding(
            factor_id="title_tag",
            factor_name="Title Tag",
            detected=False,
            severity=Severity.CRITICAL,
            details="No <title> tag found",
        )

    length = len(title)
    optimal = 30 <= length <= 60

    return Finding(
        factor_id="title_tag",
        factor_name="Title Tag",
        detected=True,
        severity=Severity.CRITICAL,
        count=length,
        evidence=(title[:100],),
        details=f"Length: {length} chars" + (" (optimal)" if optimal else f" ({'too short' if length < 30 else 'too long'})"),
    )


def _detect_meta_description(description: str | None) -> Finding:
    if not description:
        return Finding(
            factor_id="meta_description",
            factor_name="Meta Description",
            detected=False,
            severity=Severity.IMPORTANT,
            details="No meta description found",
        )

    length = len(description)
    optimal = 120 <= length <= 160

    return Finding(
        factor_id="meta_description",
        factor_name="Meta Description",
        detected=True,
        severity=Severity.IMPORTANT,
        count=length,
        evidence=(description[:160],),
        details=f"Length: {length} chars" + (" (optimal)" if optimal else f" ({'too short' if length < 120 else 'too long'})"),
    )


def _detect_canonical_url(soup: BeautifulSoup | None, page_url: str) -> Finding:
    if not soup:
        return Finding(
            factor_id="canonical_url",
            factor_name="Canonical URL",
            detected=None,
            severity=Severity.IMPORTANT,
            details="No HTML to analyze",
        )

    canonical = soup.find("link", attrs={"rel": "canonical"})
    if not canonical or not canonical.get("href"):
        return Finding(
            factor_id="canonical_url",
            factor_name="Canonical URL",
            detected=False,
            severity=Severity.IMPORTANT,
            details="No canonical URL specified",
        )

    href = str(canonical["href"]).strip()
    # Check if self-referencing (normalize trailing slashes)
    self_ref = href.rstrip("/") == page_url.rstrip("/")

    return Finding(
        factor_id="canonical_url",
        factor_name="Canonical URL",
        detected=True,
        severity=Severity.IMPORTANT,
        count=1,
        evidence=(href[:200],),
        details="Self-referencing canonical" if self_ref else f"Points to: {href[:100]}",
    )


def _detect_single_h1(soup: BeautifulSoup | None) -> Finding:
    if not soup:
        return Finding(
            factor_id="single_h1",
            factor_name="Single H1 Tag",
            detected=None,
            severity=Severity.RECOMMENDED,
            details="No HTML to analyze",
        )

    h1_tags = soup.find_all("h1")
    count = len(h1_tags)

    if count == 1:
        h1_text = h1_tags[0].get_text(strip=True)[:100]
        return Finding(
            factor_id="single_h1",
            factor_name="Single H1 Tag",
            detected=True,
            severity=Severity.RECOMMENDED,
            count=1,
            evidence=(h1_text,),
            details="Exactly one H1 tag",
        )

    return Finding(
        factor_id="single_h1",
        factor_name="Single H1 Tag",
        detected=False,
        severity=Severity.RECOMMENDED,
        count=count,
        details=f"{'No' if count == 0 else count} H1 tag(s) found (expected exactly 1)",
    )


def _detect_internal_links(soup: BeautifulSoup | None, page_url: str) -> Finding:
    if not soup:
        return Finding(
            factor_id="internal_links",
            factor_name="Internal Links",
            detected=None,
            severity=Severity.RECOMMENDED,
            details="No HTML to analyze",
        )

    try:
        page_domain = urlparse(page_url).netloc.lower()
    except Exception:
        page_domain = ""

    internal_count = 0
    for link in soup.find_all("a", href=True)[:500]:
        href = str(link["href"])
        if href.startswith("/") and not href.startswith("//"):
            internal_count += 1
        elif href.startswith(("http://", "https://")):
            try:
                link_domain = urlparse(href).netloc.lower()
                if link_domain == page_domain:
                    internal_count += 1
            except Exception:
                continue

    detected = internal_count >= 3

    return Finding(
        factor_id="internal_links",
        factor_name="Internal Links",
        detected=detected,
        severity=Severity.RECOMMENDED,
        count=internal_count,
        details=f"{internal_count} internal link(s)" + ("" if detected else " (recommend 3+)"),
    )


def _detect_image_alt_ratio(soup: BeautifulSoup | None) -> Finding:
    if not soup:
        return Finding(
            factor_id="image_alt_ratio",
            factor_name="Image Alt Text",
            detected=None,
            severity=Severity.RECOMMENDED,
            details="No HTML to analyze",
        )

    images = soup.find_all("img")[:200]
    total = len(images)

    if total == 0:
        return Finding(
            factor_id="image_alt_ratio",
            factor_name="Image Alt Text",
            detected=True,
            severity=Severity.RECOMMENDED,
            count=0,
            details="No images on page",
        )

    with_alt = sum(
        1 for img in images
        if img.get("alt") and img["alt"].strip()
    )
    ratio = with_alt / total if total > 0 else 0
    detected = ratio >= 0.8

    return Finding(
        factor_id="image_alt_ratio",
        factor_name="Image Alt Text",
        detected=detected,
        severity=Severity.RECOMMENDED,
        count=with_alt,
        evidence=(f"{with_alt}/{total} images have alt text",),
        details=f"Alt ratio: {ratio:.0%}" + ("" if detected else " (recommend 80%+)"),
    )


def _detect_https(url: str) -> Finding:
    is_https = url.startswith("https://")

    return Finding(
        factor_id="https",
        factor_name="HTTPS",
        detected=is_https,
        severity=Severity.CRITICAL,
        details="HTTPS enabled" if is_https else "Not using HTTPS",
    )


def _detect_mobile_viewport(soup: BeautifulSoup | None) -> Finding:
    if not soup:
        return Finding(
            factor_id="mobile_viewport",
            factor_name="Mobile Viewport",
            detected=None,
            severity=Severity.IMPORTANT,
            details="No HTML to analyze",
        )

    viewport = soup.find("meta", attrs={"name": "viewport"})
    if not viewport or not viewport.get("content"):
        return Finding(
            factor_id="mobile_viewport",
            factor_name="Mobile Viewport",
            detected=False,
            severity=Severity.IMPORTANT,
            details="No viewport meta tag",
        )

    content = str(viewport["content"])
    return Finding(
        factor_id="mobile_viewport",
        factor_name="Mobile Viewport",
        detected=True,
        severity=Severity.IMPORTANT,
        evidence=(content[:100],),
        details="Viewport configured",
    )
