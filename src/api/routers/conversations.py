"""Conversation CRUD API endpoints."""

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from ..rate_limit import limiter
from ...billing.models import BillingContext
from ...conversations import (
    ConversationNotFoundError,
    ConversationService,
)
from ..dependencies import get_billing_context, get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["conversations"])


# ── Request/Response models ─────────────────────────────────────────────────


class RenameRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)


# ── Dependency ──────────────────────────────────────────────────────────────


def get_conversation_service(request: Request) -> ConversationService:
    return request.app.state.conversation_service


# ── Endpoints ───────────────────────────────────────────────────────────────


@router.post("", status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_conversation(
    request: Request,
    billing: BillingContext = Depends(get_billing_context),
    service: ConversationService = Depends(get_conversation_service),
) -> dict[str, Any]:
    """Create a new conversation with tier-based TTL."""
    conv = await service.create_conversation(billing.user.id, billing.tier)
    return {
        "id": str(conv.id),
        "title": conv.title,
        "created_at": conv.created_at.isoformat(),
        "expires_at": conv.expires_at.isoformat(),
    }


@router.get("")
@limiter.limit("30/minute")
async def list_conversations(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user_id: UUID = Depends(get_current_user_id),
    service: ConversationService = Depends(get_conversation_service),
) -> dict[str, Any]:
    """List user's conversations (paginated)."""
    conversations = await service.list_conversations(user_id, limit, offset)
    return {
        "data": [
            {
                "id": str(c.id),
                "title": c.title,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat(),
                "expires_at": c.expires_at.isoformat(),
            }
            for c in conversations
        ],
        "total": -1,  # Not computed for v1 perf
        "limit": limit,
        "offset": offset,
    }


@router.get("/{conversation_id}")
@limiter.limit("30/minute")
async def get_conversation(
    request: Request,
    conversation_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: ConversationService = Depends(get_conversation_service),
) -> dict[str, Any]:
    """Get single conversation (ownership enforced)."""
    try:
        conv = await service.get_conversation(conversation_id, user_id)
    except ConversationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "conversation_not_found", "message": f"Conversation {conversation_id} not found"},
        )
    return {
        "id": str(conv.id),
        "title": conv.title,
        "created_at": conv.created_at.isoformat(),
        "updated_at": conv.updated_at.isoformat(),
        "expires_at": conv.expires_at.isoformat(),
    }


@router.get("/{conversation_id}/messages")
@limiter.limit("30/minute")
async def get_messages(
    request: Request,
    conversation_id: UUID,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user_id: UUID = Depends(get_current_user_id),
    service: ConversationService = Depends(get_conversation_service),
) -> dict[str, Any]:
    """Get messages (paginated, chronological)."""
    try:
        messages = await service.get_messages(conversation_id, user_id, limit, offset)
    except ConversationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "conversation_not_found", "message": f"Conversation {conversation_id} not found"},
        )
    return {
        "data": [
            {
                "id": str(m.id),
                "conversation_id": str(m.conversation_id),
                "role": m.role,
                "content": m.content,
                "metadata": m.metadata,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
        "total": -1,  # Not computed for v1 perf
        "limit": limit,
        "offset": offset,
    }


@router.patch("/{conversation_id}")
@limiter.limit("30/minute")
async def rename_conversation(
    request: Request,
    conversation_id: UUID,
    body: RenameRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: ConversationService = Depends(get_conversation_service),
) -> dict[str, Any]:
    """Rename conversation."""
    try:
        conv = await service.rename_conversation(conversation_id, user_id, body.title)
    except ConversationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "conversation_not_found", "message": f"Conversation {conversation_id} not found"},
        )
    return {
        "id": str(conv.id),
        "title": conv.title,
        "updated_at": conv.updated_at.isoformat(),
    }


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("30/minute")
async def delete_conversation(
    request: Request,
    conversation_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: ConversationService = Depends(get_conversation_service),
) -> None:
    """Delete conversation + all workspace data."""
    try:
        await service.delete_conversation(conversation_id, user_id)
    except ConversationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "conversation_not_found", "message": f"Conversation {conversation_id} not found"},
        )
