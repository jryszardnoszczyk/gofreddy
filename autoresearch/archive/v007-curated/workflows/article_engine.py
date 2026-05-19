"""article_engine WorkflowSpec — per Content Engine Lanes v1 U13 + master plan §4.5.

Article_engine produces blog + LinkedIn Article drafts from topic +
voice persona + source material + optional findings-brief. Mirrors
x_engine's WorkflowSpec shape; the per-platform divergence lives in
`session_eval_article_engine.py` (structural gate enforces blog
schema.org / LinkedIn Article fold-safe hook / length brackets) and
the evolvable `programs/article_engine-session.md` register guidance.

Per U13 §judge wiring: voice substrate sourced from shared `VoicePersona`
spec (R20) via `ARTICLE_ENGINE_VOICE_PERSONA_REF` — same direct-cutover
pattern as U11 (linkedin_engine) + U12 (x_engine), no toggle.

`configure_env` reads:
- `ARTICLE_ENGINE_TOPIC`           — required (the article subject)
- `ARTICLE_ENGINE_VOICE_PERSONA_REF` — required (persona slug)
- `ARTICLE_ENGINE_TARGET_PLATFORMS` — required (csv: blog | linkedin_article)
- `ARTICLE_ENGINE_SOURCE_MATERIAL_PATHS` — optional (operator-curated handoff
   content; resolved from ClientConfig.source_material_paths at fixture
   time; the loader handles md + pdf + html per U13 JR decision)
- `ARTICLE_ENGINE_BRIEFS_PATH`     — optional (findings-brief root for
   the lane's brief consumer; consumption mode driven by ClientConfig.
   article_brief_consumption_mode)
"""
from __future__ import annotations

import os
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


ALLOWED_PLATFORMS: frozenset[str] = frozenset({"blog", "linkedin_article"})
"""Per U13 §scope: v1 article_engine ships TWO platforms. Any other
target requires a follow-up unit (e.g., Medium, Substack)."""


def configure_env(_client: str) -> None:
    """Validate U13 env vars + compile + materialize the persona-sourced
    voice substrate.

    Per U11 / U12 pattern: ARTICLE_ENGINE_VOICE_PERSONA_REF is REQUIRED.
    Direct cutover, no toggle per TD-19.

    Raises:
        RuntimeError: on missing/invalid required env vars or empty
            persona corpus.
    """
    # Lazy import — see linkedin_engine.configure_env for rationale.
    from src.voice.persona import (
        compile_substrate,
        load_corpus_files,
        load_persona,
    )
    import stat as _stat

    # --- Voice persona resolution (mirrors U11/U12) ---
    persona_ref = os.environ.get("ARTICLE_ENGINE_VOICE_PERSONA_REF", "").strip()
    if not persona_ref:
        raise RuntimeError(
            "ARTICLE_ENGINE_VOICE_PERSONA_REF is required (U13 direct cutover, "
            "no toggle per TD-19). Set it via the fixture env block or "
            "operator wiring to a persona slug from voice_personas/<slug>.yaml."
        )
    persona = load_persona(persona_ref)
    corpus = load_corpus_files(persona)
    if not corpus:
        raise RuntimeError(
            f"persona {persona_ref!r} resolves to an empty corpus at "
            f"{persona.corpus_path}. article_engine cannot run without "
            f"voice substrate content."
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
    topic = os.environ.get("ARTICLE_ENGINE_TOPIC", "").strip()
    if not topic:
        raise RuntimeError(
            "ARTICLE_ENGINE_TOPIC is required. The fixture or operator must "
            "set it to the article subject (e.g., 'KSeF e-invoicing for "
            "Polish SMBs', 'Botox aftercare protocols')."
        )

    # --- Target platforms (csv) ---
    platforms_raw = os.environ.get("ARTICLE_ENGINE_TARGET_PLATFORMS", "").strip()
    if not platforms_raw:
        raise RuntimeError(
            "ARTICLE_ENGINE_TARGET_PLATFORMS is required. Set as comma-"
            "separated list of platforms from "
            f"{sorted(ALLOWED_PLATFORMS)} (e.g., 'blog,linkedin_article')."
        )
    platforms = {p.strip() for p in platforms_raw.split(",") if p.strip()}
    invalid = platforms - ALLOWED_PLATFORMS
    if invalid:
        raise RuntimeError(
            f"ARTICLE_ENGINE_TARGET_PLATFORMS contains unsupported platforms: "
            f"{sorted(invalid)}. Allowed: {sorted(ALLOWED_PLATFORMS)}."
        )

    # --- Pass-through env vars (optional; agent reads them in session.md) ---
    # Source material + briefs paths are optional — empty article runs
    # land at the 3-claims-per-1000-words floor structurally.
    angle_id = os.environ.get("AUTORESEARCH_CONTEXT", "").strip()
    if angle_id:
        os.environ["ARTICLE_ENGINE_ANGLE_ID"] = angle_id
    session_dir = os.environ.get("AUTORESEARCH_SESSION_DIR", "").strip()
    if session_dir:
        os.environ["ARTICLE_ENGINE_SESSION_DIR"] = session_dir


def pre_summary_hooks(session_dir: Path, client: str, run_script: RunScript) -> None:
    """No-op — drafts ARE the deliverables."""
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
            "article_engine", artifact, session_dir, eval_path, "full"
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
        "no ship-eligible article drafts produced; downgrading session for retry.",
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
    """No-op — drafts ARE the deliverables; per-fixture metrics live in
    the judge's per_criterion array."""
    return


def count_findings(text: str) -> int:
    """Return 0 — drafts ARE the deliverables; no findings.md gate."""
    return 0


SPEC = WorkflowSpec(
    name="article_engine",
    config=WorkflowConfig(
        subdirs=["drafts"],
        default_timeout=3600,           # longer than x_engine; articles are bigger
        multiturn_timeout=10800,
        stall_limit=5,
        default_client="jr",
        default_context="",
        multiturn_max_turns=4000,
    ),
    config_dir_name="article_engine",
    configure_env=configure_env,
    pre_summary_hooks=pre_summary_hooks,
    snapshot_evaluations=snapshot_evaluations,
    completion_guard=completion_guard,
    list_deliverables=list_deliverables,
    augment_quality_metrics=augment_quality_metrics,
    count_findings=count_findings,
    findings_promotion=FindingsPromotionConfig(
        title="Global Findings: Article Engine",
        confirmed_threshold=2,
        repeated_threshold=2,
    ),
    render_report=lambda sd, c, rs: rs(
        "render_report.py", str(sd), "article_engine", c,
    ),
)
