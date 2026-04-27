"""API key management endpoints."""

import secrets
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator

from ..dependencies import get_current_user_id, get_api_key_repo
from ..rate_limit import limiter
from ..users import ApiKeyRepo

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


class CreateApiKeyRequest(BaseModel):
    """Request to create a new API key."""
    name: str | None = Field(None, max_length=100, description="Optional key name")

    @field_validator("name", mode="after")
    @classmethod
    def _strip_or_null(cls, value: str | None) -> str | None:
        # F-b-5-6: empty / whitespace-only names produce rows where the name
        # field is "" rather than null; the keys list then displays a label
        # column with blank entries indistinguishable from null. Mirror the
        # /v1/monitors fix (F-b-4-1): strip then null-out empty values.
        if value is None:
            return None
        stripped = value.strip()
        return stripped if stripped else None


class CreateApiKeyResponse(BaseModel):
    """Response with cleartext key (shown only once)."""
    id: UUID
    key: str = Field(description="Full API key (only shown once)")
    key_prefix: str
    name: str | None


class ApiKeyResponse(BaseModel):
    """API key details (masked)."""
    id: UUID
    key_prefix: str
    name: str | None
    created_at: str
    last_used_at: str | None
    is_active: bool


@router.post(
    "",
    response_model=CreateApiKeyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new API key",
    responses={
        400: {"description": "Max key limit reached"},
        401: {"description": "Not authenticated"},
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit("5/hour")
async def create_api_key(
    request: Request,
    body: CreateApiKeyRequest,
    user_id: UUID = Depends(get_current_user_id),
    repo: ApiKeyRepo = Depends(get_api_key_repo),
) -> CreateApiKeyResponse:
    """Create a new API key.

    The full key is returned only once in this response.
    Store it securely - it cannot be retrieved again.
    """
    # Generate key with vi_sk_ prefix
    raw_token = secrets.token_urlsafe(32)
    full_key = f"vi_sk_{raw_token}"

    api_key = await repo.create_api_key_atomic(user_id, full_key, body.name)
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "max_keys_reached",
                "message": "Maximum of 10 active API keys reached. Revoke an existing key first.",
            },
        )

    return CreateApiKeyResponse(
        id=api_key.id,
        key=full_key,
        key_prefix=api_key.key_prefix,
        name=api_key.name,
    )


@router.get(
    "",
    response_model=list[ApiKeyResponse],
    summary="List API keys",
    responses={
        401: {"description": "Not authenticated"},
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit("30/minute")
async def list_api_keys(
    request: Request,
    user_id: UUID = Depends(get_current_user_id),
    repo: ApiKeyRepo = Depends(get_api_key_repo),
) -> list[ApiKeyResponse]:
    """List all API keys for the current user (including revoked)."""
    keys = await repo.list_api_keys(user_id)
    return [
        ApiKeyResponse(
            id=k.id,
            key_prefix=k.key_prefix,
            name=k.name,
            created_at=k.created_at.isoformat(),
            last_used_at=k.last_used_at.isoformat() if k.last_used_at else None,
            is_active=k.is_active,
        )
        for k in keys
    ]


@router.delete(
    "/{key_id}",
    status_code=status.HTTP_200_OK,
    summary="Revoke an API key",
    responses={
        404: {"description": "Key not found"},
        401: {"description": "Not authenticated"},
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit("30/minute")
async def revoke_api_key(
    request: Request,
    key_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    repo: ApiKeyRepo = Depends(get_api_key_repo),
) -> dict:
    """Revoke an API key (soft-delete).

    Idempotent: revoking an already-revoked key returns success.
    """
    revoked = await repo.revoke_api_key(key_id, user_id)
    if not revoked:
        # Check if key exists but is already revoked (idempotent)
        keys = await repo.list_api_keys(user_id)
        key_exists = any(k.id == key_id for k in keys)
        if key_exists:
            return {"status": "revoked", "key_id": str(key_id)}
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": f"API key {key_id} not found"},
        )
    return {"status": "revoked", "key_id": str(key_id)}
