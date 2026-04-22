"""Contract tests for the R-#33 calibration judge (Unit 11).

The judge replaces the cap-at-3 cliff. Pinned contract:

- `calibrate_gradient` returns `{"score": int in [0, 5], "reasoning": str}`.
- The reasoning is non-empty.
- Sonnet call is made unless `EVAL_CALIBRATION=off`.
- Failure preserves the primary score (degrade to permissive, not restrictive).
- Cache keyed on (PROMPT_VERSION, criterion_id, sha256(reasoning),
  sha256(evidence_block)).
"""

from __future__ import annotations

import pytest

from src.evaluation.judges import (
    PROMPT_VERSION,
    calibrate_gradient,
)
from src.evaluation.judges import sonnet_agent as sonnet_agent_mod
from src.evaluation.judges import _CALIBRATION_CACHE


@pytest.fixture(autouse=True)
def _clear_cache():
    _CALIBRATION_CACHE.clear()
    yield
    _CALIBRATION_CACHE.clear()


@pytest.fixture
def fake_sonnet(monkeypatch):
    """Patch `call_sonnet_json` with a scripted responder."""
    calls = []

    def _install(responder):
        async def _fake(prompt, *, operation, model=None, timeout=None):
            calls.append({"prompt": prompt, "operation": operation})
            return responder(prompt, operation=operation)
        monkeypatch.setattr(
            "src.evaluation.judges.call_sonnet_json", _fake,
        )
        return calls

    return _install


class TestCalibrationContract:
    """Output shape: {score, reasoning}, score in range, reasoning non-empty."""

    async def test_returns_score_and_reasoning(self, fake_sonnet):
        fake_sonnet(lambda p, operation: {
            "score": 4,
            "reasoning": "evidence supports a strong but not unambiguous reading",
        })
        result = await calibrate_gradient(
            "CI-3", "rubric text", 5, "primary reasoning", ["q1"], {"q0": True},
        )
        assert isinstance(result, dict)
        assert set(result.keys()) == {"score", "reasoning"}
        assert isinstance(result["score"], int)
        assert isinstance(result["reasoning"], str)
        assert result["reasoning"].strip()

    async def test_score_clamped_to_0_5_range(self, fake_sonnet):
        # Judge returns score above range — should clamp to 5.
        fake_sonnet(lambda p, operation: {"score": 99, "reasoning": "out-of-range"})
        result = await calibrate_gradient(
            "CI-3", "rubric", 4, "reasoning", ["q"], {"q0": True},
        )
        assert 0 <= result["score"] <= 5

        # Judge returns negative — should clamp to 0.
        fake_sonnet(lambda p, operation: {"score": -3, "reasoning": "neg"})
        _CALIBRATION_CACHE.clear()
        result = await calibrate_gradient(
            "CI-3", "rubric", 4, "different reasoning", ["q"], {"q0": True},
        )
        assert 0 <= result["score"] <= 5

    async def test_score_in_int_0_to_5(self, fake_sonnet):
        # All five claimed bands round-trip cleanly.
        for claimed in (1, 2, 3, 4, 5):
            fake_sonnet(lambda p, operation, c=claimed: {
                "score": c, "reasoning": f"supports band {c}",
            })
            _CALIBRATION_CACHE.clear()
            result = await calibrate_gradient(
                f"CI-{claimed}", "r", claimed, "primary", ["q"], {"q0": True},
            )
            assert result["score"] == claimed

    async def test_non_string_reasoning_is_coerced(self, fake_sonnet):
        fake_sonnet(lambda p, operation: {"score": 3, "reasoning": {"nested": "obj"}})
        result = await calibrate_gradient(
            "CI-3", "rubric", 4, "reasoning", ["q"], {"q0": True},
        )
        assert isinstance(result["reasoning"], str)
        assert result["reasoning"].strip()


class TestCalibrationSmoothing:
    """No cliff: judge can lower 5→3, 5→4, or keep 5; or raise from primary."""

    async def test_lowers_score_when_evidence_thin(self, fake_sonnet):
        fake_sonnet(lambda p, operation: {
            "score": 3, "reasoning": "only one weak quote — supports band 3 not 5",
        })
        result = await calibrate_gradient(
            "CI-3", "rubric", 5, "claims band 5", ["weak quote"], {"q0": True},
        )
        assert result["score"] == 3
        assert "band 3" in result["reasoning"]

    async def test_keeps_score_when_well_supported(self, fake_sonnet):
        fake_sonnet(lambda p, operation: {
            "score": 5, "reasoning": "evidence supports band 5",
        })
        result = await calibrate_gradient(
            "GEO-1", "rubric", 5, "primary said 5", ["a", "b", "c"],
            {"q0": True, "q1": True, "q2": True},
        )
        assert result["score"] == 5


class TestCalibrationFailure:
    """Sonnet failure preserves primary score (permissive, not restrictive)."""

    async def test_timeout_preserves_primary(self, monkeypatch):
        async def fail(prompt, *, operation, model=None, timeout=None):
            raise sonnet_agent_mod.SonnetAgentError("timeout")
        monkeypatch.setattr(
            "src.evaluation.judges.call_sonnet_json", fail,
        )
        result = await calibrate_gradient(
            "CI-3", "rubric", 4, "primary reasoning", ["q"], {"q0": True},
        )
        assert result["score"] == 4
        assert "calibration judge error" in result["reasoning"]


class TestCalibrationDisabled:
    """EVAL_CALIBRATION=off skips the call and preserves primary."""

    async def test_disabled_skips_sonnet(self, monkeypatch):
        async def boom(*a, **kw):
            raise AssertionError("Sonnet called when calibration disabled")
        monkeypatch.setattr(
            "src.evaluation.judges.call_sonnet_json", boom,
        )
        monkeypatch.setenv("EVAL_CALIBRATION", "off")

        result = await calibrate_gradient(
            "CI-3", "rubric", 4, "primary", ["q"], {"q0": True},
        )
        assert result["score"] == 4
        assert "calibration disabled" in result["reasoning"]


class TestCalibrationCache:
    """Cache key embeds PROMPT_VERSION + criterion + sha(reasoning) + sha(evidence)."""

    async def test_repeat_call_uses_cache(self, fake_sonnet):
        calls = fake_sonnet(lambda p, operation: {"score": 3, "reasoning": "x"})
        await calibrate_gradient(
            "CI-3", "rubric", 4, "reasoning", ["q"], {"q0": True},
        )
        await calibrate_gradient(
            "CI-3", "rubric", 4, "reasoning", ["q"], {"q0": True},
        )
        assert len(calls) == 1

    async def test_different_reasoning_misses_cache(self, fake_sonnet):
        calls = fake_sonnet(lambda p, operation: {"score": 3, "reasoning": "x"})
        await calibrate_gradient("CI-3", "r", 4, "reasoning A", ["q"], {"q0": True})
        await calibrate_gradient("CI-3", "r", 4, "reasoning B", ["q"], {"q0": True})
        assert len(calls) == 2

    async def test_prompt_version_pinned(self):
        assert PROMPT_VERSION
        # Format check: short git-ish hash; any change here means we broke
        # cache invalidation expectations downstream.
        assert PROMPT_VERSION.startswith("v1-")


class TestCalibrationPromptCarriesContext:
    """Prompt must include the criterion, score band claim, and evidence verdicts."""

    async def test_prompt_includes_criterion_score_evidence(self, fake_sonnet):
        calls = fake_sonnet(lambda p, operation: {"score": 4, "reasoning": "ok"})
        await calibrate_gradient(
            "MON-2",
            "rubric body about severity classification",
            5,
            "claims band 5",
            ["evidence quote one", "evidence quote two"],
            {"q0": True, "q1": False},
        )
        prompt = calls[0]["prompt"]
        assert "MON-2" in prompt
        assert "5/5" in prompt
        assert "evidence quote one" in prompt
        assert "evidence quote two" in prompt
        assert "supported=true" in prompt
        assert "supported=false" in prompt
