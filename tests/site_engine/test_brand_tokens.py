"""U18 brand_tokens.json schema + loader tests.

Per plan §U18 verification + Threat Model brand_tokens-swap mitigation:
the tokens.json schema is the defense against a maliciously-swapped
brand-tokens file injecting external URLs into typeface specs,
tracking pixels into palette tokens, or extreme values that crash
section layout.

Tests pin INTENT (the attack surface each rule defends) so a regression
that silently relaxes a check fails a test that documents the WHY.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.site_engine.brand_tokens import (
    BrandTokens,
    BrandTokensNotFoundError,
    ColorPalette,
    Typeface,
    Typography,
    load_brand_tokens,
)


# ---------------------------------------------------------------------------
# Color palette — hex codes only
# ---------------------------------------------------------------------------


def test_palette_accepts_short_hex() -> None:
    p = ColorPalette(primary="#FFF")
    assert p.primary == "#FFF"


def test_palette_accepts_long_hex() -> None:
    p = ColorPalette(primary="#a1b2c3")
    assert p.primary == "#a1b2c3"


def test_palette_accepts_hex_with_alpha() -> None:
    p = ColorPalette(primary="#a1b2c3ff")
    assert p.primary == "#a1b2c3ff"


def test_palette_rejects_named_color() -> None:
    """Pin: CSS named colors ('red', 'blue', 'transparent') would let
    an attacker write `transparent` to hide watermarks or `red` to
    flag-burn. Hex-only forces explicit specification."""
    with pytest.raises(ValidationError):
        ColorPalette(primary="red")


def test_palette_rejects_url_smuggling() -> None:
    """Pin: `url('http://attacker/pixel.png')` would inject a tracking
    pixel via CSS variable. Hex-regex blocks the surface."""
    with pytest.raises(ValidationError) as exc:
        ColorPalette(primary="url(http://evil.example/track.png)")
    assert "hex code" in str(exc.value).lower()


def test_palette_rejects_gradient() -> None:
    """Pin: `linear-gradient(...)` would allow image-data smuggling
    via gradient stops in some CSS engines."""
    with pytest.raises(ValidationError):
        ColorPalette(primary="linear-gradient(red, blue)")


def test_palette_rejects_var_reference() -> None:
    """Pin: `var(--evil)` would reference a CSS variable defined
    elsewhere (potentially malicious DOM-supplied value)."""
    with pytest.raises(ValidationError):
        ColorPalette(primary="var(--secret)")


def test_palette_rejects_javascript_protocol() -> None:
    with pytest.raises(ValidationError):
        ColorPalette(primary="javascript:alert(1)")


def test_palette_allows_optional_tokens_none() -> None:
    """Pin: only `primary` is required; other tokens default None."""
    p = ColorPalette(primary="#000000")
    assert p.secondary is None
    assert p.accent is None


# ---------------------------------------------------------------------------
# Typeface — no smuggled URLs / scripts
# ---------------------------------------------------------------------------


def test_typeface_accepts_plain_family() -> None:
    t = Typeface(family="Inter")
    assert t.family == "Inter"


def test_typeface_accepts_quoted_family_with_spaces() -> None:
    t = Typeface(family="Helvetica Neue")
    assert t.family == "Helvetica Neue"


def test_typeface_rejects_url_smuggling() -> None:
    """Pin: an @font-face src `url(...)` smuggled into family name
    would let an attacker host the font on a tracking origin."""
    with pytest.raises(ValidationError) as exc:
        Typeface(family="Inter, url(http://attacker.example/font.woff2)")
    assert "url(" in str(exc.value).lower()


def test_typeface_rejects_at_import() -> None:
    """Pin: CSS `@import` would let an attacker pull a remote
    stylesheet through the brand-tokens vector."""
    with pytest.raises(ValidationError):
        Typeface(family="@import url(evil.css)")


def test_typeface_rejects_javascript_protocol() -> None:
    with pytest.raises(ValidationError):
        Typeface(family="javascript:alert(1)")


def test_typeface_rejects_data_uri() -> None:
    """Pin: data: URIs would let an attacker embed an inline font
    binary, defeating the same-origin font-hosting requirement."""
    with pytest.raises(ValidationError):
        Typeface(family="Inter, data:font/woff2;base64,AAAA")


def test_typeface_rejects_html_tag_smuggling() -> None:
    """Pin: HTML tag chars in a family name suggest injection,
    not a real font."""
    with pytest.raises(ValidationError):
        Typeface(family="</style><script>alert(1)</script>")


def test_typeface_rejects_oversized_family() -> None:
    """Pin: family names beyond 256 chars are injection-shaped, not
    real fonts. Real font names are <50 chars."""
    with pytest.raises(ValidationError) as exc:
        Typeface(family="X" * 500)
    assert "256" in str(exc.value) or "cap" in str(exc.value).lower()


def test_typeface_accepts_int_weight() -> None:
    t = Typeface(family="Inter", weight=400)
    assert t.weight == 400


def test_typeface_accepts_string_weight() -> None:
    t = Typeface(family="Inter", weight="bold")
    assert t.weight == "bold"


def test_typeface_rejects_out_of_range_weight() -> None:
    with pytest.raises(ValidationError):
        Typeface(family="Inter", weight=1500)


def test_typeface_rejects_unknown_string_weight() -> None:
    with pytest.raises(ValidationError):
        Typeface(family="Inter", weight="extrabold")


# ---------------------------------------------------------------------------
# Spacing / motion bounds
# ---------------------------------------------------------------------------


def test_spacing_bounds_reject_giant_value() -> None:
    """Pin: 10000px would break section layout. Capped at 256."""
    with pytest.raises(ValidationError):
        BrandTokens.model_validate({
            "palette": {"primary": "#000000"},
            "typography": {"body": {"family": "Inter"}},
            "spacing": {"xs": 10000},
        })


def test_motion_bounds_reject_giant_duration() -> None:
    """Pin: 60000ms (60s) transition is jank, not animation. Capped
    at 5000ms."""
    with pytest.raises(ValidationError):
        BrandTokens.model_validate({
            "palette": {"primary": "#000000"},
            "typography": {"body": {"family": "Inter"}},
            "motion": {"duration_fast_ms": 60000},
        })


def test_motion_bounds_reject_negative_duration() -> None:
    with pytest.raises(ValidationError):
        BrandTokens.model_validate({
            "palette": {"primary": "#000000"},
            "typography": {"body": {"family": "Inter"}},
            "motion": {"duration_slow_ms": -100},
        })


# ---------------------------------------------------------------------------
# Full BrandTokens model
# ---------------------------------------------------------------------------


def test_minimal_brand_tokens_construct() -> None:
    bt = BrandTokens.model_validate({
        "palette": {"primary": "#000000"},
        "typography": {"body": {"family": "Inter"}},
    })
    assert bt.palette.primary == "#000000"
    assert bt.typography.body.family == "Inter"
    # Defaults fill in spacing + motion
    assert bt.spacing.md == 16
    assert bt.motion.duration_normal_ms == 300


def test_brand_tokens_frozen() -> None:
    bt = BrandTokens.model_validate({
        "palette": {"primary": "#000000"},
        "typography": {"body": {"family": "Inter"}},
    })
    with pytest.raises(ValidationError):
        bt.palette = ColorPalette(primary="#FFFFFF")  # type: ignore[misc]


def test_brand_tokens_allows_experimental_extras() -> None:
    """Per `extra='allow'`: operators can carry experimental tokens
    that the bounded fields haven't formalized yet — but they cannot
    relax the bounded validators."""
    bt = BrandTokens.model_validate({
        "palette": {"primary": "#000000"},
        "typography": {"body": {"family": "Inter"}},
        "experimental_radius": 8,
    })
    # Validates without error; experimental field is preserved.
    assert getattr(bt, "experimental_radius") == 8


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


def test_load_brand_tokens_from_valid_file(tmp_path: Path) -> None:
    path = tmp_path / "tokens.json"
    path.write_text(json.dumps({
        "palette": {"primary": "#0066cc"},
        "typography": {"body": {"family": "Inter", "weight": 400}},
    }))
    bt = load_brand_tokens(path)
    assert bt.palette.primary == "#0066cc"
    assert bt.typography.body.weight == 400


def test_load_brand_tokens_raises_on_missing_file(tmp_path: Path) -> None:
    with pytest.raises(BrandTokensNotFoundError) as exc:
        load_brand_tokens(tmp_path / "missing.json")
    assert "U18 launch runbook" in str(exc.value)


def test_load_brand_tokens_raises_on_malformed_json(tmp_path: Path) -> None:
    path = tmp_path / "tokens.json"
    path.write_text("{not valid json")
    with pytest.raises(json.JSONDecodeError):
        load_brand_tokens(path)


def test_load_brand_tokens_raises_on_non_mapping_top_level(tmp_path: Path) -> None:
    path = tmp_path / "tokens.json"
    path.write_text("[1, 2, 3]")
    with pytest.raises(ValueError) as exc:
        load_brand_tokens(path)
    assert "mapping" in str(exc.value)


def test_load_brand_tokens_raises_on_url_smuggling(tmp_path: Path) -> None:
    """End-to-end attack scenario: an operator's brand/tokens.json is
    swapped for a malicious file that smuggles a tracking-pixel URL
    into the primary color token. Loader rejects at validation time."""
    path = tmp_path / "tokens.json"
    path.write_text(json.dumps({
        "palette": {"primary": "url(http://attacker.example/pixel.png)"},
        "typography": {"body": {"family": "Inter"}},
    }))
    with pytest.raises(ValidationError):
        load_brand_tokens(path)
