"""Tests for generation domain models."""

import pytest
from pydantic import ValidationError
from uuid import uuid4

from src.generation.models import Cadre, Caption, CompositionSpec


class TestCadre:
    def test_frozen_immutability(self):
        cadre = Cadre(index=0, prompt="test", duration_seconds=5)
        with pytest.raises(ValidationError):
            cadre.index = 1

    def test_default_transition(self):
        cadre = Cadre(index=0, prompt="test", duration_seconds=5)
        assert cadre.transition == "fade"
        assert cadre.seed_image_storage_key is None

    def test_accepts_optional_seed_image_storage_key(self):
        cadre = Cadre(
            index=0,
            prompt="test",
            duration_seconds=5,
            seed_image_storage_key="previews/user-id/0123456789abcdef0123456789abcdef.png",
        )
        assert cadre.seed_image_storage_key == "previews/user-id/0123456789abcdef0123456789abcdef.png"

    def test_valid_cadre(self):
        cadre = Cadre(
            index=3, prompt="A sunset over mountains",
            duration_seconds=10, transition="dissolve",
        )
        assert cadre.index == 3
        assert cadre.prompt == "A sunset over mountains"
        assert cadre.duration_seconds == 10
        assert cadre.transition == "dissolve"

    @pytest.mark.parametrize("duration", [-1, -100, 0])
    def test_rejects_non_positive_duration(self, duration):
        with pytest.raises(ValidationError):
            Cadre(index=0, prompt="test", duration_seconds=duration)

    def test_rejects_duration_above_max(self):
        with pytest.raises(ValidationError):
            Cadre(index=0, prompt="test", duration_seconds=31)

    def test_accepts_boundary_durations(self):
        assert Cadre(index=0, prompt="test", duration_seconds=1).duration_seconds == 1
        assert Cadre(index=0, prompt="test", duration_seconds=30).duration_seconds == 30

    def test_accepts_long_prompt(self):
        cadre = Cadre(index=0, prompt="a" * 5000, duration_seconds=5)
        assert len(cadre.prompt) == 5000

    @pytest.mark.parametrize("bad_transition", ["slide", "zoom", "", "FADE"])
    def test_rejects_invalid_transition(self, bad_transition):
        with pytest.raises(ValidationError):
            Cadre(index=0, prompt="test", duration_seconds=5, transition=bad_transition)

    @pytest.mark.parametrize("valid_transition", ["fade", "cut", "dissolve", "wipe"])
    def test_accepts_valid_transitions(self, valid_transition):
        cadre = Cadre(index=0, prompt="test", duration_seconds=5, transition=valid_transition)
        assert cadre.transition == valid_transition

    @pytest.mark.parametrize("bad_index", [-1, 20, 100])
    def test_rejects_out_of_range_index(self, bad_index):
        with pytest.raises(ValidationError):
            Cadre(index=bad_index, prompt="test", duration_seconds=5)

    def test_accepts_boundary_indices(self):
        assert Cadre(index=0, prompt="test", duration_seconds=5).index == 0
        assert Cadre(index=19, prompt="test", duration_seconds=5).index == 19


class TestCaption:
    def test_valid_caption(self):
        c = Caption(text="Hello world!", start_seconds=0.0, end_seconds=5.0)
        assert c.text == "Hello world!"
        assert c.position == "bottom"

    def test_max_length(self):
        with pytest.raises(Exception):
            Caption(text="a" * 201, start_seconds=0.0, end_seconds=5.0)

    @pytest.mark.parametrize("unsafe", [
        "test;drop",       # semicolon — FFmpeg filter chain separator
        "test%{expr}",     # percent — FFmpeg dynamic expansion
        "test[pad]",       # brackets — FFmpeg filter pad labels
        "test\\n",         # backslash — escape sequences
        "test#comment",    # hash — FFmpeg/ASS comment
        "test`shell`",     # backtick — shell expansion
        "test$var",        # dollar — shell expansion
        "test|pipe",       # pipe — shell expansion
        "Line 1\nLine 2", # newline — control character
    ])
    def test_rejects_unsafe_characters(self, unsafe):
        with pytest.raises(Exception):
            Caption(text=unsafe, start_seconds=0.0, end_seconds=5.0)

    @pytest.mark.parametrize("safe", [
        "Hello world!",
        "Question? Answer.",
        "It's a great day",
        "Price - discount",
        "test:value",                # colons are safe in SRT
        'test"quoted"',              # quotes are safe
        "Great video @user",         # at-sign is safe
        "Price (50) - discount",     # parentheses are safe
        "A & B",                     # ampersand is safe
        "Bonjour le monde",          # Unicode accented chars
        "こんにちは",                  # CJK
    ])
    def test_allows_safe_characters(self, safe):
        c = Caption(text=safe, start_seconds=0.0, end_seconds=5.0)
        assert c.text == safe


class TestCompositionSpec:
    def test_valid_spec(self):
        spec = CompositionSpec(
            cadres=[Cadre(index=0, prompt="test", duration_seconds=5)],
        )
        assert len(spec.cadres) == 1
        assert spec.aspect_ratio == "9:16"
        assert spec.resolution == "720p"

    def test_min_cadres(self):
        with pytest.raises(Exception):
            CompositionSpec(cadres=[])

    def test_max_cadres(self):
        cadres = [Cadre(index=i % 20, prompt=f"test {i}", duration_seconds=5) for i in range(21)]
        with pytest.raises(Exception):
            CompositionSpec(cadres=cadres)

    def test_max_source_analysis_ids(self):
        ids = [uuid4() for _ in range(26)]
        with pytest.raises(Exception):
            CompositionSpec(
                cadres=[Cadre(index=0, prompt="test", duration_seconds=5)],
                source_analysis_ids=ids,
            )

    def test_defaults(self):
        spec = CompositionSpec(
            cadres=[Cadre(index=0, prompt="test", duration_seconds=5)],
        )
        assert spec.captions == []
        assert spec.source_analysis_ids == []

    @pytest.mark.parametrize("bad_resolution", ["4K", "bananas", ""])
    def test_rejects_invalid_resolution(self, bad_resolution):
        with pytest.raises(Exception):
            CompositionSpec(
                cadres=[Cadre(index=0, prompt="test", duration_seconds=5)],
                resolution=bad_resolution,
            )

    @pytest.mark.parametrize("bad_ratio", ["bananas", "4:3", "2:1", ""])
    def test_rejects_invalid_aspect_ratio(self, bad_ratio):
        with pytest.raises(Exception):
            CompositionSpec(
                cadres=[Cadre(index=0, prompt="test", duration_seconds=5)],
                aspect_ratio=bad_ratio,
            )

    @pytest.mark.parametrize("valid_resolution", ["480p", "720p"])
    def test_accepts_valid_resolution(self, valid_resolution):
        spec = CompositionSpec(
            cadres=[Cadre(index=0, prompt="test", duration_seconds=5)],
            resolution=valid_resolution,
        )
        assert spec.resolution == valid_resolution

    @pytest.mark.parametrize("valid_ratio", ["9:16", "16:9", "1:1"])
    def test_accepts_valid_aspect_ratio(self, valid_ratio):
        spec = CompositionSpec(
            cadres=[Cadre(index=0, prompt="test", duration_seconds=5)],
            aspect_ratio=valid_ratio,
        )
        assert spec.aspect_ratio == valid_ratio

    @pytest.mark.parametrize("bad_preset", ["bananas", "HORMOZI", "", "Comic Sans"])
    def test_rejects_invalid_caption_preset(self, bad_preset):
        with pytest.raises(Exception):
            CompositionSpec(
                cadres=[Cadre(index=0, prompt="test", duration_seconds=5)],
                caption_preset=bad_preset,
            )

    @pytest.mark.parametrize("valid_preset", ["default", "hormozi", "minimal", "elegant", "cinematic", "neon"])
    def test_accepts_valid_caption_preset(self, valid_preset):
        spec = CompositionSpec(
            cadres=[Cadre(index=0, prompt="test", duration_seconds=5)],
            caption_preset=valid_preset,
        )
        assert spec.caption_preset == valid_preset
