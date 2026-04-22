"""LLM judge implementations for evaluation criteria.

## Unit 11 agent replacements (R-#32 + R-#33)

Two Sonnet subprocess judges replace older deterministic heuristics:

- **Paraphrase judge (R-#32, replaces `fuzzy_match`):** one Sonnet call per
  criterion per output carrying ALL evidence quotes together, returning
  `{quote_id: bool}` verdicts. Naive per-quote calls would add ~200 LLM calls
  per variant evaluation (4 domains × 8 criteria × 2 judges × ~3 quotes).
  The batched shape keeps this at 1 call per criterion-output.
- **Calibration judge (R-#33, replaces the cap-at-3 cliff):** one Sonnet call
  per gradient criterion per judge. Takes the gradient judge's
  `(score, evidence_cited, reasoning)` and verifies the evidence actually
  supports the claimed score band. Returns an adjusted `{score, reasoning}` —
  smooth calibration, no cliff.

**Cost:** ~one additional Sonnet call per criterion per judge for calibration
and one batched paraphrase call per criterion per output. ~$0.50 per variant
evaluation at current Sonnet pricing — tracked via `cost_recorder`.

**Cache keys** incorporate `PROMPT_VERSION` so prompt edits self-invalidate
without manual cache flushes.

**Offline fallback:** set `EVAL_EVIDENCE_AGENT=off` to force the deterministic
`fuzzy_match` path (used by offline tests + CI). Calibration never runs when
`EVAL_CALIBRATION=off`.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import math
import os
from typing import Any, Protocol

from ..exceptions import JudgeError
from ..models import (
    ChecklistScore,
    DimensionResult,
    GradientScore,
    ScoringType,
)
from .sonnet_agent import SonnetAgentError, call_sonnet_json

logger = logging.getLogger(__name__)


# Bump this string whenever any of the PARAPHRASE / CALIBRATION prompt bodies
# below are edited. Cache keys embed it so stale entries become unreachable by
# construction — no manual cache flush. Short git-style hash for readability.
PROMPT_VERSION: str = "v1-d7b2"


class JudgeProtocol(Protocol):
    """Protocol for LLM judges."""

    async def judge_dimension(
        self,
        criterion_id: str,
        rubric_prompt: str,
        output_text: str,
        source_text: str,
        *,
        scoring_type: str,
    ) -> DimensionResult: ...

    async def close(self) -> None: ...


def normalize_gradient(score: int) -> float:
    """Normalize gradient score (1-5) to 0.0-1.0."""
    return (score - 1) / 4


def normalize_checklist(passed_count: int, total: int = 4) -> float:
    """Normalize checklist score (0-4 passed) to 0.0-1.0."""
    return passed_count / total


def geometric_mean(scores: list[float], *, floor: float = 0.01) -> float:
    """Compute geometric mean of scores with floor to prevent zero-domination.

    A single zero no longer kills the entire score. Instead, zeros are
    floored to 0.01, which still heavily penalizes weak dimensions
    (pulling score to ~0.1-0.3 range) without making all variants score 0.
    """
    if not scores:
        return 0.0
    floored = [max(s, floor) for s in scores]
    product = math.prod(floored)
    if product <= 0:
        return 0.0
    return product ** (1 / len(floored))


# ─── Shared parsing + evidence verification ──────────────────────────────


def escape_untrusted_tags(text: str) -> str:
    """Escape </untrusted_input> in content to prevent tag boundary escape."""
    return text.replace("</untrusted_input>", "&lt;/untrusted_input&gt;")


def fuzzy_match(quote: str, text: str, threshold: float = 0.5) -> bool:
    """Deterministic token-overlap fallback for `EVAL_EVIDENCE_AGENT=off`.

    Kept as a backstop for offline tests / CI so the evaluation pipeline is
    functional without an Anthropic dependency. The production path is the
    paraphrase judge below; do not call this directly from new code.

    Threshold 0.5 was tuned for *narrative* evidence the LLM produces during
    checklist judging — 0.8 flipped legitimate passes to fail (MON-4
    diagnosis, 2026-04-17). 0.5 still catches fabricated citations whose
    content words don't appear anywhere in the output.
    """
    quote_tokens = set(quote.lower().split())
    text_tokens = set(text.lower().split())
    if not quote_tokens:
        return False
    overlap = len(quote_tokens & text_tokens) / len(quote_tokens)
    return overlap >= threshold


def _evidence_agent_enabled() -> bool:
    """Paraphrase judge runs unless explicitly disabled (offline / CI)."""
    return os.environ.get("EVAL_EVIDENCE_AGENT", "on").lower() != "off"


def _calibration_enabled() -> bool:
    """Calibration judge runs unless explicitly disabled (offline / CI)."""
    return os.environ.get("EVAL_CALIBRATION", "on").lower() != "off"


# ─── Paraphrase judge (R-#32) ────────────────────────────────────────────


_PARAPHRASE_PROMPT_TEMPLATE = """\
You are a deterministic paraphrase checker. For each numbered claim, decide
whether its meaning is present in the text (paraphrase counts; exact-string
match is not required). Do not guess — if a claim has no grounding, return
supported=false.

Text:
<text>
{output_text}
</text>

Claims:
{claims_block}

Return a SINGLE JSON object (no prose, no markdown fences) of the form:
{{"verdicts": [{{"id": "<quote_id>", "supported": <true|false>}}, ...]}}

Return exactly one entry per claim, preserving the provided ids.
"""


# Per-process paraphrase cache: (PROMPT_VERSION, criterion_id,
# sha256(output_text), sha256(quote)) → bool. Unbounded — evaluation runs are
# short-lived subprocesses; cache never grows large enough to matter.
_PARAPHRASE_CACHE: dict[tuple[str, str, str, str], bool] = {}


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def _paraphrase_cache_key(
    criterion_id: str, output_hash: str, quote: str,
) -> tuple[str, str, str, str]:
    """Cache key format is part of R-#32's spec — don't change without bumping PROMPT_VERSION."""
    return (PROMPT_VERSION, criterion_id, output_hash, _hash_text(quote))


async def verify_evidence_batch(
    criterion_id: str,
    quotes: list[str],
    output_text: str,
    *,
    timeout: float | None = None,
) -> dict[str, bool]:
    """Return `{quote_id: bool}` paraphrase-support verdicts for each quote.

    One Sonnet call covers all quotes for a single criterion-output pair
    (batching shape required by R-#32 — per-quote calls would add ~200
    LLM calls per variant evaluation).

    quote_id format is `q{i}` where `i` matches the input list order. Callers
    reconstruct per-quote verdicts by zipping with `quotes`.

    On failure (timeout, CLI error, parse error) we degrade to `fuzzy_match`
    — failure should not silently score claims as supported, but should also
    not collapse the entire evaluation. WARN-level log makes frequency
    observable via the existing log pipeline.
    """
    if not quotes:
        return {}

    output_hash = _hash_text(output_text)
    verdicts: dict[str, bool] = {}
    uncached: list[tuple[str, str]] = []  # (quote_id, quote)

    for i, quote in enumerate(quotes):
        qid = f"q{i}"
        key = _paraphrase_cache_key(criterion_id, output_hash, quote)
        cached = _PARAPHRASE_CACHE.get(key)
        if cached is not None:
            verdicts[qid] = cached
        else:
            uncached.append((qid, quote))

    if not uncached:
        return verdicts

    if not _evidence_agent_enabled():
        for qid, quote in uncached:
            match = fuzzy_match(quote, output_text)
            verdicts[qid] = match
            _PARAPHRASE_CACHE[
                _paraphrase_cache_key(criterion_id, output_hash, quote)
            ] = match
        return verdicts

    claims_block = "\n".join(
        f"{qid}. {escape_untrusted_tags(quote)}" for qid, quote in uncached
    )
    prompt = _PARAPHRASE_PROMPT_TEMPLATE.format(
        output_text=escape_untrusted_tags(output_text),
        claims_block=claims_block,
    )

    try:
        data = await call_sonnet_json(
            prompt, operation="evidence_paraphrase_check", timeout=timeout,
        )
    except SonnetAgentError as e:
        logger.warning(
            "Paraphrase judge failed for %s (%d quotes), falling back to fuzzy_match: %s",
            criterion_id, len(uncached), e,
        )
        for qid, quote in uncached:
            match = fuzzy_match(quote, output_text)
            verdicts[qid] = match
            _PARAPHRASE_CACHE[
                _paraphrase_cache_key(criterion_id, output_hash, quote)
            ] = match
        return verdicts

    raw_verdicts = data.get("verdicts") or []
    by_id = {
        v.get("id"): bool(v.get("supported", False))
        for v in raw_verdicts
        if isinstance(v, dict) and isinstance(v.get("id"), str)
    }
    for qid, quote in uncached:
        supported = by_id.get(qid)
        if supported is None:
            # Missing verdict → treat as unsupported per plan edge-case #2.
            logger.debug(
                "Paraphrase judge omitted verdict for %s/%s; treating as unsupported",
                criterion_id, qid,
            )
            supported = False
        verdicts[qid] = supported
        _PARAPHRASE_CACHE[
            _paraphrase_cache_key(criterion_id, output_hash, quote)
        ] = supported

    return verdicts


# ─── Calibration judge (R-#33) ───────────────────────────────────────────


_CALIBRATION_PROMPT_TEMPLATE = """\
You are a blinded calibration checker for a rubric-based evaluation. The
primary judge has scored a criterion on a 1-5 gradient. Your job is to
verify whether the cited evidence actually supports the claimed score band,
and adjust if not.

Bands (anchors):
  1 = no or contradicted support · 2 = thin/weak support · 3 = partial
  support · 4 = strong support · 5 = unambiguous, multi-point support

Criterion: {criterion_id}

Rubric:
<rubric>
{rubric_prompt}
</rubric>

Primary judge score: {score}/5
Primary judge reasoning:
<reasoning>{reasoning}</reasoning>

Evidence cited (with paraphrase-verification verdicts):
{evidence_block}

Guidelines:
- If the verified evidence clearly supports the claimed band, return the
  same score.
- If the evidence is thinner than the claimed band, lower the score to the
  band the evidence actually supports (e.g. claimed 5 but only 1 weak quote
  → return 3).
- If the evidence is stronger than the claimed band, raise the score.
- If the reasoning contradicts the evidence, lower accordingly.
- Integer scores only (1-5). No cliffs, no cap — adjust smoothly.

Return a SINGLE JSON object (no prose, no markdown fences):
{{"score": <int 1..5>, "reasoning": "<1-2 sentences on the adjustment>"}}
"""


_CalibrationKey = tuple[str, str, str, str]  # (PROMPT_VERSION, criterion_id, sha_reasoning, sha_evidence)
_CALIBRATION_CACHE: dict[_CalibrationKey, tuple[int, str]] = {}


def _calibration_cache_key(
    criterion_id: str, reasoning: str, evidence_block: str,
) -> _CalibrationKey:
    return (
        PROMPT_VERSION,
        criterion_id,
        _hash_text(reasoning),
        _hash_text(evidence_block),
    )


async def calibrate_gradient(
    criterion_id: str,
    rubric_prompt: str,
    score: int,
    reasoning: str,
    evidence: list[str],
    evidence_verdicts: dict[str, bool],
    *,
    timeout: float | None = None,
) -> dict[str, Any]:
    """Return `{score: int in [0,5], reasoning: str}` — the calibrated result.

    Uses the primary judge's claims blinded to no outputs we haven't already
    seen; one Sonnet call per gradient criterion per judge (see module
    docstring for cost accounting).

    On failure (timeout, CLI error, parse error) return the primary judge's
    unchanged score + a reasoning note explaining the fallback. Failure
    should not penalize — the cap-at-3 gate this replaces also had this
    "degrade to permissive" property.
    """
    score = max(1, min(5, int(score)))

    verdict_lines = []
    for i, quote in enumerate(evidence):
        qid = f"q{i}"
        supported = evidence_verdicts.get(qid)
        flag = (
            "supported=unknown"
            if supported is None
            else f"supported={'true' if supported else 'false'}"
        )
        verdict_lines.append(f"- [{flag}] {escape_untrusted_tags(quote)}")
    evidence_block = "\n".join(verdict_lines) if verdict_lines else "(no evidence cited)"

    cache_key = _calibration_cache_key(criterion_id, reasoning, evidence_block)
    cached = _CALIBRATION_CACHE.get(cache_key)
    if cached is not None:
        return {"score": cached[0], "reasoning": cached[1]}

    if not _calibration_enabled():
        result = {
            "score": score,
            "reasoning": "calibration disabled (EVAL_CALIBRATION=off); "
                        "primary judge score retained",
        }
        _CALIBRATION_CACHE[cache_key] = (result["score"], result["reasoning"])
        return result

    prompt = _CALIBRATION_PROMPT_TEMPLATE.format(
        criterion_id=criterion_id,
        rubric_prompt=escape_untrusted_tags(rubric_prompt[:2000]),
        score=score,
        reasoning=escape_untrusted_tags(reasoning[:2000]),
        evidence_block=evidence_block,
    )

    try:
        data = await call_sonnet_json(
            prompt, operation="calibration_check", timeout=timeout,
        )
    except SonnetAgentError as e:
        logger.warning(
            "Calibration judge failed for %s, keeping primary score %d: %s",
            criterion_id, score, e,
        )
        return {
            "score": score,
            "reasoning": f"calibration judge error ({e}); primary score retained",
        }

    try:
        adjusted_score = int(data.get("score", score))
    except (TypeError, ValueError):
        logger.warning("Calibration judge returned non-int score for %s: %r", criterion_id, data)
        adjusted_score = score
    adjusted_score = max(0, min(5, adjusted_score))

    adjusted_reasoning = data.get("reasoning") or ""
    if not isinstance(adjusted_reasoning, str):
        adjusted_reasoning = json.dumps(adjusted_reasoning)[:500]
    if not adjusted_reasoning.strip():
        adjusted_reasoning = "calibration returned empty reasoning; score adjusted"

    _CALIBRATION_CACHE[cache_key] = (adjusted_score, adjusted_reasoning)
    return {"score": adjusted_score, "reasoning": adjusted_reasoning}


# ─── Judge response parsing (async) ──────────────────────────────────────


async def parse_judge_response(
    judge_name: str,
    criterion_id: str,
    response_text: str,
    output_text: str,
    is_gradient: bool,
    model: str,
    *,
    rubric_prompt: str = "",
) -> DimensionResult:
    """Parse and validate LLM judge response with evidence gates.

    Shared between GeminiJudge and OpenAIJudge. Async so it can await the
    batched paraphrase judge (R-#32) and the calibration judge (R-#33).
    """
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError as e:
        raise JudgeError(judge_name, criterion_id, f"Invalid JSON: {e}") from e

    if is_gradient:
        return await _parse_gradient(
            criterion_id, data, output_text, model, rubric_prompt=rubric_prompt,
        )
    return await _parse_checklist(criterion_id, data, output_text, model)


async def _parse_gradient(
    criterion_id: str,
    data: dict[str, Any],
    output_text: str,
    model: str,
    *,
    rubric_prompt: str = "",
) -> DimensionResult:
    """Parse gradient (1-5) response with paraphrase + calibration judges."""
    parsed = GradientScore.model_validate(data)
    primary_score = max(1, min(5, parsed.score))

    # Batched paraphrase verification (R-#32) — one Sonnet call for all quotes.
    verdicts = await verify_evidence_batch(
        criterion_id, parsed.evidence, output_text,
    )
    verified_evidence = [
        quote for i, quote in enumerate(parsed.evidence) if verdicts.get(f"q{i}", False)
    ]

    # Calibration judge (R-#33) — replaces the cap-at-3 cliff. Runs on every
    # gradient criterion; the judge itself is the one that decides whether
    # adjustment is warranted (no gating heuristic).
    calibration = await calibrate_gradient(
        criterion_id,
        rubric_prompt,
        primary_score,
        parsed.reasoning,
        parsed.evidence,
        verdicts,
    )
    calibrated_score = int(calibration["score"])
    # Allow the calibration judge to return 0 (unsupported-at-all band).
    calibrated_score = max(0, min(5, calibrated_score))

    # Normalize: primary is in [1,5] → [0,1]; calibration may return 0 which
    # maps to below-1 band (score=0.0). Keep [0,1] clamp.
    if calibrated_score == 0:
        normalized = 0.0
    else:
        normalized = max(0.0, min(1.0, (calibrated_score - 1) / 4))

    reasoning = parsed.reasoning
    calibration_reasoning = calibration.get("reasoning", "").strip()
    if calibrated_score != primary_score and calibration_reasoning:
        reasoning = (
            f"{parsed.reasoning}\n\n[calibration {primary_score}→{calibrated_score}] "
            f"{calibration_reasoning}"
        )

    return DimensionResult(
        criterion_id=criterion_id,
        scoring_type=ScoringType.GRADIENT,
        raw_score=calibrated_score,
        normalized_score=normalized,
        reasoning=reasoning,
        evidence=verified_evidence,
        model=model,
    )


async def _parse_checklist(
    criterion_id: str,
    data: dict[str, Any],
    output_text: str,
    model: str,
) -> DimensionResult:
    """Parse checklist (4 sub-questions) response with batched paraphrase gate."""
    parsed = ChecklistScore.model_validate(data)
    sub_qs = parsed.sub_questions[:4]

    quotes = [sq.evidence for sq in sub_qs]
    verdicts = await verify_evidence_batch(criterion_id, quotes, output_text)

    sub_results: list[dict[str, Any]] = []
    passed_count = 0
    for i, sq in enumerate(sub_qs):
        verified = verdicts.get(f"q{i}", False)
        actually_passed = sq.passed and verified

        if sq.passed and not verified:
            logger.info(
                "Evidence gate: %s sub-question flipped to fail (fabricated evidence)",
                criterion_id,
            )

        if actually_passed:
            passed_count += 1

        sub_results.append({
            "question": sq.question,
            "passed": actually_passed,
            "evidence": sq.evidence,
            "evidence_verified": verified,
        })

    normalized = passed_count / 4

    return DimensionResult(
        criterion_id=criterion_id,
        scoring_type=ScoringType.CHECKLIST,
        raw_score=passed_count,
        normalized_score=normalized,
        reasoning=parsed.reasoning,
        evidence=[sq.evidence for sq in sub_qs if sq.evidence],
        model=model,
        sub_questions=sub_results,
    )


# Keep asyncio re-export for legacy callers (tests occasionally reference it via this module).
__all__ = [
    "PROMPT_VERSION",
    "JudgeProtocol",
    "normalize_gradient",
    "normalize_checklist",
    "geometric_mean",
    "escape_untrusted_tags",
    "fuzzy_match",
    "verify_evidence_batch",
    "calibrate_gradient",
    "parse_judge_response",
    "asyncio",
]
