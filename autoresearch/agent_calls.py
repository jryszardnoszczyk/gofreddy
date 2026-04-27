"""AsyncOpenAI + Pydantic helpers for autoresearch agent calls (R-#29+).

Thin wrapper used by ``select_parent.py`` today; other autoresearch modules
that need an in-process LLM judgment (future units) should reuse this helper
so provider imports stay isolated to one file.

Design notes:
  - Single-turn structured-output calls only. No multi-step agents here —
    multi-step work belongs in the Claude CLI subprocess path.
  - Response shape is pinned via Pydantic; malformed responses raise so the
    caller can decide whether to retry or hard-fail (per plan: agent failure
    = generation failure, meta-agent retries next cycle).
  - No caching at this layer — infrequent calls per plan.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Literal

from openai import AsyncOpenAI
from pydantic import BaseModel, Field, field_validator


# Model constant — follows the existing AsyncOpenAI pattern in
# ``src/evaluation/judges/openai.py`` which uses ``gpt-5.4``. Override per
# call if another model is desired; no ``model_router`` entry needed because
# autoresearch agent calls are rare and cost-trivial.
DEFAULT_MODEL = "gpt-5.4"


class ParentSelection(BaseModel):
    """Pydantic schema for the parent-selection agent response."""

    parent_id: str = Field(..., min_length=1, description="id of the chosen parent variant")
    rationale: str = Field(..., min_length=1, description="1-3 sentence justification balancing exploration vs exploitation")
    confidence: Literal["high", "medium", "low"] = Field(..., description="agent's confidence in the pick")

    @field_validator("parent_id")
    @classmethod
    def _strip_parent_id(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("parent_id must be non-empty after strip")
        return v

    @field_validator("rationale")
    @classmethod
    def _strip_rationale(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("rationale must be non-empty after strip")
        return v


_SELECT_PARENT_PROMPT = """You are selecting the next parent variant for autoresearch evolution, lane={lane}.

Candidates (top-{k} by objective_score):
{candidate_block}

Recent trajectory (last {traj_n} generations, oldest -> newest):
{trajectory_block}

Your job is NOT "pick the best variant." It is to pick a parent that balances
EXPLORATION (novel directions, under-explored prompt modifications, diverse
failure modes vs. current frontier) against EXPLOITATION (fit, pass-rate
gains, rising trajectory).

Prefer: (a) parents with rising trajectory, (b) diverse failure modes vs.
current frontier, (c) parents whose children under-explored the space.
Penalize: (a) plateau children (composite variance <0.01 across >=4 children),
(b) high max_fixture_sd at high composite (fixture saturation).

Without this balance, the loop risks mode collapse toward safe-looking
variants. Your rationale MUST explicitly name the balance struck (what was
exploration pressure, what was exploitation pressure, why this parent).

Return STRICT JSON matching:
{{"parent_id": "<id from the candidates above>",
  "rationale": "<1-3 sentences naming the exploration-vs-exploitation balance>",
  "confidence": "high" | "medium" | "low"}}
"""


def _format_candidates(candidates: list[dict]) -> str:
    lines: list[str] = []
    for c in candidates:
        lines.append(
            f"- id={c.get('id')} score={c.get('score')} children={c.get('children')} "
            f"mean_keep={c.get('mean_keep')} max_fixture_sd={c.get('max_fixture_sd')} "
            f"children_deltas={c.get('children_deltas')} "
            f"best_child_score={c.get('best_child_score')} status={c.get('status')}"
        )
    return "\n".join(lines) if lines else "(no candidates)"


def _format_trajectory(gen_rows: list[dict]) -> str:
    if not gen_rows:
        return "(cold start — no trajectory rows yet; use candidate snapshot only)"
    lines: list[str] = []
    for r in gen_rows:
        lines.append(
            f"- gen_id={r.get('gen_id')} mean_composite={r.get('mean_composite')} "
            f"mean_keep={r.get('mean_keep')} inner_outer_corr={r.get('inner_outer_corr')}"
        )
    return "\n".join(lines)


def build_select_parent_prompt(
    candidates: list[dict], gen_rows: list[dict], lane: str,
) -> str:
    """Render the exploration-vs-exploitation parent-selection prompt."""
    return _SELECT_PARENT_PROMPT.format(
        lane=lane,
        k=len(candidates),
        traj_n=len(gen_rows),
        candidate_block=_format_candidates(candidates),
        trajectory_block=_format_trajectory(gen_rows),
    )


async def _call_openai_json(
    prompt: str,
    *,
    model: str = DEFAULT_MODEL,
    timeout: int = 30,
    api_key: str | None = None,
) -> str:
    """Low-level AsyncOpenAI call returning raw JSON text content.

    Caller is responsible for Pydantic validation.

    Multi-provider routing: when ``AUTORESEARCH_PARENT_BASE_URL`` is set,
    requests are routed to that endpoint (must be OpenAI-compatible — e.g.,
    OpenRouter at https://openrouter.ai/api/v1). When
    ``AUTORESEARCH_PARENT_API_KEY`` is set, it overrides ``OPENAI_API_KEY``
    for this client only. When ``AUTORESEARCH_PARENT_MODEL`` is set, it
    overrides the default ``model`` parameter — required when the routed
    endpoint expects a qualified slug (e.g., OpenRouter requires
    ``openai/gpt-5.4`` rather than the bare ``gpt-5.4`` default).
    """
    explicit_key = api_key or os.environ.get("AUTORESEARCH_PARENT_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not explicit_key:
        raise RuntimeError(
            "OPENAI_API_KEY (or AUTORESEARCH_PARENT_API_KEY) is not set — cannot run autoresearch agent call"
        )
    base_url = os.environ.get("AUTORESEARCH_PARENT_BASE_URL") or None
    resolved_model = os.environ.get("AUTORESEARCH_PARENT_MODEL") or model
    client = AsyncOpenAI(api_key=explicit_key, base_url=base_url)
    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=resolved_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                response_format={"type": "json_object"},
            ),
            timeout=timeout,
        )
        choice = response.choices[0]
        if choice.finish_reason not in ("stop", "length"):
            raise RuntimeError(
                f"autoresearch agent call got bad finish_reason={choice.finish_reason}"
            )
        content = choice.message.content
        if not content:
            raise RuntimeError("autoresearch agent call returned empty content")
        return content
    finally:
        await client.close()


async def select_parent_agent(
    candidates: list[dict],
    gen_rows: list[dict],
    lane: str,
    *,
    model: str = DEFAULT_MODEL,
    timeout: int = 30,
) -> ParentSelection:
    """Call the parent-selection agent and return a validated ``ParentSelection``.

    Raises ``RuntimeError`` on API / connection failures, ``pydantic.ValidationError``
    on schema violations, and ``ValueError`` on malformed JSON. The caller
    (``select_parent.py``) surfaces any of these as a generation failure — no
    sigmoid fallback.
    """
    prompt = build_select_parent_prompt(candidates, gen_rows, lane)
    content = await _call_openai_json(prompt, model=model, timeout=timeout)
    try:
        raw = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"parent-selection agent returned non-JSON: {exc}: {content[:200]}") from exc
    return ParentSelection.model_validate(raw)
