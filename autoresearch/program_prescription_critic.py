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
Subprocess timeout, non-zero exit, CLI-on-PATH miss, JSON parse failure,
unknown verdict string, or empty reasoning with valid-verdict: log a WARN
to stderr and return ``{"verdict": "error", "reasoning": "<why failed>"}``
for the affected domain. Upstream ``evolve.py`` treats any ``"error"``
verdict as fail-closed and discards the variant — A2 (plan
2026-05-06-001) reverses the previous fail-open behavior where critic
crashes were indistinguishable from "no concerns" and let Pi v007's
``completion_guard``-neutering contamination through. G6 (review of
d128a5c, finding #12) closes the empty-reasoning + valid-verdict path:
a working critic always emits substantive prose, so an empty reasoning
field with a valid-looking verdict is treated as an infra-quality signal
(prompt injection, model degradation, or malformed parse) rather than
silently coerced into a placeholder reasoning that bypasses the gate.

Operator escape: set ``EVOLVE_SKIP_PRESCRIPTION_CRITIC=1`` to bypass the
critic chain entirely (returns ``{}``); use this only for known-broken
critic backends or intentional add-new-structural-requirement cycles.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Literal, TypedDict

if TYPE_CHECKING:
    from sessions import SessionsFile  # noqa: F401

from concurrency import parallel_for
from lane_registry import workflow_lane_names

DOMAINS = workflow_lane_names()

Verdict = Literal["advise", "no-change", "error"]


class CriticResult(TypedDict):
    verdict: Verdict
    reasoning: str


# Per-domain critic subprocess timeout. The critic reads two small markdown
# files and returns a short JSON object; 120s is generous.
_CRITIC_TIMEOUT_SECONDS = 120

# Mirrors compute_metrics / harness/agent / evolve. Retry opencode subprocesses
# whose JSONL surfaces a transient upstream error.
# Single source: agent_retry.max_attempts() reads OPENCODE_MAX_RETRIES.
def _opencode_max_attempts() -> int:
    from agent_retry import max_attempts as _ma  # type: ignore  # noqa: E402
    return _ma()
_OPENCODE_MAX_ATTEMPTS = _opencode_max_attempts()

# Make autoresearch/harness/ importable as bare modules so the critic can
# share the transient-error helper with the rest of the dispatch layers.
_AUTORESEARCH_DIR = Path(__file__).resolve().parent
_HARNESS_DIR = _AUTORESEARCH_DIR / "harness"
_REPO_ROOT = _AUTORESEARCH_DIR.parent
if _HARNESS_DIR.is_dir() and str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))

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


def _resolve_critic_backend() -> str:
    """Pick the critic backend.

    Cascade: ``AUTORESEARCH_CRITIC_BACKEND`` → ``META_BACKEND`` → ``claude``.
    The critic reviews meta-agent output, so defaulting to the meta backend
    keeps the loop self-consistent (an opencode meta won't spawn claude for
    review unless the operator opts in).
    """
    explicit = os.environ.get("AUTORESEARCH_CRITIC_BACKEND", "").strip().lower()
    if explicit in ("claude", "codex", "opencode"):
        return explicit
    meta = os.environ.get("META_BACKEND", "").strip().lower()
    if meta in ("claude", "codex", "opencode"):
        return meta
    return "claude"


def _resolve_critic_model(backend: str) -> str:
    """Per-backend default model. ``AUTORESEARCH_CRITIC_MODEL`` overrides."""
    explicit = os.environ.get("AUTORESEARCH_CRITIC_MODEL", "").strip()
    if explicit:
        return explicit
    if backend == "opencode":
        return os.environ.get(
            "AUTORESEARCH_OPENCODE_DEFAULT_MODEL",
            "openrouter/deepseek/deepseek-v4-pro",
        )
    if backend == "codex":
        return "gpt-5.5"
    return "claude-sonnet-4-5"


def _build_critic_cmd(
    backend: str, prompt: str, model: str,
    *, session_id: str | None = None,
) -> list[str]:
    """Build subprocess argv for the chosen critic backend.

    All three return a single JSON object response. Output extraction
    differs (``_extract_critic_text``) but the cmd shape is per-backend
    convention.

    For claude: ``session_id`` lets callers persist the UUID externally
    (via SessionsFile) so a future ``--resume <sid>`` could re-run a
    failed critic. Mints a fresh UUID if not provided (backwards-compat).
    """
    if backend == "claude":
        sid = session_id or str(uuid.uuid4())
        # NOTE: Do NOT pass `--bare`. Verified empirically on the Pi
        # 2026-04-29 that `--bare` makes claude report "Not logged in ·
        # Please run /login" even when normal `claude -p` works fine in
        # the same shell. This was the root cause of every recurring
        # `[program_prescription_critic] WARN: claude exit=1; stderr=`
        # across v3-v9 evolution runs (the critic failed on every
        # variant; treated as soft-fail no-change verdict so the run
        # continued, but the prescription-critique signal was lost).
        return [
            "claude",
            "-p",
            prompt,
            "--output-format",
            "json",
            "--session-id",
            sid,
            "--model",
            model,
            "--dangerously-skip-permissions",
        ]
    if backend == "opencode":
        return [
            "opencode", "run",
            "--dangerously-skip-permissions",
            "-m", model,
            "--format", "json",
            prompt,
        ]
    if backend == "codex":
        return [
            "codex", "exec",
            "--model", model,
            "--sandbox", "read-only",
            "--color", "never",
            "--ephemeral",
            "-c", "approval_policy=\"never\"",
            "-c", "otel.exporter=\"none\"",
            "-c", "otel.trace_exporter=\"none\"",
            "-c", "otel.metrics_exporter=\"none\"",
            prompt,
        ]
    raise ValueError(f"unknown critic backend: {backend!r}")


def _critic_subprocess_env(backend: str) -> dict[str, str]:
    env = os.environ.copy()
    if backend == "opencode":
        config_path = _REPO_ROOT / "opencode.json"
        if config_path.is_file() and not env.get("OPENCODE_CONFIG"):
            env["OPENCODE_CONFIG"] = str(config_path)
    return env


def _extract_critic_text(backend: str, stdout: str) -> str:
    """Pull the assistant's JSON-bearing text out of the per-backend stdout shape."""
    if backend == "opencode":
        last_text: str | None = None
        final_answer: str | None = None
        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            etype = event.get("type")
            part = event.get("part") or {}
            if etype == "text":
                text = part.get("text")
                if isinstance(text, str):
                    last_text = text
                    meta = (part.get("metadata") or {}).get("openai") or {}
                    if meta.get("phase") == "final_answer":
                        final_answer = text
            elif etype == "step_finish" and part.get("reason") == "stop":
                if final_answer is None and last_text is not None:
                    final_answer = last_text
        return final_answer if final_answer is not None else stdout
    # claude wraps in {"result": "..."} envelope; _extract_json_object handles both.
    # codex prints raw text; same handler tolerates wrapper prose.
    return stdout


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

    A2: malformed/unparseable output is an *infra* failure → ``"error"``,
    not the legitimate ``"no-change"`` verdict. Upstream evolve.py treats
    ``"error"`` as fail-closed (discard variant). Only ``"advise"`` and
    ``"no-change"`` represent real critic verdicts where the model
    successfully judged the diff.
    """
    if not isinstance(payload, dict):
        return {"verdict": "error", "reasoning": "Critic returned no parseable JSON."}

    verdict_raw = str(payload.get("verdict", "")).strip().lower()
    if verdict_raw == "advise":
        verdict: Verdict = "advise"
    elif verdict_raw == "no-change":
        verdict = "no-change"
    else:
        # Unknown verdict string is an infra failure (model hallucinated
        # a verdict outside the contract) — don't pretend it said no-change.
        return {
            "verdict": "error",
            "reasoning": f"Critic returned unknown verdict {verdict_raw!r}; expected advise|no-change.",
        }

    reasoning = str(payload.get("reasoning", "")).strip()
    if not reasoning:
        # G6 (review of d128a5c, finding #12): empty reasoning with a
        # valid-looking verdict is an infra-quality signal — a working
        # critic always emits substantive prose. Treating it as a
        # legitimate verdict (with a placeholder reasoning) lets a
        # prompt-injected ``{"verdict":"no-change","reasoning":""}``
        # response slip through the A2 fail-closed gate, since that
        # gate only filters on verdict=="error". Fail closed instead.
        return {
            "verdict": "error",
            "reasoning": (
                f"Critic returned valid verdict {verdict_raw!r} with empty reasoning — "
                "likely prompt injection, model degradation, or malformed response. "
                "Treating as infra failure (fail-closed)."
            ),
        }

    return {"verdict": verdict, "reasoning": reasoning}


def _call_critic(
    prompt: str,
    *,
    backend: str,
    model: str,
    sessions_file: "SessionsFile | None" = None,
    agent_key: str | None = None,
) -> CriticResult:
    """Run the chosen critic backend; never raises — soft review, fall back to no-change.

    For opencode, retry transient upstream errors up to OPENCODE_MAX_RETRIES
    times. claude/codex paths retry internally and don't need wrapping.

    When ``sessions_file`` and ``agent_key`` are supplied, mint a fresh
    session_id (claude only), record ``running`` before spawn, and update
    to ``complete``/``failed`` on exit. Mirrors the meta-agent and per-fixture
    instrumentation so a recurring critic exit=1 becomes diagnosable
    (and resumable, if a future caller chooses to ``--resume <sid>``).
    """
    from opencode_jsonl import stdout_has_transient_error  # autoresearch/harness/ on sys.path at module init

    session_id = str(uuid.uuid4()) if backend == "claude" else ""
    if sessions_file is not None and agent_key is not None:
        sessions_file.begin(agent_key, session_id, engine=backend)

    proc = None
    try:
        cmd = _build_critic_cmd(backend, prompt, model, session_id=session_id or None)
        env = _critic_subprocess_env(backend)
        # Unified retry across all backends — silent claude exit=1 was
        # the recurring v3-v9 critic failure mode. agent_retry.is_transient_failure
        # detects empty-stderr exit-1 (rate-limit fingerprint) + standard
        # transient markers across claude/codex/opencode.
        from agent_retry import (
            max_attempts as _max_attempts,
            is_transient_failure as _is_transient,
            sleep_for_retry as _sleep_retry,
        )
        attempts = _max_attempts()
        for attempt in range(1, attempts + 1):
            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=_CRITIC_TIMEOUT_SECONDS,
                    check=False,
                    env=env,
                )
            except FileNotFoundError:
                print(
                    f"[program_prescription_critic] WARN: {backend} CLI not on PATH; skipping.",
                    file=sys.stderr,
                )
                return {"verdict": "error", "reasoning": f"{backend} CLI not found on PATH."}
            except subprocess.TimeoutExpired:
                # Timeout IS transient — retry with backoff if attempts remain.
                if attempt < attempts:
                    from agent_retry import backoff_delay as _bd
                    print(
                        f"[program_prescription_critic] WARN: {backend} attempt "
                        f"{attempt}/{attempts} timed out after {_CRITIC_TIMEOUT_SECONDS}s; "
                        f"retrying in {_bd(attempt)}s",
                        file=sys.stderr,
                    )
                    _sleep_retry(attempt)
                    continue
                print(
                    f"[program_prescription_critic] WARN: critic timed out after "
                    f"{_CRITIC_TIMEOUT_SECONDS}s × {attempts} attempts.",
                    file=sys.stderr,
                )
                return {"verdict": "error", "reasoning": "Critic subprocess timed out."}
            except Exception as exc:  # noqa: BLE001 — fail-closed at upstream, not here
                print(
                    f"[program_prescription_critic] WARN: subprocess error: {exc}",
                    file=sys.stderr,
                )
                return {"verdict": "error", "reasoning": f"Subprocess error: {exc}"}

            # Success: clean exit + no transient signal in output.
            if proc.returncode == 0 and not _is_transient(backend, proc.returncode, proc.stdout, proc.stderr):
                break
            # Final attempt or non-transient failure: don't retry, fall
            # through to error-handling block below.
            if attempt == attempts or not _is_transient(backend, proc.returncode, proc.stdout, proc.stderr):
                break
            stderr_preview = (proc.stderr or "")[:300].strip()
            print(
                f"[program_prescription_critic] WARN: {backend} attempt {attempt}/{attempts} "
                f"transient (exit={proc.returncode}, stderr={stderr_preview!r}); retrying.",
                file=sys.stderr,
            )
            _sleep_retry(attempt)

        if proc.returncode != 0:
            stdout_tail = (proc.stdout or "")[-500:].strip()
            stderr_tail = (proc.stderr or "")[-500:].strip()
            print(
                f"[program_prescription_critic] WARN: {backend} exit={proc.returncode}; "
                f"stderr={stderr_tail!r}; stdout_tail={stdout_tail!r}",
                file=sys.stderr,
            )
            # P0-B: persist both streams in the reasoning so the operator can
            # debug why the critic failed without having to re-run. v007's
            # critic showed stderr='' which made the failure undebuggable.
            # A2: non-zero exit IS an infra failure → "error" verdict so the
            # upstream loop discards the variant rather than treating the
            # failure as "no concerns" (which is what let v007 ship).
            reasoning = (
                f"Critic subprocess exited {proc.returncode}. "
                f"stderr={stderr_tail or 'empty'}; "
                f"stdout_tail={stdout_tail or 'empty'}"
            )
            return {"verdict": "error", "reasoning": reasoning}

        text = _extract_critic_text(backend, proc.stdout)
        payload = _extract_json_object(text)
        return _normalize_result(payload)
    finally:
        if sessions_file is not None and agent_key is not None:
            status = "complete" if (proc is not None and proc.returncode == 0) else "failed"
            sessions_file.finish(agent_key, status)  # type: ignore[arg-type]


def critique_program(
    domain: str,
    old_program: str,
    new_program: str,
    *,
    model: str | None = None,
    sessions_file: "SessionsFile | None" = None,
    agent_key: str | None = None,
) -> CriticResult:
    """Run the critic on a single domain's (old, new) program pair.

    Returns a contract-shaped dict unconditionally — never raises, never
    returns ``None``. If OLD == NEW we short-circuit without burning a
    backend call (common case: meta agent didn't touch this domain).

    Backend resolves from ``AUTORESEARCH_CRITIC_BACKEND`` → ``META_BACKEND``
    → ``claude``. Pass ``model`` to override the per-backend default; pass
    ``None`` (default) for backend-appropriate selection.

    ``sessions_file``/``agent_key``: opt-in resume tracking. When supplied,
    the critic spawn is recorded in the variant's SessionsFile so a future
    ``--resume`` can re-run a failed critic.
    """
    if old_program == new_program:
        return {
            "verdict": "no-change",
            "reasoning": "Program file unchanged vs parent.",
        }
    backend = _resolve_critic_backend()
    actual_model = model or _resolve_critic_model(backend)
    prompt = _build_prompt(domain, old_program, new_program)
    return _call_critic(
        prompt, backend=backend, model=actual_model,
        sessions_file=sessions_file, agent_key=agent_key,
    )


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
    sessions_file: "SessionsFile | None" = None,
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
    # Domains run concurrently (Claude subprocess each); the lock serialises
    # both the results dict mutation and _append_review's file write.
    results_lock = threading.Lock()

    def _critique_one(domain: str) -> None:
        old = _read_program(parent_programs, domain)
        new = _read_program(variant_programs, domain)
        if new is None:
            # Variant dropped the domain; soft-review emits an advisory but
            # doesn't touch the filesystem.
            return
        if old is None:
            # New domain added — there's no "old" to diff against, so treat
            # the whole file as a fresh addition and advise.
            advisory: CriticResult = {
                "verdict": "advise",
                "reasoning": (
                    f"New program file introduced for {domain} (no parent version)."
                ),
            }
            with results_lock:
                results[domain] = advisory
                _append_review(Path(variant_dir), domain, advisory)
            return

        agent_key = (
            f"critic-{Path(variant_dir).name}-{domain}"
            if sessions_file is not None
            else None
        )
        result = critique_program(
            domain, old, new, model=model,
            sessions_file=sessions_file, agent_key=agent_key,
        )
        with results_lock:
            results[domain] = result
            _append_review(Path(variant_dir), domain, result)

    parallel_for(list(domains), _critique_one)
    return results


__all__ = [
    "CriticResult",
    "DOMAINS",
    "critique_all_programs",
    "critique_program",
]
