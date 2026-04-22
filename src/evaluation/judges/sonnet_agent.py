"""Claude Sonnet subprocess helper for evaluation paraphrase + calibration judges.

Used by Unit 11 (R-#32 paraphrase judge, R-#33 calibration judge). Matches the
"Claude Code CLI subprocess" runtime policy from
`docs/plans/2026-04-22-007-refactor-pipeline-simplifications-plan.md` (Key
Technical Decisions row "Agent runtime") — `claude -p …` with Sonnet.

The call shape is deliberately minimal compared to `harness/engine._build_claude_cmd`:
no stream-json, no session resume, no toolbelt. Evaluation judges only need a
short prompt → structured JSON response round-trip. Cost is recorded via
`src.common.cost_recorder` for observability.

Cost estimate (~$3/1M input, ~$15/1M output for Sonnet):
- Paraphrase batch call: ~500 tokens in / ~200 tokens out ≈ $0.005 per call.
- Calibration call: ~800 tokens in / ~200 tokens out ≈ $0.006 per call.
Per variant evaluation (4 domains × 8 criteria × ~2 judges):
- Paraphrase: 1 call per criterion per judge per output ≈ 64 calls ≈ $0.32.
- Calibration: 1 call per gradient criterion per judge ≈ 32 calls ≈ $0.19.
Total Unit 11 add-on: ~$0.50 per variant evaluation.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
from dataclasses import dataclass

from ...common.cost_recorder import cost_recorder

logger = logging.getLogger(__name__)

# Default model per plan "Judgment model = Sonnet" decision. Override via env for
# golden/regression replays pinned to an older model snapshot.
SONNET_MODEL: str = os.environ.get("EVAL_SONNET_MODEL", "claude-sonnet-4-6")

# Subprocess-wall timeout. Intentionally well under the judge's own 30s
# per-call timeout — a stuck agent should fail the downstream judge loudly
# rather than starve its deadline.
_CLAUDE_TIMEOUT: float = float(os.environ.get("EVAL_SONNET_TIMEOUT_S", "45"))

# Approximate per-million-token prices for cost recording. Treated as an
# estimate because the CLI does not surface token counts; we derive them from
# character count / 4 (OpenAI heuristic). The cost_recorder entry is annotated
# with `metadata={"estimated": True}` so downstream dashboards can distinguish.
_SONNET_INPUT_USD_PER_MTOK = 3.0
_SONNET_OUTPUT_USD_PER_MTOK = 15.0


@dataclass(frozen=True)
class SonnetAgentError(Exception):
    """Raised when the Sonnet subprocess call fails unrecoverably."""

    detail: str

    def __str__(self) -> str:  # pragma: no cover - dataclass-string
        return f"SonnetAgentError: {self.detail}"


def _approx_tokens(text: str) -> int:
    """~4 chars / token heuristic for cost estimation (CLI hides exact counts)."""
    return max(1, len(text) // 4)


async def _record_cost(operation: str, prompt: str, response: str) -> None:
    t_in = _approx_tokens(prompt)
    t_out = _approx_tokens(response)
    cost = (t_in / 1_000_000) * _SONNET_INPUT_USD_PER_MTOK + (
        t_out / 1_000_000
    ) * _SONNET_OUTPUT_USD_PER_MTOK
    await cost_recorder.record(
        "anthropic",
        operation,
        tokens_in=t_in,
        tokens_out=t_out,
        cost_usd=round(cost, 6),
        model=SONNET_MODEL,
        metadata={"estimated": True, "transport": "claude_cli"},
    )


async def call_sonnet_json(
    prompt: str,
    *,
    operation: str,
    model: str | None = None,
    timeout: float | None = None,
) -> dict:
    """Run `claude -p <prompt>` and return the parsed top-level JSON object.

    The prompt MUST instruct Claude to emit a single JSON object as its final
    output. We take the last JSON object in stdout to tolerate a preceding
    markdown-fenced block if Claude ignores the "no prose" instruction.

    Raises:
        SonnetAgentError on timeout, non-zero exit, missing CLI, or
        unparseable response.
    """
    claude_bin = shutil.which("claude")
    if claude_bin is None:
        raise SonnetAgentError("claude CLI not found on PATH")

    cmd = [
        claude_bin,
        "--bare",
        "-p",
        prompt,
        "--model",
        model or SONNET_MODEL,
        "--dangerously-skip-permissions",
        "--output-format",
        "text",
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_b, stderr_b = await asyncio.wait_for(
            proc.communicate(), timeout=timeout or _CLAUDE_TIMEOUT,
        )
    except asyncio.TimeoutError as e:
        raise SonnetAgentError(f"claude -p timed out after {timeout or _CLAUDE_TIMEOUT}s") from e
    except FileNotFoundError as e:
        raise SonnetAgentError(f"claude CLI missing: {e}") from e

    if proc.returncode != 0:
        stderr = stderr_b.decode("utf-8", errors="replace").strip()
        raise SonnetAgentError(f"claude -p exit {proc.returncode}: {stderr[:300]}")

    stdout = stdout_b.decode("utf-8", errors="replace")
    await _record_cost(operation, prompt, stdout)

    # Grab the last {...} block — tolerates an optional ```json fence.
    data = _extract_last_json_object(stdout)
    if data is None:
        raise SonnetAgentError(f"no JSON object in response: {stdout[:200]!r}")
    return data


def _extract_last_json_object(text: str) -> dict | None:
    """Return the last balanced JSON object in `text`, or None if absent."""
    # Cheap fast path — whole string is the object.
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            obj = json.loads(stripped)
        except json.JSONDecodeError:
            pass
        else:
            if isinstance(obj, dict):
                return obj

    # Fallback scanner — find last {...} balanced region. Small state machine,
    # string-aware, escape-aware. Sufficient for the bounded prompts we send.
    depth = 0
    in_string = False
    escape = False
    last_end = -1
    last_start = -1
    current_start = -1
    for i, ch in enumerate(text):
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            if depth == 0:
                current_start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and current_start >= 0:
                last_start = current_start
                last_end = i
                current_start = -1
    if last_start < 0 or last_end < 0:
        return None
    try:
        obj = json.loads(text[last_start : last_end + 1])
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) else None
