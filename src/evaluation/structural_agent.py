"""Claim-grounding agent for the monitoring structural validator.

Replaces R-#37's regex-based digest-hallucination guard with a Sonnet call
that extracts side-effect claims from ``session.md`` and verifies each
claim against the outputs bundle (evidence-span requirement).

Reuses the general-purpose Claude CLI subprocess helper shipped by Unit 11
at ``src/evaluation/judges/sonnet_agent.py`` — the round-trip shape
(prompt-in, JSON-out) is identical.

Failure policy: per the plan's "Agent-call failures" note (no silent
fallback), a Sonnet error converts to a single structural failure so the
caller sees the issue rather than silently passing the claim.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from .judges.sonnet_agent import SonnetAgentError, call_sonnet_json

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ClaimVerdict:
    """Per-claim verdict from the grounding agent."""

    claim: str
    supported: bool
    evidence_path: str | None
    reason: str


_PROMPT_TEMPLATE = """\
You are auditing a monitoring-session agent for claim fabrication.

The agent may have written narrative claims about side-effects it took
(e.g. "Digest persisted to ...", "Archive updated", "Metrics written to ...")
into session.md without actually running the command. Your job: extract
those side-effect claims and verify each one against the outputs bundle.

## session.md

{session_md}

## Available output file paths (outputs the agent actually produced)

{output_paths}

## Task

1. Extract every *side-effect claim* from session.md — a claim that
   asserts a file was written, a command was run, data was persisted,
   or an artifact was produced. Ignore analytical findings, summaries,
   and narrative without a concrete side-effect.
2. For each claim, determine whether the outputs bundle contains
   corroborating evidence (the file the claim names must appear in the
   output paths, or the claim must cite an output path that exists).
3. A claim is `supported: false` if the claim names a specific file and
   that file is absent, OR if the claim asserts a persistence /
   write-side-effect and no corresponding output exists.

## Output

Return a single JSON object with this exact shape, and nothing else:

{{
  "claims": [
    {{
      "claim": "<verbatim claim sentence from session.md>",
      "supported": true|false,
      "evidence_path": "<output path that grounds the claim, or null>",
      "reason": "<one short sentence>"
    }}
  ]
}}

If there are no side-effect claims, return `{{"claims": []}}`.
"""


def _build_prompt(session_md: str, output_paths: list[str]) -> str:
    # Cap paths list length — 300 paths is plenty, keeps prompt bounded.
    paths_block = "\n".join(f"- {p}" for p in sorted(output_paths)[:300])
    if not paths_block:
        paths_block = "(no output files)"
    return _PROMPT_TEMPLATE.format(
        session_md=session_md[:8000],  # Safety cap — session.md is usually <2KB
        output_paths=paths_block,
    )


async def verify_claims_async(
    session_md: str,
    outputs: dict[str, str],
    *,
    timeout: float | None = None,
) -> list[ClaimVerdict]:
    """Extract side-effect claims from ``session_md`` and verify them.

    Returns a list of :class:`ClaimVerdict`. An empty list means the
    agent found no side-effect claims worth checking — the validator
    should treat that as a clean pass.

    On Sonnet subprocess failure, raises :class:`SonnetAgentError` so
    the caller can surface a structural failure rather than a silent
    pass.
    """
    if not session_md.strip():
        return []

    prompt = _build_prompt(session_md, list(outputs.keys()))
    data = await call_sonnet_json(
        prompt, operation="structural_claim_grounding", timeout=timeout,
    )

    raw_claims = data.get("claims")
    if not isinstance(raw_claims, list):
        raise SonnetAgentError(
            f"claim-grounding response missing 'claims' list: {str(data)[:200]!r}"
        )

    verdicts: list[ClaimVerdict] = []
    for entry in raw_claims:
        if not isinstance(entry, dict):
            continue
        claim = entry.get("claim")
        if not isinstance(claim, str) or not claim.strip():
            continue
        supported = bool(entry.get("supported", False))
        evidence_path = entry.get("evidence_path")
        if evidence_path is not None and not isinstance(evidence_path, str):
            evidence_path = None
        reason = entry.get("reason", "")
        if not isinstance(reason, str):
            reason = ""
        verdicts.append(
            ClaimVerdict(
                claim=claim.strip(),
                supported=supported,
                evidence_path=evidence_path,
                reason=reason.strip(),
            )
        )
    return verdicts


__all__ = ["ClaimVerdict", "verify_claims_async", "SonnetAgentError"]
