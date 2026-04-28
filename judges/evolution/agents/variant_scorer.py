"""Per-fixture variant scorer.

Invokes the claude (primary) CLI and one secondary CLI on the scorer
prompt. The secondary family defaults to ``codex`` and can be flipped to
``opencode`` via the ``EVOLUTION_JUDGE_SECONDARY`` env var (e.g. when
ChatGPT Plus is at quota and openrouter/deepseek is healthier). Parse
failures raise RuntimeError — the service surfaces these as 5xx and the
autoresearch client logs ``judge_unreachable``.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
from pathlib import Path
from typing import Any

from judges.invoke_cli import invoke_claude, invoke_codex, invoke_opencode


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


def _resolve_secondary() -> tuple[str, "asyncio.Future"]:
    """Return ``(family_label, invoker)`` for the secondary judge.

    Driven by ``EVOLUTION_JUDGE_SECONDARY`` env var. Default ``codex``
    preserves prior behavior. Set ``opencode`` to route through OpenRouter
    (e.g. openrouter/deepseek/deepseek-v4-pro) when codex is unavailable.
    """
    family = os.environ.get("EVOLUTION_JUDGE_SECONDARY", "codex").strip().lower()
    if family == "opencode":
        return "opencode", invoke_opencode
    if family == "codex":
        return "codex", invoke_codex
    raise RuntimeError(
        f"EVOLUTION_JUDGE_SECONDARY={family!r} unsupported (must be 'codex' or 'opencode')"
    )


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
    secondary_family, secondary_invoker = _resolve_secondary()
    primary_stdout, secondary_stdout = await asyncio.gather(
        invoke_claude(prompt),
        secondary_invoker(prompt),
    )
    primary = _extract_json(primary_stdout, "claude")
    secondary = _extract_json(secondary_stdout, secondary_family)

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
