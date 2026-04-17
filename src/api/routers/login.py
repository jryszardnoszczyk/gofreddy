"""Login page — Jinja-rendered, Supabase JS SDK loaded from ESM CDN.

The HTML page handles sign-in client-side via @supabase/supabase-js, then
redirects to /portal/<first-slug>/ on success. The server only ships the
anon-key config + styles; all auth state lives in Supabase's localStorage.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()

_TEMPLATES = Jinja2Templates(
    directory=str(Path(__file__).resolve().parents[3] / "portal" / "templates")
)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    settings = request.app.state.supabase_settings
    return _TEMPLATES.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "supabase_url": settings.supabase_url,
            "supabase_anon_key": settings.supabase_anon_key,
        },
    )
