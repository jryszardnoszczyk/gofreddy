"""Role-locked FastAPI server for the judge services.

One implementation, two deployments: the ``JUDGE_MODE`` env var (``session``
or ``evolution``) decides which routes are live on this host. Cross-mode
requests return 404 with a short diagnostic.

All request bodies are dicts; no Pydantic models. Prompts and credentials
never cross this HTTP boundary — payloads from autoresearch name only
session_ref / domain / fixture / etc., and the service reads files + holds
credentials locally.

Events audit trail: every ``/invoke/*`` call logs
``autoresearch.events.log_event(kind="judge_audit", mode=..., endpoint=...,
payload_hash=..., verdict=...)`` on the judge-service host's events log.
Full reasoning stays inside the returned verdict body.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Optional

from fastapi import FastAPI, Header, HTTPException

from autoresearch.events import log_event


def _payload_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str).encode()
    return hashlib.sha256(encoded).hexdigest()[:16]


def create_app(*, mode: Optional[str] = None, invoke_token: Optional[str] = None) -> FastAPI:
    """Build a FastAPI app locked to one mode.

    Mode + token read from args first, then env (``JUDGE_MODE``, ``INVOKE_TOKEN``).
    No default — missing config raises on app construction, same as the
    daemon would at startup.
    """
    resolved_mode = mode or os.environ.get("JUDGE_MODE")
    if resolved_mode not in ("session", "evolution"):
        raise RuntimeError(
            f"judges.server: JUDGE_MODE must be 'session' or 'evolution', got {resolved_mode!r}"
        )
    resolved_token = invoke_token or os.environ.get("INVOKE_TOKEN", "")

    app = FastAPI(
        title=f"gofreddy-{resolved_mode}-judge",
        description="Role-locked judge service. No runtime mutation.",
    )
    app.state.mode = resolved_mode
    app.state.invoke_token = resolved_token

    def _require_token(authorization: Optional[str]) -> None:
        expected = f"Bearer {app.state.invoke_token}"
        if not authorization or authorization != expected:
            raise HTTPException(status_code=401, detail="invalid token")

    def _audit(kind: str, endpoint: str, payload: Any, verdict: Any) -> None:
        log_event(
            kind=kind,
            mode=app.state.mode,
            endpoint=endpoint,
            payload_hash=_payload_hash(payload),
            verdict=verdict,
        )

    # ─── session-only endpoints ────────────────────────────────────────
    if resolved_mode == "session":
        from judges.session.agents import review_agent, critique_agent

        @app.post("/invoke/review")
        async def invoke_review(
            payload: dict, authorization: Optional[str] = Header(None),
        ) -> dict:
            _require_token(authorization)
            verdict = await review_agent.review(payload)
            _audit("judge_audit", "/invoke/review", payload, verdict)
            return verdict

        @app.post("/invoke/critique")
        async def invoke_critique(
            payload: dict, authorization: Optional[str] = Header(None),
        ) -> dict:
            _require_token(authorization)
            verdict = await critique_agent.critique(payload)
            _audit("judge_audit", "/invoke/critique", payload, verdict)
            return verdict

    # ─── evolution-only endpoints ──────────────────────────────────────
    if resolved_mode == "evolution":
        from judges.evolution.agents import (
            variant_scorer,
            promotion_agent,
            rollback_agent,
            canary_agent,
            system_health_agent,
        )

        @app.post("/invoke/score")
        async def invoke_score(
            payload: dict, authorization: Optional[str] = Header(None),
        ) -> dict:
            _require_token(authorization)
            verdict = await variant_scorer.score_variant(payload)
            _audit("judge_audit", "/invoke/score", payload, verdict)
            return verdict

        @app.post("/invoke/decide/promotion")
        async def invoke_decide_promotion(
            payload: dict, authorization: Optional[str] = Header(None),
        ) -> dict:
            _require_token(authorization)
            verdict = await promotion_agent.decide(payload)
            _audit("judge_audit", "/invoke/decide/promotion", payload, verdict)
            return verdict

        @app.post("/invoke/decide/rollback")
        async def invoke_decide_rollback(
            payload: dict, authorization: Optional[str] = Header(None),
        ) -> dict:
            _require_token(authorization)
            verdict = await rollback_agent.decide(payload)
            _audit("judge_audit", "/invoke/decide/rollback", payload, verdict)
            return verdict

        @app.post("/invoke/decide/canary")
        async def invoke_decide_canary(
            payload: dict, authorization: Optional[str] = Header(None),
        ) -> dict:
            _require_token(authorization)
            verdict = await canary_agent.decide(payload)
            _audit("judge_audit", "/invoke/decide/canary", payload, verdict)
            return verdict

        @app.post("/invoke/system_health/{role}")
        async def invoke_system_health(
            role: str,
            payload: dict,
            authorization: Optional[str] = Header(None),
        ) -> Any:
            _require_token(authorization)
            if role not in system_health_agent.ROLES:
                raise HTTPException(
                    status_code=404,
                    detail=f"unknown system_health role: {role}",
                )
            verdict = await system_health_agent.evaluate(role, payload)
            _audit(
                "judge_audit",
                f"/invoke/system_health/{role}",
                payload,
                verdict,
            )
            return verdict

    return app


# ─── module-level app for `python -m judges.server` / uvicorn ──────────

_BUILT_APP: Optional[FastAPI] = None


def _get_app() -> FastAPI:
    global _BUILT_APP
    if _BUILT_APP is None:
        _BUILT_APP = create_app()
    return _BUILT_APP


def __getattr__(name: str):  # pragma: no cover — loader hook
    if name == "app":
        return _get_app()
    raise AttributeError(name)


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    port = int(os.environ.get("JUDGE_PORT", "7100"))
    uvicorn.run(_get_app(), host="127.0.0.1", port=port)
