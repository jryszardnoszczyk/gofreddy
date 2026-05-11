"""Shared helpers for the simple decision agents (canary/promotion/rollback).

Per Plan D D5 (2026-05-11): the 3 single-decision agents share ~30 LOC of
boilerplate (load prompt → invoke claude → extract JSON → validate
decision). This module factors that out behind a `make_decide` factory
so each agent file collapses to a 15-LOC declaration.

Wire format unchanged: each agent still exposes an async `decide(payload)`
that returns the same dict shape.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Awaitable, Callable

from judges.invoke_cli import invoke_claude


_JSON_BLOCK = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)
_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def _extract_json(agent_name: str, text: str) -> dict[str, Any]:
    match = _JSON_BLOCK.search(text)
    raw = match.group(1) if match else text.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{agent_name}: could not parse JSON verdict: {exc}") from exc


def make_decide(
    *,
    agent_name: str,
    prompt_filename: str,
    allowed: set[str],
    format_kwargs: Callable[[dict[str, Any]], dict[str, str]],
) -> Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]:
    """Build an async `decide(payload)` for a single-decision agent.

    `format_kwargs(payload)` returns the dict passed to `prompt.format(**...)`
    — typically json.dumps'd payload subsections.
    """
    prompt_path = _PROMPTS_DIR / prompt_filename

    async def decide(payload: dict[str, Any]) -> dict[str, Any]:
        prompt = prompt_path.read_text().format(**format_kwargs(payload))
        stdout = await invoke_claude(prompt)
        verdict = _extract_json(agent_name, stdout)
        decision = verdict.get("decision")
        if decision not in allowed:
            raise RuntimeError(f"{agent_name}: invalid decision {decision!r}")
        return {
            "decision": decision,
            "reasoning": verdict.get("reasoning", ""),
            "confidence": verdict.get("confidence"),
            "concerns": verdict.get("concerns", []),
        }

    return decide
