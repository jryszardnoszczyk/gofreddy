"""Marketing audit workflow lane (autoresearch L1.5 integration).

L2 of the marketing-audit master plan ships the gated `freddy audit` CLI
pipeline (src/audit/, intake → payment → ship gates). This module wires
the same MA-1..MA-8 rubrics into an autoresearch session-loop consumption
mode so the lane can be evolved/scored alongside geo/competitive/etc.

Mirrors competitive.py shape — single-deliverable scoring on `findings.md`,
plus the report.{md,json,html,pdf} cluster from src/audit/. The agent's
session prompt lives at v006/programs/marketing_audit-session.md.

L3 work (Stage 2 sub-agents, Phase-0 framing, capability_registry, render
harness) is a separate multi-week build per master plan §3.5/§7.4.
"""
from __future__ import annotations

import re
from pathlib import Path

from .eval_cache import read_cached_eval_if_fresh
from .specs import FindingsPromotionConfig, RunScript, RunSessionEvaluator, WorkflowConfig, WorkflowSpec


def configure_env(_client: str) -> None:
    return


def pre_summary_hooks(_session_dir: Path, _client: str, _run_script: RunScript) -> None:
    return


def snapshot_evaluations(session_dir: Path, run_session_evaluator: RunSessionEvaluator) -> dict[str, object]:
    artifact = session_dir / "findings.md"
    eval_path = session_dir / "eval_feedback.json"

    cached = read_cached_eval_if_fresh(artifact, eval_path)
    if cached is not None:
        return {"findings_decision": cached["decision"]}

    data = run_session_evaluator("marketing_audit", artifact, session_dir, eval_path, "full")
    return {"findings_decision": data.get("decision") if data else None}


def completion_guard(eval_summary: dict[str, object]) -> tuple[str | None, str | None]:
    decision = eval_summary.get("findings_decision")
    if decision == "KEEP":
        return None, None
    note = f"Final findings.md session evaluation is {decision or 'missing'}; rerun SYNTHESIZE before marking COMPLETE."
    return note, "findings.md"


def list_deliverables(session_dir: Path) -> list[str]:
    """Marketing audit ships findings.md as primary + the report.{md,json,html,pdf}
    cluster + optional proposal.md + gap_report.md (per master plan + lane_registry)."""
    deliverables: list[str] = []
    for name in ("findings.md", "report.md", "report.json", "report.html", "report.pdf",
                 "proposal.md", "gap_report.md"):
        if (session_dir / name).exists():
            deliverables.append(name)
    return deliverables


def augment_quality_metrics(results: list[dict], quality_metrics: dict) -> None:
    """Optional: surface severity distribution + gap_flagged count if the agent
    emitted them. Best-effort — drop silently if missing."""
    severities = [r.get("severity_max") for r in results if r.get("severity_max") is not None]
    parsed: list[float] = []
    for s in severities:
        try:
            parsed.append(float(s))
        except (TypeError, ValueError):
            continue
    if parsed:
        quality_metrics["avg_severity_max"] = round(sum(parsed) / len(parsed), 2)
    gap_count = sum(1 for r in results if r.get("gap_flagged"))
    if gap_count:
        quality_metrics["gap_flagged_count"] = gap_count


def count_findings(text: str) -> int:
    """Marketing audit findings.md is organized into ParentFinding sections.
    Count the higher of: (a) `### ` ParentFinding headers, (b) `- ` bullet
    lines (per-section evidence rolls up under each ParentFinding)."""
    parent_finding_headers = len(re.findall(r"^### ", text, re.MULTILINE))
    bullets = len(re.findall(r"^- ", text, re.MULTILINE))
    section_headers = len(re.findall(r"^## ", text, re.MULTILINE))
    return max(parent_finding_headers, bullets, section_headers)


SPEC = WorkflowSpec(
    name="marketing_audit",
    config=WorkflowConfig(
        # Marketing audit produces a multi-section findings doc + report cluster.
        # subdirs declared per master plan §6.4 (Stage 2 per-agent output dirs).
        subdirs=["findability", "narrative", "acquisition", "experience", "phase0", "lens_outputs"],
        default_timeout=2400,           # marketing audit synthesis is slower than competitive
        multiturn_timeout=10800,
        stall_limit=7,                  # tolerates more iters — multi-stage pipeline
        default_client="Anthropic",
        default_context="https://www.anthropic.com",
        multiturn_max_turns=3000,
    ),
    config_dir_name="marketing_audit",
    configure_env=configure_env,
    pre_summary_hooks=pre_summary_hooks,
    snapshot_evaluations=snapshot_evaluations,
    completion_guard=completion_guard,
    list_deliverables=list_deliverables,
    augment_quality_metrics=augment_quality_metrics,
    count_findings=count_findings,
    findings_promotion=FindingsPromotionConfig(
        title="Global Findings: Marketing Audit",
        confirmed_threshold=2,
        repeated_threshold=2,
    ),
    # A3: Lane opts into post-session HTML+PDF rendering. The composer is
    # mostly a thin pointer to the Stage-5 deliverable from src/audit/stages.py
    # (which produces the canonical report.html via Jinja2 + WeasyPrint).
    # Stage-5 mirrors its output into this session dir at report.html /
    # report.pdf, so the composer either short-circuits to "see Stage-5
    # deliverable" or composes minimally from session-level artifacts.
    render_report=lambda sd, c, rs: rs("render_report.py", str(sd), "marketing_audit", c),
)
