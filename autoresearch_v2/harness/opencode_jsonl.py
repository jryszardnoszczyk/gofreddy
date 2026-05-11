"""Parser for OpenCode's `--format json` JSONL output.

Verbatim port of v1's opencode_jsonl.py (the alert agent + backend
retry path both depend on transient-error detection here — it's the
load-bearing function this module exists for).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SessionSummary:
    total_cost: float = 0.0
    total_cache_reads: int = 0
    final_answer: str | None = None


def parse_session(log_path: Path) -> SessionSummary:
    if not log_path.exists():
        return SessionSummary()

    total_cost = 0.0
    total_cache_reads = 0
    final_answer: str | None = None
    last_text: str | None = None

    with log_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            event_type = event.get("type")
            part = event.get("part") or {}

            if event_type == "step_finish":
                cost = part.get("cost")
                if isinstance(cost, (int, float)):
                    total_cost += float(cost)
                tokens = part.get("tokens") or {}
                cache = tokens.get("cache") or {}
                reads = cache.get("read")
                if isinstance(reads, int):
                    total_cache_reads += reads
                if part.get("reason") == "stop" and last_text is not None and final_answer is None:
                    final_answer = last_text
            elif event_type == "text":
                text = part.get("text")
                if isinstance(text, str):
                    last_text = text
                    openai_meta = (part.get("metadata") or {}).get("openai") or {}
                    if openai_meta.get("phase") == "final_answer":
                        final_answer = text

    return SessionSummary(
        total_cost=total_cost,
        total_cache_reads=total_cache_reads,
        final_answer=final_answer,
    )


# OpenRouter / upstream-provider transient failure markers (retry-worthy).
_TRANSIENT_ERROR_MARKERS = (
    "rate_limit_exceeded",
    "provider_overloaded",
    "timeout",
    "\"code\":429",
    "\"code\":503",
    "\"code\":504",
)


def _line_is_transient_error(line: str) -> bool:
    line = line.strip()
    if not line or '"type":"error"' not in line:
        return False
    return any(marker in line for marker in _TRANSIENT_ERROR_MARKERS)


def session_has_transient_error(log_path: Path) -> bool:
    if not log_path.exists():
        return False
    with log_path.open("r", encoding="utf-8") as fh:
        return any(_line_is_transient_error(line) for line in fh)


def stdout_has_transient_error(stdout: str) -> bool:
    if not stdout:
        return False
    return any(_line_is_transient_error(line) for line in stdout.splitlines())
