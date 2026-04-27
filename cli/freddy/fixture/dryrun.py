"""Judge-based fixture calibration harness (``freddy fixture dry-run``).

Phase 7 of Plan A: qualitative validation gate that replaces the mechanical
canary gate. Raw stats (per-seed scores, median, MAD, cost) are shipped to
the evolution-judge-service ``system_health/fixture_quality`` role; the
agent returns a verdict and the CLI maps verdict to exit code. There are
no hardcoded quality thresholds in this module — the agent owns the call.

Exit code mapping (delegated to the CLI):
  * ``healthy``                            → 0
  * ``saturated`` / ``degenerate`` /
    ``unstable`` / ``cost_excess`` /
    ``needs_revision``                     → 1
  * ``unclear`` (agent abstention)          → 2 (also logs ``judge_abstain``)
"""
from __future__ import annotations

import json
import os
import statistics
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# Expose JudgeUnreachable from the autoresearch side so both the fixture
# refresh + dry-run code paths raise the same exception type. The import
# is deferred for test-time isolation — tests that mock call_quality_judge
# don't need the full autoresearch module graph.
try:
    from autoresearch.evaluate_variant import JudgeUnreachable  # type: ignore
except Exception:  # pragma: no cover - fallback for isolated imports
    class JudgeUnreachable(RuntimeError):
        """Raised when the evolution-judge service is unreachable."""


_VERDICTS_REJECT = {
    "saturated",
    "degenerate",
    "unstable",
    "cost_excess",
    "needs_revision",
}
_VERDICT_ABSTAIN = "unclear"
_VERDICT_HEALTHY = "healthy"


@dataclass
class QualityVerdict:
    """Structured verdict returned by the fixture_quality judge agent."""

    verdict: str
    reasoning: str
    confidence: float
    recommended_action: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "recommended_action": self.recommended_action,
        }


@dataclass
class DryRunReport:
    """Full dry-run report assembled from raw stats + judge verdict."""

    fixture_id: str
    fixture_version: str
    baseline_variant: str
    judge_seeds: int
    per_seed_scores: list[float]
    median_score: float
    mad: float
    structural_passed: bool
    warnings: list[str] = field(default_factory=list)
    quality_verdict: dict[str, Any] = field(default_factory=dict)
    cost_usd: float = 0.0
    duration_seconds: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "fixture_id": self.fixture_id,
            "fixture_version": self.fixture_version,
            "baseline_variant": self.baseline_variant,
            "judge_seeds": self.judge_seeds,
            "per_seed_scores": self.per_seed_scores,
            "median_score": self.median_score,
            "mad": self.mad,
            "structural_passed": self.structural_passed,
            "warnings": self.warnings,
            "quality_verdict": self.quality_verdict,
            "cost_usd": self.cost_usd,
            "duration_seconds": self.duration_seconds,
        }


def call_quality_judge(payload: dict[str, Any]) -> QualityVerdict:
    """POST ``payload`` to the evolution-judge-service fixture_quality role.

    The service exposes ``POST /invoke/system_health/fixture_quality``;
    payload must carry ``role`` + ``stats`` + ``fixture_metadata`` (and may
    include additional fields the agent uses for context). On HTTP failure
    this function logs ``kind="judge_unreachable"`` and raises
    :class:`JudgeUnreachable`. Tests mock this function directly.
    """
    import httpx  # local import keeps module surface lean
    from autoresearch.events import log_event

    from ..output import emit_error

    judge_url = os.environ.get("EVOLUTION_JUDGE_URL", "http://localhost:7200").rstrip("/")
    endpoint = f"{judge_url}/invoke/system_health/fixture_quality"
    token = os.environ.get("EVOLUTION_INVOKE_TOKEN", "")
    if not token:
        emit_error(
            "missing_token",
            "SESSION_INVOKE_TOKEN/EVOLUTION_INVOKE_TOKEN not set; refusing to send "
            "an unauthenticated request to the judge service.",
        )
    try:
        response = httpx.post(
            endpoint,
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=120.0,
        )
    except (httpx.HTTPError, OSError) as exc:
        log_event(
            kind="judge_unreachable",
            endpoint="/invoke/system_health/fixture_quality",
            error=repr(exc),
        )
        raise JudgeUnreachable(
            f"evolution-judge fixture_quality unreachable: {exc}"
        ) from exc

    if response.status_code >= 500:
        log_event(
            kind="judge_unreachable",
            endpoint="/invoke/system_health/fixture_quality",
            error=f"HTTP {response.status_code}: {response.text[:500]}",
        )
        raise JudgeUnreachable(
            f"evolution-judge fixture_quality returned {response.status_code}"
        )
    if response.status_code >= 400:
        raise JudgeUnreachable(
            f"evolution-judge fixture_quality rejected payload: "
            f"HTTP {response.status_code} {response.text[:200]}"
        )

    try:
        data = response.json()
    except json.JSONDecodeError as exc:
        raise JudgeUnreachable(
            f"evolution-judge fixture_quality returned invalid JSON: {exc}"
        ) from exc
    return QualityVerdict(
        verdict=str(data.get("verdict") or "").strip().lower() or _VERDICT_ABSTAIN,
        reasoning=str(data.get("reasoning") or ""),
        confidence=float(data.get("confidence") or 0.0),
        recommended_action=data.get("recommended_action"),
    )


def _run_single_fixture_eval(
    fixture_id: str,
    manifest_path: Path,
    pool: str,
    baseline: str,
    seeds: int,
    cache_root: Path,
) -> dict[str, Any]:
    """Invoke :func:`autoresearch.evaluate_variant.evaluate_single_fixture`.

    Tests patch this symbol directly. Returns the raw stats dict that
    :func:`run_dry_run` consumes.
    """
    from autoresearch import evaluate_variant
    from autoresearch.lane_runtime import ensure_materialized_runtime

    # archive/current_runtime/ is a derived mirror of the active lane heads
    # (built by lane_runtime from current.json). Production entry points reach
    # the runner via runtime_bootstrap.py, which materializes the mirror
    # before exec. The dry-run path invokes archive/<baseline>/run.py
    # directly; without this call the agent subprocess Popen'd by harness
    # fails with FileNotFoundError on cwd=archive/current_runtime.
    archive_dir = Path(evaluate_variant.__file__).resolve().parent / "archive"
    ensure_materialized_runtime(archive_dir)

    return evaluate_variant.evaluate_single_fixture(
        fixture_id,
        manifest_path=str(manifest_path),
        pool=pool,
        baseline=baseline,
        seeds=seeds,
        cache_root=str(cache_root),
    )


def _median_and_mad(scores: list[float]) -> tuple[float, float]:
    """Pure-Python median + MAD (median absolute deviation)."""
    if not scores:
        return 0.0, 0.0
    median = float(statistics.median(scores))
    mad = float(statistics.median(abs(s - median) for s in scores))
    return round(median, 4), round(mad, 4)


def _verdict_to_exit_code(verdict: str) -> int:
    """Map an agent verdict to a CLI exit code. No thresholds — string lookup."""
    v = (verdict or "").strip().lower()
    if v == _VERDICT_HEALTHY:
        return 0
    if v == _VERDICT_ABSTAIN:
        return 2
    if v in _VERDICTS_REJECT:
        return 1
    # Unknown verdict from the agent — treat as abstention so the operator
    # reviews manually rather than auto-rejecting on a label we don't know.
    return 2


def run_dry_run(
    fixture_id: str,
    *,
    manifest_path: Path,
    pool: str,
    baseline: str,
    seeds: int,
    cache_root: Path,
) -> tuple[dict[str, Any], int]:
    """Execute the judge-based dry-run calibration for one fixture.

    Returns ``(report_dict, exit_code)``. The caller is responsible for
    emitting the report (e.g. as JSON) and raising ``typer.Exit(exit_code)``.

    * ``exit_code == 0`` — verdict ``healthy``.
    * ``exit_code == 1`` — explicit rejection
      (``saturated``/``degenerate``/``unstable``/``cost_excess``/
      ``needs_revision``).
    * ``exit_code == 2`` — verdict ``unclear`` (or unknown). Emits
      ``kind="judge_abstain"`` to ``events.jsonl``.
    """
    from cli.freddy.fixture.schema import (
        assert_pool_matches,
        parse_suite_manifest,
    )

    payload_raw = json.loads(Path(manifest_path).read_text())
    manifest = parse_suite_manifest(payload_raw)
    assert_pool_matches(pool, manifest)

    fixture_spec = None
    fixture_domain: str | None = None
    for dom, fixtures in manifest.fixtures.items():
        for spec in fixtures:
            if spec.fixture_id == fixture_id:
                fixture_spec = spec
                fixture_domain = dom
                break
        if fixture_spec is not None:
            break
    if fixture_spec is None:
        raise KeyError(
            f"fixture {fixture_id!r} not found in manifest {manifest.suite_id!r}"
        )

    started = time.monotonic()
    raw = _run_single_fixture_eval(
        fixture_id,
        manifest_path,
        pool,
        baseline,
        seeds,
        cache_root,
    )
    per_seed_scores = [float(s) for s in raw.get("per_seed_scores", [])]
    structural_passed = bool(raw.get("structural_passed", True))
    cost_usd = float(raw.get("cost_usd", 0.0) or 0.0)
    warnings_list: list[str] = [str(w) for w in (raw.get("warnings") or [])]
    median, mad = _median_and_mad(per_seed_scores)

    judge_payload = {
        "role": "fixture_quality",
        "stats": {
            "per_seed_scores": per_seed_scores,
            "median": median,
            "mad": mad,
            "cost_usd": cost_usd,
            "structural_passed": structural_passed,
        },
        "fixture_metadata": {
            "fixture_id": fixture_id,
            "fixture_version": fixture_spec.version,
            "domain": fixture_domain,
            "anchor": bool(fixture_spec.anchor),
            "context": fixture_spec.context,
            "baseline_variant": baseline,
        },
    }
    verdict = call_quality_judge(judge_payload)

    report = DryRunReport(
        fixture_id=fixture_id,
        fixture_version=fixture_spec.version,
        baseline_variant=baseline,
        judge_seeds=seeds,
        per_seed_scores=per_seed_scores,
        median_score=median,
        mad=mad,
        structural_passed=structural_passed,
        warnings=warnings_list,
        quality_verdict=verdict.as_dict(),
        cost_usd=cost_usd,
        duration_seconds=int(round(time.monotonic() - started)),
    )

    exit_code = _verdict_to_exit_code(verdict.verdict)
    if exit_code == 2:
        # Agent abstained — log a trail for the operator to review.
        from autoresearch.events import log_event

        log_event(
            kind="judge_abstain",
            fixture_id=fixture_id,
            pool=pool,
            baseline=baseline,
            verdict=verdict.as_dict(),
            per_seed_scores=per_seed_scores,
            median=median,
            mad=mad,
            cost_usd=cost_usd,
        )
    return report.to_dict(), exit_code


@dataclass
class DiscriminabilityReport:
    """Per-variant distributions + agent verdict on separability."""

    fixture_id: str
    variant_scores: dict[str, list[float]]
    verdict: str  # separable | not_separable | insufficient_data
    reasoning: str
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "fixture_id": self.fixture_id,
            "variant_scores": self.variant_scores,
            "verdict": self.verdict,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
        }


def run_discriminability_check(
    *,
    fixture_id: str,
    pool: str,
    manifest_path: Path,
    variants: list[str],
    seeds: int = 10,
    cache_root: Path | None = None,
) -> DiscriminabilityReport:
    """Collect per-variant raw score distributions, delegate separability to the agent.

    For each variant, run the fixture ``seeds`` times and collect the raw
    per-seed scores. Hand all variant distributions to the
    ``system_health.discriminability`` agent role — the agent decides
    ``separable`` / ``not_separable`` / ``insufficient_data`` from the raw
    numbers. No Wilcoxon / Cliff's delta / p-value thresholds.
    """
    if len(variants) < 2:
        raise ValueError("--variants requires at least two ids")

    from cli.freddy.fixture.schema import assert_pool_matches, parse_suite_manifest

    payload = json.loads(Path(manifest_path).read_text())
    assert_pool_matches(pool, parse_suite_manifest(payload))

    resolved_cache_root = cache_root or Path.home() / ".local/share/gofreddy/fixture-cache"

    variant_scores: dict[str, list[float]] = {}
    for variant in variants:
        result = _run_single_fixture_eval(
            fixture_id,
            manifest_path,
            pool,
            variant,
            seeds,
            resolved_cache_root,
        )
        variant_scores[variant] = [float(s) for s in result.get("per_seed_scores", [])]

    verdict = call_quality_judge({
        "role": "discriminability",
        "fixture_id": fixture_id,
        "variant_scores": variant_scores,
        "seeds_per_variant": seeds,
    })
    return DiscriminabilityReport(
        fixture_id=fixture_id,
        variant_scores=variant_scores,
        verdict=verdict.verdict,
        reasoning=verdict.reasoning,
        confidence=verdict.confidence,
    )
