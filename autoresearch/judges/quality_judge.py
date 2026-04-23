"""Quality-judge client: advisory system-health decisions.

Thin HTTP client for the evolution-judge-service `/invoke/system_health/{role}`
endpoint. The unified ``system_health_agent`` on the judge-service decides;
this module only builds the request and parses the response.

Roles: fixture_quality | saturation | calibration_drift | content_drift |
discriminability | noise_escalation.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx


EVOLUTION_JUDGE_URL = os.environ.get("EVOLUTION_JUDGE_URL", "http://localhost:7200")
EVOLUTION_INVOKE_TOKEN = os.environ.get("EVOLUTION_INVOKE_TOKEN", "")


_SYSTEM_HEALTH_ROLES = {
    "saturation", "content_drift", "discriminability",
    "fixture_quality", "calibration_drift", "noise_escalation",
}


@dataclass(frozen=True)
class QualityVerdict:
    """Role-dependent verdict. See Plan B Phase 0b QualityVerdict for
    the full per-role value table. Kept as an opaque string here so new
    verdict values ship on the judge-service side without autoresearch
    changes.
    """
    verdict: str
    reasoning: str
    confidence: float
    recommended_action: str | None = None


def call_quality_judge(payload: dict[str, Any]) -> QualityVerdict:
    """POST the quality-judge role endpoint and parse the verdict."""
    role = payload.get("role")
    if role not in _SYSTEM_HEALTH_ROLES:
        raise ValueError(f"invalid system_health role: {role!r}")
    r = httpx.post(
        f"{EVOLUTION_JUDGE_URL}/invoke/system_health/{role}",
        json=payload,
        headers={"Authorization": f"Bearer {EVOLUTION_INVOKE_TOKEN}"},
        timeout=300,
    )
    r.raise_for_status()
    data = r.json()
    return QualityVerdict(
        verdict=str(data["verdict"]),
        reasoning=str(data.get("reasoning", "")),
        confidence=float(data.get("confidence", 0.5)),
        recommended_action=data.get("recommended_action"),
    )
