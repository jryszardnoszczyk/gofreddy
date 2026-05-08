"""x_engine WorkflowSpec — per master plan v13 §4.3.

Mirrors the shape of `competitive.py` (NOT geo.py — geo's pre_summary_hooks
runs scripts that don't apply to drafts-as-deliverables). Per-fixture session
produces 3-5 ship-eligible X drafts under `drafts/<draft_id>.md`. The shared
voice substrate at `programs/references/voice.md` is locked READ-ONLY by both
this lane's `LaneSpec.readonly_subprefixes` AND linkedin_engine's. Per-session
re-`chmod 0444` runs in `configure_env` (idempotent; both lanes re-chmod the
same file)."""
from __future__ import annotations

import os
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


# Variant root resolution: `<variant>/workflows/x_engine.py.parent.parent ==
# <variant>`. The shared voice substrate lives at
# `<variant>/programs/references/voice.md`.
_VARIANT_ROOT = Path(__file__).resolve().parent.parent
_VOICE_SUBSTRATE = _VARIANT_ROOT / "programs" / "references" / "voice.md"


def configure_env(_client: str) -> None:
    """Re-chmod the voice substrate + propagate fixture context into env.

    Two responsibilities:

    1) Re-stamp `programs/references/voice.md` to 0444 (defence-in-depth on
       top of prepare_meta_workspace's chmod; the meta-agent has Write+Edit
       tools and could chmod +w the substrate before mutation).

    2) Bridge the lane-agnostic ``AUTORESEARCH_CONTEXT`` (set by run.py from
       the fixture's context arg) into the lane-specific
       ``X_ENGINE_ANGLE_ID``, and bridge ``AUTORESEARCH_SESSION_DIR`` into
       ``X_ENGINE_SESSION_DIR``. The session.md prompt expects these names so
       the agent loads the routed angle from `xeng angle-show $ANGLE_ID`
       instead of falling back to `xeng angle-list` and picking the latest.
       Without this bridge, every fixture's session would pick the same
       latest angle regardless of fixture id (observed 2026-05-08 evening
       substrate sweep).
    """
    if _VOICE_SUBSTRATE.exists():
        try:
            os.chmod(_VOICE_SUBSTRATE, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        except OSError:
            # Permission errors here are non-fatal — the substrate may be on a
            # filesystem that doesn't support chmod (e.g. mounted volumes); the
            # downstream readonly check still fires on edit attempts.
            pass

    angle_id = os.environ.get("AUTORESEARCH_CONTEXT", "").strip()
    if angle_id:
        os.environ["X_ENGINE_ANGLE_ID"] = angle_id
    session_dir = os.environ.get("AUTORESEARCH_SESSION_DIR", "").strip()
    if session_dir:
        os.environ["X_ENGINE_SESSION_DIR"] = session_dir


def pre_summary_hooks(session_dir: Path, client: str, run_script: RunScript) -> None:
    """No-op — the x_engine lane has no pre-summary script to run.

    geo.py runs `allocate_gaps.py` + `build_geo_report.py`; competitive.py
    runs nothing; both new lanes mirror competitive's no-op."""
    return


def snapshot_evaluations(
    session_dir: Path, run_session_evaluator: RunSessionEvaluator
) -> dict[str, object]:
    """Iterate every `drafts/*.md` artifact, run the in-session evaluator,
    return per-draft KEEP/REVISE decisions for the completion guard."""
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
            "x_engine", artifact, session_dir, eval_path, "full"
        )
        decisions.append({
            "artifact": str(artifact.relative_to(session_dir)),
            "decision": (data or {}).get("decision"),
        })
    return {"draft_decisions": decisions}


def completion_guard(
    eval_summary: dict[str, object],
) -> tuple[str | None, str | None]:
    """KEEP if any draft's decision is KEEP; otherwise return RUNNING note.

    A session that produces zero ship-eligible drafts is downgraded — better
    to surface "no ship eligible" loudly than mark COMPLETE on regression."""
    decisions = eval_summary.get("draft_decisions") or []
    if any((d or {}).get("decision") == "KEEP" for d in decisions):
        return None, None
    return (
        "RUNNING",
        "no ship-eligible drafts produced; downgrading session for retry.",
    )


def list_deliverables(session_dir: Path) -> list[str]:
    """All `drafts/*.md` files relative to session_dir."""
    drafts_dir = session_dir / "drafts"
    if not drafts_dir.exists():
        return []
    return sorted(
        f"drafts/{p.name}" for p in drafts_dir.iterdir() if p.is_file()
    )


def augment_quality_metrics(results: list[dict], quality_metrics: dict) -> None:
    """No-op v1 — drafts ARE the deliverables; per-fixture metrics live in
    the judge's per_criterion array, not a separate quality-score field."""
    return


def count_findings(text: str) -> int:
    """Return 0 — drafts ARE the deliverables; no findings.md is parsed.

    Per master plan v13 §4.3: the lane has no findings.md gate; the agent
    may write one for cross-draft observations but it's optional and not
    counted against any threshold."""
    return 0


SPEC = WorkflowSpec(
    name="x_engine",
    config=WorkflowConfig(
        subdirs=["angles", "drafts"],
        default_timeout=1800,
        multiturn_timeout=7200,
        stall_limit=5,
        default_client="jr",
        default_context="",  # fixture context is angle_id; agent reads from env
        multiturn_max_turns=2500,
    ),
    config_dir_name="x_engine",
    configure_env=configure_env,
    pre_summary_hooks=pre_summary_hooks,
    snapshot_evaluations=snapshot_evaluations,
    completion_guard=completion_guard,
    list_deliverables=list_deliverables,
    augment_quality_metrics=augment_quality_metrics,
    count_findings=count_findings,
    findings_promotion=FindingsPromotionConfig(
        title="Global Findings: X Engine",
        confirmed_threshold=2,
        repeated_threshold=2,
    ),
)
