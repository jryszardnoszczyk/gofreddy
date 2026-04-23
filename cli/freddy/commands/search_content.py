"""Search competitor content across platforms.

Data-only tool for autoresearch sessions. No LLM calls.
Uses IC (Influencers.club) discovery API directly — avoids full SearchService
dependency chain (parser, fetchers, backends).
"""

from __future__ import annotations

import asyncio
import json
import os

import typer

from ..output import emit, emit_error
from cli.freddy.fixture.cache_integration import try_read_cache

_VALID_PLATFORMS = {"tiktok", "instagram", "youtube"}


def search_content_command(
    query: str = typer.Argument(..., help="Search query (brand/keyword)"),
    platform: str = typer.Option("tiktok", "--platform", help="Platform: tiktok|instagram|youtube"),
    limit: int = typer.Option(10, "--limit", help="Max results"),
) -> None:
    """Search competitor content across platforms via IC discovery."""
    if platform not in _VALID_PLATFORMS:
        emit_error("invalid_platform", f"Must be one of: {', '.join(sorted(_VALID_PLATFORMS))}")
        return

    cached = try_read_cache("ic", "creator_videos", query)
    if cached is not None:
        typer.echo(json.dumps(cached))
        return

    ic_key = os.environ.get("IC_API_KEY")
    if not ic_key:
        emit_error("missing_credentials", "IC_API_KEY environment variable not set")
        return

    try:
        result = asyncio.run(_search(query, platform, limit, ic_key))
    except SystemExit:
        raise
    except Exception:
        emit_error("search_content_failed", "Failed to search content")
        return

    from ..main import get_state
    emit(result, human=get_state().human)


async def _search(query: str, platform: str, limit: int, api_key: str) -> dict:
    from src.search.ic_backend import ICBackend

    backend = ICBackend(api_key=api_key)
    async with backend:
        result = await backend.discover(
            platform=platform,
            filters={"ai_search": query[:500]},
            limit=min(limit, 50),
        )
        accounts = result.get("accounts", [])[:limit]
        return {
            "query": query,
            "platform": platform,
            "result_count": len(accounts),
            "results": accounts,
        }
