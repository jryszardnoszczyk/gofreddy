"""Pareto-constraint critique agent for program mutations (R-#15).

Soft-review-only critic that reads the (old, new) pair of each
``programs/<domain>-session.md`` after the meta agent mutates a variant, and
emits an *advisory* verdict distinguishing PRESCRIPTION (imperative edits:
"do X", banned word lists, edit-order mandates) from DESCRIPTION (quality
criteria, structural gate requirements, data grounding expectations).

Per the Unit 9 softening in
``docs/plans/2026-04-22-007-refactor-pipeline-simplifications-plan.md``, the
critic **never rejects** — it only appends a markdown section to
``variant_dir/critic_reviews.md`` so the operator can eyeball drift over
time. The verdict enum is narrowed to ``{"advise", "no-change"}``.

Escape valve
------------
Set ``EVOLVE_SKIP_PRESCRIPTION_CRITIC=1`` to bypass the critic entirely
(returns an empty dict without calling any subprocess). Intended for
intentional "add new structural requirement" cycles or infra outages.

Failure mode
------------
Subprocess timeout, non-zero exit, or JSON parse failure: log a WARN to
stderr and return ``{"verdict": "no-change", "reasoning": "<why failed>"}``
for the affected domain. Evolution continues unblocked — this is soft
review; infra issues must not stall the loop.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, TypedDict

DOMAINS = ("geo", "competitive", "monitoring", "storyboard")

Verdict = Literal["advise", "no-change"]


class CriticResult(TypedDict):
    verdict: Verdict
    reasoning: str


# Per-domain critic subprocess timeout. The critic reads two small markdown
# files and returns a short JSON object; 120s is generous.
_CRITIC_TIMEOUT_SECONDS = 120

_PROMPT_TEMPLATE = """You are a program-mutation critic evaluating a change to an LLM agent's \
session program. The program tells a research agent how to work — it should \
describe *what good looks like* and *what the structural gate requires*, NOT \
dictate *how* to work.

PRESCRIPTION = a rule the agent must follow, a banned word list, an edit-order
mandate, a fixed heuristic ("em-dash > 1/page = rewrite"), a forced taxonomy,
imperative edits ("do X", "never use Y", "always rewrite if Z").
DESCRIPTION = a quality criterion, a data grounding expectation, a structural
requirement imposed by the gate, an observation of what good work looks like.

Read OLD_PROGRAM and NEW_PROGRAM below. Judge whether the diff adds net
PRESCRIPTION. Output a single JSON object (no prose before or after) with
exactly these keys:

{{
  "verdict": "advise" | "no-change",
  "reasoning": "<one-to-three sentences citing specific lines if advising>"
}}

Verdict rules (soft review — advisory only, never blocks):
- "advise" if the diff introduces net new prescription (new imperatives,
  rules, banned terms, forced taxonomies, edit-order mandates) that the
  operator should eyeball.
- "no-change" if the diff is prescription-neutral or net-removes prescription
  (compression, clarification, or replacing imperatives with descriptive
  criteria).

=== OLD_PROGRAM ({domain}) ===
{old_program}

=== NEW_PROGRAM ({domain}) ===
{new_program}
"""


def _build_prompt(domain: str, old_program: str, new_program: str) -> str:
    return _PROMPT_TEMPLATE.format(
        domain=domain, old_program=old_program, new_program=new_program
    )


def _build_claude_cmd(prompt: str, model: str = "claude-sonnet-4-5") -> list[str]:
    """Claude CLI subprocess, matching ``harness/engine.py:_build_claude_cmd`` shape.

    Uses ``--print`` (non-streaming) since the critic reads a single JSON
    response, not a live stream. Generates a fresh session id so concurrent
    variant evaluations don't collide.
    """
    session_id = str(uuid.uuid4())
    return [
        "claude",
        "--bare",
        "-p",
        prompt,
        "--output-format",
        "json",
        "--session-id",
        session_id,
        "--model",
        model,
        "--dangerously-skip-permissions",
    ]


def _extract_json_object(text: str) -> dict | None:
    """Pull the first balanced ``{...}`` object out of raw CLI output.

    Claude's ``--output-format json`` wraps the assistant turn in an envelope
    like ``{"type": "result", "result": "<inner json or prose>"}``. We try the
    envelope first, then fall back to a greedy object scan so the parser
    tolerates both shapes + any stray prose the model emits around the JSON.
    """
    text = text.strip()
    if not text:
        return None

    # Envelope case: whole stdout is a JSON object with a ``result`` field
    # whose value is the model's text (which itself contains our JSON).
    try:
        envelope = json.loads(text)
        if isinstance(envelope, dict):
            inner = envelope.get("result") or envelope.get("text") or envelope
            if isinstance(inner, str):
                return _extract_json_object(inner)
            if isinstance(inner, dict) and "verdict" in inner:
                return inner
    except json.JSONDecodeError:
        pass

    # Greedy object scan: find the first {...} that parses as JSON.
    for match in re.finditer(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.DOTALL):
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, dict) and "verdict" in parsed:
                return parsed
        except json.JSONDecodeError:
            continue
    return None


def _normalize_result(payload: dict | None) -> CriticResult:
    """Coerce raw LLM output into the contract shape.

    Unknown verdict strings collapse to ``"no-change"`` (soft review default —
    never block on malformed output). Missing/empty reasoning gets a
    placeholder so the contract's non-empty-string guarantee holds.
    """
    if not isinstance(payload, dict):
        return {"verdict": "no-change", "reasoning": "Critic returned no parseable JSON."}

    verdict_raw = str(payload.get("verdict", "")).strip().lower()
    verdict: Verdict = "advise" if verdict_raw == "advise" else "no-change"

    reasoning = str(payload.get("reasoning", "")).strip()
    if not reasoning:
        reasoning = "Critic returned empty reasoning; defaulting to no-change."

    return {"verdict": verdict, "reasoning": reasoning}


def _call_claude(prompt: str, model: str = "claude-sonnet-4-5") -> CriticResult:
    """Run the Claude CLI subprocess; catch every failure and fall back to no-change."""
    cmd = _build_claude_cmd(prompt, model=model)
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=_CRITIC_TIMEOUT_SECONDS,
            check=False,
        )
    except FileNotFoundError:
        print(
            "[program_prescription_critic] WARN: claude CLI not on PATH; skipping.",
            file=sys.stderr,
        )
        return {"verdict": "no-change", "reasoning": "claude CLI not found on PATH."}
    except subprocess.TimeoutExpired:
        print(
            f"[program_prescription_critic] WARN: critic timed out after "
            f"{_CRITIC_TIMEOUT_SECONDS}s; continuing.",
            file=sys.stderr,
        )
        return {"verdict": "no-change", "reasoning": "Critic subprocess timed out."}
    except Exception as exc:  # noqa: BLE001 — soft review, never block evolution
        print(
            f"[program_prescription_critic] WARN: subprocess error: {exc}",
            file=sys.stderr,
        )
        return {"verdict": "no-change", "reasoning": f"Subprocess error: {exc}"}

    if proc.returncode != 0:
        print(
            f"[program_prescription_critic] WARN: claude exit={proc.returncode}; "
            f"stderr={proc.stderr[:500]}",
            file=sys.stderr,
        )
        return {
            "verdict": "no-change",
            "reasoning": f"Critic subprocess exited {proc.returncode}.",
        }

    payload = _extract_json_object(proc.stdout)
    return _normalize_result(payload)


def critique_program(
    domain: str,
    old_program: str,
    new_program: str,
    *,
    model: str = "claude-sonnet-4-5",
) -> CriticResult:
    """Run the critic on a single domain's (old, new) program pair.

    Returns a contract-shaped dict unconditionally — never raises, never
    returns ``None``. If OLD == NEW we short-circuit without burning a
    Claude call (common case: meta agent didn't touch this domain).
    """
    if old_program == new_program:
        return {
            "verdict": "no-change",
            "reasoning": "Program file unchanged vs parent.",
        }
    prompt = _build_prompt(domain, old_program, new_program)
    return _call_claude(prompt, model=model)


def _append_review(variant_dir: Path, domain: str, result: CriticResult) -> None:
    """Append the critic's advisory to ``variant_dir/critic_reviews.md``.

    The file is created on first write; subsequent calls append. Timestamp
    is ISO-8601 UTC so review entries sort chronologically without parsing.
    """
    variant_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = (
        f"## {ts} — {domain}\n\n"
        f"- **verdict:** `{result['verdict']}`\n"
        f"- **reasoning:** {result['reasoning']}\n\n"
    )
    review_path = variant_dir / "critic_reviews.md"
    with review_path.open("a", encoding="utf-8") as f:
        f.write(entry)


def _read_program(programs_dir: Path, domain: str) -> str | None:
    path = programs_dir / f"{domain}-session.md"
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def critique_all_programs(
    parent_dir: Path,
    variant_dir: Path,
    *,
    lane: str | None = None,
    env: dict[str, str] | None = None,
    model: str = "claude-sonnet-4-5",
) -> dict[str, CriticResult]:
    """Run the critic on every changed program file between parent and variant.

    Args:
        parent_dir: The selected-parent archive snapshot (old program source).
        variant_dir: The newly mutated variant workspace (new program source).
        lane: Optional lane filter. Ignored for "core"/None (all domains
            critiqued); otherwise restricts to matching domain.
        env: Env mapping for the ``EVOLVE_SKIP_PRESCRIPTION_CRITIC`` check.
            Defaults to ``os.environ``.
        model: Claude model slug for the critic subprocess.

    Returns:
        Mapping of ``domain -> CriticResult``. Empty dict if the escape
        env var is set, or if no program files exist in either side.
    """
    effective_env = env if env is not None else os.environ
    if str(effective_env.get("EVOLVE_SKIP_PRESCRIPTION_CRITIC", "")).strip() == "1":
        return {}

    parent_programs = Path(parent_dir) / "programs"
    variant_programs = Path(variant_dir) / "programs"
    if not variant_programs.is_dir():
        return {}

    domains = DOMAINS
    if lane and lane != "core" and lane in DOMAINS:
        domains = (lane,)

    results: dict[str, CriticResult] = {}
    for domain in domains:
        old = _read_program(parent_programs, domain)
        new = _read_program(variant_programs, domain)
        if new is None:
            # Variant dropped the domain; soft-review emits an advisory but
            # doesn't touch the filesystem.
            continue
        if old is None:
            # New domain added — there's no "old" to diff against, so treat
            # the whole file as a fresh addition and advise.
            results[domain] = {
                "verdict": "advise",
                "reasoning": (
                    f"New program file introduced for {domain} (no parent version)."
                ),
            }
            _append_review(Path(variant_dir), domain, results[domain])
            continue

        result = critique_program(domain, old, new, model=model)
        results[domain] = result
        _append_review(Path(variant_dir), domain, result)

    return results


__all__ = [
    "CriticResult",
    "DOMAINS",
    "critique_all_programs",
    "critique_program",
]
