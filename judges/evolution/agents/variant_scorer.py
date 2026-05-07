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


_PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"
_PROMPT_PATH = _PROMPT_DIR / "scorer.md"
_PROMPT_PATH_TEMPLATED = _PROMPT_DIR / "scorer_templated.md"
_JSON_BLOCK = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)

# Domains whose rubric criteria are JR-private (no LLM prior on the rubric ID
# names like "X-1", "LI-3"). These domains route to the parameterized
# scorer_templated.md prompt with criteria injected from src.evaluation.rubrics.
# Existing 4 lanes (geo/competitive/monitoring/storyboard) keep using scorer.md
# unchanged — they have a public-domain prior on the domain name and the
# 8-criteria rubric shape; switching them silently degrades baselines.
# Round-6 #11 trim: ONE parameterized template for all templated domains, not
# per-domain prompt files.
_TEMPLATED_DOMAINS: frozenset[str] = frozenset({"x_engine", "linkedin_engine"})


def _load_prompt() -> str:
    return _PROMPT_PATH.read_text()


def _load_templated_prompt() -> str:
    return _PROMPT_PATH_TEMPLATED.read_text()


def _render_criteria_for_domain(domain: str) -> str:
    """Concatenate the rubric prose blocks for ``domain`` from the central
    RUBRICS registry, with curly-brace literals escaped so the result can be
    passed through ``str.format()`` as the ``{criteria}`` value without
    `IndexError` on the rubric prose's own example JSON.
    """
    # Local import to keep the judge service free of an import-time dep on the
    # evaluation package; the helper is only called when a templated-domain
    # request lands.
    from src.evaluation.rubrics import RUBRICS  # noqa: PLC0415

    blocks: list[str] = []
    for rubric in sorted(
        (r for r in RUBRICS.values() if r.domain == domain),
        key=lambda r: r.criterion_id,
    ):
        blocks.append(f"## {rubric.criterion_id}\n\n{rubric.prompt}\n")
    if not blocks:
        raise RuntimeError(
            f"variant_scorer: no rubrics registered for domain {domain!r} "
            f"(RUBRICS lookup returned 0 entries)"
        )
    rendered = "\n".join(blocks)
    # Escape curly literals in the rubric prose so the outer .format() call
    # treats them as literals, not format placeholders. Idempotent because
    # the prose itself never contains pre-escaped braces.
    return rendered.replace("{", "{{").replace("}", "}}")


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
    domain = payload.get("domain", "")
    if domain in _TEMPLATED_DOMAINS:
        prompt = _load_templated_prompt().format(
            criteria=_render_criteria_for_domain(domain),
            domain=domain,
            fixture=json.dumps(payload.get("fixture", {}), sort_keys=True),
            session_ref=payload.get("session_ref", ""),
            artifacts=json.dumps(payload.get("artifacts", {}), sort_keys=True),
        )
    else:
        prompt = _load_prompt().format(
            domain=domain,
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
