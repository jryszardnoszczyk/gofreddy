#!/usr/bin/env python3
"""Deterministic gap allocation for GEO sessions.

Reads competitive data + page inventory -> assigns one competitive angle per page,
groups into batches of 3-4 by page type.

Usage: python scripts/geo/allocate_gaps.py <session_dir>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def load_pages(session_dir: Path) -> list[dict]:
    """Load page inventory from session directory."""
    pages = []
    pages_dir = session_dir / "pages"
    if not pages_dir.exists():
        return pages
    for page_file in sorted(pages_dir.glob("*.json")):
        try:
            data = json.loads(page_file.read_text())
            data["_slug"] = page_file.stem
            pages.append(data)
        except (json.JSONDecodeError, OSError):
            continue
    return pages


def load_competitive_data(session_dir: Path) -> dict:
    """Load competitive visibility data."""
    visibility_file = session_dir / "competitors" / "visibility.json"
    if not visibility_file.exists():
        return {}
    try:
        return json.loads(visibility_file.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def extract_competitor_gaps(competitive_data: dict) -> list[str]:
    """Extract available competitive gaps from visibility data."""
    gaps = set()
    if isinstance(competitive_data, dict):
        for query_data in competitive_data.values():
            if isinstance(query_data, dict):
                for platform_data in query_data.values():
                    if isinstance(platform_data, dict):
                        for citation in platform_data.get("citations", []):
                            if isinstance(citation, dict):
                                domain = citation.get("domain", "")
                                if domain:
                                    gaps.add(domain)
    return sorted(gaps)


def classify_page_type(page: dict) -> str:
    """Classify page into type based on content signals."""
    url = page.get("url", page.get("final_url", ""))
    text = page.get("text", "")
    word_count = len(text.split()) if text else 0
    h2_count = len(page.get("h2s", []))

    url_lower = url.lower()
    if "/pricing" in url_lower or "/plans" in url_lower:
        return "pricing"
    if "/blog/" in url_lower or "/article" in url_lower:
        return "educational"
    if "/compare" in url_lower or "/vs" in url_lower:
        return "comparison"
    if word_count < 300:
        return "thin"
    if h2_count >= 5:
        return "feature-rich"
    return "hub"


def allocate_gaps(pages: list[dict], gaps: list[str]) -> list[dict]:
    """Assign one unique competitive angle per page."""
    allocations = []
    used_gaps = set()

    for page in pages:
        page_type = classify_page_type(page)
        slug = page.get("_slug", page.get("url", "unknown"))

        # Pick first unused gap
        assigned_gap = None
        for gap in gaps:
            if gap not in used_gaps:
                assigned_gap = gap
                used_gaps.add(gap)
                break

        if assigned_gap is None:
            assigned_gap = f"unique-feature-{len(allocations)}"

        allocations.append({
            "slug": slug,
            "url": page.get("url", page.get("final_url", "")),
            "page_type": page_type,
            "assigned_gap": assigned_gap,
        })

    return allocations


def group_into_batches(allocations: list[dict], batch_size: int = 3) -> list[list[dict]]:
    """Group pages into batches by page type."""
    sorted_allocs = sorted(allocations, key=lambda x: x["page_type"])
    batches = []
    for i in range(0, len(sorted_allocs), batch_size):
        batches.append(sorted_allocs[i:i + batch_size])
    return batches


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <session_dir>", file=sys.stderr)
        sys.exit(1)

    session_dir = Path(sys.argv[1])
    if not session_dir.exists():
        print(f"Session directory not found: {session_dir}", file=sys.stderr)
        sys.exit(1)

    pages = load_pages(session_dir)
    competitive_data = load_competitive_data(session_dir)
    gaps = extract_competitor_gaps(competitive_data)

    allocations = allocate_gaps(pages, gaps)
    batches = group_into_batches(allocations)

    output = {
        "pages": len(pages),
        "gaps_available": len(gaps),
        "allocations": allocations,
        "batches": [[a["slug"] for a in batch] for batch in batches],
    }

    print(json.dumps(output, indent=2))

    # Write to session dir
    output_file = session_dir / "gap_allocation.json"
    output_file.write_text(json.dumps(output, indent=2) + "\n")
    print(f"Written: {output_file}", file=sys.stderr)


if __name__ == "__main__":
    main()
