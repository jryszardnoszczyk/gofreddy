"""ad_engine WorkflowSpec — per Content Engine Lanes v1 U15 + master plan §4.7 + TD-42.

Ad_engine produces 3-5 variants per format for Meta + LinkedIn ad
creative (meta_reels, meta_image, linkedin_sponsored, linkedin_doc_ad).
Each variant artifact carries paired ad_creative + lp_hero copy
(TD-42 single-pass) so the AD-8 conversion-readiness rubric can score
message-match between the ad and the landing-page hero.

Per JR's 2026-05-19 U15 decisions:
- 5-provider signal aggregator ships as DI fetchers (same pattern as
  vision_judge + citation_verifier).
- Ad + LP copy live in ONE variant artifact per TD-42.
- Banned-terms YAML is operator-curated, independent of
  medical_pl/legal_pl placeholder rule sets.

Inner-loop STATICALLY PINNED to claude/sonnet (NOT codex) — see
LaneSpec for rationale.

`configure_env` reads:
- `AD_ENGINE_CAMPAIGN_GOAL`        — required
- `AD_ENGINE_OFFER`                — required
- `AD_ENGINE_TARGET_AUDIENCE`      — required
- `AD_ENGINE_VOICE_PERSONA_REF`    — required
- `AD_ENGINE_PLATFORM_TARGET`      — required (csv: meta | linkedin)
- `AD_ENGINE_AD_FORMAT_PER_PLATFORM` — required (JSON map)
- `AD_ENGINE_LOCALE_GL` / `AD_ENGINE_LOCALE_HL` — optional (default us/en)
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


ALLOWED_PLATFORMS: frozenset[str] = frozenset({"meta", "linkedin"})
ALLOWED_AD_FORMATS: frozenset[str] = frozenset({
    "meta_reels", "meta_image", "linkedin_sponsored", "linkedin_doc_ad",
})


def configure_env(_client: str) -> None:
    """Validate U15 env vars + compile voice substrate."""
    from src.voice.persona import (
        compile_substrate,
        load_corpus_files,
        load_persona,
    )

    persona_ref = os.environ.get("AD_ENGINE_VOICE_PERSONA_REF", "").strip()
    if not persona_ref:
        raise RuntimeError(
            "AD_ENGINE_VOICE_PERSONA_REF is required (U15). Voice persona "
            "governs AD-6 voice fidelity. Set via fixture env or operator "
            "wiring to a persona slug from voice_personas/<slug>.yaml."
        )
    persona = load_persona(persona_ref)
    corpus = load_corpus_files(persona)
    if not corpus:
        raise RuntimeError(
            f"persona {persona_ref!r} resolves to an empty corpus at "
            f"{persona.corpus_path}. ad_engine cannot generate "
            f"voice-consistent ad copy without content."
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

    # Required env vars
    for key in (
        "AD_ENGINE_CAMPAIGN_GOAL",
        "AD_ENGINE_OFFER",
        "AD_ENGINE_TARGET_AUDIENCE",
        "AD_ENGINE_PLATFORM_TARGET",
        "AD_ENGINE_AD_FORMAT_PER_PLATFORM",
    ):
        if not os.environ.get(key, "").strip():
            raise RuntimeError(
                f"{key} is required (U15 ad_engine config). See "
                f"programs/ad_engine-session.md for the expected shape."
            )

    # Platform validation
    platforms_raw = os.environ["AD_ENGINE_PLATFORM_TARGET"]
    platforms = {p.strip() for p in platforms_raw.split(",") if p.strip()}
    invalid_platforms = platforms - ALLOWED_PLATFORMS
    if "google" in invalid_platforms:
        raise RuntimeError(
            "AD_ENGINE_PLATFORM_TARGET=google is architecture-supported but "
            "build deferred to v1.5. v1 supports {meta, linkedin}."
        )
    if invalid_platforms:
        raise RuntimeError(
            f"AD_ENGINE_PLATFORM_TARGET contains unsupported platforms: "
            f"{sorted(invalid_platforms)}. Allowed: {sorted(ALLOWED_PLATFORMS)}."
        )

    # Pass-through env
    angle_id = os.environ.get("AUTORESEARCH_CONTEXT", "").strip()
    if angle_id:
        os.environ["AD_ENGINE_CAMPAIGN_ID"] = angle_id
    session_dir = os.environ.get("AUTORESEARCH_SESSION_DIR", "").strip()
    if session_dir:
        os.environ["AD_ENGINE_SESSION_DIR"] = session_dir


def pre_summary_hooks(session_dir: Path, client: str, run_script: RunScript) -> None:
    """No-op — variants ARE the deliverables."""
    return


def snapshot_evaluations(
    session_dir: Path, run_session_evaluator: RunSessionEvaluator
) -> dict[str, object]:
    """Per-variant KEEP/REVISE decisions."""
    drafts_dir = session_dir / "drafts"
    if not drafts_dir.exists():
        return {"draft_decisions": []}

    decisions: list[dict[str, object]] = []
    for artifact in sorted(drafts_dir.glob("*.json")):
        # Skip aggregator/brief annex files.
        if artifact.name.startswith("_"):
            continue
        eval_path = artifact.with_suffix(".eval.json")
        cached = read_cached_eval_if_fresh(artifact, eval_path)
        if cached is not None:
            decisions.append({
                "artifact": str(artifact.relative_to(session_dir)),
                "decision": cached.get("decision"),
            })
            continue
        data = run_session_evaluator(
            "ad_engine", artifact, session_dir, eval_path, "full"
        )
        decisions.append({
            "artifact": str(artifact.relative_to(session_dir)),
            "decision": (data or {}).get("decision"),
        })
    return {"draft_decisions": decisions}


def completion_guard(
    eval_summary: dict[str, object],
) -> tuple[str | None, str | None]:
    """KEEP if any variant decision is KEEP; otherwise downgrade."""
    decisions = eval_summary.get("draft_decisions") or []
    if any((d or {}).get("decision") == "KEEP" for d in decisions):
        return None, None
    return (
        "RUNNING",
        "no ship-eligible ad variants produced; downgrading session for retry.",
    )


def list_deliverables(session_dir: Path) -> list[str]:
    """All non-annex JSON variant artifacts."""
    drafts_dir = session_dir / "drafts"
    if not drafts_dir.exists():
        return []
    return sorted(
        f"drafts/{p.name}"
        for p in drafts_dir.iterdir()
        if p.is_file() and p.suffix == ".json" and not p.name.startswith("_")
    )


def augment_quality_metrics(results: list[dict], quality_metrics: dict) -> None:
    return


def count_findings(text: str) -> int:
    return 0


SPEC = WorkflowSpec(
    name="ad_engine",
    config=WorkflowConfig(
        subdirs=["drafts"],
        default_timeout=3600,
        multiturn_timeout=10800,
        stall_limit=5,
        default_client="jr",
        default_context="",
        multiturn_max_turns=4000,
    ),
    config_dir_name="ad_engine",
    configure_env=configure_env,
    pre_summary_hooks=pre_summary_hooks,
    snapshot_evaluations=snapshot_evaluations,
    completion_guard=completion_guard,
    list_deliverables=list_deliverables,
    augment_quality_metrics=augment_quality_metrics,
    count_findings=count_findings,
    findings_promotion=FindingsPromotionConfig(
        title="Global Findings: Ad Engine",
        confirmed_threshold=2,
        repeated_threshold=2,
    ),
    render_report=lambda sd, c, rs: rs(
        "render_report.py", str(sd), "ad_engine", c,
    ),
)
