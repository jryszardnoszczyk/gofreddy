"""image_engine SessionEvalSpec — per Content Engine Lanes v1 U14 + TD-41.

Mirrors session_eval_article_engine.py shape: per-rubric display criteria
strings, per-artifact `structural_gate` enforcing format dispatch + slide
count + dimensions + anti-patterns, a `load_source_data` returning topic
+ voice substrate + brand tokens, and a cross-cohort criterion for IE-6
over `drafts/*/slide_*.png` (carousel rollup).

Per JR's 2026-05-19 U14 decisions:
- All 6 formats validated here (full v1 scope).
- Vision rubrics routed through vision_judge (separate primitive).
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

import yaml

from .session_eval_common import CrossItemCriterion, SessionEvalSpec


# Display criteria — what the in-session evaluator shows the agent.
# Mirrored by RUBRICS prose in src/evaluation/rubrics.py.
CRITERIA: dict[str, str] = {
    "IE-1": (
        "Hook visual — focal subject readable at 120px thumbnail, "
        "text-overlay ≤7 words, viewer can identify subject + claim "
        "in <2 seconds."
    ),
    "IE-2": (
        "Brand consistency — palette ΔE ≤15 from brand tokens, "
        "typography matches brand, logo Pillow-composited (NEVER "
        "fal-rendered)."
    ),
    "IE-3": (
        "Info density legibility — body text readable at 120px and "
        "1080px, hierarchy clear, whitespace balanced."
    ),
    "IE-4": (
        "Format compliance — exact pixel dimensions, slide count "
        "within bounds, safe-zones respected, text-overlay caps."
    ),
    "IE-5": (
        "Visual specificity — one concrete topic-specific subject, "
        "no generic AI register, anti-patterns YAML hits cap at 4."
    ),
    "IE-6": (
        "Carousel arc — cover stops scroll, PSR/hook-stakes-value "
        "structure, payoff in slide N-1, explicit CTA last slide."
    ),
    "IE-7": (
        "Alt-text + caption voice — alt-text ≤120 chars describes "
        "KEY information, caption matches assigned persona's voice."
    ),
    "IE-8": (
        "Repurposability — composition reusable across ≥2 formats "
        "with minor crop/text-resize."
    ),
}


# Per-format pixel dimensions (TD-41 + plan §per-format visual conventions).
_FORMAT_DIMENSIONS: dict[str, tuple[int, int]] = {
    "ig_single": (1080, 1080),
    "ig_carousel": (1080, 1080),      # per-slide
    "ig_story": (1080, 1920),
    "li_doc_carousel": (1080, 1080),  # per-slide; 1080x1350 portrait also valid
    "hero_banner": (1600, 900),
    "ad_static": (1080, 1080),         # default; platform-specific overrides
}

# Carousel slide-count bounds per TD-41.
_CAROUSEL_SLIDE_COUNT_BOUNDS: dict[str, tuple[int, int]] = {
    "ig_carousel": (5, 10),
    "li_doc_carousel": (8, 12),
}

# Required frontmatter keys (image_engine drafts carry a YAML sidecar or
# inline frontmatter in a meta.json file for carousels).
_REQUIRED_FRONTMATTER_KEYS: tuple[str, ...] = (
    "draft_id", "topic", "format", "voice_persona", "brand_tokens_path",
)


def _read_image_dimensions(image_path: Path) -> tuple[int, int] | None:
    """Read PNG/JPG dimensions via Pillow. Returns None on read failure."""
    try:
        from PIL import Image  # type: ignore[import-untyped]
    except ImportError:
        return None
    try:
        with Image.open(image_path) as img:
            return (img.width, img.height)
    except Exception:
        return None


def _read_meta(artifact: Path) -> dict | None:
    """Read the image draft's metadata.

    For single-image artifacts (PNG/JPG file): looks for a sibling
    `<draft_id>.meta.json` or a `.meta.yaml` with frontmatter.
    For carousel directories: looks for `meta.json` inside.
    """
    if artifact.is_file():
        meta_json = artifact.with_suffix(".meta.json")
        if meta_json.is_file():
            try:
                return json.loads(meta_json.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return None
        return None
    elif artifact.is_dir():
        meta_path = artifact / "meta.json"
        if meta_path.is_file():
            try:
                return json.loads(meta_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return None
    return None


def _carousel_slides(artifact: Path) -> list[Path]:
    """Return sorted slide paths for a carousel directory."""
    if not artifact.is_dir():
        return []
    return sorted(artifact.glob("slide_*.png"))


def _load_anti_patterns(variant_root: Path) -> list[dict] | None:
    """Load image_engine anti_patterns.yml."""
    path = variant_root / "templates" / "image_engine" / "anti_patterns.yml"
    if not path.is_file():
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return None
    if not isinstance(data, dict):
        return None
    patterns = data.get("patterns")
    return patterns if isinstance(patterns, list) else None


def _find_variant_root(session_dir: Path) -> Path | None:
    try:
        from harness.session_paths import find_variant_root  # type: ignore  # noqa: PLC0415
        return find_variant_root(session_dir)
    except (ValueError, ImportError):
        if len(session_dir.parents) > 2:
            return session_dir.parents[2]
    return None


def structural_gate(_mode: str, artifact: Path, session_dir: Path) -> list[str]:
    """Per-artifact structural gate. For single images, `artifact` is
    the PNG/JPG path. For carousels, `artifact` is the directory
    containing slide_*.png files."""
    failures: list[str] = []
    if not artifact.exists():
        failures.append(f"Artifact not found: {artifact}")
        return failures

    meta = _read_meta(artifact)
    if meta is None:
        failures.append(
            f"No meta.json sidecar for {artifact}. FIX: write metadata to "
            f"<draft_id>.meta.json (single image) or <carousel_dir>/meta.json "
            f"(carousel) with required keys: {list(_REQUIRED_FRONTMATTER_KEYS)}."
        )
        return failures
    missing = [k for k in _REQUIRED_FRONTMATTER_KEYS if k not in meta]
    if missing:
        failures.append(f"meta.json missing required keys: {missing}.")
        return failures

    fmt = meta.get("format")
    if fmt not in _FORMAT_DIMENSIONS:
        failures.append(
            f"format={fmt!r} invalid; must be one of {sorted(_FORMAT_DIMENSIONS)}."
        )
        return failures

    expected_dims = _FORMAT_DIMENSIONS[fmt]

    # Single-image format check
    if artifact.is_file():
        if fmt in _CAROUSEL_SLIDE_COUNT_BOUNDS:
            failures.append(
                f"format={fmt!r} is a carousel format but artifact is a single "
                f"file. Carousel drafts must live in a directory with "
                f"slide_*.png files."
            )
            return failures
        dims = _read_image_dimensions(artifact)
        if dims is None:
            failures.append(f"Could not read image dimensions for {artifact}.")
        else:
            failures.extend(
                _validate_single_dimensions(artifact, fmt, dims, expected_dims),
            )

    # Carousel format check
    elif artifact.is_dir():
        if fmt not in _CAROUSEL_SLIDE_COUNT_BOUNDS:
            failures.append(
                f"format={fmt!r} is a single-image format but artifact is a "
                f"directory. Single-image drafts must be PNG/JPG files."
            )
            return failures
        slides = _carousel_slides(artifact)
        lo, hi = _CAROUSEL_SLIDE_COUNT_BOUNDS[fmt]
        if not (lo <= len(slides) <= hi):
            failures.append(
                f"format={fmt!r} slide count={len(slides)} outside [{lo}, {hi}]. "
                f"Hard structural fail."
            )
            return failures
        for slide_path in slides:
            slide_dims = _read_image_dimensions(slide_path)
            if slide_dims is None:
                failures.append(f"Could not read slide dimensions for {slide_path}.")
            elif slide_dims != expected_dims:
                # Allow li_doc_carousel 1080x1350 portrait variant
                if fmt == "li_doc_carousel" and slide_dims == (1080, 1350):
                    continue
                failures.append(
                    f"Slide {slide_path.name} dimensions={slide_dims} do not "
                    f"match {fmt} expected={expected_dims}."
                )

    # Anti-patterns deterministic load (vision_judge will report observed
    # failure_modes; this is the pre-check for substrate-banned patterns).
    variant_root = _find_variant_root(session_dir)
    if variant_root is not None:
        anti_patterns = _load_anti_patterns(variant_root)
        if anti_patterns is None:
            failures.append(
                "Could not load templates/image_engine/anti_patterns.yml. "
                "vision_judge cannot run failure-mode detection without it."
            )

    return failures


def _validate_single_dimensions(
    artifact: Path, fmt: str, dims: tuple[int, int],
    expected_dims: tuple[int, int],
) -> list[str]:
    """Single-image format dimension check. ad_static accepts the
    default 1080x1080 but operators MAY use platform-specific
    dimensions; we soft-warn rather than fail for ad_static."""
    if dims == expected_dims:
        return []
    if fmt == "ad_static":
        # Accept any reasonable ad dimensions; format compliance is
        # judged qualitatively in IE-4.
        return []
    return [
        f"Image {artifact.name} dimensions={dims} do not match {fmt} "
        f"expected={expected_dims}.",
    ]


def load_source_data(_mode: str, artifact: Path, session_dir: Path) -> str:
    """Concatenate topic + voice substrate + brand tokens for the
    judge."""
    parts: list[str] = []

    topic = os.environ.get("IMAGE_ENGINE_TOPIC", "").strip()
    if topic:
        parts.append(f"## Topic\n{topic}")

    # Voice substrate (compiled by configure_env to current_runtime).
    variant_root = _find_variant_root(session_dir)
    if variant_root is not None:
        voice_path = variant_root / "programs" / "references" / "voice.md"
        if voice_path.is_file():
            try:
                parts.append(
                    f"## Voice substrate\n"
                    f"{voice_path.read_text(encoding='utf-8', errors='replace')[:4000]}"
                )
            except OSError:
                pass

    # Brand tokens — operator-curated JSON (palette + typography).
    brand_path = os.environ.get("IMAGE_ENGINE_BRAND_TOKENS_PATH", "").strip()
    if brand_path:
        try:
            tokens_text = Path(brand_path).read_text(encoding="utf-8")
            parts.append(f"## Brand tokens\n```json\n{tokens_text[:2000]}\n```")
        except OSError:
            pass

    return "\n\n".join(parts)


# Structural gate functions for LaneSpec.structural_gate_functions
# (each delegates to the per-aspect filter on structural_gate output).

def frontmatter_yaml_required_fields(artifact: Path, session_dir: Path) -> list[str]:
    return [f for f in structural_gate("full", artifact, session_dir)
            if "meta.json" in f]


def format_valid(artifact: Path, session_dir: Path) -> list[str]:
    return [f for f in structural_gate("full", artifact, session_dir)
            if "format=" in f]


def image_dimensions_match_format(artifact: Path, session_dir: Path) -> list[str]:
    return [f for f in structural_gate("full", artifact, session_dir)
            if "dimensions" in f]


def carousel_slide_count_valid(artifact: Path, session_dir: Path) -> list[str]:
    return [f for f in structural_gate("full", artifact, session_dir)
            if "slide count" in f.lower()]


def brand_wordmark_pillow_composited(artifact: Path, session_dir: Path) -> list[str]:
    # The Pillow-composite check is performed by vision_judge (IE-2 logo_treatment
    # dimension); the structural gate routes the rubric to the judge.
    return []


def ad_text_overlay_within_cap(artifact: Path, session_dir: Path) -> list[str]:
    # Pixel-area text-overlay check is vision_judge's IE-3/IE-4 territory.
    return []


def hero_contrast_wcag_compliant(artifact: Path, session_dir: Path) -> list[str]:
    # WCAG 2.2 contrast check fires in vision_judge IE-3.
    return []


def anti_patterns_within_threshold(artifact: Path, session_dir: Path) -> list[str]:
    return [f for f in structural_gate("full", artifact, session_dir)
            if "anti_patterns" in f.lower()]


SPEC = SessionEvalSpec(
    domain="image_engine",
    domain_name="Image Engine",
    criteria=CRITERIA,
    structural_gate=structural_gate,
    load_source_data=load_source_data,
    cross_item_criteria={
        # IE-6 carousel arc: cross-item over carousel slides.
        # session_eval_common evaluates the cross-item criterion against
        # the glob; the carousel rollup is performed in vision_judge.
        "IE-6": CrossItemCriterion(
            glob="drafts/*/slide_*.png",
            max_items=12,         # max li_doc_carousel slide count
            words_per_item=0,     # images, not text
        ),
    },
)
