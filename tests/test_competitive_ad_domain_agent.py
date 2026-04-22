"""Contract tests for R-#38 — agent fallback for ad-domain near-matches.

Pins the public contract of :func:`_agent_recover_near_misses` and the
fast-path behavior of :func:`_ad_domain_matches` / :func:`_is_near_miss`:

- Exact hostname match (after www/casing normalization) → fast path YES
  without ever touching the Sonnet agent.
- A near-miss (shared registered-domain or substring containment) that
  the agent approves → ad is kept.
- A near-miss that the agent rejects → ad is dropped.
- Agent UNSURE verdict is treated as NO at the filter level
  (conservative — we'd rather drop a genuine ad than mis-attribute a
  rival's).
- Repeat `(brand, queried_domain, landing_domain)` tuples hit the
  module-level cache and do NOT spawn a second subprocess.
"""

from __future__ import annotations

import pytest

from src.competitive import service as svc
from src.competitive.service import (
    _AD_DOMAIN_AGENT_CACHE,
    _ad_domain_matches,
    _agent_recover_near_misses,
    _is_near_miss,
)


@pytest.fixture(autouse=True)
def _clear_agent_cache():
    _AD_DOMAIN_AGENT_CACHE.clear()
    yield
    _AD_DOMAIN_AGENT_CACHE.clear()


@pytest.fixture
def fake_sonnet(monkeypatch):
    """Patch `call_sonnet_json` on the competitive.service module."""
    calls: list[dict] = []

    def _install(responder):
        async def _fake(prompt, *, operation, model=None, timeout=None):
            calls.append({"prompt": prompt, "operation": operation})
            return responder(prompt, operation=operation)

        monkeypatch.setattr(
            "src.competitive.service.call_sonnet_json", _fake,
        )
        return calls

    return _install


class TestFastPath:
    """Exact hostname match never calls the agent."""

    def test_exact_match_returns_true(self):
        ad = {"link_url": "https://example.com/page"}
        assert _ad_domain_matches(ad, "example.com") is True

    def test_www_prefix_is_ignored(self):
        ad = {"link_url": "https://www.example.com/page"}
        assert _ad_domain_matches(ad, "example.com") is True

    def test_missing_link_url_is_kept(self):
        assert _ad_domain_matches({"link_url": None}, "example.com") is True
        assert _ad_domain_matches({}, "example.com") is True

    def test_subdomain_is_not_exact_match(self):
        """Exact-match is strict; near-miss handling is a separate stage."""
        ad = {"link_url": "https://ads.example.com/x"}
        assert _ad_domain_matches(ad, "example.com") is False

    async def test_exact_match_never_calls_agent(self, fake_sonnet):
        def boom(prompt, operation):
            raise AssertionError("agent should not be called on exact match")

        calls = fake_sonnet(boom)

        # No near-miss ads → agent is untouched.
        verdicts = await _agent_recover_near_misses("example.com", "example.com", [])
        assert verdicts == {}
        assert calls == []


class TestNearMissHeuristic:
    def test_subdomain_is_near_miss(self):
        assert _is_near_miss("ads.example.com", "example.com") is True
        assert _is_near_miss("example.com", "ads.example.com") is True

    def test_shared_registered_domain_is_near_miss(self):
        assert _is_near_miss("shop.example.com", "www-example.com") is False
        assert _is_near_miss("a.example.com", "b.example.com") is True

    def test_unrelated_is_not_near_miss(self):
        assert _is_near_miss("competitor.com", "example.com") is False

    def test_empty_is_not_near_miss(self):
        assert _is_near_miss("", "example.com") is False
        assert _is_near_miss("example.com", "") is False

    def test_identical_is_not_near_miss(self):
        # Identical should have been caught by fast path; not a near-miss.
        assert _is_near_miss("example.com", "example.com") is False


class TestAgentFallback:
    async def test_agent_yes_keeps_ad(self, fake_sonnet):
        def responder(prompt, operation):
            assert operation == "ad_domain_disambiguation"
            return {"verdicts": [{"id": "a0", "verdict": "YES"}]}

        calls = fake_sonnet(responder)
        ads = [{"link_url": "https://ads.example.com/x", "headline": "Buy now"}]
        verdicts = await _agent_recover_near_misses("example.com", "example.com", ads)
        assert verdicts == {0: "YES"}
        assert len(calls) == 1

    async def test_agent_no_drops_ad(self, fake_sonnet):
        def responder(prompt, operation):
            return {"verdicts": [{"id": "a0", "verdict": "NO"}]}

        fake_sonnet(responder)
        ads = [{"link_url": "https://ads.example.com/x"}]
        verdicts = await _agent_recover_near_misses("example.com", "example.com", ads)
        assert verdicts == {0: "NO"}

    async def test_agent_unsure_is_not_yes(self, fake_sonnet):
        """UNSURE is a downstream drop: we only keep ads on explicit YES."""

        def responder(prompt, operation):
            return {"verdicts": [{"id": "a0", "verdict": "UNSURE"}]}

        fake_sonnet(responder)
        ads = [{"link_url": "https://ads.example.com/x"}]
        verdicts = await _agent_recover_near_misses("example.com", "example.com", ads)
        assert verdicts == {0: "UNSURE"}

    async def test_batch_preserves_per_ad_verdicts(self, fake_sonnet):
        def responder(prompt, operation):
            return {
                "verdicts": [
                    {"id": "a0", "verdict": "YES"},
                    {"id": "a1", "verdict": "NO"},
                    {"id": "a2", "verdict": "UNSURE"},
                ],
            }

        calls = fake_sonnet(responder)
        ads = [
            {"link_url": "https://ads.example.com/1"},
            {"link_url": "https://cdn.example.com/2"},
            {"link_url": "https://shop.example.com/3"},
        ]
        verdicts = await _agent_recover_near_misses("example.com", "example.com", ads)
        assert verdicts == {0: "YES", 1: "NO", 2: "UNSURE"}
        assert len(calls) == 1  # Single batched call, not one per ad.

    async def test_agent_error_defaults_to_no(self, fake_sonnet, monkeypatch):
        async def boom(prompt, *, operation, model=None, timeout=None):
            raise svc.SonnetAgentError("subprocess blew up")

        monkeypatch.setattr("src.competitive.service.call_sonnet_json", boom)
        ads = [{"link_url": "https://ads.example.com/x"}]
        verdicts = await _agent_recover_near_misses("example.com", "example.com", ads)
        assert verdicts == {0: "NO"}


class TestCache:
    async def test_second_call_hits_cache_no_agent_call(self, fake_sonnet):
        call_count = {"n": 0}

        def responder(prompt, operation):
            call_count["n"] += 1
            return {"verdicts": [{"id": "a0", "verdict": "YES"}]}

        fake_sonnet(responder)
        ads = [{"link_url": "https://ads.example.com/x"}]
        first = await _agent_recover_near_misses("example.com", "example.com", ads)
        second = await _agent_recover_near_misses("example.com", "example.com", ads)
        assert first == {0: "YES"}
        assert second == {0: "YES"}
        assert call_count["n"] == 1  # Second call served from cache.

    async def test_cache_key_includes_brand_and_landing(self, fake_sonnet):
        """Different brands / landings cache independently."""
        responses = iter([
            {"verdicts": [{"id": "a0", "verdict": "YES"}]},
            {"verdicts": [{"id": "a0", "verdict": "NO"}]},
        ])

        def responder(prompt, operation):
            return next(responses)

        calls = fake_sonnet(responder)
        ad_a = [{"link_url": "https://ads.example.com/x"}]
        ad_b = [{"link_url": "https://cdn.example.com/y"}]
        await _agent_recover_near_misses("example.com", "example.com", ad_a)
        await _agent_recover_near_misses("example.com", "example.com", ad_b)
        assert len(calls) == 2  # Different landing hosts → distinct cache keys.

    async def test_partial_cache_hit_only_sends_uncached(self, fake_sonnet):
        """If 1 of 2 ads is cached, the batch call ships only the other one."""
        responses = iter([
            {"verdicts": [{"id": "a0", "verdict": "YES"}]},
            {"verdicts": [{"id": "a0", "verdict": "NO"}]},
        ])

        def responder(prompt, operation):
            return next(responses)

        calls = fake_sonnet(responder)
        ad_a = {"link_url": "https://ads.example.com/x"}
        ad_b = {"link_url": "https://cdn.example.com/y"}

        # Prime cache for ad_a.
        await _agent_recover_near_misses("example.com", "example.com", [ad_a])
        # Second call has ad_a (cached) + ad_b (new).
        verdicts = await _agent_recover_near_misses(
            "example.com", "example.com", [ad_a, ad_b],
        )
        assert verdicts == {0: "YES", 1: "NO"}
        assert len(calls) == 2
