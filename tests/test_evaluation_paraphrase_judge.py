"""Contract tests for the R-#32 paraphrase judge (Unit 11).

The judge replaces token-overlap `fuzzy_match`. These tests pin the public
contract:

- `verify_evidence_batch` returns a `{quote_id: bool}` map with keys
  matching the input quote set (`q0`, `q1`, ... in input order).
- One Sonnet call handles all quotes for a criterion (batching shape).
- The offline `EVAL_EVIDENCE_AGENT=off` fallback uses `fuzzy_match`.
- Failure of the Sonnet subprocess degrades to `fuzzy_match` with WARN log.
- Cache keys embed `PROMPT_VERSION` + criterion_id + sha256(output_text) +
  sha256(quote), dedupeing adjacent fixtures.
"""

from __future__ import annotations

import json

import pytest

from src.evaluation.judges import (
    PROMPT_VERSION,
    fuzzy_match,
    verify_evidence_batch,
)
from src.evaluation.judges import sonnet_agent as sonnet_agent_mod
from src.evaluation.judges import _PARAPHRASE_CACHE


@pytest.fixture(autouse=True)
def _clear_cache():
    _PARAPHRASE_CACHE.clear()
    yield
    _PARAPHRASE_CACHE.clear()


@pytest.fixture
def fake_sonnet(monkeypatch):
    """Patch `call_sonnet_json` with a scripted responder.

    Usage: fake_sonnet(lambda prompt, **kw: {"verdicts": [...]})
    Returns the call log.
    """
    calls = []

    def _install(responder):
        async def _fake(prompt, *, operation, model=None, timeout=None):
            calls.append({"prompt": prompt, "operation": operation})
            result = responder(prompt, operation=operation)
            return result

        monkeypatch.setattr(
            "src.evaluation.judges.call_sonnet_json", _fake,
        )
        return calls

    return _install


class TestParaphraseBatchShape:
    """Batching shape: one Sonnet call handles all quotes."""

    async def test_returns_bool_map_keyed_q0_q1(self, fake_sonnet):
        def responder(prompt, operation):
            return {"verdicts": [
                {"id": "q0", "supported": True},
                {"id": "q1", "supported": False},
                {"id": "q2", "supported": True},
            ]}
        calls = fake_sonnet(responder)

        verdicts = await verify_evidence_batch(
            "CI-3",
            ["quote one paraphrase", "fabricated claim", "another paraphrase"],
            "The article discusses paraphrase topics.",
        )
        assert verdicts == {"q0": True, "q1": False, "q2": True}
        assert len(calls) == 1
        assert calls[0]["operation"] == "evidence_paraphrase_check"

    async def test_keys_match_input_quote_count(self, fake_sonnet):
        fake_sonnet(lambda p, operation: {"verdicts": [
            {"id": f"q{i}", "supported": True} for i in range(4)
        ]})
        verdicts = await verify_evidence_batch(
            "GEO-1",
            ["a", "b", "c", "d"],
            "text",
        )
        assert set(verdicts.keys()) == {"q0", "q1", "q2", "q3"}
        assert all(isinstance(v, bool) for v in verdicts.values())

    async def test_empty_quote_list_no_call(self, fake_sonnet):
        calls = fake_sonnet(lambda p, operation: {"verdicts": []})
        verdicts = await verify_evidence_batch("MON-4", [], "text")
        assert verdicts == {}
        assert calls == []

    async def test_missing_verdict_treated_as_unsupported(self, fake_sonnet):
        # Judge omits q1 entirely.
        fake_sonnet(lambda p, operation: {"verdicts": [
            {"id": "q0", "supported": True},
        ]})
        verdicts = await verify_evidence_batch(
            "SB-2", ["a", "b"], "text",
        )
        assert verdicts["q0"] is True
        assert verdicts["q1"] is False


class TestParaphraseCache:
    """Cache keyed on (PROMPT_VERSION, criterion_id, sha256(output), sha256(quote))."""

    async def test_cache_hit_skips_second_call(self, fake_sonnet):
        calls = fake_sonnet(lambda p, operation: {"verdicts": [
            {"id": "q0", "supported": True},
        ]})
        await verify_evidence_batch("CI-3", ["q"], "text")
        await verify_evidence_batch("CI-3", ["q"], "text")
        assert len(calls) == 1  # second call was fully cache-hit

    async def test_cache_key_splits_on_criterion(self, fake_sonnet):
        calls = fake_sonnet(lambda p, operation: {"verdicts": [
            {"id": "q0", "supported": True},
        ]})
        await verify_evidence_batch("CI-3", ["q"], "text")
        await verify_evidence_batch("GEO-1", ["q"], "text")
        assert len(calls) == 2  # different criterion → miss

    async def test_prompt_version_is_pinned(self):
        assert PROMPT_VERSION.startswith("v1-")
        assert len(PROMPT_VERSION) > 3


class TestOfflineFallback:
    """EVAL_EVIDENCE_AGENT=off forces deterministic `fuzzy_match`."""

    async def test_offline_uses_fuzzy_match(self, monkeypatch, fake_sonnet):
        # Scripted sonnet shouldn't be called — monkeypatch the whole module
        # to raise if it is.
        def boom(*a, **kw):
            raise AssertionError("sonnet called when EVAL_EVIDENCE_AGENT=off")
        monkeypatch.setattr("src.evaluation.judges.call_sonnet_json", boom)
        monkeypatch.setenv("EVAL_EVIDENCE_AGENT", "off")

        quote_match = "topic words present"
        quote_miss = "zzzzz abcdef"
        text = "An article about topic words present in the body."

        verdicts = await verify_evidence_batch(
            "CI-3", [quote_match, quote_miss], text,
        )
        # q0 matches (token overlap), q1 does not.
        assert verdicts["q0"] == fuzzy_match(quote_match, text)
        assert verdicts["q1"] == fuzzy_match(quote_miss, text)


class TestSonnetFailureFallback:
    """Sonnet CLI errors degrade to fuzzy_match; never silently mark supported."""

    async def test_timeout_falls_back_to_fuzzy(self, monkeypatch):
        async def fail(prompt, *, operation, model=None, timeout=None):
            raise sonnet_agent_mod.SonnetAgentError("timeout")
        monkeypatch.setattr(
            "src.evaluation.judges.call_sonnet_json", fail,
        )
        verdicts = await verify_evidence_batch(
            "CI-3", ["words in body"], "words in body of article",
        )
        # fuzzy_match would accept this (full overlap).
        assert verdicts["q0"] is True

    async def test_fallback_does_not_mask_fabrication(self, monkeypatch):
        async def fail(prompt, *, operation, model=None, timeout=None):
            raise sonnet_agent_mod.SonnetAgentError("exit 1")
        monkeypatch.setattr(
            "src.evaluation.judges.call_sonnet_json", fail,
        )
        verdicts = await verify_evidence_batch(
            "CI-3", ["zzzzz fake fabricated tokens"], "unrelated text",
        )
        assert verdicts["q0"] is False


class TestSonnetAgentJsonExtraction:
    """call_sonnet_json is load-bearing; guard the JSON extractor."""

    def test_extractor_handles_plain_object(self):
        obj = sonnet_agent_mod._extract_last_json_object('{"score": 5}')
        assert obj == {"score": 5}

    def test_extractor_picks_last_of_multiple_objects(self):
        text = '{"old": true}\nsome prose\n{"score": 3}'
        assert sonnet_agent_mod._extract_last_json_object(text) == {"score": 3}

    def test_extractor_tolerates_markdown_fence(self):
        text = 'here is the answer:\n```json\n{"ok": true}\n```'
        assert sonnet_agent_mod._extract_last_json_object(text) == {"ok": True}

    def test_extractor_returns_none_on_no_object(self):
        assert sonnet_agent_mod._extract_last_json_object("plain prose, no JSON") is None

    def test_extractor_ignores_braces_in_strings(self):
        text = '{"msg": "not an object: {", "score": 1}'
        assert sonnet_agent_mod._extract_last_json_object(text) == {
            "msg": "not an object: {",
            "score": 1,
        }


class TestPromptShape:
    """Sanity: batched prompt actually includes every claim with its id."""

    async def test_prompt_carries_all_ids(self, fake_sonnet):
        calls = fake_sonnet(lambda p, operation: {"verdicts": [
            {"id": f"q{i}", "supported": False} for i in range(3)
        ]})
        await verify_evidence_batch(
            "CI-3", ["alpha", "bravo", "charlie"], "haystack text",
        )
        prompt = calls[0]["prompt"]
        for qid in ("q0", "q1", "q2"):
            assert qid in prompt
        for claim in ("alpha", "bravo", "charlie"):
            assert claim in prompt
