"""Session-time trusted critique agent."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from judges.invoke_cli import invoke_claude, invoke_codex


_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "critique.md"
_JSON_BLOCK = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


def _load_prompt() -> str:
    return _PROMPT_PATH.read_text()


def _extract_json(text: str) -> dict[str, Any]:
    match = _JSON_BLOCK.search(text)
    raw = match.group(1) if match else text.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"critique_agent: could not parse JSON verdict: {exc}") from exc


async def _dispatch(prompt: str) -> str:
    """Per-step model split (2026-05-13): route session-time critique through
    CRITIQUE_BACKEND/CRITIQUE_MODEL. Default codex/gpt-5.5 because v5
    burned the Claude Max 5h pool with hardcoded claude opus critiques on
    every fixture session. invoke_claude stays the fallback for environments
    without codex installed.
    """
    backend = os.environ.get("CRITIQUE_BACKEND", "codex").strip().lower()
    model = os.environ.get("CRITIQUE_MODEL", "").strip()
    if backend == "claude":
        return await invoke_claude(prompt, model=model or "claude-opus-4-7")
    return await invoke_codex(prompt, model=model or "gpt-5.5")


async def critique(payload: dict[str, Any]) -> dict[str, Any]:
    """Run critique. Payload: ``{session_artifacts, session_goal}``.

    Returns the structured critique dict with ``overall``, ``confidence``,
    ``issues[]``, ``rationale``.
    """
    prompt = _load_prompt().format(
        session_artifacts=payload.get("session_artifacts", ""),
        session_goal=payload.get("session_goal", ""),
    )
    stdout = await _dispatch(prompt)
    return _extract_json(stdout)
