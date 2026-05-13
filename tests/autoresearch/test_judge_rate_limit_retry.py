"""Coverage for the 2026-05-13 Phase 3 dead-lane fix.

5 evolution lanes (competitive, marketing_audit, linkedin_engine,
monitoring, x_engine) died with the same `JudgeUnreachable` after the
fast-retry policy (4 attempts, ~40s budget) collapsed inside a 12+ min
Claude Max usage-limit window. Fix: detect upstream rate-limit signals
in 5xx/429 responses (and CLI stdout for agent_retry) and PROMOTE to a
long-backoff schedule (60s/120s/300s/600s/900s ≈ 32min) that survives
a typical reset window. Both retry helpers (HTTP-side
`evaluate_variant._post_with_retry` + subprocess-side
`agent_retry.is_rate_limit_failure`) get the new policy.

Memory: project-phase3-resume-state-2026-05-13.md.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Path bootstrap mirrors test_per_step_model_split.py.
_repo_root = Path(__file__).resolve().parents[2]
_autoresearch_dir = _repo_root / "autoresearch"
if str(_autoresearch_dir) in sys.path:
    sys.path.remove(str(_autoresearch_dir))
sys.path.insert(0, str(_autoresearch_dir))
for _mod in [m for m in list(sys.modules) if m == "harness" or m.startswith("harness.")]:
    file_attr = getattr(sys.modules[_mod], "__file__", None) or ""
    if not file_attr.startswith(str(_autoresearch_dir)):
        del sys.modules[_mod]

import agent_retry  # noqa: E402
import evaluate_variant  # noqa: E402


# --------------------------------------------------------------------------- #
# evaluate_variant._is_rate_limit_response — body-marker classification
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("body,expected", [
    ("You've hit your limit · resets 1:40pm (Europe/Warsaw)", True),
    ("rate_limit_exceeded for project foo", True),
    ("HTTP 429 Too Many Requests", True),
    ("Quota exceeded for this resource", True),
    ("KeyError: 'completion'", False),
    ("Internal server error: judge crashed mid-call", False),
    ("ValueError: bad payload", False),
])
def test_is_rate_limit_response_body_markers(body, expected):
    """5xx body content must classify as rate-limit-vs-crash correctly."""
    # 500 status — only the body markers should drive classification.
    assert evaluate_variant._is_rate_limit_response(500, body) is expected


def test_is_rate_limit_response_429_is_unconditional():
    """429 is ALWAYS rate-limit, regardless of body content."""
    assert evaluate_variant._is_rate_limit_response(429, "anything at all") is True
    assert evaluate_variant._is_rate_limit_response(429, "") is True


def test_is_rate_limit_response_4xx_non_429_is_not_rate_limit():
    """400/401/404 are caller errors, not rate-limit. They should NOT
    promote — they need to fail fast so the operator sees the bug."""
    assert evaluate_variant._is_rate_limit_response(400, "rate limit") is False
    assert evaluate_variant._is_rate_limit_response(401, "hit your limit") is False
    assert evaluate_variant._is_rate_limit_response(404, "quota exceeded") is False


def test_is_rate_limit_response_2xx_is_not_rate_limit():
    """Sanity: 2xx never classifies as rate-limit even if body somehow has markers."""
    assert evaluate_variant._is_rate_limit_response(200, "rate limit") is False


# --------------------------------------------------------------------------- #
# agent_retry.is_rate_limit_failure — CLI output classification
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("stderr,expected", [
    (b"You've hit your limit \xc2\xb7 resets 1:40pm", True),  # Claude CLI Max-cap
    (b"rate_limit_exceeded after 3 retries", True),
    (b"HTTP 429 Too Many Requests", True),
    (b"quota exceeded; refresh credits", True),
    (b"Connection refused", False),
    (b"Not logged in", False),  # auth missing — terminal, not rate-limit
    (b"", False),  # empty
])
def test_is_rate_limit_failure_marker_detection(stderr, expected):
    assert agent_retry.is_rate_limit_failure(stdout=b"", stderr=stderr) is expected


def test_is_rate_limit_failure_checks_stdout_too():
    """Claude CLI prints rate-limit notice to STDOUT, not stderr — must
    match either stream so the meta-agent retry path catches it."""
    assert agent_retry.is_rate_limit_failure(
        stdout=b"You've hit your limit \xc2\xb7 resets 1:40pm",
        stderr=b"",
    ) is True


def test_rate_limit_backoff_schedule():
    """Long-backoff delays must follow the 60s/120s/300s/600s/900s schedule
    so a Claude Max reset window (typically 5min-1hr) is outlasted."""
    assert agent_retry.rate_limit_backoff_delay(1) == 60.0
    assert agent_retry.rate_limit_backoff_delay(2) == 120.0
    assert agent_retry.rate_limit_backoff_delay(3) == 300.0
    assert agent_retry.rate_limit_backoff_delay(4) == 600.0
    assert agent_retry.rate_limit_backoff_delay(5) == 900.0
    # Beyond the schedule: clamp to last delay so we don't crash but also
    # don't accelerate (extra retries should still wait the longest interval).
    assert agent_retry.rate_limit_backoff_delay(99) == 900.0


def test_rate_limit_max_attempts_default():
    """Default 6 total attempts — initial + 5 retries — covers ~32min."""
    assert agent_retry.rate_limit_max_attempts() == 6


def test_fast_backoff_unchanged():
    """The original fast-retry schedule (2s/8s/30s) must NOT change — it's
    the fallback for genuine transient failures (network blips, judge
    restarts) where short backoff is appropriate."""
    assert agent_retry.backoff_delay(1) == 2.0
    assert agent_retry.backoff_delay(2) == 8.0
    assert agent_retry.backoff_delay(3) == 30.0


# --------------------------------------------------------------------------- #
# Integration: _post_with_retry promotes to long-backoff on rate-limit body
# --------------------------------------------------------------------------- #


class _FakeResponse:
    def __init__(self, status_code: int, text: str):
        self.status_code = status_code
        self.text = text


def test_post_with_retry_promotes_on_rate_limit_then_succeeds(monkeypatch):
    """First call returns 500 with rate-limit body → promote to long-backoff
    policy → second call returns 200 → success."""
    # Shrink the budget so the test runs in <1s and freeze sleep.
    monkeypatch.setattr(evaluate_variant, "_JUDGE_RATE_LIMIT_DELAYS", (0.0, 0.0, 0.0))
    monkeypatch.setattr(evaluate_variant, "_JUDGE_RATE_LIMIT_BUDGET_S", 60.0)
    monkeypatch.setattr(evaluate_variant, "_JUDGE_RETRY_DELAYS", (0.0, 0.0, 0.0))

    call_log: list[int] = []

    def fake_post(url, **kwargs):
        call_log.append(len(call_log) + 1)
        if call_log[-1] == 1:
            return _FakeResponse(500, "You've hit your limit · resets 1:40pm")
        return _FakeResponse(200, '{"result": "ok"}')

    import httpx
    with patch.object(httpx, "post", side_effect=fake_post):
        response = evaluate_variant._post_with_retry(
            endpoint="http://test/score",
            request_body={"x": 1},
            token="bearer-token",
            fixture_id="fix1",
            domain="geo",
            variant_id="v999",
        )
    assert response.status_code == 200
    assert len(call_log) == 2


def test_post_with_retry_genuine_5xx_uses_fast_policy(monkeypatch):
    """5xx with NO rate-limit markers must NOT promote — stays on fast
    retry budget (4 attempts, ~40s) so genuine judge crashes fail fast."""
    monkeypatch.setattr(evaluate_variant, "_JUDGE_RETRY_DELAYS", (0.0, 0.0, 0.0))
    monkeypatch.setattr(evaluate_variant, "_JUDGE_RETRY_TOTAL_BUDGET_S", 60.0)

    call_log: list[int] = []

    def fake_post(url, **kwargs):
        call_log.append(1)
        return _FakeResponse(500, "ValueError: judge crashed mid-call")

    import httpx
    with patch.object(httpx, "post", side_effect=fake_post), \
         pytest.raises(evaluate_variant.JudgeUnreachable, match="fast"):
        evaluate_variant._post_with_retry(
            endpoint="http://test/score",
            request_body={"x": 1},
            token="bearer-token",
            fixture_id="fix1",
            domain="geo",
            variant_id="v999",
        )
    # 4 attempts on the fast policy (initial + 3 retries).
    assert len(call_log) == 4


def test_post_with_retry_codex_credits_short_circuits(monkeypatch):
    """Codex credit exhaustion is terminal — even though it's a 500, the
    short-circuit must fire BEFORE the rate-limit promotion (credits don't
    return after a window reset). Existing behavior, regression guard."""
    monkeypatch.setattr(evaluate_variant, "_JUDGE_RETRY_DELAYS", (0.0, 0.0, 0.0))

    call_log: list[int] = []

    def fake_post(url, **kwargs):
        call_log.append(1)
        return _FakeResponse(500, "codex credits exhausted on backend")

    import httpx
    with patch.object(httpx, "post", side_effect=fake_post), \
         pytest.raises(evaluate_variant.JudgeUnreachable, match="codex credits"):
        evaluate_variant._post_with_retry(
            endpoint="http://test/score",
            request_body={"x": 1},
            token="bearer-token",
            fixture_id="fix1",
            domain="geo",
            variant_id="v999",
        )
    assert len(call_log) == 1  # short-circuit, no retries
