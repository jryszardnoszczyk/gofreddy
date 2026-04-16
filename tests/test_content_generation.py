"""Tests for content generation service — mock-based for Gemini control flow."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.content_gen.config import ContentGenSettings
from src.content_gen.exceptions import ContentGenError
from src.content_gen.service import ContentGenerationService
from src.content_gen.voice_models import VoiceProfile
from src.content_gen.voice_repository import PostgresVoiceRepository
from src.seo.article_repository import PostgresArticleRepository


@pytest.fixture
def settings():
    return ContentGenSettings(enabled=True)


@pytest.fixture
def mock_voice_repo():
    return AsyncMock(spec=PostgresVoiceRepository)


@pytest.fixture
def mock_article_repo():
    return AsyncMock(spec=PostgresArticleRepository)


@pytest.fixture
def mock_gemini():
    client = MagicMock()
    return client


@pytest.fixture
def service(mock_gemini, mock_voice_repo, mock_article_repo, settings):
    return ContentGenerationService(
        gemini_client=mock_gemini,
        voice_repo=mock_voice_repo,
        article_repo=mock_article_repo,
        settings=settings,
    )


class TestBuildSystemInstruction:
    @pytest.mark.asyncio
    async def test_without_voice_profile(self, service):
        result = await service._build_system_instruction(
            uuid4(), "Test action instruction"
        )
        assert result == "Test action instruction"

    @pytest.mark.asyncio
    async def test_with_voice_profile(self, service, mock_voice_repo):
        profile = VoiceProfile(
            id=uuid4(), org_id=uuid4(), name="Test", platform="twitter",
            username="test", system_instruction="VOICE: Be bold and direct.",
        )
        mock_voice_repo.get_profile.return_value = profile

        result = await service._build_system_instruction(
            profile.org_id, "Action instruction", voice_profile_id=profile.id,
        )
        assert "VOICE: Be bold and direct." in result
        assert "Action instruction" in result

    @pytest.mark.asyncio
    async def test_voice_profile_not_found_raises(self, service, mock_voice_repo):
        mock_voice_repo.get_profile.return_value = None
        with pytest.raises(ContentGenError, match="voice_profile_not_found"):
            await service._build_system_instruction(
                uuid4(), "instruction", voice_profile_id=uuid4(),
            )

    @pytest.mark.asyncio
    async def test_voice_profile_org_isolation(self, service, mock_voice_repo):
        """Voice profile must belong to requesting org."""
        mock_voice_repo.get_profile.return_value = None  # org_id mismatch
        with pytest.raises(ContentGenError, match="voice_profile_not_found"):
            await service._build_system_instruction(
                uuid4(), "instruction", voice_profile_id=uuid4(),
            )


@pytest.mark.mock_required
class TestGenerate:
    @pytest.mark.asyncio
    async def test_empty_candidates_raises(self, service, mock_gemini):
        """Guard response.candidates for emptiness."""
        mock_response = MagicMock()
        mock_response.candidates = []
        mock_gemini.aio.models.generate_content = AsyncMock(return_value=mock_response)

        with pytest.raises(ContentGenError, match="empty_response"):
            await service._generate(
                "sys", "content", {"type": "object"}, action_name="test",
            )
