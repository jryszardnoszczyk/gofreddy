"""Parser for OpenCode's `--format json` JSONL output.

Each line of OpenCode's session log is a JSON object. We extract:
  - per-step USD cost (sum across step_finish events)
  - cache utilization (sum of cache.read across step_finish events)
  - final answer text (last `text` event with phase="final_answer", or last
    text before the terminal step_finish with reason="stop")

Spec: docs/superpowers/specs/2026-04-26-multi-provider-agentic-pipeline-design.md
Appendix A documents the event schema as verified 2026-04-26.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SessionSummary:
    """Aggregate result of parsing a single OpenCode JSONL session log."""

    total_cost: float = 0.0
    total_cache_reads: int = 0
    final_answer: str | None = None


def parse_session(log_path: Path) -> SessionSummary:
    """Parse an OpenCode JSONL log file. Malformed lines are skipped."""
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
                    metadata = part.get("metadata") or {}
                    openai_meta = metadata.get("openai") or {}
                    if openai_meta.get("phase") == "final_answer":
                        final_answer = text

    return SessionSummary(
        total_cost=total_cost,
        total_cache_reads=total_cache_reads,
        final_answer=final_answer,
    )


# Transient OpenRouter / upstream-provider failure markers worth retrying.
# All three appear as `{"type":"error","error":{"data":{"message":"..."}}}`
# events in the JSONL while the opencode subprocess still exits 0 (it
# captures the API failure rather than crashing). Sources observed in
# the wild against deepseek-v4-pro:
#   - "rate_limit_exceeded" / 429 — Together / DeepSeek throttling
#   - "provider_overloaded" / 503 — Together capacity blip
#   - "timeout" / 504 — upstream inference timeout (Novita has 22s default)
_TRANSIENT_ERROR_MARKERS = (
    "rate_limit_exceeded",
    "provider_overloaded",
    "timeout",
    "\"code\":429",
    "\"code\":503",
    "\"code\":504",
)


def session_has_transient_error(log_path: Path) -> bool:
    """Return True if the JSONL log contains an error event worth retrying.

    Used by the harness/evolve/alert dispatch layers to retry opencode
    invocations that completed cleanly at the subprocess level but failed
    at the upstream-provider level. Distinct from session_succeeded: a
    transient error means "try again", not "give up."
    """
    if not log_path.exists():
        return False
    with log_path.open("r", encoding="utf-8") as fh:
        return any(_line_is_transient_error(line) for line in fh)


def stdout_has_transient_error(stdout: str) -> bool:
    """In-memory variant of session_has_transient_error.

    The alert agent in compute_metrics.py captures opencode stdout into a
    string (no log file), so retry detection there walks the string. Same
    set of transient markers; same semantics.
    """
    if not stdout:
        return False
    return any(_line_is_transient_error(line) for line in stdout.splitlines())


def _line_is_transient_error(line: str) -> bool:
    line = line.strip()
    if not line or '"type":"error"' not in line:
        return False
    return any(marker in line for marker in _TRANSIENT_ERROR_MARKERS)
