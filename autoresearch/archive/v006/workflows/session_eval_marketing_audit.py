"""Marketing audit SessionEvalSpec — wires MA-1..MA-8 rubrics from
`programs/marketing_audit/prompts/rubrics/MA-N.md` into the autoresearch
session-judge scoring path.

Mirrors session_eval_competitive.py shape. Rubrics are inlined here (not
loaded from disk at score-time) so the substrate's frozen-prompt invariant
holds: the agent can edit the program docs but not change what the rubrics
actually measure mid-eval. Source-of-truth is the .md files in
`programs/marketing_audit/prompts/rubrics/`; keep them in sync via the
regen_marketing_audit_manifest.py script.
"""
from __future__ import annotations

import json
from pathlib import Path

from .session_eval_common import SessionEvalSpec, artifact_or_failure, count_regex


# Marketing-audit-specific banned phrases — picked from MA-6 (Polish + Voice
# Consistency). AI-tell vocabulary that drops the deliverable's
# customer-facing-agency-artifact quality bar.
MA_BANNED_PHRASES = [
    "in today's fast-paced world",
    "in the ever-evolving landscape",
    "leverage synergies",
    "drive impact",
    "unlock value",
    "best practices",
    "key takeaways",
    "deep dive",
    "moving forward",
    "going forward",
    "circle back",
    "low-hanging fruit",
]


# 9 deliverable sections per programs/marketing_audit-session.md structural
# requirements block. The structural gate verifies all 9 are present.
REQUIRED_SECTIONS = [
    "findability",
    "narrative",
    "acquisition",
    "experience",
    "competitive",
    "monitoring",
    "geo",
    "state_of_business",
    "martech_compliance",
]


CRITERIA: dict[str, str] = {
    "MA-1": (
        "Strategic Narrative Coherence — findings.md is organized around ONE strategic argument "
        "per section, not a list of issues. Every finding within a section serves the section's "
        "thesis, and every section serves a unifying audit-level thesis surfaced in the "
        "State-of-the-Business opener. Reader walks away with a strategic frame, not N "
        "disconnected problems."
    ),
    "MA-2": (
        "Evidence Traceability — Every claim cites a lens_id AND ≥1 evidence_url. Numbers are "
        "source-attributed (no naked stats). Estimates carry 'estimated' or 'approx' with "
        "explicit confidence range. Generalizations from small N are flagged. ParentFinding "
        "addresses_rubrics arrays match the lens IDs cited in evidence."
    ),
    "MA-3": (
        "Phase-0 Framing Applied — State-of-the-Business opener pulls measurements from "
        "phase0_meta.json (the 9 meta-frames). Per-section findings color by relevant Phase-0 "
        "frames where applicable. Phase-0 measurements that came back null are surfaced as "
        "findings (gap-honesty), NOT papered over."
    ),
    "MA-4": (
        "Actionable + Capability-Mapped — Each ParentFinding's recommendation is STRATEGIC "
        "(≥50 words of substance, names what would solve this in terms the agency engagement "
        "delivers) AND maps cleanly to a capability_registry tier (fix_it / build_it / run_it). "
        "Recommendations are NOT DIY execution guides; they describe the work the agency would "
        "do."
    ),
    "MA-5": (
        "Severity Calibration — Severity (0-3) on every SubSignal + ParentFinding is anchored "
        "to lens-specific severity_anchors from the rubric YAML. No severity inflation. "
        "ParentFinding severity = max of children (rollup rule). Severity distributions across "
        "the audit are credible — not a sea of '3's."
    ),
    "MA-6": (
        "Polish + Voice Consistency — Prose has the voice quality of a customer-facing $1K-$15K "
        "agency artifact. No AI-tell vocabulary. Voice is consistent across sections (one author, "
        "not five). Em-dash density is restrained. Headings parallel; no section-level voice "
        "drift."
    ),
    "MA-7": (
        "Gap Honesty — gap_flagged rubrics from per-agent rubric_coverage maps surface in "
        "gap_report.md. Missing-data findings are surfaced in findings.md, NOT papered over with "
        "speculation. Phase-0 nulls are findings. Provider-blocked lenses are honest gaps, not "
        "invented signals."
    ),
    "MA-8": (
        "Engagement-Fit — Findings + proposal align with the capability_registry. Tier-mapping "
        "serves a pitch for a $15K+ engagement (not a $1K-only artifact). At audit-render time, "
        "the rubric judges whether the deliverable IS pitching a credible agency engagement vs. "
        "reading like a one-off audit report."
    ),
}


def structural_gate(_mode: str, artifact: Path, session_dir: Path) -> list[str]:
    early = artifact_or_failure(artifact)
    if early is not None:
        return early
    failures: list[str] = []

    text = artifact.read_text(encoding="utf-8", errors="replace")

    # 9 required sections per session.md structural requirements.
    text_lower = text.lower()
    missing_sections = [s for s in REQUIRED_SECTIONS if s.replace("_", " ") not in text_lower
                        and s.replace("_", "") not in text_lower
                        and s not in text_lower]
    if missing_sections:
        failures.append(f"Missing required sections: {', '.join(missing_sections)}")

    # Headings: at least one per required section minimum.
    headings = count_regex(text, r"^#{2,3}\s+")
    if headings < 6:
        failures.append(f"Only {headings} markdown sub-headings (need 6+ for 9-section audit)")

    # Evidence URLs (MA-2): every audit needs source URLs.
    evidence_urls = count_regex(text, r"https?://")
    if evidence_urls < 3:
        failures.append(f"Only {evidence_urls} source URLs cited (need 3+ for MA-2 evidence traceability)")

    # ParentFinding count — at least one per section minimum.
    parent_findings = count_regex(text, r"^### ")
    if parent_findings < 5:
        failures.append(f"Only {parent_findings} ParentFinding headers (need 5+ across 9 sections)")

    # MA-6 banned-phrase check.
    found_banned = [p for p in MA_BANNED_PHRASES if p in text_lower]
    if found_banned:
        failures.append(f"AI-tell phrases found (MA-6 violation): {', '.join(found_banned[:3])}"
                       + (f" (+{len(found_banned)-3} more)" if len(found_banned) > 3 else ""))

    # Word-count sanity — multi-section audit shouldn't be a one-pager.
    word_count = len(text.split())
    if word_count < 800:
        failures.append(f"findings.md is {word_count} words (need 800+ for 9-section audit)")
    if word_count > 8000:
        failures.append(f"findings.md is {word_count} words (max 8000 — over-length kills MA-6 polish)")

    return failures


def load_source_data(_mode: str, _artifact: Path, session_dir: Path) -> str:
    """Surface phase0_meta.json + per-Stage-2-agent outputs + gap_report.md to
    the inner critic so it can verify MA-2 evidence traceability claims and
    MA-3 Phase-0 framing alignment."""
    parts: list[str] = []

    # Phase 0 meta — the 9 meta-frames the State-of-the-Business opener
    # should pull from.
    phase0_path = session_dir / "phase0" / "phase0_meta.json"
    if not phase0_path.exists():
        phase0_path = session_dir / "phase0_meta.json"
    if phase0_path.exists():
        try:
            content = phase0_path.read_text(encoding="utf-8", errors="replace")
            parts.append(f"## phase0_meta.json (the 9 Phase-0 meta-frames)\n```json\n{content[:3000]}\n```")
        except OSError:
            pass

    # Per-Stage-2-agent outputs (findability/narrative/acquisition/experience).
    for agent in ("findability", "narrative", "acquisition", "experience"):
        agent_dir = session_dir / agent
        if agent_dir.exists():
            for path in sorted(agent_dir.glob("*.json"))[:2]:
                try:
                    content = path.read_text(encoding="utf-8", errors="replace")
                    parts.append(f"## {agent}/{path.name}\n```json\n{content[:1500]}\n```")
                except OSError:
                    continue

    # Gap report — MA-7 gap honesty check.
    gap_path = session_dir / "gap_report.md"
    if gap_path.exists():
        try:
            content = gap_path.read_text(encoding="utf-8", errors="replace")
            parts.append(f"## gap_report.md\n{content[:1500]}")
        except OSError:
            pass

    # Lens outputs — raw lens evidence the agent's findings should trace to.
    lens_dir = session_dir / "lens_outputs"
    if lens_dir.exists():
        for path in sorted(lens_dir.glob("*.json"))[:5]:
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
                parts.append(f"## lens_outputs/{path.name}\n```json\n{content[:800]}\n```")
            except OSError:
                continue

    # findings.md context already passed via artifact param — don't double-include.

    return "\n\n".join(parts)


SPEC = SessionEvalSpec(
    domain="marketing_audit",
    domain_name="Marketing Audit",
    criteria=CRITERIA,
    structural_gate=structural_gate,
    load_source_data=load_source_data,
)
