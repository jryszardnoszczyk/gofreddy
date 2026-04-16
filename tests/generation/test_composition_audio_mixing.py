"""Tests for CompositionService audio mixing (PR-100)."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.generation.composition import CompositionService
from src.generation.exceptions import GenerationError
from src.generation.models import Cadre, CompositionSpec


def _make_spec(n_cadres=2, duration=5) -> CompositionSpec:
    return CompositionSpec(
        cadres=[
            Cadre(index=i, prompt=f"Shot {i}", duration_seconds=duration)
            for i in range(n_cadres)
        ],
        resolution="720p",
    )


class TestComposeSignature:
    """Verify compose() accepts the new audio parameters."""

    @pytest.mark.asyncio
    @pytest.mark.mock_required
    async def test_accepts_narration_path_kwarg(self):
        service = CompositionService()
        # Should not raise TypeError for unexpected keyword
        import inspect
        sig = inspect.signature(service.compose)
        assert "narration_path" in sig.parameters
        assert "music_path" in sig.parameters

    @pytest.mark.asyncio
    @pytest.mark.mock_required
    async def test_compose_single_accepts_audio_params(self):
        service = CompositionService()
        import inspect
        sig = inspect.signature(service._compose_single)
        assert "narration_path" in sig.parameters
        assert "music_path" in sig.parameters


class TestNarrationValidation:
    @pytest.mark.asyncio
    @pytest.mark.mock_required
    async def test_narration_file_not_found(self):
        service = CompositionService()
        spec = _make_spec()
        fake_cadre = Path("/tmp/nonexistent-cadre.mp4")
        fake_narration = Path("/tmp/nonexistent-narration.mp3")

        # Mock _probe_clip so we get past the probing stage
        with patch.object(service, "_probe_clip", new_callable=AsyncMock, return_value=(True, 5.0)):
            with pytest.raises(GenerationError, match="Narration file not found"):
                await service.compose(
                    [fake_cadre, fake_cadre],
                    spec,
                    Path("/tmp/out.mp4"),
                    narration_path=fake_narration,
                )

    @pytest.mark.asyncio
    @pytest.mark.mock_required
    async def test_music_file_not_found(self):
        service = CompositionService()
        spec = _make_spec()
        fake_cadre = Path("/tmp/nonexistent-cadre.mp4")
        fake_music = Path("/tmp/nonexistent-music.mp3")

        with patch.object(service, "_probe_clip", new_callable=AsyncMock, return_value=(True, 5.0)):
            with pytest.raises(GenerationError, match="Music file not found"):
                await service.compose(
                    [fake_cadre, fake_cadre],
                    spec,
                    Path("/tmp/out.mp4"),
                    music_path=fake_music,
                )
