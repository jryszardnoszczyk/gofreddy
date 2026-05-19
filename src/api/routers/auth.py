"""Authentication routes for Supabase OAuth.

Ported from freddy/src/api/routers/auth.py with two changes:
  - BillingService dep removed (gofreddy has no billing layer)
  - /me returns {user_id, email, role, client_slugs} instead of {tier, subscription_status, org_id}
"""

import logging
import time
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from ..dependencies import (
    AuthPrincipal,
    _decode_supabase_jwt,
    get_auth_principal,
    is_token_revoked,
    revoke_token,
)
from ..membership import list_client_memberships
from ..rate_limit import limiter

# Cookie attributes — see plan §Unit 4. httpOnly + Secure + SameSite=Strict.
# Path=/ so EventSource and all portal routes see the cookie.
_COOKIE_NAME = "sb_session"

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthMeResponse(BaseModel):
    """Current user info."""

    user_id: str
    email: str | None = None
    role: str
    client_slugs: list[str] = Field(default_factory=list)


@router.get("/me", response_model=AuthMeResponse)
@limiter.limit("30/minute")
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
@limiter.limit("10/minute")
async def logout(
    request: Request,
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


# ---------------------------------------------------------------------------
# Cookie auth — POST /v1/auth/cookie + DELETE /v1/auth/cookie.
#
# Replaces the prior `?token=<jwt>` SSE URL fallback. The browser POSTs the
# Supabase access_token after sign-in; the server validates it via the same
# `_decode_supabase_jwt` machinery `verify_supabase_token` uses, then sets a
# httpOnly + Secure + SameSite=Strict cookie. EventSource then inherits the
# cookie via same-origin, so no token ever appears in URLs or browser logs.
# ---------------------------------------------------------------------------


class CookieSetRequest(BaseModel):
    """Body for POST /v1/auth/cookie."""

    access_token: str = Field(..., min_length=1)


@router.post("/cookie", status_code=204)
@limiter.limit("10/minute")
async def set_session_cookie(
    request: Request,
    response: Response,
    body: CookieSetRequest,
) -> None:
    """Validate a Supabase JWT and set it as an httpOnly cookie.

    Validation reuses `_decode_supabase_jwt` + `is_token_revoked` so claim
    parity (aud/iss/algorithm allowlist + blocklist) matches every other
    authed surface. On failure the cookie is NOT set; status is 401.
    """
    token = body.access_token

    supabase_settings = getattr(request.app.state, "supabase_settings", None)
    if supabase_settings is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "auth_unavailable", "message": "Authentication not configured"},
        )
    jwks_client = getattr(request.app.state, "jwks_client", None)

    try:
        claims = _decode_supabase_jwt(token, supabase_settings, jwks_client)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "token_expired", "message": "Token has expired"},
        )
    except jwt.InvalidAudienceError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_token", "message": "Invalid token audience"},
        )
    except jwt.InvalidIssuerError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_token", "message": "Invalid token issuer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_token", "message": "Invalid authentication token"},
        )

    if is_token_revoked(claims):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "token_revoked", "message": "Token has been revoked"},
        )

    # Cookie Max-Age = JWT exp - now, clamped to >= 0. If the JWT has no exp
    # claim, fall back to a session cookie (max_age=None).
    exp_claim = claims.get("exp")
    max_age: int | None
    if isinstance(exp_claim, (int, float)):
        delta = int(exp_claim) - int(time.time())
        max_age = max(delta, 0)
    else:
        max_age = None

    response.set_cookie(
        key=_COOKIE_NAME,
        value=token,
        max_age=max_age,
        httponly=True,
        samesite="strict",
        secure=True,
        path="/",
    )
    return None


@router.delete("/cookie", status_code=204)
@limiter.limit("10/minute")
async def clear_session_cookie(
    request: Request,
    response: Response,
    principal: Annotated[AuthPrincipal, Depends(get_auth_principal)],
) -> None:
    """Clear the session cookie AND revoke the JWT.

    Revocation matters because the JWT could otherwise be replayed via
    `Authorization: Bearer <jwt>` after the cookie is gone (T6). The cookie
    is also cleared (Max-Age=0, empty value) with the same attributes used
    on set, so browsers retire it cleanly.
    """
    if principal.claims:
        revoke_token(principal.claims)
    response.set_cookie(
        key=_COOKIE_NAME,
        value="",
        max_age=0,
        httponly=True,
        samesite="strict",
        secure=True,
        path="/",
    )
    return None
