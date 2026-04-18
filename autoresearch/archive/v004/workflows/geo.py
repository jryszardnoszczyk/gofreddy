from __future__ import annotations

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


def completion_guard(_eval_summary: dict[str, object]) -> tuple[str | None, str | None]:
    return None, None


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


SPEC = WorkflowSpec(
    name="geo",
    config=WorkflowConfig(
        subdirs=["pages", "competitors", "optimized"],
        default_timeout=1800,
        multiturn_timeout=7200,
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
    findings_promotion=FindingsPromotionConfig(
        title="Global Findings: GEO",
        confirmed_threshold=3,
        repeated_threshold=2,
    ),
)
