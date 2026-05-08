from __future__ import annotations

import os
import re
from pathlib import Path

from .eval_cache import evaluate_artifact_glob
from .specs import FindingsPromotionConfig, RunScript, RunSessionEvaluator, WorkflowConfig, WorkflowSpec


def configure_env(client: str) -> None:
    os.environ.setdefault("CREATOR_HANDLE", client)
    os.environ.setdefault("STORYBOARD_COUNT", "5")


def pre_summary_hooks(_session_dir: Path, _client: str, _run_script: RunScript) -> None:
    return


def snapshot_evaluations(session_dir: Path, run_session_evaluator: RunSessionEvaluator) -> dict[str, object]:
    story_decisions = evaluate_artifact_glob(
        "storyboard", session_dir, "stories/*.json", "story", "full",
        run_session_evaluator,
    )
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


def count_findings(text: str) -> int:
    """Count storyboard findings. Legacy `### [` headers plus bullet-list
    summaries produced by newer iterations."""
    headers = len(re.findall(r"^### \[", text, re.MULTILINE))
    bullets = len(re.findall(r"^- ", text, re.MULTILINE))
    return max(headers, bullets)


SPEC = WorkflowSpec(
    name="storyboard",
    config=WorkflowConfig(
        subdirs=["patterns", "stories", "storyboards", "frames", "clips"],
        default_timeout=1800,
        multiturn_timeout=7200,
        # 2026-05-08 evening: raised 5→10 after live evidence that the lane's
        # analyze_patterns + plan_story phases legitimately consume 5+ minutes
        # of agent work between phase events (verified via TechReview run that
        # produced 11 patterns + 5 KEEP stories under stall_count). The prior
        # P1 audit conflated `max_iter` (hard ceiling) with `stall_limit` (idle
        # threshold) — they aren't comparable. The agent IS doing productive
        # work writing to patterns/, stories/, storyboards/, frames/ subdirs;
        # state_changed just doesn't see those writes between phase events.
        # Doubling the threshold buys the agent room to complete a long phase
        # without raising the false-positive risk the audit was guarding (the
        # cyber-flag stub-file concern was about a different lane's behavior).
        stall_limit=10,
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
    count_findings=count_findings,
    findings_promotion=FindingsPromotionConfig(
        title="Global Findings: Storyboard",
        confirmed_threshold=2,
        repeated_threshold=2,
    ),
    render_report=lambda sd, c, rs: rs("render_report.py", str(sd), "storyboard", c),  # B-storyboard
)
