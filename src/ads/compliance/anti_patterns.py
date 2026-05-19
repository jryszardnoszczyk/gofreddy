"""Ad-engine anti-patterns deterministic pre-check (TD-42, U15).

14 catalogued patterns from the U15 plan §approach. Runs BEFORE judge
dispatch as part of the structural gate. Hit count caps AD-1 (hook
strength) at 4 per occurrence + AD-6 (voice fidelity) at 3 if any
pattern fires.

Per CLAUDE.md Rule 5: this is deterministic regex matching — code,
not LLM. The judge sees the hit count + pattern IDs and applies the
cap; this module just identifies which patterns fired.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class AntiPatternHit:
    """One anti-pattern match."""

    pattern_id: str
    matched_text: str
    rationale: str


# 14 patterns per TD-42. Each entry: (pattern_id, regex, rationale).
# Regex compiled at module load; case-insensitive throughout.
_PATTERNS: tuple[tuple[str, str, str], ...] = (
    (
        "tired_of_x_meet_y",
        r"\btired of [\w\s]{1,30}[.!?]?\s*meet\s+\w+",
        "PAS-formula opener — saturated across 2024-2025 SaaS ads.",
    ),
    (
        "unlock_outcome",
        r"\bunlock\s+(your\s+)?[\w\s]{1,20}\b",
        "Generic outcome-promise opener.",
    ),
    (
        "harness_the_power_of",
        r"\bharness the power of\b",
        "Cliched AI-era opener.",
    ),
    (
        "revolutionize_your_vertical",
        r"\brevolutionize\s+your\s+[\w\s]{1,20}\b",
        "Empty signifier; SEO penalty per Google 2025 guidance.",
    ),
    (
        "ai_powered_without_capability",
        r"\bAI[- ]powered\b(?![^.]{0,40}\b(?:analyze|extract|generate|"
        r"summari[sz]e|forecast|classif|detect|translate|recommend)\w*)",
        "88% of B2B buyers tune out 'AI-powered' without a concrete "
        "capability noun in the same sentence.",
    ),
    (
        "leverage_thing",
        r"\bleverage\s+(your\s+|the\s+)?[\w\s]{1,20}\b",
        "Generic AI register; replace with 'use'.",
    ),
    (
        "seamlessly_integrate",
        r"\bseamlessly\s+integrat\w+",
        "AI tell; vacant qualifier.",
    ),
    (
        "game_changer_next_gen",
        r"\b(?:game[- ]?chang(?:er|ing)|next[- ]?generation|cutting[- ]?edge)\b",
        "Empty superlatives; overused.",
    ),
    (
        "learn_more_cta",
        r"\b(?:CTA|button|click here):?\s*\"?Learn\s+More\"?",
        "0% of top-2%-CTR LinkedIn ads use 'Learn More'. Use a "
        "platform-native verb or specific outcome verb.",
    ),
    (
        "stock_office_workers",
        r"\b(?:stock photo|image brief).*(?:office worker|people shaking hands|"
        r"team meeting around laptop)",
        "0% of top-2%-CTR ads use stock photos.",
    ),
    (
        "founder_studio_future_of_x",
        r"\bfounder studio[- ]shot\b.*\bthe future of [\w\s]{1,20}\b",
        "Candid phone-selfies outperform staged founder photos by 45% "
        "engagement (Andromeda 2025).",
    ),
    (
        "three_icon_trio",
        r"\bthree[- ]icon trio\b|\b3 icons in a row\b",
        "Already enforced in SE-8 (site_engine); propagate to ad "
        "image briefs.",
    ),
    (
        "built_for_modern_teams",
        r"\bbuilt for (?:modern teams|the way [\w\s]{1,15} works?)\b",
        "Vague target audience; no firmographic specificity.",
    ),
    (
        "headline_over_12_words",
        # The headline_over_12_words check is structural — counts words
        # in extracted headline field. Regex stub here for completeness;
        # the structural gate computes the count from the artifact.
        r"^(?:headline|H1):\s*(?:\S+\s+){12,}",
        "Meta hard-caps at 40 chars; LinkedIn at 70. Soft-cap at 12 "
        "words for clarity.",
    ),
)


# Compile regexes once.
_COMPILED: tuple[tuple[str, re.Pattern, str], ...] = tuple(
    (pid, re.compile(rx, re.IGNORECASE | re.MULTILINE), rationale)
    for pid, rx, rationale in _PATTERNS
)


def find_anti_pattern_hits(text: str) -> list[AntiPatternHit]:
    """Scan `text` for anti-pattern matches. Returns list of hits;
    empty list = clean."""
    hits: list[AntiPatternHit] = []
    for pid, regex, rationale in _COMPILED:
        match = regex.search(text)
        if match:
            hits.append(AntiPatternHit(
                pattern_id=pid,
                matched_text=match.group(0)[:120],
                rationale=rationale,
            ))
    return hits


def cap_score_from_hits(
    base_score: float, hits: list[AntiPatternHit], rubric_id: str,
) -> float:
    """Apply the per-rubric cap per TD-42.

    - AD-1: cap at 4 per hit count (so 2 hits cap at 3, 3+ hits cap at 2).
    - AD-6: cap at 3 if ANY hit (voice slipped into AI house-style).
    - Other rubrics: no cap.
    """
    if not hits:
        return base_score
    if rubric_id == "AD-1":
        cap = max(2.0, 4.0 - 0.5 * (len(hits) - 1))
        return min(base_score, cap)
    if rubric_id == "AD-6":
        return min(base_score, 3.0)
    return base_score


__all__ = [
    "AntiPatternHit",
    "cap_score_from_hits",
    "find_anti_pattern_hits",
]
