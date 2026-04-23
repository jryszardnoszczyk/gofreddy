"""Schema.org JSON-LD parsing.

Covers preflight lens 09 (Schema JSON-LD parsing).

Expected signal shape (homepage + /about + /pricing sampled):

    {
        "pages_sampled": [str],
        "types_present": [str],           # e.g. ["Organization", "WebSite", "Product"]
        "at_graph_composability": bool,   # true if @graph nodes @id-linked
        "search_action": bool,            # WebSite.potentialAction present
        "breadcrumbs":   bool,            # BreadcrumbList present on deep pages
        "errors": [str],                  # JSON-LD parse errors by page
    }

Implementation note (v1): httpx fetch → BeautifulSoup → find `<script
type="application/ld+json">` → json.loads each block → collect @types + walk
@graph. Skip malformed blocks rather than raising.
"""
from __future__ import annotations


async def check(domain: str) -> dict:
    # TODO(v1-step-C): implement via httpx + BeautifulSoup + json.
    return {"implemented": False}
