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
from src.evaluation.structural import structural_gate


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

# Domains routed to scorer_binary.md (v3.3+ 0/0.5/1 + outcome-question shape).
# competitive moved here 2026-05-18 when the CI rubric collapsed from the
# 1/3/5 gradient + checklist 8-criteria shape to the 6-criteria binary
# shape per docs/handoffs/2026-05-17-judge-design-step1-competitive.md.
# monitoring moved here 2026-05-19 when the MON rubric collapsed from the
# 8-criteria gradient/checklist shape to the 6-criteria binary shape per
# docs/handoffs/2026-05-18-judge-design-step1-monitoring.md (v3 — MON-5 +
# MON-6 ship as documented exceptions to the ≤5 criteria ceiling).
# geo + storyboard moved here 2026-05-19 (wiring fix) when their v3 prose
# landed in rubrics.py but routing still went through scorer.md (gradient).
# scorer_binary.md was generalized in the same wiring fix to inject the
# lane's binary_scorer_context + criterion_count from LaneSpec.
_BINARY_DOMAINS: frozenset[str] = frozenset(
    {"competitive", "monitoring", "geo", "storyboard"}
)


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


_DEFAULT_LANE_CONTEXT = (
    "You are scoring an artifact produced by the gofreddy evolution loop. "
    "Score what is in front of you against the criteria below; the judge is "
    "the only thing standing between speculative output and a real deliverable."
)


def _lane_context_for_domain(domain: str) -> str:
    """Return the `binary_scorer_context` from LaneSpec for ``domain``.

    Falls back to ``_DEFAULT_LANE_CONTEXT`` if the lane has no context set or
    the lane_registry import fails. Escapes curly literals so the result can
    be passed through ``str.format()`` as ``{lane_context}`` without
    KeyError on context prose that happens to contain curly braces.
    """
    try:
        from autoresearch.lane_registry import LANES  # noqa: PLC0415
    except Exception:
        return _DEFAULT_LANE_CONTEXT
    spec = LANES.get(domain)
    context = getattr(spec, "binary_scorer_context", "") if spec else ""
    if not context.strip():
        context = _DEFAULT_LANE_CONTEXT
    return context.replace("{", "{{").replace("}", "}}")


def _criterion_count_for_domain(domain: str) -> int:
    """Return the number of rubric criteria registered for ``domain``.

    Used so scorer_binary.md / scorer_templated.md can compute
    ``aggregate_score = sum(per_criterion.score) * 10 / count`` dynamically
    rather than hardcoding ``÷ 6`` (CI). Falls back to 6 if the rubrics
    module is unreachable.
    """
    try:
        from src.evaluation.rubrics import RUBRICS  # noqa: PLC0415
    except Exception:
        return 6
    count = sum(1 for r in RUBRICS.values() if r.domain == domain)
    return count if count > 0 else 6


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
    # v3.3+: binary-shape lanes enable the expanded deterministic
    # structural_gate (CI_STRUCTURAL_V33=1) which adds 9+ anti-hallucination /
    # shape checks on top of the legacy 2-check default. Setting the env var
    # in-process is safe because structural_gate reads it on each call.
    if domain in _BINARY_DOMAINS:
        os.environ["CI_STRUCTURAL_V33"] = "1"
    if domain in _BINARY_DOMAINS:
        prompt = _load_binary_prompt().format(
            lane_context=_lane_context_for_domain(domain),
            criteria=_render_criteria_for_domain(domain),
            domain=domain,
            fixture=json.dumps(payload.get("fixture", {}), sort_keys=True),
            session_ref=payload.get("session_ref", ""),
            artifacts=json.dumps(payload.get("artifacts", {}), sort_keys=True),
        )
    elif domain in _TEMPLATED_DOMAINS:
        prompt = _load_templated_prompt().format(
            lane_context=_lane_context_for_domain(domain),
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
    artifacts_obj = payload.get("artifacts", {})

    # Run deterministic structural_gate in parallel with the judges. For
    # v3.3+ binary-shape lanes this is the 11-check anti-hallucination /
    # shape pass; for other lanes it falls through to the legacy shape
    # checks. The judge's self-reported `structural_passed` is preserved
    # in the per-family blocks but the aggregate now ANDs the
    # deterministic verdict in so a judge can't override a structural
    # failure.
    structural_outputs: dict[str, str] = (
        {k: v for k, v in artifacts_obj.items() if isinstance(v, str)}
        if isinstance(artifacts_obj, dict)
        else {}
    )
    primary_stdout, secondary_stdout, structural_result = await asyncio.gather(
        primary_invoker(prompt),
        secondary_invoker(prompt),
        structural_gate(domain, structural_outputs),
    )
    primary = _extract_json(primary_stdout, primary_family)
    secondary = _extract_json(secondary_stdout, secondary_family)

    try:
        p_score = float(primary.get("aggregate_score", 0.0) or 0.0)
        s_score = float(secondary.get("aggregate_score", 0.0) or 0.0)
        mean = (p_score + s_score) / 2.0
    except (TypeError, ValueError):
        mean = 0.0

    # Deterministic gate is authoritative: if structural_result.passed is
    # False the variant cannot be marked structural_passed=True regardless
    # of what the judges reported. Failure list surfaces for downstream
    # eval_digest visibility.
    structural_passed = bool(
        structural_result.passed
        and primary.get("structural_passed", True)
        and secondary.get("structural_passed", True)
    )
    aggregate = {
        "fixture_id": primary.get("fixture_id") or secondary.get("fixture_id"),
        "domain": payload.get("domain"),
        "aggregate_score": mean,
        "structural_passed": structural_passed,
        "structural_failures": list(structural_result.failures),
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
