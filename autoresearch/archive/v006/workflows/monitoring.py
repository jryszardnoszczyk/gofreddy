from __future__ import annotations

import os
import re
from datetime import date, timedelta
from pathlib import Path

from .eval_cache import read_cached_eval_if_fresh
from .specs import FindingsPromotionConfig, RunScript, RunSessionEvaluator, WorkflowConfig, WorkflowSpec


def _resolve_monitoring_week() -> tuple[str, str]:
    pinned_start = os.environ.get("AUTORESEARCH_WEEK_START", "").strip()
    pinned_end = os.environ.get("AUTORESEARCH_WEEK_END", "").strip()
    if pinned_start or pinned_end:
        if not pinned_start or not pinned_end:
            raise ValueError(
                "Monitoring benchmark week pins must define both "
                "AUTORESEARCH_WEEK_START and AUTORESEARCH_WEEK_END."
            )
        try:
            week_start = date.fromisoformat(pinned_start)
            week_end = date.fromisoformat(pinned_end)
        except ValueError as exc:
            raise ValueError(
                "AUTORESEARCH_WEEK_START and AUTORESEARCH_WEEK_END must use YYYY-MM-DD format."
            ) from exc
        if week_end < week_start:
            raise ValueError("AUTORESEARCH_WEEK_END must be on or after AUTORESEARCH_WEEK_START.")
        return week_start.isoformat(), week_end.isoformat()

    today = date.today()
    days_since_sunday = (today.weekday() + 1) % 7
    week_end = today - timedelta(days=days_since_sunday)
    week_start = week_end - timedelta(days=6)
    return week_start.isoformat(), week_end.isoformat()


def configure_env(_client: str) -> None:
    week_start, week_end = _resolve_monitoring_week()
    os.environ["WEEK_END"] = week_end
    os.environ["WEEK_START"] = week_start


def pre_summary_hooks(_session_dir: Path, _client: str, _run_script: RunScript) -> None:
    return


def snapshot_evaluations(session_dir: Path, run_session_evaluator: RunSessionEvaluator) -> dict[str, object]:
    story_decisions: list[dict[str, str | None]] = []
    eval_dir = session_dir / "evals"
    for artifact in sorted((session_dir / "synthesized").glob("*.md")):
        output_path = eval_dir / f"story-{artifact.stem}.json"
        cached = read_cached_eval_if_fresh(artifact, output_path)
        if cached is not None:
            story_decisions.append({"artifact": artifact.name, "decision": cached["decision"]})
            continue
        data = run_session_evaluator("monitoring", artifact, session_dir, output_path, "per-story")
        story_decisions.append({"artifact": artifact.name, "decision": data.get("decision") if data else None})

    digest_artifact = session_dir / "digest.md"
    digest_eval_path = session_dir / "digest_eval.json"
    cached_digest = read_cached_eval_if_fresh(digest_artifact, digest_eval_path)
    if cached_digest is not None:
        return {
            "story_decisions": story_decisions,
            "digest_decision": cached_digest["decision"],
        }

    digest_data = run_session_evaluator("monitoring", digest_artifact, session_dir, digest_eval_path, "full")
    return {
        "story_decisions": story_decisions,
        "digest_decision": digest_data.get("decision") if digest_data else None,
    }


def completion_guard(eval_summary: dict[str, object]) -> tuple[str | None, str | None]:
    decision = eval_summary.get("digest_decision")
    if decision == "KEEP":
        return None, None
    note = f"Final digest session evaluation is {decision or 'missing'}; rerun DELIVER before marking COMPLETE."
    return note, "digest.md"


def list_deliverables(session_dir: Path) -> list[str]:
    return ["digest.md"] if (session_dir / "digest.md").exists() else []


def augment_quality_metrics(results: list[dict], quality_metrics: dict) -> None:
    story_deltas = [result.get("story_delta") for result in results if result.get("story_delta") is not None]
    if story_deltas:
        quality_metrics["avg_story_delta"] = round(sum(story_deltas) / len(story_deltas), 3)
    elif not results:
        quality_metrics["avg_story_delta"] = None


def count_findings(text: str) -> int:
    """Count monitoring findings. Plain `- ` bullets under `# Findings`."""
    return len(re.findall(r"^- ", text, re.MULTILINE))


SPEC = WorkflowSpec(
    name="monitoring",
    config=WorkflowConfig(
        subdirs=["mentions", "stories", "synthesized", "anomalies", "recommendations"],
        default_timeout=1800,
        multiturn_timeout=7200,
        stall_limit=15,
        multiturn_max_turns=3000,
        default_client="",
        default_context="",
    ),
    config_dir_name="monitoring",
    configure_env=configure_env,
    pre_summary_hooks=pre_summary_hooks,
    snapshot_evaluations=snapshot_evaluations,
    completion_guard=completion_guard,
    list_deliverables=list_deliverables,
    augment_quality_metrics=augment_quality_metrics,
    count_findings=count_findings,
    findings_promotion=FindingsPromotionConfig(
        title="Global Findings: Monitoring & Brand Intelligence",
        confirmed_threshold=2,
        repeated_threshold=2,
    ),
)
