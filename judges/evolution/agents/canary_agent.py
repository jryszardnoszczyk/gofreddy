"""Autonomous canary go / fail / revise decision agent."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from judges.invoke_cli import invoke_claude


_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "canary.md"
_JSON_BLOCK = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)
_ALLOWED = {"go", "fail", "revise"}


def _load_prompt() -> str:
    return _PROMPT_PATH.read_text()


def _extract_json(text: str) -> dict[str, Any]:
    match = _JSON_BLOCK.search(text)
    raw = match.group(1) if match else text.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"canary_agent: could not parse JSON verdict: {exc}") from exc


async def decide(payload: dict[str, Any]) -> dict[str, Any]:
    prompt = _load_prompt().format(
        canary_checkpoints=json.dumps(payload.get("canary_checkpoints", {}), sort_keys=True),
        variant_id=payload.get("variant_id", ""),
    )
    stdout = await invoke_claude(prompt)
    verdict = _extract_json(stdout)
    decision = verdict.get("decision")
    if decision not in _ALLOWED:
        raise RuntimeError(f"canary_agent: invalid decision {decision!r}")
    return {
        "decision": decision,
        "reasoning": verdict.get("reasoning", ""),
        "confidence": verdict.get("confidence"),
        "concerns": verdict.get("concerns", []),
    }
