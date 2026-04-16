"""Content quality pattern detectors for GEO audit.

Each detector checks a specific AutoGEO quality rule and returns a Finding.
Uses `check_*` prefix (public, separate module) — deliberate divergence from
detector.py's `_detect_*` private functions.
"""

import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from .models import Finding, Severity


def check_heading_hierarchy(soup: BeautifulSoup) -> Finding:
    """Rule 1: H1→H2→H3 nesting, detect skipped levels."""
    headings = []
    for tag in soup.find_all(["h1", "h2", "h3", "h4"]):
        level = int(tag.name[1])
        headings.append(level)

    if not headings:
        return Finding(
            factor_id="heading_hierarchy",
            factor_name="Heading Hierarchy",
            detected=False,
            severity=Severity.RECOMMENDED,
            details="No headings found",
        )

    skips = []
    for i in range(1, len(headings)):
        if headings[i] > headings[i - 1] + 1:
            skips.append(f"H{headings[i-1]}→H{headings[i]}")

    return Finding(
        factor_id="heading_hierarchy",
        factor_name="Heading Hierarchy",
        detected=len(skips) == 0,
        severity=Severity.RECOMMENDED,
        count=len(skips),
        evidence=tuple(skips[:3]),
        details="Proper hierarchy" if not skips else f"Skipped levels: {', '.join(skips[:3])}",
    )


def check_statistics_presence(text: str) -> Finding:
    """Rule 2: Count statistics/data points in text."""
    pattern = r"\d+[%$€£]|\$[\d,]+|\d+\.\d+[%x]|\d{2,}(?:\s*(?:million|billion|thousand|users|customers|pages))"
    matches = re.findall(pattern, text, re.IGNORECASE)
    count = len(matches)

    return Finding(
        factor_id="statistics_presence",
        factor_name="Statistics & Data Points",
        detected=count >= 3,
        severity=Severity.IMPORTANT,
        count=count,
        evidence=tuple(matches[:5]),
        details=f"{count} data point(s) found" + ("" if count >= 3 else " (recommend 3+)"),
    )


def check_authoritative_citations(soup: BeautifulSoup) -> Finding:
    """Rule 3: Count links to .gov, .edu, doi.org."""
    auth_domains = {".gov", ".edu", "doi.org", "scholar.google.com", "pubmed.ncbi.nlm.nih.gov"}
    count = 0
    evidence = []

    for link in soup.find_all("a", href=True)[:500]:
        href = str(link["href"])
        try:
            parsed = urlparse(href)
            domain = parsed.netloc.lower()
            if any(domain.endswith(d) for d in auth_domains):
                count += 1
                evidence.append(domain)
        except Exception:
            continue

    return Finding(
        factor_id="authoritative_citations",
        factor_name="Authoritative Citations",
        detected=count >= 1,
        severity=Severity.RECOMMENDED,
        count=count,
        evidence=tuple(list(set(evidence))[:5]),
        details=f"{count} authoritative link(s)" + ("" if count >= 1 else " (recommend 1+)"),
    )


def check_expert_quotes(soup: BeautifulSoup) -> Finding:
    """Rule 5: Blockquotes with attribution pattern."""
    blockquotes = soup.find_all("blockquote")
    attributed = 0
    evidence = []

    for bq in blockquotes[:20]:
        text = bq.get_text(strip=True)
        # Check for attribution patterns: "— Name", "- Name", cite tag
        cite = bq.find("cite")
        has_dash_attr = bool(re.search(r"[—–-]\s*[A-Z][a-z]", text))
        if cite or has_dash_attr:
            attributed += 1
            evidence.append(text[:80])

    return Finding(
        factor_id="expert_quotes",
        factor_name="Expert Quotes with Attribution",
        detected=attributed >= 1,
        severity=Severity.OPTIONAL,
        count=attributed,
        evidence=tuple(evidence[:3]),
        details=f"{attributed} attributed quote(s)" + ("" if attributed >= 1 else " (recommend 1+)"),
    )


def check_faq_sections(soup: BeautifulSoup, schema_types: list[str]) -> Finding:
    """Rule 6: FAQ heading, FAQPage schema, or details/summary elements."""
    signals = []

    # Check headings for FAQ
    for heading in soup.find_all(["h2", "h3"]):
        text = heading.get_text(strip=True).lower()
        if "faq" in text or "frequently asked" in text or "common questions" in text:
            signals.append("FAQ heading found")
            break

    # Check schema
    if "FAQPage" in schema_types:
        signals.append("FAQPage schema present")

    # Check details/summary elements
    details_count = len(soup.find_all("details"))
    if details_count >= 3:
        signals.append(f"{details_count} <details> elements")

    return Finding(
        factor_id="faq_sections",
        factor_name="FAQ Section",
        detected=len(signals) >= 1,
        severity=Severity.IMPORTANT,
        count=len(signals),
        evidence=tuple(signals),
        details="; ".join(signals) if signals else "No FAQ section detected",
    )


def check_answer_first_intro(soup: BeautifulSoup) -> Finding:
    """Rule 8: First paragraph should lead with key fact, not filler."""
    import copy
    soup = copy.copy(soup)
    for tag in soup.find_all(["style", "noscript"]):
        tag.decompose()
    first_p = soup.find("p")
    if not first_p:
        return Finding(
            factor_id="answer_first_intro",
            factor_name="Answer-First Introduction",
            detected=None,
            severity=Severity.IMPORTANT,
            details="No paragraph found",
        )

    text = first_p.get_text(strip=True)
    word_count = len(text.split())

    filler_starts = [
        "in this article", "in this guide", "in this post",
        "welcome to", "today we", "have you ever",
        "are you looking", "if you're looking", "when it comes to",
    ]
    has_filler = any(text.lower().startswith(f) for f in filler_starts)
    good_length = 20 <= word_count <= 80

    return Finding(
        factor_id="answer_first_intro",
        factor_name="Answer-First Introduction",
        detected=not has_filler and good_length,
        severity=Severity.IMPORTANT,
        count=word_count,
        evidence=(text[:120],),
        details=(
            f"{word_count} words"
            + (", starts with filler" if has_filler else "")
            + (f", too {'short' if word_count < 20 else 'long'}" if not good_length else "")
        ),
    )


def check_comparison_tables(soup: BeautifulSoup) -> Finding:
    """Rule 9: Comparison tables with >=3 cols and >=3 rows."""
    from .extraction import detect_comparison_table

    detected = detect_comparison_table(soup)
    table_count = len(soup.find_all("table"))

    return Finding(
        factor_id="comparison_tables",
        factor_name="Comparison Tables",
        detected=detected,
        severity=Severity.RECOMMENDED,
        count=table_count,
        details="Comparison table found" if detected else f"{table_count} table(s), none qualifying as comparison (need 3+ cols, 3+ rows)",
    )


def check_list_structures(soup: BeautifulSoup) -> Finding:
    """Rule 10: Ordered/unordered lists for scannability."""
    ul_count = len(soup.find_all("ul"))
    ol_count = len(soup.find_all("ol"))
    total = ul_count + ol_count

    # Calculate list-to-text ratio
    text_len = len(soup.get_text(strip=True))
    list_text_len = sum(
        len(lst.get_text(strip=True))
        for lst in soup.find_all(["ul", "ol"])[:50]
    )
    ratio = list_text_len / max(1, text_len)

    return Finding(
        factor_id="list_structures",
        factor_name="List Structures",
        detected=total >= 2,
        severity=Severity.RECOMMENDED,
        count=total,
        evidence=(f"{ul_count} unordered, {ol_count} ordered, {ratio:.0%} of content",),
        details=f"{total} list(s)" + ("" if total >= 2 else " (recommend 2+)"),
    )


def check_eeat_signals(soup: BeautifulSoup) -> Finding:
    """Rule 12: Author byline, Person schema, rel=author."""
    signals = []

    # Author links
    author_links = soup.find_all("a", attrs={"rel": "author"})
    if author_links:
        signals.append(f"{len(author_links)} rel=author link(s)")

    # Author meta
    author_meta = soup.find("meta", attrs={"name": "author"})
    if author_meta and author_meta.get("content"):
        signals.append(f"meta author: {author_meta['content'][:50]}")

    # Look for common author patterns
    for cls in ["author", "byline", "writer"]:
        elements = soup.find_all(class_=re.compile(cls, re.IGNORECASE))
        if elements:
            signals.append(f".{cls} element found")
            break

    # Person schema (check raw HTML for speed)
    raw = str(soup)[:50000]
    if '"Person"' in raw or "'Person'" in raw:
        signals.append("Person schema detected")

    return Finding(
        factor_id="eeat_signals",
        factor_name="E-E-A-T Signals",
        detected=len(signals) >= 1,
        severity=Severity.RECOMMENDED,
        count=len(signals),
        evidence=tuple(signals[:3]),
        details="; ".join(signals) if signals else "No author/expertise signals found",
    )


def check_paragraph_focus(text: str) -> Finding:
    """Rule 13: Paragraphs should be 3-5 sentences max."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return Finding(
            factor_id="paragraph_focus",
            factor_name="Focused Paragraphs",
            detected=None,
            severity=Severity.OPTIONAL,
            details="No paragraphs detected",
        )

    long_paras = 0
    for para in paragraphs:
        sentences = re.split(r"[.!?]+\s+", para)
        sent_count = len([s for s in sentences if len(s.strip()) > 10])
        if sent_count > 5:
            long_paras += 1

    return Finding(
        factor_id="paragraph_focus",
        factor_name="Focused Paragraphs",
        detected=long_paras == 0,
        severity=Severity.OPTIONAL,
        count=long_paras,
        evidence=(f"{long_paras}/{len(paragraphs)} paragraphs exceed 5 sentences",),
        details="All paragraphs focused" if long_paras == 0 else f"{long_paras} paragraph(s) too long (>5 sentences)",
    )


def check_word_count(text: str) -> Finding:
    """Rule 15: Comprehensive coverage (1000+ words for complex topics)."""
    words = len(text.split())

    return Finding(
        factor_id="word_count",
        factor_name="Content Comprehensiveness",
        detected=words >= 1000,
        severity=Severity.RECOMMENDED,
        count=words,
        details=f"{words} words" + ("" if words >= 1000 else " (recommend 1000+ for complex topics)"),
    )


def check_content_freshness(json_ld_objects: list[dict], soup: BeautifulSoup) -> Finding:
    """Rule 11: Content freshness via dateModified signals."""
    from .extraction import extract_dates

    pub_date, mod_date = extract_dates(soup)

    # Also check JSON-LD objects directly
    if not mod_date:
        for obj in json_ld_objects:
            if obj.get("dateModified"):
                mod_date = str(obj["dateModified"])[:10]
                break

    signals = []
    if pub_date:
        signals.append(f"Published: {pub_date}")
    if mod_date:
        signals.append(f"Modified: {mod_date}")

    return Finding(
        factor_id="content_freshness",
        factor_name="Content Freshness Signals",
        detected=bool(mod_date or pub_date),
        severity=Severity.RECOMMENDED,
        count=len(signals),
        evidence=tuple(signals),
        details="; ".join(signals) if signals else "No dateModified or datePublished found",
    )


# =============================================================================
# Collector
# =============================================================================


def detect_content_quality(
    soup: BeautifulSoup, text: str, schema_types: list[str],
    json_ld_objects: list[dict] | None = None,
) -> list[Finding]:
    """Run all content quality detectors and return aggregated findings.

    Handles None for 'unable to check' cases (matching detector.py convention).
    """
    findings: list[Finding] = []

    findings.append(check_heading_hierarchy(soup))
    findings.append(check_statistics_presence(text))
    findings.append(check_authoritative_citations(soup))
    findings.append(check_expert_quotes(soup))
    findings.append(check_faq_sections(soup, schema_types))
    findings.append(check_answer_first_intro(soup))
    findings.append(check_comparison_tables(soup))
    findings.append(check_list_structures(soup))
    findings.append(check_eeat_signals(soup))
    findings.append(check_paragraph_focus(text))
    findings.append(check_word_count(text))

    if json_ld_objects is not None:
        findings.append(check_content_freshness(json_ld_objects, soup))

    return findings
