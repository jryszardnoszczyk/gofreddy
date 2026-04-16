"""Tests for Influencers.club (IC) search backend.

Uses respx (httpx mock transport). The backend and respx router are
created together so the httpx client is created INSIDE the mock context.
"""

import httpx
import pytest
import respx

from src.search.ic_backend import ICBackend
from src.search.exceptions import ICUnavailableError

IC_BASE_URL = "https://api-dashboard.influencers.club"

_CREDITS_RESPONSE = {"credits_left": "11850.50"}

_DISCOVERY_RESPONSE = {
    "total": 2,
    "limit": 50,
    "credits_left": "11849.48",
    "accounts": [
        {
            "user_id": "12345",
            "profile": {
                "username": "fitness_jane",
                "full_name": "Jane Doe",
                "picture": "https://example.com/pic.jpg",
                "followers": 50000,
                "engagement_percent": 3.5,
            },
        },
        {
            "user_id": "67890",
            "profile": {
                "username": "health_coach",
                "full_name": "John Smith",
                "picture": None,
                "followers": 120000,
                "engagement_percent": 2.1,
            },
        },
    ],
}

_ENRICH_FULL_RESPONSE = {
    "credits_left": "11848.48",
    "email": "jane@example.com",
    "location": "New York, US",
    "first_name": "Jane",
    "has_brand_deals": True,
    "is_business": False,
    "platforms": {
        "instagram": {
            "userid": "12345",
            "username": "fitness_jane",
            "full_name": "Jane Doe",
            "follower_count": 50000,
            "engagement_percent": 3.5,
            "niche_class": "Health & Fitness",
            "niche_sub_class": "Yoga",
            "income_last_90_days_min": 1500.0,
            "income_last_90_days_max": 3000.0,
        },
    },
}

_ENRICH_RAW_RESPONSE = {
    "credits_left": "11848.45",
    "data": {"raw": "platform_native_data"},
}

_CONTENT_RESPONSE = {
    "credits_left": "11848.42",
    "posts": [
        {
            "url": "https://instagram.com/p/abc123",
            "thumbnail": "https://example.com/thumb.jpg",
            "likes": 5000,
            "comments": 200,
            "caption": "Morning yoga session",
        },
    ],
}

_SIMILAR_RESPONSE = {
    "credits_left": "11849.00",
    "accounts": [
        {
            "user_id": "99999",
            "profile": {
                "username": "yoga_master",
                "full_name": "Yoga Master",
                "followers": 75000,
            },
        },
    ],
}


@pytest.fixture
async def backend_and_router():
    """Async fixture — creates backend INSIDE respx context so transport is mocked."""
    with respx.mock(base_url=IC_BASE_URL) as router:
        # Health check endpoint (called during __aenter__)
        router.get("/public/v1/accounts/credits/").respond(200, json=_CREDITS_RESPONSE)
        b = ICBackend(api_key="test-api-key", base_url=IC_BASE_URL)
        await b.__aenter__()
        yield b, router
        await b.__aexit__(None, None, None)


@pytest.fixture
async def backend(backend_and_router):
    return backend_and_router[0]


@pytest.fixture
async def router(backend_and_router):
    return backend_and_router[1]


class TestDiscover:
    async def test_basic_discovery(self, backend, router):
        router.post("/public/v1/discovery/").respond(200, json=_DISCOVERY_RESPONSE)
        result = await backend.discover("instagram")
        assert result["total"] == 2
        assert len(result["accounts"]) == 2
        assert result["accounts"][0]["profile"]["username"] == "fitness_jane"

    async def test_discovery_with_filters(self, backend, router):
        router.post("/public/v1/discovery/").respond(200, json=_DISCOVERY_RESPONSE)
        filters = {
            "number_of_followers": {"min": 10000, "max": 100000},
            "engagement_percent": {"min": 2.0},
            "ai_search": "fitness influencer who does yoga",
        }
        result = await backend.discover("instagram", filters, limit=20)
        assert result["total"] == 2

    async def test_discovery_invalid_platform(self, backend):
        with pytest.raises(ValueError, match="Unsupported platform"):
            await backend.discover("snapchat")

    async def test_discovery_page_limit_capped(self, backend, router):
        """Limit is capped at 50 (IC max)."""
        route = router.post("/public/v1/discovery/").respond(200, json=_DISCOVERY_RESPONSE)
        await backend.discover("instagram", limit=100)
        request = route.calls[0].request
        body = request.content
        import json
        parsed = json.loads(body)
        assert parsed["paging"]["limit"] == 50


class TestEnrichFull:
    async def test_enrich_full(self, backend, router):
        router.post("/public/v1/creators/enrich/handle/full/").respond(200, json=_ENRICH_FULL_RESPONSE)
        result = await backend.enrich_full("instagram", "fitness_jane")
        assert result["email"] == "jane@example.com"
        assert result["platforms"]["instagram"]["niche_class"] == "Health & Fitness"

    async def test_enrich_full_invalid_handle(self, backend):
        with pytest.raises(ValueError, match="Invalid handle"):
            await backend.enrich_full("instagram", "../../../etc/passwd")


class TestEnrichRaw:
    async def test_enrich_raw(self, backend, router):
        router.post("/public/v1/creators/enrich/handle/raw/").respond(200, json=_ENRICH_RAW_RESPONSE)
        result = await backend.enrich_raw("instagram", "fitness_jane")
        assert result["data"]["raw"] == "platform_native_data"


class TestContent:
    async def test_get_content(self, backend, router):
        router.post("/public/v1/creators/content/posts/").respond(200, json=_CONTENT_RESPONSE)
        result = await backend.get_content("instagram", "fitness_jane")
        assert len(result["posts"]) == 1
        assert result["posts"][0]["likes"] == 5000

    async def test_get_content_invalid_platform(self, backend):
        """Content API only supports instagram, tiktok, youtube."""
        with pytest.raises(ValueError, match="Unsupported platform"):
            await backend.get_content("twitter", "some_user")

    async def test_get_post_details(self, backend, router):
        details_response = {"credits_left": "11848.39", "data": {"transcript": "hello world"}}
        router.post("/public/v1/creators/content/details/").respond(200, json=details_response)
        result = await backend.get_post_details(
            "instagram", "fitness_jane", "https://instagram.com/p/abc123", content_type="transcript"
        )
        assert result["data"]["transcript"] == "hello world"

    async def test_invalid_content_type(self, backend):
        with pytest.raises(ValueError, match="Invalid content_type"):
            await backend.get_post_details("instagram", "user", "https://x.com/p/1", content_type="invalid")


class TestSimilar:
    async def test_find_similar(self, backend, router):
        router.post("/public/v1/discovery/creators/similar/").respond(200, json=_SIMILAR_RESPONSE)
        result = await backend.find_similar("instagram", "fitness_jane", limit=10)
        assert len(result["accounts"]) == 1
        assert result["accounts"][0]["profile"]["username"] == "yoga_master"


class TestAudienceOverlap:
    async def test_audience_overlap(self, backend, router):
        overlap_response = {"credits_left": "11847.48", "overlap": 0.35}
        router.post("/public/v1/creators/audience/overlap/").respond(200, json=overlap_response)
        result = await backend.audience_overlap("instagram", ["fitness_jane", "yoga_master"])
        assert result["overlap"] == 0.35

    async def test_audience_overlap_too_few_handles(self, backend):
        with pytest.raises(ValueError, match="2-10 handles"):
            await backend.audience_overlap("instagram", ["only_one"])

    async def test_audience_overlap_too_many_handles(self, backend):
        with pytest.raises(ValueError, match="2-10 handles"):
            handles = [f"user_{i}" for i in range(11)]
            await backend.audience_overlap("instagram", handles)


class TestConnectedSocials:
    async def test_connected_socials(self, backend, router):
        socials_response = {
            "credits_left": "11848.00",
            "socials": [
                {"platform": "youtube", "handle": "fitness_jane_yt"},
                {"platform": "tiktok", "handle": "fitness_jane_tt"},
            ],
        }
        router.post("/public/v1/creators/socials/").respond(200, json=socials_response)
        result = await backend.connected_socials("instagram", "fitness_jane")
        assert len(result["socials"]) == 2


class TestEnrichEmail:
    async def test_enrich_email_advanced(self, backend, router):
        email_response = {"credits_left": "11846.48", "platforms": {"instagram": {"username": "found_user"}}}
        router.post("/public/v1/creators/enrich/email/advanced/").respond(200, json=email_response)
        result = await backend.enrich_email("jane@example.com")
        assert result["platforms"]["instagram"]["username"] == "found_user"

    async def test_enrich_email_basic(self, backend, router):
        email_response = {"credits_left": "11849.90", "platforms": {}}
        router.post("/public/v1/creators/enrich/email/").respond(200, json=email_response)
        result = await backend.enrich_email("jane@example.com", enrich_type="basic")
        assert "platforms" in result

    async def test_enrich_email_invalid_type(self, backend):
        with pytest.raises(ValueError, match="Invalid enrich_type"):
            await backend.enrich_email("jane@example.com", enrich_type="super")


class TestGetCredits:
    async def test_get_credits(self, backend, router):
        # credits endpoint was already mocked in fixture, but add a fresh one
        router.get("/public/v1/accounts/credits/").respond(200, json={"credits_left": "9999.99"})
        result = await backend.get_credits()
        assert result["credits_left"] == "9999.99"


class TestGetClassifier:
    async def test_get_locations(self, backend, router):
        locations_response = [{"id": 1, "name": "United States"}, {"id": 2, "name": "United Kingdom"}]
        router.get("/public/v1/discovery/classifier/locations/instagram/").respond(200, json=locations_response)
        result = await backend.get_classifier("locations", platform="instagram")
        assert len(result) == 2

    async def test_get_languages(self, backend, router):
        languages_response = [{"code": "en", "name": "English"}]
        router.get("/public/v1/discovery/classifier/languages/").respond(200, json=languages_response)
        result = await backend.get_classifier("languages")
        assert len(result) == 1

    async def test_invalid_classifier_type(self, backend):
        with pytest.raises(ValueError, match="Invalid classifier_type"):
            await backend.get_classifier("invalid_type")


class TestCircuitBreaker:
    async def test_circuit_breaker_opens_after_failures(self, backend, router):
        """Circuit breaker should open after 3 consecutive failures (across retries)."""
        router.post("/public/v1/discovery/").respond(500, text="Server Error")
        # First call: 3 retries = 3 circuit breaker failures => breaker opens
        with pytest.raises(ICUnavailableError):
            await backend.discover("instagram")
        # Next call hits the open circuit breaker immediately
        with pytest.raises(ICUnavailableError) as exc_info:
            await backend.discover("instagram")
        assert exc_info.value.detail == "Circuit breaker open — IC temporarily disabled"

    async def test_circuit_breaker_recovers(self, backend, router):
        """Circuit breaker should recover after reset timeout."""
        router.post("/public/v1/discovery/").respond(500, text="Server Error")
        with pytest.raises(ICUnavailableError):
            await backend.discover("instagram")
        # Breaker is now open. Force reset by manipulating timeout.
        backend._circuit_breaker._last_failure_time = 0.0
        # Now it should be in HALF_OPEN and allow a request
        router.post("/public/v1/discovery/").respond(200, json=_DISCOVERY_RESPONSE)
        result = await backend.discover("instagram")
        assert result["total"] == 2


class TestRetry:
    async def test_retry_on_429(self, backend, router):
        """Should retry on 429 with Retry-After header."""
        route = router.post("/public/v1/discovery/")
        route.side_effect = [
            httpx.Response(429, headers={"Retry-After": "0.01"}, text="Rate limited"),
            httpx.Response(200, json=_DISCOVERY_RESPONSE),
        ]
        result = await backend.discover("instagram")
        assert result["total"] == 2

    async def test_retry_on_500(self, backend, router):
        """Should retry on 500."""
        route = router.post("/public/v1/discovery/")
        route.side_effect = [
            httpx.Response(500, text="Server Error"),
            httpx.Response(200, json=_DISCOVERY_RESPONSE),
        ]
        result = await backend.discover("instagram")
        assert result["total"] == 2

    async def test_retry_on_502(self, backend, router):
        """Should retry on 502."""
        route = router.post("/public/v1/discovery/")
        route.side_effect = [
            httpx.Response(502, text="Bad Gateway"),
            httpx.Response(200, json=_DISCOVERY_RESPONSE),
        ]
        result = await backend.discover("instagram")
        assert result["total"] == 2

    async def test_retry_on_503(self, backend, router):
        """Should retry on 503."""
        route = router.post("/public/v1/discovery/")
        route.side_effect = [
            httpx.Response(503, text="Service Unavailable"),
            httpx.Response(200, json=_DISCOVERY_RESPONSE),
        ]
        result = await backend.discover("instagram")
        assert result["total"] == 2

    async def test_fail_immediately_on_401(self, backend, router):
        """Should NOT retry on 401 — raise immediately."""
        router.post("/public/v1/discovery/").respond(401, text="Unauthorized")
        with pytest.raises(ICUnavailableError, match="IC unavailable"):
            await backend.discover("instagram")

    async def test_fail_immediately_on_403(self, backend, router):
        """Should NOT retry on 403 — raise immediately."""
        router.post("/public/v1/discovery/").respond(403, text="Forbidden")
        with pytest.raises(ICUnavailableError, match="IC unavailable"):
            await backend.discover("instagram")

    async def test_422_returns_empty_dict(self, backend, router):
        """422 validation error returns empty dict (not retried)."""
        router.post("/public/v1/discovery/").respond(422, text='{"detail": "invalid filter"}')
        result = await backend.discover("instagram")
        assert result == {}

    async def test_exhausted_retries_raises(self, backend, router):
        """After exhausting retries on 500, should raise ICUnavailableError."""
        router.post("/public/v1/discovery/").respond(500, text="Server Error")
        with pytest.raises(ICUnavailableError, match="IC unavailable"):
            await backend.discover("instagram")


class TestCreditsLeftParsing:
    async def test_credits_left_string(self, backend, router):
        """credits_left comes as a string from IC — should be logged correctly."""
        response = {**_DISCOVERY_RESPONSE, "credits_left": "5000.75"}
        router.post("/public/v1/discovery/").respond(200, json=response)
        result = await backend.discover("instagram")
        assert result["credits_left"] == "5000.75"

    async def test_credits_left_missing(self, backend, router):
        """Response without credits_left should not crash."""
        response = {"total": 0, "accounts": []}
        router.post("/public/v1/discovery/").respond(200, json=response)
        result = await backend.discover("instagram")
        assert result["total"] == 0

    async def test_credits_left_non_numeric(self, backend, router):
        """Non-numeric credits_left should not crash."""
        response = {**_DISCOVERY_RESPONSE, "credits_left": "unlimited"}
        router.post("/public/v1/discovery/").respond(200, json=response)
        result = await backend.discover("instagram")
        # Should not raise — just log '?' for credits_left
        assert result["total"] == 2


class TestEngagementPercent:
    async def test_engagement_over_100(self, backend, router):
        """IC engagement_percent can exceed 100 — should be handled gracefully."""
        response = {
            "total": 1,
            "credits_left": "11849.49",
            "accounts": [
                {
                    "user_id": "viral_creator",
                    "profile": {
                        "username": "viral_creator",
                        "full_name": "Viral Creator",
                        "followers": 1000,
                        "engagement_percent": 150.0,
                    },
                },
            ],
        }
        router.post("/public/v1/discovery/").respond(200, json=response)
        result = await backend.discover("instagram")
        assert result["accounts"][0]["profile"]["engagement_percent"] == 150.0


class TestValidation:
    async def test_invalid_handle_path_traversal(self, backend):
        with pytest.raises(ValueError, match="Invalid handle"):
            await backend.enrich_full("instagram", "../../admin")

    async def test_invalid_handle_spaces(self, backend):
        with pytest.raises(ValueError, match="Invalid handle"):
            await backend.enrich_full("instagram", "has spaces")

    async def test_valid_handle_with_underscore(self, backend, router):
        router.post("/public/v1/creators/enrich/handle/full/").respond(200, json=_ENRICH_FULL_RESPONSE)
        result = await backend.enrich_full("instagram", "fitness_jane_123")
        assert result["email"] == "jane@example.com"

    async def test_valid_handle_with_dot(self, backend, router):
        router.post("/public/v1/creators/enrich/handle/full/").respond(200, json=_ENRICH_FULL_RESPONSE)
        result = await backend.enrich_full("instagram", "jane.doe")
        assert "email" in result

    async def test_empty_api_key_raises(self):
        with pytest.raises(ValueError, match="API key is required"):
            ICBackend(api_key="")


class TestNetworkErrors:
    async def test_network_error_retries_then_raises(self, backend, router):
        """Network errors should retry then raise ICUnavailableError."""
        router.post("/public/v1/discovery/").mock(side_effect=httpx.ConnectError("Connection refused"))
        with pytest.raises(ICUnavailableError, match="IC unavailable"):
            await backend.discover("instagram")

    async def test_timeout_retries_then_raises(self, backend, router):
        """Timeout errors should retry then raise ICUnavailableError."""
        router.post("/public/v1/discovery/").mock(side_effect=httpx.ReadTimeout("Read timeout"))
        with pytest.raises(ICUnavailableError, match="IC unavailable"):
            await backend.discover("instagram")


class TestNotInitialized:
    async def test_request_before_init_raises(self):
        """Calling methods before __aenter__ should raise RuntimeError."""
        b = ICBackend(api_key="test-key")
        with pytest.raises(RuntimeError, match="not initialized"):
            await b.discover("instagram")


class TestAllPlatforms:
    """Test all 6 discovery platforms work."""

    @pytest.mark.parametrize("platform", ["instagram", "youtube", "tiktok", "twitch", "twitter", "onlyfans"])
    async def test_discovery_all_platforms(self, backend, router, platform):
        router.post("/public/v1/discovery/").respond(200, json=_DISCOVERY_RESPONSE)
        result = await backend.discover(platform)
        assert result["total"] == 2
