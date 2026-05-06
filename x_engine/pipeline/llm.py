"""LLM provider wrapper. v2: Codex CLI subprocess (uses JR's ChatGPT subscription).

No paid API. `codex exec` runs against gpt-5.5 (default) under the user's logged-in
ChatGPT plan, so cost-per-call is $0 — only subject to plan rate limits.

Provider-agnostic interface so swapping back to OpenAI/Anthropic API is one file edit.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CODEX_BIN = os.environ.get("X_ENGINE_CODEX_BIN", "codex")
DEFAULT_EFFORT = os.environ.get("X_ENGINE_REASONING_EFFORT", "low")
DEFAULT_TIMEOUT_SECONDS = int(os.environ.get("X_ENGINE_TIMEOUT_S", "180"))

# Models / labels — kept for backwards-compat with call sites.
# The actual model is whatever JR's logged-in Codex plan defaults to (gpt-5.5).
DEFAULT_WRITER_MODEL = "codex-default"
DEFAULT_CRITIC_MODEL = "codex-default"
DEFAULT_TOPIC_MODEL = "codex-default"


@dataclass
class LLMResponse:
    text: str
    input_tokens: int
    output_tokens: int
    model: str

    @property
    def cost_usd(self) -> float:
        # Codex CLI uses ChatGPT subscription — no per-call cost.
        return 0.0


def _strict_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Recursively add `additionalProperties: false` to every object in a schema.

    OpenAI strict mode requires this. We allow callers to omit it for readability.
    """
    if isinstance(schema, dict):
        if schema.get("type") == "object" and "additionalProperties" not in schema:
            schema = dict(schema)
            schema["additionalProperties"] = False
        return {k: _strict_schema(v) for k, v in schema.items()}
    if isinstance(schema, list):
        return [_strict_schema(v) for v in schema]
    return schema


class LLM:
    """Codex CLI subprocess wrapper. Stateless, single-shot ephemeral calls.

    Each call_json:
      1. Concatenates system + user into one prompt (codex doesn't separate them)
      2. Writes schema to a temp file
      3. subprocess: codex exec --ephemeral -s read-only --output-schema F --output-last-message F2
      4. Parses last-message file as JSON
    """

    def __init__(self, api_key: str | None = None):
        # api_key kwarg kept for back-compat with the OpenAI version; ignored.
        # Verify codex is reachable.
        try:
            subprocess.run(
                [CODEX_BIN, "--version"],
                check=True,
                capture_output=True,
                timeout=10,
            )
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            raise RuntimeError(
                f"codex CLI not reachable as '{CODEX_BIN}'. Install Codex or set X_ENGINE_CODEX_BIN. ({e})"
            ) from e

    def call_json(
        self,
        *,
        system: str,
        user: str,
        model: str | None = None,  # ignored — codex uses logged-in plan default
        max_output_tokens: int = 4000,  # ignored — codex doesn't expose this flag
        temperature: float = 0.7,  # ignored — codex doesn't expose
        schema: dict[str, Any] | None = None,
        effort: str | None = None,
    ) -> tuple[dict[str, Any], LLMResponse]:
        """Call codex exec, return (parsed_dict, raw_response).

        Raises ValueError if the model returns invalid JSON (rare with --output-schema).
        Raises RuntimeError on subprocess failure (timeout, non-zero exit).
        """
        prompt = (
            "=== SYSTEM PROMPT ===\n\n"
            + system
            + "\n\n=== USER MESSAGE ===\n\n"
            + user
            + "\n\nReturn ONLY the requested JSON. No prose, no preamble, no commentary."
        )
        with tempfile.TemporaryDirectory() as tmp:
            schema_path = Path(tmp) / "schema.json"
            output_path = Path(tmp) / "out.txt"
            if schema:
                schema_path.write_text(json.dumps(_strict_schema(schema)))

            cmd = [
                CODEX_BIN,
                "exec",
                "--ephemeral",
                "--skip-git-repo-check",
                "--ignore-user-config",  # avoid loading project AGENTS.md etc — clean room
                "-s", "read-only",
                "--color", "never",
                "-c", f"model_reasoning_effort={effort or DEFAULT_EFFORT}",
                "--output-last-message", str(output_path),
            ]
            if schema:
                cmd += ["--output-schema", str(schema_path)]
            cmd.append("-")  # read prompt from stdin

            try:
                result = subprocess.run(
                    cmd,
                    input=prompt,
                    text=True,
                    capture_output=True,
                    timeout=DEFAULT_TIMEOUT_SECONDS,
                )
            except subprocess.TimeoutExpired as e:
                raise RuntimeError(
                    f"codex exec timed out after {DEFAULT_TIMEOUT_SECONDS}s"
                ) from e

            if result.returncode != 0:
                raise RuntimeError(
                    f"codex exec failed (exit {result.returncode}): {result.stderr[:500]}"
                )

            if not output_path.exists():
                raise RuntimeError(
                    f"codex exec produced no output file. stderr: {result.stderr[:500]}"
                )
            text = output_path.read_text().strip()

        # Best-effort token count — parse from stderr "tokens used" line if present
        tokens_used = 0
        for line in (result.stderr or "").splitlines():
            if "tokens used" in line.lower():
                try:
                    tokens_used = int(float(line.split()[-1]) * 1000)
                except (ValueError, IndexError):
                    pass

        llm_resp = LLMResponse(
            text=text,
            input_tokens=tokens_used,  # codex doesn't split in/out — bundle into input
            output_tokens=0,
            model=model or "codex-default",
        )
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Codex returned invalid JSON: {e}\nRaw: {text[:500]}"
            ) from e
        return parsed, llm_resp
