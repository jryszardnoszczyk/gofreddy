"""Test doubles for video generation flows."""

import asyncio
import base64
import shutil
from pathlib import Path
from typing import Self
import uuid

from .models import PreviewResult, StoryboardDraft, StoryboardSceneDraft, VerificationResult
from .providers import ImageResult, VideoClip

_PREVIEW_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO7+L7sAAAAASUVORK5CYII="
)


class FakeGenerationClient:
    """Test double for GenerationProvider. Returns fixture video with 2s delay."""

    _FIXTURE_PATH = Path(__file__).resolve().parent.parent.parent / "tests" / "fixtures" / "test_cadre.mp4"

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc) -> None:
        pass

    async def close(self) -> None:
        pass

    def reset_circuit_breaker(self) -> None:
        pass

    async def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "9:16",
        image_url: str | None = None,
    ) -> ImageResult:
        return ImageResult(url="https://fake.gen/test_image.png")

    async def generate_clip(
        self,
        prompt: str,
        duration: int,
        resolution: str,
        aspect_ratio: str = "auto",
        image_url: str | None = None,
    ) -> VideoClip:
        await asyncio.sleep(2.0)  # Simulate generation time
        return VideoClip(
            url="https://fake.x.ai/test_cadre.mp4",
            request_id="fake-request-id",
        )

    async def download_video(self, url: str, dest: Path) -> None:
        shutil.copy2(self._FIXTURE_PATH, dest)


class FakeIdeaService:
    """Deterministic storyboard ideation for local fake mode."""

    async def generate_storyboard_draft(
        self,
        *,
        creative_patterns: list[object],
        topic: str,
        style: str,
        context: str | None = None,
    ) -> StoryboardDraft:
        topic_text = topic.strip() or "Untitled concept"
        style_text = style.strip() or "creator-native pacing"
        scene_count = max(2, min(3, len(creative_patterns) or 3))
        scenes = [
            StoryboardSceneDraft(
                index=index,
                title=f"{topic_text[:48]} Scene {index + 1}",
                summary=(
                    f"{topic_text} in a {style_text} treatment."
                    if index == 0
                    else f"Continue {topic_text.lower()} with {style_text} energy."
                )[:240],
                prompt=(
                    f"{topic_text}. Scene {index + 1}. "
                    f"Vertical social video, {style_text}, crisp detail, creator-first framing."
                )[:2000],
                duration_seconds=4 if index < scene_count - 1 else 5,
                transition="fade" if index < scene_count - 1 else "cut",
            )
            for index in range(scene_count)
        ]
        return StoryboardDraft(
            scenes=scenes,
            aspect_ratio="9:16",
            resolution="720p",
        )


class FakeImagePreviewService:
    """Deterministic preview generation backed by local fake storage."""

    def __init__(self, storage) -> None:
        self._storage = storage

    async def generate_preview(
        self,
        user_id,
        prompt: str,
        aspect_ratio: str = "9:16",
        style_ref_path: str | None = None,
        model: str = "gemini",
    ) -> PreviewResult:
        del aspect_ratio, style_ref_path
        filename = f"{uuid.uuid4().hex}.png"
        r2_key = await self._storage.upload_preview(user_id, filename, _PREVIEW_PNG_BYTES)
        image_url = await self._storage.get_preview_url(r2_key)
        return PreviewResult(
            image_url=image_url,
            r2_key=r2_key,
            local_path="",
            qa_score=8,
            qa_feedback=f"Deterministic preview generated for: {prompt[:80]}",
            model_used=model,
        )

    async def verify_preview(
        self,
        prompt: str,
        generated_r2_key: str,
        style_ref_path: str | None = None,
    ) -> VerificationResult:
        del generated_r2_key, style_ref_path
        return VerificationResult(
            scene_score=8,
            style_score=7,
            overall_score=7,
            feedback=f"Deterministic verification for: {prompt[:60]}",
            improvement_suggestion="Add more specific lighting details to improve scene accuracy.",
        )

    async def generate_batch(
        self,
        user_id,
        prompts: list[str],
        style_ref_path: str,
        aspect_ratio: str = "9:16",
        model: str = "gemini",
    ) -> list[PreviewResult]:
        del style_ref_path, aspect_ratio
        results: list[PreviewResult] = []
        for prompt in prompts:
            results.append(await self.generate_preview(user_id, prompt, model=model))
        return results


# Backward-compatible alias
FakeGrokClient = FakeGenerationClient
