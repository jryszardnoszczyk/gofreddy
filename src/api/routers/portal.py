"""Portal routes — HTML shell + JSON summary.

Design note: a browser page-load cannot send Authorization headers, so the
`/portal/<slug>` route serves an unauthenticated HTML shell. The shell reads
the Supabase session client-side (localStorage) and fetches the authed
`/v1/portal/<slug>/summary` JSON endpoint to render data. Unauth → /login.
"""
from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ..dependencies import AuthPrincipal, get_auth_principal
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
        name="portal_placeholder.html",
        context={
            "slug": slug,
            "supabase_url": settings.supabase_url,
            "supabase_anon_key": settings.supabase_anon_key,
        },
    )


@router.get("/v1/portal/{slug}/summary")
@limiter.limit("60/minute")
async def portal_summary(
    request: Request,
    slug: str,
    principal: Annotated[AuthPrincipal, Depends(get_auth_principal)],
) -> dict:
    """Authed JSON summary for a client's portal. Phase 1 placeholder."""
    role = await resolve_client_access(
        request.app.state.db_pool, principal.user_id, slug
    )
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "no_membership", "message": f"No access to client '{slug}'"},
        )
    email = principal.claims.get("email") if principal.claims else None
    return {
        "slug": slug,
        "role": role,
        "email": email,
        "phase": 1,
        "message": "Auth + membership working. Phase 2 will render real JSONL data here.",
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

_LANES = {"geo", "competitive", "monitoring", "storyboard", "marketing_audit"}
_OPERATOR_ONLY_LANES = {"geo", "competitive", "monitoring", "storyboard"}
_TENANT_LANES = {"marketing_audit"}


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
    if not variant.startswith("v") or not variant[1:].isdigit():
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


# ---------------------------------------------------------------------------
# α6: Cross-lane meta-pattern viewer (membership-gated)
# Path: /v1/portal/{slug}/meta-patterns
# Surfaces archive/meta_patterns.json (refreshed post-evolve by α5).
# Renders top-N clusters of agent reasoning that recur across lanes/fixtures.
# ---------------------------------------------------------------------------


def _safe_int(value: object, default: int = 0) -> int:
    """Coerce attacker-influenced cluster fields to int; never raise.

    Cluster JSON is produced by detect_meta_patterns walking agent-authored
    transcripts. A poisoned cluster with ``occurrences: "many"`` would crash
    the route with an uncaught ValueError → 500 (cheap DoS). Treat
    non-coercible values as zero.
    """
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
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
