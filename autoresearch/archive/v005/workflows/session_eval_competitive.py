from __future__ import annotations

import json
import re
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


def _has_competitor_grounding(text: str, session_dir: Path) -> bool:
    """Return True if brief.md contains verbatim text from competitor source files.

    Checks ad headlines/body_text for ad-tier competitors and quoted website copy
    for scrape-only competitors. Returns True (skip check) when no competitor data
    exists yet — the gate is only meaningful after GATHER completes.
    """
    comp_dir = session_dir / "competitors"
    if not comp_dir.exists():
        return True  # no source data yet; skip

    comp_files = [
        p for p in sorted(comp_dir.glob("*.json"))
        if not p.name.startswith("_") and not p.name.endswith("_raw.json")
    ]
    if not comp_files:
        return True  # no competitor files; skip

    for path in comp_files[:6]:
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue

        # Check verbatim ad text fields
        for ad in (data.get("ads") or [])[:50]:
            for field in ("headline", "body_text", "cta_text"):
                val = str(ad.get(field, "")).strip()
                if len(val) > 10 and val in text:
                    return True

        # For scrape-only competitors, look for quoted phrases from website copy.
        # Strategy: extract all double-quoted strings from the brief, then check
        # if any appear verbatim in the competitor's scraped text fields.
        # This bidirectional check handles the common case where the brief quotes
        # a headline or sentence from the scrape, even when the raw scrape text
        # does not itself contain embedded double-quote characters.
        scrape = data.get("scrape") or {}
        brief_quotes = re.findall(r'"([^"\n]{10,150})"', text)
        scrape_text_parts: list[str] = []
        for page in (scrape.get("pages") or [])[:3]:
            for field in ("h1", "meta_description", "title"):
                val = str(page.get(field, "")).strip()
                if val:
                    scrape_text_parts.append(val)
            # Use text field (current format) or content field (legacy format)
            page_body = str(page.get("text") or page.get("content") or "").strip()
            if page_body:
                scrape_text_parts.append(page_body)
        scrape_full = " ".join(scrape_text_parts)
        if scrape_full:
            for quote in brief_quotes:
                if quote in scrape_full:
                    return True
            # Legacy fallback: split content on double-quotes
            for chunk in scrape_full.split('"'):
                chunk = chunk.strip()
                if len(chunk) > 10 and chunk in text:
                    return True

    return False


def structural_gate(_mode: str, artifact: Path, session_dir: Path) -> list[str]:
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

    # Grounding check: brief must contain verbatim text from competitor source data.
    # The outer-loop grounding matcher requires exact quotes from competitors/*.json.
    # A brief that passes all other gates but has no verbatim source quotes scores 0.
    if not _has_competitor_grounding(text, session_dir):
        failures.append(
            "Grounding check failed: no verbatim competitor text found in brief.md. "
            "Include exact ad headlines or website copy in double quotes, e.g.: "
            "'Canva (100 ads, Foreplay): \"Design anything, anywhere\" — targeting SMBs'. "
            "Without source quotes the outer grounding scorer assigns score=0."
        )

    return failures


def load_source_data(_mode: str, _artifact: Path, session_dir: Path) -> str:
    """Build source context for the external judge.

    Provides structured headline lists rather than raw JSON truncation so the
    judge can verify whether brief.md actually quotes from the source data.
    """
    parts: list[str] = []
    comp_dir = session_dir / "competitors"
    if comp_dir.exists():
        for path in sorted(comp_dir.glob("*.json"))[:6]:
            if path.name.endswith("_raw.json"):
                continue
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            try:
                data = json.loads(content)
                ads = data.get("ads") or []
                headlines = [
                    str(ad.get("headline", "")).strip()
                    for ad in ads[:30]
                    if str(ad.get("headline", "")).strip()
                ]
                summary: dict = {
                    "name": data.get("name", path.stem),
                    "data_tier": data.get("data_tier", "unknown"),
                    "ad_count": len(ads),
                    "sample_headlines": headlines[:20],
                }
                # For scrape-only competitors, include website copy for grounding verification
                if not headlines:
                    scrape = data.get("scrape") or {}
                    pages = scrape.get("pages") or []
                    if pages:
                        summary["scrape_excerpt"] = str(pages[0].get("content", ""))[:500]
                parts.append(
                    f"## Competitor: {path.stem}\n```json\n{json.dumps(summary, indent=2)}\n```"
                )
            except Exception:
                # Fallback to raw truncation
                parts.append(f"## Competitor: {path.stem}\n```json\n{content[:2000]}\n```")
    return "\n\n".join(parts)


SPEC = SessionEvalSpec(
    domain="competitive",
    domain_name="Competitive Intelligence",
    criteria=CRITERIA,
    structural_gate=structural_gate,
    load_source_data=load_source_data,
)
