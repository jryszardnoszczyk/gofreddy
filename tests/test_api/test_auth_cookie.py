"""POST/DELETE /v1/auth/cookie + cookie-based get_auth_principal precedence.

Covers Unit 4 of the portal-moments redesign plan
(docs/plans/2026-05-18-001-feat-portal-moments-redesign-plan.md §Unit 4).

Why we test against the real Supabase stack:
  The local Supabase fixture issues real JWTs the same way production does
  (ES256 via JWKS). Mocking `verify_supabase_token` would let claim-parity
  bugs slip through (wrong aud, wrong iss, HS256-vs-JWKS confusion). The
  fixtures from conftest.py provide a real JWT via `test_tenant['token']`.

Synthetic JWTs are only used where the negative case requires a specific
malformed claim that the real Supabase wouldn't mint — those go through the
HS256 fallback path inside `_decode_supabase_jwt`.

Cookie-attribute caveats in this test harness:
  * The conftest `api_client` fixture uses `http://testserver` as the base
    URL. The real cookie is set with `Secure=True`, so httpx's cookie jar
    refuses to store it on plaintext URLs (correct browser-aligned
    behavior). Tests that need to RESEND the cookie therefore parse the
    Set-Cookie value out of the POST response and pass it explicitly via
    `cookies=` on the next request. The Set-Cookie attributes themselves
    are still asserted (httponly/samesite/secure/path/max-age) — those
    checks read the raw header, not the jar.

These require local Supabase (auto-skip when not running, per conftest).
"""
from __future__ import annotations

import time

import httpx
import jwt as pyjwt
import pytest


# --- helpers -------------------------------------------------------------

_HS256_SECRET = "unused-locally-via-jwks"  # matches conftest._set_test_env


@pytest.fixture(autouse=True)
def _reset_rate_limiter() -> None:
    """Clear the slowapi limiter between tests.

    The session-scoped FastAPI app shares one in-memory limiter across all
    tests. Several scenarios here POST /v1/auth/cookie multiple times, and
    the route's prod limit of 10/min is sized for human use, not tight
    test loops. Resetting keeps every test isolated from prior request
    counters without diluting the prod limit.
    """
    from src.api.rate_limit import limiter
    limiter.reset()


def _make_hs256_jwt(
    *,
    sub: str = "00000000-0000-0000-0000-000000000000",
    aud: str = "authenticated",
    iss: str | None = None,
    exp_offset: int = 3600,
    extra_claims: dict | None = None,
) -> str:
    """Mint a synthetic HS256 JWT for negative-path tests.

    Production tokens come from the real Supabase stack via the test fixtures;
    these synthetic tokens exist only to exercise specific decode errors that
    `_decode_supabase_jwt` raises (wrong aud, wrong iss, expired) without
    depending on the real auth service to mint a malformed token.
    """
    payload: dict = {
        "sub": sub,
        "aud": aud,
        "iss": iss if iss is not None else "http://127.0.0.1:54321/auth/v1",
        "exp": int(time.time()) + exp_offset,
        "iat": int(time.time()),
        "email": "synthetic@gofreddy.test",
    }
    if extra_claims:
        payload.update(extra_claims)
    return pyjwt.encode(payload, _HS256_SECRET, algorithm="HS256")


def _cookie_attrs(set_cookie_header: str) -> dict:
    """Parse a Set-Cookie header into a flat lower-cased attribute dict.

    httpx exposes Set-Cookie via `response.headers.get("set-cookie")` (or
    `get_list("set-cookie")` for multiple). We only set one cookie per
    response, so the first header is enough.

    Starlette wraps the cookie value in double quotes when it is empty (so
    the wire form is `sb_session=""`). We strip a single layer of matching
    quotes from the value so the assertion side sees `""` as `""`.
    """
    parts = [p.strip() for p in set_cookie_header.split(";")]
    name_value = parts[0]
    name, _, value = name_value.partition("=")
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        value = value[1:-1]
    out = {"_name": name, "_value": value}
    for part in parts[1:]:
        if "=" in part:
            k, _, v = part.partition("=")
            out[k.strip().lower()] = v.strip()
        else:
            out[part.strip().lower()] = True
    return out


# --- POST /v1/auth/cookie happy path ------------------------------------


@pytest.mark.asyncio
async def test_post_cookie_sets_sb_session_with_required_attributes(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    """Valid JWT → 204 + Set-Cookie with httpOnly + SameSite=Strict + Secure + Path=/ + Max-Age.

    Why: this is the contract the SSE auth path now depends on. If any of
    these attributes silently drop, the cookie either won't ride along
    EventSource (Path) or stops being a credential at all (httpOnly/Secure)
    or becomes cross-site leakable (SameSite).
    """
    r = await api_client.post(
        "/v1/auth/cookie",
        json={"access_token": test_tenant["token"]},
    )
    assert r.status_code == 204, r.text

    set_cookie = r.headers.get("set-cookie")
    assert set_cookie, "expected Set-Cookie header"
    attrs = _cookie_attrs(set_cookie)
    assert attrs["_name"] == "sb_session"
    assert attrs["_value"] == test_tenant["token"]
    assert attrs.get("httponly") is True
    assert attrs.get("samesite", "").lower() == "strict"
    assert attrs.get("secure") is True
    assert attrs.get("path") == "/"
    # Max-Age clamps to >= 0; for a fresh Supabase JWT (1h TTL) it's > 0.
    assert int(attrs["max-age"]) >= 0


@pytest.mark.asyncio
async def test_post_cookie_max_age_matches_jwt_exp_window(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    """Max-Age computed from JWT exp − now (clamped to ≥0).

    Why: a fixed Max-Age would either outlive a short-lived token (window
    of replay after silent expiry) or expire while the JWT is still valid
    (premature re-auth flow). The exp claim is the single source of truth.
    """
    # Decode without verifying signature to read exp — same trick test code
    # could use to assert against.
    claims = pyjwt.decode(test_tenant["token"], options={"verify_signature": False})
    exp_claim = int(claims["exp"])

    before = int(time.time())
    r = await api_client.post(
        "/v1/auth/cookie",
        json={"access_token": test_tenant["token"]},
    )
    after = int(time.time())
    assert r.status_code == 204

    attrs = _cookie_attrs(r.headers["set-cookie"])
    max_age = int(attrs["max-age"])
    # Expected window: exp - after ≤ max_age ≤ exp - before
    assert exp_claim - after <= max_age <= exp_claim - before


# --- DELETE /v1/auth/cookie happy path ----------------------------------


@pytest.mark.asyncio
async def test_delete_cookie_clears_sb_session(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    """DELETE → 204 + Set-Cookie with empty value + Max-Age=0.

    Browsers retire a cookie when they see Max-Age=0 with matching attributes
    (httpOnly/Secure/SameSite/Path). Anything else and the old cookie
    silently lingers in the jar.
    """
    r = await api_client.delete(
        "/v1/auth/cookie",
        headers={"Authorization": f"Bearer {test_tenant['token']}"},
    )
    assert r.status_code == 204, r.text
    set_cookie = r.headers.get("set-cookie")
    assert set_cookie, "expected Set-Cookie header on clear"
    attrs = _cookie_attrs(set_cookie)
    assert attrs["_name"] == "sb_session"
    assert attrs["_value"] == ""
    assert int(attrs["max-age"]) == 0
    assert attrs.get("httponly") is True
    assert attrs.get("samesite", "").lower() == "strict"
    assert attrs.get("secure") is True
    assert attrs.get("path") == "/"


@pytest.mark.asyncio
async def test_delete_cookie_requires_auth(
    api_client: httpx.AsyncClient,
) -> None:
    """Unauthenticated DELETE → 401. Public clear would let an attacker
    log other users out at scale via CSRF.
    """
    r = await api_client.delete("/v1/auth/cookie")
    assert r.status_code == 401


# --- cookie-based principal resolution ----------------------------------


@pytest.mark.asyncio
async def test_cookie_principal_authed_route_resolves(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    """sb_session cookie alone authenticates GET /v1/auth/me — no header needed.

    Why: this is the actual SC-equivalent assertion for EventSource. If the
    cookie path doesn't resolve a principal, every authed route on the portal
    breaks for browser clients.
    """
    # Set the cookie via the real endpoint.
    set_r = await api_client.post(
        "/v1/auth/cookie",
        json={"access_token": test_tenant["token"]},
    )
    assert set_r.status_code == 204

    # httpx strips Secure cookies on http:// (the conftest base URL); pass
    # the cookie value back explicitly to simulate what the browser does
    # on a real HTTPS or localhost connection.
    cookie_attrs = _cookie_attrs(set_r.headers["set-cookie"])
    r = await api_client.get(
        "/v1/auth/me",
        cookies={"sb_session": cookie_attrs["_value"]},
    )
    assert r.status_code == 200, r.text
    assert r.json()["email"] == test_tenant["email"]


# --- precedence edge cases ----------------------------------------------


@pytest.mark.asyncio
async def test_cookie_wins_over_authorization_header(
    api_client: httpx.AsyncClient, test_tenant: dict, outsider: dict
) -> None:
    """When BOTH cookie and Authorization header are present, cookie wins.

    Why: the explicit precedence rule is "cookie → header → API key". If a
    proxy or stale localStorage smuggles in an Authorization header, the
    fresh first-party cookie must still be the identity the server trusts.
    """
    # Cookie = test_tenant; Authorization header = outsider (different user).
    set_r = await api_client.post(
        "/v1/auth/cookie",
        json={"access_token": test_tenant["token"]},
    )
    assert set_r.status_code == 204
    cookie_value = _cookie_attrs(set_r.headers["set-cookie"])["_value"]

    r = await api_client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {outsider['token']}"},
        cookies={"sb_session": cookie_value},
    )
    assert r.status_code == 200, r.text
    # The principal must be test_tenant (cookie owner), not outsider.
    assert r.json()["email"] == test_tenant["email"]


@pytest.mark.asyncio
async def test_empty_cookie_falls_through_to_header(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    """An empty sb_session cookie should NOT short-circuit to a 401 — it's
    not "present", so header path takes over.

    Why: browsers may send `sb_session=` (no value) during expiry transitions
    or after a partial clear. Treating that as a hard failure would lock out
    users mid-refresh; treating it as "not present" lets the header path
    (or a fresh cookie set) recover.
    """
    r = await api_client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {test_tenant['token']}"},
        cookies={"sb_session": ""},
    )
    assert r.status_code == 200, r.text
    assert r.json()["email"] == test_tenant["email"]


@pytest.mark.asyncio
async def test_invalid_cookie_does_not_fall_through_to_header(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    """A present-but-INVALID cookie is a definitive 401. NO fall-through.

    Why: silent fall-through would mask a tampered cookie with a legitimate
    Authorization header — the user thinks they're logged in via cookie when
    they're actually authed via header. That breaks the security model of
    "the cookie IS the session" that the rest of the portal assumes.
    """
    r = await api_client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {test_tenant['token']}"},
        cookies={"sb_session": "not-a-real-jwt"},
    )
    assert r.status_code == 401


# --- POST error paths ----------------------------------------------------


@pytest.mark.asyncio
async def test_post_cookie_invalid_jwt_returns_401_no_cookie(
    api_client: httpx.AsyncClient,
) -> None:
    """Malformed JWT → 401 invalid_token AND no Set-Cookie."""
    r = await api_client.post(
        "/v1/auth/cookie",
        json={"access_token": "not-a-real-jwt"},
    )
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "invalid_token"
    assert r.headers.get("set-cookie") is None


@pytest.mark.asyncio
async def test_post_cookie_expired_jwt_returns_401_no_cookie(
    api_client: httpx.AsyncClient,
) -> None:
    """Expired JWT → 401 token_expired AND no Set-Cookie.

    The exp claim is enforced by `_decode_supabase_jwt`'s HS256 fallback —
    pyjwt raises ExpiredSignatureError when exp < now.
    """
    expired = _make_hs256_jwt(exp_offset=-60)
    r = await api_client.post(
        "/v1/auth/cookie",
        json={"access_token": expired},
    )
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "token_expired"
    assert r.headers.get("set-cookie") is None


@pytest.mark.asyncio
async def test_post_cookie_wrong_audience_returns_401(
    api_client: httpx.AsyncClient,
) -> None:
    """JWT with `aud != "authenticated"` → 401 invalid_token.

    Why: aud is the multi-tenant safety net. A token minted for a different
    Supabase audience must NOT authenticate the portal.
    """
    bad_aud = _make_hs256_jwt(aud="not-authenticated")
    r = await api_client.post(
        "/v1/auth/cookie",
        json={"access_token": bad_aud},
    )
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "invalid_token"


@pytest.mark.asyncio
async def test_post_cookie_wrong_issuer_returns_401(
    api_client: httpx.AsyncClient,
) -> None:
    """JWT with wrong iss → 401 invalid_token.

    Why: iss-pinning prevents tokens from other Supabase projects (e.g. a
    staging stack or someone else's tenant) from authenticating here.
    """
    bad_iss = _make_hs256_jwt(iss="https://attacker.example/auth/v1")
    r = await api_client.post(
        "/v1/auth/cookie",
        json={"access_token": bad_iss},
    )
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "invalid_token"


# --- revocation + replay (T6) -------------------------------------------


@pytest.mark.asyncio
async def test_delete_cookie_revokes_token_blocks_header_replay(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    """T6: after DELETE /v1/auth/cookie, the same JWT must NOT be usable via
    Authorization: Bearer until natural exp.

    Why: clearing only the cookie would let a thief who already captured the
    JWT (via XSS pre-fix, malicious browser extension, etc.) keep using it.
    The blocklist closes that window for the cookie's lifetime.
    """
    # Sanity: token works.
    r = await api_client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {test_tenant['token']}"},
    )
    assert r.status_code == 200

    # Delete the cookie (also revokes).
    r = await api_client.delete(
        "/v1/auth/cookie",
        headers={"Authorization": f"Bearer {test_tenant['token']}"},
    )
    assert r.status_code == 204

    # Same JWT via header must now be rejected.
    # Use a fresh client so no jar-residue cookie sneaks the request through.
    transport = api_client._transport  # ASGITransport
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as fresh:
        r = await fresh.get(
            "/v1/auth/me",
            headers={"Authorization": f"Bearer {test_tenant['token']}"},
        )
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "token_revoked"


# --- SSE integration (cookie-only) --------------------------------------


@pytest.mark.asyncio
async def test_sse_stream_authenticates_on_cookie_alone(
    api_client: httpx.AsyncClient, test_tenant: dict, monkeypatch
) -> None:
    """EventSource-equivalent: the SSE stream route resolves principal from
    cookie alone (no Authorization header, no ?token= URL fallback).

    Mirrors test_portal_stream.py — uses a finite-tail monkeypatch because
    ASGITransport buffers infinite generators.
    """
    import json as _json
    from typing import AsyncIterator

    async def fake_tail(path, **_kwargs) -> AsyncIterator[str]:
        yield f"data: {_json.dumps({'kind': 'render'})}\n\n"

    from src.api.routers import portal as portal_mod
    monkeypatch.setattr(portal_mod, "tail_events_sse", fake_tail)

    # Set the cookie.
    set_r = await api_client.post(
        "/v1/auth/cookie",
        json={"access_token": test_tenant["token"]},
    )
    assert set_r.status_code == 204
    cookie_value = _cookie_attrs(set_r.headers["set-cookie"])["_value"]

    # Hit the stream with NO Authorization header, NO ?token=. Cookie only.
    r = await api_client.get(
        f"/v1/portal/{test_tenant['client_slug']}/stream",
        cookies={"sb_session": cookie_value},
    )
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("text/event-stream")


@pytest.mark.asyncio
async def test_sse_stream_401_after_logout_clear(
    api_client: httpx.AsyncClient, test_tenant: dict, monkeypatch
) -> None:
    """After DELETE /v1/auth/cookie, the SSE reconnect must 401 (cookie
    gone + JWT blocklisted).
    """
    # Set, then delete.
    set_r = await api_client.post(
        "/v1/auth/cookie",
        json={"access_token": test_tenant["token"]},
    )
    assert set_r.status_code == 204
    del_r = await api_client.delete(
        "/v1/auth/cookie",
        headers={"Authorization": f"Bearer {test_tenant['token']}"},
    )
    assert del_r.status_code == 204

    # Reconnect attempt — fresh client to avoid jar-cookie residue.
    transport = api_client._transport
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as fresh:
        r = await fresh.get(
            f"/v1/portal/{test_tenant['client_slug']}/stream",
        )
    assert r.status_code == 401


# --- removal verification (Unit 4 hard requirement) ---------------------


def test_resolve_principal_for_sse_helper_is_removed() -> None:
    """The pre-Unit-4 SSE auth helper must no longer exist in portal.py.

    A grep-equivalent assertion at the source level. If this fires, somebody
    re-introduced the `?token=` URL fallback and the security review needs
    to re-open.
    """
    from src.api.routers import portal as portal_mod

    assert not hasattr(portal_mod, "_resolve_principal_for_sse"), (
        "Unit 4 requires _resolve_principal_for_sse to be removed; "
        "found it in src.api.routers.portal"
    )


def test_portal_stream_signature_has_no_token_query_param() -> None:
    """portal_stream signature must NOT carry a `token` query parameter."""
    import inspect

    from src.api.routers.portal import portal_stream

    sig = inspect.signature(portal_stream)
    assert "token" not in sig.parameters, (
        "Unit 4 requires the ?token= URL fallback removed; "
        f"portal_stream still has parameter `token`: {sig}"
    )
