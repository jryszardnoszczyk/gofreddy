"""FastAPI dependency injection for gofreddy auth.

Core blocks extracted verbatim from freddy/src/api/dependencies.py:
  - Token blocklist        (freddy L85-120)
  - AuthPrincipal          (freddy L133-139)
  - security + api_key_header (freddy L246-248)
  - _decode_supabase_jwt   (freddy L250-287)
  - verify_supabase_token  (freddy L290-345)
  - get_auth_principal     (freddy L1734-1786)
  - _resolve_user_from_jwt (freddy L1807-1863; BillingRepository → UserRepo)
  - _resolve_user_from_api_key (freddy L1865-1877; BillingRepository → UserRepo)
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Literal
from uuid import UUID

import asyncpg
import jwt
from cachetools import TTLCache
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from ..auth.config import SupabaseSettings
from .users import UserRepo

logger = logging.getLogger(__name__)

AuthCredentialType = Literal["jwt", "api_key"]

# ─── Token Blocklist ────────────────────────────────────────────────────────
# KNOWN LIMITATION: In-memory blocklist is per-instance. Cloud Run may route
# the next request to a different instance where the token is not blocked.
# For full revocation, use a shared store (Redis or DB table). Acceptable for
# v1 since tokens have short TTLs (1 hour default) and this provides defense
# against replay on the same instance.
_token_blocklist: TTLCache[str, float] = TTLCache(maxsize=10_000, ttl=86400)


def _blocklist_token_key(claims: dict[str, Any]) -> str | None:
    """Extract unique blocklist key from JWT claims. Returns None if not blockable."""
    jti = claims.get("jti")
    if jti:
        return f"jti:{jti}"
    sub = claims.get("sub")
    iat = claims.get("iat")
    if sub and iat:
        return f"sub:{sub}:iat:{iat}"
    return None


def revoke_token(claims: dict[str, Any]) -> bool:
    """Add a token to the blocklist. Returns True if added, False if not blockable."""
    key = _blocklist_token_key(claims)
    if not key:
        return False
    _token_blocklist[key] = time.time()
    return True


def is_token_revoked(claims: dict[str, Any]) -> bool:
    """Check if a token has been revoked."""
    key = _blocklist_token_key(claims)
    if not key:
        return False
    return key in _token_blocklist

# ─── AuthPrincipal ──────────────────────────────────────────────────────────
@dataclass(frozen=True)
class AuthPrincipal:
    """Resolved authenticated caller for the current request."""

    user_id: UUID
    credential_type: AuthCredentialType
    claims: dict[str, Any] | None


security = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def _decode_supabase_jwt(
    token: str,
    supabase_settings: "SupabaseSettings",
    jwks_client: PyJWKClient | None,
) -> dict[str, Any]:
    """Decode a Supabase JWT using JWKS (ES256) or shared secret (HS256).

    Newer Supabase CLI versions (v2.76+) issue ES256 tokens with a JWKS endpoint.
    Cloud Supabase uses HS256 with a shared JWT secret. We try JWKS first, then
    fall back to the shared secret.
    """
    expected_issuer = f"{supabase_settings.supabase_url}/auth/v1"
    decode_kwargs: dict[str, Any] = {
        "audience": "authenticated",
        "issuer": expected_issuer,
    }

    # Try JWKS first (handles ES256, RS256, etc.)
    if jwks_client is not None:
        try:
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            return jwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256", "RS256"],
                **decode_kwargs,
            )
        except (jwt.exceptions.PyJWKClientError, jwt.InvalidTokenError):
            # JWKS failed — fall through to HS256
            pass

    # Fallback: HS256 with shared secret (Supabase Cloud)
    return jwt.decode(
        token,
        supabase_settings.supabase_jwt_secret.get_secret_value(),
        algorithms=["HS256"],
        **decode_kwargs,
    )


async def verify_supabase_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict[str, Any]:
    """Verify Supabase JWT from Authorization: Bearer header.

    Returns decoded JWT claims (sub, email, etc.).
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "missing_token", "message": "Missing authentication token"},
        )
    token = credentials.credentials

    supabase_settings: SupabaseSettings | None = getattr(
        request.app.state, "supabase_settings", None
    )
    if supabase_settings is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "auth_unavailable", "message": "Authentication not configured"},
        )

    jwks_client: PyJWKClient | None = getattr(request.app.state, "jwks_client", None)

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

    return claims

async def get_auth_principal(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    x_api_key: str | None = Depends(api_key_header),
) -> AuthPrincipal:
    """Resolve request principal from JWT (preferred) or API key."""
    try:
        has_authorization_header = "authorization" in request.headers

        # Deterministic precedence: when Authorization is present, JWT path wins.
        if has_authorization_header:
            if credentials and credentials.credentials:
                claims = await verify_supabase_token(request=request, credentials=credentials)
                user_id = await _resolve_user_from_jwt(request, claims)
                return AuthPrincipal(
                    user_id=user_id,
                    credential_type="jwt",
                    claims=claims,
                )

            # Do not fallback to API key when Authorization was provided but malformed.
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "invalid_token",
                    "message": "Invalid authentication token",
                },
            )

        if x_api_key:
            user_id = await _resolve_user_from_api_key(request, x_api_key)
            return AuthPrincipal(
                user_id=user_id,
                credential_type="api_key",
                claims=None,
            )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "missing_credentials",
                "message": "Provide Authorization Bearer token or X-API-Key header",
            },
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to resolve auth principal")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "auth_unavailable", "message": "Authentication service unavailable"},
        )


async def _resolve_user_from_jwt(
    request: Request,
    claims: dict[str, Any],
) -> UUID:
    """Resolve local user ID from JWT claims (sub + email)."""
    import asyncpg

    supabase_user_id = claims.get("sub")
    email = claims.get("email")
    if email:
        email = email.lower()
    if not supabase_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_token", "message": "Token missing 'sub' claim"},
        )

    repo: UserRepo = request.app.state.user_repo
    # Fast path: lookup by Supabase user ID
    user = await repo.get_user_by_supabase_id(supabase_user_id)
    if user:
        return user.id

    # First login: try to link existing user by email, or create new
    if email:
        existing = await repo.get_user_by_email(email)
        if existing:
            # Idempotent: if already linked to THIS identity, succeed silently
            if existing.supabase_user_id == supabase_user_id:
                return existing.id
            linked = await repo.link_supabase_user(existing.id, supabase_user_id)
            if not linked:
                # User already has a DIFFERENT Supabase identity — fail closed
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "identity_conflict",
                        "message": "This email is already linked to a different authentication identity. Contact support.",
                    },
                )
            return existing.id

    # Completely new user — create with Supabase identity
    try:
        new_user = await repo.create_user(
            email=email or f"{supabase_user_id}@supabase.user",
            supabase_user_id=supabase_user_id,
        )
        return new_user.id
    except asyncpg.UniqueViolationError:
        # Concurrent insert with same email — retry lookup
        if email:
            existing = await repo.get_user_by_email(email)
            if existing:
                return existing.id
        raise  # Unexpected constraint violation

async def _resolve_user_from_api_key(
    request: Request,
    api_key: str,
) -> UUID:
    """Resolve local user ID from API key."""
    repo: UserRepo = request.app.state.user_repo
    user = await repo.get_user_by_api_key(api_key)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_api_key", "message": "Invalid or expired API key"},
        )
    return user.id


async def get_current_user_id(
    principal: AuthPrincipal = Depends(get_auth_principal),
) -> UUID:
    """Bare user_id dependency for routes that don't need the full principal."""
    return principal.user_id


def get_api_key_repo(request: Request):
    """Return the request's ApiKeyRepo — set in lifespan."""
    return request.app.state.api_key_repo


def get_session_service(request: Request):
    """Return the request's SessionService — set in lifespan."""
    return request.app.state.session_service
