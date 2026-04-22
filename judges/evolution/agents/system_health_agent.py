"""Role-dispatched advisory agent for system-health concerns.

Six roles share a single prompt file with distinct sections. Each request
picks the matching section; the agent invocation is a fresh CLI call so
no cross-concern context leaks.

Batching: when ``items`` is a list of N>1 entries, evaluate each item
independently in one call (up to 20). Parse-failure falls back to
per-item calls; the fallback is logged upstream via
``autoresearch.events.log_event(kind="judge_batch_fallback")``.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from judges.invoke_cli import invoke_claude


_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "system_health.md"
_JSON_BLOCK = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)

ROLES = {
    "saturation",
    "content_drift",
    "discriminability",
    "fixture_quality",
    "calibration_drift",
    "noise_escalation",
}

MAX_BATCH_SIZE = 20


def _load_prompt() -> str:
    return _PROMPT_PATH.read_text()


def _section_for_role(role: str) -> str:
    """Extract the ``## {role}`` section of the prompt."""
    prompt = _load_prompt()
    pattern = re.compile(
        rf"^## {re.escape(role)}\s*$(.*?)(?=^## |\Z)",
        re.DOTALL | re.MULTILINE,
    )
    m = pattern.search(prompt)
    if not m:
        raise RuntimeError(f"system_health_agent: prompt section for role {role!r} missing")
    return m.group(1).strip()


def _extract_json(text: str) -> Any:
    match = _JSON_BLOCK.search(text)
    raw = match.group(1) if match else text.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"system_health_agent: could not parse JSON verdict: {exc}") from exc


def _format_batch_prompt(role: str, items: list[Any]) -> str:
    section = _section_for_role(role)
    header = (
        f"Role: {role}\n"
        f"Evaluate each of the following {len(items)} items independently; "
        "peer-ranked, not sequential.\n\n"
    )
    body = json.dumps({"items": items}, sort_keys=True, indent=2)
    return f"{header}{section}\n\n<items>\n{body}\n</items>"


def _format_single_prompt(role: str, item: Any) -> str:
    section = _section_for_role(role)
    body = json.dumps(item, sort_keys=True, indent=2)
    return f"Role: {role}\n\n{section}\n\n<input>\n{body}\n</input>"


async def evaluate(role: str, payload: dict[str, Any]) -> Any:
    """Evaluate a system-health concern.

    Payload either has ``item`` (single) or ``items`` (list — batched).
    Returns a single verdict dict for single-item calls, or a list of
    verdicts for batched calls.
    """
    if role not in ROLES:
        raise RuntimeError(f"system_health_agent: unknown role {role!r}")

    if "items" in payload:
        items = list(payload["items"])
        if len(items) > MAX_BATCH_SIZE:
            raise RuntimeError(
                f"system_health_agent: batch size {len(items)} exceeds max {MAX_BATCH_SIZE}"
            )
        prompt = _format_batch_prompt(role, items)
        stdout = await invoke_claude(prompt)
        return _extract_json(stdout)

    prompt = _format_single_prompt(role, payload.get("item", payload))
    stdout = await invoke_claude(prompt)
    return _extract_json(stdout)
