"""Monitor commands — mentions, sentiment, share of voice, baseline, topics."""

from collections import Counter

import typer

from ..api import api_request, handle_errors, make_client
from ..config import load_config
from ..output import emit, emit_error

app = typer.Typer(help="Brand monitoring data commands.", no_args_is_help=True)


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
    config = _require_config()
    client = make_client(config)

    # Mentions endpoint returns empty on nonexistent monitors; probe the
    # detail endpoint so a typo'd UUID surfaces monitor_not_found, matching
    # sentiment/sov/trends/digest/query-monitor.
    api_request(client, "GET", f"/v1/monitors/{monitor_id}")

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

    # G2: Summary format — aggregate stats + top-20 + theme grouping + recency sampling
    if format == "summary":
        output = _build_summary(all_mentions, api_total)
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
    config = _require_config()
    client = make_client(config)

    window_map = {7: "7d", 14: "14d", 30: "30d", 90: "90d"}
    window = window_map.get(window_days, "7d")
    params: dict = {"window": window}
    result = api_request(client, "GET", f"/v1/monitors/{monitor_id}/share-of-voice", params=params)

    from ..main import get_state
    emit(result, human=get_state().human)


def _build_summary(mentions: list, api_total: int) -> dict:
    """Build summary format: stats + top-20 by engagement + themes + recency."""
    # Aggregate stats
    source_counts = Counter(m.get("source", "unknown") for m in mentions)
    lang_counts = Counter(m.get("language", "unknown") for m in mentions)

    def _eng(m: dict) -> int:
        total = m.get("engagement_total")
        if total is not None:
            return int(total)
        return (m.get("engagement_likes", 0) or 0) + (m.get("engagement_shares", 0) or 0) + (m.get("engagement_comments", 0) or 0)

    # Top 20 by engagement
    top_20 = sorted(mentions, key=_eng, reverse=True)[:20]

    # Frequency-grouped themes (word frequency from content)
    word_freq: dict[str, int] = {}
    for m in mentions:
        content = m.get("content", "")
        for word in content.lower().split():
            if len(word) > 4:
                word_freq[word] = word_freq.get(word, 0) + 1
    themes = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]

    # 3 most recent per source
    recent_by_source: dict[str, list] = {}
    for m in sorted(mentions, key=lambda x: x.get("published_at", "") or "", reverse=True):
        src = m.get("source", "unknown")
        if src not in recent_by_source:
            recent_by_source[src] = []
        if len(recent_by_source[src]) < 3:
            recent_by_source[src].append({
                "content": (m.get("content", ""))[:200],
                "author": m.get("author_handle"),
                "engagement": _eng(m),
                "published_at": m.get("published_at"),
            })

    return {
        "total": api_total,
        "fetched": len(mentions),
        "sources": dict(source_counts),
        "languages": dict(lang_counts.most_common(5)),
        "top_mentions": [
            {"source": m.get("source"), "content": (m.get("content", ""))[:200],
             "author": m.get("author_handle"), "engagement": _eng(m)}
            for m in top_20
        ],
        "themes": [{"word": w, "count": c} for w, c in themes],
        "recent_by_source": recent_by_source,
    }


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

    from src.monitoring.intelligence.commodity_baseline import generate_commodity_baseline

    baseline_obj = generate_commodity_baseline(
        mentions_data=mentions_result,
        sentiment_data=sentiment_result,
        sov_data=sov_result,
        alerts_data=alerts_data,
        period_start=period_start,
        period_end=period_end,
    )

    from ..main import get_state
    emit({"baseline": baseline_obj.markdown}, human=get_state().human)


