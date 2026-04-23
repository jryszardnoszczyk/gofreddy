"""Promotion-judge client: autonomous promote/rollback/canary decisions.

Thin HTTP client for the evolution-judge-service `/invoke/decide/{role}`
endpoint. Cross-family by judge-service configuration (Claude Opus 4.7 vs.
the primary gpt-5.4 scorer); the cross-family property is enforced on the
judge-service side, not here.

On outage (connection error, non-2xx, timeout, malformed JSON): emit
``kind="judge_unreachable"`` to the autoresearch events log and raise
``JudgeUnreachable``. Matches Plan A Phase 0c: no threshold fallback.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

import httpx


EVOLUTION_JUDGE_URL = os.environ.get("EVOLUTION_JUDGE_URL", "http://localhost:7200")
EVOLUTION_INVOKE_TOKEN = os.environ.get("EVOLUTION_INVOKE_TOKEN", "")


_DECISION_ROLES = {"promotion", "rollback", "canary"}


class JudgeUnreachable(RuntimeError):
    """Evolution-judge service did not return a parseable verdict. Halt + re-run."""
    pass


@dataclass(frozen=True)
class PromotionVerdict:
    """Role-dependent verdict. See Plan B Phase 0b PromotionVerdict for
    the full per-role value table. Stored as an opaque string so new
    verdict values ship on the judge-service side without autoresearch
    changes.

    ``concerns`` is a list of either plain-string concern labels or dicts
    with at minimum a ``severity`` key. Phase 6 ``is_promotable`` gates on
    dict-shaped concerns whose severity is ``"blocking"``.
    """
    decision: str
    reasoning: str
    confidence: float
    concerns: list = field(default_factory=list)


def call_promotion_judge(payload: dict[str, Any]) -> PromotionVerdict:
    """POST the promotion-judge role endpoint and parse the verdict."""
    from autoresearch.events import log_event

    role = payload.get("role", "promotion")
    if role not in _DECISION_ROLES:
        raise ValueError(f"invalid decision role: {role!r}")
    try:
        r = httpx.post(
            f"{EVOLUTION_JUDGE_URL}/invoke/decide/{role}",
            json=payload,
            headers={"Authorization": f"Bearer {EVOLUTION_INVOKE_TOKEN}"},
            timeout=300,
        )
        r.raise_for_status()
        data = r.json()
    except (httpx.HTTPError, ValueError) as exc:
        log_event(
            kind="judge_unreachable",
            endpoint=f"/invoke/decide/{role}",
            error_class=type(exc).__name__,
            error=str(exc)[:500],
        )
        raise JudgeUnreachable(f"evolution-judge unreachable: {exc}") from exc
    return PromotionVerdict(
        decision=str(data["decision"]),
        reasoning=str(data.get("reasoning", "")),
        confidence=float(data.get("confidence", 0.5)),
        concerns=list(data.get("concerns", [])),
    )
