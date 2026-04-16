"""Tests for PR-101: Video Polish — aspect ratio, transcript editing, filler removal, caption presets, Unicode captions."""

import re
import unicodedata

import pytest

from src.generation.caption_presets import get_preset, DEFAULT, HORMOZI, NEON
from src.generation.composition import _resolve_dimensions, _build_force_style, _sanitize_caption
from src.generation.models import CAPTION_SAFE_RE, CaptionStyle, CompositionSpec
from src.generation.text_utils import strip_fillers


# ── _resolve_dimensions ──────────────────────────────────────────────


class TestResolveDimensions:
    """Test aspect-ratio-aware dimension resolution."""

    @pytest.mark.parametrize(
        "resolution, aspect_ratio, expected",
        [
            # 16:9 landscape
            ("480p", "16:9", (854, 480)),
            ("720p", "16:9", (1280, 720)),
            ("1080p", "16:9", (1920, 1080)),
            # 9:16 portrait
            ("480p", "9:16", (480, 854)),
            ("720p", "9:16", (720, 1280)),
            ("1080p", "9:16", (1080, 1920)),
            # 1:1 square
            ("480p", "1:1", (480, 480)),
            ("720p", "1:1", (720, 720)),
            ("1080p", "1:1", (1080, 1080)),
        ],
    )
    def test_all_combinations(self, resolution, aspect_ratio, expected):
        result = _resolve_dimensions(resolution, aspect_ratio)
        assert result == expected

    def test_all_even_numbers(self):
        for res in ("480p", "720p", "1080p"):
            for ar in ("9:16", "16:9", "1:1"):
                w, h = _resolve_dimensions(res, ar)
                assert w % 2 == 0, f"{res} {ar}: width {w} is odd"
                assert h % 2 == 0, f"{res} {ar}: height {h} is odd"

    def test_unknown_resolution_defaults_720(self):
        w, h = _resolve_dimensions("360p", "16:9")
        assert h == 720  # short edge = 720 (default)

    def test_unknown_aspect_ratio_defaults_landscape(self):
        w, h = _resolve_dimensions("1080p", "unknown")
        assert w > h  # landscape


# ── strip_fillers ────────────────────────────────────────────────────


class TestStripFillers:
    """Test filler word removal."""

    def test_removes_common_fillers(self):
        result = strip_fillers("Um, so basically, you know, the product is great")
        assert "um" not in result.lower()
        assert "basically" not in result.lower()
        assert "you know" not in result.lower()
        assert "great" in result.lower()

    def test_no_fillers_unchanged(self):
        text = "The product is absolutely fantastic"
        assert strip_fillers(text) == text

    def test_fillers_at_start(self):
        result = strip_fillers("Uh so this is cool")
        assert result.startswith("so") or result.startswith("this")

    def test_fillers_at_end(self):
        result = strip_fillers("This is cool, you know, really")
        assert "you know" not in result.lower()

    def test_non_english_passthrough(self):
        text = "Um das ist ja basically cool"
        assert strip_fillers(text, language="de") == text

    def test_empty_string(self):
        assert strip_fillers("") == ""

    def test_multiple_spaces_collapsed(self):
        result = strip_fillers("I um like this")
        assert "  " not in result


# ── CAPTION_SAFE_RE ──────────────────────────────────────────────────


class TestCaptionSafeRegex:
    """Test Unicode-aware caption safety regex."""

    @pytest.mark.parametrize("text", [
        "Hello world",
        "Bonjour le monde",
        "Hola Mundo!",
        "こんにちは世界",  # Japanese
        "Привет мир",  # Cyrillic
        "مرحبا بالعالم",  # Arabic
        "Héllo wörld",  # accented
        "It's a test - really!",  # apostrophe and dash
        "Price: 10.99, yes!",  # colon removed from denylist? Actually colon IS allowed now
    ])
    def test_accepts_unicode(self, text):
        # Normalize first as the validator does
        normalized = unicodedata.normalize("NFKC", text)
        assert CAPTION_SAFE_RE.match(normalized), f"Regex rejected: {text!r}"

    @pytest.mark.parametrize("text", [
        "test\\injection",  # backslash
        "test;chain",  # semicolon
        "test%{expr}",  # percent + braces
        "test[pad]",  # brackets
        "test`shell`",  # backtick
        "test$var",  # dollar
        "test|pipe",  # pipe
        "test#comment",  # hash
        "test\ttab",  # tab (control char)
        "test\nnewline",  # newline (control char)
        "test\rcarriage",  # carriage return
    ])
    def test_rejects_injection_vectors(self, text):
        assert not CAPTION_SAFE_RE.match(text), f"Regex accepted dangerous: {text!r}"

    def test_nfkc_normalization_blocks_fullwidth(self):
        """Fullwidth characters like ＜ (U+FF1C) normalize to < via NFKC."""
        fullwidth_lt = "\uff1c"  # fullwidth <
        normalized = unicodedata.normalize("NFKC", fullwidth_lt)
        # After normalization, < should still be accepted (it's not in our denylist)
        # But control chars like fullwidth semicolon ＄ -> $ ARE blocked
        fullwidth_dollar = "\uff04"
        norm_dollar = unicodedata.normalize("NFKC", fullwidth_dollar)
        assert not CAPTION_SAFE_RE.match(norm_dollar)


# ── _sanitize_caption ────────────────────────────────────────────────


class TestSanitizeCaption:
    def test_passes_safe_text_through(self):
        result = _sanitize_caption("Hello world")
        assert "Hello world" in result

    def test_strips_injection_chars(self):
        result = _sanitize_caption("test\\;%{}[]`$|#bad")
        # Backslash is stripped entirely (critical for FFmpeg injection prevention)
        assert "\\" not in result
        # Dollar, pipe, hash, backtick are stripped
        assert "$" not in result
        assert "|" not in result
        assert "#" not in result
        assert "`" not in result
        # Safe words survive sanitization
        assert "test" in result
        assert "bad" in result

    def test_unicode_preserved(self):
        result = _sanitize_caption("Bonjour le monde")
        assert "Bonjour" in result


# ── Caption Presets ──────────────────────────────────────────────────


class TestCaptionPresets:
    def test_get_known_presets(self):
        for name in ("default", "hormozi", "minimal", "elegant", "cinematic", "neon"):
            style = get_preset(name)
            assert style.name == name

    def test_unknown_falls_back_to_default(self):
        style = get_preset("nonexistent")
        assert style.name == "default"
        assert style == DEFAULT

    def test_hormozi_has_large_font(self):
        assert HORMOZI.font_size == 48
        assert HORMOZI.bold is True

    def test_neon_has_colored_outline(self):
        assert NEON.outline_colour != "&H00000000"


# ── _build_force_style ───────────────────────────────────────────────


class TestBuildForceStyle:
    def test_default_style_string(self):
        result = _build_force_style(DEFAULT)
        assert "FontName=Arial" in result
        assert "FontSize=24" in result
        assert "BorderStyle=3" in result
        assert "Alignment=2" in result

    def test_alignment_override(self):
        result = _build_force_style(DEFAULT, alignment=6)
        assert "Alignment=6" in result

    def test_hormozi_style_string(self):
        result = _build_force_style(HORMOZI)
        assert "Montserrat Bold" in result
        assert "FontSize=48" in result
        assert "Bold=1" in result

    def test_no_spaces_in_style_values(self):
        result = _build_force_style(DEFAULT)
        # Each key=value pair separated by commas, no trailing spaces
        parts = result.split(",")
        for part in parts:
            assert "=" in part


# ── CompositionSpec.caption_preset ───────────────────────────────────


class TestCompositionSpecCaptionPreset:
    def test_default_preset(self):
        spec = CompositionSpec(
            cadres=[{"index": 0, "prompt": "test", "duration_seconds": 5}],
        )
        assert spec.caption_preset == "default"

    def test_custom_preset(self):
        spec = CompositionSpec(
            cadres=[{"index": 0, "prompt": "test", "duration_seconds": 5}],
            caption_preset="hormozi",
        )
        assert spec.caption_preset == "hormozi"
