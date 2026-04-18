from __future__ import annotations

import json
from pathlib import Path

from .session_eval_common import (
    CrossItemCriterion,
    SessionEvalSpec,
)


CRITERIA: dict[str, str] = {
    "GEO-1": (
        "Each content block contains a self-contained, quotable answer to a real question "
        "someone types into an AI search engine. An AI retrieval system should be able to "
        "extract any single paragraph or FAQ answer and use it as a complete response — no "
        "meaning lost, no clicking through required."
    ),
    "GEO-2": (
        "The facts are specific, verifiable, and current. \"$249/month for 2,000 tracked "
        "keywords\" not \"affordable plans for every budget.\" Concrete numbers, named "
        "competitors, dated claims. Every data point traces to something the client can "
        "verify before publishing."
    ),
    "GEO-3": (
        "It honestly positions the client within the competitive landscape, including where "
        "they lose. First-party content has a natural credibility ceiling with AI engines. "
        "The only way through it is earned trust: acknowledge where competitors genuinely win."
    ),
    "GEO-4": (
        "Every block fits the page's existing voice, structure, and scope — with placement "
        "instructions precise enough for a developer to ship without interpretation. Content "
        "reads like it was always there, not bolted on. Scoped to what this one page can "
        "realistically achieve."
    ),
    "GEO-5": (
        "It publishes knowledge only this company can credibly provide — the citability moat. "
        "Proprietary methodology, category-specific technical depth, unique feature "
        "explanations. These create queries where the client's page becomes the only credible "
        "primary source."
    ),
    "GEO-6": (
        "Across all pages in a session, each one tells a different story. No two pages use "
        "the same primary differentiator, repeat the same competitive framing, or lean on "
        "the same statistics. Cross-page coherence means the pages reinforce each other as a "
        "site, not cannibalize each other."
    ),
    "GEO-7": (
        "The content directly and completely answers the target queries declared for the "
        "page. For each target query, a user typing exactly that into an AI search engine "
        "would receive a satisfying answer from this page alone. The content matches search "
        "intent — informational queries get explanations, commercial queries get comparisons, "
        "transactional queries get pricing and next steps. A page optimized for \"how much "
        "does Ahrefs cost\" that provides company history instead of pricing fails regardless "
        "of structural quality."
    ),
    "GEO-8": (
        "Technical recommendations fix real problems found on the actual page, not "
        "boilerplate. \"21 of 22 images lack alt text\" is actionable. \"Consider adding alt "
        "text to images\" is not."
    ),
}

def structural_gate(_mode: str, artifact: Path, session_dir: Path) -> list[str]:
    failures = []
    if not artifact.exists():
        failures.append(f"Artifact not found: {artifact}")
        return failures

    gap_file = session_dir / "gap_allocation.json"
    if not gap_file.exists():
        failures.append(
            "gap_allocation.json not found. FIX: create it at "
            "<session_dir>/gap_allocation.json with allocations[] array (see Decision Flow in program)."
        )
    elif gap_file.stat().st_size < 10:
        failures.append("gap_allocation.json is empty or trivial — add at least one allocation entry.")

    text = artifact.read_text(encoding="utf-8", errors="replace")
    if "[FAQ]" not in text and "## FAQ" not in text.upper() and "## Frequently Asked" not in text:
        failures.append(
            "No FAQ block found. FIX: add a [FAQ] block with 5-7 self-contained Q&A pairs. "
            "This is the highest-impact single change for AI engine citability."
        )
    if "[INTRO]" not in text:
        failures.append(
            "No [INTRO] block found. FIX: add an [INTRO] block with a 40-60 word answer-first opening "
            "that names the product and a specific competitor differentiator in the first two sentences."
        )

    if len(text.split()) < 300:
        failures.append(
            f"Artifact is only {len(text.split())} words — too thin to pass quality evaluation. "
            "Minimum: 300 words with actual content blocks, not just headings."
        )
    return failures


def load_source_data(_mode: str, artifact: Path, session_dir: Path) -> str:
    parts: list[str] = []
    slug = artifact.stem
    page_file = session_dir / "pages" / f"{slug}.json"
    if page_file.exists():
        try:
            page_data = json.loads(page_file.read_text(encoding="utf-8", errors="replace"))
            parts.append(f"## Original Page Data\n```json\n{json.dumps(page_data, indent=2)[:3000]}\n```")
        except (json.JSONDecodeError, OSError):
            pass

    gap_file = session_dir / "gap_allocation.json"
    if gap_file.exists():
        try:
            gap_data = gap_file.read_text(encoding="utf-8", errors="replace")
            parts.append(f"## Target Queries (gap_allocation.json)\n```json\n{gap_data[:2000]}\n```")
        except OSError:
            pass
    audit_full = session_dir / "audits" / f"{slug}.full.json"
    audit_basic = session_dir / "audits" / f"{slug}.json"
    audit_file = audit_full if audit_full.exists() else audit_basic
    if audit_file.exists():
        try:
            parts.append(f"## Technical Audit: {slug}\n```json\n{audit_file.read_text(encoding='utf-8', errors='replace')[:800]}\n```")
        except OSError:
            pass
    return "\n\n".join(parts)


SPEC = SessionEvalSpec(
    domain="geo",
    domain_name="GEO (Generative Engine Optimization)",
    criteria=CRITERIA,
    structural_gate=structural_gate,
    load_source_data=load_source_data,
    cross_item_criteria={"GEO-6": CrossItemCriterion(glob="optimized/*.md", max_items=5, words_per_item=500)},
)
