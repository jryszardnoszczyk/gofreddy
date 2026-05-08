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
