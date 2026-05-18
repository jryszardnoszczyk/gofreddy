"""Portal routes — HTML shell + JSON summary.

Design note: a browser page-load cannot send Authorization headers, so the
`/portal/<slug>` route serves an unauthenticated HTML shell. The shell reads
the Supabase session client-side (localStorage) and fetches the authed
`/v1/portal/<slug>/summary` JSON endpoint to render data. Unauth → /login.
"""
from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from autoresearch.events import (
    EventLogCorruption,
    client_events_path,
    read_events,
    tail_events_sse,
)

from ..dependencies import (
    AuthPrincipal,
    get_auth_principal,
)
from ..membership import resolve_client_access
from ..rate_limit import limiter

router = APIRouter()

_TEMPLATES = Jinja2Templates(
    directory=str(Path(__file__).resolve().parents[3] / "portal" / "templates")
)


@router.get("/portal/{slug}", response_class=HTMLResponse)
async def portal_shell(request: Request, slug: str) -> HTMLResponse:
    """HTML shell — no auth on the page itself; JS handles session + data fetch."""
    settings = request.app.state.supabase_settings
    return _TEMPLATES.TemplateResponse(
        request=request,
        name="portal_phase2.html",
        context={
            "slug": slug,
            "supabase_url": settings.supabase_url,
            "supabase_anon_key": settings.supabase_anon_key,
        },
    )


# ---------------------------------------------------------------------------
# P5 — Phase 2 portal /summary helpers
#
# Pure functions taking pre-parsed event lists so they're unit-testable
# without booting the FastAPI app. The route below does the I/O (reads
# events.jsonl, scans archive dir) and threads the results through these.
# ---------------------------------------------------------------------------


def _parse_event_timestamp(raw: Any) -> _dt.datetime | None:
    """Parse the canonical timestamp shape (`2026-05-13T...Z` or `+00:00`).

    Returns None on missing/malformed input so callers can skip silently
    instead of crashing the whole summary on one bad event.
    """
    if not isinstance(raw, str) or not raw:
        return None
    try:
        return _dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _cost_rollup(
    events: list[dict[str, Any]], *, now: _dt.datetime
) -> dict[str, float]:
    """Sum cost_usd across kind='cost' events bucketed today/week/month UTC.

    Week starts Monday (datetime.weekday()=0). Month starts on day 1. All
    cutoffs are based on `now`'s UTC date, so a request near midnight UTC
    flips the "today" bucket exactly once. Non-numeric cost_usd values are
    skipped without erroring the rollup.
    """
    if now.tzinfo is None:
        now = now.replace(tzinfo=_dt.timezone.utc)
    today_start = _dt.datetime.combine(
        now.date(), _dt.time.min, tzinfo=_dt.timezone.utc
    )
    week_start = today_start - _dt.timedelta(days=now.weekday())
    month_start = today_start.replace(day=1)

    today = week = month = 0.0
    for ev in events:
        if ev.get("kind") != "cost":
            continue
        cost = ev.get("cost_usd")
        if not isinstance(cost, (int, float)):
            continue
        ts = _parse_event_timestamp(ev.get("timestamp"))
        if ts is None:
            continue
        if ts >= month_start:
            month += float(cost)
        if ts >= week_start:
            week += float(cost)
        if ts >= today_start:
            today += float(cost)
    return {
        "today_usd": round(today, 6),
        "week_usd": round(week, 6),
        "month_usd": round(month, 6),
    }


def _lane_summary(events: list[dict[str, Any]]) -> list[str]:
    """Distinct sorted list of `lane` values that appear in the events stream."""
    return sorted(
        {
            ev["lane"]
            for ev in events
            if isinstance(ev.get("lane"), str) and ev["lane"]
        }
    )


def _audit_page(
    events: list[dict[str, Any]],
    *,
    kind: str | None = None,
    actor: str | None = None,
    lane: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    """Filter + paginate audit events. Newest first within page.

    Filter chips on the frontend produce these query params; matching is
    exact-string. Page numbering is 1-based; out-of-range pages return an
    empty `events` list with the correct `total` so the UI can clamp.
    """
    filtered: list[dict[str, Any]] = []
    for ev in events:
        if kind is not None and ev.get("kind") != kind:
            continue
        if actor is not None and ev.get("actor") != actor:
            continue
        if lane is not None and ev.get("lane") != lane:
            continue
        filtered.append(ev)
    filtered.reverse()  # newest first
    total = len(filtered)
    page = max(page, 1)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "events": filtered[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def _read_events_for_summary(path: Path) -> list[dict[str, Any]]:
    """Read all events for the per-client log; return [] on missing/corrupt.

    A corrupted line elsewhere in the history must not 500 the summary
    endpoint — the portal is a read-only observer and should degrade
    gracefully. Returning [] is the right v1 behavior; an operator fix on
    the underlying file restores the data on next request.
    """
    if not path.exists() and not (
        path.parent.exists() and any(path.parent.glob(path.name + ".*"))
    ):
        return []
    try:
        return list(read_events(path=path))
    except EventLogCorruption:
        return []


def _list_recent_reports(
    slug: str,
    role: str,
    *,
    archive_root: Path | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Scan archive for fixture reports the user can access.

    Auth mirrors portal_report_view exactly:
      * tenant lanes (marketing_audit): fixture must equal slug
      * operator lanes: role must be 'admin'

    Results are sorted by report mtime desc and capped at `limit`. Variant
    + lane + fixture names must pass the existing allowlist regexes so a
    poisoned dir name can't surface a path that won't pass the /reports
    route's own validation.
    """
    root = archive_root if archive_root is not None else _ARCHIVE_ROOT
    if not root.exists():
        return []
    candidates: list[dict[str, Any]] = []
    for variant_dir in root.iterdir():
        if not variant_dir.is_dir() or not _VARIANT_RE.fullmatch(variant_dir.name):
            continue
        sessions = variant_dir / "sessions"
        if not sessions.is_dir():
            continue
        for lane_dir in sessions.iterdir():
            lane = lane_dir.name
            if lane not in _LANES or not lane_dir.is_dir():
                continue
            tenant_lane = lane in _TENANT_LANES
            if not tenant_lane and role != "admin":
                continue
            for fixture_dir in lane_dir.iterdir():
                fixture = fixture_dir.name
                if not fixture_dir.is_dir():
                    continue
                if not all(ch.isalnum() or ch in "-_" for ch in fixture):
                    continue
                if tenant_lane and fixture != slug:
                    continue
                report = fixture_dir / "report.html"
                if not report.is_file():
                    continue
                candidates.append(
                    {
                        "lane": lane,
                        "variant": variant_dir.name,
                        "fixture": fixture,
                        "url": (
                            f"/v1/portal/{slug}/reports/"
                            f"{lane}/{variant_dir.name}/{fixture}"
                        ),
                        "rendered_at": report.stat().st_mtime,
                    }
                )
    candidates.sort(key=lambda r: r["rendered_at"], reverse=True)
    return candidates[:limit]


@router.get("/v1/portal/{slug}/summary")
@limiter.limit("60/minute")
async def portal_summary(
    request: Request,
    slug: str,
    principal: Annotated[AuthPrincipal, Depends(get_auth_principal)],
    audit_kind: Annotated[str | None, Query()] = None,
    audit_actor: Annotated[str | None, Query()] = None,
    audit_lane: Annotated[str | None, Query()] = None,
    audit_page: Annotated[int, Query(ge=1)] = 1,
) -> dict:
    """Authed JSON summary for a client's portal — Phase 2.

    Returns the data the portal page renders:
      * client identity (slug, role, email)
      * cost rollup (today / week / month USD)
      * lane summary (which lanes have events for this client)
      * recent reports list (top 10 by mtime)
      * paginated audit trail with `?audit_kind=` / `?audit_actor=` /
        `?audit_lane=` filter params

    Reads the per-client wide log; per-run subdir logs are not merged in
    v1. All event-derived data is computed in pure helpers above for
    unit-test friendliness; this function is the I/O + auth shell.
    """
    if not _slug_valid(slug):
        raise HTTPException(
            status_code=400, detail={"code": "invalid_slug"}
        )
    role = await resolve_client_access(
        request.app.state.db_pool, principal.user_id, slug
    )
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "no_membership", "message": f"No access to client '{slug}'"},
        )
    email = principal.claims.get("email") if principal.claims else None

    events_path = client_events_path(slug)
    events = _read_events_for_summary(events_path)
    now_utc = _dt.datetime.now(_dt.timezone.utc)

    return {
        "slug": slug,
        "role": role,
        "email": email,
        "phase": 2,
        "cost": _cost_rollup(events, now=now_utc),
        "lanes": _lane_summary(events),
        "recent_reports": _list_recent_reports(slug, role),
        "audit": _audit_page(
            events,
            kind=audit_kind,
            actor=audit_actor,
            lane=audit_lane,
            page=audit_page,
        ),
    }


# ---------------------------------------------------------------------------
# Spec D2: per-fixture report viewer (membership-gated)
# Path: /v1/portal/{slug}/reports/{lane}/{variant}/{fixture}
# Returns the rendered HTML report from
#   autoresearch/archive/<variant>/sessions/<lane>/<fixture>/report.html
#
# Authorization model (post-2026-05-08 review):
#  - marketing_audit fixtures ARE customer slugs — fixture MUST equal {slug}.
#    Member role on {slug} grants access to that one fixture. Cross-tenant
#    fixture reads (slug=acme, fixture=initech) are rejected with 404 to
#    avoid an enumeration oracle.
#  - geo / competitive / monitoring / storyboard "fixtures" are internal
#    autoresearch evolution-test fixtures (mayoclinic, epic, Lululemon,
#    Gossip.Goblin) — operator-only data. Restricted to admin role.
#  - All path components pass through resolve()+is_relative_to() guards to
#    block symlink + traversal escapes.
# ---------------------------------------------------------------------------

_ARCHIVE_ROOT = Path(__file__).resolve().parents[3] / "autoresearch" / "archive"
_ARCHIVE_ROOT_REAL = _ARCHIVE_ROOT.resolve()

_LANES = {
    "geo", "competitive", "monitoring", "storyboard",
    "marketing_audit", "x_engine", "linkedin_engine",
}
_OPERATOR_ONLY_LANES = {
    "geo", "competitive", "monitoring", "storyboard",
    "x_engine", "linkedin_engine",
}
_TENANT_LANES = {"marketing_audit"}

# Variant directory names: `v` + digits + optional `-suffix` (lowercase
# alphanumeric, e.g. `v007-curated`). The hyphenated form is in production
# use for x_engine + linkedin_engine.
_VARIANT_RE = re.compile(r"^v\d+(-[a-z0-9]+)?$")



def _safe_archive_path(*parts: str) -> Path | None:
    """Resolve a path under _ARCHIVE_ROOT; return None on traversal/symlink escape.

    Defense in depth on top of the per-component allowlist regexes — even if
    one component slips a ``..`` past validation, the resolve() +
    is_relative_to() check catches the escape. Also rejects when any segment
    along the path is a symlink, so an attacker who plants
    ``sessions/<lane>/<client>/report.html → /etc/passwd`` cannot have the
    portal serve it (resolve() would traverse the symlink and the relative_to
    check would catch it as well — belt and braces).
    """
    candidate = _ARCHIVE_ROOT.joinpath(*parts)
    # Reject if any segment from the archive root down is a symlink. Using
    # lstat per-segment (vs resolve+compare) gives a clearer error model.
    cursor = _ARCHIVE_ROOT
    for segment in parts:
        cursor = cursor / segment
        if cursor.is_symlink():
            return None
    try:
        real = candidate.resolve()
    except (OSError, RuntimeError):
        return None
    try:
        real.relative_to(_ARCHIVE_ROOT_REAL)
    except ValueError:
        return None
    return real


@router.get("/v1/portal/{slug}/reports/{lane}/{variant}/{fixture}",
            response_class=HTMLResponse)
@limiter.limit("60/minute")
async def portal_report_view(
    request: Request,
    slug: str,
    lane: str,
    variant: str,
    fixture: str,
    principal: Annotated[AuthPrincipal, Depends(get_auth_principal)],
) -> HTMLResponse:
    """Authed view of a rendered fixture report (HTML).

    Per-lane authorization (see module docstring above):
      marketing_audit → member role on {slug} AND fixture == slug
      operator lanes  → admin role on {slug}
    """
    role = await resolve_client_access(
        request.app.state.db_pool, principal.user_id, slug
    )
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "no_membership", "message": f"No access to client '{slug}'"},
        )

    # Defense-in-depth: validate path components against simple allowlist
    # before doing the resolve() check below.
    if lane not in _LANES:
        raise HTTPException(status_code=400, detail={"code": "invalid_lane"})
    if not _VARIANT_RE.fullmatch(variant):
        raise HTTPException(status_code=400, detail={"code": "invalid_variant"})
    # fixture slug constrained to alphanumerics + - _ (no '.' to keep this
    # tighter than 'invalid_fixture' allowed before; '.' would let attackers
    # play games with extensions and dotted dirs).
    if not fixture or not all(ch.isalnum() or ch in "-_" for ch in fixture):
        raise HTTPException(status_code=400, detail={"code": "invalid_fixture"})
    if not slug or not all(ch.isalnum() or ch in "-_" for ch in slug):
        raise HTTPException(status_code=400, detail={"code": "invalid_slug"})

    # Lane-specific authorization (the cross-tenant fix).
    if lane in _TENANT_LANES:
        if fixture != slug:
            # Return 404 (not 403) to avoid leaking the existence of other
            # tenants' fixtures.
            raise HTTPException(
                status_code=404,
                detail={"code": "report_not_found"},
            )
    else:  # operator lanes
        if role != "admin":
            raise HTTPException(
                status_code=403,
                detail={"code": "operator_only",
                        "message": f"Lane '{lane}' is operator-only — admin role required."},
            )

    report_path = _safe_archive_path(variant, "sessions", lane, fixture, "report.html")
    if report_path is None or not report_path.is_file():
        raise HTTPException(
            status_code=404,
            detail={"code": "report_not_found"},
        )

    return HTMLResponse(content=report_path.read_text(encoding="utf-8"))


async def _authorise_report_access(
    request: Request,
    slug: str,
    lane: str,
    variant: str,
    fixture: str,
    principal: AuthPrincipal,
) -> None:
    """Shared auth + path-component validation for the bundle and per-file
    routes. Mirrors portal_report_view's checks but raises HTTPException
    inline instead of returning HTMLResponse. Centralises the policy so a
    future tightening lands once.
    """
    role = await resolve_client_access(
        request.app.state.db_pool, principal.user_id, slug
    )
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "no_membership", "message": f"No access to client '{slug}'"},
        )
    if lane not in _LANES:
        raise HTTPException(status_code=400, detail={"code": "invalid_lane"})
    if not _VARIANT_RE.fullmatch(variant):
        raise HTTPException(status_code=400, detail={"code": "invalid_variant"})
    if not fixture or not all(ch.isalnum() or ch in "-_" for ch in fixture):
        raise HTTPException(status_code=400, detail={"code": "invalid_fixture"})
    if not slug or not all(ch.isalnum() or ch in "-_" for ch in slug):
        raise HTTPException(status_code=400, detail={"code": "invalid_slug"})
    if lane in _TENANT_LANES:
        if fixture != slug:
            raise HTTPException(status_code=404, detail={"code": "report_not_found"})
    else:
        if role != "admin":
            raise HTTPException(
                status_code=403,
                detail={"code": "operator_only",
                        "message": f"Lane '{lane}' is operator-only — admin role required."},
            )


@router.get(
    "/v1/portal/{slug}/reports/{lane}/{variant}/{fixture}/bundle.tar.gz",
)
@limiter.limit("30/minute")
async def portal_report_bundle(
    request: Request,
    slug: str,
    lane: str,
    variant: str,
    fixture: str,
    principal: Annotated[AuthPrincipal, Depends(get_auth_principal)],
) -> FileResponse:
    """Authed download of bundle.tar.gz for a fixture's session.

    Same auth model as portal_report_view: tenant lanes require slug ==
    fixture, operator lanes require admin. The bundle is generated by
    render_report.py at render time; if it doesn't exist on disk we return
    404 (and not "regenerate on demand" — that would let an attacker
    trigger render storms).
    """
    await _authorise_report_access(request, slug, lane, variant, fixture, principal)

    bundle_path = _safe_archive_path(
        variant, "sessions", lane, fixture, "bundle.tar.gz"
    )
    if bundle_path is None or not bundle_path.is_file():
        raise HTTPException(status_code=404, detail={"code": "bundle_not_found"})

    return FileResponse(
        path=str(bundle_path),
        media_type="application/gzip",
        filename=f"{lane}-{variant}-{fixture}-bundle.tar.gz",
    )


# ---------------------------------------------------------------------------
# α6: Cross-lane meta-pattern viewer (membership-gated)
# Path: /v1/portal/{slug}/meta-patterns
# Surfaces archive/meta_patterns.json (refreshed post-evolve by α5).
# Renders top-N clusters of agent reasoning that recur across lanes/fixtures.
# ---------------------------------------------------------------------------


def _safe_int(value: object, default: int = 0) -> int:
    """Coerce attacker-influenced cluster fields to int; never raise.

    Cluster JSON is produced by detect_meta_patterns walking agent-authored
    transcripts. A poisoned cluster with ``occurrences: "many"``, a literal
    ``Infinity`` (json.loads parses non-strict by default), or ``NaN`` would
    crash the route with an uncaught ValueError / OverflowError → 500
    (admin-only DoS). Treat all non-coercible values as ``default``.

    Caught by 2026-05-08 re-review (adv-new-1) — the prior version missed
    OverflowError so ``int(float('inf'))`` still escaped.
    """
    try:
        # Coerce via float first to handle NaN / Infinity literals, then
        # to int. NaN raises ValueError; Infinity raises OverflowError.
        return int(float(value))  # type: ignore[arg-type]
    except (TypeError, ValueError, OverflowError):
        return default


@router.get("/v1/portal/{slug}/meta-patterns", response_class=HTMLResponse)
@limiter.limit("30/minute")
async def portal_meta_patterns(
    request: Request,
    slug: str,
    principal: Annotated[AuthPrincipal, Depends(get_auth_principal)],
) -> HTMLResponse:
    """Operator-only view of cross-lane meta-patterns.

    archive/meta_patterns.json aggregates reasoning beats across EVERY tenant
    (all lanes, all fixtures, all variants). It does not have per-tenant
    attribution that would let us filter to one customer. Therefore this
    route is gated on admin role — non-admin members of a client are NOT
    allowed to read it. Per 2026-05-08 review (cross-tenant leak fix).
    """
    import json
    from html import escape

    role = await resolve_client_access(
        request.app.state.db_pool, principal.user_id, slug
    )
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "no_membership", "message": f"No access to client '{slug}'"},
        )
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "operator_only",
                    "message": "Cross-lane meta-patterns aggregate data across "
                               "every tenant; admin role required."},
        )

    meta_path = _ARCHIVE_ROOT / "meta_patterns.json"
    if not meta_path.exists():
        raise HTTPException(
            status_code=404,
            detail={"code": "meta_patterns_not_generated",
                    "message": "Meta-patterns are produced after evolve cycles. "
                               "Run an evolve generation first."},
        )

    try:
        from src.shared.reporting.report_base import build_html_document
    except ImportError:
        raise HTTPException(status_code=500, detail={"code": "reporting_unavailable"})

    # Tolerate corrupted / partial-written meta_patterns.json — render an
    # empty body instead of 500. detect_meta_patterns now writes via .tmp +
    # os.replace so torn writes are rare, but a stale truncated file from
    # before this PR shouldn't kill the route.
    try:
        payload = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        payload = {}

    patterns = payload.get("meta_patterns", []) if isinstance(payload, dict) else []
    stats = payload.get("stats", {}) if isinstance(payload, dict) else {}

    if not patterns:
        body = (
            '<h2>Cross-Lane Meta-Patterns</h2>'
            '<p>No patterns surfaced yet. Run more evolve cycles to gather data.</p>'
        )
    else:
        rows = []
        for p in patterns[:50]:
            if not isinstance(p, dict):
                continue
            rep_text = escape(str(p.get("representative_text", ""))[:240])
            kind = escape(str(p.get("kind", "")))
            occurrences = _safe_int(p.get("occurrences"))
            distinct_lanes = _safe_int(p.get("distinct_lanes"))
            distinct_fixtures = _safe_int(p.get("distinct_fixtures"))
            lane_list_value = p.get("lanes", [])
            if not isinstance(lane_list_value, list):
                lane_list_value = []
            lanes = escape(", ".join(str(x) for x in lane_list_value))
            rows.append(
                f"<tr>"
                f"<td><code>{kind}</code></td>"
                f"<td>{occurrences}</td>"
                f"<td>{distinct_lanes}</td>"
                f"<td>{distinct_fixtures}</td>"
                f"<td>{lanes}</td>"
                f"<td style='font-size:13px'>{rep_text}</td>"
                f"</tr>"
            )
        body = (
            '<h2>Cross-Lane Meta-Patterns</h2>'
            f'<p>{len(patterns)} clusters · {_safe_int(stats.get("sessions"))} sessions · '
            f'{_safe_int(stats.get("beats"))} reasoning beats analysed.</p>'
            '<table class="rprt-key-table"><thead><tr>'
            '<th>Kind</th><th>Occurrences</th><th>Lanes</th>'
            '<th>Fixtures</th><th>Lane List</th><th>Representative Text</th>'
            '</tr></thead><tbody>' + "\n".join(rows) + "</tbody></table>"
        )

    title = f"FREDDY · Meta-Patterns · {slug}"
    html = build_html_document(title=title, sections=[("body", body)])
    html = html.replace("<body>", '<body><div class="rprt-page">').replace(
        "</body>", "</div></body>"
    )
    return HTMLResponse(content=html)


# ---------------------------------------------------------------------------
# P3 — Operator-side event ingestion endpoint
# Path: POST /v1/portal/_ingest
#
# Accepts canonical event payloads from operator-side instrumentation
# (Claude Code PostToolUse hooks, Codex wrappers, ad-hoc local scripts) and
# routes them into the canonical events log at the per-client path resolved
# by client_events_path(client_id).
#
# Auth: shared-secret bearer token from GOFREDDY_INGEST_TOKEN env var. This is
# operator-only; it does NOT accept Supabase JWTs. NEVER expose this endpoint
# to public network — production deployment must restrict to localhost or
# internal network via reverse-proxy ACL.
#
# Body schema (subset of canonical event schema; see autoresearch.events):
#   {
#     "kind":       "tool_call" | "model_call" | ...,    (required)
#     "source":     "claude_code" | "codex" | "manual",  (required)
#     "client_id":  "klinika-melitus" | null,            (optional)
#     "action":     "string",                            (optional)
#     "session_id": "uuid",                              (optional)
#     ...any other canonical fields per autoresearch.events.CANONICAL_FIELDS
#   }
#
# Returns: 200 {event_id, kind, path}
# ---------------------------------------------------------------------------

import os as _os
from typing import Any as _Any

from fastapi import Body


def _get_ingest_token() -> str | None:
    """Resolve the bearer token from env. Returns None if unset → endpoint
    rejects all calls (closed by default)."""
    token = _os.environ.get("GOFREDDY_INGEST_TOKEN")
    return token if token else None


@router.post("/v1/portal/_ingest")
@limiter.limit("600/minute")  # high cap — every Claude Code tool call fires this
async def portal_ingest(
    request: Request,
    payload: Annotated[dict[str, _Any], Body(...)],
) -> dict:
    """Append a canonical event to the per-client log.

    Closed by default: requires GOFREDDY_INGEST_TOKEN env var set + matching
    Authorization header. Validation rules:
      - kind: required, string; if not in KNOWN_KINDS must start with 'x-'
              (forward-compat namespace for source-specific event types)
      - source: required, string
      - client_id: optional, string|None — None routes to operator-internal log
      - all other canonical fields: optional, passed through

    Returns event_id (ULID-shaped) the caller can correlate against subsequent
    events (parent_event_id linkage for tree views).
    """
    # Auth (shared-secret bearer token)
    expected_token = _get_ingest_token()
    if not expected_token:
        raise HTTPException(
            status_code=503,
            detail={"code": "ingest_disabled",
                    "message": "GOFREDDY_INGEST_TOKEN not configured"},
        )
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail={"code": "missing_bearer"})
    provided = auth_header[len("Bearer "):].strip()
    # Constant-time compare
    import hmac as _hmac
    if not _hmac.compare_digest(provided, expected_token):
        raise HTTPException(status_code=401, detail={"code": "bad_token"})

    # Body validation
    kind = payload.get("kind")
    source = payload.get("source")
    if not isinstance(kind, str) or not kind:
        raise HTTPException(
            status_code=400,
            detail={"code": "missing_kind", "message": "kind is required"},
        )
    if not isinstance(source, str) or not source:
        raise HTTPException(
            status_code=400,
            detail={"code": "missing_source", "message": "source is required"},
        )

    # Kind validation: known kind OR explicit x-prefix extension
    from autoresearch.events import KNOWN_KINDS, log_event, client_events_path
    if kind not in KNOWN_KINDS and not kind.startswith("x-"):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "unknown_kind",
                "message": (
                    f"kind '{kind}' is not in KNOWN_KINDS and lacks the 'x-' "
                    f"extension prefix. Use a known kind or x-<custom>."
                ),
            },
        )

    # Generate a sortable event_id (ULID-shaped: timestamp + random suffix).
    # We avoid pulling a ULID library; UUID4 hex prefixed by ms timestamp is
    # K-sortable enough for the portal's append-only stream.
    import time as _time
    import secrets as _secrets
    event_id = f"{int(_time.time() * 1000):013d}-{_secrets.token_hex(6)}"

    client_id = payload.get("client_id")
    # Build the kwargs for log_event from the payload, excluding control fields
    log_kwargs = {k: v for k, v in payload.items() if k not in ("kind",)}
    log_kwargs.setdefault("event_id", event_id)

    target_path = client_events_path(client_id)
    try:
        log_event(kind=kind, path=target_path, **log_kwargs)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"code": "log_write_failed", "message": str(exc)},
        ) from exc

    return {
        "event_id": event_id,
        "kind": kind,
        "path": str(target_path),
    }


# ---------------------------------------------------------------------------
# P4 — SSE live event stream
# Path: GET /v1/portal/{slug}/stream
#
# Tails clients/<slug>/audit/events.jsonl (the wide log; per-run subdirs are
# intentionally not followed in v1 — see autoresearch/events.py tail docs).
# Emits last 50 events as backlog, then live events as they're appended, plus
# a `: ping` heartbeat every 15s.
#
# Authorization:
#   EventSource cannot send custom headers, but it DOES send same-origin
#   cookies automatically. Auth flows through the standard
#   `Depends(get_auth_principal)` chain (cookie → Authorization → X-API-Key);
#   POST /v1/auth/cookie sets the `sb_session` cookie after sign-in so the
#   browser's EventSource carries it transparently. The prior `?token=<jwt>`
#   URL fallback was removed (Unit 4) — JWTs no longer appear in URLs or
#   access logs.
#
# Membership: same `resolve_client_access` machinery as /summary and
# /reports/* — 403 on no membership.
# ---------------------------------------------------------------------------

_SLUG_OK_CHARS = set("-_")


def _slug_valid(slug: str) -> bool:
    return bool(slug) and all(ch.isalnum() or ch in _SLUG_OK_CHARS for ch in slug)


@router.get("/v1/portal/{slug}/stream")
@limiter.limit("30/minute")
async def portal_stream(
    request: Request,
    slug: str,
    principal: Annotated[AuthPrincipal, Depends(get_auth_principal)],
) -> StreamingResponse:
    """SSE live tail of the per-client canonical events log.

    Yields `data: <json>\\n\\n` SSE messages framing each event in the JSONL
    log at ``clients/<slug>/audit/events.jsonl``, plus `: ping\\n\\n`
    heartbeats every 15s to keep proxies from closing idle connections.

    Backlog: last 50 events are emitted on connect (no Last-Event-ID handling
    in v1 — reconnects always replay the most recent 50). Rotation is
    detected via inode change in the tailer.
    """
    if not _slug_valid(slug):
        raise HTTPException(
            status_code=400, detail={"code": "invalid_slug"}
        )

    role = await resolve_client_access(
        request.app.state.db_pool, principal.user_id, slug
    )
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "no_membership",
                "message": f"No access to client '{slug}'",
            },
        )

    target_path = client_events_path(slug)

    return StreamingResponse(
        tail_events_sse(target_path),
        media_type="text/event-stream",
        headers={
            # Defeat proxy buffering — without these, nginx / Fly's edge will
            # buffer the response and clients see stale silence.
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
