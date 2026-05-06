#!/usr/bin/env python3
"""Deterministic brief.md → report.md transform.

Replaces LLM-based DELIVER phase. Applies consistent formatting:
- Title upgrade (brief → Competitive Intelligence Report)
- Metadata header (date, client, data sources)
- Section reordering for executive consumption
- Markdown cleanup (consistent heading levels, table formatting)

Usage:
    python3 scripts/format_report.py <session_dir>
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


REPORT_HEADER = """# Competitive Intelligence Report: {client}

**Generated**: {date}
**Data Sources**: {sources}
**Quality Score**: {quality_score}

---

"""

# Preferred section order for the final report
SECTION_ORDER = [
    "Executive Summary",
    "Share of Observed",
    "Competitive Positioning",
    "Competitor Ads",
    "Creative Patterns",
    "Content & Creator Ecosystem",
    "Format Vacuum",
    "Known Unknowns",
    "Recommendations",
    "Monitoring Triggers",
    "Changes vs Prior",
]


def _extract_sections(text: str) -> list[tuple[str, str, str]]:
    """Extract (heading, title, content) tuples from markdown."""
    sections = []
    # Split on ## headers
    parts = re.split(r"(^##\s+.+$)", text, flags=re.MULTILINE)

    for i in range(1, len(parts), 2):
        heading = parts[i].strip()
        content = parts[i + 1] if i + 1 < len(parts) else ""
        title = heading.lstrip("#").strip()
        sections.append((heading, title, content.strip()))

    return sections


def _order_sections(sections: list[tuple[str, str, str]]) -> list[tuple[str, str, str]]:
    """Reorder sections to match preferred order."""
    ordered = []
    remaining = list(sections)

    for preferred in SECTION_ORDER:
        for i, (heading, title, content) in enumerate(remaining):
            if preferred.lower() in title.lower():
                ordered.append((heading, title, content))
                remaining.pop(i)
                break

    # Append any sections not in preferred order
    ordered.extend(remaining)
    return ordered


def _detect_sources(text: str) -> str:
    """Detect data sources mentioned in the brief."""
    sources = []
    source_map = {
        "Foreplay": "Foreplay (Meta/TikTok/LinkedIn ads)",
        "Adyntel": "Adyntel (Google Display ads)",
        "freddy detect": "GEO Infrastructure Scan",
        "freddy visibility": "AI Search Visibility",
        "freddy scrape": "Website Scraping",
        "ScrapeCreators": "TikTok Creator Data",
    }
    for keyword, label in source_map.items():
        if keyword.lower() in text.lower():
            sources.append(label)
    return ", ".join(sources) if sources else "See individual sections"


def _extract_quality_score(session_dir: Path) -> str:
    """Extract quality score from results.jsonl."""
    results_file = session_dir / "results.jsonl"
    if not results_file.exists():
        return "N/A"

    # Read last verify entry
    for line in reversed(results_file.read_text().strip().split("\n")):
        try:
            entry = json.loads(line)
            if entry.get("type") in ("verify", "synthesize"):
                score = entry.get("quality_score", "")
                if score:
                    return str(score)
        except json.JSONDecodeError:
            continue
    return "N/A"


def format_report(session_dir: str) -> None:
    """Transform brief.md into report.md."""
    session_path = Path(session_dir)
    brief_path = session_path / "brief.md"
    report_path = session_path / "report.md"

    if not brief_path.exists():
        print(f"No brief.md found in {session_dir}", file=sys.stderr)
        sys.exit(1)

    brief_text = brief_path.read_text()

    # Extract client name from first line or session.md
    client = "Unknown Client"
    session_md = session_path / "session.md"
    if session_md.exists():
        match = re.search(r"^# Session:\s*(.+)$", session_md.read_text(), re.MULTILINE)
        if match:
            client = match.group(1).strip()

    # Extract and reorder sections
    sections = _extract_sections(brief_text)
    sections = _order_sections(sections)

    # Build report
    header = REPORT_HEADER.format(
        client=client,
        date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        sources=_detect_sources(brief_text),
        quality_score=_extract_quality_score(session_path),
    )

    body_parts = []
    for heading, title, content in sections:
        body_parts.append(f"{heading}\n\n{content}")

    report_text = header + "\n\n".join(body_parts) + "\n"

    # Atomic write
    tmp = report_path.with_suffix(".md.tmp")
    tmp.write_text(report_text)
    tmp.rename(report_path)
    print(f"Written: {report_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <session_dir>", file=sys.stderr)
        sys.exit(1)
    format_report(sys.argv[1])
