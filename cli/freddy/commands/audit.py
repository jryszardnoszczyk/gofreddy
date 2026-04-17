"""Audit commands — call providers directly for client audits."""
from __future__ import annotations

import asyncio
import dataclasses
from pathlib import Path
from typing import Any

import typer

from src.common.cost_recorder import cost_recorder

from ..providers import emit, get_provider, handle_errors
from ..config import load_config

app = typer.Typer(help="Client distribution audit commands.", no_args_is_help=True)


def _init_cost_log(client_name: str | None) -> None:
    """Route cost logs to per-client file when client specified."""
    if client_name:
        cfg = load_config()
        if cfg is None or cfg.clients_dir is None:
            raise typer.BadParameter(
                "No clients_dir configured. Run `freddy setup` or set FREDDY_CLIENTS_DIR."
            )
        log_path = cfg.clients_dir / client_name / "cost_log.jsonl"
    else:
        log_path = Path.home() / ".freddy" / "cost_log.jsonl"
    cost_recorder.init(log_path)


def _to_dict(obj: Any) -> Any:
    """Make dataclasses JSON-serializable; lists recurse."""
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.asdict(obj)
    if isinstance(obj, list):
        return [_to_dict(x) for x in obj]
    return obj


@app.command()
@handle_errors
def seo(
    domain: str = typer.Argument(..., help="Domain to audit (e.g. example.com)"),
    client: str | None = typer.Option(None, "--client", help="Scope to a client workspace"),
) -> None:
    """Run an SEO audit via DataForSEO: domain rank snapshot."""
    _init_cost_log(client)
    provider = get_provider("dataforseo")

    async def _run() -> dict:
        rank = await provider.snapshot_domain_rank(domain)
        return {"domain": domain, "rank": _to_dict(rank)}

    emit(asyncio.run(_run()))


@app.command()
@handle_errors
def competitive(
    domain: str = typer.Argument(..., help="Competitor domain"),
    client: str | None = typer.Option(None, "--client", help="Scope to a client workspace"),
    limit: int = typer.Option(50, "--limit", help="Max ads from Foreplay"),
) -> None:
    """Fetch competitor ads from Foreplay + Adyntel."""
    _init_cost_log(client)
    foreplay = get_provider("foreplay")
    adyntel = get_provider("adyntel")

    async def _run() -> dict:
        results: dict = {"domain": domain, "foreplay": [], "adyntel": []}
        try:
            results["foreplay"] = _to_dict(
                await foreplay.search_ads_by_domain(domain, limit=limit)
            )
        except Exception as e:
            results["foreplay_error"] = str(e)
        try:
            results["adyntel"] = _to_dict(
                await adyntel.search_google_ads(domain=domain)
            )
        except Exception as e:
            results["adyntel_error"] = str(e)
        finally:
            await foreplay.close()
            if hasattr(adyntel, "close"):
                await adyntel.close()
        return results

    emit(asyncio.run(_run()))


@app.command()
@handle_errors
def monitor(
    query: str = typer.Argument(..., help="Search query (brand, keyword, etc.)"),
    client: str | None = typer.Option(None, "--client", help="Scope to a client workspace"),
    limit: int = typer.Option(100, "--limit", help="Max mentions"),
) -> None:
    """Fetch recent mentions via Xpoz across social platforms."""
    _init_cost_log(client)
    xpoz = get_provider("xpoz")

    async def _run() -> dict:
        async with xpoz:
            mentions = await xpoz.fetch_all_mentions(query, max_results=limit)
        payload = _to_dict(mentions)
        return {"query": query, "count": len(payload), "mentions": payload}

    emit(asyncio.run(_run()))
