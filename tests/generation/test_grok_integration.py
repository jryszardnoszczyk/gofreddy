"""Integration test with real Grok API.

Requires XAI_API_KEY environment variable.
Run with: pytest -m external_api tests/generation/test_grok_integration.py
"""

import os

import pytest
from pydantic import SecretStr

from src.generation.config import GenerationSettings
from src.generation.grok_client import GrokImagineClient


@pytest.mark.external_api
@pytest.mark.skipif(
    not os.getenv("XAI_API_KEY"),
    reason="XAI_API_KEY not set",
)
class TestGrokIntegration:
    @pytest.mark.asyncio
    async def test_generate_single_cadre(self, tmp_path):
        """Generate a single 5s cadre at 480p resolution."""
        settings = GenerationSettings(
            xai_api_key=SecretStr(os.getenv("XAI_API_KEY", "")),
            generation_enabled=True,
            poll_timeout_seconds=300.0,
            poll_interval_seconds=5.0,
        )

        async with GrokImagineClient(settings) as client:
            clip = await client.generate_clip(
                prompt="A serene mountain landscape with gentle clouds",
                duration=5,
                resolution="480p",
            )
            assert clip.url
            assert clip.request_id

            # Download and validate
            dest = tmp_path / "test_output.mp4"
            await client.download_video(clip.url, dest)
            assert dest.exists()
            assert dest.stat().st_size > 0
