"""Verify cli/freddy/commands/evaluate.py is an HTTP-only thin client.

No provider URLs, no provider SDK imports. The only HTTP client it uses
is httpx; the only outbound URLs are the local judge-service URLs
parameterized by env.
"""
from __future__ import annotations

import re
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[2]
_EVALUATE = _REPO_ROOT / "cli" / "freddy" / "commands" / "evaluate.py"


def _source() -> str:
    return _EVALUATE.read_text()


def test_no_provider_api_urls() -> None:
    src = _source()
    assert "api.openai.com" not in src
    assert "api.anthropic.com" not in src
    assert "generativelanguage.googleapis.com" not in src


def test_no_provider_sdk_imports() -> None:
    src = _source()
    # Match any ``import openai``, ``from openai import`` etc. as a
    # first-column directive (regex anchored to line start under MULTILINE).
    for forbidden in ("openai", "anthropic", "google.genai"):
        pattern = re.compile(rf"^\s*(?:from|import)\s+{re.escape(forbidden)}\b", re.MULTILINE)
        assert not pattern.search(src), f"must not import {forbidden}"


def test_no_evaluate_prompt_string() -> None:
    src = _source()
    assert "EVALUATE_PROMPT" not in src
    assert "adversarial reviewer" not in src.lower()


def test_uses_httpx_post() -> None:
    src = _source()
    assert "httpx.post" in src or "httpx.Client" in src or "httpx.AsyncClient" in src


def test_reads_judge_urls_from_env() -> None:
    src = _source()
    assert "SESSION_JUDGE_URL" in src
    assert "EVOLUTION_JUDGE_URL" in src
    assert "SESSION_INVOKE_TOKEN" in src
    assert "EVOLUTION_INVOKE_TOKEN" in src
