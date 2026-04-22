"""Tests for Unit 14 — `freddy monitor mentions --format summary` Sonnet summarizer.

Pins the public contract:

- Happy path: Sonnet returns valid JSON → Pydantic parses → output carries the
  new shape (top_mentions / themes / source_mix) alongside deterministic
  aggregates (total / fetched / sources / languages).
- Subprocess failure degrades to deterministic aggregates + WARNING log
  (no exception surfaced to CLI user).
- Pydantic validation failure on malformed Sonnet JSON → same fallback.
- Cache hit: identical inputs read the cached payload; no repeat Sonnet call.
- Volume tier → source_mix sample-size instruction in the rendered prompt.
- PROMPT_VERSION is embedded in the cache key (stale entries unreachable
  after a prompt edit by construction).
"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from cli.freddy.commands import monitor as monitor_mod


# ─── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _isolated_cache(tmp_path, monkeypatch):
    """Route the monitor-summary cache at a tmp path per test."""
    monkeypatch.setattr(monitor_mod, "_CACHE_DIR", tmp_path / "cache")
    yield


def _mention(i: int, source: str = "reddit", content: str | None = None) -> dict:
    return {
        "id": f"m{i}",
        "source": source,
        "language": "en",
        "content": content or f"content number {i}",
        "author_handle": f"u{i}",
        "published_at": f"2026-04-{(i % 28) + 1:02d}T00:00:00Z",
        "engagement_likes": i,
    }


def _valid_sonnet_payload() -> dict:
    return {
        "top_mentions": [
            {"mention_id": "m0", "relevance_rank": 1, "reason": "pricing-tier pushback"},
            {"mention_id": "m2", "relevance_rank": 2, "reason": "churn signal"},
        ],
        "themes": [
            {"theme": "pricing pushback", "representative_quotes": ["too expensive"]},
        ],
        "source_mix": [
            {"source": "reddit",
             "sample": [{"mention_id": "m0", "headline": "pricing complaint"}]},
        ],
    }


# ─── Happy path ───────────────────────────────────────────────────────────────


class TestBuildSummaryHappyPath:
    def test_output_carries_sonnet_shape_plus_aggregates(self, monkeypatch):
        payload = _valid_sonnet_payload()

        async def _fake_call(prompt):
            return payload

        monkeypatch.setattr(monitor_mod, "_call_sonnet_summary", _fake_call)

        mentions = [_mention(i) for i in range(5)]
        out = monitor_mod._build_summary(mentions, api_total=5, monitor_id="mon-1")

        # Deterministic aggregates (raw floor).
        assert out["total"] == 5
        assert out["fetched"] == 5
        assert out["sources"] == {"reddit": 5}
        assert out["languages"] == {"en": 5}

        # Sonnet-authored portion.
        assert out["top_mentions"][0]["mention_id"] == "m0"
        assert out["top_mentions"][0]["relevance_rank"] == 1
        assert out["themes"][0]["theme"] == "pricing pushback"
        assert out["themes"][0]["representative_quotes"] == ["too expensive"]
        assert out["source_mix"][0]["source"] == "reddit"
        assert out["source_mix"][0]["sample"][0]["headline"] == "pricing complaint"

        # Old-shape keys that described engagement-naive heuristics are gone.
        assert "recent_by_source" not in out

    def test_empty_mentions_skips_sonnet(self, monkeypatch):
        called = {"n": 0}

        async def _fake_call(prompt):  # pragma: no cover - must not fire
            called["n"] += 1
            return _valid_sonnet_payload()

        monkeypatch.setattr(monitor_mod, "_call_sonnet_summary", _fake_call)
        out = monitor_mod._build_summary([], api_total=0, monitor_id="mon-1")

        assert called["n"] == 0
        assert out["total"] == 0
        assert out["fetched"] == 0
        assert out["top_mentions"] == []
        assert out["themes"] == []
        assert out["source_mix"] == []


# ─── Failure handling ─────────────────────────────────────────────────────────


class TestSubprocessFailureFallback:
    def test_subprocess_error_falls_back_to_aggregates(self, monkeypatch, caplog):
        async def _boom(prompt):
            raise RuntimeError("claude -p exit 1: boom")

        monkeypatch.setattr(monitor_mod, "_call_sonnet_summary", _boom)

        mentions = [_mention(i) for i in range(3)]
        with caplog.at_level("WARNING", logger=monitor_mod.logger.name):
            out = monitor_mod._build_summary(mentions, api_total=3, monitor_id="mon-1")

        # Only aggregates — Sonnet keys absent.
        assert out == {
            "total": 3,
            "fetched": 3,
            "sources": {"reddit": 3},
            "languages": {"en": 3},
        }
        assert any("Sonnet call failed" in rec.message for rec in caplog.records)

    def test_pydantic_validation_failure_falls_back(self, monkeypatch, caplog):
        async def _bad_shape(prompt):
            return {"top_mentions": [{"mention_id": "m0"}],  # missing required fields
                    "themes": [], "source_mix": []}

        monkeypatch.setattr(monitor_mod, "_call_sonnet_summary", _bad_shape)

        mentions = [_mention(i) for i in range(2)]
        with caplog.at_level("WARNING", logger=monitor_mod.logger.name):
            out = monitor_mod._build_summary(mentions, api_total=2, monitor_id="mon-1")

        assert "top_mentions" not in out
        assert out["total"] == 2
        assert any("shape invalid" in rec.message for rec in caplog.records)


# ─── Cache ────────────────────────────────────────────────────────────────────


class TestCache:
    def test_second_call_reads_cache(self, monkeypatch):
        calls = {"n": 0}
        payload = _valid_sonnet_payload()

        async def _fake_call(prompt):
            calls["n"] += 1
            return payload

        monkeypatch.setattr(monitor_mod, "_call_sonnet_summary", _fake_call)

        mentions = [_mention(i) for i in range(4)]
        a = monitor_mod._build_summary(mentions, api_total=4, monitor_id="mon-1")
        b = monitor_mod._build_summary(mentions, api_total=4, monitor_id="mon-1")

        assert calls["n"] == 1  # second call served from disk cache
        assert a["top_mentions"] == b["top_mentions"]

    def test_cache_key_embeds_prompt_version(self):
        k1 = monitor_mod._cache_key("mon-1", ["m0", "m1"])
        # Simulate a prompt-version bump — key must change.
        with patch.object(monitor_mod, "PROMPT_VERSION", "9999-99-99.vX"):
            k2 = monitor_mod._cache_key("mon-1", ["m0", "m1"])
        assert k1 != k2

    def test_cache_key_is_order_independent(self):
        k1 = monitor_mod._cache_key("mon-1", ["m0", "m1", "m2"])
        k2 = monitor_mod._cache_key("mon-1", ["m2", "m0", "m1"])
        assert k1 == k2

    def test_stale_entry_ignored_past_ttl(self, monkeypatch, tmp_path):
        # TTL→0 forces the "expired" branch on a fresh write.
        monkeypatch.setattr(monitor_mod, "_CACHE_TTL_SECONDS", 0)
        calls = {"n": 0}

        async def _fake_call(prompt):
            calls["n"] += 1
            return _valid_sonnet_payload()

        monkeypatch.setattr(monitor_mod, "_call_sonnet_summary", _fake_call)
        mentions = [_mention(i) for i in range(3)]
        monitor_mod._build_summary(mentions, api_total=3, monitor_id="mon-1")
        monitor_mod._build_summary(mentions, api_total=3, monitor_id="mon-1")
        assert calls["n"] == 2


# ─── Volume-tiered prompt ─────────────────────────────────────────────────────


class TestVolumeTierPrompt:
    @pytest.mark.parametrize("fetched,expected", [
        (1, 1), (25, 1),             # low
        (26, 3), (100, 3),           # medium
        (101, 5), (5000, 5),         # high
    ])
    def test_sample_size_thresholds(self, fetched, expected):
        assert monitor_mod._sample_size_for_volume(fetched) == expected

    def test_prompt_embeds_requested_sample_size(self):
        enriched = monitor_mod._ensure_mention_ids(
            [_mention(i) for i in range(60)]
        )
        prompt = monitor_mod._build_sonnet_prompt("mon-x", enriched, sample_size=3)
        assert "`sample` size MUST be exactly 3" in prompt
        assert "mon-x" in prompt


# ─── Schema model smoke ───────────────────────────────────────────────────────


class TestPydanticModels:
    def test_rejects_negative_rank(self):
        from pydantic import ValidationError as _VE
        with pytest.raises(_VE):
            monitor_mod.TopMention(mention_id="m0", relevance_rank=0, reason="x")

    def test_round_trip_matches_input(self):
        p = monitor_mod.SonnetSummaryPayload.model_validate(_valid_sonnet_payload())
        # model_dump is what the CLI hands back; must be plain dicts (JSON-safe).
        dumped = p.model_dump()
        assert json.dumps(dumped)  # no non-serializable leaves
        assert dumped["source_mix"][0]["sample"][0]["mention_id"] == "m0"
