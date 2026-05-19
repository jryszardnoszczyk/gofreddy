"""ad_engine SessionEvalSpec — per Content Engine Lanes v1 U15 + TD-42.

Mirrors session_eval_article_engine/image_engine shape with ad-specific
structural enforcement: variant artifact JSON shape, per-format variant
counts, diversity gate (Jaccard ≤0.3), banned-terms hard-gate, message-
match gate (Jaccard ≥0.4), per-platform character limits,
anti-pattern hits.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from .session_eval_common import CrossItemCriterion, SessionEvalSpec


CRITERIA: dict[str, str] = {
    "AD-1": (
        "Hook strength — first 8 words / first frame contains a concrete "
        "number, named competitor/category, contrarian claim, or workflow "
        "noun. Anti-pattern hits cap at 4."
    ),
    "AD-2": (
        "CTA clarity — viewer knows what happens on click in ≤4 words. "
        "Generic CTAs ('Learn More') cap at 3."
    ),
    "AD-3": (
        "Offer specificity — includes ≥1 of {price, duration, quantity, "
        "named deliverable}. Competitor-stealable = specific."
    ),
    "AD-4": (
        "Platform-format compliance — Meta/LinkedIn auto-approve. Hard "
        "caps: Meta 125/27/30 chars; LinkedIn 150 intro / 1-2 line headline; "
        "Reels 9-15s. Banned-term + character-limit checks structural."
    ),
    "AD-5": (
        "Variant diversity — pairwise Jaccard on hook+opening-8-token ≤0.3; "
        "archetype enum values all distinct; no shared proof noun."
    ),
    "AD-6": (
        "Voice fidelity — matches client's other channels; anti-pattern "
        "hits cap at 3 (voice slipped into AI house-style)."
    ),
    "AD-7": (
        "Market-signal alignment — cites brief.recurring_hook_archetypes as "
        "counter or amplify. NO-OP when all Meta-side sources degraded."
    ),
    "AD-8": (
        "Conversion-readiness — jaccard(ad.hook, lp.headline) ≥0.4; CTA "
        "verb exact match; proof noun overlap."
    ),
}


# Per-format variant counts + character limits per TD-42.
_VARIANT_COUNT_BY_FORMAT: dict[str, int] = {
    "meta_reels": 4,
    "meta_image": 4,
    "linkedin_sponsored": 4,
    "linkedin_doc_ad": 3,
}

_CHARACTER_LIMITS: dict[str, dict[str, int]] = {
    "meta_reels": {"body": 125, "headline": 27, "description": 30},
    "meta_image": {"body": 125, "headline": 27, "description": 30},
    "linkedin_sponsored": {"intro": 150, "body": 150},
    "linkedin_doc_ad": {"slide_word_limit": 30},
}


_STOPWORDS: frozenset[str] = frozenset({
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for",
    "from", "have", "i", "in", "into", "is", "it", "its", "of", "on",
    "or", "that", "the", "to", "was", "were", "will", "with", "your", "you",
})


def _tokenize(text: str) -> set[str]:
    """Lowercase + strip stopwords + return token set for Jaccard."""
    tokens = re.findall(r"[a-z0-9']+", text.lower())
    return {t for t in tokens if t not in _STOPWORDS}


def _jaccard(a: str, b: str) -> float:
    """Jaccard on stopword-stripped token sets."""
    set_a = _tokenize(a)
    set_b = _tokenize(b)
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def _load_variant(artifact: Path) -> dict | None:
    """Read variant JSON; returns None on parse failure."""
    try:
        return json.loads(artifact.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def structural_gate(_mode: str, artifact: Path, session_dir: Path) -> list[str]:
    """Per-variant structural gate. Variant artifacts are JSON files
    with ad_creative + lp_hero sections."""
    failures: list[str] = []
    if not artifact.exists():
        failures.append(f"Artifact not found: {artifact}")
        return failures

    variant = _load_variant(artifact)
    if variant is None:
        failures.append(f"Variant artifact {artifact} is not valid JSON.")
        return failures

    # Required top-level keys
    for key in ("variant_id", "format", "ad_creative", "lp_hero"):
        if key not in variant:
            failures.append(f"Variant missing required key: {key!r}")
            return failures

    fmt = variant["format"]
    if fmt not in _VARIANT_COUNT_BY_FORMAT:
        failures.append(
            f"format={fmt!r} unsupported; must be one of "
            f"{sorted(_VARIANT_COUNT_BY_FORMAT)}."
        )
        return failures

    ad_creative = variant.get("ad_creative", {})
    lp_hero = variant.get("lp_hero", {})

    # Required ad_creative + lp_hero subkeys
    for ac_key in ("hook", "body", "cta"):
        if ac_key not in ad_creative:
            failures.append(f"ad_creative missing key: {ac_key!r}")
    for lp_key in ("headline", "primary_cta", "proof_point"):
        if lp_key not in lp_hero:
            failures.append(f"lp_hero missing key: {lp_key!r}")
    if failures:
        return failures

    # Message-match gate (AD-8 hard structural)
    ad_hook = str(ad_creative.get("hook", ""))
    lp_headline = str(lp_hero.get("headline", ""))
    match_score = _jaccard(ad_hook, lp_headline)
    if match_score < 0.4:
        failures.append(
            f"AD-8 message-match gate failed: jaccard(ad.hook, lp.headline) "
            f"= {match_score:.2f} < 0.4. Align ad hook with LP headline."
        )

    # CTA verb match
    ad_cta = ad_creative.get("cta", {})
    lp_cta = lp_hero.get("primary_cta", {})
    ad_verb = (
        ad_cta.get("verb") if isinstance(ad_cta, dict)
        else str(ad_cta).split()[0] if ad_cta else ""
    )
    lp_verb = (
        lp_cta.get("verb") if isinstance(lp_cta, dict)
        else str(lp_cta).split()[0] if lp_cta else ""
    )
    if ad_verb and lp_verb and ad_verb.lower() != lp_verb.lower():
        failures.append(
            f"AD-8 CTA verb mismatch: ad.cta.verb={ad_verb!r} but "
            f"lp.primary_cta.verb={lp_verb!r}. Must match exactly."
        )

    # Banned-terms hard-gate (Meta health-vertical + LinkedIn aggressive +
    # guaranteed-N% regex). The gate fires regardless of vertical for
    # universal patterns; health-specific words fire only when client is
    # health/wellness/aesthetic_medicine vertical (operator-set, not yet
    # plumbed in v1 — fires conservatively here).
    failures.extend(_banned_term_check(ad_creative, lp_hero, fmt))

    # Character-limit check per format
    failures.extend(_character_limit_check(ad_creative, fmt))

    # Anti-patterns deterministic pre-check
    failures.extend(_anti_pattern_check(ad_creative))

    return failures


def _banned_term_check(
    ad_creative: dict, lp_hero: dict, fmt: str,
) -> list[str]:
    """Run banned-term checks against ad copy + LP copy."""
    try:
        from src.ads.compliance import (
            text_violates_guaranteed_results,
            text_violates_linkedin_aggressive,
            text_violates_meta_health,
        )
    except ImportError:
        return []

    all_text = " ".join([
        str(ad_creative.get("hook", "")),
        str(ad_creative.get("body", "")),
        str(lp_hero.get("headline", "")),
    ])

    failures: list[str] = []

    # Health-vertical banned words fire for Meta formats (operator-set
    # vertical assumed = health/wellness; refine when ClientConfig
    # threads vertical through env in U18).
    if fmt.startswith("meta_"):
        meta_hits = text_violates_meta_health(all_text)
        if meta_hits:
            failures.append(
                f"Banned Meta health-vertical words present: {meta_hits}. "
                f"Meta auto-rejects these in health/wellness ads."
            )

    # LinkedIn aggressive-promotional fires for LinkedIn formats
    if fmt.startswith("linkedin_"):
        li_hits = text_violates_linkedin_aggressive(all_text)
        if li_hits:
            failures.append(
                f"Banned LinkedIn aggressive phrases present: {li_hits}. "
                f"LinkedIn moderation flags these."
            )

    # Universal "guaranteed N% results" regex
    if text_violates_guaranteed_results(all_text):
        failures.append(
            "Banned phrase: 'Guaranteed N% results' regex matched. "
            "Meta post-2025 enforcement auto-flags."
        )

    return failures


def _character_limit_check(ad_creative: dict, fmt: str) -> list[str]:
    """Per-format character-limit check per TD-42 hard caps."""
    limits = _CHARACTER_LIMITS.get(fmt, {})
    failures: list[str] = []
    for field_name, cap in limits.items():
        if field_name == "slide_word_limit":
            continue  # LinkedIn doc ad: per-slide word counts checked elsewhere
        value = str(ad_creative.get(field_name, ""))
        if len(value) > cap:
            failures.append(
                f"{fmt} {field_name} length={len(value)} > {cap} char cap. "
                f"Meta/LinkedIn auto-reject overruns."
            )
    return failures


def _anti_pattern_check(ad_creative: dict) -> list[str]:
    """14-pattern deterministic anti-pattern check."""
    try:
        from src.ads.compliance import find_anti_pattern_hits
    except ImportError:
        return []

    all_text = " ".join([
        str(ad_creative.get("hook", "")),
        str(ad_creative.get("body", "")),
        str(ad_creative.get("cta", "")),
    ])
    hits = find_anti_pattern_hits(all_text)
    if hits:
        ids = [h.pattern_id for h in hits]
        return [
            f"Anti-pattern hits ({len(hits)}): {ids[:3]}"
            f"{'...' if len(ids) > 3 else ''}. Cap AD-1 + AD-6 scores."
        ]
    return []


def load_source_data(_mode: str, artifact: Path, session_dir: Path) -> str:
    """Concatenate campaign goal + offer + audience + voice substrate +
    signal_bundle (if present) for the judge."""
    parts: list[str] = []

    for key in (
        "AD_ENGINE_CAMPAIGN_GOAL", "AD_ENGINE_OFFER", "AD_ENGINE_TARGET_AUDIENCE",
    ):
        val = os.environ.get(key, "").strip()
        if val:
            parts.append(f"## {key}\n{val}")

    # Voice substrate
    try:
        from harness.session_paths import find_variant_root  # type: ignore  # noqa: PLC0415
        variant_root = find_variant_root(session_dir)
    except (ValueError, ImportError):
        variant_root = (
            session_dir.parents[2] if len(session_dir.parents) > 2 else None
        )
    if variant_root is not None:
        voice = variant_root / "programs" / "references" / "voice.md"
        if voice.is_file():
            try:
                parts.append(
                    f"## Voice substrate\n"
                    f"{voice.read_text(encoding='utf-8', errors='replace')[:4000]}"
                )
            except OSError:
                pass

    # Signal bundle (if aggregator ran)
    signal_bundle = session_dir / "drafts" / "_signal_bundle.json"
    if signal_bundle.is_file():
        try:
            parts.append(
                f"## Competitive signal bundle\n```json\n"
                f"{signal_bundle.read_text(encoding='utf-8')[:3000]}\n```"
            )
        except OSError:
            pass

    return "\n\n".join(parts)


# Structural gate functions for LaneSpec.structural_gate_functions

def variant_artifact_well_formed(artifact: Path, session_dir: Path) -> list[str]:
    return [f for f in structural_gate("full", artifact, session_dir)
            if "missing required key" in f or "not valid JSON" in f or "missing key" in f]


def variant_count_per_format(artifact: Path, session_dir: Path) -> list[str]:
    """Per-format variant count check operates at the SESSION level
    (count all drafts/<format>_*.json), not per-artifact. Returns
    empty here; the session-level aggregator runs separately."""
    return []


def diversity_gate_passes(artifact: Path, session_dir: Path) -> list[str]:
    """Diversity gate is cross-variant (pairwise Jaccard); runs at
    session level via session_eval_common.cross_item_criteria, not
    per-artifact. Returns empty stub here."""
    return []


def banned_terms_absent(artifact: Path, session_dir: Path) -> list[str]:
    return [f for f in structural_gate("full", artifact, session_dir)
            if "Banned" in f]


def message_match_gate_passes(artifact: Path, session_dir: Path) -> list[str]:
    return [f for f in structural_gate("full", artifact, session_dir)
            if "AD-8" in f]


def anti_patterns_within_threshold(artifact: Path, session_dir: Path) -> list[str]:
    return [f for f in structural_gate("full", artifact, session_dir)
            if "Anti-pattern" in f]


def character_limits_respected(artifact: Path, session_dir: Path) -> list[str]:
    return [f for f in structural_gate("full", artifact, session_dir)
            if "char cap" in f]


def platform_target_valid(artifact: Path, session_dir: Path) -> list[str]:
    return [f for f in structural_gate("full", artifact, session_dir)
            if "format=" in f]


SPEC = SessionEvalSpec(
    domain="ad_engine",
    domain_name="Ad Engine",
    criteria=CRITERIA,
    structural_gate=structural_gate,
    load_source_data=load_source_data,
    cross_item_criteria={
        "AD-5": CrossItemCriterion(
            glob="drafts/*.json",
            max_items=20,
            words_per_item=300,
        ),
    },
)
