from __future__ import annotations

import os
import re
from pathlib import Path

from .eval_cache import evaluate_artifact_glob
from .specs import FindingsPromotionConfig, RunScript, RunSessionEvaluator, WorkflowConfig, WorkflowSpec


# Content Engine v1 U8 — storyboard extension contract.
#
# Five supported platform targets (cf. plan R1). When unset, defaults to
# youtube_long so existing fixtures (which never set this env) keep
# producing the same artifact shape they did pre-U8.
ALLOWED_PLATFORM_TARGETS: frozenset[str] = frozenset({
    "ig_reels", "tiktok", "ig_story", "ig_carousel", "youtube_long",
})

# Three format modes (R2). Narrative is the pre-U8 behavior; educational
# + brand_authority unlock new content shapes (info-density + voice-
# corpus anchoring respectively).
ALLOWED_FORMAT_MODES: frozenset[str] = frozenset({
    "narrative", "educational", "brand_authority",
})

# Per format mode, the content types the lane needs unrestricted access
# to in order to produce ANY artifact. If the per-client content_denylist
# blocks every required type for the chosen mode, configure_env fails
# loud per D17 — the alternative is silent zero-output runs which
# violate CLAUDE.md Rule 12 (Fail Loud).
_MODE_REQUIRED_CONTENT_TYPES: dict[str, frozenset[str]] = {
    # Narrative storytelling needs at least ONE of: depicted-scenes,
    # voiceover_with_b_roll, or animated_visualizations.
    "narrative": frozenset({"depicted_scenes", "voiceover_with_b_roll", "animated_visualizations"}),
    # Educational mode requires at least one informational-content type.
    "educational": frozenset({"informational_visuals", "diagrams", "screen_captures", "data_visualization"}),
    # Brand_authority requires voice-corpus or brand_imagery surfaces.
    "brand_authority": frozenset({"voice_corpus_quotes", "brand_imagery", "case_study_visuals"}),
}


def configure_env(client: str) -> None:
    """Set env defaults for a storyboard subprocess.

    Per U8: extended with platform_target + format_mode + voice persona
    + content_denylist env vars. The caller (autoresearch CLI / harness)
    is responsible for translating ClientConfig → env vars BEFORE
    invoking the subprocess; this function validates the result.

    Raises ValueError per D17 when format_mode requires content types
    that the client's content_denylist blocks entirely (e.g., Klinika's
    `clinical_visuals + before_after_imagery` denylist would not by
    itself violate D17 because narrative still has access to b-roll /
    animated visualizations).
    """
    os.environ.setdefault("CREATOR_HANDLE", client)
    os.environ.setdefault("STORYBOARD_COUNT", "5")

    # platform_target — D17 default to youtube_long.
    platform = os.environ.setdefault("STORYBOARD_PLATFORM_TARGET", "youtube_long")
    if platform not in ALLOWED_PLATFORM_TARGETS:
        raise ValueError(
            f"STORYBOARD_PLATFORM_TARGET={platform!r} not in supported set "
            f"{sorted(ALLOWED_PLATFORM_TARGETS)}. Set to one of these or unset "
            f"for the default (youtube_long)."
        )

    # format_mode — default narrative (existing pre-U8 behavior).
    format_mode = os.environ.setdefault("STORYBOARD_FORMAT_MODE", "narrative")
    if format_mode not in ALLOWED_FORMAT_MODES:
        raise ValueError(
            f"STORYBOARD_FORMAT_MODE={format_mode!r} not in supported set "
            f"{sorted(ALLOWED_FORMAT_MODES)}."
        )

    # voice_persona_ref — optional. Brand-authority mode is the only one
    # that hard-requires it; the others soft-degrade.
    voice_persona = os.environ.get("STORYBOARD_VOICE_PERSONA_REF", "").strip()
    if format_mode == "brand_authority" and not voice_persona:
        raise ValueError(
            "STORYBOARD_FORMAT_MODE=brand_authority requires "
            "STORYBOARD_VOICE_PERSONA_REF to be set (the brand-authority "
            "shape anchors on voice corpus quotes + persona style anchors)."
        )

    # content_denylist — D17 enforcement.
    denylist_raw = os.environ.get("STORYBOARD_CONTENT_DENYLIST", "").strip()
    denylist = {x.strip() for x in denylist_raw.split(",") if x.strip()}
    required = _MODE_REQUIRED_CONTENT_TYPES.get(format_mode, frozenset())
    if required and required.issubset(denylist):
        # Every required content type is denied → lane cannot produce.
        raise ValueError(
            f"STORYBOARD_FORMAT_MODE={format_mode!r} requires at least one "
            f"of {sorted(required)} but STORYBOARD_CONTENT_DENYLIST denies "
            f"all of them. The lane cannot produce any artifact under "
            f"these constraints (D17 fail-loud). Either change the format "
            f"mode or relax the client's content_denylist."
        )


def pre_summary_hooks(_session_dir: Path, _client: str, _run_script: RunScript) -> None:
    return


def snapshot_evaluations(session_dir: Path, run_session_evaluator: RunSessionEvaluator) -> dict[str, object]:
    story_decisions = evaluate_artifact_glob(
        "storyboard", session_dir, "stories/*.json", "story", "full",
        run_session_evaluator,
    )
    return {"story_decisions": story_decisions}


def completion_guard(eval_summary: dict[str, object]) -> tuple[str | None, str | None]:
    decisions = [item for item in eval_summary.get("story_decisions", []) if isinstance(item, dict)]
    if decisions and any(item.get("decision") != "KEEP" for item in decisions):
        note = "At least one storyboard plan failed final session evaluation; rerun PLAN_STORY/IDEATE before marking COMPLETE."
        return note, "stories/*.json"
    return None, None


def list_deliverables(session_dir: Path) -> list[str]:
    deliverables: list[str] = []
    if (session_dir / "report.md").exists():
        deliverables.append("report.md")
    storyboards_dir = session_dir / "storyboards"
    if storyboards_dir.exists():
        deliverables.extend(f"storyboards/{path.name}" for path in storyboards_dir.iterdir() if path.is_file())
    return deliverables


def augment_quality_metrics(results: list[dict], quality_metrics: dict) -> None:
    scene_scores = [result.get("scene_score") for result in results if result.get("scene_score") is not None]
    if scene_scores:
        quality_metrics["avg_scene_score"] = round(sum(scene_scores) / len(scene_scores), 3)


# Content Engine v1 U8 — per-format-mode rubric reweighting (R2).
#
# Narrative mode keeps the pre-U8 uniform weights so existing fixtures
# score identically (regression-free). Educational + brand_authority
# tilt the geometric-mean weighting toward the axes that matter most
# for those output shapes:
#   educational     — SB-3 (earned transitions) + SB-4 (recontextualizing
#                     turn) RELAXED; SB-6 (AI-producibility) +
#                     info-density emphasis UPWEIGHTED.
#   brand_authority — SB-1 (creator authenticity) + SB-5 (performable
#                     voice script) UPWEIGHTED; SB-7 (platform pacing)
#                     softened (brand_authority is less platform-bound).
_FORMAT_MODE_WEIGHTS: dict[str, dict[str, float]] = {
    "narrative": {},  # empty = uniform; pre-U8 behavior preserved.
    "educational": {
        "SB-3": 0.7,  # relaxed; explainers tolerate less earned transition
        "SB-4": 0.7,  # relaxed; explainers don't always re-contextualize
        "SB-6": 1.3,  # upweighted; info-density visuals must be producible
    },
    "brand_authority": {
        "SB-1": 1.4,  # upweighted; voice fidelity is the whole point
        "SB-5": 1.3,  # upweighted; performable voice script load-bearing
        "SB-7": 0.8,  # softened; brand_authority is less platform-bound
    },
}


def custom_score(config, variant_dir_str: str, parent_id: str | None) -> None:
    """Lane-specific scoring hook (cf. LaneSpec.custom_score).

    Per U8: format-mode-aware reweighting of the SB-1..SB-8 axes. Runs
    the default substrate scorer first to populate per-axis scores +
    aggregate composite, then post-processes the variant's score
    payload to apply the mode's tier weights. Narrative mode is a
    no-op (existing fixtures unaffected).
    """
    # Default scoring runs first; we mutate the resulting payload.
    # Imported lazily so the SPEC module load doesn't require the
    # substrate scoring module (matches marketing_audit precedent).
    from . import _score_variant_search  # type: ignore[attr-defined]
    _score_variant_search(config, variant_dir_str, parent_id)

    format_mode = os.environ.get("STORYBOARD_FORMAT_MODE", "narrative").strip().lower()
    weights = _FORMAT_MODE_WEIGHTS.get(format_mode)
    if not weights:
        return  # narrative or unknown mode → leave default scoring as-is.

    # Reweight the per-axis scores in the lane's score payload.
    # Substrate writes lineage.jsonl with per-axis scores; we walk the
    # variant's score sidecar and apply the weights, recomputing
    # the geometric mean. The exact file path + shape is substrate-
    # specific; here we use the documented evolution-substrate
    # convention (`<variant_dir>/lane_score.json`).
    import json
    variant_dir = Path(variant_dir_str)
    score_path = variant_dir / "lane_score.json"
    if not score_path.is_file():
        # Default scorer didn't write the file (e.g., variant failed L1).
        # Leave the lineage entry untouched; nothing to reweight.
        return
    try:
        payload = json.loads(score_path.read_text())
    except json.JSONDecodeError:
        return
    per_axis = payload.get("per_axis") or {}
    if not isinstance(per_axis, dict) or not per_axis:
        return

    # Apply weights → recompute weighted geometric mean.
    weighted_scores: list[tuple[float, float]] = []
    for axis_id, raw_score in per_axis.items():
        weight = float(weights.get(axis_id, 1.0))
        try:
            score = float(raw_score)
        except (TypeError, ValueError):
            continue
        if score <= 0 or weight <= 0:
            continue
        weighted_scores.append((score, weight))

    if weighted_scores:
        import math
        # Weighted geometric mean = exp( Σ(w_i * ln(s_i)) / Σ(w_i) ).
        log_sum = sum(w * math.log(s) for s, w in weighted_scores)
        weight_sum = sum(w for _, w in weighted_scores)
        new_composite = math.exp(log_sum / weight_sum) if weight_sum else 0.0
        payload["composite_reweighted"] = round(new_composite, 4)
        payload["reweighting_mode"] = format_mode
        score_path.write_text(json.dumps(payload, indent=2))


def count_findings(text: str) -> int:
    """Count storyboard findings. Legacy `### [` headers plus bullet-list
    summaries produced by newer iterations."""
    headers = len(re.findall(r"^### \[", text, re.MULTILINE))
    bullets = len(re.findall(r"^- ", text, re.MULTILINE))
    return max(headers, bullets)


SPEC = WorkflowSpec(
    name="storyboard",
    config=WorkflowConfig(
        subdirs=["patterns", "stories", "storyboards", "frames", "clips"],
        default_timeout=1800,
        multiturn_timeout=7200,
        # 2026-05-08 evening: raised 5→10 after live evidence that the lane's
        # analyze_patterns + plan_story phases legitimately consume 5+ minutes
        # of agent work between phase events (verified via TechReview run that
        # produced 11 patterns + 5 KEEP stories under stall_count). The prior
        # P1 audit conflated `max_iter` (hard ceiling) with `stall_limit` (idle
        # threshold) — they aren't comparable. The agent IS doing productive
        # work writing to patterns/, stories/, storyboards/, frames/ subdirs;
        # state_changed just doesn't see those writes between phase events.
        # Doubling the threshold buys the agent room to complete a long phase
        # without raising the false-positive risk the audit was guarding (the
        # cyber-flag stub-file concern was about a different lane's behavior).
        stall_limit=10,
        default_client="Gossip.Goblin",
        default_context="youtube",
        multiturn_max_turns=3000,
    ),
    config_dir_name="storyboard",
    configure_env=configure_env,
    pre_summary_hooks=pre_summary_hooks,
    snapshot_evaluations=snapshot_evaluations,
    completion_guard=completion_guard,
    list_deliverables=list_deliverables,
    augment_quality_metrics=augment_quality_metrics,
    count_findings=count_findings,
    findings_promotion=FindingsPromotionConfig(
        title="Global Findings: Storyboard",
        confirmed_threshold=2,
        repeated_threshold=2,
    ),
    render_report=lambda sd, c, rs: rs("render_report.py", str(sd), "storyboard", c),  # B-storyboard
)
