#!/usr/bin/env python3
"""Stage 1 transcript extraction — distills Codex CLI iteration_*.log.err
files into structured reasoning beats for downstream Stage-2 Opus rendering.

Spec section A8 (`docs/plans/2026-05-07-003-self-improving-report-rendering.md`).

Usage:
    extract_reasoning.py <session_dir>           # → JSON to stdout
    extract_reasoning.py <session_dir> -o out.json

The extraction is lane-agnostic: works for geo / competitive / monitoring /
storyboard sessions equally because they all run through the same Codex CLI
runner that emits `^codex$` reasoning markers, `^exec$` tool-call markers,
and `tokens used` footers per iteration.

Calibration tests (per spec A8.1) live at scripts/tests/test_extract_reasoning.py.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

CODEX_RE = re.compile(r"^codex$")
EXEC_RE = re.compile(r"^exec$")
TOKEN_RE = re.compile(r"^tokens used$")

# Heuristic markers — tuned 2026-05-08 against frozen sample transcripts
# (geo/nubank, competitive/figma, monitoring/Shopify) per A8.1 calibration.
# Pattern: classify on the first verb / first clause of the beat, not on
# substring matches throughout. "I have enough for a degraded but real
# baseline" must classify as `ship` (first clause = "I have enough"), not
# `hit_failure` despite the word "failed" appearing later.

# Order matters: more-specific patterns first, fallthrough to generic.
FIRST_CLAUSE_RULES = [
    # ship — concluding/persisting/done patterns (most specific first)
    (re.compile(r"^(.*phase complet|.*completed exactly|.*phase complete\b|completed exactly|i have enough|the .* is in place|the artifact is|i'll persist|i'm persisting|persisting the|state .* persisted|persisted (?:report|the))",
                re.IGNORECASE), "ship"),
    # recover — succeeded/passed/works after a failure
    (re.compile(r"^(.*now passes|.*scrape succeeded|.*succeeded|.*works|i have enough .* (?:for|to)|local checks passed|validation passed|local structural)",
                re.IGNORECASE), "recover"),
    # adapt — switching/falling-back/narrowing in response to a problem
    (re.compile(r"^(.*so i'm (?:retry|switch|narrow|using|adapt|adjust|fall|moving)|i'm (?:retry|switch|narrow|adjust|fall|adapt|moving|treating)|i'll (?:retry|switch|narrow|adapt|adjust|fall)|i am (?:retry|switch|narrow))",
                re.IGNORECASE), "adapt"),
    # hit_failure — current-tense failure of own action
    (re.compile(r"^(.*could not reach|.*returned (?:a |an |)connection_error|.*returned a connection|.*failed (?:with|because|to)|.*(?:rejected|refused) (?:the |my |)|.*the (?:evaluator|cli|api) (?:returned|rejected|failed|ignored|collapsed|capped))",
                re.IGNORECASE), "hit_failure"),
    # decide — committing to a phase/plan
    (re.compile(r"^(.*next (?:single |missing |)phase|.*i'm going to (?:complete|do|run|gather)|.*i'll (?:complete|do|run|gather)|.*i am going to (?:complete|do|run))",
                re.IGNORECASE), "decide"),
    # first_move — opening "read state first" pattern
    (re.compile(r"^(i'?ll (?:read|load|start by|pick up)|i'm (?:going to read|about to|reading)|let me (?:read|load))",
                re.IGNORECASE), "first_move"),
]


@dataclass
class Beat:
    iteration: int
    kind: str
    text: str
    line_no: int


@dataclass
class IterationExtract:
    iteration: int
    phase: str
    status: str
    reasoning_beats: list[Beat]
    tool_calls: list[str]
    tool_count: int
    token_count: float | None


def classify_beat(text: str, idx: int) -> str:
    """First-clause classifier — A8.1 fix.

    Looks at the first sentence/clause only; falls back to FIRST_MOVE for
    iteration-opening beats and `other` for anything not matched.
    """
    # First-move heuristic: very first beat of an iteration with the
    # "read state first" pattern.
    if idx == 0 and re.match(
        r"^(i'?ll (?:read|load|start)|i'm going to (?:read|load))",
        text, re.IGNORECASE
    ):
        return "first_move"

    # Take the first sentence (or first 200 chars if no period found).
    first = text.split(". ")[0]
    first = first[:200].lstrip("- ").lstrip()

    for pattern, label in FIRST_CLAUSE_RULES:
        if pattern.match(first):
            return label

    # Secondary check: substring of action language
    low = text.lower()
    if any(s in low for s in ("validating", "validate", "running structural",
                              "running checks", "checking", "verify")):
        return "validate"
    return "other"


def extract_phase_from_results(session_dir: Path, iteration: int) -> tuple[str, str]:
    """Map iteration → (phase, status) via results.jsonl."""
    rj = session_dir / "results.jsonl"
    if not rj.exists():
        return ("?", "?")
    for line in rj.read_text().splitlines():
        try:
            obj = json.loads(line)
            if obj.get("iteration") == iteration:
                return (obj.get("type", "?"), obj.get("status", "?"))
        except (ValueError, json.JSONDecodeError):
            continue
    return ("?", "?")


def extract_iteration(log_err: Path, iteration: int,
                      session_dir: Path) -> IterationExtract:
    lines = log_err.read_text().splitlines()
    beats: list[Beat] = []
    tool_calls: list[str] = []
    tokens: float | None = None

    i = 0
    beat_idx = 0
    while i < len(lines):
        ln = lines[i]
        if CODEX_RE.match(ln):
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            if j < len(lines):
                txt = lines[j].strip()
                if txt and len(txt) > 20:
                    beats.append(Beat(
                        iteration=iteration,
                        kind=classify_beat(txt, beat_idx),
                        text=txt,
                        line_no=j + 1,
                    ))
                    beat_idx += 1
            i = j + 1
            continue
        if EXEC_RE.match(ln):
            j = i + 1
            if j < len(lines):
                cmd = lines[j].strip()
                cmd = re.sub(r"^/bin/zsh -lc ['\"]", "", cmd)
                cmd = cmd[:200]
                if cmd:
                    tool_calls.append(cmd)
            i = j + 1
            continue
        if TOKEN_RE.match(ln):
            j = i + 1
            if j < len(lines):
                try:
                    tokens = float(lines[j].strip())
                except ValueError:
                    pass
            i = j + 1
            continue
        i += 1

    phase, status = extract_phase_from_results(session_dir, iteration)
    return IterationExtract(
        iteration=iteration,
        phase=phase,
        status=status,
        reasoning_beats=beats,
        tool_calls=tool_calls,
        tool_count=len(tool_calls),
        token_count=tokens,
    )


def detect_pivots(iterations: list[IterationExtract]) -> list[dict]:
    """A8.1 fallback rule: emit any (hit_failure → adapt|recover|ship)
    transition AND any (decide → adapt) transition, in addition to the
    primary heuristic. Recall ≥80% on calibration set."""
    pivots = []
    for it in iterations:
        for i, b in enumerate(it.reasoning_beats):
            if i == 0:
                continue
            prev = it.reasoning_beats[i - 1]
            if (prev.kind == "hit_failure" and b.kind in ("adapt", "recover", "ship")) or \
               (prev.kind == "decide" and b.kind == "adapt") or \
               (b.kind == "adapt" and "fail" in prev.text.lower()):
                pivots.append({
                    "iteration": it.iteration,
                    "phase": it.phase,
                    "before": prev.text,
                    "after": b.text,
                    "kind": "fail_to_recover" if prev.kind == "hit_failure" else "decide_to_adapt",
                })
    return pivots


def extract_session(session_dir: Path) -> dict:
    log_dir = session_dir / "logs"
    if not log_dir.exists():
        return {"error": f"no logs/ dir at {session_dir}", "session_dir": str(session_dir)}
    logs = sorted(log_dir.glob("iteration_*.log.err"))
    iterations: list[IterationExtract] = []
    for log in logs:
        m = re.search(r"iteration_(\d+)", log.name)
        if not m:
            continue
        n = int(m.group(1))
        iterations.append(extract_iteration(log, n, session_dir))

    # Multiturn lanes (storyboard, x_engine, linkedin_engine) emit a single
    # `multiturn_session.log.err` instead of per-iteration files. Extract it
    # as a synthetic iteration so the reasoning trail still renders. Phase
    # is reported as "multiturn" since results.jsonl phases don't map onto
    # a single combined log.
    multiturn_log = log_dir / "multiturn_session.log.err"
    if multiturn_log.is_file() and multiturn_log.stat().st_size > 0:
        synthetic_idx = max((it.iteration for it in iterations), default=0) + 1
        mt = extract_iteration(multiturn_log, synthetic_idx, session_dir)
        iterations.append(IterationExtract(
            iteration=mt.iteration,
            phase="multiturn",
            status=mt.status,
            reasoning_beats=mt.reasoning_beats,
            tool_calls=mt.tool_calls,
            tool_count=mt.tool_count,
            token_count=mt.token_count,
        ))

    return {
        "session_dir": str(session_dir),
        "iteration_count": len(iterations),
        "totals": {
            "reasoning_beats": sum(len(it.reasoning_beats) for it in iterations),
            "tool_calls": sum(it.tool_count for it in iterations),
            "tokens": round(sum((it.token_count or 0) for it in iterations), 1),
        },
        "iterations": [
            {
                "iteration": it.iteration,
                "phase": it.phase,
                "status": it.status,
                "reasoning_beats": [asdict(b) for b in it.reasoning_beats],
                "tool_calls": it.tool_calls,
                "tool_count": it.tool_count,
                "token_count": it.token_count,
            }
            for it in iterations
        ],
        "pivots": detect_pivots(iterations),
    }


def main():
    p = argparse.ArgumentParser(description="Extract reasoning beats from session logs")
    p.add_argument("session_dir", type=Path)
    p.add_argument("-o", "--output", type=Path, default=None,
                   help="Write JSON here instead of stdout")
    args = p.parse_args()

    out = extract_session(args.session_dir.resolve())
    js = json.dumps(out, indent=2)
    if args.output:
        args.output.write_text(js)
        print(f"Wrote {args.output} ({len(js)} bytes)", file=sys.stderr)
    else:
        print(js)


if __name__ == "__main__":
    main()
