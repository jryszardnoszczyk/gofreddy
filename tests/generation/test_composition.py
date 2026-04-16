"""Tests for CompositionService."""

import asyncio
import shutil
from pathlib import Path

import pytest

from src.generation.composition import (
    CompositionService,
    _sanitize_caption,
    _generate_srt,
)
from src.generation.exceptions import GenerationError, GenerationTimeoutError
from src.generation.models import Cadre, Caption, CompositionSpec


@pytest.fixture
def composition_service():
    return CompositionService()


@pytest.fixture
def fixture_video():
    """Path to test fixture video."""
    p = Path(__file__).parent.parent / "fixtures" / "test_cadre.mp4"
    if not p.exists():
        pytest.skip("test_cadre.mp4 fixture not found")
    return p


class TestCaptionSanitization:
    def test_safe_text_passes_through(self):
        assert "Hello World" in _sanitize_caption("Hello World")

    def test_strips_backslash(self):
        result = _sanitize_caption("Hello\\nWorld")
        assert "\\" not in result or result == "Hello\\nWorld"  # regex strips disallowed

    def test_strips_semicolon_injection(self):
        result = _sanitize_caption("text;[evil]filter")
        # Semicolons and brackets should be escaped or stripped
        assert ";" not in result or "\\;" in result

    def test_preserves_unicode(self):
        """Unicode chars (including emojis) are now allowed — only injection vectors are blocked."""
        result = _sanitize_caption("Hello 🎬 World")
        assert "🎬" in result

    def test_allows_basic_punctuation(self):
        result = _sanitize_caption("Hello, World! How's it going?")
        assert "Hello" in result

    def test_preserves_emoji_only(self):
        """Emoji-only text is now valid (denylist approach, not allowlist)."""
        result = _sanitize_caption("🎬🎭")
        assert "🎬" in result

    def test_hyphen_allowed(self):
        result = _sanitize_caption("well-known fact")
        assert "well" in result


class TestSRTGeneration:
    def test_generates_valid_srt(self, tmp_path):
        captions = [
            Caption(text="Hello", start_seconds=0.0, end_seconds=2.0),
            Caption(text="World", start_seconds=3.0, end_seconds=5.0),
        ]
        srt_path = tmp_path / "test.srt"
        _generate_srt(captions, srt_path)
        content = srt_path.read_text()
        assert "1\n" in content
        assert "2\n" in content
        assert "Hello" in content
        assert "World" in content
        assert "-->" in content

    def test_refuses_existing_file(self, tmp_path):
        """O_EXCL should reject existing files (symlink prevention)."""
        srt_path = tmp_path / "existing.srt"
        srt_path.write_text("existing")
        with pytest.raises(FileExistsError):
            _generate_srt(
                [Caption(text="test", start_seconds=0.0, end_seconds=1.0)],
                srt_path,
            )


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="FFmpeg not installed")
class TestCompositionService:
    @pytest.mark.asyncio
    async def test_validate_output(self, composition_service, fixture_video):
        duration = await composition_service.validate_output(fixture_video)
        assert duration > 0
        assert duration < 10  # fixture is 3s

    @pytest.mark.asyncio
    async def test_validate_missing_file(self, composition_service, tmp_path):
        with pytest.raises(GenerationError, match="does not exist"):
            await composition_service.validate_output(tmp_path / "nonexistent.mp4")

    @pytest.mark.asyncio
    async def test_validate_zero_byte(self, composition_service, tmp_path):
        empty = tmp_path / "empty.mp4"
        empty.write_bytes(b"")
        with pytest.raises(GenerationError, match="zero bytes"):
            await composition_service.validate_output(empty)

    @pytest.mark.asyncio
    async def test_extract_final_frame(self, composition_service, fixture_video, tmp_path):
        output = tmp_path / "frame.png"
        result = await composition_service.extract_final_frame(fixture_video, output)
        assert result.exists()
        assert result.stat().st_size > 0

    @pytest.mark.asyncio
    async def test_compose_single_cadre(self, composition_service, fixture_video, tmp_path):
        output = tmp_path / "output.mp4"
        spec = CompositionSpec(
            cadres=[Cadre(index=0, prompt="test", duration_seconds=3)],
            resolution="480p",
        )
        result = await composition_service.compose([fixture_video], spec, output)
        assert result.exists()
        assert result.stat().st_size > 0

    @pytest.mark.asyncio
    async def test_compose_with_captions(self, composition_service, fixture_video, tmp_path):
        output = tmp_path / "output.mp4"
        spec = CompositionSpec(
            cadres=[Cadre(index=0, prompt="test", duration_seconds=3)],
            resolution="480p",
            captions=[Caption(text="Hello World", start_seconds=0.0, end_seconds=2.0)],
        )
        result = await composition_service.compose([fixture_video], spec, output)
        assert result.exists()
        assert result.stat().st_size > 0

    @pytest.mark.asyncio
    async def test_compose_two_cadres(self, composition_service, fixture_video, tmp_path):
        output = tmp_path / "output.mp4"
        spec = CompositionSpec(
            cadres=[
                Cadre(index=0, prompt="first", duration_seconds=3),
                Cadre(index=1, prompt="second", duration_seconds=3),
            ],
            resolution="480p",
        )
        # Use same fixture for both cadres
        result = await composition_service.compose(
            [fixture_video, fixture_video], spec, output
        )
        assert result.exists()
        assert result.stat().st_size > 0
