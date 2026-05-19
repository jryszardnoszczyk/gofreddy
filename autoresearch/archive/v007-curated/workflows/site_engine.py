"""site_engine WorkflowSpec — per Content Engine Lanes v1 U15b + master plan §4.8 + TD-30.

Site_engine mutates section-level site artifacts (hero, value_prop,
social_proof, faq, cta, pricing) for a target client site. Per
TD-28 v1 scope: SECTION-LEVEL ONLY; full-page rewrites are out of v1
(would require cross-section composition mutation surface).

Per JR's 2026-05-19 U14 update: visual rubrics route through
Gemini 3 Flash Preview (D24 originally specified 2.5).

`configure_env` reads:
- `SITE_ENGINE_TARGET_URL`        — required
- `SITE_ENGINE_SECTION`           — required (one of allowed sections)
- `SITE_ENGINE_VOICE_PERSONA_REF` — required (for SE-4)
- `SITE_ENGINE_BRAND_TOKENS_PATH` — required (palette + typography hex)
- `SITE_ENGINE_BRIEFS_PATH`       — optional (marketing_audit + geo briefs)
- `SITE_ENGINE_AUDIENCE`          — optional
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


ALLOWED_SECTIONS: frozenset[str] = frozenset({
    "hero", "value_prop", "social_proof", "faq", "cta", "pricing",
})


def configure_env(_client: str) -> None:
    """Validate U15b env vars + compile voice substrate."""
    from src.voice.persona import (
        compile_substrate,
        load_corpus_files,
        load_persona,
    )

    persona_ref = os.environ.get("SITE_ENGINE_VOICE_PERSONA_REF", "").strip()
    if not persona_ref:
        raise RuntimeError(
            "SITE_ENGINE_VOICE_PERSONA_REF is required (U15b). Voice "
            "persona governs SE-4. Set via fixture env or operator wiring."
        )
    persona = load_persona(persona_ref)
    corpus = load_corpus_files(persona)
    if not corpus:
        raise RuntimeError(
            f"persona {persona_ref!r} resolves to an empty corpus at "
            f"{persona.corpus_path}. site_engine cannot generate "
            f"voice-consistent copy without content."
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

    target_url = os.environ.get("SITE_ENGINE_TARGET_URL", "").strip()
    if not target_url:
        raise RuntimeError(
            "SITE_ENGINE_TARGET_URL is required. Set to the client's "
            "live site URL (used as render baseline + brand-token source)."
        )

    section = os.environ.get("SITE_ENGINE_SECTION", "").strip()
    if not section:
        raise RuntimeError(
            f"SITE_ENGINE_SECTION is required. Allowed: {sorted(ALLOWED_SECTIONS)}."
        )
    if section not in ALLOWED_SECTIONS:
        raise RuntimeError(
            f"SITE_ENGINE_SECTION={section!r} not in supported set "
            f"{sorted(ALLOWED_SECTIONS)}. Per TD-28 v1 scope: section-"
            f"level only; full-page rewrites are out of v1."
        )

    brand_tokens_path = os.environ.get("SITE_ENGINE_BRAND_TOKENS_PATH", "").strip()
    if not brand_tokens_path:
        raise RuntimeError(
            "SITE_ENGINE_BRAND_TOKENS_PATH is required. Brand tokens "
            "(palette + typography hex) are mutation-READ-ONLY per "
            "TD-43 Tier-C; the lane consumes them but never edits values."
        )
    # Validate tokens.json contents at lane startup per plan §U18 +
    # Threat Model brand_tokens-swap mitigation: external URLs in
    # typeface families, JS protocol handlers, and out-of-range
    # spacing/motion values raise here BEFORE the variant agent burns
    # tokens. Lazy import so this module stays importable without
    # site_engine package (mirrors voice persona lazy-import).
    from src.site_engine.brand_tokens import load_brand_tokens
    load_brand_tokens(brand_tokens_path)

    angle_id = os.environ.get("AUTORESEARCH_CONTEXT", "").strip()
    if angle_id:
        os.environ["SITE_ENGINE_CONTEXT_ID"] = angle_id
    session_dir = os.environ.get("AUTORESEARCH_SESSION_DIR", "").strip()
    if session_dir:
        os.environ["SITE_ENGINE_SESSION_DIR"] = session_dir


def pre_summary_hooks(session_dir: Path, client: str, run_script: RunScript) -> None:
    return


def snapshot_evaluations(
    session_dir: Path, run_session_evaluator: RunSessionEvaluator
) -> dict[str, object]:
    """Per-variant KEEP/REVISE decisions."""
    drafts_dir = session_dir / "drafts"
    if not drafts_dir.exists():
        return {"draft_decisions": []}

    decisions: list[dict[str, object]] = []
    for artifact in sorted(drafts_dir.glob("*.html")):
        eval_path = artifact.with_suffix(".eval.json")
        cached = read_cached_eval_if_fresh(artifact, eval_path)
        if cached is not None:
            decisions.append({
                "artifact": str(artifact.relative_to(session_dir)),
                "decision": cached.get("decision"),
            })
            continue
        data = run_session_evaluator(
            "site_engine", artifact, session_dir, eval_path, "full"
        )
        decisions.append({
            "artifact": str(artifact.relative_to(session_dir)),
            "decision": (data or {}).get("decision"),
        })
    return {"draft_decisions": decisions}


def completion_guard(
    eval_summary: dict[str, object],
) -> tuple[str | None, str | None]:
    decisions = eval_summary.get("draft_decisions") or []
    if any((d or {}).get("decision") == "KEEP" for d in decisions):
        return None, None
    return (
        "RUNNING",
        "no ship-eligible section variants produced; downgrading for retry.",
    )


def list_deliverables(session_dir: Path) -> list[str]:
    drafts_dir = session_dir / "drafts"
    if not drafts_dir.exists():
        return []
    return sorted(
        f"drafts/{p.name}" for p in drafts_dir.iterdir()
        if p.is_file() and p.suffix == ".html"
    )


def augment_quality_metrics(results: list[dict], quality_metrics: dict) -> None:
    return


def count_findings(text: str) -> int:
    return 0


SPEC = WorkflowSpec(
    name="site_engine",
    config=WorkflowConfig(
        subdirs=["drafts"],
        default_timeout=3600,
        multiturn_timeout=10800,
        stall_limit=5,
        default_client="jr",
        default_context="",
        multiturn_max_turns=4000,
    ),
    config_dir_name="site_engine",
    configure_env=configure_env,
    pre_summary_hooks=pre_summary_hooks,
    snapshot_evaluations=snapshot_evaluations,
    completion_guard=completion_guard,
    list_deliverables=list_deliverables,
    augment_quality_metrics=augment_quality_metrics,
    count_findings=count_findings,
    findings_promotion=FindingsPromotionConfig(
        title="Global Findings: Site Engine",
        confirmed_threshold=2,
        repeated_threshold=2,
    ),
    render_report=lambda sd, c, rs: rs(
        "render_report.py", str(sd), "site_engine", c,
    ),
)
