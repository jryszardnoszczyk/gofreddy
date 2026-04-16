"""Tests for ImagePreviewService."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.common.gemini_models import GEMINI_FLASH_IMAGE, GEMINI_FLASH_LITE
from src.generation.config import GenerationSettings
from src.generation.exceptions import PreviewError
from src.generation.image_preview_service import ImagePreviewService
from src.generation.models import PreviewResult, VerificationResult


@pytest.fixture
def settings():
    return GenerationSettings(
        generation_enabled=True,
        preview_enabled=True,
        preview_model=GEMINI_FLASH_IMAGE,
    )


@pytest.fixture
def mock_storage():
    storage = MagicMock()
    storage.upload_preview = AsyncMock(return_value="previews/user-id/abc.png")
    storage.get_preview_url = AsyncMock(return_value="https://r2.example.com/previews/user-id/abc.png")
    storage.download_preview = AsyncMock(return_value=b"fake-png-data")
    return storage


@pytest.fixture
def mock_client():
    return MagicMock()


@pytest.fixture
def service(mock_client, mock_storage, settings):
    return ImagePreviewService(client=mock_client, storage=mock_storage, settings=settings)


def _make_image_response(image_data: bytes = b"fake-png-data", finish_reason: str = "STOP"):
    """Create a mock Gemini response with inline image data."""
    inline_data = MagicMock()
    inline_data.data = image_data

    part = MagicMock()
    part.inline_data = inline_data

    content = MagicMock()
    content.parts = [part]

    candidate = MagicMock()
    candidate.finish_reason = finish_reason
    candidate.content = content

    response = MagicMock()
    response.candidates = [candidate]
    response.text = '{"score": 7, "feedback": "Good match"}'
    response.usage_metadata = None  # extract_gemini_usage handles None gracefully
    return response


def _make_text_only_response(text: str = "", finish_reason: str = "STOP"):
    """Create a mock Gemini response with no image (text only)."""
    part = MagicMock()
    part.inline_data = None

    content = MagicMock()
    content.parts = [part]

    candidate = MagicMock()
    candidate.finish_reason = finish_reason
    candidate.content = content

    response = MagicMock()
    response.candidates = [candidate]
    response.text = text
    response.usage_metadata = None
    return response


def _make_qa_response(score: int = 8, feedback: str = "Nice scene"):
    """Create a mock Gemini QA response."""
    resp = MagicMock()
    resp.text = f'{{"score": {score}, "feedback": "{feedback}"}}'
    resp.candidates = [MagicMock(finish_reason="STOP")]
    resp.usage_metadata = None
    return resp


class TestGeneratePreview:
    @pytest.mark.asyncio
    async def test_success(self, service, mock_client, mock_storage):
        img_resp = _make_image_response()
        qa_resp = _make_qa_response()

        mock_client.aio.models.generate_content = AsyncMock(side_effect=[img_resp, qa_resp])

        result = await service.generate_preview(uuid4(), "A sunset beach scene")

        assert isinstance(result, PreviewResult)
        assert result.image_url == "https://r2.example.com/previews/user-id/abc.png"
        assert result.r2_key == "previews/user-id/abc.png"
        assert result.qa_score == 8
        assert result.qa_feedback == "Nice scene"
        assert result.model_used == "gemini"
        mock_storage.upload_preview.assert_awaited_once()
        # QA downloads the generated image for verification
        mock_storage.download_preview.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_safety_block_raises(self, service, mock_client):
        response = _make_image_response(finish_reason="SAFETY")
        mock_client.aio.models.generate_content = AsyncMock(return_value=response)

        with pytest.raises(PreviewError, match="safety filter"):
            await service.generate_preview(uuid4(), "test prompt")

    @pytest.mark.asyncio
    async def test_no_image_in_response_raises(self, service, mock_client):
        response = _make_text_only_response("Some text")
        mock_client.aio.models.generate_content = AsyncMock(return_value=response)

        with pytest.raises(PreviewError, match="No image generated"):
            await service.generate_preview(uuid4(), "test prompt")

    @pytest.mark.asyncio
    async def test_timeout_raises(self, service, mock_client):
        mock_client.aio.models.generate_content = AsyncMock(
            side_effect=asyncio.TimeoutError()
        )

        with pytest.raises(PreviewError, match="timed out"):
            await service.generate_preview(uuid4(), "test prompt")

    @pytest.mark.asyncio
    async def test_rate_limit_raises(self, service, mock_client):
        mock_client.aio.models.generate_content = AsyncMock(
            side_effect=RuntimeError("429 RESOURCE_EXHAUSTED")
        )

        with pytest.raises(PreviewError, match="Rate limited"):
            await service.generate_preview(uuid4(), "test prompt")

    @pytest.mark.asyncio
    async def test_generic_error_raises(self, service, mock_client):
        mock_client.aio.models.generate_content = AsyncMock(
            side_effect=RuntimeError("Connection failed")
        )

        with pytest.raises(PreviewError, match="generation failed"):
            await service.generate_preview(uuid4(), "test prompt")

    @pytest.mark.asyncio
    async def test_with_style_reference(self, service, mock_client, mock_storage):
        img_resp = _make_image_response()
        qa_resp = _make_qa_response(score=7, feedback="OK")

        mock_client.aio.models.generate_content = AsyncMock(side_effect=[img_resp, qa_resp])

        result = await service.generate_preview(
            uuid4(), "A beach scene", style_ref_path="previews/user/ref.png"
        )

        assert isinstance(result, PreviewResult)
        # download_preview called 3x: generation style conditioning + QA anchor + QA generated image
        assert mock_storage.download_preview.await_count == 3

    @pytest.mark.asyncio
    async def test_qa_failure_returns_none_scores(self, service, mock_client):
        img_resp = _make_image_response()
        # QA call fails
        mock_client.aio.models.generate_content = AsyncMock(
            side_effect=[img_resp, asyncio.TimeoutError()]
        )

        result = await service.generate_preview(uuid4(), "test prompt")
        assert result.qa_score is None
        assert result.qa_feedback is None

    @pytest.mark.asyncio
    async def test_qa_uses_verifier_model(self, service, mock_client, mock_storage):
        """Verify QA uses the lightweight verifier model, not the generation model."""
        img_resp = _make_image_response()
        qa_resp = _make_qa_response()

        mock_client.aio.models.generate_content = AsyncMock(side_effect=[img_resp, qa_resp])

        await service.generate_preview(uuid4(), "A sunset scene")

        # Second call is QA — should use verifier model
        qa_call = mock_client.aio.models.generate_content.call_args_list[1]
        assert qa_call.kwargs["model"] == GEMINI_FLASH_LITE


class TestGenerateBatch:
    @pytest.mark.asyncio
    async def test_batch_success(self, service, mock_client, mock_storage):
        img_resp = _make_image_response()
        qa_resp = _make_qa_response(score=7, feedback="OK")
        mock_storage.download_preview = AsyncMock(return_value=b"fake-anchor-png")

        mock_client.aio.models.generate_content = AsyncMock(side_effect=[
            img_resp, qa_resp,
            img_resp, qa_resp,
            img_resp, qa_resp,
        ])

        results = await service.generate_batch(
            uuid4(),
            ["scene 1", "scene 2", "scene 3"],
            style_ref_path="previews/user/ref.png",
        )

        assert len(results) == 3
        assert all(r is not None for r in results)

    @pytest.mark.asyncio
    async def test_batch_partial_failure(self, service, mock_client, mock_storage):
        img_resp = _make_image_response()
        qa_resp = _make_qa_response(score=7, feedback="OK")
        mock_storage.download_preview = AsyncMock(return_value=b"fake-anchor-png")

        # First succeeds, second fails, third succeeds
        call_count = 0

        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # Calls: 1=img1, 2=qa1, 3=img2(fail), 4=img3, 5=qa3
            if call_count == 3:
                raise RuntimeError("Connection failed")
            if call_count in (1, 4):
                return img_resp
            return qa_resp

        mock_client.aio.models.generate_content = AsyncMock(side_effect=side_effect)

        results = await service.generate_batch(
            uuid4(),
            ["scene 1", "scene 2", "scene 3"],
            style_ref_path="previews/user/ref.png",
        )

        assert len(results) == 3
        # At least one should be None (the failed one)
        none_count = sum(1 for r in results if r is None)
        assert none_count >= 1


def _make_verification_response(
    scene_score: int = 8,
    style_score: int = 7,
    feedback: str = "Good overall",
    improvement_suggestion: str = "Add more contrast",
):
    """Create a mock Gemini structured verification response."""
    resp = MagicMock()
    resp.text = (
        f'{{"scene_score": {scene_score}, "style_score": {style_score}, '
        f'"feedback": "{feedback}", "improvement_suggestion": "{improvement_suggestion}"}}'
    )
    resp.candidates = [MagicMock(finish_reason="STOP")]
    resp.usage_metadata = None
    return resp


class TestVerifyPreview:
    @pytest.mark.asyncio
    async def test_success_with_style_ref(self, service, mock_client, mock_storage):
        verify_resp = _make_verification_response(scene_score=8, style_score=6)
        mock_client.aio.models.generate_content = AsyncMock(return_value=verify_resp)

        result = await service.verify_preview(
            "A sunset beach scene",
            "previews/user/gen.png",
            style_ref_path="previews/user/anchor.png",
        )

        assert isinstance(result, VerificationResult)
        assert result.scene_score == 8
        assert result.style_score == 6
        assert result.overall_score == 6  # min(8, 6)
        assert result.feedback == "Good overall"
        assert result.improvement_suggestion == "Add more contrast"
        # Downloads: anchor + generated image
        assert mock_storage.download_preview.await_count == 2

    @pytest.mark.asyncio
    async def test_success_without_style_ref(self, service, mock_client, mock_storage):
        verify_resp = _make_verification_response(scene_score=9, style_score=9)
        mock_client.aio.models.generate_content = AsyncMock(return_value=verify_resp)

        result = await service.verify_preview("A beach scene", "previews/user/gen.png")

        assert result.scene_score == 9
        assert result.style_score == 9
        # Only downloads generated image (no anchor)
        assert mock_storage.download_preview.await_count == 1

    @pytest.mark.asyncio
    async def test_uses_verifier_model(self, service, mock_client, mock_storage):
        verify_resp = _make_verification_response()
        mock_client.aio.models.generate_content = AsyncMock(return_value=verify_resp)

        await service.verify_preview("test", "previews/user/gen.png")

        call = mock_client.aio.models.generate_content.call_args
        assert call.kwargs["model"] == GEMINI_FLASH_LITE

    @pytest.mark.asyncio
    async def test_timeout_raises(self, service, mock_client, mock_storage):
        mock_client.aio.models.generate_content = AsyncMock(
            side_effect=asyncio.TimeoutError()
        )

        with pytest.raises(PreviewError, match="timed out"):
            await service.verify_preview("test", "previews/user/gen.png")

    @pytest.mark.asyncio
    async def test_download_failure_raises(self, service, mock_client, mock_storage):
        mock_storage.download_preview = AsyncMock(side_effect=RuntimeError("R2 down"))

        with pytest.raises(PreviewError, match="Could not download"):
            await service.verify_preview("test", "previews/user/gen.png")

    @pytest.mark.asyncio
    async def test_clamps_scores(self, service, mock_client, mock_storage):
        """Scores outside 1-10 are clamped."""
        resp = MagicMock()
        resp.text = '{"scene_score": 15, "style_score": -3, "feedback": "ok", "improvement_suggestion": "none"}'
        resp.candidates = [MagicMock(finish_reason="STOP")]
        resp.usage_metadata = None
        mock_client.aio.models.generate_content = AsyncMock(return_value=resp)

        result = await service.verify_preview("test", "previews/user/gen.png")
        assert result.scene_score == 10
        assert result.style_score == 1
