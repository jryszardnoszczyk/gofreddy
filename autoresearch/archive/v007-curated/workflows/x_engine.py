"""x_engine WorkflowSpec — per master plan v13 §4.3.

Per U12 (Content Engine Lanes v1 — R20 direct cutover, TD-19; mirrors
U11 for linkedin_engine): the voice substrate is sourced from a shared
`VoicePersona` spec (see `src/voice/persona.py`) rather than the
per-lane `programs/references/voice.md` file. The persona slug is
resolved at session start via the `X_ENGINE_VOICE_PERSONA_REF` env
var; configure_env compiles the persona's corpus + voice_rules +
style_anchors via `src.voice.persona.compile_substrate` and writes
the result to `current_runtime/programs/references/voice.md`, where
the existing session.md + judge service continue to read it. No
toggle, no fallback — fixtures + operator wiring must set the env var.

Mirrors the shape of `competitive.py` (NOT geo.py — geo's
pre_summary_hooks runs scripts that don't apply to drafts-as-
deliverables). Per-fixture session produces 3-5 ship-eligible X drafts
under `drafts/<draft_id>.md`.

The legacy variant-tree `programs/references/voice.md` is preserved
for diff/blame history. After both U11 + U12 land it has no live
reader — the jr persona corpus is the new source of truth. A
follow-up cleanup commit may delete the legacy file + drop it from
`lane_registry.path_prefixes`."""
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
# <variant>`. The compiled substrate is written into the runtime root
# (`<variant>.parent / "current_runtime" / "programs" / "references" / "voice.md"`).
_VARIANT_ROOT = Path(__file__).resolve().parent.parent


def configure_env(_client: str) -> None:
    """Compile + materialize the persona-sourced voice substrate +
    propagate fixture context into env.

    Per U12 (R20 / TD-19; mirrors U11): direct cutover from per-lane
    voice.md to shared `VoicePersona` spec. `X_ENGINE_VOICE_PERSONA_REF`
    is REQUIRED — the lane cannot run without an assigned persona.

    Raises:
        RuntimeError: when `X_ENGINE_VOICE_PERSONA_REF` is unset or
            resolves to a persona with an empty corpus.
        src.voice.persona.VoicePersonaNotFoundError: when the referenced
            persona YAML does not exist.
    """
    # Lazy import — see linkedin_engine.configure_env for the rationale
    # (subprocess contexts may not have src/ on sys.path; we want module
    # import to stay robust and configure_env to fail loud at call time).
    from src.voice.persona import compile_substrate, load_corpus_files, load_persona

    persona_ref = os.environ.get("X_ENGINE_VOICE_PERSONA_REF", "").strip()
    if not persona_ref:
        raise RuntimeError(
            "X_ENGINE_VOICE_PERSONA_REF is required (U12 direct cutover, "
            "no toggle per TD-19). Set it via the fixture env block or "
            "operator wiring to a persona slug from voice_personas/"
            "<slug>.yaml — e.g., 'jr' (default), 'dr_maria' (Klinika), "
            "'partner_jamka' (DWF)."
        )
    persona = load_persona(persona_ref)
    corpus = load_corpus_files(persona)
    if not corpus:
        raise RuntimeError(
            f"persona {persona_ref!r} resolves to an empty corpus at "
            f"{persona.corpus_path}. x_engine cannot run without voice "
            f"substrate content. Author corpus files (.md or .pdf) or "
            f"verify the consent gate (Content Engine v1 §Compliance "
            f"Posture parallel-track risk #1)."
        )

    substrate_text = compile_substrate(persona, corpus)

    runtime_voice = (
        _VARIANT_ROOT.parent / "current_runtime"
        / "programs" / "references" / "voice.md"
    )
    runtime_voice.parent.mkdir(parents=True, exist_ok=True)
    # Unlink first: the prior session may have left the file 0444. The
    # compile output replaces the file content fully — no diff to keep.
    runtime_voice.unlink(missing_ok=True)
    runtime_voice.write_text(substrate_text, encoding="utf-8")
    try:
        os.chmod(runtime_voice, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    except OSError:
        # Best-effort — proceeds with default perms on filesystems that
        # don't support chmod (CI containers, some network mounts).
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
    # Auto-render the HTML+PDF report once the session reaches COMPLETE.
    # post_session.post_session_hooks looks at this attr; lanes that omit
    # it skip auto-render. AUTORESEARCH_AUTO_RENDER=0 globally disables
    # auto-render at the post-session-hook layer.
    render_report=lambda sd, c, rs: rs("render_report.py", str(sd), "x_engine", c),
)
