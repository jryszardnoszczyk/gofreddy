"""citation_verifier — URL fetch + HTML strip + claude verification.

The verifier accepts dependency-injected `fetch_url` + `call_claude`
callables so tests exercise the full pipeline without network or
claude subprocess overhead.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from src.verification.citation_cache import CitationCache
from src.verification.citation_verifier import (
    CitationFetchError,
    CitationVerification,
    verify_citation,
)


def _ok_claude_call(prompt: str) -> str:
    """Test stand-in: returns a verified=true JSON response."""
    return (
        '{"verified": true, "confidence": 0.85, '
        '"rationale": "page directly states the claim"}'
    )


def _no_claude_call(prompt: str) -> str:
    return (
        '{"verified": false, "confidence": 0.2, '
        '"rationale": "page does not address claim"}'
    )


def _ok_fetch(url: str) -> str:
    return "<html><body><p>The relevant content body.</p></body></html>"


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


def test_empty_claim_raises() -> None:
    with pytest.raises(CitationFetchError) as exc:
        verify_citation("", "https://example.com", call_claude=_ok_claude_call)
    assert "claim must be non-empty" in str(exc.value)


def test_empty_url_raises() -> None:
    with pytest.raises(CitationFetchError) as exc:
        verify_citation("a claim", "", call_claude=_ok_claude_call)
    assert "url must be non-empty" in str(exc.value)


def test_missing_call_claude_raises() -> None:
    """v1 has no default claude backend — caller MUST inject."""
    with pytest.raises(CitationFetchError) as exc:
        verify_citation("a claim", "https://example.com")
    assert "call_claude is required" in str(exc.value)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_verified_true_when_claude_says_verified() -> None:
    result = verify_citation(
        "a claim",
        "https://example.com",
        fetch_url=_ok_fetch,
        call_claude=_ok_claude_call,
    )
    assert isinstance(result, CitationVerification)
    assert result.verified is True
    assert result.confidence == 0.85
    assert "directly" in result.rationale
    assert result.degraded is False


def test_verified_false_when_claude_says_unverified() -> None:
    result = verify_citation(
        "a claim",
        "https://example.com",
        fetch_url=_ok_fetch,
        call_claude=_no_claude_call,
    )
    assert result.verified is False
    assert result.confidence == 0.2
    assert result.degraded is False


# ---------------------------------------------------------------------------
# Degraded modes (404 / paywalled / JS-heavy)
# ---------------------------------------------------------------------------


def test_fetch_failure_returns_degraded() -> None:
    def fetch_404(url: str) -> str:
        raise RuntimeError("404 Not Found")

    result = verify_citation(
        "a claim",
        "https://example.com/missing",
        fetch_url=fetch_404,
        call_claude=_ok_claude_call,
    )
    assert result.degraded is True
    assert result.verified is False
    assert "404" in result.rationale


def test_claude_exception_returns_degraded() -> None:
    def claude_explodes(prompt: str) -> str:
        raise RuntimeError("subprocess died")

    result = verify_citation(
        "a claim",
        "https://example.com",
        fetch_url=_ok_fetch,
        call_claude=claude_explodes,
    )
    assert result.degraded is True
    assert "subprocess died" in result.rationale


def test_claude_unparseable_response_returns_degraded() -> None:
    def claude_returns_prose(prompt: str) -> str:
        return "I cannot verify this claim because no clear JSON was provided."

    result = verify_citation(
        "a claim",
        "https://example.com",
        fetch_url=_ok_fetch,
        call_claude=claude_returns_prose,
    )
    assert result.degraded is True
    assert result.verified is False


def test_claude_response_with_markdown_fence_still_parses() -> None:
    """Claude sometimes wraps JSON in ```json fences. The regex
    extraction tolerates this."""
    def claude_with_fence(prompt: str) -> str:
        return (
            "Sure, here's the verification:\n"
            "```json\n"
            '{"verified": true, "confidence": 0.7, "rationale": "ok"}\n'
            "```\n"
            "Let me know if you need more details."
        )

    result = verify_citation(
        "a claim",
        "https://example.com",
        fetch_url=_ok_fetch,
        call_claude=claude_with_fence,
    )
    assert result.verified is True
    assert result.degraded is False


# ---------------------------------------------------------------------------
# HTML stripping — script/style content must not reach claude
# ---------------------------------------------------------------------------


def test_html_stripping_removes_scripts(tmp_path: Path) -> None:
    """The prompt must not include <script> bodies — they pollute the
    verification context and could prompt-inject if attacker-supplied."""
    captured_prompts: list[str] = []

    def capture(prompt: str) -> str:
        captured_prompts.append(prompt)
        return '{"verified": true, "confidence": 0.5, "rationale": "ok"}'

    def fetch_with_scripts(url: str) -> str:
        return (
            "<html><body>"
            "<script>alert('xss');</script>"
            "<p>Real content.</p>"
            "</body></html>"
        )

    verify_citation(
        "claim", "https://example.com",
        fetch_url=fetch_with_scripts, call_claude=capture,
    )
    assert len(captured_prompts) == 1
    assert "alert" not in captured_prompts[0]
    assert "Real content" in captured_prompts[0]


# ---------------------------------------------------------------------------
# Cache integration
# ---------------------------------------------------------------------------


def test_cache_hit_skips_fetch_and_claude(tmp_path: Path) -> None:
    """Pre-warmed cache → verifier returns cached result without
    invoking fetch_url or call_claude."""
    cache = CitationCache(path=tmp_path / "cache.json")
    cache.set("c", "https://example.com", {
        "verified": True, "confidence": 0.95, "rationale": "cached", "degraded": False,
    })

    fetches: list[str] = []
    claude_calls: list[str] = []
    def fetch_should_not_run(url: str) -> str:
        fetches.append(url)
        return ""
    def claude_should_not_run(prompt: str) -> str:
        claude_calls.append(prompt)
        return ""

    result = verify_citation(
        "c", "https://example.com",
        fetch_url=fetch_should_not_run,
        call_claude=claude_should_not_run,
        cache=cache,
    )
    assert result.verified is True
    assert result.confidence == 0.95
    assert result.rationale == "cached"
    assert fetches == []
    assert claude_calls == []


def test_cache_miss_then_set(tmp_path: Path) -> None:
    """Cache miss → fetch+verify → set into cache → next call hits."""
    cache = CitationCache(path=tmp_path / "cache.json")
    claude_call_count = {"n": 0}

    def counting_claude(prompt: str) -> str:
        claude_call_count["n"] += 1
        return '{"verified": true, "confidence": 0.7, "rationale": "ok"}'

    # First call: miss → invokes claude
    verify_citation(
        "c", "https://example.com",
        fetch_url=_ok_fetch, call_claude=counting_claude, cache=cache,
    )
    assert claude_call_count["n"] == 1

    # Second call: hit → does not invoke claude
    verify_citation(
        "c", "https://example.com",
        fetch_url=_ok_fetch, call_claude=counting_claude, cache=cache,
    )
    assert claude_call_count["n"] == 1


def test_cache_does_not_persist_degraded_results_collide_with_real(tmp_path: Path) -> None:
    """A degraded result IS cached so the verifier doesn't repeatedly
    hit a 404'd URL with claude tokens. Operators clear with `--fresh`
    when the URL comes back online."""
    cache = CitationCache(path=tmp_path / "cache.json")

    def fetch_404(url: str) -> str:
        raise RuntimeError("404")

    first = verify_citation(
        "c", "https://example.com",
        fetch_url=fetch_404,
        call_claude=_ok_claude_call,
        cache=cache,
    )
    assert first.degraded is True

    fetch_calls: list[str] = []
    def fetch_counter(url: str) -> str:
        fetch_calls.append(url)
        return ""
    verify_citation(
        "c", "https://example.com",
        fetch_url=fetch_counter,
        call_claude=_ok_claude_call,
        cache=cache,
    )
    # Second call did NOT hit the fetcher again — degraded is cached.
    assert fetch_calls == []
