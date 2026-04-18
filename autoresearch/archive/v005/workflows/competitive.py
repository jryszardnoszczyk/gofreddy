from __future__ import annotations

from pathlib import Path

from .eval_cache import read_cached_eval_if_fresh
from .specs import FindingsPromotionConfig, RunScript, RunSessionEvaluator, WorkflowConfig, WorkflowSpec


def configure_env(_client: str) -> None:
    return


def pre_summary_hooks(session_dir: Path, client: str, run_script: RunScript) -> None:
    # format_report.py was the brief.md → report.md transform. report.md was
    # removed in Unit 13 of the autoresearch fix plan (run #6 triage) after
    # forensic analysis showed it was near-identical to brief.md and drifted
    # silently from it. The transform is no longer invoked.
    if (session_dir / "brief.md").exists():
        run_script("extract_prior_summary.py", str(session_dir), client)


def snapshot_evaluations(session_dir: Path, run_session_evaluator: RunSessionEvaluator) -> dict[str, object]:
    artifact = session_dir / "brief.md"
    eval_path = session_dir / "eval_feedback.json"

    cached = read_cached_eval_if_fresh(artifact, eval_path)
    if cached is not None:
        return {"brief_decision": cached["decision"]}

    data = run_session_evaluator("competitive", artifact, session_dir, eval_path, "full")
    return {"brief_decision": data.get("decision") if data else None}


def completion_guard(eval_summary: dict[str, object]) -> tuple[str | None, str | None]:
    decision = eval_summary.get("brief_decision")
    if decision == "KEEP":
        return None, None
    note = f"Final brief session evaluation is {decision or 'missing'}; rerun VERIFY before marking COMPLETE."
    return note, "brief.md"


def list_deliverables(session_dir: Path) -> list[str]:
    deliverables: list[str] = []
    # brief.md is the final deliverable for competitive. report.md was
    # previously listed here but was removed after the run #6 triage —
    # it was near-identical to brief.md (~35 diff lines across ~2K words),
    # invisible to the scorer, and drifted from brief.md in ways the
    # evaluator could not see. If the agent still writes it on older
    # sessions, the file is simply ignored now.
    if (session_dir / "brief.md").exists():
        deliverables.append("brief.md")
    analyses_dir = session_dir / "analyses"
    if analyses_dir.exists():
        deliverables.extend(f"analyses/{path.name}" for path in analyses_dir.iterdir() if path.is_file())
    return deliverables


def augment_quality_metrics(results: list[dict], quality_metrics: dict) -> None:
    scores = [result.get("quality_score") for result in results if result.get("quality_score")]
    parsed: list[float] = []
    for score in scores:
        if isinstance(score, str) and "/" in score:
            try:
                parsed.append(float(score.split("/")[0]))
            except ValueError:
                continue
        elif isinstance(score, (int, float)):
            parsed.append(float(score))
    if parsed:
        quality_metrics["avg_quality_score"] = round(sum(parsed) / len(parsed), 1)


SPEC = WorkflowSpec(
    name="competitive",
    config=WorkflowConfig(
        subdirs=["competitors", "analyses"],
        default_timeout=1800,
        multiturn_timeout=7200,
        stall_limit=5,
        default_client="figma",
        default_context="figma",
        multiturn_max_turns=2500,
    ),
    config_dir_name="competitive",
    configure_env=configure_env,
    pre_summary_hooks=pre_summary_hooks,
    snapshot_evaluations=snapshot_evaluations,
    completion_guard=completion_guard,
    list_deliverables=list_deliverables,
    augment_quality_metrics=augment_quality_metrics,
    findings_promotion=FindingsPromotionConfig(
        title="Global Findings: Competitive Intelligence",
        confirmed_threshold=2,
        repeated_threshold=2,
    ),
)
