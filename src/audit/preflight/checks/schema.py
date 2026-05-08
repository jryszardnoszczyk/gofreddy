"""Schema.org JSON-LD parsing.

Fetches homepage + /about + /pricing, parses ``<script type="application/ld+json">``
blocks, extracts @types and detects @graph composability + SearchAction +
BreadcrumbList markers. Skip-not-raise on malformed blocks.
"""
from __future__ import annotations

import json
from typing import Any

import httpx
from bs4 import BeautifulSoup


_PAGES = ("", "/about", "/pricing")


def _walk_types(node: Any, out: set[str]) -> None:
    if isinstance(node, dict):
        t = node.get("@type")
        if isinstance(t, str):
            out.add(t)
        elif isinstance(t, list):
            for x in t:
                if isinstance(x, str):
                    out.add(x)
        for v in node.values():
            _walk_types(v, out)
    elif isinstance(node, list):
        for v in node:
            _walk_types(v, out)


def _has_graph_ids(node: Any) -> bool:
    """True if any @graph node carries an @id (composability marker)."""
    if isinstance(node, dict):
        graph = node.get("@graph")
        if isinstance(graph, list):
            return any(isinstance(g, dict) and "@id" in g for g in graph)
    return False


def _has_search_action(types: set[str], data: Any) -> bool:
    if "WebSite" not in types:
        return False
    # Cheap scan — search the JSON for "potentialAction"+"SearchAction".
    blob = json.dumps(data) if not isinstance(data, str) else data
    return "SearchAction" in blob


async def check(domain: str) -> dict:
    base = f"https://{domain.strip().rstrip('/')}"
    pages_sampled: list[str] = []
    types: set[str] = set()
    composability = False
    search_action = False
    breadcrumbs = False
    errors: list[str] = []

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        for path in _PAGES:
            url = base + path
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    continue
                pages_sampled.append(url)
                soup = BeautifulSoup(resp.text, "html.parser")
                for block in soup.find_all("script", attrs={"type": "application/ld+json"}):
                    raw = block.string or block.get_text(strip=True)
                    if not raw:
                        continue
                    try:
                        data = json.loads(raw)
                    except json.JSONDecodeError as exc:
                        errors.append(f"{url}: {exc.msg}")
                        continue
                    block_types: set[str] = set()
                    _walk_types(data, block_types)
                    types |= block_types
                    if _has_graph_ids(data):
                        composability = True
                    if _has_search_action(block_types, data):
                        search_action = True
                    if "BreadcrumbList" in block_types and path:
                        breadcrumbs = True
            except httpx.HTTPError:
                continue

    return {
        "pages_sampled": pages_sampled,
        "types_present": sorted(types),
        "at_graph_composability": composability,
        "search_action": search_action,
        "breadcrumbs": breadcrumbs,
        "errors": errors,
    }
