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
