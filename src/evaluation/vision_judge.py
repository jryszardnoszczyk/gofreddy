"""Multimodal vision sub-judge for image_engine (D24 / U14).

Per D24 + JR's 2026-05-19 model-update: visual rubrics (IE-1 hook
visual, IE-2 brand consistency, IE-3 info density legibility, IE-5
visual specificity, IE-6 carousel arc) are scored by Gemini 3 Flash
Preview through this primitive. Text-only rubrics (IE-4 format
compliance, IE-7 alt-text + voice-consistent caption, IE-8
repurposability) continue through claude/opus via the existing outer
judge service — this module ONLY handles visual rubrics.

The plan reference D24 originally specified Gemini 2.5; JR updated
the backend to Gemini 3 Flash Preview during U14 design. The DI
pattern (`call_gemini` callable) is unchanged — only the production
backend's model identifier shifts when U18 wires the real client.

This is NOT a wrapper around `image_preview_service.verify_preview()`
(which is a fixed 2-axis preview QA tool). vision_judge is a fresh,
rubric-driven multimodal judge; the two coexist as siblings.

Per JR's 2026-05-19 U14 decision: dependency-injected `call_gemini`
callable so the contract is testable without binding to a specific
SDK or CLI. Production wiring lands in U18 alongside the operator's
gemini invocation pattern (same shape as U13's citation_verifier).
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)


# Per-rubric dimension lists — operationalized scoring sub-axes the
# Gemini 3 Flash Preview prompt asks for. Per the plan §vision-judge
# prompt architecture (TD-41 refined): each visual rubric scores along
# multiple sub-dimensions so the operator + outer composite can audit
# WHY a score landed. Non-visual rubric IDs are not handled here.
_RUBRIC_DIMENSIONS: dict[str, tuple[str, ...]] = {
    "IE-1": ("stop_scroll_strength", "focal_clarity", "thumbnail_legibility"),
    "IE-2": (
        "palette_fidelity", "typography_consistency",
        "logo_treatment", "iconography_register",
    ),
    "IE-3": (
        "legibility_at_thumbnail", "whitespace_balance", "hierarchy_clarity",
    ),
    "IE-5": (
        "concept_concreteness", "absence_of_generic_filler", "metaphor_strength",
    ),
    "IE-6": ("cover_hook", "slide_pacing", "payoff_strength", "cta_clarity"),
}


VISUAL_RUBRIC_IDS: frozenset[str] = frozenset(_RUBRIC_DIMENSIONS)
"""Rubric IDs this judge handles. evaluate_variant dispatches to
vision_judge only for these; other IE-* + AE-* + etc. route through
the existing text-only judge service."""


class VisionJudgeError(Exception):
    """Raised on hard misuse: unknown rubric_id, missing images, or
    missing call_gemini. Operational failures return a degraded
    `VisionScore` instead of raising — same pattern as
    citation_verifier."""


@dataclass(frozen=True)
class VisionScore:
    """Outcome of one vision-judge call.

    Mirrors the shape `evaluate_variant.py` expects from any rubric:
    a scalar score on the rubric's scale, a rationale string for
    operator audit, and per-dimension subscores for diagnostic
    visibility. `failure_modes_observed` captures any
    `anti_patterns.yml` IDs the judge identified — non-empty list
    caps the IE-5 score at 4 per TD-41."""

    rubric_id: str
    score: float
    rationale: str
    dimension_scores: dict[str, float] = field(default_factory=dict)
    failure_modes_observed: list[str] = field(default_factory=list)
    degraded: bool = False


def _build_vision_prompt(
    rubric_id: str,
    rubric_prose: str,
    context: dict,
    anti_patterns: list[dict] | None,
) -> str:
    """Compose the Gemini 3 Flash Preview prompt.

    Sections (per TD-41 vision-judge architecture):
    - SYSTEM: scoring instructions + JSON-only output contract.
    - BRAND TOKENS: palette hex + typography family + logo position.
      Per TD-41: hex codes (NOT swatch images) — Flux/Gemini both
      handle exact-hex brand color specs better than raster swatches.
    - CONTEXT: topic, voice persona excerpt, format + dims, slide
      n/m for carousels.
    - RUBRIC: the IE-{n} anchor prose verbatim.
    - DIMENSIONS: per-rubric sub-axes the model must score.
    - ANTI-PATTERNS: catalogued failure modes the model checks for.
    """
    dims = _RUBRIC_DIMENSIONS[rubric_id]

    parts = [
        "SYSTEM: You are a visual judge scoring images against a single "
        "rubric. Score on the rubric's scale (1-5 or 0-10 — see the "
        "rubric prose). Output ONLY valid JSON; no preamble.",
        "",
        f"BRAND TOKENS: {json.dumps(context.get('brand_tokens', {}))}",
        f"CONTEXT: topic={context.get('topic', '')!r}; "
        f"voice_persona_excerpt={context.get('voice_excerpt', '')[:600]!r}; "
        f"format={context.get('format', '')!r}; "
        f"dimensions={context.get('image_dims', '')!r}; "
        f"slide={context.get('slide_index', '')}/{context.get('slide_count', '')}",
        "",
        f"RUBRIC ({rubric_id}):",
        rubric_prose.strip(),
        "",
        f"DIMENSIONS — score each on the rubric's scale: {list(dims)}",
    ]

    if anti_patterns:
        chunks = [
            f"- {entry.get('name', '<unnamed>')}: {entry.get('why', '')}"
            for entry in anti_patterns
            if isinstance(entry, dict)
        ]
        parts.append("")
        parts.append(
            "ANTI-PATTERNS (catalogued). For each, observe whether the "
            "image exhibits it; list IDs in failure_modes_observed:"
        )
        parts.extend(chunks)

    parts.extend([
        "",
        "Return JSON ONLY in this exact shape:",
        '{"score": <number>, "dimension_scores": {<dim>: <number>, ...}, '
        '"rationale": "<one-sentence explanation>", '
        '"failure_modes_observed": [<pattern_id>, ...]}',
    ])
    return "\n".join(parts)


_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


def _parse_gemini_response(raw: str) -> dict:
    """Extract the JSON object from gemini's response. Tolerates
    ```json fences + leading prose since gemini occasionally wraps."""
    match = _JSON_OBJECT_RE.search(raw)
    if not match:
        raise ValueError(f"no JSON object found in gemini response: {raw[:200]!r}")
    return json.loads(match.group(0))


def vision_judge(
    rubric_id: str,
    rubric_prose: str,
    image_paths: list[Path],
    *,
    call_gemini: Callable[[str, list[Path]], str],
    context: dict | None = None,
    anti_patterns: list[dict] | None = None,
) -> VisionScore:
    """Score images against a visual rubric using Gemini 3 Flash
    Preview (or a test fake via the call_gemini DI).

    Args:
        rubric_id: one of {"IE-1", "IE-2", "IE-3", "IE-5", "IE-6"}.
            Other rubric IDs raise VisionJudgeError.
        rubric_prose: the rubric's anchor prose (from
            src.evaluation.rubrics RUBRICS[rubric_id].prompt).
        image_paths: list of PNG/JPG paths to evaluate. Multi-image
            for carousel rubrics (IE-6 rolls up); single-image for
            others.
        call_gemini: callable taking (prompt, image_paths) and
            returning gemini's text response. REQUIRED — no default
            until U18 wires the production Gemini 3 Flash Preview
            backend. Same DI pattern as citation_verifier's
            call_claude.
        context: dict carrying brand_tokens, topic, voice_excerpt,
            format, image_dims, slide_index, slide_count. Slotted
            into the prompt.
        anti_patterns: anti-patterns.yml records (list of
            {name, regex, why} dicts). The prompt asks gemini to
            identify hits; results land in
            `failure_modes_observed`.

    Returns:
        `VisionScore` with score + dimension_scores + rationale +
        failure_modes_observed. On gemini call failure or parse
        failure, returns a degraded result (mirrors
        citation_verifier semantics — operationally common; flagged
        for human review, not a hard fail).

    Raises:
        VisionJudgeError on misuse: unknown rubric_id (not visual),
        empty image_paths, missing call_gemini.
    """
    if rubric_id not in VISUAL_RUBRIC_IDS:
        raise VisionJudgeError(
            f"rubric_id {rubric_id!r} is not a visual rubric. vision_judge "
            f"handles only {sorted(VISUAL_RUBRIC_IDS)}; route others through "
            f"the text-only judge service."
        )
    if not image_paths:
        raise VisionJudgeError(
            "image_paths is empty. Pass at least one PNG/JPG path."
        )
    if call_gemini is None:
        raise VisionJudgeError(
            "call_gemini is required. Pass a callable that takes (prompt, "
            "image_paths) and returns gemini's text response. Production "
            "wiring (Gemini 3 Flash Preview) lands in U18."
        )

    ctx = context or {}
    prompt = _build_vision_prompt(rubric_id, rubric_prose, ctx, anti_patterns)

    try:
        raw_response = call_gemini(prompt, image_paths)
    except Exception as exc:
        logger.warning(
            "vision_judge: gemini call failed for %s (%s); returning degraded",
            rubric_id, exc,
        )
        return VisionScore(
            rubric_id=rubric_id,
            score=0.0,
            rationale=f"gemini call failed: {exc}",
            dimension_scores={},
            failure_modes_observed=[],
            degraded=True,
        )

    try:
        parsed = _parse_gemini_response(raw_response)
    except (ValueError, KeyError, TypeError) as exc:
        logger.warning(
            "vision_judge: gemini response unparseable for %s (%s); "
            "returning degraded",
            rubric_id, exc,
        )
        return VisionScore(
            rubric_id=rubric_id,
            score=0.0,
            rationale=f"gemini response unparseable: {exc}",
            dimension_scores={},
            failure_modes_observed=[],
            degraded=True,
        )

    dim_scores_raw = parsed.get("dimension_scores", {})
    if not isinstance(dim_scores_raw, dict):
        dim_scores_raw = {}
    dim_scores = {
        str(k): float(v)
        for k, v in dim_scores_raw.items()
        if isinstance(v, (int, float))
    }

    failure_modes = parsed.get("failure_modes_observed", [])
    if not isinstance(failure_modes, list):
        failure_modes = []
    failure_modes = [str(m) for m in failure_modes]

    return VisionScore(
        rubric_id=rubric_id,
        score=float(parsed.get("score", 0.0)),
        rationale=str(parsed.get("rationale", "")),
        dimension_scores=dim_scores,
        failure_modes_observed=failure_modes,
        degraded=False,
    )


def roll_up_carousel(scores: list[VisionScore]) -> VisionScore:
    """Per TD-41: carousel-level rubrics (IE-6) take per-slide scores
    and roll them up via `mean(dimension_scores) + min(score) gate` —
    one weak slide drags the whole carousel score.

    The roll-up returns a synthetic VisionScore with the same shape;
    `score` = min across slides (gate); `dimension_scores` = mean per
    dimension; `rationale` = synthesis of per-slide rationales;
    `failure_modes_observed` = union across slides; `degraded` =
    True if ANY slide was degraded.
    """
    if not scores:
        raise VisionJudgeError("roll_up_carousel needs at least one score")

    rubric_id = scores[0].rubric_id
    if not all(s.rubric_id == rubric_id for s in scores):
        raise VisionJudgeError(
            "roll_up_carousel slices must all be the same rubric_id"
        )

    # min gate on the overall score
    min_score = min(s.score for s in scores)

    # mean across dimensions
    all_dims: dict[str, list[float]] = {}
    for s in scores:
        for dim, val in s.dimension_scores.items():
            all_dims.setdefault(dim, []).append(val)
    dim_means = {dim: sum(vs) / len(vs) for dim, vs in all_dims.items()}

    # failure modes — union
    failure_union: list[str] = []
    seen: set[str] = set()
    for s in scores:
        for mode in s.failure_modes_observed:
            if mode not in seen:
                failure_union.append(mode)
                seen.add(mode)

    degraded = any(s.degraded for s in scores)

    # rationale — bullet per slide
    rationale_lines = [
        f"- slide {i + 1}: {s.rationale[:160]}" for i, s in enumerate(scores)
    ]

    return VisionScore(
        rubric_id=rubric_id,
        score=min_score,
        rationale="\n".join(rationale_lines),
        dimension_scores=dim_means,
        failure_modes_observed=failure_union,
        degraded=degraded,
    )


__all__ = [
    "VISUAL_RUBRIC_IDS",
    "VisionJudgeError",
    "VisionScore",
    "roll_up_carousel",
    "vision_judge",
]
