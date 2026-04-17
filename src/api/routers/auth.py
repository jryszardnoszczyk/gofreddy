"""Authentication routes for Supabase OAuth.

Ported from freddy/src/api/routers/auth.py with two changes:
  - BillingService dep removed (gofreddy has no billing layer)
  - /me returns {user_id, email, role, client_slugs} instead of {tier, subscription_status, org_id}
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from ..dependencies import AuthPrincipal, get_auth_principal, revoke_token
from ..membership import list_client_memberships

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthMeResponse(BaseModel):
    """Current user info."""

    user_id: str
    email: str | None = None
    role: str
    client_slugs: list[str] = Field(default_factory=list)


@router.get("/me", response_model=AuthMeResponse)
async def get_me(
    request: Request,
    principal: Annotated[AuthPrincipal, Depends(get_auth_principal)],
) -> AuthMeResponse:
    """Return current user info + accessible client slugs."""
    try:
        memberships = await list_client_memberships(
            request.app.state.db_pool, principal.user_id
        )
        email = principal.claims.get("email") if principal.claims else None
        # Admin role on any membership wins globally
        role = "admin" if any(m.role == "admin" for m in memberships) else (
            memberships[0].role if memberships else "viewer"
        )
        return AuthMeResponse(
            user_id=str(principal.user_id),
            email=email,
            role=role,
            client_slugs=[m.slug for m in memberships],
        )
    except Exception:
        logger.exception("Failed to get user info")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "service_unavailable", "message": "Could not retrieve user info"},
        )


@router.post("/logout", status_code=204)
async def logout(
    principal: Annotated[AuthPrincipal, Depends(get_auth_principal)],
) -> None:
    """Revoke the current JWT token (server-side blocklist).

    Note: In-memory blocklist — effective only on this Cloud Run instance.
    Full cross-instance revocation requires a shared store (future enhancement).
    """
    if principal.claims:
        revoke_token(principal.claims)
    # API key callers: nothing to revoke (keys are managed via /v1/api-keys DELETE)
    return None
