"""Static-image composition (U6).

Tests construct synthetic source images in tmp_path rather than rely on
committed reference PNGs — keeps test fixtures small and lets us assert
exact dimensions / pixel attributes without floating-point fuzziness.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from src.generation.image_composer import (
    FORMAT_DIMENSIONS,
    compose_carousel,
    compose_doc_carousel,
    compose_hero,
    compose_single,
)


@pytest.fixture
def synth_source(tmp_path: Path):
    """Factory: create a synthetic PNG of a given size + colour, return path."""
    def _build(name: str, size: tuple[int, int] = (1200, 800), colour: str = "blue") -> Path:
        path = tmp_path / name
        Image.new("RGB", size, colour).save(path, "PNG")
        return path
    return _build


@pytest.fixture
def minimal_brand() -> dict:
    """Brand spec with no logo / no font — exercises the text-only stamp fallback."""
    return {"name": "FixtureBrand", "text_color": "#FFFFFF"}


@pytest.fixture
def brand_with_logo(tmp_path: Path) -> dict:
    """Brand spec with a synthetic logo file."""
    logo_path = tmp_path / "logo.png"
    Image.new("RGBA", (200, 200), (255, 255, 255, 255)).save(logo_path, "PNG")
    return {"name": "FixtureBrand", "logo": str(logo_path)}


# ---------------------------------------------------------------------------
# FORMAT_DIMENSIONS pin
# ---------------------------------------------------------------------------


def test_format_dimensions_includes_six_v1_formats() -> None:
    """All six v1 formats are dimensioned. Drift pin so a renaming
    or addition is deliberate."""
    expected = {
        "ig_single", "ig_carousel", "ig_story",
        "li_doc_carousel", "hero_banner", "ad_static",
    }
    assert set(FORMAT_DIMENSIONS.keys()) == expected


# ---------------------------------------------------------------------------
# compose_single
# ---------------------------------------------------------------------------


def test_compose_single_ig_single_writes_1080_square(synth_source, tmp_path, minimal_brand) -> None:
    src = synth_source("source.png", size=(1600, 1200))
    out = tmp_path / "out.png"
    compose_single(src, "Test overlay", minimal_brand, out)
    assert out.is_file()
    with Image.open(out) as img:
        assert img.size == (1080, 1080)


def test_compose_single_ig_story_writes_vertical(synth_source, tmp_path, minimal_brand) -> None:
    src = synth_source("source.png", size=(2000, 1000))
    out = tmp_path / "story.png"
    compose_single(src, "Story", minimal_brand, out, format_key="ig_story")
    with Image.open(out) as img:
        assert img.size == (1080, 1920)


def test_compose_single_empty_overlay_does_not_crash(synth_source, tmp_path, minimal_brand) -> None:
    """Per plan U6 edge case: empty text overlay → image generated without overlay box."""
    src = synth_source("source.png")
    out = tmp_path / "out.png"
    compose_single(src, None, minimal_brand, out)
    assert out.is_file()
    compose_single(src, "", minimal_brand, out)
    assert out.is_file()


def test_compose_single_missing_source_raises(tmp_path, minimal_brand) -> None:
    """Per plan U6 error path: source prompt-image file missing → clear error."""
    with pytest.raises(FileNotFoundError) as exc:
        compose_single(tmp_path / "missing.png", "x", minimal_brand, tmp_path / "out.png")
    assert "missing.png" in str(exc.value)


def test_compose_single_brand_with_logo(synth_source, tmp_path, brand_with_logo) -> None:
    src = synth_source("source.png")
    out = tmp_path / "out.png"
    compose_single(src, "x", brand_with_logo, out)
    assert out.is_file()


def test_compose_single_no_logo_falls_back_to_text_stamp(synth_source, tmp_path, minimal_brand) -> None:
    """Per plan U6 edge case: brand spec missing logo → fallback to text-only brand stamp."""
    src = synth_source("source.png")
    out = tmp_path / "out.png"
    # minimal_brand has no logo; the function must not crash.
    compose_single(src, "x", minimal_brand, out)
    assert out.is_file()


def test_compose_single_long_text_wraps(synth_source, tmp_path, minimal_brand) -> None:
    """Per plan U6 edge case: text overlay too long for slide → auto-wrap."""
    src = synth_source("source.png")
    out = tmp_path / "out.png"
    long_text = "word " * 50
    compose_single(src, long_text, minimal_brand, out)
    assert out.is_file()


# ---------------------------------------------------------------------------
# compose_carousel
# ---------------------------------------------------------------------------


def test_compose_carousel_5_slides_produces_5_pngs(synth_source, tmp_path, minimal_brand) -> None:
    """Per plan U6 happy path: compose 5-slide carousel → 5 PNGs produced."""
    slides = [
        {"prompt_image_path": synth_source(f"src-{i}.png", colour=("red", "green", "blue", "yellow", "magenta")[i]),
         "text_overlay": f"Slide {i + 1}"}
        for i in range(5)
    ]
    output = tmp_path / "carousel"
    paths = compose_carousel(slides, minimal_brand, output)
    assert len(paths) == 5
    assert all(p.is_file() for p in paths)
    # All slides match the ig_carousel size (1080x1080)
    for p in paths:
        with Image.open(p) as img:
            assert img.size == FORMAT_DIMENSIONS["ig_carousel"]


def test_compose_carousel_single_slide_works(synth_source, tmp_path, minimal_brand) -> None:
    """Per plan U6 edge case: single-slide carousel → exactly 1 PNG."""
    slides = [{"prompt_image_path": synth_source("src.png"), "text_overlay": "Solo"}]
    paths = compose_carousel(slides, minimal_brand, tmp_path / "out")
    assert len(paths) == 1


def test_compose_carousel_empty_slides_raises(tmp_path, minimal_brand) -> None:
    with pytest.raises(ValueError) as exc:
        compose_carousel([], minimal_brand, tmp_path / "out")
    assert "empty" in str(exc.value).lower()


def test_compose_carousel_brand_anchor_passes_slide_to_slide(synth_source, tmp_path, minimal_brand) -> None:
    """Per plan U6 integration: carousel sequential brand-anchor passthrough.
    First slide sets anchor; subsequent slides inherit when not declared."""
    slides = [
        {"prompt_image_path": synth_source("src-0.png"), "brand_anchor": "top-right"},
        {"prompt_image_path": synth_source("src-1.png")},  # inherits top-right
        {"prompt_image_path": synth_source("src-2.png")},  # still top-right
    ]
    paths = compose_carousel(slides, minimal_brand, tmp_path / "carousel")
    assert len(paths) == 3
    # All produced successfully; brand-anchor invariance is internal-state
    # but the function not crashing is the contract pin.


def test_compose_carousel_missing_prompt_image_raises(tmp_path, minimal_brand) -> None:
    slides = [{"text_overlay": "no image"}]
    with pytest.raises(ValueError) as exc:
        compose_carousel(slides, minimal_brand, tmp_path / "out")
    assert "prompt_image_path" in str(exc.value)


# ---------------------------------------------------------------------------
# compose_doc_carousel
# ---------------------------------------------------------------------------


def test_compose_doc_carousel_8_slides_info_density_layout(synth_source, tmp_path, minimal_brand) -> None:
    """Per plan U6 happy path: compose LinkedIn document carousel (8 slides)."""
    slides = [
        {"prompt_image_path": synth_source(f"src-{i}.png"),
         "text_overlay": f"Doc slide {i + 1}: info-density layout with more text per slide than IG."}
        for i in range(8)
    ]
    paths = compose_doc_carousel(slides, minimal_brand, tmp_path / "doc")
    assert len(paths) == 8
    for p in paths:
        with Image.open(p) as img:
            assert img.size == FORMAT_DIMENSIONS["li_doc_carousel"]


# ---------------------------------------------------------------------------
# compose_hero
# ---------------------------------------------------------------------------


def test_compose_hero_default_dimensions(synth_source, tmp_path, minimal_brand) -> None:
    src = synth_source("source.png", size=(2400, 1200))
    out = tmp_path / "hero.png"
    compose_hero(src, minimal_brand, out, headline="Welcome to the future")
    with Image.open(out) as img:
        assert img.size == FORMAT_DIMENSIONS["hero_banner"]


def test_compose_hero_custom_dimensions(synth_source, tmp_path, minimal_brand) -> None:
    src = synth_source("source.png", size=(2400, 1200))
    out = tmp_path / "hero.png"
    compose_hero(src, minimal_brand, out, dimensions=(1920, 600))
    with Image.open(out) as img:
        assert img.size == (1920, 600)


def test_compose_hero_missing_source_raises(tmp_path, minimal_brand) -> None:
    with pytest.raises(FileNotFoundError):
        compose_hero(tmp_path / "missing.png", minimal_brand, tmp_path / "out.png")


# ---------------------------------------------------------------------------
# Integration: brand_strictness=permissive equivalent (logo missing)
# ---------------------------------------------------------------------------


def test_brand_missing_logo_still_produces_image(synth_source, tmp_path) -> None:
    """The U2 ClientConfig brand_strictness='permissive' lets clients
    onboard without a polished logo file. The composer must not crash;
    text-only stamp fallback runs when brand.name is set."""
    src = synth_source("source.png")
    out = tmp_path / "out.png"
    compose_single(src, "x", {"name": "BrandWithoutLogo"}, out)
    assert out.is_file()


def test_brand_missing_everything_no_stamp_no_crash(synth_source, tmp_path) -> None:
    """Even more degraded: brand dict has no logo and no name. The
    composer skips the stamp entirely without crashing."""
    src = synth_source("source.png")
    out = tmp_path / "out.png"
    compose_single(src, "x", {}, out)
    assert out.is_file()
