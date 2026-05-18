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
_PROMPT_PATH_BINARY = _PROMPT_DIR / "scorer_binary.md"
_JSON_BLOCK = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)

# Domains whose rubric criteria are JR-private (no LLM prior on the rubric ID
# names like "X-1", "LI-3"). These domains route to the parameterized
# scorer_templated.md prompt with criteria injected from src.evaluation.rubrics.
# Existing 3 of the original 4 public-prior lanes (geo/monitoring/storyboard)
# keep using scorer.md unchanged.
# Round-6 #11 trim: ONE parameterized template for all templated domains, not
# per-domain prompt files.
_TEMPLATED_DOMAINS: frozenset[str] = frozenset({"x_engine", "linkedin_engine"})

# Domains routed to scorer_binary.md (v3.3 0/0.5/1 + outcome-question shape).
# competitive moved here 2026-05-18 when the CI rubric collapsed from the
# 1/3/5 gradient + checklist 8-criteria shape to the 6-criteria binary
# shape per docs/handoffs/2026-05-17-judge-design-step1-competitive.md.
# Other 3 lanes stay on scorer.md until each gets the v3.3-equivalent
# Path-A iteration of its own.
_BINARY_DOMAINS: frozenset[str] = frozenset({"competitive"})


def _load_prompt() -> str:
    return _PROMPT_PATH.read_text()


def _load_templated_prompt() -> str:
    return _PROMPT_PATH_TEMPLATED.read_text()


def _load_binary_prompt() -> str:
    return _PROMPT_PATH_BINARY.read_text()


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


_INVOKERS_BY_FAMILY = {
    "claude": invoke_claude,
    "codex": invoke_codex,
    "opencode": invoke_opencode,
}


def _resolve_judge(env_var: str, default: str) -> tuple[str, "asyncio.Future"]:
    """Return ``(family_label, invoker)`` for primary or secondary judge.

    Read from ``env_var``; fall back to ``default``. Family must be one of
    claude/codex/opencode.
    """
    family = os.environ.get(env_var, default).strip().lower()
    invoker = _INVOKERS_BY_FAMILY.get(family)
    if invoker is None:
        raise RuntimeError(
            f"{env_var}={family!r} unsupported (must be claude/codex/opencode)"
        )
    return family, invoker


def _resolve_primary() -> tuple[str, "asyncio.Future"]:
    """Primary judge for variant scoring. Default ``claude`` preserves
    prior behavior. Override via ``EVOLUTION_JUDGE_PRIMARY=codex`` to
    flip the cross-family pairing (the geo lane runs claude inner today,
    so a codex primary judge eliminates same-family preference leakage)."""
    return _resolve_judge("EVOLUTION_JUDGE_PRIMARY", "claude")


def _resolve_secondary() -> tuple[str, "asyncio.Future"]:
    """Secondary judge. Default ``codex`` preserves prior behavior."""
    return _resolve_judge("EVOLUTION_JUDGE_SECONDARY", "codex")


async def score_variant(payload: dict[str, Any]) -> dict[str, Any]:
    """Score a variant session artifact set.

    Payload: ``{session_ref, domain, fixture, lane, seeds, artifacts?}``.
    Returns ``{primary, secondary, aggregate}`` where primary/secondary
    are per-family scoring dicts and aggregate is the mean score across
    families with the union of structural/grounding flags.
    """
    domain = payload.get("domain", "")
    if domain in _BINARY_DOMAINS:
        prompt = _load_binary_prompt().format(
            criteria=_render_criteria_for_domain(domain),
            domain=domain,
            fixture=json.dumps(payload.get("fixture", {}), sort_keys=True),
            session_ref=payload.get("session_ref", ""),
            artifacts=json.dumps(payload.get("artifacts", {}), sort_keys=True),
        )
    elif domain in _TEMPLATED_DOMAINS:
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
    primary_family, primary_invoker = _resolve_primary()
    secondary_family, secondary_invoker = _resolve_secondary()
    if primary_family == secondary_family:
        raise RuntimeError(
            f"Primary and secondary judges must differ to avoid same-family "
            f"preference leakage (both = {primary_family!r}). "
            f"Set EVOLUTION_JUDGE_PRIMARY and EVOLUTION_JUDGE_SECONDARY to "
            f"different families."
        )
    primary_stdout, secondary_stdout = await asyncio.gather(
        primary_invoker(prompt),
        secondary_invoker(prompt),
    )
    primary = _extract_json(primary_stdout, primary_family)
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
    result: dict[str, Any] = {"primary": primary, "secondary": secondary, "aggregate": aggregate}
    # Stream C C4-lean part 1: stamp current RUBRIC_VERSION onto the response
    # so consumers (`evaluate_variant._check_rubric_hash`) can detect when a
    # cached judgment was made against a stale rubric. Soft-fail when the
    # rubrics module isn't importable.
    try:
        from src.evaluation.rubrics import RUBRIC_VERSION  # noqa: PLC0415
        result["rubric_hash"] = RUBRIC_VERSION
    except Exception:
        pass
    return result
