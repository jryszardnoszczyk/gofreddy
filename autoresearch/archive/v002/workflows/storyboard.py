from __future__ import annotations

import os
from pathlib import Path

from .eval_cache import read_cached_eval_if_fresh
from .specs import FindingsPromotionConfig, RunScript, RunSessionEvaluator, WorkflowConfig, WorkflowSpec


def configure_env(client: str) -> None:
    os.environ.setdefault("CREATOR_HANDLE", client)
    os.environ.setdefault("STORYBOARD_COUNT", "5")


def pre_summary_hooks(_session_dir: Path, _client: str, _run_script: RunScript) -> None:
    return


def snapshot_evaluations(session_dir: Path, run_session_evaluator: RunSessionEvaluator) -> dict[str, object]:
    story_decisions: list[dict[str, str | None]] = []
    eval_dir = session_dir / "evals"
    for artifact in sorted((session_dir / "stories").glob("*.json")):
        output_path = eval_dir / f"story-{artifact.stem}.json"
        cached = read_cached_eval_if_fresh(artifact, output_path)
        if cached is not None:
            story_decisions.append({"artifact": artifact.name, "decision": cached["decision"]})
            continue
        data = run_session_evaluator("storyboard", artifact, session_dir, output_path, "full")
        story_decisions.append({"artifact": artifact.name, "decision": data.get("decision") if data else None})
    return {"story_decisions": story_decisions}


def completion_guard(eval_summary: dict[str, object]) -> tuple[str | None, str | None]:
    decisions = [item for item in eval_summary.get("story_decisions", []) if isinstance(item, dict)]
    if decisions and any(item.get("decision") != "KEEP" for item in decisions):
        note = "At least one storyboard plan failed final session evaluation; rerun PLAN_STORY/IDEATE before marking COMPLETE."
        return note, "stories/*.json"
    return None, None


def list_deliverables(session_dir: Path) -> list[str]:
    deliverables: list[str] = []
    if (session_dir / "report.md").exists():
        deliverables.append("report.md")
    storyboards_dir = session_dir / "storyboards"
    if storyboards_dir.exists():
        deliverables.extend(f"storyboards/{path.name}" for path in storyboards_dir.iterdir() if path.is_file())
    return deliverables


def augment_quality_metrics(results: list[dict], quality_metrics: dict) -> None:
    scene_scores = [result.get("scene_score") for result in results if result.get("scene_score") is not None]
    if scene_scores:
        quality_metrics["avg_scene_score"] = round(sum(scene_scores) / len(scene_scores), 3)


SPEC = WorkflowSpec(
    name="storyboard",
    config=WorkflowConfig(
        subdirs=["patterns", "stories", "storyboards", "frames", "clips"],
        default_timeout=1800,
        multiturn_timeout=7200,
        stall_limit=5,
        default_client="Gossip.Goblin",
        default_context="youtube",
        multiturn_max_turns=3000,
    ),
    config_dir_name="storyboard",
    configure_env=configure_env,
    pre_summary_hooks=pre_summary_hooks,
    snapshot_evaluations=snapshot_evaluations,
    completion_guard=completion_guard,
    list_deliverables=list_deliverables,
    augment_quality_metrics=augment_quality_metrics,
    findings_promotion=FindingsPromotionConfig(
        title="Global Findings: Storyboard",
        confirmed_threshold=2,
        repeated_threshold=2,
    ),
)
