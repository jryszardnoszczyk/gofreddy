"""Monitor commands — mentions, sentiment, share of voice, baseline, topics."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from collections import Counter
from pathlib import Path
from typing import Any

import typer
from pydantic import BaseModel, Field, ValidationError

from ..api import api_request, handle_errors, make_client
from ..config import load_config
from ..output import emit, emit_error
from cli.freddy.fixture.cache_integration import try_read_cache

logger = logging.getLogger(__name__)

app = typer.Typer(help="Brand monitoring data commands.", no_args_is_help=True)

# ─── Sonnet summarizer: module-top constants + Pydantic models ────────────────
# Bump PROMPT_VERSION on every prompt edit — stale cache entries become
# unreachable by construction (hash changes), no manual flush required.
PROMPT_VERSION = "2026-04-22.v1"

# Volume tiers drive `source_mix[*].sample` size. Inline constants (no config
# knob — single purpose, no tuning surface).
_TIER_LOW_MAX = 25        # ≤25 mentions → 1 sample per source
_TIER_MED_MAX = 100       # 26-100 → 3; >100 → 5
_SAMPLE_SIZE_LOW = 1
_SAMPLE_SIZE_MED = 3
_SAMPLE_SIZE_HIGH = 5

_CACHE_DIR = Path.home() / ".freddy" / "cache" / "monitor_summary"
_CACHE_TTL_SECONDS = 24 * 60 * 60  # 24h

# Mention payload size cap per item sent to Sonnet — keeps prompt bounded.
_MAX_MENTIONS_TO_AGENT = 200
_CONTENT_SNIPPET_CHARS = 400


class TopMention(BaseModel):
    mention_id: str
    relevance_rank: int = Field(ge=1)
    reason: str


class Theme(BaseModel):
    theme: str
    representative_quotes: list[str]


class SourceSampleItem(BaseModel):
    mention_id: str
    headline: str


class SourceMixEntry(BaseModel):
    source: str
    sample: list[SourceSampleItem]


class SonnetSummaryPayload(BaseModel):
    """Pinned schema for the Sonnet-authored portion of the summary."""

    top_mentions: list[TopMention]
    themes: list[Theme]
    source_mix: list[SourceMixEntry]


def _require_config():
    config = load_config()
    if not config:
        emit_error("not_authenticated", "No API key configured. Run: freddy auth login --api-key <key>")
    return config


@app.command()
@handle_errors
def mentions(
    monitor_id: str = typer.Argument(..., help="Monitor UUID"),
    date_from: str = typer.Option(None, "--date-from", help="Start date (YYYY-MM-DD)"),
    date_to: str = typer.Option(None, "--date-to", help="End date (YYYY-MM-DD)"),
    limit: int = typer.Option(50, "--limit", help="Mentions per page"),
    format: str = typer.Option("full", "--format", help="Output format: full|summary"),
) -> None:
    """Fetch mentions with auto-pagination (ceiling: 2000)."""
    cached = try_read_cache("xpoz", "mentions", monitor_id, shape_flags={"format": format})
    if cached is not None:
        typer.echo(json.dumps(cached))
        return
    config = _require_config()
    client = make_client(config)

    all_mentions: list = []
    offset = 0
    ceiling = 2000
    result: dict = {}

    while len(all_mentions) < ceiling:
        params: dict = {
            "monitor_id": monitor_id,
            "limit": limit,
            "offset": offset,
            "date_from": date_from,
            "date_to": date_to,
        }
        try:
            result = api_request(client, "GET", f"/v1/monitors/{monitor_id}/mentions", params=params)
        except Exception as exc:
            # EF4: Graceful page failure — return partial results
            if all_mentions:
                break
            raise exc
        items = result.get("mentions", result.get("data", []))
        if not items:
            break
        all_mentions.extend(items)
        if len(items) < limit:
            break
        offset += limit

    # CLI-5: Use API-provided total if available, fall back to local count
    api_total = result.get("total", len(all_mentions)) if result else len(all_mentions)

    # G2: Summary format — deterministic aggregates (raw floor) + Sonnet-authored
    # top_mentions / themes / source_mix. Falls back to aggregates alone on agent failure.
    if format == "summary":
        output = _build_summary(all_mentions, api_total, monitor_id=monitor_id)
    else:
        output = {"mentions": all_mentions, "total": api_total}
    # EF3: Truncation flag when ceiling hit
    if api_total > len(all_mentions):
        output["truncated"] = True
    from ..main import get_state
    emit(output, human=get_state().human)


@app.command()
@handle_errors
def sentiment(
    monitor_id: str = typer.Argument(..., help="Monitor UUID"),
    date_from: str = typer.Option(None, "--date-from", help="Start date (YYYY-MM-DD)"),
    date_to: str = typer.Option(None, "--date-to", help="End date (YYYY-MM-DD)"),
    granularity: str = typer.Option("1d", "--granularity", help="1h|6h|1d"),
) -> None:
    """Fetch sentiment time series."""
    cached = try_read_cache("xpoz", "sentiment", monitor_id)
    if cached is not None:
        typer.echo(json.dumps(cached))
        return
    config = _require_config()
    client = make_client(config)

    params: dict = {
        "window": "7d",
        "granularity": granularity,
        "date_from": date_from,
        "date_to": date_to,
    }
    result = api_request(client, "GET", f"/v1/monitors/{monitor_id}/sentiment", params=params)

    from ..main import get_state
    emit(result, human=get_state().human)


@app.command()
@handle_errors
def sov(
    monitor_id: str = typer.Argument(..., help="Monitor UUID"),
    window_days: int = typer.Option(7, "--window-days", help="Lookback window in days"),
) -> None:
    """Fetch share of voice (requires competitor_brands on monitor)."""
    cached = try_read_cache("xpoz", "sov", monitor_id)
    if cached is not None:
        typer.echo(json.dumps(cached))
        return
    config = _require_config()
    client = make_client(config)

    window_map = {7: "7d", 14: "14d", 30: "30d", 90: "90d"}
    window = window_map.get(window_days, "7d")
    params: dict = {"window": window}
    result = api_request(client, "GET", f"/v1/monitors/{monitor_id}/share-of-voice", params=params)

    from ..main import get_state
    emit(result, human=get_state().human)


def _deterministic_aggregates(mentions: list, api_total: int) -> dict:
    """Raw floor — source/language counts, total, fetched. No agent needed."""
    source_counts = Counter(m.get("source", "unknown") for m in mentions)
    lang_counts = Counter(m.get("language", "unknown") for m in mentions)
    return {
        "total": api_total,
        "fetched": len(mentions),
        "sources": dict(source_counts),
        "languages": dict(lang_counts.most_common(5)),
    }


def _sample_size_for_volume(fetched: int) -> int:
    if fetched <= _TIER_LOW_MAX:
        return _SAMPLE_SIZE_LOW
    if fetched <= _TIER_MED_MAX:
        return _SAMPLE_SIZE_MED
    return _SAMPLE_SIZE_HIGH


def _ensure_mention_ids(mentions: list[dict]) -> list[dict]:
    """Agent refers to mentions by id — synthesize stable ones if missing."""
    out: list[dict] = []
    for i, m in enumerate(mentions):
        mid = m.get("id") or m.get("mention_id") or f"m{i}"
        out.append({**m, "_mid": str(mid)})
    return out


def _cache_key(monitor_id: str, mention_ids: list[str]) -> str:
    payload = PROMPT_VERSION + "|" + monitor_id + "|" + "|".join(sorted(mention_ids))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _cache_get(key: str) -> dict | None:
    path = _CACHE_DIR / f"{key}.json"
    if not path.exists():
        return None
    try:
        age = time.time() - path.stat().st_mtime
        if age > _CACHE_TTL_SECONDS:
            return None
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _cache_put(key: str, data: dict) -> None:
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        (_CACHE_DIR / f"{key}.json").write_text(json.dumps(data), encoding="utf-8")
    except OSError as exc:
        logger.warning("monitor_summary cache write failed: %s", exc)


def _build_sonnet_prompt(monitor_id: str, mentions: list[dict], sample_size: int) -> str:
    """Ask Sonnet for relevance-ranked mentions + semantic themes + source mix.

    Agent decides relevance from query context; no engagement-naive ranking,
    no word-length>4 frequency gimmicks.
    """
    # Trim each mention to what the agent actually needs for relevance + theming.
    compact = []
    for m in mentions[:_MAX_MENTIONS_TO_AGENT]:
        compact.append({
            "mention_id": m["_mid"],
            "source": m.get("source", "unknown"),
            "language": m.get("language"),
            "author": m.get("author_handle"),
            "published_at": m.get("published_at"),
            "content": (m.get("content", "") or "")[:_CONTENT_SNIPPET_CHARS],
        })
    return (
        f"You are summarizing brand-monitoring mentions for monitor `{monitor_id}`. "
        f"Return a SINGLE JSON object — no prose, no markdown fences — with exactly these keys:\n\n"
        f"1. `top_mentions`: list of up to 20 objects "
        f"`{{\"mention_id\": str, \"relevance_rank\": int (1=most relevant), \"reason\": str}}`. "
        f"Rank by relevance to brand-health signal (pricing backlash, churn signals, product gaps, "
        f"competitive-pull, sentiment shifts, earned coverage). Ignore raw engagement unless it "
        f"reinforces a substantive signal.\n"
        f"2. `themes`: list of up to 8 objects `{{\"theme\": str, \"representative_quotes\": [str]}}`. "
        f"Themes are semantic clusters (e.g. 'pricing-tier pushback from SMB users'), not single "
        f"high-frequency words. Include 1-3 short verbatim quotes per theme.\n"
        f"3. `source_mix`: list of objects `{{\"source\": str, \"sample\": "
        f"[{{\"mention_id\": str, \"headline\": str}}]}}`. One entry per distinct source. "
        f"`sample` size MUST be exactly {sample_size} (or fewer if the source has fewer mentions). "
        f"`headline` is a ≤120-char synthesized summary of the mention.\n\n"
        f"Use ONLY `mention_id` values that appear in the input below. "
        f"Emit valid JSON with no trailing commas.\n\n"
        f"MENTIONS:\n{json.dumps(compact, ensure_ascii=False)}"
    )


async def _call_sonnet_summary(prompt: str) -> dict:
    # Local import so the CLI doesn't pay the evaluation-subpackage import cost
    # on non-summary code paths.
    from src.evaluation.judges.sonnet_agent import call_sonnet_json
    return await call_sonnet_json(prompt, operation="monitor_summary")


def _sonnet_portion(monitor_id: str, enriched: list[dict], fetched: int) -> dict | None:
    """Return validated Sonnet output, or None on any failure (caller falls back)."""
    if not enriched:
        # No mentions → no agent call, empty lists for new-shape fields.
        return {"top_mentions": [], "themes": [], "source_mix": []}

    mention_ids = [m["_mid"] for m in enriched]
    key = _cache_key(monitor_id, mention_ids)
    cached = _cache_get(key)
    if cached is not None:
        try:
            return SonnetSummaryPayload.model_validate(cached).model_dump()
        except ValidationError as exc:
            logger.warning("monitor_summary cache entry invalid, re-calling Sonnet: %s", exc)

    sample_size = _sample_size_for_volume(fetched)
    prompt = _build_sonnet_prompt(monitor_id, enriched, sample_size)

    try:
        raw = asyncio.run(_call_sonnet_summary(prompt))
    except Exception as exc:  # SonnetAgentError, timeout, CLI missing, etc.
        logger.warning("monitor_summary Sonnet call failed, falling back to aggregates: %s", exc)
        return None

    try:
        validated = SonnetSummaryPayload.model_validate(raw)
    except ValidationError as exc:
        logger.warning("monitor_summary Sonnet payload shape invalid, falling back: %s", exc)
        return None

    payload = validated.model_dump()
    _cache_put(key, payload)
    return payload


def _build_summary(mentions: list, api_total: int, monitor_id: str = "") -> dict:
    """Summary: deterministic aggregates (raw floor) + Sonnet-authored analysis.

    On subprocess failure or payload shape mismatch: fall back to deterministic
    aggregates only (with a WARNING already logged). Single purpose — no
    `--summary-intent` flag, no `--format=summary-raw` alias.
    """
    aggregates = _deterministic_aggregates(mentions, api_total)
    enriched = _ensure_mention_ids(mentions)
    sonnet = _sonnet_portion(monitor_id, enriched, len(mentions))
    if sonnet is None:
        return aggregates
    return {**aggregates, **sonnet}


@app.command()
@handle_errors
def baseline(
    monitor_id: str = typer.Argument(..., help="Monitor UUID"),
    window_days: int = typer.Option(7, "--window-days", help="Lookback window in days"),
    data_file: str = typer.Option(None, "--data-file", help="Path to JSON file with pre-computed session data (mentions, sentiment, sov, alerts)"),
) -> None:
    """Generate commodity baseline with statistics for a monitor."""
    config = _require_config()
    client = make_client(config)

    from datetime import date, timedelta

    period_end = date.today()
    period_start = period_end - timedelta(days=window_days)

    # If pre-computed data file provided, use it to avoid duplicate API calls
    pre_computed: dict = {}
    if data_file:
        import json
        from pathlib import Path
        data_path = Path(data_file)
        if data_path.exists():
            try:
                pre_computed = json.loads(data_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass

    # Fetch mentions (skip if pre-computed)
    mentions_result = pre_computed.get("mentions") or api_request(
        client, "GET", f"/v1/monitors/{monitor_id}/mentions",
        params={"limit": 50, "date_from": str(period_start), "date_to": str(period_end)},
    )

    # Fetch sentiment (skip if pre-computed)
    sentiment_result = pre_computed.get("sentiment") or api_request(
        client, "GET", f"/v1/monitors/{monitor_id}/sentiment",
        params={"window": f"{window_days}d"},
    )

    # Fetch SOV (skip if pre-computed, optional)
    sov_result = pre_computed.get("sov")
    if sov_result is None:
        try:
            sov_result = api_request(
                client, "GET", f"/v1/monitors/{monitor_id}/share-of-voice",
                params={"window": f"{window_days}d"},
            )
        except Exception:
            sov_result = None

    # Fetch alerts (skip if pre-computed)
    alerts_data = pre_computed.get("alerts")
    if alerts_data is None:
        try:
            alerts_result = api_request(
                client, "GET", f"/v1/monitors/{monitor_id}/alerts/history",
                params={"limit": 20},
            )
            alerts_data = alerts_result if isinstance(alerts_result, list) else alerts_result.get("events", [])
        except Exception:
            alerts_data = []

    from src.monitoring.intelligence.commodity_baseline import (
        InsufficientDataError,
        generate_commodity_baseline,
    )

    try:
        baseline_obj = generate_commodity_baseline(
            mentions_data=mentions_result,
            sentiment_data=sentiment_result,
            sov_data=sov_result,
            alerts_data=alerts_data,
            period_start=period_start,
            period_end=period_end,
        )
    except InsufficientDataError as exc:
        emit_error("insufficient_data", str(exc))

    from ..main import get_state
    emit({"baseline": baseline_obj.markdown}, human=get_state().human)


