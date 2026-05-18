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
from fastapi import Path as FastApiPath
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from autoresearch.events import (
    EventLogCorruption,
    client_events_path,
    read_events,
    tail_events_sse,
)
from src.portal.redaction import (
    REDACTOR_VERSION,
    redact_text,
    redact_transcript_event,
)
from src.portal.transcript_parser import (
    lookup_session_in_registry,
    parse_cc_jsonl,
    parse_codex_jsonl,
)
from src.portal.transcript_tailer import (
    cc_root,
    codex_root,
    session_registry_path,
)

from ..dependencies import (
    AuthPrincipal,
    get_auth_principal,
)
from ..membership import resolve_client_access
from ..rate_limit import limiter

router = APIRouter()


def _jinja_linkify(value: Any) -> Any:
    """Auto-linkify ``https?://...`` URLs in a string, post-autoescape.

    Runs AFTER Jinja's autoescape has done HTML-escape, so the input here is
    already HTML-safe text (e.g. ``&lt;script&gt;``). We re-wrap only literal
    ``http://`` / ``https://`` URL spans into ``<a>`` tags and return a
    ``Markup`` so Jinja doesn't double-escape.

    No markdown parser; no general HTML pass-through; no ``|safe`` from
    user-controlled inputs. Per Unit 6 spec T4.
    """
    from markupsafe import Markup, escape

    if value is None:
        return ""
    # Escape first — input may be the raw event body that hasn't been
    # autoescaped yet (Jinja autoescape applies once, at the {{...}} site).
    text = str(value)
    escaped = str(escape(text))
    url_re = re.compile(r"https?://[^\s<>\"']+")

    def _repl(m: re.Match[str]) -> str:
        url = m.group(0)
        # url itself is already escaped because we ran escape() over the
        # whole string before regex-substituting. The URL chars (& -> &amp;)
        # are valid inside href and don't need a second pass.
        return f'<a class="linkified" href="{url}" target="_blank" rel="noopener noreferrer">{url}</a>'

    return Markup(url_re.sub(_repl, escaped))


_TEMPLATES = Jinja2Templates(
    directory=str(Path(__file__).resolve().parents[3] / "portal" / "templates")
)
_TEMPLATES.env.filters["linkify"] = _jinja_linkify


# CSP header reused by every transcript-renderer route (Unit 6 + Unit 7).
# 'unsafe-inline' is scoped to style only — JS comes from /static.
_TRANSCRIPT_CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "object-src 'none'"
)


def transcript_csp_header() -> dict[str, str]:
    """Return the CSP header dict to attach to HTMLResponse on /portal pages.

    Exposed as a helper so Unit 7's `/portal/<slug>` moments-timeline route
    can apply the same policy without duplicating the literal.
    """
    return {"Content-Security-Policy": _TRANSCRIPT_CSP}


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


# ---------------------------------------------------------------------------
# Unit 3 — Moments REST endpoint
# Path: GET /v1/portal/{slug}/moments
#
# Derived-on-read timeline of "what the agency did" — one row per moment-class
# event from the per-client wide log. The frontend (Unit 7) loads this on page
# open to render the moments list; the SSE stream (portal_stream) layers live
# moments on top.
#
# Auth: cookie/Authorization/X-API-Key via get_auth_principal (Unit 4); slug
# membership via resolve_client_access. 403 no_membership when the user has no
# row in user_client_memberships for this slug; 404 client_not_found when the
# slug itself doesn't exist in the clients table (don't pretend it's a hidden
# tenant — the slug is operator-controlled, not user-input).
#
# Redaction: every moment's metadata.title + metadata.body is run through
# Unit 5's redact_text before serialization. HTML-escape is a render-time
# concern (Unit 7), NOT applied here — JSON consumers receive the raw
# <redacted:KIND> markers verbatim.
#
# Plan: docs/plans/2026-05-18-001-feat-portal-moments-redesign-plan.md
# Spec: §"Unit 3: Moments REST endpoint".
# ---------------------------------------------------------------------------

# Kinds the timeline surfaces. Anything else (e.g. raw `tool_call`,
# `model_call`, `edit`) is filtered out server-side — the moments view is
# moment-class only. Keep in sync with portal_moments.html (Unit 7).
TIMELINE_ELIGIBLE_KINDS: frozenset[str] = frozenset({
    "moment",
    "session_start",
    "session_end",
    "review_required",
    "review_approve",
    "review_reject",
    "sla_breach",
    "render",
    "promotion",
})


def _moment_session_tag(metadata: dict[str, Any] | None) -> str | None:
    """Compute the `<lane>` or `<lane>·<variant>` tag per R3.1.

    Server-side derivation avoids each consumer reimplementing. Returns None
    when no `lane` is present — moments emitted by non-lane sources (e.g.
    CC hook tool_calls promoted to moments) don't carry a meaningful tag.
    """
    if not isinstance(metadata, dict):
        return None
    lane = metadata.get("lane")
    if not isinstance(lane, str) or not lane:
        return None
    variant = metadata.get("variant")
    if isinstance(variant, str) and variant:
        return f"{lane}·{variant}"
    return lane


def _moment_session_id(event: dict[str, Any]) -> str | None:
    """Extract the session_id used for `session=` filtering.

    Canonical `session_id` is a top-level field on every event; some
    moment-class events also carry it under `metadata.session_id`. We check
    both so the filter works regardless of which writer placed it.
    """
    sid = event.get("session_id")
    if isinstance(sid, str) and sid:
        return sid
    meta = event.get("metadata")
    if isinstance(meta, dict):
        meta_sid = meta.get("session_id")
        if isinstance(meta_sid, str) and meta_sid:
            return meta_sid
    return None


def _redact_moment_metadata(metadata: Any) -> dict[str, Any]:
    """Apply redact_text to metadata.title + metadata.body in-place (on a copy).

    Limits redaction to the two free-text surfaces the spec calls out — we
    don't recursively walk the whole metadata blob here because other fields
    (moment_kind, source_event_ids, lane, variant) are operator-controlled
    enums/IDs that don't carry secrets and shouldn't be marker-mangled if
    they happen to look like high-entropy tokens.
    """
    if not isinstance(metadata, dict):
        return {}
    out = dict(metadata)
    title = out.get("title")
    if isinstance(title, str) and title:
        redacted_title, _ = redact_text(
            title, source="moment_title", emit_audit=False
        )
        out["title"] = redacted_title
    body = out.get("body")
    if isinstance(body, str) and body:
        redacted_body, _ = redact_text(
            body, source="moment_body", emit_audit=False
        )
        out["body"] = redacted_body
    return out


async def _client_slug_exists(pool, slug: str) -> bool:
    """Direct check against the clients table. `resolve_client_access` returns
    None both for "slug doesn't exist" AND "user has no membership"; this
    splits the two so we can emit 404 vs 403 per the plan's auth contract.
    """
    async with pool.acquire() as conn:
        return bool(
            await conn.fetchval(
                "SELECT TRUE FROM clients WHERE slug = $1 LIMIT 1", slug
            )
        )


@router.get("/v1/portal/{slug}/moments")
@limiter.limit("60/minute")
async def portal_moments(
    request: Request,
    slug: Annotated[str, FastApiPath(pattern=r"^[a-z0-9-]{1,64}$")],
    principal: Annotated[AuthPrincipal, Depends(get_auth_principal)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    since: Annotated[str | None, Query(pattern=r"^evt_[A-Za-z0-9_-]+$")] = None,
    before: Annotated[str | None, Query(pattern=r"^evt_[A-Za-z0-9_-]+$")] = None,
    kind: Annotated[str | None, Query(pattern=r"^[a-z_]+(,[a-z_]+)*$")] = None,
    session: Annotated[str | None, Query(pattern=r"^[A-Za-z0-9_-]{1,128}$")] = None,
) -> dict:
    """Return up to `limit` newest timeline-eligible events for `slug`, redacted.

    Pagination contract:
      * `since=<event_id>`: events whose event_id is *strictly after* the
        named event in the log's append order. Matches the SSE stream's
        Last-Event-ID resume semantics (R-Live-3) — clients re-arming after
        an SSE disconnect pass their last seen event_id and get the gap
        backfilled.
      * `before=<event_id>`: events whose event_id is *strictly before* the
        named event. Power-user pagination for walking older moments.
      * `since` + `before` are independent: either, both, or neither.
      * Results are always newest-first, capped at `limit` (default 50,
        max 200 — enforced by the Query validator).

    Response shape (also documented in the plan's Unit 3 spec):
      {
        "moments": [
          {
            "event_id": "...",
            "ts": "<canonical iso timestamp>",
            "kind": "moment" | "session_start" | ...,
            "metadata": { ...redacted... },
            "session_id": "..." | null,
            "session_tag": "<lane>·<variant>" | null,
            "redactor_version": "v1",
          },
          ...
        ],
        "oldest_event_id": "..." | null,
        "newest_event_id": "..." | null,
        "has_more": false,
      }

    Auth: 401 missing_credentials (no auth), 403 no_membership (auth but no
    row on this slug), 404 client_not_found (slug not in clients table).
    """
    # --- auth + membership gate (mirrors portal_summary) ---
    role = await resolve_client_access(
        request.app.state.db_pool, principal.user_id, slug
    )
    if role is None:
        # Disambiguate 404 (slug doesn't exist) from 403 (no membership).
        # resolve_client_access returns None for both; we want operators
        # to see 404 on typo'd URLs and members-of-other-clients to see 403.
        if not await _client_slug_exists(request.app.state.db_pool, slug):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "client_not_found",
                    "message": f"Unknown client slug: '{slug}'",
                },
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "no_membership",
                "message": f"No access to client '{slug}'",
            },
        )

    # --- parse kind filter into the timeline-eligible intersection ---
    if kind is not None:
        requested = {k for k in kind.split(",") if k}
        effective_kinds = requested & TIMELINE_ELIGIBLE_KINDS
    else:
        effective_kinds = set(TIMELINE_ELIGIBLE_KINDS)

    # If the caller asked for a kind that's not timeline-eligible (e.g.
    # tool_call), the intersection is empty — return early with an empty
    # list rather than reading the file just to drop everything.
    if not effective_kinds:
        return {
            "moments": [],
            "oldest_event_id": None,
            "newest_event_id": None,
            "has_more": False,
        }

    # --- read events from the per-client wide log (rotation-aware) ---
    # read_events already merges rotated segments (oldest-first by mtime)
    # with the current file, under shared flock. A corrupted line will raise
    # EventLogCorruption — for v1 we let it bubble to a 500; the operator
    # fix on disk restores service. (portal_summary's _read_events_for_summary
    # swallows EventLogCorruption to []; moments is stricter because a 200
    # with a silently truncated history would mislead the client.)
    events_path = client_events_path(slug)
    try:
        # Materialise into a list so we can reverse + filter without
        # re-reading. The per-client log is bounded (~100MB rotation) and
        # this endpoint is rate-limited at 60/min — memory is fine.
        all_events = list(read_events(path=events_path))
    except EventLogCorruption:
        # Match portal_summary's tolerant posture — a corrupt line on disk
        # shouldn't black-hole the timeline. Return empty + has_more=False
        # so the frontend renders "no recent activity" instead of 500ing.
        all_events = []

    # --- apply since/before window in append (oldest-first) order ---
    # read_events yields rotated then current, both internally oldest-first
    # within each segment. event_id is monotonic-by-ms-timestamp by the
    # log_event convention, but we use append order (file order) as the
    # authoritative pagination cursor — matches the SSE stream's contract.
    if since is not None:
        for idx, ev in enumerate(all_events):
            if ev.get("event_id") == since:
                all_events = all_events[idx + 1:]
                break
        else:
            # `since` not found in the log — treat as "from the beginning"
            # so a stale resume cursor doesn't strand the client. The
            # alternative (404 on unknown since) would force frontends to
            # special-case stale cursors during normal log rotation.
            pass

    if before is not None:
        for idx, ev in enumerate(all_events):
            if ev.get("event_id") == before:
                all_events = all_events[:idx]
                break
        else:
            # Same posture as since: unknown `before` is a no-op, not 404.
            pass

    # --- filter by timeline-eligible kinds + optional kind/session ---
    filtered: list[dict[str, Any]] = []
    for ev in all_events:
        ev_kind = ev.get("kind")
        if ev_kind not in effective_kinds:
            continue
        if session is not None and _moment_session_id(ev) != session:
            continue
        filtered.append(ev)

    # --- newest-first + cap at limit ---
    filtered.reverse()
    has_more = len(filtered) > limit
    page = filtered[:limit]

    # --- redact + shape ---
    moments_out: list[dict[str, Any]] = []
    for ev in page:
        raw_meta = ev.get("metadata") if isinstance(ev.get("metadata"), dict) else {}
        redacted_meta = _redact_moment_metadata(raw_meta)
        moments_out.append({
            "event_id": ev.get("event_id"),
            "ts": ev.get("timestamp"),
            "kind": ev.get("kind"),
            "metadata": redacted_meta,
            "session_id": _moment_session_id(ev),
            "session_tag": _moment_session_tag(raw_meta),
            "redactor_version": REDACTOR_VERSION,
        })

    return {
        "moments": moments_out,
        # Newest-first order — `moments_out[0]` is newest, `moments_out[-1]`
        # is oldest *of this page*. The cursors describe the page boundaries
        # so the frontend can paginate with `?before=<oldest_event_id>`.
        "newest_event_id": moments_out[0]["event_id"] if moments_out else None,
        "oldest_event_id": moments_out[-1]["event_id"] if moments_out else None,
        "has_more": has_more,
    }


# ---------------------------------------------------------------------------
# Unit 6 — Transcript drill-down route
# Path: GET /portal/{slug}/transcript/{session_id}
#
# IDOR guard (R9.1): the session_id ↦ file_path mapping comes from the
# per-client session registry (clients/<slug>/audit/sessions.jsonl). The
# raw user input session_id is NEVER used to construct a filesystem path
# — only registry lookups govern access. A session_id not present in the
# requesting slug's registry returns 404 (NOT 403), so an attacker who
# enumerates valid CC UUIDs cannot tell whether the session belongs to
# another tenant or just doesn't exist.
#
# Defense in depth (T8): even if a registry row is poisoned (or written
# by a future codepath that doesn't sanitize the file_path), the helper
# _safe_transcript_path resolves the path strictly and asserts it lives
# under CC_ROOT or CODEX_ROOT — any symlink-escape returns None → 404
# transcript_unavailable, no traceback to the user.
#
# Redaction (R9.4, T3): every parsed event passes through
# redact_transcript_event BEFORE Jinja renders. HTML escape is done by
# Jinja autoescape (the template has .html extension).
#
# Pagination (R9.2): when the parsed event list exceeds 500 rows, render
# the most recent 500 + a "Load older events" link that re-requests with
# ?before=<oldest_rendered_event_id>. Server slices on subsequent fetches.
#
# CSP (T4): response carries the strict CSP returned by transcript_csp_header().
#
# Plan: docs/plans/2026-05-18-001-feat-portal-moments-redesign-plan.md
# Spec: §"Unit 6: Transcript drill-down route + renderer".
# ---------------------------------------------------------------------------


_TRANSCRIPT_PAGE_SIZE = 500


def _safe_transcript_path(file_path: str) -> Path | None:
    """Resolve a registry-stored file_path under CC_ROOT or CODEX_ROOT.

    Returns the resolved Path on success, None on any of:
      * empty / non-string input
      * Path.resolve(strict=True) failure (file missing, OSError, RuntimeError)
      * resolved path NOT relative to CC_ROOT and NOT relative to CODEX_ROOT
      * any parent segment along the original path is itself a symlink
        (catches symlink-in-parent escapes that resolve() alone could miss
        when the symlink target lies under one of the roots).

    Caller treats None as 404 ``transcript_unavailable``. No traceback
    leaks to the user.
    """
    if not isinstance(file_path, str) or not file_path:
        return None

    candidate = Path(file_path)
    try:
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError):
        return None

    try:
        cc_resolved = cc_root().resolve(strict=False)
        codex_resolved = codex_root().resolve(strict=False)
    except (OSError, RuntimeError):
        return None

    if not (
        resolved.is_relative_to(cc_resolved)
        or resolved.is_relative_to(codex_resolved)
    ):
        return None

    # Walk parents from root down: any pre-resolution segment that is
    # itself a symlink is rejected as a defense against symlink-in-parent
    # races where one parent points elsewhere even though .resolve()
    # ends up inside a watched root by coincidence.
    try:
        anchor = Path(candidate.anchor) if candidate.anchor else Path("/")
        # Use parts after the anchor to avoid double-counting "/" itself.
        cursor = anchor
        for segment in candidate.parts[len(anchor.parts):]:
            cursor = cursor / segment
            if cursor.is_symlink():
                return None
    except (OSError, RuntimeError):
        return None

    return resolved


@router.get(
    "/portal/{slug}/transcript/{session_id}",
    response_class=HTMLResponse,
)
@limiter.limit("60/minute")
async def portal_transcript(
    request: Request,
    slug: Annotated[str, FastApiPath(pattern=r"^[a-z0-9-]{1,64}$")],
    session_id: Annotated[str, FastApiPath(pattern=r"^[A-Za-z0-9_-]{1,128}$")],
    principal: Annotated[AuthPrincipal, Depends(get_auth_principal)],
    event_id: Annotated[str | None, Query(pattern=r"^[A-Za-z0-9_.-]{1,128}$")] = None,
    before: Annotated[str | None, Query(pattern=r"^[A-Za-z0-9_.-]{1,128}$")] = None,
) -> HTMLResponse:
    """Render the CC or Codex transcript backing one session_id.

    Auth model:
      * 401 — no principal (handled upstream by get_auth_principal).
      * 403 ``no_membership`` — caller has no row in user_client_memberships
        for the requested slug. The slug itself may or may not exist; we
        don't disambiguate here because the membership check is the
        narrower control.
      * 404 ``transcript_unavailable`` — slug has no registry row matching
        ``session_id`` (R9.1 IDOR), OR the registry's file_path is missing
        / outside CC_ROOT+CODEX_ROOT (T8).
    """
    # --- auth + membership gate ---
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

    # --- IDOR guard via session registry (R9.1) ---
    registry = lookup_session_in_registry(
        session_registry_path(slug), session_id
    )
    if registry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "transcript_unavailable"},
        )

    # --- T8 path safety on registry-stored file_path ---
    transcript_path = _safe_transcript_path(registry.file_path)
    if transcript_path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "transcript_unavailable"},
        )

    # --- parse per registry.source ---
    if registry.source == "codex":
        parse_result = parse_codex_jsonl(transcript_path)
    else:
        parse_result = parse_cc_jsonl(transcript_path)

    # --- redact every event BEFORE Jinja render ---
    # The renderer needs dataclass attribute access (.body, .role, etc.),
    # but redact_transcript_event takes/returns dicts. We convert each
    # event to a dict, redact, then back to a SimpleNamespace so the
    # template can keep using attribute syntax (matches U5's contract:
    # ``redact_transcript_event(ev: dict) -> (dict, records)``).
    from types import SimpleNamespace
    from dataclasses import asdict

    redacted_events: list[Any] = []
    total_redaction_count = 0
    for ev in parse_result.events:
        ev_dict = asdict(ev)
        new_ev, records = redact_transcript_event(ev_dict, emit_audit=False)
        total_redaction_count += len(records)
        redacted_events.append(SimpleNamespace(**new_ev))

    # --- pagination (R9.2): cap at 500, oldest-pagination via ?before= ---
    # event_id ordering inside the parsed list is *parse order* (file
    # order), which equals chronological order for both CC and Codex
    # JSONLs. The "before" cursor slices everything before the named
    # event_id; the cap then keeps the most recent _TRANSCRIPT_PAGE_SIZE.
    if before is not None:
        cutoff = None
        for idx, ev in enumerate(redacted_events):
            if ev.event_id == before:
                cutoff = idx
                break
        if cutoff is not None:
            redacted_events = redacted_events[:cutoff]

    has_more = len(redacted_events) > _TRANSCRIPT_PAGE_SIZE
    if has_more:
        redacted_events = redacted_events[-_TRANSCRIPT_PAGE_SIZE:]

    oldest_event_id = redacted_events[0].event_id if redacted_events else None

    # --- short path label for the meta line (don't leak the full
    # filesystem layout — show only the basename + parent dir). ---
    try:
        file_path_short = (
            f".../{transcript_path.parent.name}/{transcript_path.name}"
        )
    except Exception:  # noqa: BLE001
        file_path_short = transcript_path.name

    response = _TEMPLATES.TemplateResponse(
        request=request,
        name="portal_transcript.html",
        context={
            "slug": slug,
            "session_id": session_id,
            "source": registry.source,
            "file_path_short": file_path_short,
            "ended_at": registry.ended_at,
            "events": redacted_events,
            "partial": parse_result.partial,
            "has_more": has_more,
            "oldest_event_id": oldest_event_id,
            "redaction_count": total_redaction_count,
            "redactor_version": REDACTOR_VERSION,
            "anchor_event_id": event_id,
        },
        headers=transcript_csp_header(),
    )
    return response
