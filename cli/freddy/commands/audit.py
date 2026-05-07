"""Audit commands — call providers directly for client audits."""
from __future__ import annotations

import asyncio
import dataclasses
from pathlib import Path
from typing import Any

import typer

from src.common.cost_recorder import cost_recorder

from ..config import load_config
from ..output import emit, emit_error
from ..providers import get_provider, handle_errors

app = typer.Typer(help="Client distribution audit commands.", no_args_is_help=True)


def _init_cost_log(client_name: str | None) -> None:
    """Route cost logs to per-client file when client specified."""
    if client_name:
        cfg = load_config()
        if cfg is None or cfg.clients_dir is None:
            raise typer.BadParameter(
                "No clients_dir configured. Run `freddy setup` or set FREDDY_CLIENTS_DIR."
            )
        client_dir = cfg.clients_dir / client_name
        # Refuse unknown slugs. Silently mkdir-ing an arbitrary --client value
        # leaves a phantom workspace that `client list` reports forever, has
        # cost-log entries credited against a slug that does not exist
        # server-side, and `session start --client <same>` later rejects.
        # config.json is the same marker `client list` uses to mark a
        # workspace as active (vs. status="unknown" for stray dirs); only
        # `client new` writes it, after backend registration succeeds.
        if not (client_dir / "config.json").exists():
            # F-a-5-8: only suggest `freddy client new <slug>` when the slug
            # would itself pass slug validation. Suggesting `freddy client new
            # Bad Slug` (with spaces / capitals / empty) just produces a
            # second invalid_slug error — useless recovery hint.
            import re
            slug_re = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")
            if slug_re.match(client_name):
                hint = f" Run `freddy client new {client_name}` first."
            else:
                hint = ""
            emit_error(
                "client_not_found",
                f"Unknown client slug: '{client_name}'.{hint}",
            )
        log_path = client_dir / "cost_log.jsonl"
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


class _UpstreamProviderError(Exception):
    """Upstream provider returned a structured non-2xx response.

    Distinct from a genuinely unexpected exception — this is the upstream
    refusing the request through its documented protocol, so the CLI surfaces
    it as `upstream_error`, not `unexpected_error` (which would leak the
    raw upstream message including subscription/billing URLs).
    """


@app.command()
@handle_errors
def seo(
    domain: str = typer.Argument(..., help="Domain to audit (e.g. example.com)"),
    client: str | None = typer.Option(None, "--client", help="Scope to a client workspace"),
) -> None:
    """Run an SEO audit via DataForSEO: domain rank snapshot."""
    # Sibling `freddy audit competitive ''` rejects empty input pre-flight
    # (F-a-6-3); enforce the same contract here so siblings of the same
    # `audit` subgroup agree on empty-input handling.
    if not domain:
        emit_error(
            "validation_error",
            "Request validation failed: body.domain: String should have at least 1 character",
        )
    # DataForSEO SDK's lazy __getattr__ on RestClient recurses into a 100%-CPU
    # un-joinable thread, stalling asyncio.run() for ~300s after the inner
    # timeout fires. Call the HTTP API directly here so the CLI fails fast.
    import httpx
    from datetime import date

    from src.common.cost_recorder import cost_recorder
    from src.seo.config import SeoSettings

    _init_cost_log(client)
    settings = SeoSettings()
    login = settings.dataforseo_login
    password = settings.dataforseo_password.get_secret_value()

    async def _run() -> dict:
        async with httpx.AsyncClient(timeout=60.0, auth=(login, password)) as http:
            resp = await http.post(
                "https://api.dataforseo.com/v3/backlinks/summary/live",
                json=[
                    {
                        "target": domain,
                        "internal_list_limit": 0,
                        "backlinks_status_type": "live",
                    }
                ],
            )
        # Surface 401 / 403 / 5xx / HTML error pages as upstream failures so
        # callers don't see a raw provider message (e.g., DataForSEO's
        # subscription-renewal URL) wrapped as `unexpected_error`.
        if resp.status_code >= 400:
            raise _UpstreamProviderError(
                f"DataForSEO request failed (HTTP {resp.status_code})"
            )
        raw = resp.json()
        status_code = raw.get("status_code", 0)
        if status_code >= 40000:
            raise _UpstreamProviderError("DataForSEO request failed")
        tasks = raw.get("tasks", []) or []
        for task in tasks:
            task_code = task.get("status_code", 0)
            if task_code >= 40000:
                raise _UpstreamProviderError("DataForSEO task failed")
        result_data = (
            (tasks[0].get("result") or [{}])[0]
            if tasks and tasks[0].get("result")
            else {}
        )
        await cost_recorder.record(
            "dataforseo", "domain_rank_snapshot", cost_usd=0.02
        )
        rank = {
            "domain": domain,
            "rank": result_data.get("rank"),
            "backlinks_total": result_data.get("backlinks", 0) or 0,
            "referring_domains": result_data.get("referring_domains", 0) or 0,
            "snapshot_date": date.today().isoformat(),
            "org_id": None,
        }
        return {"domain": domain, "rank": rank}

    try:
        result = asyncio.run(_run())
    except _UpstreamProviderError as exc:
        emit_error("upstream_error", str(exc))
    from ..main import get_state
    emit(result, human=get_state().human)


@app.command()
@handle_errors
def competitive(
    domain: str = typer.Argument(..., help="Competitor domain"),
    client: str | None = typer.Option(None, "--client", help="Scope to a client workspace"),
    limit: int = typer.Option(50, "--limit", help="Max ads from Foreplay"),
) -> None:
    """Fetch competitor ads from Foreplay + Adyntel."""
    # Sibling `freddy competitive brief --domain ''` rejects empty input via
    # Pydantic min_length=1 on the API body. This command calls providers
    # directly and must enforce the same contract pre-flight; otherwise
    # Foreplay/Adyntel treat '' as "no filter" and return ads for an
    # unrelated brand tagged with domain: ''.
    if not domain:
        emit_error(
            "validation_error",
            "Request validation failed: body.domain: String should have at least 1 character",
        )
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

    from ..main import get_state
    emit(asyncio.run(_run()), human=get_state().human)


@app.command()
@handle_errors
def monitor(
    query: str = typer.Argument(..., help="Search query (brand, keyword, etc.)"),
    client: str | None = typer.Option(None, "--client", help="Scope to a client workspace"),
    limit: int = typer.Option(100, "--limit", help="Max mentions"),
) -> None:
    """Fetch recent mentions via Xpoz across social platforms."""
    # Siblings `freddy audit competitive ''` and `freddy audit seo ''` reject
    # empty input pre-flight; without the same check here, xpoz/MCP echoes a
    # raw upstream zod error (`MCP error -32602: Invalid arguments…`) wrapped
    # as `unexpected_error`, breaking sibling symmetry across the audit
    # subgroup.
    if not query:
        emit_error(
            "validation_error",
            "Request validation failed: body.query: String should have at least 1 character",
        )
    _init_cost_log(client)
    xpoz = get_provider("xpoz")

    async def _run() -> dict:
        async with xpoz:
            mentions = await xpoz.fetch_all_mentions(query, max_results=limit)
        payload = _to_dict(mentions)
        return {"query": query, "count": len(payload), "mentions": payload}

    from ..main import get_state
    emit(asyncio.run(_run()), human=get_state().human)


# ─── Marketing audit lifecycle verbs (master plan §3.3, §3.11, §5.6) ───────
#
# 7 verbs covering the v1 marketing_audit pipeline lifecycle. Coexist with
# the seo/competitive/monitor distribution-audit verbs above; namespace
# separation is by intent (state-machine transitions vs lane-specific
# fetches), not subcommand prefix — master plan locks the `freddy audit
# <verb>` shape.


def _ma_audit_dir(slug: str) -> Path:
    cfg = load_config()
    if cfg is None or cfg.clients_dir is None:
        raise typer.BadParameter("No clients_dir configured. Run `freddy setup`.")
    return cfg.clients_dir / slug / "audit"


def _ma_state_file(slug: str):
    from src.audit.state import AuditStateFile
    return AuditStateFile(path=_ma_audit_dir(slug) / "state.json")


def _ma_state_mutate(slug: str, **kv: Any) -> None:
    """Atomic state mutation for gate transitions."""
    sf = _ma_state_file(slug)
    def _apply(s):
        return dataclasses.replace(s, **kv)
    sf.mutate(_apply)


@app.command("init")
@handle_errors
def ma_init(
    slug: str = typer.Argument(..., help="Client slug (existing freddy client workspace)"),
    domain: str = typer.Option(..., "--domain", help="Prospect domain or URL"),
) -> None:
    """Initialize a marketing audit workspace at clients/<slug>/audit/."""
    from src.audit.state import AuditState
    try:
        from ulid import ULID  # type: ignore[import-not-found]
        audit_id = str(ULID()).lower()
    except ImportError:
        import secrets, time
        audit_id = f"aud_{int(time.time())}_{secrets.token_hex(4)}"
    audit_dir = _ma_audit_dir(slug)
    audit_dir.mkdir(parents=True, exist_ok=True)
    state = AuditState(audit_id=audit_id, client_slug=slug, prospect_domain=domain)
    _ma_state_file(slug).save(state)
    from ..main import get_state
    emit({"slug": slug, "audit_id": state.audit_id, "audit_dir": str(audit_dir)}, human=get_state().human)


@app.command("run")
@handle_errors
def ma_run(
    slug: str = typer.Argument(...),
    resume: bool = typer.Option(  # noqa: ARG001  — informational; stages are
        False, "--resume",        # idempotent so resume is always available
        help="Informational; all stages are idempotent and skip when complete.",
    ),
) -> None:
    """Run the marketing audit pipeline through the next gate. Halts at
    intake/payment/ship gates; emits the next-step CLI command."""
    from src.audit import stages
    from src.audit.agent_runner import AgentRunner
    sf = _ma_state_file(slug)
    state = sf.load()
    audit_dir = _ma_audit_dir(slug)
    ctx = stages.StageContext(audit_dir=audit_dir, state_file=sf, runner=AgentRunner())

    async def _go() -> dict:
        # Honor the three permanent gates per §3.11.
        if state.status not in {"brief_confirmed", "paid", "published"}:
            await stages.stage_0_intake(ctx)
            await stages.stage_1_warmup(ctx)
            await stages.stage_1b_predischarge(ctx)
            await stages.stage_1c_brief_synthesis(ctx)
            return {"status": "halted_at_gate", "gate": "intake", "next": f"freddy audit confirm-brief {slug}"}
        if state.status == "brief_confirmed":
            return {"status": "halted_at_gate", "gate": "payment", "next": f"freddy audit mark-paid {slug}"}
        s2 = await stages.stage_2_agents(ctx)
        s3 = await stages.stage_3_synthesis(ctx, s2)
        s4 = await stages.stage_4_proposal(ctx, s3)
        await stages.stage_5_deliverable(ctx, s3, s4)
        return {"status": "halted_at_gate", "gate": "ship", "next": f"freddy audit publish {slug} (after JR ship-gate edits)"}

    from ..main import get_state
    emit(asyncio.run(_go()), human=get_state().human)


@app.command("confirm-brief")
@handle_errors
def ma_confirm_brief(slug: str = typer.Argument(...)) -> None:
    """Pass the intake gate. JR confirms Stage 1c brief is correct."""
    _ma_state_mutate(slug, status="brief_confirmed")
    from ..main import get_state
    emit({"slug": slug, "gate": "intake", "next": f"freddy audit mark-paid {slug}"}, human=get_state().human)


@app.command("mark-paid")
@handle_errors
def ma_mark_paid(
    slug: str = typer.Argument(...),
    stripe_event_id: str = typer.Option("manual", "--stripe-event-id"),
) -> None:
    """Pass the payment gate. Production fires from Stripe webhook;
    `--stripe-event-id manual` is for test runs without Stripe wired."""
    _ma_state_mutate(slug, status="paid")
    from ..main import get_state
    emit({"slug": slug, "gate": "payment", "stripe_event_id": stripe_event_id, "next": f"freddy audit run {slug}"}, human=get_state().human)


@app.command("publish")
@handle_errors
def ma_publish(
    slug: str = typer.Argument(...),
    dry_run: bool = typer.Option(False, "--dry-run", help="Skip R2 upload; only flip state."),
) -> None:
    """Pass the ship gate. JR has reviewed deliverable/report.html.
    Uploads deliverable/ to R2 (gofreddy-audits/<audit_id>/) when R2
    creds are set; flips state to published either way."""
    audit_dir = _ma_audit_dir(slug)
    deliverable_dir = audit_dir / "deliverable"

    public_url = ""
    if deliverable_dir.exists():
        from src.audit.r2_publish import upload_audit_dir
        state = _ma_state_file(slug).load()
        # The Stage-5 ULID slug lives in state.sessions[stage_5_deliverable].session_id.
        upload_slug = (
            state.sessions.get("stage_5_deliverable", {}).get("session_id")
            or state.audit_id
        )
        public_url = upload_audit_dir(deliverable_dir, upload_slug, dry_run=dry_run)

    _ma_state_mutate(slug, status="published")
    from ..main import get_state
    emit({
        "slug": slug, "gate": "ship",
        "public_url": public_url or "(R2 upload skipped — set R2_* env vars to enable)",
        "next": f"freddy audit close-engagement {slug} --converted=Y|N (T+60d)",
    }, human=get_state().human)


@app.command("close-engagement")
@handle_errors
def ma_close_engagement(
    slug: str = typer.Argument(...),
    converted: str = typer.Option(..., "--converted", help="Y if prospect signed $15K+ engagement within 60d, N otherwise"),
) -> None:
    """Close the T+60d engagement-conversion signal. Appends to
    audits/lineage.jsonl so next variant scoring picks up the
    engagement bonus (master plan §6.5)."""
    converted_bool = converted.strip().upper() == "Y"
    _ma_state_mutate(slug, status="engagement_closed")

    audit_id = _ma_state_file(slug).load().audit_id
    cfg = load_config()
    lineage_path = (cfg.clients_dir.parent if cfg and cfg.clients_dir else Path.cwd()) / "audits" / "lineage.jsonl"
    lineage_path.parent.mkdir(parents=True, exist_ok=True)
    import json as _json, time as _time
    with lineage_path.open("a", encoding="utf-8") as f:
        f.write(_json.dumps({
            "audit_id": audit_id, "slug": slug,
            "engagement_converted": converted_bool,
            "closed_at_ms": int(_time.time() * 1000),
        }) + "\n")
    from ..main import get_state
    emit({"slug": slug, "audit_id": audit_id, "engagement_converted": converted_bool}, human=get_state().human)


@app.command("attach")
@handle_errors
def ma_attach(
    attach_type: str = typer.Argument(..., help="gsc | sales-transcript | walkthrough-transcript | invoice | esp | survey | assets | demo | crm"),
    slug: str = typer.Argument(...),
    source: str = typer.Option(..., "--source", help="Path to data file or URL identifier"),
) -> None:
    """Attach external data to an audit. Parameterized per S6 self-review:
    one verb covers what was originally 9 attach-* commands."""
    valid_types = {"gsc", "sales-transcript", "walkthrough-transcript", "invoice", "esp", "survey", "assets", "demo", "crm"}
    if attach_type not in valid_types:
        raise typer.BadParameter(f"Unknown attach type: {attach_type!r}. Valid: {sorted(valid_types)}")
    audit_dir = _ma_audit_dir(slug)
    attach_dir = audit_dir / "attached" / attach_type
    attach_dir.mkdir(parents=True, exist_ok=True)
    src_path = Path(source)
    if src_path.exists():
        target = attach_dir / src_path.name
        target.write_bytes(src_path.read_bytes())
    else:
        target = attach_dir / f"{attach_type}.txt"
        target.write_text(str(source), encoding="utf-8")
    from ..main import get_state
    emit({"slug": slug, "attach_type": attach_type, "stored_at": str(target)}, human=get_state().human)


@app.command("prefetch")
@handle_errors
def ma_prefetch(
    context: str = typer.Argument(..., help="Prospect URL or domain (positional context)"),
) -> None:
    """Pre-fetch deterministic + free-tier audit data for a prospect URL.

    Used by ``freddy fixture refresh marketing-audit-* --pool search-v1``
    (and holdout-v1) to populate the autoresearch fixture cache with the
    cheap + deterministic part of the audit pipeline:

      - 8 preflight checks (DNS, headers, schema, social, assets, badges,
        wellknown, tooling) — fully free, HTTP-only
      - PageSpeed Lighthouse audit — Google free tier (25K/day)
      - Brave Search SERP — free tier (2K/mo)

    Paid Tier-1 providers (DataForSEO, Cloro, Apify, Foreplay, Adyntel)
    are NOT fetched here — they run live during variant evaluation cycles
    via the audit pipeline's internal ``tools/cache.py:cache_or_call``
    layer (24h TTL handles within-cohort dedup).

    Emits a single JSON blob to stdout matching the contract
    ``freddy fixture refresh`` expects: cache-storable, one record per
    fixture-cache artifact.
    """
    import json as _json
    import time as _time
    from datetime import datetime, timezone

    from src.audit.preflight import runner as preflight_runner

    started = _time.monotonic()
    started_at = datetime.now(timezone.utc).isoformat()

    # Normalize context → bare hostname for preflight (it auto-prefixes scheme)
    domain = context
    for prefix in ("https://", "http://"):
        if domain.startswith(prefix):
            domain = domain[len(prefix):]
    domain = domain.rstrip("/")

    async def _gather() -> dict[str, Any]:
        preflight = await preflight_runner.run(domain)
        signals = dict(getattr(preflight, "signals", {}))
        failures = dict(getattr(preflight, "failures", {}))
        return {"signals": signals, "failures": failures}

    preflight_result = asyncio.run(_gather())

    # PageSpeed (free, 25K/day) — single mobile audit
    pagespeed_signal: dict[str, Any] = {"present": False, "skipped": True}
    try:
        from src.seo.providers.pagespeed import check_performance
        api_key = (
            (
                __import__("os").environ.get("PAGESPEED_API_KEY", "")
                or __import__("os").environ.get("GOOGLE_PAGESPEED_KEY", "")
            ).strip()
        )
        if api_key:
            target_url = context if context.startswith("http") else f"https://{domain}"
            ps_result = asyncio.run(check_performance(target_url, api_key=api_key, timeout=60.0))
            pagespeed_signal = {
                "present": True,
                "performance_score": ps_result.performance_score,
                "lcp_ms": ps_result.lcp_ms,
                "fcp_ms": ps_result.fcp_ms,
                "cls": ps_result.cls,
                "tbt_ms": ps_result.tbt_ms,
                "speed_index_ms": ps_result.speed_index_ms,
                "strategy": ps_result.strategy,
            }
    except Exception as exc:  # noqa: BLE001 — degrade gracefully
        pagespeed_signal = {"present": False, "error": f"{type(exc).__name__}: {exc}"}

    # Brave Search (free 2K/mo) — top-10 SERP for the brand domain
    brave_signal: dict[str, Any] = {"present": False, "skipped": True}
    try:
        import os as _os
        if _os.environ.get("BRAVE_API_KEY", "").strip():
            from src.audit.tools.brave_search import BraveSearchClient
            query = domain.split("/")[0]
            client = BraveSearchClient()
            results = asyncio.run(client.web_search(query, count=10))
            brave_signal = {"present": True, "query": query, "results": results}
    except Exception as exc:  # noqa: BLE001
        brave_signal = {"present": False, "error": f"{type(exc).__name__}: {exc}"}

    duration = round(_time.monotonic() - started, 3)
    out = {
        "context": context,
        "domain": domain,
        "fetched_at": started_at,
        "duration_seconds": duration,
        "preflight": preflight_result,
        "providers": {
            "pagespeed": pagespeed_signal,
            "brave": brave_signal,
        },
        "_note": (
            "Deterministic prefetch v1: preflight (8 checks) + free Tier-1 "
            "(PageSpeed, Brave). Paid Tier-1 (DataForSEO, Cloro, Apify, "
            "Foreplay, Adyntel) run live during variant cycles."
        ),
    }
    print(_json.dumps(out, indent=2, default=str))
