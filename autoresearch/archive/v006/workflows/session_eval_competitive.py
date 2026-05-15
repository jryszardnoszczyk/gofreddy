from __future__ import annotations

import re
from pathlib import Path

from .session_eval_common import SessionEvalSpec, artifact_or_failure, count_regex


# Structural-validator bullets — see session_eval_geo.STRUCTURAL_DOC_FACTS for
# the contract these enforce. ``autoresearch.regen_program_docs`` reads this
# tuple when stamping the AUTOGEN block in ``programs/competitive-session.md``.
STRUCTURAL_DOC_FACTS: tuple[str, ...] = (
    "A file with `brief` in its name ending in `.md` exists (e.g. `brief.md`).",
    "At least one `competitors/<name>.json` (excluding `_`-prefixed helpers) is present and parses as valid JSON — shape only; judges evaluate sufficiency.",
)


CI_BANNED_PHRASES = [
    "leverage social media",
    "stay ahead",
    "consider exploring",
    "it's clear that",
    "no doubt",
    "it goes without saying",
    "needless to say",
    "at the end of the day",
    "game-changer",
    "best-in-class",
    "synergy",
    "low-hanging fruit",
]

CRITERIA: dict[str, str] = {
    "CI-1": (
        "The brief leads with a single, client-specific strategic claim a decision-maker could "
        "accept or reject ('Acme's bundling targets our SMB renewal base; respond by Q3 or "
        "lose 30% of cohort'). Every section provides evidence for, against, or nuance to that "
        "claim. Per Octopus Intelligence + Klue executive-briefing template + CI Alliance: "
        "headline is a claim, not a topic. Cataloguing without a position fails."
    ),
    "CI-2": (
        "Each finding walks observation → inference → implication → recommendation, forcing "
        "a 'so what?' at every stage. Observations name specific data sources (not 'research "
        "shows'). Inferences are explicit. Implications connect to a client decision. Per SCIP "
        "methodology + Heuer & Pherson tradecraft + CI Alliance: 'so what' is what separates "
        "intelligence from reporting."
    ),
    "CI-3": (
        "Each competitor's trajectory (next 6-18 months) is articulated using convergent "
        "signals — patents, M&A, headcount, earnings-call language, product launches, "
        "abandoned SKUs — not just current snapshot. The brief commits to a forward direction "
        "specific enough to disagree with. Per CB Insights teardown structure (WHAT-NOW / "
        "WHERE-NEXT / WHY-PRIORITY) + Grove's 10X forces."
    ),
    "CI-4": (
        "Claimed competitor advantages identify a specific Helmer power (Scale Economies / "
        "Network Economies / Counter-Positioning / Switching Costs / Branding / Cornered "
        "Resource / Process Power) or Porter force, AND apply both halves of the Benefit + "
        "Barrier test, AND distinguish operational effectiveness (replicable) from strategic "
        "positioning (sustainable trade-offs). 'They have network effects' without winner-"
        "take-all dynamics fails."
    ),
    "CI-5": (
        "The brief commits to a specific posture (attack / defend / flank / cooperate / "
        "ignore) AND names the hard trade-off — what is being deliberately deprioritized. "
        "Where-to-play and how-to-win choices are inseparable per Roger Martin. "
        "Recommendations requiring no trade-off are red flags (real strategy always costs "
        "something). A stakeholder could rebut the trade-off framing."
    ),
    "CI-6": (
        "The brief states at least one finding a stakeholder would push back on — a durable "
        "competitor advantage, structural weakness, or trend undermining client strategy. "
        "Considers at least one plausible alternative hypothesis (ACH-style) for key findings. "
        "Names key assumptions explicitly. Per Heuer & Pherson Structured Analytic Techniques "
        "+ CI Alliance bias warning + Klue 'kill your darlings.'"
    ),
    "CI-7": (
        "Exactly 2-3 top-tier recommendations, clearly separated from secondary items. Each "
        "has (a) specific action not verb-of-interest; (b) dated deadline ('by Q3 2026'); (c) "
        "consequence-of-inaction or priority rationale. The brief explicitly names what is "
        "being deprioritized. Per Klue top-3-5 rule + CI Alliance 'specific, actionable, tied "
        "to business impact' + PMA no-vague-verbs."
    ),
    "CI-8": (
        "The brief locates the industry on the BCG Advantage Matrix (Volume / Stalemate / "
        "Fragmented / Specialisation) with named evidence, AND accounts for at least three of "
        "Porter's five forces beyond direct rivalry (supplier power, buyer power, substitutes, "
        "new entrants). A recommendation tuned to a Volume industry is wrong for a Stalemate "
        "one. Per BCG + Porter Five Forces."
    ),
}

def structural_gate(_mode: str, artifact: Path, _session_dir: Path) -> list[str]:
    early = artifact_or_failure(artifact)
    if early is not None:
        return early
    failures: list[str] = []

    text = artifact.read_text(encoding="utf-8", errors="replace")
    headings = count_regex(text, r"^#{1,6}\s+")
    if headings < 3:
        failures.append(f"Only {headings} markdown headings (need 3+)")

    citation_patterns = count_regex(text, r"(?:source:|data from|according to|per\s|via\s|\[.*?\]\(http)")
    if citation_patterns < 2:
        failures.append(f"Only {citation_patterns} data source citations (need 2+)")

    word_count = len(text.split())
    if word_count > 2000:
        failures.append(f"Brief is {word_count} words (max 2000)")

    text_lower = text.lower()
    found_banned = [phrase for phrase in CI_BANNED_PHRASES if phrase.lower() in text_lower]
    if found_banned:
        failures.append(f"Banned phrases found: {', '.join(found_banned)}")

    # SOV check: require SOV term AND a percentage in the SAME sentence,
    # excluding negation phrasing ("would be misleading", "not SOV", etc).
    # Prevents passing on "A 0% SOV label would be misleading" (run #2 bug).
    _sov_sentences = re.findall(
        r"[^.!?\n]*(?:share of observed|SOV|share of voice)[^.!?\n]*",
        text,
        re.IGNORECASE,
    )
    _valid_sov = False
    for _sent in _sov_sentences:
        _low = _sent.lower()
        if "misleading" in _low or "would be" in _low or "not a" in _low:
            continue
        if re.search(r"\d+(?:\.\d+)?%", _sent):
            _valid_sov = True
            break
    if not _valid_sov:
        failures.append("No valid SOV/share-of-voice data with percentages in same sentence (negation-filtered)")
    return failures


def load_source_data(_mode: str, _artifact: Path, session_dir: Path) -> str:
    parts: list[str] = []
    comp_dir = session_dir / "competitors"
    if comp_dir.exists():
        for path in sorted(comp_dir.glob("*.json"))[:5]:
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            parts.append(f"## Competitor: {path.stem}\n```json\n{content[:2000]}\n```")
    fmd = session_dir / "findings.md"
    if fmd.exists():
        try: parts.append(f"## Competitive Findings\n{fmd.read_text(encoding='utf-8', errors='replace')[:1500]}")
        except OSError: pass
    adir = session_dir / "analyses"
    if adir.exists():
        for path in sorted(adir.glob("*.md"))[:3]:
            try: parts.append(f"## Analysis: {path.stem}\n{path.read_text(encoding='utf-8', errors='replace')[:800]}")
            except OSError: continue
    return "\n\n".join(parts)


SPEC = SessionEvalSpec(
    domain="competitive",
    domain_name="Competitive Intelligence",
    criteria=CRITERIA,
    structural_gate=structural_gate,
    load_source_data=load_source_data,
)
