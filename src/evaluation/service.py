"""Evaluation service — orchestrates structural gate → judges → aggregate → persist."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import statistics
import time
from typing import Any
from uuid import uuid4

from .exceptions import EvaluationError
from .judges import JudgeProtocol, geometric_mean
from .models import (
    DimensionResult,
    DomainResult,
    EvaluateRequest,
    EvaluationRecord,
    SessionCritiqueRequest,
    ScoringType,
)
from .repository import PostgresEvaluationRepository
from .rubrics import GEO_PREFIX, RUBRIC_VERSION, RUBRICS, SB_PREFIX
from .structural import StructuralResult, structural_gate

logger = logging.getLogger(__name__)

# Domain prefixes for rubric prompts
_DOMAIN_PREFIXES: dict[str, str] = {
    "geo": GEO_PREFIX,
    "storyboard": SB_PREFIX,
}

# Criteria IDs per domain (ordered 1-8)
_DOMAIN_CRITERIA: dict[str, list[str]] = {
    "geo": [f"GEO-{i}" for i in range(1, 9)],
    "competitive": [f"CI-{i}" for i in range(1, 9)],
    "monitoring": [f"MON-{i}" for i in range(1, 9)],
    "storyboard": [f"SB-{i}" for i in range(1, 9)],
}

# Primary deliverable per domain — the file(s) LLM judges actually score.
# Structural gate still receives the full outputs dict (validates pipeline
# artifacts like session.md + results.jsonl), but the rubrics themselves
# evaluate the primary deliverable only. Without this filter, monitoring's
# 8-file concatenation duplicated facts across digest/recommendations and
# MON-8 flagged the duplication as a quality defect (2026-04-17).
_JUDGE_PRIMARY_DELIVERABLE: dict[str, tuple[str, ...]] = {
    "monitoring": ("digest.md",),
    # competitive: brief.md is the deliverable; competitors/*.json is
    # data grounding that should reach structural (exists+parses) but
    # NOT be concatenated into the judge's blob (pollutes CI-1 thesis
    # evaluation with raw data, distorts CI-8 data-gaps scoring).
    "competitive": ("brief.md",),
}


def _build_judge_output_text(domain: str, outputs: dict[str, str]) -> str:
    """Return the text the LLM judges should score for this domain."""
    primary = _JUDGE_PRIMARY_DELIVERABLE.get(domain)
    if primary:
        selected = {k: v for k, v in outputs.items() if k in primary}
        if selected:
            return "\n\n".join(selected.values())
    return "\n\n".join(outputs.values())


# R-#34 (Unit 11, 2026-04-22): `compute_length_factor` + `_WORD_RANGES` were
# removed. The per-domain word-range multiplier was a Python-side heuristic
# that double-penalized sparse-data outputs (they also lost CI-8 / MON-8
# judgments). Cross-domain safety net moves to R-#33's calibration judge,
# which sees full output text and can flag egregious length failures. If
# monitoring/competitive/storyboard/geo degrade in the first 3 evolution
# cycles, add CI-9/SB-9/GEO-9 "Proportionality" criterion rather than
# re-introducing the Python multiplier. `DomainResult.length_factor` and
# the DB column are retained as `1.0` for schema back-compat.


def _compute_content_hash(domain: str, outputs: dict[str, str], source_data: dict[str, str]) -> str:
    """Compute deterministic hash of evaluation content for caching.

    Returns full 64-char SHA256 hexdigest. Previously truncated to 16
    chars (64 bits) which hit birthday-bound collisions ~1/65K pairs —
    at evolution scale this risked serving wrong cached results. DB
    column is TEXT with no max length, so no migration is needed; old
    16-char rows simply never match new 64-char queries (intentional
    cache invalidation — today's scoring-logic fixes made them wrong
    anyway).
    """
    h = hashlib.sha256()
    h.update(domain.encode())
    for key in sorted(outputs.keys()):
        h.update(f"\nout:{key}:{outputs[key]}".encode())
    for key in sorted(source_data.keys()):
        h.update(f"\nsrc:{key}:{source_data[key]}".encode())
    return h.hexdigest()


class EvaluationService:
    """Orchestrates the full 4-layer evaluation pipeline."""

    def __init__(
        self,
        judges: list[JudgeProtocol],
        repository: PostgresEvaluationRepository,
        *,
        replicates_per_judge: int = 1,
    ) -> None:
        self._judges = judges
        self._repository = repository
        # Each judge in self._judges is called replicates_per_judge times per criterion.
        # Total samples per criterion = len(judges) × replicates_per_judge.
        # Median of samples becomes the canonical normalized_score. Raw samples are
        # persisted on the DimensionResult so the meta-agent can inspect variance
        # via filesystem search during evolution.
        self._replicates_per_judge = max(1, replicates_per_judge)

    async def evaluate_domain(
        self,
        request: EvaluateRequest,
        *,
        user_id: Any = None,
    ) -> EvaluationRecord:
        """Run full evaluation pipeline for a single domain.

        Pipeline: cache → structural gate → LLM judges → aggregate → persist.

        The 8 LLM judge criteria are the sole source of truth for domain_score.
        The programmatic grounding gate was removed as a deliberate architectural
        decision — the regex-based claim extraction was flawed, flaky, and harmful
        (false failures on storyboard narrative, geo domain terminology, etc.).
        Factual accuracy is already covered proportionally by the LLM judge criteria.
        """
        domain = request.domain
        outputs = request.outputs
        source_data = request.source_data

        content_hash = _compute_content_hash(domain, outputs, source_data)

        # 1. Cache check
        cached = await self._repository.get_by_content_hash(content_hash, RUBRIC_VERSION)
        if cached is not None:
            logger.info("Cache hit for %s (hash=%s)", domain, content_hash)
            return cached

        # 2. Structural gate — runs first; if outputs are malformed, there is
        # nothing for the LLM judges to score. Fail fast.
        structural = structural_gate(domain, outputs)
        if not structural.passed:
            logger.info(
                "Structural gate failed for %s: %s",
                domain, structural.failures,
            )
            return await self._persist_failure(
                domain, content_hash,
                structural=structural, reason="structural_failure",
                campaign_id=request.campaign_id,
                variant_id=request.variant_id,
                user_id=user_id,
            )

        # 3. LLM judges (8 criteria x N judges, all concurrent).
        criteria_ids = _DOMAIN_CRITERIA.get(domain, [])
        if not criteria_ids:
            raise EvaluationError(f"Unknown domain: {domain}", domain=domain)

        deadline = time.monotonic() + 300  # 5-minute total deadline (8 judges concurrent, 60s each + retries)

        dimension_results = await self._run_judges(
            domain, criteria_ids, outputs, source_data, deadline
        )

        # 4. Aggregate scores. R-#34: length-factor multiplier removed;
        # calibration judge (R-#33) covers egregious length failures as
        # cross-domain safety net. `length_factor=1.0` preserved on the
        # DomainResult for DB schema back-compat.
        domain_score = geometric_mean([d.normalized_score for d in dimension_results])

        # 5. Build domain result
        result = DomainResult(
            domain=domain,
            domain_score=domain_score,
            structural_passed=structural.passed,
            length_factor=1.0,
            dimensions=dimension_results,
            content_hash=content_hash,
            rubric_version=RUBRIC_VERSION,
        )

        # 7. Persist
        record = EvaluationRecord.from_domain_result(
            result,
            campaign_id=request.campaign_id,
            variant_id=request.variant_id,
            user_id=user_id,
            dqs_score=structural.dqs_score,
        )
        await self._repository.save(record)

        logger.info(
            "Evaluated %s: score=%.3f (structural=%s)",
            domain, domain_score, structural.passed,
        )

        return record

    async def critique_session(self, request: SessionCritiqueRequest) -> list[DimensionResult]:
        """Run trusted judge execution for evolvable session-time critique."""
        deadline = time.monotonic() + 300
        judge = self._judges[0]
        resolved: list[tuple[str, ScoringType]] = []
        for criterion in request.criteria:
            try:
                scoring_type = RUBRICS[criterion.criterion_id].scoring_type
            except KeyError as exc:
                raise EvaluationError(
                    f"Unknown criterion in critique request: {criterion.criterion_id}"
                ) from exc
            resolved.append((criterion.criterion_id, scoring_type))
        tasks = [
            self._judge_with_deadline(
                judge,
                criterion.criterion_id,
                criterion.rubric_prompt,
                criterion.output_text,
                criterion.source_text,
                scoring_type,
                deadline,
            )
            for criterion, (_, scoring_type) in zip(request.criteria, resolved)
        ]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)
        return self._finalize_dimension_results(raw_results, resolved)

    async def _run_judges(
        self,
        domain: str,
        criteria_ids: list[str],
        outputs: dict[str, str],
        source_data: dict[str, str],
        deadline: float,
    ) -> list[DimensionResult]:
        """Run all criteria across the full ensemble concurrently.

        For each criterion, every judge in self._judges is called
        self._replicates_per_judge times. All samples are collected, the
        median normalized_score becomes the canonical score, and raw
        per-sample data is attached for later inspection.
        """
        prefix = _DOMAIN_PREFIXES.get(domain, "")
        source_text = "\n\n".join(source_data.values())

        criterion_tasks: list[asyncio.Task[DimensionResult]] = []
        request_meta: list[tuple[str, str]] = []
        for cid in criteria_ids:
            rubric = RUBRICS.get(cid)
            if rubric is None:
                logger.warning("No rubric found for %s", cid)
                continue
            request_meta.append((cid, rubric.scoring_type))

            prompt = f"{prefix}\n\n{rubric.prompt}" if prefix else rubric.prompt

            if rubric.is_cross_item:
                output_text = self._build_cross_item_text(domain, outputs)
            else:
                output_text = _build_judge_output_text(domain, outputs)

            criterion_tasks.append(
                asyncio.create_task(
                    self._ensemble_judge_criterion(
                        cid, prompt, output_text, source_text,
                        rubric.scoring_type, deadline,
                    )
                )
            )

        results = await asyncio.gather(*criterion_tasks, return_exceptions=True)
        return self._finalize_dimension_results(results, request_meta)

    async def _run_ensemble_samples(
        self,
        criterion_id: str,
        prompt: str,
        output_text: str,
        source_text: str,
        scoring_type: str,
        deadline: float,
    ) -> list[DimensionResult | Exception]:
        """Run every (judge × replicate) concurrently, return raw results."""
        call_tasks = [
            self._judge_with_deadline(
                judge, criterion_id, prompt, output_text, source_text,
                scoring_type, deadline,
            )
            for judge in self._judges
            for _ in range(self._replicates_per_judge)
        ]
        return await asyncio.gather(*call_tasks, return_exceptions=True)

    async def _ensemble_judge_criterion(
        self,
        criterion_id: str,
        prompt: str,
        output_text: str,
        source_text: str,
        scoring_type: str,
        deadline: float,
    ) -> DimensionResult:
        """Run every judge N times for one criterion, then return median with samples.

        All judge×replicate calls run concurrently. If some calls fail entirely,
        the median is computed from whatever completed. If ALL calls fail,
        retry the whole ensemble once before hard-zeroing — transient API
        failures shouldn't collapse the geometric-mean composite. If the
        retry also all-fails, returns an error DimensionResult (correct
        signal that judge is truly broken).
        """
        raw = await self._run_ensemble_samples(
            criterion_id, prompt, output_text, source_text, scoring_type, deadline,
        )
        if all(isinstance(r, Exception) for r in raw):
            logger.warning(
                "Ensemble judge %s: all %d samples failed on first pass, retrying once",
                criterion_id, len(raw),
            )
            raw = await self._run_ensemble_samples(
                criterion_id, prompt, output_text, source_text, scoring_type, deadline,
            )

        samples: list[dict[str, Any]] = []
        successful: list[DimensionResult] = []
        for result in raw:
            if isinstance(result, Exception):
                samples.append({
                    "model": "unknown",
                    "normalized_score": None,
                    "reasoning": None,
                    "error": f"{type(result).__name__}: {result}",
                })
                continue
            samples.append({
                "model": result.model,
                "normalized_score": result.normalized_score,
                "raw_score": result.raw_score,
                "reasoning": result.reasoning,
                "error": None,
            })
            successful.append(result)

        if not successful:
            logger.warning(
                "Ensemble judge %s: all %d samples failed", criterion_id, len(raw),
            )
            err_result = self._error_dimension_result(
                criterion_id, scoring_type,
                f"all {len(raw)} ensemble samples failed",
            )
            return DimensionResult(
                criterion_id=err_result.criterion_id,
                scoring_type=err_result.scoring_type,
                raw_score=err_result.raw_score,
                normalized_score=err_result.normalized_score,
                reasoning=err_result.reasoning,
                evidence=err_result.evidence,
                model=err_result.model,
                sub_questions=err_result.sub_questions,
                samples=samples,
            )

        median_score = statistics.median(s.normalized_score for s in successful)
        median_raw = statistics.median(s.raw_score for s in successful)

        # Representative sample: pick the successful one whose normalized_score is
        # closest to the median. This preserves its reasoning + evidence for display.
        representative = min(
            successful,
            key=lambda s: abs(s.normalized_score - median_score),
        )

        model_tag = (
            f"ensemble:median({len(successful)}/{len(raw)})"
            if len(self._judges) > 1 or self._replicates_per_judge > 1
            else representative.model
        )

        return DimensionResult(
            criterion_id=criterion_id,
            scoring_type=representative.scoring_type,
            raw_score=median_raw,
            normalized_score=median_score,
            reasoning=representative.reasoning,
            evidence=representative.evidence,
            model=model_tag,
            sub_questions=representative.sub_questions,
            samples=samples,
        )

    async def _judge_with_deadline(
        self,
        judge: JudgeProtocol,
        criterion_id: str,
        prompt: str,
        output_text: str,
        source_text: str,
        scoring_type: str,
        deadline: float,
    ) -> DimensionResult:
        """Run a single judge with deadline check."""
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return DimensionResult(
                criterion_id=criterion_id,
                scoring_type=ScoringType.GRADIENT if scoring_type == "gradient" else ScoringType.CHECKLIST,
                raw_score=0,
                normalized_score=0.0,
                reasoning="Deadline exceeded",
                evidence=[],
                model="timeout",
            )

        return await asyncio.wait_for(
            judge.judge_dimension(
                criterion_id, prompt, output_text, source_text,
                scoring_type=scoring_type,
            ),
            timeout=min(remaining, 120),
        )

    def _finalize_dimension_results(
        self,
        results: list[DimensionResult | Exception],
        request_meta: list[tuple[str, str]],
    ) -> list[DimensionResult]:
        """Normalize judge exceptions into deterministic zero-score dimensions."""
        dimension_results: list[DimensionResult] = []
        for index, result in enumerate(results):
            criterion_id, scoring_type = request_meta[index]
            if isinstance(result, Exception):
                logger.error("Judge failed for %s: %s", criterion_id, result)
                dimension_results.append(self._error_dimension_result(criterion_id, scoring_type, str(result)))
            else:
                dimension_results.append(result)
        return dimension_results

    @staticmethod
    def _error_dimension_result(
        criterion_id: str,
        scoring_type: str,
        detail: str,
    ) -> DimensionResult:
        normalized_type = ScoringType.GRADIENT if scoring_type == ScoringType.GRADIENT.value else ScoringType.CHECKLIST
        return DimensionResult(
            criterion_id=criterion_id,
            scoring_type=normalized_type,
            raw_score=0,
            normalized_score=0.0,
            reasoning=f"Judge error: {detail}",
            evidence=[],
            model="error",
        )

    def _build_cross_item_text(self, domain: str, outputs: dict[str, str]) -> str:
        """Build concatenated text for cross-item criteria (GEO-6, SB-8)."""
        parts = []
        for filename, content in sorted(outputs.items()):
            slug = filename.rsplit("/", 1)[-1].rsplit(".", 1)[0]
            if domain == "storyboard":
                parts.append(f"=== STORY: {slug} ===\n{content}")
            else:
                parts.append(f"=== PAGE: {slug} ===\n{content}")
        return "\n\n".join(parts)

    async def _persist_failure(
        self,
        domain: str,
        content_hash: str,
        *,
        structural: StructuralResult | None = None,
        reason: str,
        campaign_id: str | None = None,
        variant_id: str | None = None,
        user_id: Any = None,
    ) -> EvaluationRecord:
        """Persist a failed evaluation (score 0)."""
        dimension_data: dict[str, Any] = {"failure_reason": reason}
        if structural is not None and structural.dqs_score is not None:
            dimension_data["_dqs_score"] = structural.dqs_score

        record = EvaluationRecord(
            id=uuid4(),
            domain=domain,
            domain_score=0.0,
            grounding_score=None,
            structural_passed=structural.passed if structural else None,
            length_factor=None,
            dimension_scores=dimension_data,
            rubric_version=RUBRIC_VERSION,
            content_hash=content_hash,
            campaign_id=campaign_id,
            variant_id=variant_id,
            user_id=user_id,
        )
        await self._repository.save(record)
        return record

    async def get_evaluation(self, evaluation_id: Any, user_id: Any = None) -> EvaluationRecord | None:
        """Get full evaluation details by ID (user-scoped)."""
        return await self._repository.get_by_id(evaluation_id, user_id)

    async def get_campaign_evaluations(self, campaign_id: str, user_id: Any = None) -> list[EvaluationRecord]:
        """Get all evaluations for a campaign (user-scoped)."""
        return await self._repository.get_by_campaign(campaign_id, user_id)

    async def close(self) -> None:
        """Clean up judge resources."""
        for judge in self._judges:
            await judge.close()
