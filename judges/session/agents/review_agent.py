"""Session-time adversarial review agent.

Loads the review prompt, renders it with the payload, invokes the claude
CLI, and parses a fenced JSON block out of stdout. Returns the verdict
dict. Parse failures raise ``RuntimeError`` — callers treat that as a
judge-unreachable-equivalent (never silently substitute a fallback).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from judges.invoke_cli import invoke_claude


_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "review.md"
_JSON_BLOCK = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


def _load_prompt() -> str:
    return _PROMPT_PATH.read_text()


def _extract_json(text: str) -> dict[str, Any]:
    match = _JSON_BLOCK.search(text)
    raw = match.group(1) if match else text.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"review_agent: could not parse JSON verdict: {exc}") from exc


async def review(payload: dict[str, Any]) -> dict[str, Any]:
    """Run adversarial review. Payload: ``{original_content, proposed_changes, competitive_context}``.

    Returns ``{decision, confidence, weaknesses[], rationale}``.
    """
    prompt = _load_prompt().format(
        original_content=payload.get("original_content", "Original content not available."),
        proposed_changes=payload.get("proposed_changes", ""),
        competitive_context=payload.get("competitive_context", "No competitive data available."),
    )
    stdout = await invoke_claude(prompt)
    verdict = _extract_json(stdout)
    # Normalize to the documented contract.
    return {
        "decision": verdict.get("decision"),
        "confidence": verdict.get("confidence"),
        "weaknesses": verdict.get("weaknesses", []),
        "rationale": verdict.get("rationale", ""),
    }
