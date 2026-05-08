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
# Reuses the same membership check as portal_summary.
# ---------------------------------------------------------------------------

_ARCHIVE_ROOT = Path(__file__).resolve().parents[3] / "autoresearch" / "archive"

_LANES = {"geo", "competitive", "monitoring", "storyboard", "marketing_audit"}


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

    The fixture is identified by (lane, variant, fixture-slug). Membership in
    the client `slug` is required. The HTML is read from
    autoresearch/archive/<variant>/sessions/<lane>/<fixture>/report.html.
    """
    role = await resolve_client_access(
        request.app.state.db_pool, principal.user_id, slug
    )
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "no_membership", "message": f"No access to client '{slug}'"},
        )

    # Defense-in-depth: validate path components against simple allowlist /
    # whitelist so a malicious slug can't traverse out of the archive root.
    if lane not in _LANES:
        raise HTTPException(status_code=400, detail={"code": "invalid_lane"})
    if not variant.startswith("v") or not variant[1:].isdigit():
        raise HTTPException(status_code=400, detail={"code": "invalid_variant"})
    # fixture slug constrained to alphanumerics + - _ . (per existing fixture naming)
    if not all(ch.isalnum() or ch in "-_." for ch in fixture) or ".." in fixture:
        raise HTTPException(status_code=400, detail={"code": "invalid_fixture"})

    report_path = _ARCHIVE_ROOT / variant / "sessions" / lane / fixture / "report.html"
    if not report_path.exists():
        raise HTTPException(
            status_code=404,
            detail={"code": "report_not_found",
                    "path": str(report_path.relative_to(_ARCHIVE_ROOT))},
        )

    return HTMLResponse(content=report_path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# α6: Cross-lane meta-pattern viewer (membership-gated)
# Path: /v1/portal/{slug}/meta-patterns
# Surfaces archive/meta_patterns.json (refreshed post-evolve by α5).
# Renders top-N clusters of agent reasoning that recur across lanes/fixtures.
# ---------------------------------------------------------------------------


@router.get("/v1/portal/{slug}/meta-patterns", response_class=HTMLResponse)
@limiter.limit("30/minute")
async def portal_meta_patterns(
    request: Request,
    slug: str,
    principal: Annotated[AuthPrincipal, Depends(get_auth_principal)],
) -> HTMLResponse:
    """Authed view of cross-lane meta-patterns.

    Reads archive/meta_patterns.json (produced by post-evolve
    detect_meta_patterns invocation). 200 + simple HTML table of clusters.
    Membership in the client `slug` is required.
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

    try:
        payload = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise HTTPException(status_code=500, detail={"code": "meta_patterns_corrupt"})

    patterns = payload.get("meta_patterns", [])
    stats = payload.get("stats", {})

    if not patterns:
        body = (
            '<h2>Cross-Lane Meta-Patterns</h2>'
            '<p>No patterns surfaced yet. Run more evolve cycles to gather data.</p>'
        )
    else:
        rows = []
        for p in patterns[:50]:
            rep_text = escape(str(p.get("representative_text", ""))[:240])
            kind = escape(str(p.get("kind", "")))
            occurrences = int(p.get("occurrences", 0))
            distinct_lanes = int(p.get("distinct_lanes", 0))
            distinct_fixtures = int(p.get("distinct_fixtures", 0))
            lanes = escape(", ".join(p.get("lanes", [])))
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
            f'<p>{len(patterns)} clusters · {stats.get("sessions", 0)} sessions · '
            f'{stats.get("beats", 0)} reasoning beats analysed.</p>'
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
