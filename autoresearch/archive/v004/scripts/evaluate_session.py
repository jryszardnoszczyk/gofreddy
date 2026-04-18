#!/usr/bin/env python3
"""Session evaluator — evolvable session-time critique for all 4 domains.

Two-layer pipeline:
  Layer 1: Structural gate (deterministic, free)
  Layer 2: trusted external judge execution via `freddy evaluate critique`

Usage:
    python3 scripts/evaluate_session.py --domain geo --artifact optimized/page.md --session-dir sessions/geo/client/
    python3 scripts/evaluate_session.py --domain monitoring --artifact synthesized/story.md --session-dir sessions/monitoring/client/ --mode per-story
    python3 scripts/evaluate_session.py --domain competitive --artifact brief.md --session-dir sessions/competitive/client/
    python3 scripts/evaluate_session.py --domain storyboard --artifact stories/1.json --session-dir sessions/storyboard/client/
"""

from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
from pathlib import Path


ARCHIVE_ROOT = Path(__file__).resolve().parent.parent
AUTORESEARCH_ROOT = ARCHIVE_ROOT.parent.parent  # .../autoresearch/
for _p in (str(ARCHIVE_ROOT), str(AUTORESEARCH_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from workflows.session_eval_common import criteria_for_mode, truncate
from workflows.session_eval_registry import get_session_eval_spec

from harness.session_evaluator import (
    GRADIENT_CRITIQUE_TEMPLATE,
    build_critique_prompt,
    DEFAULT_PASS_THRESHOLD,
    compute_decision_threshold,
)


CRITIQUE_TIMEOUT = 180
DEFAULT_SCORING_TYPE = "gradient"


def run_structural_gate(domain: str, mode: str, artifact: Path, session_dir: Path) -> list[str]:
    return get_session_eval_spec(domain).structural_gate(mode, artifact, session_dir)


def load_source_data(domain: str, mode: str, artifact: Path, session_dir: Path) -> str:
    return get_session_eval_spec(domain).load_source_data(mode, artifact, session_dir)


def load_cross_item_context(domain: str, criterion_id: str, artifact: Path, session_dir: Path) -> str | None:
    spec = get_session_eval_spec(domain)
    config = spec.cross_item_criteria.get(criterion_id)
    if not config:
        return ""

    prior_items = [path for path in sorted(session_dir.glob(config.glob)) if path.resolve() != artifact.resolve()]
    if not prior_items:
        return None
    prior_items = prior_items[-config.max_items :]

    parts: list[str] = []
    for path in prior_items:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        # Keep cross-item context under the critique API prompt limits even
        # when a criterion asks for full prior-item comparison context.
        words_per_item = config.words_per_item if config.words_per_item is not None else 450
        content = truncate(content, words_per_item)
        parts.append(f"### Prior item: {path.name}\n{content}")
    if not parts:
        return None
    return "## Prior Items for Cross-Item Comparison\n\n" + "\n\n".join(parts)


def _invoke_external_critique(criteria: list[dict[str, object]]) -> dict:
    result = subprocess.run(
        ["freddy", "evaluate", "critique", "-"],
        input=json.dumps({"criteria": criteria}),
        capture_output=True,
        text=True,
        timeout=CRITIQUE_TIMEOUT,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(detail or "freddy evaluate critique failed")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("freddy evaluate critique returned invalid JSON") from exc


def _critique_unavailable(reason: str) -> dict:
    """Phase 3 (Unit 6): the heuristic fallback is gone. When the external
    critique cannot be reached, return a deterministic REWORK so the agent
    retries instead of silently keeping a possibly broken artifact.
    """
    return {
        "decision": "REWORK",
        "reason": f"critique_unavailable:{reason}",
        "results": [],
        "warnings": [f"Trusted external critique unavailable: {reason}"],
    }


async def evaluate_all_criteria(
    domain: str,
    mode: str,
    artifact: Path,
    session_dir: Path,
) -> dict:
    spec = get_session_eval_spec(domain)
    criteria = criteria_for_mode(spec, mode)
    if not criteria:
        return {
            "decision": "REWORK",
            "reason": "no_criteria_defined",
            "results": [],
            "warnings": ["No criteria defined for this domain/mode"],
        }

    try:
        artifact_content = artifact.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return {
            "decision": "REWORK",
            "reason": "artifact_read_error",
            "results": [],
            "warnings": [f"Could not read artifact: {exc}"],
        }

    source_data = load_source_data(domain, mode, artifact, session_dir)
    results_by_criterion: dict[str, dict] = {}
    critique_requests: list[dict[str, object]] = []
    for criterion_id, criterion_def in criteria.items():
        cross_ctx = load_cross_item_context(domain, criterion_id, artifact, session_dir)
        if cross_ctx is None and criterion_id in spec.cross_item_criteria:
            results_by_criterion[criterion_id] = {
                "criterion": criterion_id,
                "passes": None,
                "feedback": "First item in session, cross-item comparison not applicable.",
            }
            continue
        critique_requests.append(
            {
                "criterion_id": criterion_id,
                "rubric_prompt": build_critique_prompt(spec.domain_name, criterion_id, criterion_def, cross_ctx),
                # A3 Phase 1 fix: no character truncation. The previous [:8000]
                # silently cut off the second half of every competitive brief.md
                # (~14K chars), storyboard stories/*.json (11-14K each), and
                # geo pricing.md (~17KB), corrupting per-file evaluator scores
                # across 3 of 4 lanes. Model context windows handle 100K+
                # tokens easily; 17KB ≈ 4K tokens is nowhere near the limit.
                # If prompt-size issues ever arise, reintroduce chunking based
                # on measured token budgets, not a fixed character constant.
                "output_text": artifact_content,
                "source_text": source_data or "(No source data available)",
                "scoring_type": DEFAULT_SCORING_TYPE,
            }
        )

    if critique_requests:
        try:
            critique_response = _invoke_external_critique(critique_requests)
        except subprocess.TimeoutExpired:
            return _critique_unavailable("external_critique_timeout")
        except FileNotFoundError:
            return _critique_unavailable("freddy CLI not found")
        except Exception as exc:
            return _critique_unavailable(f"external_critique_error: {exc}")

        raw_results = critique_response.get("results")
        if not isinstance(raw_results, list):
            return _critique_unavailable("external_critique_invalid_response")

        for item in raw_results:
            if not isinstance(item, dict):
                continue
            criterion_id = str(item.get("criterion_id", "")).strip()
            if not criterion_id:
                continue
            normalized_score = float(item.get("normalized_score", 0.0) or 0.0)
            raw_score = float(item.get("raw_score", 0.0) or 0.0)
            reasoning = str(item.get("reasoning", "No reasoning provided.")).strip()
            evidence = [str(entry).strip() for entry in item.get("evidence", []) if str(entry).strip()]
            feedback = reasoning or "No feedback provided."
            if evidence:
                feedback = f"{feedback} Evidence: {' | '.join(evidence[:2])}"
            results_by_criterion[criterion_id] = {
                "criterion": criterion_id,
                "passes": normalized_score >= DEFAULT_PASS_THRESHOLD,
                "score": normalized_score,
                "raw_score": raw_score,
                "model": str(item.get("model", "")).strip(),
                "feedback": feedback,
            }

    missing = [criterion_id for criterion_id in criteria if criterion_id not in results_by_criterion]
    if missing:
        return _critique_unavailable(
            f"external_critique_missing_results:{','.join(missing)}"
        )

    results = [results_by_criterion[criterion_id] for criterion_id in criteria]
    evaluated = [result for result in results if result["passes"] is not None]
    failed = [result for result in evaluated if result["passes"] is False]
    evaluated_count = len(evaluated)
    failed_count = len(failed)

    if evaluated_count == 0:
        decision = "REWORK"
        reason = "no_criteria_evaluated"
    else:
        threshold = compute_decision_threshold(evaluated_count)
        decision = "REWORK" if failed_count >= threshold else "KEEP"
        reason = f"{failed_count}_of_{evaluated_count}_evaluated_failed"

    return {
        "decision": decision,
        "reason": reason,
        "results": results,
        "warnings": [],
    }


def make_output(decision: str, reason: str, results: list, warnings: list, gate_failures: list | None = None) -> dict:
    out: dict = {"decision": decision, "reason": reason}
    if gate_failures is not None:
        out["gate_failures"] = gate_failures
    out["results"] = results
    out["warnings"] = warnings
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Session evaluator — per-criterion LLM-based quality feedback.")
    parser.add_argument("--domain", required=True, choices=["geo", "competitive", "monitoring", "storyboard"], help="Domain to evaluate")
    parser.add_argument("--artifact", required=True, help="Path to the primary artifact to evaluate (relative to cwd)")
    parser.add_argument("--session-dir", required=True, help="Path to the session directory (relative to cwd)")
    parser.add_argument("--mode", choices=["full", "per-story"], default="full", help="Evaluation mode (only meaningful for monitoring domain)")
    args = parser.parse_args()

    artifact = Path(args.artifact)
    session_dir = Path(args.session_dir)

    try:
        gate_failures = run_structural_gate(args.domain, args.mode, artifact, session_dir)
        if gate_failures:
            print(
                json.dumps(
                    make_output(
                        decision="DISCARD",
                        reason="structural_gate_failed",
                        results=[],
                        warnings=[],
                        gate_failures=gate_failures,
                    ),
                    indent=2,
                )
            )
            return

        print(json.dumps(asyncio.run(evaluate_all_criteria(args.domain, args.mode, artifact, session_dir)), indent=2))
    except KeyboardInterrupt:
        print(json.dumps(make_output("REWORK", "interrupted", [], ["Evaluation interrupted — rerun required before KEEP."]), indent=2))
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print(json.dumps(make_output("REWORK", "script_error", [], [f"Script error: {exc} — rerun required before KEEP."]), indent=2))


if __name__ == "__main__":
    main()
