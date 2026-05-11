"""linkedin_engine WorkflowSpec — sibling to x_engine; per master plan v13 §4.3.

Identical shape to `x_engine.py`. Both lanes share the same voice substrate
and re-`chmod 0444` it in `configure_env`. The two lanes' re-stamps commute
(same target file, same operation). Per-platform divergence lives in
`session_eval_linkedin_engine.py` (structural_gate hashtags ≤5, length
brackets short_take/thought_leader/case_study, slop-check linkedin) and the
evolvable `programs/linkedin_engine-session.md` register guidance."""
from __future__ import annotations

import os
import shutil
import stat
from pathlib import Path

from .eval_cache import read_cached_eval_if_fresh
from .specs import (
    FindingsPromotionConfig,
    RunScript,
    RunSessionEvaluator,
    WorkflowConfig,
    WorkflowSpec,
)


_VARIANT_ROOT = Path(__file__).resolve().parent.parent
_VOICE_SUBSTRATE = _VARIANT_ROOT / "programs" / "references" / "voice.md"


def configure_env(_client: str) -> None:
    """Re-chmod the voice substrate + propagate fixture context into env +
    materialize voice.md into current_runtime if missing.

    Mirrors ``x_engine.configure_env`` shape — see that docstring for the
    angle-routing rationale and the voice.md materialization rationale
    (P0 #104, 2026-05-08 evening). Substitutes LINKEDIN_ENGINE_ prefixes
    for the bridged env names. Both lanes' voice.md re-stamps + copies
    commute (same target file, same operation).
    """
    if _VOICE_SUBSTRATE.exists():
        try:
            os.chmod(_VOICE_SUBSTRATE, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        except OSError:
            pass

    angle_id = os.environ.get("AUTORESEARCH_CONTEXT", "").strip()
    if angle_id:
        os.environ["LINKEDIN_ENGINE_ANGLE_ID"] = angle_id
    session_dir = os.environ.get("AUTORESEARCH_SESSION_DIR", "").strip()
    if session_dir:
        os.environ["LINKEDIN_ENGINE_SESSION_DIR"] = session_dir

    # See x_engine.configure_env docstring §3 for the materialization rationale.
    runtime_root = _VARIANT_ROOT.parent / "current_runtime"
    runtime_voice = runtime_root / "programs" / "references" / "voice.md"
    if (
        _VOICE_SUBSTRATE.exists()
        and runtime_root.exists()
        and not runtime_voice.exists()
    ):
        try:
            runtime_voice.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(_VOICE_SUBSTRATE, runtime_voice)
            os.chmod(
                runtime_voice, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH,
            )
        except OSError:
            pass


def pre_summary_hooks(session_dir: Path, client: str, run_script: RunScript) -> None:
    """No-op — mirrors competitive.py + x_engine.py."""
    return


def snapshot_evaluations(
    session_dir: Path, run_session_evaluator: RunSessionEvaluator
) -> dict[str, object]:
    """Per-draft KEEP/REVISE decisions for the completion guard."""
    drafts_dir = session_dir / "drafts"
    if not drafts_dir.exists():
        return {"draft_decisions": []}

    decisions: list[dict[str, object]] = []
    for artifact in sorted(drafts_dir.glob("*.md")):
        eval_path = artifact.with_suffix(".eval.json")
        cached = read_cached_eval_if_fresh(artifact, eval_path)
        if cached is not None:
            decisions.append({
                "artifact": str(artifact.relative_to(session_dir)),
                "decision": cached.get("decision"),
            })
            continue
        data = run_session_evaluator(
            "linkedin_engine", artifact, session_dir, eval_path, "full"
        )
        decisions.append({
            "artifact": str(artifact.relative_to(session_dir)),
            "decision": (data or {}).get("decision"),
        })
    return {"draft_decisions": decisions}


def completion_guard(
    eval_summary: dict[str, object],
) -> tuple[str | None, str | None]:
    """KEEP if any draft's decision is KEEP; otherwise downgrade for retry."""
    decisions = eval_summary.get("draft_decisions") or []
    if any((d or {}).get("decision") == "KEEP" for d in decisions):
        return None, None
    return (
        "RUNNING",
        "no ship-eligible drafts produced; downgrading session for retry.",
    )


def list_deliverables(session_dir: Path) -> list[str]:
    drafts_dir = session_dir / "drafts"
    if not drafts_dir.exists():
        return []
    return sorted(
        f"drafts/{p.name}" for p in drafts_dir.iterdir() if p.is_file()
    )


def augment_quality_metrics(results: list[dict], quality_metrics: dict) -> None:
    return


def count_findings(text: str) -> int:
    return 0


SPEC = WorkflowSpec(
    name="linkedin_engine",
    config=WorkflowConfig(
        subdirs=["angles", "drafts"],
        default_timeout=1800,
        multiturn_timeout=7200,
        stall_limit=5,
        default_client="jr",
        default_context="",
        multiturn_max_turns=2500,
    ),
    config_dir_name="linkedin_engine",
    configure_env=configure_env,
    pre_summary_hooks=pre_summary_hooks,
    snapshot_evaluations=snapshot_evaluations,
    completion_guard=completion_guard,
    list_deliverables=list_deliverables,
    augment_quality_metrics=augment_quality_metrics,
    count_findings=count_findings,
    findings_promotion=FindingsPromotionConfig(
        title="Global Findings: LinkedIn Engine",
        confirmed_threshold=2,
        repeated_threshold=2,
    ),
    # Auto-render the HTML+PDF report once the session reaches COMPLETE.
    # post_session.post_session_hooks looks at this attr; lanes that omit
    # it skip auto-render. AUTORESEARCH_AUTO_RENDER=0 globally disables
    # auto-render at the post-session-hook layer.
    render_report=lambda sd, c, rs: rs(
        "render_report.py", str(sd), "linkedin_engine", c,
    ),
)
