"""site_engine SessionEvalSpec — per Content Engine Lanes v1 U15b + TD-30 / TD-43.

Two-pass structural gate per the U15b §approach:
- Pass 1: HTML allowlist sanitizer (nh3) — any delta = fail.
- Pass 2: render + console check via U7b — render failure or
  lane-authored console error = fail.

Per Pass-5 audit: SE-6 (a11y) + SE-7 (perf) are operator hand-graded
post-promotion (no LLM judge). Only severity=critical a11y violations
trip the Pass-2 hard fail.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

import yaml

from .session_eval_common import CrossItemCriterion, SessionEvalSpec


CRITERIA: dict[str, str] = {
    "SE-1": (
        "Visual hierarchy + CTA prominence — focal_clarity, "
        "primary_cta_prominence, scan_path_pattern. Vision-judge."
    ),
    "SE-2": (
        "Copy clarity + plain-English. Text-judge against voice "
        "persona + audience."
    ),
    "SE-3": (
        "Claim honesty + anti-overselling. Text-judge; checks for "
        "unsupported quantitative claims + AI-hype register."
    ),
    "SE-4": (
        "Voice persona fit. Text-judge against assigned persona "
        "corpus + style anchors."
    ),
    "SE-5": (
        "Brand-token + aesthetic fit. Vision-judge against client "
        "brand_tokens.json (palette + typography + spacing)."
    ),
    "SE-6": (
        "Accessibility + semantic structure. OPERATOR hand-graded "
        "at pre-publish review; only critical violations trip "
        "structural gate."
    ),
    "SE-7": (
        "Performance — payload + render time. OPERATOR hand-graded "
        "at pre-publish review."
    ),
    "SE-8": (
        "Anti-slop — AI-design-tell density + originality + brand "
        "specificity. Vision-judge."
    ),
}


# Required canonical sub-elements per section per TD-43.
_REQUIRED_SUB_ELEMENTS: dict[str, frozenset[str]] = {
    "hero": frozenset({"h1", "subhead", "primary_cta"}),
    "value_prop": frozenset({"section_heading", "body"}),
    "social_proof": frozenset(),  # one of variants (logo_wall/testimonial/etc.)
    "faq": frozenset({"section_heading", "qa_pairs"}),
    "cta": frozenset({"heading", "primary_cta"}),
    "pricing": frozenset({"tier_cards"}),
}


_REQUIRED_FRONTMATTER_KEYS: tuple[str, ...] = (
    "variant_id", "section", "voice_persona", "brand_tokens_path",
)


def _parse_frontmatter(text: str) -> dict | None:
    """Extract YAML frontmatter from an HTML comment block at top.

    Convention: site_engine HTML drafts open with
    <!-- frontmatter:
    key: value
    -->
    so the resulting file is a valid HTML5 fragment with operator-
    readable metadata in a comment."""
    match = re.search(
        r"<!--\s*frontmatter:\s*\n(.*?)\n-->", text, re.DOTALL,
    )
    if not match:
        return None
    try:
        parsed = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _strip_frontmatter(text: str) -> str:
    """Remove the frontmatter comment block; return the HTML body."""
    return re.sub(
        r"<!--\s*frontmatter:\s*\n.*?\n-->\s*", "", text,
        flags=re.DOTALL, count=1,
    )


def structural_gate(_mode: str, artifact: Path, session_dir: Path) -> list[str]:
    """Per-variant structural gate. Two-pass per the U15b plan."""
    failures: list[str] = []
    if not artifact.exists():
        failures.append(f"Artifact not found: {artifact}")
        return failures
    text = artifact.read_text(encoding="utf-8", errors="replace")

    # Frontmatter parse + required keys
    fm = _parse_frontmatter(text)
    if fm is None:
        failures.append(
            "No frontmatter comment block. FIX: open the HTML with "
            "<!-- frontmatter: ... --> declaring "
            f"{list(_REQUIRED_FRONTMATTER_KEYS)}."
        )
        return failures
    missing = [k for k in _REQUIRED_FRONTMATTER_KEYS if k not in fm]
    if missing:
        failures.append(f"Frontmatter missing required keys: {missing}.")
        return failures

    section = fm.get("section")
    if section not in _REQUIRED_SUB_ELEMENTS:
        failures.append(
            f"section={section!r} invalid; must be one of "
            f"{list(_REQUIRED_SUB_ELEMENTS)}."
        )
        return failures

    # Full-page rewrite check — v1 is SECTION-LEVEL ONLY per TD-28.
    body = _strip_frontmatter(text)
    if _count_top_level_sections(body) > 1:
        failures.append(
            "Variant attempts a full-page rewrite (multiple semantic "
            "<section> tags at top level). v1 is section-level only "
            "per TD-28; submit one section at a time."
        )

    # Pass 1: HTML sanitizer round-trip
    try:
        from src.site_engine.sanitizer import sanitize_section_html
    except ImportError:
        failures.append(
            "src.site_engine.sanitizer not importable; verify src/ "
            "is on sys.path."
        )
        return failures

    sanitizer_result = sanitize_section_html(body)
    if not sanitizer_result.safe:
        deltas_text = "; ".join(d.detail for d in sanitizer_result.deltas[:3])
        failures.append(
            f"HTML sanitizer Pass-1 fail: {deltas_text}"
        )

    # Required sub-elements check (sub-element class/data-tag hint)
    required = _REQUIRED_SUB_ELEMENTS.get(section, frozenset())
    for sub in required:
        # Sub-element presence detected via class hint OR data-element
        # attribute OR a tag-based heuristic (h1 → check for <h1>).
        if sub == "h1" and not re.search(r"<h1[\s>]", body, re.IGNORECASE):
            failures.append(f"Section {section!r} missing required <h1>.")
        elif sub == "primary_cta" and not re.search(
            r"data-element=[\"']primary_cta[\"']|class=[\"'][^\"']*primary[- ]cta",
            body, re.IGNORECASE,
        ):
            failures.append(
                f"Section {section!r} missing required primary_cta "
                f"(use data-element=\"primary_cta\" or class~=\"primary-cta\")."
            )
        elif sub in ("subhead", "section_heading", "body", "heading",
                     "qa_pairs", "tier_cards") and not re.search(
            rf"data-element=[\"']{re.escape(sub)}[\"']", body, re.IGNORECASE,
        ):
            failures.append(
                f"Section {section!r} missing required sub-element "
                f"{sub!r} (use data-element=\"{sub}\")."
            )

    # Pass 2 (render + console) — handled at evaluate-variant time by U7b.
    # The gate signals "ready for render"; the actual render runs post-gate.

    return failures


def _count_top_level_sections(html: str) -> int:
    """Count <section> tags that aren't nested inside another <section>.
    Crude: count opening section tags, allow one (the wrapper)."""
    return len(re.findall(r"<section[\s>]", html, re.IGNORECASE))


def load_source_data(_mode: str, artifact: Path, session_dir: Path) -> str:
    """Concatenate target_url + section + voice substrate + brand
    tokens + audience for the judge."""
    parts: list[str] = []

    for key in (
        "SITE_ENGINE_TARGET_URL", "SITE_ENGINE_SECTION",
        "SITE_ENGINE_AUDIENCE",
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

    brand_path = os.environ.get("SITE_ENGINE_BRAND_TOKENS_PATH", "").strip()
    if brand_path:
        try:
            parts.append(
                f"## Brand tokens\n```json\n"
                f"{Path(brand_path).read_text(encoding='utf-8')[:2000]}\n```"
            )
        except OSError:
            pass

    return "\n\n".join(parts)


# Structural gate functions for LaneSpec.structural_gate_functions

def frontmatter_yaml_required_fields(artifact: Path, session_dir: Path) -> list[str]:
    return [f for f in structural_gate("full", artifact, session_dir)
            if "frontmatter" in f.lower()]


def section_type_valid(artifact: Path, session_dir: Path) -> list[str]:
    return [f for f in structural_gate("full", artifact, session_dir)
            if "section=" in f]


def html_sanitizer_passes_unchanged(artifact: Path, session_dir: Path) -> list[str]:
    return [f for f in structural_gate("full", artifact, session_dir)
            if "sanitizer" in f.lower()]


def required_sub_elements_present(artifact: Path, session_dir: Path) -> list[str]:
    return [f for f in structural_gate("full", artifact, session_dir)
            if "missing required" in f.lower()]


def render_succeeds(artifact: Path, session_dir: Path) -> list[str]:
    """Pass-2 render check delegated to U7b at evaluate-variant time."""
    return []


def no_lane_authored_console_errors(artifact: Path, session_dir: Path) -> list[str]:
    return []  # delegated to U7b at evaluate-variant time


def no_full_page_rewrite(artifact: Path, session_dir: Path) -> list[str]:
    return [f for f in structural_gate("full", artifact, session_dir)
            if "full-page" in f.lower()]


def layout_recipe_in_allowlist(artifact: Path, session_dir: Path) -> list[str]:
    """Layout-recipe allowlist enforcement is delegated to the per-
    section schema in session.md — agent picks from declared recipes."""
    return []


SPEC = SessionEvalSpec(
    domain="site_engine",
    domain_name="Site Engine",
    criteria=CRITERIA,
    structural_gate=structural_gate,
    load_source_data=load_source_data,
    cross_item_criteria={},  # no cross-cohort rubric in v1
)
