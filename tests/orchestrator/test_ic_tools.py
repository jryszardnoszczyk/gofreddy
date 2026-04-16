"""Tests for IC (Influencers.club) agent tool handlers.

Validates IC tool registration, handler behavior,
and the consolidated IC tools (creator_profile, discover_creators).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.billing.tiers import Tier
from src.orchestrator.tools import build_default_registry
from src.search.exceptions import ICUnavailableError


def _mock_ic_backend():
    """Create a mock ICBackend with default responses."""
    backend = MagicMock()
    backend.discover = AsyncMock(return_value={
        "accounts": [
            {
                "profile": {
                    "username": "fitness_guru",
                    "full_name": "Fitness Guru",
                    "picture": "https://cdn.example.com/avatar.jpg",
                    "followers": 100000,
                    "engagement_percent": 4.5,
                    "is_verified": True,
                },
            },
            {
                "profile": {
                    "username": "yoga_master",
                    "full_name": "Yoga Master",
                    "picture": "https://cdn.example.com/avatar2.jpg",
                    "followers": 50000,
                    "engagement_percent": 3.2,
                    "is_verified": False,
                },
            },
        ],
    })
    backend.find_similar = AsyncMock(return_value={
        "accounts": [
            {
                "profile": {
                    "username": "similar_creator",
                    "full_name": "Similar Creator",
                    "picture": "https://cdn.example.com/similar.jpg",
                    "followers": 80000,
                    "engagement_percent": 5.0,
                    "is_verified": True,
                },
            },
        ],
    })
    backend.enrich_full = AsyncMock(return_value={
        "result": {
            "instagram": {
                "username": "fitness_guru",
                "full_name": "Fitness Guru",
                "follower_count": 100000,
                "engagement_percent": 4.5,
            },
            "audience": {"countries": [{"code": "US", "pct": 45}]},
            "income": {"estimated_monthly": 5000},
            "niche_class": "Health & Fitness",
            "niche_sub_class": "Yoga",
            "email": "guru@fitness.com",
            "connected_socials": [{"platform": "youtube"}, {"platform": "tiktok"}],
        },
    })
    backend.enrich_email = AsyncMock(return_value={
        "result": {
            "instagram": {
                "username": "found_user",
                "full_name": "Found User",
                "follower_count": 25000,
                "engagement_percent": 3.0,
            },
        },
    })
    backend.connected_socials = AsyncMock(return_value={
        "result": {
            "youtube": {"username": "fitness_guru_yt", "url": "https://youtube.com/@fitness_guru_yt"},
            "tiktok": {"username": "fitness_guru", "url": "https://tiktok.com/@fitness_guru"},
        },
    })
    backend.get_content = AsyncMock(return_value={
        "data": [
            {"id": "post1", "url": "https://instagram.com/p/abc", "likes": 5000, "caption": "Great workout"},
            {"id": "post2", "url": "https://instagram.com/p/def", "likes": 3000, "caption": "Morning routine"},
        ],
    })
    backend.get_post_details = AsyncMock(return_value={
        "post": {"id": "post1", "likes": 5000, "caption": "Great workout"},
        "transcript": "Today I want to show you my favorite exercises...",
    })
    backend.audience_overlap = AsyncMock(return_value={
        "overlap_pct": 32.5,
        "pairs": [{"a": "user1", "b": "user2", "overlap": 32.5}],
    })
    backend.get_credits = AsyncMock(return_value={"credits_left": "42.5"})
    return backend


@pytest.fixture
def ic_backend():
    return _mock_ic_backend()


def _build_registry(ic_backend=None, tier=Tier.PRO):
    """Build registry with IC backend."""
    registry, restricted = build_default_registry(
        search_service=None,
        fetchers=None,
        tier=tier,
        ic_backend=ic_backend,
    )
    return registry, restricted


# ── Tool Registration ────────────────────────────────────────────────


class TestICToolRegistration:
    def test_ic_tools_registered_when_backend_available(self, ic_backend):
        registry, _ = _build_registry(ic_backend=ic_backend)
        ic_tools = {"creator_profile"}
        registered = set(registry.names)
        assert ic_tools.issubset(registered), f"Missing: {ic_tools - registered}"
        assert "get_creator_content" not in registered, "get_creator_content should be absorbed into manage_ic_creator"

    def test_ic_tools_not_registered_without_backend(self):
        registry, _ = _build_registry(ic_backend=None)
        ic_tools = {"creator_profile"}
        registered = set(registry.names)
        assert not ic_tools & registered, f"Should not be registered: {ic_tools & registered}"

    def test_search_creators_registered_with_ic_only(self, ic_backend):
        registry, _ = _build_registry(ic_backend=ic_backend)
        assert "discover_creators" in registry.names


# ── manage_ic_creator: enrich ────────────────────────────────────────


class TestEnrichCreator:
    async def test_happy_path(self, ic_backend):
        registry, _ = _build_registry(ic_backend=ic_backend)
        result = await registry.execute("creator_profile", {
            "action": "enrich", "platform": "instagram", "username": "fitness_guru",
        })
        assert "summary" in result
        assert "fitness_guru" in result["summary"]
        assert result["platform"] == "instagram"
        assert result["username"] == "fitness_guru"
        assert result["profile"]["follower_count"] == 100000
        assert result["niche"]["class"] == "Health & Fitness"
        assert result["email"] == "guru@fitness.com"
        ic_backend.enrich_full.assert_called_once()

    async def test_creator_not_found(self, ic_backend):
        ic_backend.enrich_full = AsyncMock(return_value={})
        registry, _ = _build_registry(ic_backend=ic_backend)
        result = await registry.execute("creator_profile", {
            "action": "enrich", "platform": "instagram", "username": "nonexistent",
        })
        # Empty result -> profile is empty dict but no error key
        # Actually with empty {} the handler returns an empty profile
        assert "summary" in result

    async def test_ic_unavailable(self, ic_backend):
        ic_backend.enrich_full = AsyncMock(side_effect=ICUnavailableError(503, "down"))
        registry, _ = _build_registry(ic_backend=ic_backend)
        result = await registry.execute("creator_profile", {
            "action": "enrich", "platform": "instagram", "username": "someone",
        })
        assert result["error"] == "ic_unavailable"

    async def test_invalid_platform(self, ic_backend):
        ic_backend.enrich_full = AsyncMock(side_effect=ValueError("bad platform"))
        registry, _ = _build_registry(ic_backend=ic_backend)
        result = await registry.execute("creator_profile", {
            "action": "enrich", "platform": "badplatform", "username": "someone",
        })
        assert result["error"] == "ic_invalid_platform"

    async def test_unexpected_error(self, ic_backend):
        ic_backend.enrich_full = AsyncMock(side_effect=RuntimeError("boom"))
        registry, _ = _build_registry(ic_backend=ic_backend)
        result = await registry.execute("creator_profile", {
            "action": "enrich", "platform": "instagram", "username": "someone",
        })
        assert result["error"] == "ic_unavailable"


# ── manage_ic_creator: list_content ────────────────────────────────────


class TestGetCreatorContent:
    async def test_happy_path(self, ic_backend):
        registry, _ = _build_registry(ic_backend=ic_backend)
        result = await registry.execute("creator_profile", {
            "action": "list_content", "platform": "instagram", "username": "fitness_guru",
        })
        assert "summary" in result
        assert len(result["posts"]) == 2
        assert result["total"] == 2
        assert result["page"] == 0

    async def test_invalid_platform_rejected_by_ic(self, ic_backend):
        ic_backend.get_content = AsyncMock(side_effect=ValueError("platform not supported"))
        registry, _ = _build_registry(ic_backend=ic_backend)
        result = await registry.execute("creator_profile", {
            "action": "list_content", "platform": "twitch", "username": "someone",
        })
        assert result["error"] == "ic_invalid_platform"

    async def test_ic_unavailable(self, ic_backend):
        ic_backend.get_content = AsyncMock(side_effect=ICUnavailableError(503, "down"))
        registry, _ = _build_registry(ic_backend=ic_backend)
        result = await registry.execute("creator_profile", {
            "action": "list_content", "platform": "instagram", "username": "someone",
        })
        assert result["error"] == "ic_unavailable"

    async def test_pagination(self, ic_backend):
        registry, _ = _build_registry(ic_backend=ic_backend)
        result = await registry.execute("creator_profile", {
            "action": "list_content", "platform": "tiktok", "username": "creator", "page": 2,
        })
        assert result["page"] == 2
        ic_backend.get_content.assert_called_once_with("tiktok", "creator", page=2)


# ── manage_ic_creator: get_post ──────────────────────────────────────


class TestGetPostDetails:
    async def test_happy_path_data(self, ic_backend):
        registry, _ = _build_registry(ic_backend=ic_backend)
        result = await registry.execute("creator_profile", {
            "action": "get_post", "platform": "instagram", "username": "fitness_guru",
            "post_url": "https://www.instagram.com/p/abc123",
        })
        assert "summary" in result
        assert result["content_type"] == "data"
        assert result["result"] is not None

    async def test_happy_path_transcript(self, ic_backend):
        registry, _ = _build_registry(ic_backend=ic_backend)
        result = await registry.execute("creator_profile", {
            "action": "get_post", "platform": "tiktok", "username": "creator",
            "post_url": "https://www.tiktok.com/@creator/video/123",
            "content_type": "transcript",
        })
        assert result["content_type"] == "transcript"

    async def test_invalid_post_url_domain(self, ic_backend):
        registry, _ = _build_registry(ic_backend=ic_backend)
        result = await registry.execute("creator_profile", {
            "action": "get_post", "platform": "instagram", "username": "creator",
            "post_url": "https://evil.com/p/abc123",
        })
        assert result["error"] == "invalid_parameter"
        ic_backend.get_post_details.assert_not_called()

    async def test_unsupported_content_type_for_platform(self, ic_backend):
        """Instagram only supports data/comments -- transcript should fail."""
        registry, _ = _build_registry(ic_backend=ic_backend)
        result = await registry.execute("creator_profile", {
            "action": "get_post", "platform": "instagram", "username": "creator",
            "post_url": "https://www.instagram.com/p/abc",
            "content_type": "transcript",
        })
        assert result["error"] == "invalid_parameter"

    async def test_hallucinated_url_rejected(self, ic_backend):
        registry, _ = _build_registry(ic_backend=ic_backend)
        result = await registry.execute("creator_profile", {
            "action": "get_post", "platform": "instagram", "username": "creator",
            "post_url": "https://hallucinated-site.com/p/abc",
        })
        assert result["error"] == "invalid_parameter"
        ic_backend.get_post_details.assert_not_called()


# ── manage_ic_creator: connected_socials ─────────────────────────────


class TestGetConnectedSocials:
    async def test_happy_path(self, ic_backend):
        registry, _ = _build_registry(ic_backend=ic_backend)
        result = await registry.execute("creator_profile", {
            "action": "connected_socials", "platform": "instagram", "username": "fitness_guru",
        })
        assert "summary" in result
        assert "connected_socials" in result
        assert len(result["platforms_found"]) == 2

    async def test_ic_unavailable(self, ic_backend):
        ic_backend.connected_socials = AsyncMock(side_effect=ICUnavailableError(503, "down"))
        registry, _ = _build_registry(ic_backend=ic_backend)
        result = await registry.execute("creator_profile", {
            "action": "connected_socials", "platform": "instagram", "username": "someone",
        })
        assert result["error"] == "ic_unavailable"

    async def test_unexpected_error(self, ic_backend):
        ic_backend.connected_socials = AsyncMock(side_effect=RuntimeError("boom"))
        registry, _ = _build_registry(ic_backend=ic_backend)
        result = await registry.execute("creator_profile", {
            "action": "connected_socials", "platform": "instagram", "username": "someone",
        })
        assert result["error"] == "ic_unavailable"


# ── manage_ic_creator: check_credits ─────────────────────────────────


class TestCheckICCredits:
    async def test_happy_path(self, ic_backend):
        registry, _ = _build_registry(ic_backend=ic_backend)
        result = await registry.execute("creator_profile", {
            "action": "check_credits",
        })
        assert "42.5" in result["summary"]
        assert result["credits"]["credits_left"] == "42.5"

    async def test_error(self, ic_backend):
        ic_backend.get_credits = AsyncMock(side_effect=RuntimeError("api error"))
        registry, _ = _build_registry(ic_backend=ic_backend)
        result = await registry.execute("creator_profile", {
            "action": "check_credits",
        })
        assert result["error"] == "ic_unavailable"


# ── manage_ic_creator: invalid action ────────────────────────────────


class TestManageICCreatorInvalidAction:
    async def test_unknown_action(self, ic_backend):
        registry, _ = _build_registry(ic_backend=ic_backend)
        result = await registry.execute("creator_profile", {
            "action": "nonexistent",
        })
        assert result["error"] == "invalid_request"
        assert "Unknown action" in result["summary"]


# ── search_creators IC integration ───────────────────────────────────


class TestSearchCreatorsIC:
    async def test_ic_primary_search(self, ic_backend):
        """IC is used as primary backend for search mode."""
        registry, _ = _build_registry(ic_backend=ic_backend)
        result = await registry.execute("discover_creators", {
            "keywords": "fitness", "platforms": ["instagram"],
        })
        assert "creators" in result
        assert len(result["creators"]) >= 1
        ic_backend.discover.assert_called_once()

    async def test_ic_similar_mode(self, ic_backend):
        """mode=similar uses IC find_similar as primary."""
        registry, _ = _build_registry(ic_backend=ic_backend)
        result = await registry.execute("discover_creators", {
            "mode": "similar",
            "reference_username": "fitness_guru",
            "reference_platform": "instagram",
        })
        assert result["mode"] == "similar"
        assert len(result["creators"]) >= 1
        ic_backend.find_similar.assert_called_once()

    async def test_ic_email_mode(self, ic_backend):
        """mode=email uses IC enrich_email as primary."""
        registry, _ = _build_registry(ic_backend=ic_backend, tier=Tier.PRO)
        result = await registry.execute("discover_creators", {
            "mode": "email", "email": "test@example.com",
        })
        assert result["mode"] == "email"
        assert len(result["creators"]) >= 1
        ic_backend.enrich_email.assert_called_once()

class TestSearchCreatorsIC422Handling:
    async def test_ic_empty_response_returns_empty(self, ic_backend):
        """IC returns {} on 422 -- search returns empty results."""
        ic_backend.discover = AsyncMock(return_value={})
        registry, _ = _build_registry(ic_backend=ic_backend)
        result = await registry.execute("discover_creators", {
            "keywords": "fitness", "platforms": ["instagram"],
        })
        assert result["creators"] == []

    async def test_ic_empty_accounts_list(self, ic_backend):
        """IC returns {accounts: []} -- no fallback, just empty results."""
        ic_backend.discover = AsyncMock(return_value={"accounts": []})
        registry, _ = _build_registry(ic_backend=ic_backend)
        result = await registry.execute("discover_creators", {
            "keywords": "fitness", "platforms": ["instagram"],
        })
        assert result["creators"] == []


# ── Engagement rate normalization ────────────────────────────────────


class TestEngagementRateNormalization:
    async def test_ic_engagement_percent_normalized(self, ic_backend):
        """IC engagement_percent (4.5%) normalized to 0.045."""
        registry, _ = _build_registry(ic_backend=ic_backend)
        result = await registry.execute("discover_creators", {
            "keywords": "fitness", "platforms": ["instagram"],
        })
        creators = result["creators"]
        assert len(creators) >= 1
        # 4.5% -> 0.045
        assert creators[0]["engagement_rate"] == pytest.approx(0.045, abs=0.001)

    async def test_ic_none_engagement_preserved(self, ic_backend):
        """None engagement_percent stays None (not 0)."""
        ic_backend.discover = AsyncMock(return_value={
            "accounts": [{"profile": {"username": "test", "engagement_percent": None, "followers": 100}}],
        })
        registry, _ = _build_registry(ic_backend=ic_backend)
        result = await registry.execute("discover_creators", {
            "keywords": "test", "platforms": ["instagram"],
        })
        assert result["creators"][0]["engagement_rate"] is None

    async def test_ic_zero_engagement_preserved(self, ic_backend):
        """0% engagement stays 0.0 (not None)."""
        ic_backend.discover = AsyncMock(return_value={
            "accounts": [{"profile": {"username": "test", "engagement_percent": 0, "followers": 100}}],
        })
        registry, _ = _build_registry(ic_backend=ic_backend)
        result = await registry.execute("discover_creators", {
            "keywords": "test", "platforms": ["instagram"],
        })
        assert result["creators"][0]["engagement_rate"] == 0.0


# ── post_url domain validation ───────────────────────────────────────


class TestPostUrlValidation:
    async def test_valid_instagram_url(self, ic_backend):
        registry, _ = _build_registry(ic_backend=ic_backend)
        result = await registry.execute("creator_profile", {
            "action": "get_post", "platform": "instagram", "username": "user",
            "post_url": "https://www.instagram.com/p/abc123",
        })
        assert "error" not in result

    async def test_valid_tiktok_url(self, ic_backend):
        registry, _ = _build_registry(ic_backend=ic_backend)
        result = await registry.execute("creator_profile", {
            "action": "get_post", "platform": "tiktok", "username": "user",
            "post_url": "https://www.tiktok.com/@user/video/123",
        })
        assert "error" not in result

    async def test_valid_youtube_url(self, ic_backend):
        registry, _ = _build_registry(ic_backend=ic_backend)
        result = await registry.execute("creator_profile", {
            "action": "get_post", "platform": "youtube", "username": "user",
            "post_url": "https://www.youtube.com/watch?v=abc",
        })
        assert "error" not in result

    async def test_hallucinated_url_rejected(self, ic_backend):
        registry, _ = _build_registry(ic_backend=ic_backend)
        result = await registry.execute("creator_profile", {
            "action": "get_post", "platform": "instagram", "username": "user",
            "post_url": "https://hallucinated-site.com/p/abc",
        })
        assert result["error"] == "invalid_parameter"
        ic_backend.get_post_details.assert_not_called()
