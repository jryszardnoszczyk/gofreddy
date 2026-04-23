"""Judge-client interface tests. Mock httpx.post; test wiring + response parsing.

Under the Phase 0c HTTP-client architecture, tests mock the HTTP transport
(httpx.post), not an in-process model-invocation function. This tests the
CLIENT's contract: does it POST to the right URL with the right bearer
token, and does it parse the response correctly?

Prompts and agent logic live on the judge-service; autoresearch never
imports them.
"""
from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

import httpx
import pytest

from autoresearch.judges.quality_judge import call_quality_judge, QualityVerdict
from autoresearch.judges.promotion_judge import (
    call_promotion_judge,
    PromotionVerdict,
    JudgeUnreachable,
)


def _mock_http_response(body: str, status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value=json.loads(body))
    resp.text = body
    return resp


# --- quality judge -------------------------------------------------------


def test_quality_judge_returns_verdict_with_reasoning():
    payload = {
        "role": "fixture_quality",
        "fixture_id": "geo-bmw-ev-de",
        "stats": {"median": 0.92, "mad": 0.03, "cost_usd": 0.12},
    }
    mock = json.dumps({
        "verdict": "saturated",
        "reasoning": "Median 0.92 near ceiling; low MAD; fixture too easy.",
        "confidence": 0.85,
        "recommended_action": "rotate_out_next_cycle",
    })
    with patch("httpx.post", return_value=_mock_http_response(mock)):
        result = call_quality_judge(payload)
    assert isinstance(result, QualityVerdict)
    assert result.verdict == "saturated"
    assert "ceiling" in result.reasoning.lower()
    assert 0.0 <= result.confidence <= 1.0
    assert result.recommended_action == "rotate_out_next_cycle"


def test_quality_judge_posts_to_correct_endpoint():
    payload = {"role": "saturation", "pool": "holdout-v1"}
    mock = json.dumps({"verdict": "fine", "reasoning": "", "confidence": 0.6})
    with patch("httpx.post", return_value=_mock_http_response(mock)) as post:
        call_quality_judge(payload)
    url = post.call_args.args[0]
    assert url.endswith("/invoke/system_health/saturation")
    headers = post.call_args.kwargs.get("headers", {})
    assert headers.get("Authorization", "").startswith("Bearer ")


def test_quality_judge_rejects_unknown_role():
    with pytest.raises(ValueError, match="invalid system_health role"):
        call_quality_judge({"role": "not_a_real_role"})


# --- promotion judge -----------------------------------------------------


def test_promotion_judge_promote_when_signals_coherent():
    payload = {
        "role": "promotion",
        "candidate_id": "v007", "baseline_id": "v006", "lane": "geo",
        "public_scores": {"candidate": 0.72, "baseline": 0.65},
        "holdout_scores": {"candidate": 0.62, "baseline": 0.55},
    }
    mock = json.dumps({
        "decision": "promote",
        "reasoning": "Public + holdout both up; both judges agree.",
        "confidence": 0.88,
        "concerns": [],
    })
    with patch("httpx.post", return_value=_mock_http_response(mock)):
        result = call_promotion_judge(payload)
    assert isinstance(result, PromotionVerdict)
    assert result.decision == "promote"
    assert result.confidence == 0.88


def test_promotion_judge_rejects_on_concerns():
    payload = {"role": "promotion", "candidate_id": "v008", "baseline_id": "v006", "lane": "geo"}
    mock = json.dumps({
        "decision": "reject",
        "reasoning": "Cross-family disagreement + single-fixture dominance.",
        "confidence": 0.82,
        "concerns": ["cross_family_disagreement", "uneven_per_fixture_wins"],
    })
    with patch("httpx.post", return_value=_mock_http_response(mock)):
        result = call_promotion_judge(payload)
    assert result.decision == "reject"
    assert "cross_family_disagreement" in result.concerns


def test_promotion_judge_canary_go_decision():
    payload = {"role": "canary", "mode": "go_fail", "lane": "geo", "checkpoints": []}
    mock = json.dumps({
        "decision": "go",
        "reasoning": "Divergence trends up monotonically.",
        "confidence": 0.93,
        "concerns": [],
    })
    with patch("httpx.post", return_value=_mock_http_response(mock)):
        result = call_promotion_judge(payload)
    assert result.decision == "go"


def test_promotion_judge_rollback_decision():
    payload = {"role": "rollback", "lane": "geo", "current_head": "v010",
               "prior_head": "v006", "head_scores_log": []}
    mock = json.dumps({
        "decision": "rollback",
        "reasoning": "Three consecutive post-promotion regressions.",
        "confidence": 0.91,
        "concerns": [],
    })
    with patch("httpx.post", return_value=_mock_http_response(mock)):
        result = call_promotion_judge(payload)
    assert result.decision == "rollback"


def test_promotion_judge_posts_to_correct_endpoint_per_role():
    mock = json.dumps({"decision": "promote", "reasoning": "", "confidence": 0.6, "concerns": []})
    with patch("httpx.post", return_value=_mock_http_response(mock)) as post:
        call_promotion_judge({"role": "canary"})
    url = post.call_args.args[0]
    assert url.endswith("/invoke/decide/canary")


def test_promotion_judge_rejects_unknown_role():
    with pytest.raises(ValueError, match="invalid decision role"):
        call_promotion_judge({"role": "not_a_real_role"})


def test_promotion_judge_raises_judge_unreachable_on_http_error(tmp_path, monkeypatch):
    """Emit kind=judge_unreachable + raise JudgeUnreachable on transport failure.

    Matches Plan A Phase 0c: no threshold fallback, no silent retry.
    """
    # Point events log at tmp to avoid polluting the user's real log.
    monkeypatch.setenv("AUTORESEARCH_EVENTS_LOG", str(tmp_path / "events.jsonl"))

    def _raises(*args, **kwargs):
        raise httpx.ConnectError("connection refused")

    with patch("httpx.post", side_effect=_raises):
        with pytest.raises(JudgeUnreachable, match="evolution-judge unreachable"):
            call_promotion_judge({"role": "promotion"})


def test_promotion_judge_raises_judge_unreachable_on_bad_json(tmp_path, monkeypatch):
    """A successful HTTP exchange with malformed JSON still raises JudgeUnreachable."""
    monkeypatch.setenv("AUTORESEARCH_EVENTS_LOG", str(tmp_path / "events.jsonl"))

    resp = MagicMock()
    resp.status_code = 200
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(side_effect=ValueError("no JSON"))
    resp.text = "not json"
    with patch("httpx.post", return_value=resp):
        with pytest.raises(JudgeUnreachable):
            call_promotion_judge({"role": "promotion"})
