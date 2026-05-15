from __future__ import annotations

import json
from pathlib import Path

from .session_eval_common import (
    CrossItemCriterion,
    SessionEvalSpec,
    artifact_or_failure,
)


# Structural-validator bullets read by ``autoresearch.regen_program_docs`` when
# stamping the AUTOGEN block in ``programs/geo-session.md``. The variant's gate
# code is the source of truth for *this variant's* prompt; a meta-agent that
# adds a new ``failures.append(...)`` to ``structural_gate`` should also append
# the matching bullet here. Drift is caught by ``test_structural_doc_facts``.
STRUCTURAL_DOC_FACTS: tuple[str, ...] = (
    "At least one `optimized/<file>` is present with non-empty content.",
    "Every `<script type=\"application/ld+json\">` block inside an optimized file parses as valid JSON.",
    "`gap_allocation.json` exists at the session root with at least one allocation entry.",
    "The artifact contains a `[FAQ]` marker, or a `## FAQ` heading, or a `## Frequently Asked` heading (around the 5-7 Q&A block from CQ-2).",
    "The artifact contains a literal `[INTRO]` marker — the bracket form is required; `## Intro` / `## Introduction` will fail.",
    "The artifact is at least 300 words. The `[HOWTO]`, `[SCHEMA]`, `[TECHFIX]`, `[PRUNE]`, and `[FILL]` markers follow the same bracket convention and are read by `scripts/build_geo_report.py` when compiling the final report.",
)


CRITERIA: dict[str, str] = {
    "GEO-1": (
        "Every 40-75 word passage stands alone — named entities present, no orphan pronouns, "
        "no 'as mentioned above' references. Per Volpini's chunk-completeness principle and "
        "Profound's passage study (40-75w passages cited 3.1× more often), the unit of AI-"
        "engine citation is the passage, not the page. Headings restate the entity; lists "
        "self-resolve."
    ),
    "GEO-2": (
        "Substantive claims pair with verifiable evidence: dated statistics with named sources, "
        "direct quotations from credible third parties, inline citations to external authority "
        "or first-party data with stated methodology. Per Aggarwal et al. (KDD 2024), evidence-"
        "injection methods lift AI-engine visibility +28-40%. Vague marketing copy ('leading,' "
        "'industry-best') fails."
    ),
    "GEO-3": (
        "The content names alternatives (including 'do nothing'), cites at least one external "
        "voice (analyst, journalist, comparison-site, named customer), and acknowledges at "
        "least one specific area where a named competitor genuinely wins. Per Forrester 2026, "
        "AI buyers validate vendor claims against external sources before trusting. The Verge "
        "documented Google AI Mode discounting vendor self-isolation."
    ),
    "GEO-4": (
        "The product/brand is named consistently across sections — same string, capitalization, "
        "spacing. A one-sentence entity definition appears early ('X is an A for B who need C'). "
        "Subject-predicate-object statements repeat the entity's identity. Per Kalicube Entity "
        "SEO + Slawski's patent analysis: embeddings cluster name variants as separate entities, "
        "fragmenting citation signal."
    ),
    "GEO-5": (
        "The page's first 40-75 words of meaningful body content land a declarative claim — "
        "names the entity, identifies its category, names its primary differentiator and target "
        "audience — in document register, not query-echo register. Per Skywork 2025: 90% of top-"
        "cited Perplexity answers deliver the core in the first 100 words. Profound: 44% of AI "
        "citations come from the top third of pages."
    ),
    "GEO-6": (
        "Across all pages in a session, each one tells a different story. No two pages use "
        "the same primary differentiator, repeat the same competitive framing, or lean on "
        "the same statistics. Cross-page coherence means the pages reinforce each other as a "
        "site, not cannibalize each other."
    ),
    "GEO-7": (
        "The page declares its target queries; each declared query is directly answered by a "
        "specific passage. Format matches query class: 'Best X for Y' → comparison table/list; "
        "'How to X' → ordered steps; 'X vs Y' → side-by-side. Per Shepard's #5/#6 (9.2/9.0) "
        "and Profound's table-vs-prose finding (tables cited 4.2× more on comparison content)."
    ),
    "GEO-8": (
        "Technical recommendations fix real problems found on the actual page, not "
        "boilerplate. \"21 of 22 images lack alt text\" is actionable. \"Consider adding alt "
        "text to images\" is not."
    ),
    "GEO-9": (
        "A visible publication or update date appears near the top, dated within the last "
        "12-18 months. Body content contains current-year references where relevant. Statistics "
        "are time-stamped. Third-party citations include dates. Per Skywork 2025 Perplexity "
        "(70% top-cited sources have 12-18mo date) + Search Engine Land 8K-citation (44% "
        "from current-year content). Generic evergreen ('modern,' 'today's') fails."
    ),
}

def structural_gate(_mode: str, artifact: Path, session_dir: Path) -> list[str]:
    early = artifact_or_failure(artifact)
    if early is not None:
        return early
    failures: list[str] = []

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
