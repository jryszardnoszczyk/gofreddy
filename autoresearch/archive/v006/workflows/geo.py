from __future__ import annotations

import re
from pathlib import Path

from .specs import FindingsPromotionConfig, RunScript, RunSessionEvaluator, WorkflowConfig, WorkflowSpec


def configure_env(_client: str) -> None:
    return


def pre_summary_hooks(session_dir: Path, _client: str, run_script: RunScript) -> None:
    gap_file = session_dir / "gap_allocation.json"
    has_pages = (session_dir / "pages").exists() and any((session_dir / "pages").glob("*.json"))
    if has_pages and not gap_file.exists():
        run_script("allocate_gaps.py", str(session_dir))
    run_script("build_geo_report.py", str(session_dir))


def snapshot_evaluations(session_dir: Path, run_session_evaluator: RunSessionEvaluator) -> dict[str, object]:
    decisions: list[dict[str, str | None]] = []
    eval_dir = session_dir / "evals"
    for artifact in sorted((session_dir / "optimized").glob("*.md")):
        output_path = eval_dir / f"optimized-{artifact.stem}.json"
        data = run_session_evaluator("geo", artifact, session_dir, output_path, "full")
        decisions.append({"artifact": artifact.name, "decision": data.get("decision") if data else None})
    return {"optimized_decisions": decisions}


def completion_guard(eval_summary: dict[str, object]) -> tuple[str | None, str | None]:
    """P1: enforce that GEO sessions declaring COMPLETE actually produced
    deliverables. Pre-fix this returned (None, None) unconditionally, so
    a geo agent could write `## Status: COMPLETE` with zero `optimized/*.md`
    files and zero `report.md` and the loop would exit clean.

    Returns (downgrade_to_status, reason) — both None means "accept COMPLETE";
    a non-None first element means "downgrade and continue".
    """
    decisions = eval_summary.get("optimized_decisions") if isinstance(eval_summary, dict) else None
    if isinstance(decisions, list) and len(decisions) > 0:
        # At least one optimized page was evaluated — that's a real
        # deliverable. Accept COMPLETE.
        return None, None
    # No optimized pages = nothing to ship. Downgrade so the loop continues.
    return "RUNNING", "no optimized/*.md deliverables produced; downgrading"


def list_deliverables(session_dir: Path) -> list[str]:
    deliverables: list[str] = []
    if (session_dir / "report.md").exists():
        deliverables.append("report.md")
    optimized_dir = session_dir / "optimized"
    if optimized_dir.exists():
        deliverables.extend(f"optimized/{path.name}" for path in optimized_dir.iterdir() if path.is_file())
    return deliverables


def augment_quality_metrics(_results: list[dict], _quality_metrics: dict) -> None:
    return


def count_findings(text: str) -> int:
    """Count geo findings. Current format: `- CATEGORY: …` bullets under
    `## Confirmed` / `## Disproved` sections. Falls back to `### [` headers
    used by older geo formats."""
    bullets = len(re.findall(r"^- (CONTENT|QUALITY|INFRA|SCHEMA):", text, re.MULTILINE))
    headers = len(re.findall(r"^### \[", text, re.MULTILINE))
    plain_bullets = len(re.findall(r"^- ", text, re.MULTILINE))
    return max(bullets, headers, plain_bullets)


SPEC = WorkflowSpec(
    name="geo",
    config=WorkflowConfig(
        subdirs=["pages", "competitors", "optimized"],
        default_timeout=1800,
        multiturn_timeout=7200,
        # P1 audit: v001 had stall_limit=5; v006 silently raised to 15 with no
        # commit message rationale. Combined with 5-10min/iteration latency,
        # 15 burns 75-150 min before bailing on stuck sessions. Reverted to 5.
        stall_limit=5,
        max_wall_time_seconds=6000,
        default_client="semrush",
        default_context="https://www.semrush.com",
        multiturn_max_turns=2500,
    ),
    config_dir_name="seo",
    configure_env=configure_env,
    pre_summary_hooks=pre_summary_hooks,
    snapshot_evaluations=snapshot_evaluations,
    completion_guard=completion_guard,
    list_deliverables=list_deliverables,
    augment_quality_metrics=augment_quality_metrics,
    count_findings=count_findings,
    findings_promotion=FindingsPromotionConfig(
        title="Global Findings: GEO",
        confirmed_threshold=3,
        repeated_threshold=2,
    ),
)
