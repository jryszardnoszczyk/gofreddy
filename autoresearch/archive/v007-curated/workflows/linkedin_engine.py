"""linkedin_engine WorkflowSpec — sibling to x_engine; per master plan v13 §4.3.

Per U11 (Content Engine Lanes v1 — R20 direct cutover, TD-19): the voice
substrate is sourced from a shared `VoicePersona` spec (see
`src/voice/persona.py`) rather than the per-lane `programs/references/
voice.md` file. The persona slug is resolved at session start via the
`LINKEDIN_ENGINE_VOICE_PERSONA_REF` env var; configure_env compiles the
persona's corpus + voice_rules + style_anchors into a markdown substrate
written to `current_runtime/programs/references/voice.md`, where the
existing session.md + judge service continue to read it. No toggle, no
fallback — fixtures + operator wiring must set the env var.

The legacy variant-tree `programs/references/voice.md` is preserved for
x_engine (which still consumes it pre-U12) and to keep diff/blame history
intact. linkedin_engine no longer reads it.

Per-platform divergence lives in `session_eval_linkedin_engine.py`
(structural_gate hashtags ≤5, length brackets short_take/thought_leader/
case_study, slop-check linkedin) and the evolvable
`programs/linkedin_engine-session.md` register guidance."""
from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import TYPE_CHECKING

from .eval_cache import read_cached_eval_if_fresh
from .specs import (
    FindingsPromotionConfig,
    RunScript,
    RunSessionEvaluator,
    WorkflowConfig,
    WorkflowSpec,
)

if TYPE_CHECKING:
    from src.voice.persona import CorpusFile, VoicePersona


_VARIANT_ROOT = Path(__file__).resolve().parent.parent


def _compile_voice_substrate(
    persona: "VoicePersona", corpus_files: list["CorpusFile"],
) -> str:
    """Concatenate persona corpus + optional rules/anchors into a single
    markdown substrate string.

    For the default `jr` persona (single corpus file, empty voice_rules,
    empty style_anchors) the output is bit-identical to the pre-U11
    `programs/references/voice.md` content — preserves D10 regression
    bar without per-fixture re-baselining.

    Multi-corpus personas (Klinika, DWF) get a separator-joined corpus
    body plus a Voice Rules bullet section and a Style Anchors section
    so the agent + judge see the full persona definition in a single
    substrate file.
    """
    parts = [cf.text for cf in corpus_files]
    body = "\n\n---\n\n".join(parts) if len(parts) > 1 else parts[0]

    suffix = ""
    if persona.voice_rules:
        bullets = "\n".join(f"- {rule}" for rule in persona.voice_rules)
        suffix += f"\n\n## Voice Rules\n\n{bullets}\n"
    if persona.style_anchors:
        chunks = [
            f"### {name}\n\n{prose.rstrip()}"
            for name, prose in persona.style_anchors.items()
        ]
        suffix += "\n\n## Style Anchors\n\n" + "\n\n".join(chunks) + "\n"
    return body + suffix


def configure_env(_client: str) -> None:
    """Compile + materialize the persona-sourced voice substrate +
    propagate fixture context into env.

    Per U11 (R20 / TD-19): direct cutover from per-lane voice.md to
    shared `VoicePersona` spec. `LINKEDIN_ENGINE_VOICE_PERSONA_REF`
    is REQUIRED — the lane cannot run without an assigned persona.

    Raises:
        RuntimeError: when `LINKEDIN_ENGINE_VOICE_PERSONA_REF` is unset
            or resolves to a persona with an empty corpus.
        src.voice.persona.VoicePersonaNotFoundError: when the referenced
            persona YAML does not exist.
    """
    # Lazy import: lane modules may be loaded in subprocess contexts where
    # `src/` is not on sys.path. Defer the import to call time so module
    # import stays robust; configure_env crashes loudly at call time if
    # the substrate state is broken (which is the correct failure mode).
    from src.voice.persona import load_corpus_files, load_persona

    persona_ref = os.environ.get("LINKEDIN_ENGINE_VOICE_PERSONA_REF", "").strip()
    if not persona_ref:
        raise RuntimeError(
            "LINKEDIN_ENGINE_VOICE_PERSONA_REF is required (U11 direct "
            "cutover, no toggle per TD-19). Set it via the fixture env "
            "block or operator wiring to a persona slug from "
            "voice_personas/<slug>.yaml — e.g., 'jr' (default), "
            "'dr_maria' (Klinika), 'partner_jamka' (DWF)."
        )
    persona = load_persona(persona_ref)
    corpus = load_corpus_files(persona)
    if not corpus:
        raise RuntimeError(
            f"persona {persona_ref!r} resolves to an empty corpus at "
            f"{persona.corpus_path}. linkedin_engine cannot run without "
            f"voice substrate content. Author corpus files (.md or .pdf) "
            f"or verify the consent gate (Content Engine v1 §Compliance "
            f"Posture parallel-track risk #1)."
        )

    substrate_text = _compile_voice_substrate(persona, corpus)

    runtime_voice = (
        _VARIANT_ROOT.parent / "current_runtime"
        / "programs" / "references" / "voice.md"
    )
    runtime_voice.parent.mkdir(parents=True, exist_ok=True)
    # Unlink first: the prior file may be 0444 (re-chmodded by an earlier
    # session) which would block write_text. The compile output replaces
    # the file content fully — there's no diff to preserve.
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
        os.environ["LINKEDIN_ENGINE_ANGLE_ID"] = angle_id
    session_dir = os.environ.get("AUTORESEARCH_SESSION_DIR", "").strip()
    if session_dir:
        os.environ["LINKEDIN_ENGINE_SESSION_DIR"] = session_dir


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
