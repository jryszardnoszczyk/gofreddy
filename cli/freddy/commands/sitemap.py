"""Sitemap parser CLI command.

Fetches and parses sitemaps from a domain URL.
"""

import asyncio
import importlib
import json
import sys
from pathlib import Path

import typer

try:
    from src.geo.sitemap import SitemapParser
except ImportError:
    repo_root = Path(__file__).resolve().parents[3]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    try:
        for module_name in ("src.geo.sitemap", "src.geo", "src"):
            sys.modules.pop(module_name, None)
        SitemapParser = importlib.import_module("src.geo.sitemap").SitemapParser
    except ImportError:
        SitemapParser = None  # type: ignore[assignment,misc]


def sitemap_command(
    url: str = typer.Argument(..., help="Base URL of the site (e.g., https://example.com)"),
    max_urls: int = typer.Option(100, "--max", help="Maximum URLs to return"),
) -> None:
    """Parse sitemaps from a domain and list discovered URLs."""
    if SitemapParser is None:
        typer.echo(
            json.dumps(
                {
                    "error": {
                        "code": "sitemap_unavailable",
                        "message": "Could not import src.geo.sitemap",
                    }
                }
            ),
            err=True,
        )
        raise typer.Exit(1)
    parser = SitemapParser()
    inventory = asyncio.run(parser.parse(url))

    entries = inventory.entries[:max_urls]
    output = {
        "urls_found": len(inventory.entries),
        "urls_returned": len(entries),
        "sitemaps_parsed": inventory.sitemaps_parsed,
        "errors": inventory.errors,
        "urls": [
            {
                "url": e.url,
                "lastmod": e.lastmod,
                "priority": e.priority,
            }
            for e in entries
        ],
    }

    typer.echo(json.dumps(output, indent=2))
