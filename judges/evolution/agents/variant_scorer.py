"""Per-fixture variant scorer.

Invokes both the claude (primary) and codex (secondary) CLIs on the
scorer prompt. Returns per-family fixture scores plus simple aggregates.
Parse failures raise RuntimeError — the service surfaces these as 5xx
and the autoresearch client logs ``judge_unreachable``.
"""
from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import Any

from judges.invoke_cli import invoke_claude, invoke_codex


_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "scorer.md"
_JSON_BLOCK = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


def _load_prompt() -> str:
    return _PROMPT_PATH.read_text()


def _extract_json(text: str, family: str) -> dict[str, Any]:
    match = _JSON_BLOCK.search(text)
    raw = match.group(1) if match else text.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"variant_scorer[{family}]: could not parse JSON verdict: {exc}"
        ) from exc


async def score_variant(payload: dict[str, Any]) -> dict[str, Any]:
    """Score a variant session artifact set.

    Payload: ``{session_ref, domain, fixture, lane, seeds, artifacts?}``.
    Returns ``{primary, secondary, aggregate}`` where primary/secondary
    are per-family scoring dicts and aggregate is the mean score across
    families with the union of structural/grounding flags.
    """
    prompt = _load_prompt().format(
        domain=payload.get("domain", ""),
        fixture=json.dumps(payload.get("fixture", {}), sort_keys=True),
        session_ref=payload.get("session_ref", ""),
        artifacts=json.dumps(payload.get("artifacts", {}), sort_keys=True),
    )
    primary_stdout, secondary_stdout = await asyncio.gather(
        invoke_claude(prompt),
        invoke_codex(prompt),
    )
    primary = _extract_json(primary_stdout, "claude")
    secondary = _extract_json(secondary_stdout, "codex")

    try:
        p_score = float(primary.get("aggregate_score", 0.0) or 0.0)
        s_score = float(secondary.get("aggregate_score", 0.0) or 0.0)
        mean = (p_score + s_score) / 2.0
    except (TypeError, ValueError):
        mean = 0.0

    aggregate = {
        "fixture_id": primary.get("fixture_id") or secondary.get("fixture_id"),
        "domain": payload.get("domain"),
        "aggregate_score": mean,
        "structural_passed": bool(
            primary.get("structural_passed") and secondary.get("structural_passed")
        ),
        "grounding_passed": bool(
            primary.get("grounding_passed") and secondary.get("grounding_passed")
        ),
    }
    return {"primary": primary, "secondary": secondary, "aggregate": aggregate}
