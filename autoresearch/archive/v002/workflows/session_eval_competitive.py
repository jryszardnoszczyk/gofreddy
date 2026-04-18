from __future__ import annotations

from pathlib import Path

from .session_eval_common import SessionEvalSpec, count_regex


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
        "The brief has a thesis, not just findings. A single strategic argument organizes "
        "the entire document. Every section serves that argument. The reader finishes knowing "
        "one thing clearly, not twelve things vaguely."
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
        "It identifies asymmetric opportunities — gaps in the landscape that match the "
        "client's strengths. Not just what no one is doing, but what no one is doing that "
        "this client is uniquely positioned to own."
    ),
    "CI-6": (
        "Findings contradict each other or the client's assumptions, and the brief says so. "
        "Uncomfortable truths survive editing. The brief is not optimized to make the client "
        "feel good about their current approach."
    ),
    "CI-7": (
        "The brief makes hard calls about what matters most. Not everything is Priority 1. "
        "The reader knows which 2-3 actions drive disproportionate impact and which findings "
        "are interesting but not urgent."
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
    failures = []
    if not artifact.exists():
        failures.append(f"Artifact not found: {artifact}")
        return failures

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

    has_sov = bool(count_regex(text, r"(?:share of observed|SOV|share of voice)"))
    has_pct = bool(count_regex(text, r"\d+(?:\.\d+)?%"))
    if not (has_sov and has_pct):
        failures.append("No SOV/share-of-voice data with percentages found")
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
    return "\n\n".join(parts)


SPEC = SessionEvalSpec(
    domain="competitive",
    domain_name="Competitive Intelligence",
    criteria=CRITERIA,
    structural_gate=structural_gate,
    load_source_data=load_source_data,
)
