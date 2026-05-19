"""Static-image composition (U6) — Pillow-based.

Consumed by image_engine (U14) and ad_engine (U15) for ad statics. Per
TD-41 the bulk of image generation is fal.ai (generative); this module
handles the deterministic compositing layer on top: brand stamps,
text overlays, carousel slide-to-slide brand-anchor passthrough, and
LinkedIn document carousel info-density layout.

Per D13: Pillow by default. Multi-slide carousels are sequential
(brand-anchor metadata passes slide-to-slide) so brand consistency
holds across the set without parallel-render race conditions.

Per Pass-5 simplification: no separate BrandStamp / CarouselSlide /
DocSlide dataclasses — slide content is passed as a plain dict
keyed by `text_overlay`, `prompt_image_path`, `brand_anchor`. If shape
complexity grows post-launch, promote to dataclasses in v1.5.

Format dimensions (locked at the module level so all callers agree):

    ig_single        1080×1080  (1:1 IG feed)
    ig_carousel      1080×1080  (1:1 multi-slide)
    ig_story         1080×1920  (9:16 vertical)
    li_doc_carousel  1080×1080  (1:1 LinkedIn doc)
    hero_banner      configurable per call (default 1600×900)
    ad_static        per-platform spec (default 1200×628 for Meta)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# Per the 4-agent review (adv-7): cap Pillow's decompression-bomb
# tolerance to 50 MP. ig_story (1080×1920) is ~2 MP, hero_banner
# (1600×900) is ~1.4 MP; 50 MP gives ~25× headroom and rejects the
# 30000×30000 PNGs that would OOM-kill an evolution worker.
Image.MAX_IMAGE_PIXELS = 50_000_000


# ---------------------------------------------------------------------------
# Per-format dimension table (single source of truth — callers cite this
# rather than inlining numbers)
# ---------------------------------------------------------------------------

FORMAT_DIMENSIONS: dict[str, tuple[int, int]] = {
    "ig_single":       (1080, 1080),
    "ig_carousel":     (1080, 1080),
    "ig_story":        (1080, 1920),
    "li_doc_carousel": (1080, 1080),
    "hero_banner":     (1600, 900),
    "ad_static":       (1200, 628),
}


# ---------------------------------------------------------------------------
# Brand stamp — extracted as a helper so all four composition functions
# share the same overlay behavior
# ---------------------------------------------------------------------------


def _resolve_logo(brand: dict[str, Any]) -> Path | None:
    """Resolve the optional logo path; return None when absent or missing."""
    raw = brand.get("logo")
    if not raw:
        return None
    p = Path(raw)
    return p if p.is_file() else None


def _load_font(brand: dict[str, Any], size: int) -> ImageFont.ImageFont:
    """Resolve a TTF/OTF font from brand if present, falling back to
    Pillow's bundled default so the composer never crashes on a missing
    font file (matches the brand_strictness 'permissive' fallback behavior
    from ClientConfig U2)."""
    font_path = brand.get("font")
    if font_path:
        path = Path(font_path)
        if path.is_file():
            try:
                return ImageFont.truetype(str(path), size=size)
            except OSError:
                logger.warning("falling back to default font; truetype load failed: %s", path)
    return ImageFont.load_default()


def _apply_brand_stamp(
    img: Image.Image, brand: dict[str, Any], *, anchor: str | None = None,
) -> None:
    """Composite the brand stamp (logo + optional accent stripe) onto `img`.

    `anchor` selects the corner. When None, falls back to
    `brand.get('logo_anchor')` so callers (compose_carousel) can pass
    the anchor through the brand dict on a slide-by-slide basis per D13.
    Default is bottom-right when neither is set.

    Per the 4-agent review (M1 T1-C): the previous default `anchor='bottom-
    right'` parameter shadowed the brand dict's value, so carousel anchor
    passthrough was dead code. Fixed by making the parameter default to
    None and reading from brand on miss.

    The function mutates `img` in place; no return value because Pillow
    composite operations are in-place. Brand spec missing a logo falls
    back to a text-only stamp using the brand's `name` (when set),
    matching the brand_strictness=permissive behavior contract.
    """
    if anchor is None:
        anchor = brand.get("logo_anchor", "bottom-right")
    width, height = img.size
    logo_path = _resolve_logo(brand)
    pad = max(width, height) // 40  # ~2.5% padding from edges

    if logo_path is not None:
        logo = Image.open(logo_path).convert("RGBA")
        # Scale logo to ~6% of the longer dimension; brand_tokens may
        # override via brand['logo_scale']
        scale = float(brand.get("logo_scale", 0.06))
        target_h = max(int(min(width, height) * scale), 24)
        ratio = target_h / logo.height
        target_w = int(logo.width * ratio)
        logo = logo.resize((target_w, target_h), Image.LANCZOS)
        if anchor == "bottom-right":
            pos = (width - target_w - pad, height - target_h - pad)
        elif anchor == "top-right":
            pos = (width - target_w - pad, pad)
        elif anchor == "top-left":
            pos = (pad, pad)
        else:
            pos = (pad, height - target_h - pad)
        img.paste(logo, pos, logo)
    elif brand.get("name"):
        # Text-only stamp fallback (brand_strictness=permissive).
        draw = ImageDraw.Draw(img)
        font = _load_font(brand, size=max(16, width // 40))
        text = str(brand["name"])
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        pos = (width - text_w - pad, height - text_h - pad)
        draw.text(pos, text, fill=brand.get("text_color", "#FFFFFF"), font=font)


def _apply_text_overlay(
    img: Image.Image,
    text: str,
    brand: dict[str, Any],
    *,
    region: str = "lower",
    max_chars_per_line: int | None = None,
) -> None:
    """Render `text` over `img` in a horizontal band.

    `region` is "upper" / "middle" / "lower". `max_chars_per_line` is
    derived from the image width when not provided. Auto-wraps long
    lines; truncates if total wrapped text exceeds the band's safe area.
    Mutates `img` in place.
    """
    if not text:
        return
    width, height = img.size
    draw = ImageDraw.Draw(img)
    font_size = max(28, width // 28)
    font = _load_font(brand, size=font_size)

    if max_chars_per_line is None:
        # Rough heuristic from image width + font glyph width.
        max_chars_per_line = max(20, width // (font_size // 2 + 2))

    # Word-wrap.
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = (current + " " + word).strip()
        if len(candidate) <= max_chars_per_line:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    # Position by region.
    line_height = int(font_size * 1.25)
    total_text_h = line_height * len(lines)
    if region == "upper":
        start_y = height // 8
    elif region == "middle":
        start_y = (height - total_text_h) // 2
    else:
        start_y = height - total_text_h - height // 8

    text_color = brand.get("text_color", "#FFFFFF")
    shadow_color = brand.get("text_shadow", "#000000")
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        x = (width - line_w) // 2
        y = start_y + i * line_height
        # Drop shadow for legibility on photo backgrounds.
        draw.text((x + 2, y + 2), line, fill=shadow_color, font=font)
        draw.text((x, y), line, fill=text_color, font=font)


def _resize_to_format(img: Image.Image, format_key: str) -> Image.Image:
    """Resize `img` to the format's canonical dimensions (cover-crop, no
    aspect-ratio distortion)."""
    target = FORMAT_DIMENSIONS[format_key]
    target_w, target_h = target
    src_w, src_h = img.size
    src_ratio = src_w / src_h
    tgt_ratio = target_w / target_h
    if src_ratio > tgt_ratio:
        # Source wider; crop sides
        new_w = int(src_h * tgt_ratio)
        offset = (src_w - new_w) // 2
        img = img.crop((offset, 0, offset + new_w, src_h))
    elif src_ratio < tgt_ratio:
        # Source taller; crop top/bottom
        new_h = int(src_w / tgt_ratio)
        offset = (src_h - new_h) // 2
        img = img.crop((0, offset, src_w, offset + new_h))
    return img.resize(target, Image.LANCZOS)


# ---------------------------------------------------------------------------
# Composition entry points (the four shapes referenced by U14 + U15)
# ---------------------------------------------------------------------------


def compose_single(
    prompt_image_path: Path,
    text_overlay: str | None,
    brand: dict[str, Any],
    output_path: Path,
    *,
    format_key: str = "ig_single",
) -> Path:
    """Compose a single image with optional text overlay + brand stamp.

    Args:
        prompt_image_path: source image from fal.ai (or any image file).
        text_overlay: optional headline. None / "" → no overlay box.
        brand: brand dict (logo path, font path, palette colors).
        output_path: where to write the composed PNG.
        format_key: one of FORMAT_DIMENSIONS keys (default ig_single 1080×1080).
    """
    if not prompt_image_path.is_file():
        raise FileNotFoundError(
            f"compose_single: source image not found at {prompt_image_path}"
        )
    img = Image.open(prompt_image_path).convert("RGB")
    img = _resize_to_format(img, format_key)
    if text_overlay:
        _apply_text_overlay(img, text_overlay, brand)
    _apply_brand_stamp(img, brand)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG")
    return output_path


def compose_carousel(
    slides: list[dict[str, Any]],
    brand: dict[str, Any],
    output_dir: Path,
    *,
    format_key: str = "ig_carousel",
) -> list[Path]:
    """Compose a multi-slide carousel.

    Each slide is a dict with keys `prompt_image_path` (Path), `text_overlay`
    (str | None), and optional `brand_anchor` (any — passed slide-to-slide
    so consumers can ensure visual continuity, e.g., recurring colour
    block position).

    Per D13: sequential — slide N receives slide (N-1)'s `brand_anchor`
    from the previous output's metadata so brand consistency holds
    deterministically. Returned list is in slide order.
    """
    if not slides:
        raise ValueError("compose_carousel: slides list is empty")

    output_dir.mkdir(parents=True, exist_ok=True)
    composed: list[Path] = []
    prev_anchor: Any = None
    for i, slide in enumerate(slides):
        if "prompt_image_path" not in slide:
            raise ValueError(
                f"compose_carousel: slide {i} missing prompt_image_path"
            )
        # Slide-to-slide anchor passthrough: the *slide* may declare its own
        # anchor; otherwise we inherit the previous slide's anchor so brand
        # stamp position is consistent down the set.
        anchor = slide.get("brand_anchor", prev_anchor) or "bottom-right"
        merged_brand = {**brand, "logo_anchor": anchor}
        out_path = output_dir / f"slide-{i + 1:02d}.png"
        compose_single(
            prompt_image_path=Path(slide["prompt_image_path"]),
            text_overlay=slide.get("text_overlay"),
            brand=merged_brand,
            output_path=out_path,
            format_key=format_key,
        )
        composed.append(out_path)
        prev_anchor = anchor
    return composed


def compose_doc_carousel(
    slides: list[dict[str, Any]],
    brand: dict[str, Any],
    output_dir: Path,
) -> list[Path]:
    """Compose a LinkedIn document carousel (1:1, info-density layout).

    Document carousels lean on more text per slide than IG carousels;
    this function uses a tighter wrap + larger body region. Mirrors
    compose_carousel shape so consumers can swap formats with one
    argument change.
    """
    if not slides:
        raise ValueError("compose_doc_carousel: slides list is empty")

    output_dir.mkdir(parents=True, exist_ok=True)
    composed: list[Path] = []
    for i, slide in enumerate(slides):
        if "prompt_image_path" not in slide:
            raise ValueError(
                f"compose_doc_carousel: slide {i} missing prompt_image_path"
            )
        img = Image.open(Path(slide["prompt_image_path"])).convert("RGB")
        img = _resize_to_format(img, "li_doc_carousel")
        text = slide.get("text_overlay")
        if text:
            # LI document carousels tolerate more text — wrap at 32 chars/line
            # in the middle region.
            _apply_text_overlay(
                img, text, brand, region="middle", max_chars_per_line=32,
            )
        _apply_brand_stamp(img, brand, anchor="top-left")
        out_path = output_dir / f"doc-slide-{i + 1:02d}.png"
        img.save(out_path, "PNG")
        composed.append(out_path)
    return composed


def compose_hero(
    prompt_image_path: Path,
    brand: dict[str, Any],
    output_path: Path,
    *,
    dimensions: tuple[int, int] | None = None,
    headline: str | None = None,
) -> Path:
    """Compose a hero banner.

    `dimensions` overrides FORMAT_DIMENSIONS['hero_banner'] when set
    (lets U15b site_engine produce banners sized to the client's
    target page).
    """
    if not prompt_image_path.is_file():
        raise FileNotFoundError(
            f"compose_hero: source image not found at {prompt_image_path}"
        )
    img = Image.open(prompt_image_path).convert("RGB")
    if dimensions is not None:
        target_w, target_h = dimensions
        # Inline cover-crop logic (mirrors _resize_to_format but with
        # caller-provided dims).
        src_w, src_h = img.size
        src_ratio = src_w / src_h
        tgt_ratio = target_w / target_h
        if src_ratio > tgt_ratio:
            new_w = int(src_h * tgt_ratio)
            offset = (src_w - new_w) // 2
            img = img.crop((offset, 0, offset + new_w, src_h))
        elif src_ratio < tgt_ratio:
            new_h = int(src_w / tgt_ratio)
            offset = (src_h - new_h) // 2
            img = img.crop((0, offset, src_w, offset + new_h))
        img = img.resize((target_w, target_h), Image.LANCZOS)
    else:
        img = _resize_to_format(img, "hero_banner")

    if headline:
        _apply_text_overlay(img, headline, brand, region="middle")
    _apply_brand_stamp(img, brand, anchor="top-left")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG")
    return output_path


__all__ = [
    "FORMAT_DIMENSIONS",
    "compose_single",
    "compose_carousel",
    "compose_doc_carousel",
    "compose_hero",
]
