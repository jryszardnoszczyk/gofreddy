"""image_engine WorkflowSpec — per Content Engine Lanes v1 U14 + master plan §4.6 + TD-41.

Image_engine produces composed final images across 6 formats:
- ig_single        (1080x1080 Instagram single)
- ig_carousel      (5-10 x 1080x1080 Instagram carousel)
- ig_story         (1080x1920 Instagram story)
- li_doc_carousel  (8-12 x 1080x1080 LinkedIn document carousel)
- hero_banner      (1600x900 website hero)
- ad_static        (platform-specific; text-overlay <20% pixel area)

Per TD-41: single workflow with format dispatch. ~70% shared pipeline
(topic → angle → fal source generation → brand-stamp → alt-text →
caption → judge); per-format divergence in composition strategy +
skeleton template + rubric weights. Six separate lanes would 6× the
meta-agent mutation surface for ~3 surfaces of real divergence.

Per JR's 2026-05-19 U14 decisions:
- All 6 formats ship in v1 (full scope).
- Vision judge backend = Gemini 3 Flash Preview (D24 originally said 2.5).
- Two-step carousel storytelling per plan: outline pass + per-slide
  fal-prompts with previous-slide visual context echoed.

`configure_env` reads:
- `IMAGE_ENGINE_TOPIC`               — required
- `IMAGE_ENGINE_FORMAT`              — required (one of the 6 above)
- `IMAGE_ENGINE_VOICE_PERSONA_REF`   — required (for alt-text + caption voice)
- `IMAGE_ENGINE_BRAND_TOKENS_PATH`   — required (palette + typography)
- `IMAGE_ENGINE_BRIEFS_PATH`         — optional
"""
from __future__ import annotations

import os
import stat as _stat
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


ALLOWED_FORMATS: frozenset[str] = frozenset({
    "ig_single", "ig_carousel", "ig_story",
    "li_doc_carousel", "hero_banner", "ad_static",
})
"""Per U14 §scope: v1 image_engine ships all 6 formats."""


def configure_env(_client: str) -> None:
    """Validate U14 env vars + compile + materialize the persona-sourced
    voice substrate (for alt-text + caption voice consistency, IE-7).

    Same direct-cutover pattern as U11/U12/U13. The voice substrate
    governs alt-text + caption fidelity; the image's visual content
    is governed by brand_tokens + the topic. Vision rubrics (IE-1/2/
    3/5/6) score visual quality via vision_judge.py + Gemini 3 Flash
    Preview.

    Raises:
        RuntimeError: missing/invalid env vars or empty persona corpus.
    """
    from src.voice.persona import (
        compile_substrate,
        load_corpus_files,
        load_persona,
    )

    persona_ref = os.environ.get("IMAGE_ENGINE_VOICE_PERSONA_REF", "").strip()
    if not persona_ref:
        raise RuntimeError(
            "IMAGE_ENGINE_VOICE_PERSONA_REF is required (U14 direct cutover "
            "per TD-19). Voice persona governs IE-7 alt-text + caption "
            "voice consistency. Set via fixture env or operator wiring."
        )
    persona = load_persona(persona_ref)
    corpus = load_corpus_files(persona)
    if not corpus:
        raise RuntimeError(
            f"persona {persona_ref!r} resolves to an empty corpus at "
            f"{persona.corpus_path}. image_engine cannot generate "
            f"voice-consistent alt-text/captions without content."
        )
    substrate_text = compile_substrate(persona, corpus)

    runtime_voice = (
        _VARIANT_ROOT.parent / "current_runtime"
        / "programs" / "references" / "voice.md"
    )
    runtime_voice.parent.mkdir(parents=True, exist_ok=True)
    runtime_voice.unlink(missing_ok=True)
    runtime_voice.write_text(substrate_text, encoding="utf-8")
    try:
        os.chmod(runtime_voice, _stat.S_IRUSR | _stat.S_IRGRP | _stat.S_IROTH)
    except OSError:
        pass

    # --- Topic ---
    topic = os.environ.get("IMAGE_ENGINE_TOPIC", "").strip()
    if not topic:
        raise RuntimeError(
            "IMAGE_ENGINE_TOPIC is required. Set to the image subject "
            "(e.g., 'Botox aftercare protocols', 'KSeF timeline')."
        )

    # --- Format ---
    fmt = os.environ.get("IMAGE_ENGINE_FORMAT", "").strip()
    if not fmt:
        raise RuntimeError(
            f"IMAGE_ENGINE_FORMAT is required. Allowed: {sorted(ALLOWED_FORMATS)}."
        )
    if fmt not in ALLOWED_FORMATS:
        raise RuntimeError(
            f"IMAGE_ENGINE_FORMAT={fmt!r} not in supported set "
            f"{sorted(ALLOWED_FORMATS)}."
        )

    # --- Brand tokens path ---
    brand_tokens = os.environ.get("IMAGE_ENGINE_BRAND_TOKENS_PATH", "").strip()
    if not brand_tokens:
        raise RuntimeError(
            "IMAGE_ENGINE_BRAND_TOKENS_PATH is required — palette + "
            "typography hint baked into fal prompts per TD-41 brand-stamp "
            "approach (hex codes, not swatch images)."
        )

    # --- Pass-through env vars ---
    angle_id = os.environ.get("AUTORESEARCH_CONTEXT", "").strip()
    if angle_id:
        os.environ["IMAGE_ENGINE_ANGLE_ID"] = angle_id
    session_dir = os.environ.get("AUTORESEARCH_SESSION_DIR", "").strip()
    if session_dir:
        os.environ["IMAGE_ENGINE_SESSION_DIR"] = session_dir


def pre_summary_hooks(session_dir: Path, client: str, run_script: RunScript) -> None:
    """No-op — drafts ARE the deliverables (composed PNGs)."""
    return


def snapshot_evaluations(
    session_dir: Path, run_session_evaluator: RunSessionEvaluator
) -> dict[str, object]:
    """Per-draft KEEP/REVISE decisions. For carousel drafts, each
    `drafts/<draft_id>/` directory of slides is treated as one
    artifact (the session_eval rolls slides into a single decision)."""
    drafts_dir = session_dir / "drafts"
    if not drafts_dir.exists():
        return {"draft_decisions": []}

    decisions: list[dict[str, object]] = []
    # Single images: drafts/*.png + drafts/*.jpg
    # Carousels: drafts/<draft_id>/slide_*.png — the carousel dir IS the artifact.
    for entry in sorted(drafts_dir.iterdir()):
        if entry.is_file() and entry.suffix in (".png", ".jpg"):
            artifact = entry
        elif entry.is_dir() and any(entry.glob("slide_*.png")):
            artifact = entry  # carousel dir
        else:
            continue
        # Use the .eval.json sibling (for files) or meta.json inside (for dirs)
        eval_path = (
            artifact.with_suffix(".eval.json")
            if artifact.is_file()
            else artifact / "eval.json"
        )
        cached = (
            read_cached_eval_if_fresh(artifact, eval_path)
            if artifact.is_file()
            else None  # carousel cache: re-evaluate every session
        )
        if cached is not None:
            decisions.append({
                "artifact": str(artifact.relative_to(session_dir)),
                "decision": cached.get("decision"),
            })
            continue
        data = run_session_evaluator(
            "image_engine", artifact, session_dir, eval_path, "full"
        )
        decisions.append({
            "artifact": str(artifact.relative_to(session_dir)),
            "decision": (data or {}).get("decision"),
        })
    return {"draft_decisions": decisions}


def completion_guard(
    eval_summary: dict[str, object],
) -> tuple[str | None, str | None]:
    """KEEP if any draft's decision is KEEP; otherwise downgrade."""
    decisions = eval_summary.get("draft_decisions") or []
    if any((d or {}).get("decision") == "KEEP" for d in decisions):
        return None, None
    return (
        "RUNNING",
        "no ship-eligible image drafts produced; downgrading session for retry.",
    )


def list_deliverables(session_dir: Path) -> list[str]:
    """Composed images (single PNG/JPG files) and carousel directories."""
    drafts_dir = session_dir / "drafts"
    if not drafts_dir.exists():
        return []
    out: list[str] = []
    for entry in sorted(drafts_dir.iterdir()):
        if entry.is_file() and entry.suffix in (".png", ".jpg"):
            out.append(f"drafts/{entry.name}")
        elif entry.is_dir() and any(entry.glob("slide_*.png")):
            slides = sorted(entry.glob("slide_*.png"))
            out.extend(f"drafts/{entry.name}/{s.name}" for s in slides)
    return out


def augment_quality_metrics(results: list[dict], quality_metrics: dict) -> None:
    """No-op — images ARE the deliverables."""
    return


def count_findings(text: str) -> int:
    """Return 0 — no findings.md gate for image_engine."""
    return 0


SPEC = WorkflowSpec(
    name="image_engine",
    config=WorkflowConfig(
        subdirs=["drafts"],
        default_timeout=3600,
        multiturn_timeout=10800,
        stall_limit=5,
        default_client="jr",
        default_context="",
        multiturn_max_turns=4000,
    ),
    config_dir_name="image_engine",
    configure_env=configure_env,
    pre_summary_hooks=pre_summary_hooks,
    snapshot_evaluations=snapshot_evaluations,
    completion_guard=completion_guard,
    list_deliverables=list_deliverables,
    augment_quality_metrics=augment_quality_metrics,
    count_findings=count_findings,
    findings_promotion=FindingsPromotionConfig(
        title="Global Findings: Image Engine",
        confirmed_threshold=2,
        repeated_threshold=2,
    ),
    render_report=lambda sd, c, rs: rs(
        "render_report.py", str(sd), "image_engine", c,
    ),
)
