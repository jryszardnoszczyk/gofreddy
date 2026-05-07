"""Free AI Visibility Scan handler — L4 #6 lead-magnet entry point.

Receives form submissions from the Cloudflare intake worker, persists
a scan workspace under ``<scans_dir>/<scan_id>/``, optionally pings
Slack leads, and spawns the synthesis worker via FastAPI BackgroundTasks.

The synthesis worker (``_run_scan``) is intentionally minimal in v1: it
writes a placeholder synthesis.md and flips ``scan_status`` to
``delivered``. Full Stage-0 + 1a-subset + Opus synthesis + email-via-L4
#7 + R2 upload land when those lanes are wired (master plan §5.2).
"""
from __future__ import annotations

import dataclasses
import json
import logging
import os
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, EmailStr, Field, HttpUrl

router = APIRouter(prefix="/v1/scan", tags=["scan"])
logger = logging.getLogger(__name__)


class ScanRequest(BaseModel):
    url: HttpUrl
    email: EmailStr
    vertical: str | None = None
    segment: str | None = None
    geo: str | None = None
    employee_count: str | None = None


class ScanResponse(BaseModel):
    scan_id: str
    tracking_url: str
    status: str = Field(default="pending")


@dataclasses.dataclass
class ScanState:
    scan_id: str
    url: str
    email: str
    firmographics: dict
    scan_status: str = "pending"
    scan_url: str | None = None
    created_at: str = ""
    error: str | None = None


def _scans_dir() -> Path:
    explicit = os.environ.get("GOFREDDY_SCANS_DIR")
    if explicit:
        return Path(explicit)
    cd = Path(os.environ.get("GOFREDDY_CLIENTS_DIR", "/data/clients"))
    return cd.parent / "_scans"


def _scan_dir(scan_id: str) -> Path:
    return _scans_dir() / scan_id


def _save_state(state: ScanState) -> None:
    d = _scan_dir(state.scan_id)
    d.mkdir(parents=True, exist_ok=True)
    (d / "state.json").write_text(
        json.dumps(dataclasses.asdict(state), indent=2, sort_keys=True), encoding="utf-8"
    )


def _load_state(scan_id: str) -> ScanState:
    p = _scan_dir(scan_id) / "state.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    return ScanState(**data)


def _new_scan_id() -> str:
    try:
        from ulid import ULID  # type: ignore[import-not-found]
        return str(ULID()).lower()
    except ImportError:
        return f"scan_{int(time.time())}_{secrets.token_hex(4)}"


def _slack_lead_ping(scan_id: str, url: str, email: str) -> None:
    hook = os.environ.get("SLACK_WEBHOOK_LEADS", "").strip()
    if not hook:
        return
    try:
        httpx.post(
            hook,
            json={"text": f"New free scan request: {url} ({email}) — id `{scan_id}`"},
            timeout=5.0,
        )
    except Exception:
        logger.exception("slack lead ping failed for %s", scan_id)


def _run_scan(scan_id: str) -> None:
    """v1 placeholder synthesis worker.

    Writes ``synthesis.md``, sends the synthesis email via Resend (no-op
    if RESEND_API_KEY unset), and flips ``scan_status`` to ``delivered``.
    Full Stage-0 + 1a-subset + Opus synthesis lands when the
    ``scan_synthesis.md`` prompt is wired.
    """
    try:
        state = _load_state(scan_id)
        synthesis_md = (
            f"# AI Visibility Scan — {state.url}\n\n"
            f"_Placeholder synthesis. Full Opus-driven scan lands when "
            f"`prompts/scan_synthesis.md` and Stage-1a subset wiring ship._\n"
        )
        d = _scan_dir(scan_id)
        (d / "synthesis.md").write_text(synthesis_md, encoding="utf-8")

        from src.audit.email_delivery import send_email
        synthesis_html = (
            f"<h1>AI Visibility Scan — {state.url}</h1>"
            f"<p>Your free scan is ready. Full report lands when synthesis "
            f"prompt is wired; this is the placeholder delivery confirming "
            f"end-to-end plumbing.</p>"
        )
        send_email(
            to=state.email,
            subject=f"Your AI Visibility Scan — {state.url}",
            html=synthesis_html,
            text=synthesis_md,
        )

        new_state = dataclasses.replace(state, scan_status="delivered")
        _save_state(new_state)
    except Exception as exc:
        logger.exception("scan worker failed for %s", scan_id)
        try:
            state = _load_state(scan_id)
            _save_state(dataclasses.replace(state, scan_status="failed", error=str(exc)))
        except Exception:
            pass


@router.post("/request", response_model=ScanResponse, status_code=202)
async def scan_request(req: ScanRequest, background: BackgroundTasks) -> ScanResponse:
    scan_id = _new_scan_id()
    firmographics = {
        k: v for k, v in {
            "vertical": req.vertical, "segment": req.segment,
            "geo": req.geo, "employee_count": req.employee_count,
        }.items() if v is not None
    }
    state = ScanState(
        scan_id=scan_id,
        url=str(req.url),
        email=str(req.email),
        firmographics=firmographics,
        scan_status="running",
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    _save_state(state)
    _slack_lead_ping(scan_id, str(req.url), str(req.email))
    background.add_task(_run_scan, scan_id)

    base = os.environ.get("SCAN_PUBLIC_BASE_URL", "https://reports.gofreddy.ai/scan").rstrip("/")
    return ScanResponse(scan_id=scan_id, tracking_url=f"{base}/{scan_id}/", status="running")


@router.get("/{scan_id}", response_model=ScanResponse)
async def scan_status_get(scan_id: str) -> ScanResponse:
    p = _scan_dir(scan_id) / "state.json"
    if not p.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"unknown scan_id={scan_id}")
    state = _load_state(scan_id)
    base = os.environ.get("SCAN_PUBLIC_BASE_URL", "https://reports.gofreddy.ai/scan").rstrip("/")
    return ScanResponse(scan_id=scan_id, tracking_url=f"{base}/{scan_id}/", status=state.scan_status)
