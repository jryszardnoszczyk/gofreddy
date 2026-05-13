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
        "The brief states a single, client-specific, contestable thesis containing a "
        "strategic recommendation the client could accept or reject. The thesis passes the "
        "client-substitution test: replacing the client's name with a generic peer breaks "
        "the recommendation's specificity (recommendation only makes sense for THIS client "
        "given its specific capabilities). The brief presents at least one substantive "
        "piece of evidence-against, paired with an explicit reason the recommendation "
        "survives despite the counter — not a single dismissive sentence (\"while X, the "
        "client's broader platform compensates\"). Score 3: thesis is generic enough that "
        "any peer could fit it, or counter-evidence is defused immediately. Anti-gaming: "
        "\"challenges\" sections containing weak counter-arguments that don't actually "
        "complicate the recommendation fail."
    ),
    "CI-2": (
        "Every claim traces to something observed, and confidence is explicit. When data is "
        "incomplete or contradictory, the brief says so and adjusts its conclusions "
        "proportionally. No claim outruns its evidence."
    ),
    "CI-3": (
        "Each competitor is understood by their trajectory — what they're building toward, "
        "not just where they are. The brief articulates apparent strategy, rate of change, "
        "and what each competitor is abandoning."
    ),
    "CI-4": (
        "Recommendations are specific, time-bound, and sized to the client's actual capacity "
        "to act. \"Deploy llms.txt by Mar 26\" is good. \"Deploy llms.txt by Mar 26, your "
        "dev can do this in a half-day\" is better. Recommendations the client can't execute "
        "are decoration."
    ),
    "CI-5": (
        "For each named gap, the brief cites a client capability that passes the "
        "competitor-substitution test: replacing the client with its closest peer would "
        "break the strategic logic. The capability rests on something the client uniquely "
        "has (a specific data asset, a specific integration partner, a specific team "
        "composition, a specific market position) — not a generic label (\"our AI "
        "platform,\" \"our enterprise sales motion\"). Score 3: pairing is generic enough "
        "that a competitor with similar capabilities could pursue the same gap with the "
        "same logic. Anti-gaming: capability names without a single concrete asset behind "
        "them (a named product feature, a named partnership, a named customer base) fail."
    ),
    "CI-6": (
        "The brief includes at least one finding that would prompt a real strategic "
        "decision if the client accepted it — naming a capability the client cannot quickly "
        "close, a market position eroding faster than the client's plans assume, or a "
        "structural shift that invalidates a piece of the client's stated strategy. The "
        "uncomfortable truth is specific enough that a stakeholder could plausibly veto its "
        "inclusion (\"we shouldn't say this\") rather than waving it through as standard "
        "caution. Score 3: uncomfortable findings narrowly scoped to not threaten the "
        "position (e.g., a competitor wins in a market the client doesn't compete in), or "
        "immediately neutralized within the same paragraph. Anti-gaming: hedge-defused "
        "counters (\"while X is concerning, broader strengths compensate\") in the same "
        "sentence fail."
    ),
    "CI-7": (
        "The top 2-3 actions are ranked AND the brief makes an explicit case for the "
        "sequencing — naming what's lost by doing lower-ranked actions first, what's gained "
        "by doing the top action despite its costs. The case is specific enough that a "
        "stakeholder could rebut it by challenging the brief's tradeoff weighting. Score 3: "
        "ranking rests on labels (\"Priority 1\" / \"Priority 2\") without explaining why "
        "doing 1 first beats doing 2 first. Anti-gaming: applying multiple priority axes "
        "(\"Priority 1, Quick Win, Strategic\") without forcing a single sequence, or "
        "labeling everything \"high impact,\" both fail. The ranking must be a commitment, "
        "not a categorization."
    ),
    "CI-8": (
        "When data sources failed, the brief recalibrates rather than speculates. It names "
        "what is missing, what analysis became impossible, and how the remaining data changes "
        "what can be concluded. It does not silently omit gap-affected sections or present "
        "inferred data with unearned confidence. The gap itself is treated as an intelligence "
        "finding."
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
