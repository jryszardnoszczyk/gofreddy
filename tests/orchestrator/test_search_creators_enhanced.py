"""Tests for enhanced discover_creators tool with dual-backend dispatch.

Covers all 4 modes (search, similar, email, network), merge logic,
error paths, partial failure, tier gating, and bot score enrichment.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.billing.tiers import Tier
from src.common.enums import Platform
from src.monitoring.models import DataSource, XpozUser
from src.monitoring.exceptions import MentionFetchError
from src.orchestrator.tools import build_default_registry
from src.search.exceptions import ICUnavailableError


# ── Fixtures ────────────────────────────────────────────────────────


def _make_xpoz_user(
    username: str = "alice_test",
    platform: DataSource = DataSource.TWITTER,
    follower_count: int = 10000,
    is_inauthentic: bool | None = False,
    inauthentic_prob_score: float | None = 0.15,
    relevance_score: float | None = 0.8,
) -> XpozUser:
    return XpozUser(
        platform=platform,
        user_id=f"xpoz-{username}",
        username=username,
        display_name=f"Display {username}",
        bio="Test bio",
        follower_count=follower_count,
        following_count=500,
        post_count=200,
        is_verified=True,
        profile_image_url="https://img.example.com/avatar.jpg",
        is_inauthentic=is_inauthentic,
        inauthentic_prob_score=inauthentic_prob_score,
        relevance_score=relevance_score,
        relevant_posts_count=10,
        relevant_engagement_sum=5000,
    )


def _mock_xpoz_adapters(
    twitter_users: list[XpozUser] | None = None,
    instagram_users: list[XpozUser] | None = None,
    reddit_users: list[XpozUser] | None = None,
    connections: list[XpozUser] | None = None,
) -> dict[str, MagicMock]:
    adapters: dict[str, MagicMock] = {}
    for plat, users in [("twitter", twitter_users), ("instagram", instagram_users), ("reddit", reddit_users)]:
        if users is not None:
            adapter = MagicMock()
            adapter.search_users_by_keywords = AsyncMock(return_value=users)
            adapter.get_user_connections = AsyncMock(return_value=connections or [])
            adapters[plat] = adapter
    return adapters


def _mock_ic_backend(
    discover_accounts: list[dict] | None = None,
    find_similar_accounts: list[dict] | None = None,
):
    """Create a mock IC backend with default responses."""
    backend = MagicMock()
    accounts = discover_accounts or []
    backend.discover = AsyncMock(return_value={"accounts": accounts})
    backend.find_similar = AsyncMock(return_value={
        "accounts": find_similar_accounts or [],
    })
    backend.enrich_full = AsyncMock(return_value={})
    backend.enrich_email = AsyncMock(return_value={
        "result": {
            "instagram": {
                "username": "found_creator",
                "full_name": "Found Creator",
                "follower_count": 25000,
                "engagement_percent": 3.0,
            },
        },
    })
    backend.get_credits = AsyncMock(return_value={"credits_left": "42.5"})
    return backend


def _make_ic_account(
    username: str = "alice_test",
    followers: int = 15000,
    engagement_percent: float = 3.5,
    is_verified: bool = True,
) -> dict:
    return {
        "profile": {
            "username": username,
            "full_name": f"IC {username}",
            "picture": "https://cdn.example.com/avatar.jpg",
            "followers": followers,
            "engagement_percent": engagement_percent,
            "is_verified": is_verified,
        },
    }


def _build_registry(
    xpoz_adapters=None, ic_backend=None, tier=Tier.FREE, fetchers=None,
):
    registry, restricted = build_default_registry(
        search_service=None,
        fetchers=fetchers,
        tier=tier,
        ic_backend=ic_backend,
        xpoz_adapters=xpoz_adapters,
    )
    return registry, restricted


# ── Mode: Search ────────────────────────────────────────────────────


class TestSearchModeXpozOnly:
    """1. mode=search, Xpoz-only platforms (Twitter, Reddit)."""

    async def test_xpoz_only_platforms_no_ic(self):
        xpoz_user = _make_xpoz_user(platform=DataSource.TWITTER)
        xpoz = _mock_xpoz_adapters(twitter_users=[xpoz_user])
        registry, _ = _build_registry(xpoz_adapters=xpoz)

        result = await registry.execute("discover_creators", {
            "keywords": "fitness",
            "platforms": ["twitter"],
        })

        assert result["mode"] == "search"
        assert len(result["creators"]) == 1
        assert result["creators"][0]["platform"] == "twitter"
        assert result["creators"][0]["data_source"] == "xpoz"
        assert result["creators"][0]["is_inauthentic"] is False
        assert result["creators"][0]["inauthentic_prob_score"] == 0.15

    async def test_bot_scores_populated(self):
        """12. Twitter creators from Xpoz have bot detection fields."""
        xpoz_user = _make_xpoz_user(
            is_inauthentic=True,
            inauthentic_prob_score=0.85,
        )
        xpoz = _mock_xpoz_adapters(twitter_users=[xpoz_user])
        registry, _ = _build_registry(xpoz_adapters=xpoz)

        result = await registry.execute("discover_creators", {
            "keywords": "test",
            "platforms": ["twitter"],
        })

        creator = result["creators"][0]
        assert creator["is_inauthentic"] is True
        assert creator["inauthentic_prob_score"] == 0.85


class TestSearchModeICOnly:
    """2. mode=search, IC-only platforms (TikTok, YouTube)."""

    async def test_ic_only_platforms_no_xpoz(self):
        ic = _mock_ic_backend(discover_accounts=[
            _make_ic_account(username="tiktok_creator"),
        ])
        registry, _ = _build_registry(ic_backend=ic)

        result = await registry.execute("discover_creators", {
            "keywords": "cooking",
            "platforms": ["tiktok"],
        })

        assert result["mode"] == "search"
        assert len(result["creators"]) >= 1
        assert result["creators"][0]["data_source"] == "influencersclub"
        # Bot fields should be None for IC-only
        assert result["creators"][0]["is_inauthentic"] is None

    async def test_relevance_sort_keeps_provider_order_when_scores_are_missing(self):
        ic = _mock_ic_backend(discover_accounts=[
            _make_ic_account(username="relevant_first", followers=5000),
            _make_ic_account(username="bigger_but_second", followers=50000),
        ])
        registry, _ = _build_registry(ic_backend=ic)

        result = await registry.execute("discover_creators", {
            "keywords": "cooking creators",
            "platforms": ["tiktok"],
            "sort_by": "RELEVANCE",
        })

        assert [creator["username"] for creator in result["creators"][:2]] == [
            "relevant_first",
            "bigger_but_second",
        ]

    async def test_keywords_narrow_to_explicit_platform_hint(self):
        ic = _mock_ic_backend(discover_accounts=[
            _make_ic_account(username="chef_tok"),
        ])
        registry, _ = _build_registry(ic_backend=ic)

        await registry.execute("discover_creators", {
            "keywords": "Find cooking creators on TikTok",
            "platforms": ["instagram", "youtube"],
        })

        requested_platforms = [call.args[0] for call in ic.discover.await_args_list]
        assert requested_platforms == ["tiktok"]

    async def test_fetcher_fallback_stays_on_requested_tiktok_platform(self):
        ic = _mock_ic_backend(discover_accounts=[])
        tiktok_fetcher = AsyncMock()
        tiktok_fetcher.search_keyword = AsyncMock(return_value=[
            {
                "aweme_id": "video-1",
                "desc": "cooking creator recipe ideas",
                "author": {
                    "uniqueId": "chef_tok",
                    "nickname": "Chef Tok",
                    "signature": "Cooking videos",
                    "uid": "user-1",
                },
                "authorStats": {
                    "followerCount": 42000,
                },
            },
        ])
        registry, _ = _build_registry(
            ic_backend=ic,
            fetchers={Platform.TIKTOK: tiktok_fetcher},
        )

        result = await registry.execute("discover_creators", {
            "keywords": "Find cooking creators on TikTok",
            "platforms": ["tiktok"],
        })

        assert result["creators"][0]["platform"] == "tiktok"
        assert result["creators"][0]["username"] == "chef_tok"
        assert result["creators"][0]["data_source"] == "fetcher_search"
        assert "instagram" not in result["summary"]


class TestSearchModeDualBackend:
    """3. mode=search, Instagram (dual-backend) — merge."""

    async def test_instagram_merge_produces_merged_data_source(self):
        xpoz_user = _make_xpoz_user(
            username="shared_user",
            platform=DataSource.INSTAGRAM,
            is_inauthentic=False,
            inauthentic_prob_score=0.2,
            relevance_score=0.9,
        )
        xpoz = _mock_xpoz_adapters(instagram_users=[xpoz_user])
        ic = _mock_ic_backend(discover_accounts=[
            _make_ic_account(username="shared_user", engagement_percent=3.5),
        ])
        registry, _ = _build_registry(ic_backend=ic, xpoz_adapters=xpoz)

        result = await registry.execute("discover_creators", {
            "keywords": "fitness",
            "platforms": ["instagram"],
        })

        assert result["mode"] == "search"
        # Deduplication: one entry, not two
        usernames = [c["username"] for c in result["creators"]]
        assert usernames.count("shared_user") == 1
        merged = result["creators"][0]
        assert merged["data_source"] == "merged"
        # Enriched with Xpoz bot data
        assert merged["inauthentic_prob_score"] == 0.2
        assert merged["relevance_score"] == 0.9
        # Kept IC engagement data
        assert merged["engagement_rate"] == 0.035  # 3.5% / 100 = decimal


class TestSearchModePartialFailure:
    """4. mode=search, partial failure — one backend raises."""

    async def test_partial_results_when_one_backend_fails(self):
        xpoz = _mock_xpoz_adapters(twitter_users=[_make_xpoz_user()])
        ic = _mock_ic_backend()
        # Make IC raise
        ic.discover = AsyncMock(side_effect=ICUnavailableError(503, "down"))
        registry, _ = _build_registry(ic_backend=ic, xpoz_adapters=xpoz)

        result = await registry.execute("discover_creators", {
            "keywords": "test",
            "platforms": ["twitter", "instagram"],
        })

        assert result["partial_results"] is True
        assert len(result["creators"]) >= 1  # Xpoz results survived


class TestSearchModeAllFail:
    """19. mode=search, all backends fail."""

    async def test_all_backends_fail_returns_error_summary(self):
        xpoz = _mock_xpoz_adapters(twitter_users=[])
        # Make Xpoz raise
        xpoz["twitter"].search_users_by_keywords = AsyncMock(
            side_effect=MentionFetchError("Xpoz down")
        )
        ic = _mock_ic_backend()
        ic.discover = AsyncMock(
            side_effect=ICUnavailableError(503, "down")
        )
        registry, _ = _build_registry(ic_backend=ic, xpoz_adapters=xpoz)

        result = await registry.execute("discover_creators", {
            "keywords": "test",
            "platforms": ["twitter", "instagram"],
        })

        assert result["creators"] == []
        assert "error" in result["summary"].lower() or "try again" in result["summary"].lower()


class TestSearchModeEmptyResults:
    """13. Empty results from both backends."""

    async def test_empty_results_returns_no_creators(self):
        xpoz = _mock_xpoz_adapters(twitter_users=[])
        ic = _mock_ic_backend(discover_accounts=[])
        registry, _ = _build_registry(ic_backend=ic, xpoz_adapters=xpoz)

        result = await registry.execute("discover_creators", {
            "keywords": "nonexistent-topic-xyz",
            "platforms": ["twitter", "instagram"],
        })

        assert result["creators"] == []
        assert result["digest"]["total"] == 0


class TestSearchModeXpozAdapterUnavailable:
    """16. xpoz_adapters=None — IC-only results."""

    async def test_no_xpoz_adapters_falls_back_to_ic(self):
        ic = _mock_ic_backend(discover_accounts=[
            _make_ic_account(username="ic_only"),
        ])
        registry, _ = _build_registry(ic_backend=ic, xpoz_adapters=None)

        result = await registry.execute("discover_creators", {
            "keywords": "fitness",
            "platforms": ["instagram"],
        })

        assert len(result["creators"]) >= 1
        assert result["creators"][0]["data_source"] == "influencersclub"
        assert "error" not in result


# ── Mode: Similar ───────────────────────────────────────────────────


class TestSimilarMode:
    """5. mode=similar: calls IC find_similar."""

    async def test_similar_returns_normalized_results(self):
        ic = _mock_ic_backend(find_similar_accounts=[
            _make_ic_account(username="lookalike_1"),
        ])
        registry, _ = _build_registry(ic_backend=ic)

        result = await registry.execute("discover_creators", {
            "mode": "similar",
            "reference_username": "seed_user",
            "reference_platform": "instagram",
        })

        assert result["mode"] == "similar"
        assert len(result["creators"]) >= 1
        assert result["similar_to"] == "seed_user"
        ic.find_similar.assert_called_once()

    async def test_similar_twitter_without_ic_returns_unavailable(self):
        """6. mode=similar, Twitter — no IC backend for twitter similar."""
        xpoz = _mock_xpoz_adapters(twitter_users=[])
        registry, _ = _build_registry(xpoz_adapters=xpoz)

        result = await registry.execute("discover_creators", {
            "mode": "similar",
            "reference_username": "test",
            "reference_platform": "twitter",
        })

        assert result["error"] == "providers_unavailable"

    async def test_similar_missing_params(self):
        ic = _mock_ic_backend()
        registry, _ = _build_registry(ic_backend=ic)

        result = await registry.execute("discover_creators", {
            "mode": "similar",
        })

        assert result["error"] == "missing_parameter"


# ── Mode: Email ─────────────────────────────────────────────────────


class TestEmailMode:
    """7-8, 17-18. mode=email tests."""

    async def test_email_returns_results(self):
        """7. mode=email calls IC email lookup."""
        ic = _mock_ic_backend()
        registry, _ = _build_registry(ic_backend=ic, tier=Tier.PRO)

        result = await registry.execute("discover_creators", {
            "mode": "email",
            "email": "creator@example.com",
        })

        assert result["mode"] == "email"
        assert len(result["creators"]) >= 1
        ic.enrich_email.assert_called_once()

    async def test_email_missing_param(self):
        """8. mode=email, missing param."""
        ic = _mock_ic_backend()
        registry, _ = _build_registry(ic_backend=ic, tier=Tier.PRO)

        result = await registry.execute("discover_creators", {
            "mode": "email",
        })

        assert result["error"] == "missing_parameter"

    async def test_email_free_tier_blocked(self):
        """17. mode=email, free tier returns tier_required error."""
        ic = _mock_ic_backend()
        registry, _ = _build_registry(ic_backend=ic, tier=Tier.FREE)

        result = await registry.execute("discover_creators", {
            "mode": "email",
            "email": "test@example.com",
        })

        assert result["error"] == "tier_required"

    async def test_email_invalid_format(self):
        """18. mode=email, invalid format."""
        ic = _mock_ic_backend()
        registry, _ = _build_registry(ic_backend=ic, tier=Tier.PRO)

        result = await registry.execute("discover_creators", {
            "mode": "email",
            "email": "not-an-email",
        })

        assert result["error"] == "invalid_parameter"


# ── Mode: Network ───────────────────────────────────────────────────


class TestNetworkMode:
    """9-11. mode=network tests."""

    async def test_network_followers(self):
        """9. mode=network, followers."""
        connections = [_make_xpoz_user(username="follower_1", platform=DataSource.TWITTER)]
        xpoz = _mock_xpoz_adapters(twitter_users=[], connections=connections)
        registry, _ = _build_registry(xpoz_adapters=xpoz)

        result = await registry.execute("discover_creators", {
            "mode": "network",
            "reference_username": "target_user",
            "reference_platform": "twitter",
            "connection_type": "followers",
        })

        assert result["mode"] == "network"
        assert len(result["connections"]) == 1
        assert result["connection_type"] == "followers"
        xpoz["twitter"].get_user_connections.assert_called_once()

    async def test_network_invalid_platform_tiktok(self):
        """10. mode=network, invalid platform (TikTok)."""
        xpoz = _mock_xpoz_adapters(twitter_users=[])
        registry, _ = _build_registry(xpoz_adapters=xpoz)

        result = await registry.execute("discover_creators", {
            "mode": "network",
            "reference_username": "user",
            "reference_platform": "tiktok",
        })

        assert result["error"] == "invalid_platform_mode"

    async def test_network_reddit_invalid(self):
        """11. mode=network, Reddit — invalid."""
        xpoz = _mock_xpoz_adapters(reddit_users=[])
        registry, _ = _build_registry(xpoz_adapters=xpoz)

        result = await registry.execute("discover_creators", {
            "mode": "network",
            "reference_username": "user",
            "reference_platform": "reddit",
        })

        assert result["error"] == "invalid_platform_mode"

    async def test_network_missing_params(self):
        xpoz = _mock_xpoz_adapters(twitter_users=[])
        registry, _ = _build_registry(xpoz_adapters=xpoz)

        result = await registry.execute("discover_creators", {
            "mode": "network",
        })

        assert result["error"] == "missing_parameter"


# ── Merge Logic ─────────────────────────────────────────────────────


class TestMergeCreators:
    """15. _merge_creators dedup."""

    async def test_same_platform_username_deduplicates(self):
        xpoz_user = _make_xpoz_user(
            username="Overlap_User",
            platform=DataSource.INSTAGRAM,
            inauthentic_prob_score=0.3,
            relevance_score=0.7,
        )
        xpoz = _mock_xpoz_adapters(instagram_users=[xpoz_user])
        ic = _mock_ic_backend(discover_accounts=[
            _make_ic_account(username="overlap_user"),
        ])
        registry, _ = _build_registry(ic_backend=ic, xpoz_adapters=xpoz)

        result = await registry.execute("discover_creators", {
            "keywords": "test",
            "platforms": ["instagram"],
        })

        # Case-insensitive dedup: only one entry
        usernames_lower = [c["username"].lower() for c in result["creators"]]
        assert usernames_lower.count("overlap_user") == 1
        merged = [c for c in result["creators"] if c["username"].lower() == "overlap_user"][0]
        assert merged["data_source"] == "merged"


# ── Registration & Gating ──────────────────────────────────────────


class TestRegistration:
    """14. find_similar_creators removed. discover_creators available at all tiers."""

    async def test_find_similar_creators_not_in_registry(self):
        ic = _mock_ic_backend()
        registry, restricted = _build_registry(ic_backend=ic, tier=Tier.PRO)

        assert "find_similar_creators" not in registry.names
        assert "find_similar_creators" not in restricted

    async def test_discover_creators_available_for_free_tier(self):
        ic = _mock_ic_backend()
        registry, restricted = _build_registry(ic_backend=ic, tier=Tier.FREE)

        assert "discover_creators" in registry.names
        assert "discover_creators" not in restricted

    async def test_discover_creators_available_for_pro_tier(self):
        ic = _mock_ic_backend()
        registry, _ = _build_registry(ic_backend=ic, tier=Tier.PRO)

        assert "discover_creators" in registry.names

    async def test_discover_creators_registered_with_xpoz_only(self):
        xpoz = _mock_xpoz_adapters(twitter_users=[])
        registry, _ = _build_registry(xpoz_adapters=xpoz, ic_backend=None)

        assert "discover_creators" in registry.names

    async def test_discover_creators_not_registered_when_no_backends(self):
        registry, _ = _build_registry(xpoz_adapters=None, ic_backend=None)

        assert "discover_creators" not in registry.names
