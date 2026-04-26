"""Agency session tracking API endpoints.

Tenant surgery vs freddy:
  - POST /: body gains client_id; 403 if caller can't write to that client.
  - GET /: scope = accessible client_ids (None for admin); lists all or by set.
  - All per-session endpoints: fetch unscoped, check client_id scope, then act.
"""

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from ..dependencies import AuthPrincipal, get_auth_principal
from ..membership import resolve_accessible_client_ids
from ..rate_limit import limiter
from ...sessions import (
    SessionAlreadyCompleted,
    SessionNotFound,
    SessionService,
)
from ...sessions.models import Session
from ...sessions.settings import SessionSettings
from ...sessions.validation import BoundedJsonb

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["sessions"])

_settings = SessionSettings()


# ── Request/Response models ─────────────────────────────────────────────────


class CreateSessionRequest(BaseModel):
    client_id: UUID | None = None
    client_slug: str | None = Field(default=None, max_length=200)
    client_name: str = Field(default="default", max_length=200)
    source: str = Field(default="cli", max_length=50)
    session_type: str = Field(default="ad_hoc", max_length=50)
    purpose: str | None = Field(default=None, max_length=500)


class CompleteSessionRequest(BaseModel):
    status: str = Field(default="completed", pattern=r"^(completed|failed)$")
    summary: str | None = Field(default=None, max_length=5000)


class LogActionRequest(BaseModel):
    tool_name: str = Field(max_length=200)
    input_summary: BoundedJsonb | None = None
    output_summary: BoundedJsonb | None = None
    duration_ms: int | None = Field(default=None, ge=0)
    cost_credits: int = Field(default=0, ge=0)
    status: str = Field(default="success", max_length=50)
    error_code: str | None = Field(default=None, max_length=100)


class LogIterationRequest(BaseModel):
    iteration_number: int = Field(ge=1)
    iteration_type: str = Field(max_length=50)
    status: str = Field(default="success", max_length=50)
    exit_code: int | None = None
    duration_ms: int | None = Field(default=None, ge=0)
    state_snapshot: str | None = Field(default=None, max_length=2_000_000)
    result_entry: dict | None = None
    log_output: str | None = Field(default=None, max_length=5_000_000)


# ── Dependency ──────────────────────────────────────────────────────────────


def get_session_service(request: Request) -> SessionService:
    return request.app.state.session_service


# ── Helpers ─────────────────────────────────────────────────────────────────


def _session_not_found(session_id: UUID) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "session_not_found", "message": f"Session {session_id} not found"},
    )


def _session_already_completed(session_id: UUID) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={"code": "session_already_completed", "message": f"Session {session_id} is already completed"},
    )


def _forbidden(msg: str = "Not a member of this client") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"code": "forbidden", "message": msg},
    )


async def _scope(request: Request, auth: AuthPrincipal) -> list[UUID] | None:
    """Caller's accessible client_ids; None for admin (all access)."""
    return await resolve_accessible_client_ids(
        request.app.state.db_pool, auth.user_id
    )


def _check_client_scope(
    session: Session | None,
    accessible: list[UUID] | None,
    session_id: UUID,
) -> Session:
    """Raise 404 if missing, 403 if the session's client_id is out of scope."""
    if session is None:
        raise _session_not_found(session_id)
    if accessible is None:
        return session
    if session.client_id is None or session.client_id not in accessible:
        raise _forbidden()
    return session


# ── Endpoints ───────────────────────────────────────────────────────────────


@router.post("", status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_session(
    request: Request,
    body: CreateSessionRequest,
    auth: AuthPrincipal = Depends(get_auth_principal),
    service: SessionService = Depends(get_session_service),
) -> dict[str, Any]:
    """Create a session (or return existing running one for this client).

    Accepts either client_id (UUID) or client_slug (human-readable) — slug is
    convenience for the CLI, which doesn't know client UUIDs.
    """
    target_client_id = body.client_id
    accessible = await _scope(request, auth)
    if target_client_id is None:
        if not body.client_slug:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": "client_required", "message": "client_id or client_slug required"},
            )
        async with request.app.state.db_pool.acquire() as conn:
            target_client_id = await conn.fetchval(
                "SELECT id FROM clients WHERE slug = $1", body.client_slug,
            )
        if target_client_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "client_not_found", "message": f"Unknown client slug: {body.client_slug}"},
            )
        if accessible is not None and target_client_id not in accessible:
            raise _forbidden()
    else:
        # UUID branch: gate the existence-check on scope membership FIRST so a
        # cross-org caller can't enumerate which UUIDs exist via 404 vs 403
        # response differential. Non-admins (accessible is a bounded set) only
        # get the existence-check 404 if the UUID is in their accessible set.
        if accessible is not None and target_client_id not in accessible:
            raise _forbidden()
        async with request.app.state.db_pool.acquire() as conn:
            exists = await conn.fetchval(
                "SELECT TRUE FROM clients WHERE id = $1", target_client_id,
            )
        if not exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "client_not_found", "message": f"Unknown client_id: {target_client_id}"},
            )
    session = await service.create_or_return_existing(
        org_id=auth.user_id,
        client_id=target_client_id,
        client_name=body.client_name,
        source=body.source,
        session_type=body.session_type,
        purpose=body.purpose,
    )
    return session.to_dict()


@router.get("")
@limiter.limit("30/minute")
async def list_sessions(
    request: Request,
    client_name: str | None = Query(default=None, max_length=200),
    session_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    auth: AuthPrincipal = Depends(get_auth_principal),
    service: SessionService = Depends(get_session_service),
) -> dict[str, Any]:
    """List sessions within the caller's scope."""
    accessible = await _scope(request, auth)
    if accessible is None:
        sessions = await service.list_sessions(
            org_id=None,
            client_name=client_name,
            status=session_status,
            limit=limit,
            offset=offset,
        )
    elif not accessible:
        sessions = []
    else:
        sessions = await service.list_sessions_for_client_ids(
            client_ids=accessible,
            client_name=client_name,
            status=session_status,
            limit=limit,
            offset=offset,
        )
    return {
        "data": [s.to_dict() for s in sessions],
        "limit": limit,
        "offset": offset,
    }


@router.get("/{session_id}")
@limiter.limit("30/minute")
async def get_session(
    request: Request,
    session_id: UUID,
    auth: AuthPrincipal = Depends(get_auth_principal),
    service: SessionService = Depends(get_session_service),
) -> dict[str, Any]:
    """Get session details."""
    session = await service.get_by_id(session_id)
    accessible = await _scope(request, auth)
    session = _check_client_scope(session, accessible, session_id)
    return session.to_dict()


@router.patch("/{session_id}")
@limiter.limit("30/minute")
async def complete_session(
    request: Request,
    session_id: UUID,
    body: CompleteSessionRequest,
    auth: AuthPrincipal = Depends(get_auth_principal),
    service: SessionService = Depends(get_session_service),
) -> dict[str, Any]:
    """Complete a running session with summary."""
    session = await service.get_by_id(session_id)
    accessible = await _scope(request, auth)
    session = _check_client_scope(session, accessible, session_id)
    try:
        updated = await service.complete_session(
            session_id=session_id,
            org_id=session.org_id,
            status=body.status,
            summary=body.summary,
        )
    except SessionNotFound:
        raise _session_not_found(session_id)
    except SessionAlreadyCompleted:
        raise _session_already_completed(session_id)
    return updated.to_dict()


@router.post("/{session_id}/actions", status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def log_action(
    request: Request,
    session_id: UUID,
    body: LogActionRequest,
    auth: AuthPrincipal = Depends(get_auth_principal),
    service: SessionService = Depends(get_session_service),
) -> dict[str, Any]:
    """Log an action to a session."""
    session = await service.get_by_id(session_id)
    accessible = await _scope(request, auth)
    session = _check_client_scope(session, accessible, session_id)
    try:
        action = await service.log_action(
            session_id=session_id,
            org_id=session.org_id,
            tool_name=body.tool_name,
            input_summary=body.input_summary,
            output_summary=body.output_summary,
            duration_ms=body.duration_ms,
            cost_credits=body.cost_credits,
            status=body.status,
            error_code=body.error_code,
        )
    except SessionNotFound:
        raise _session_not_found(session_id)
    except SessionAlreadyCompleted:
        raise _session_already_completed(session_id)
    return action.to_dict()


@router.get("/{session_id}/actions")
@limiter.limit("30/minute")
async def get_actions(
    request: Request,
    session_id: UUID,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    auth: AuthPrincipal = Depends(get_auth_principal),
    service: SessionService = Depends(get_session_service),
) -> dict[str, Any]:
    """Get actions for a session."""
    session = await service.get_by_id(session_id)
    accessible = await _scope(request, auth)
    session = _check_client_scope(session, accessible, session_id)
    try:
        actions = await service.get_actions(
            session_id=session_id,
            org_id=session.org_id,
            limit=limit,
            offset=offset,
        )
    except SessionNotFound:
        raise _session_not_found(session_id)
    return {
        "data": [a.to_dict() for a in actions],
        "limit": limit,
        "offset": offset,
    }


@router.post("/{session_id}/iterations", status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def log_iteration(
    request: Request,
    session_id: UUID,
    body: LogIterationRequest,
    auth: AuthPrincipal = Depends(get_auth_principal),
    service: SessionService = Depends(get_session_service),
) -> dict[str, Any]:
    """Log an iteration. Large payloads go to R2 when configured, Postgres otherwise."""
    session = await service.get_by_id(session_id)
    accessible = await _scope(request, auth)
    session = _check_client_scope(session, accessible, session_id)

    log_r2_key: str | None = None
    state_r2_key: str | None = None

    log_storage = getattr(request.app.state, "session_log_storage", None)
    if log_storage:
        if body.log_output:
            try:
                log_r2_key = await log_storage.upload_log(
                    str(session_id), body.iteration_number, body.log_output
                )
            except Exception:
                logger.warning(
                    "R2 log upload failed for session %s iter %d, falling back to Postgres",
                    session_id, body.iteration_number, exc_info=True,
                )
                log_r2_key = None
        if body.state_snapshot:
            try:
                state_r2_key = await log_storage.upload_state(
                    str(session_id), body.iteration_number, body.state_snapshot
                )
            except Exception:
                logger.warning(
                    "R2 state upload failed for session %s iter %d, falling back to Postgres",
                    session_id, body.iteration_number, exc_info=True,
                )
                state_r2_key = None

    try:
        iteration = await service.log_iteration(
            session_id=session_id,
            org_id=session.org_id,
            iteration_number=body.iteration_number,
            iteration_type=body.iteration_type,
            status=body.status,
            exit_code=body.exit_code,
            duration_ms=body.duration_ms,
            state_snapshot=state_r2_key or body.state_snapshot,
            result_entry=body.result_entry,
            log_output=log_r2_key or body.log_output,
        )
    except SessionNotFound:
        raise _session_not_found(session_id)
    return iteration.to_dict()


@router.get("/{session_id}/iterations")
@limiter.limit("30/minute")
async def get_iterations(
    request: Request,
    session_id: UUID,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    auth: AuthPrincipal = Depends(get_auth_principal),
    service: SessionService = Depends(get_session_service),
) -> dict[str, Any]:
    """Get iterations for a session."""
    session = await service.get_by_id(session_id)
    accessible = await _scope(request, auth)
    session = _check_client_scope(session, accessible, session_id)
    try:
        iterations = await service.get_iterations(
            session_id=session_id,
            org_id=session.org_id,
            limit=limit,
            offset=offset,
        )
    except SessionNotFound:
        raise _session_not_found(session_id)
    return {
        "data": [i.to_dict() for i in iterations],
        "limit": limit,
        "offset": offset,
    }


@router.post("/{session_id}/transcript", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def upload_transcript(
    request: Request,
    session_id: UUID,
    auth: AuthPrincipal = Depends(get_auth_principal),
    service: SessionService = Depends(get_session_service),
) -> dict[str, Any]:
    """Upload session transcript (exempt from 1MB body limit, 15MB max)."""
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > _settings.max_transcript_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail={
                        "code": "transcript_too_large",
                        "message": f"Transcript exceeds {_settings.max_transcript_bytes // (1024 * 1024)}MB limit",
                    },
                )
        except (ValueError, TypeError):
            pass

    body = await request.body()
    if len(body) > _settings.max_transcript_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "code": "transcript_too_large",
                "message": f"Transcript exceeds {_settings.max_transcript_bytes // (1024 * 1024)}MB limit",
            },
        )

    session = await service.get_by_id(session_id)
    accessible = await _scope(request, auth)
    session = _check_client_scope(session, accessible, session_id)

    transcript = body.decode("utf-8", errors="replace")

    try:
        updated = await service.set_transcript(session_id, session.org_id, transcript)
    except SessionNotFound:
        raise _session_not_found(session_id)

    if not updated:
        raise _session_not_found(session_id)

    return {"status": "ok", "session_id": str(session_id), "size_bytes": len(body)}
