"""Server-side redaction layer for portal-visible content (Unit 5 of the
portal-moments redesign).

Layered defense against agent-produced secrets leaking into the browser:

1. ``redact_transcript_event`` first runs a **file-pattern denylist** on
   Bash/Read/Write/Edit/MultiEdit/NotebookEdit/Grep tool args. If any arg
   names a secret-file shape (``.env``, ``id_rsa``, ``*.pem``, etc.) the
   tool's ``result`` is replaced with a one-line summary — args remain
   visible (the path is not the secret, the contents are).
2. Then ``scrub_with_records`` (``src/shared/reporting/scrub.py``) runs over
   every remaining string in the event, catching any inline secrets that
   slipped past layer 1 via the 17+ regex patterns there.

``redact_text`` / ``redact_metadata`` are the entry points for non-event
content (moment titles, bodies, metadata). All three return
``(redacted, list[RedactionRecord])`` so callers can log what was caught
via the operator-internal ``moment_kind="redaction_applied"`` audit trail.

``REDACTOR_VERSION = "v1"`` is stamped on output by callers (Units 3/6/7)
so a future v2 can re-scan already-served content.

Plan: docs/plans/2026-05-18-001-feat-portal-moments-redesign-plan.md
Spec: §"Unit 5: Server-side redaction pass".
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from autoresearch.events import log_event
from src.shared.reporting.scrub import ScrubRecord, scrub_with_records

REDACTOR_VERSION = "v1"

# Tools whose args we inspect for secret-file paths. Broader than
# Bash/Read-only per Unit 5 spec — Write/Edit/MultiEdit/NotebookEdit/Grep
# can equally leak `.env` contents into the transcript.
_FILE_TOOLS: frozenset[str] = frozenset({
    "Bash", "Read", "Write", "Edit", "MultiEdit", "NotebookEdit", "Grep",
})

# Arg fields per tool that may carry file paths or commands. We don't
# enumerate per-tool because the field names overlap and the cost of
# scanning a non-existent field is zero.
_PATH_ARG_FIELDS: tuple[str, ...] = (
    "command",     # Bash
    "file_path",   # Read, Write, Edit, MultiEdit, NotebookEdit
    "path",        # alt
    "pattern",     # Grep search pattern (e.g. "API_KEY")
    "glob",        # Grep file glob
    "notebook_path",  # NotebookEdit
)

# Secret-file shapes. Match as a substring of the arg value — Bash commands
# embed paths inline (e.g. ``cat .env``), so we look for the bare token
# anywhere in the string. Word-boundary at the START prevents partial
# matches inside longer filenames (e.g. ``my.envoy.conf`` doesn't match
# ``.env``); the END is open because ``.env.local`` / ``id_rsa.pub`` /
# ``server.pem.bak`` all warrant redaction.
_SECRET_FILE_PATTERN: re.Pattern[str] = re.compile(
    r"(?<![A-Za-z0-9])"
    r"("
    r"\.env(?:\.[A-Za-z0-9_]+)?"     # .env, .env.local, .env.production
    r"|\.envrc"                       # direnv
    r"|id_rsa(?:[._][A-Za-z0-9_]*)?"  # id_rsa, id_rsa.pub, id_rsa_backup
    r"|id_ed25519(?:[._][A-Za-z0-9_]*)?"
    r"|id_ecdsa(?:[._][A-Za-z0-9_]*)?"
    r"|id_dsa(?:[._][A-Za-z0-9_]*)?"
    r"|\.git/credentials"
    r"|[A-Za-z0-9_\-/.]*\.pem\b"
    r"|[A-Za-z0-9_\-/.]*\.key\b"
    r"|[A-Za-z0-9_\-/.]*\.crt\b"
    r"|[A-Za-z0-9_\-/.]*\.p12\b"
    r"|[A-Za-z0-9_\-/.]*\.pfx\b"
    r")"
)


@dataclass(frozen=True)
class RedactionRecord:
    """One redaction event for audit logging.

    Carries the kind of redaction, the source surface (transcript /
    moment_title / moment_body / moment_meta), and the length of the
    original matched value. **Original value is NEVER stored** — only
    kind + length for cardinality, per R-Sec-3.
    """

    redaction_kind: str
    source: str
    original_length: int


def _emit_audit(records: list[RedactionRecord]) -> None:
    """Emit one operator-internal moment per redaction record (R-Sec-3).

    No ``client_id``, no ``path`` override — defaults to the operator-internal
    ``~/.local/share/gofreddy/events.jsonl``. Title omitted: we don't want
    redacted-content evidence in the operator log either. Per TD-56 there
    is no ``emit_moment`` wrapper — we call ``log_event`` directly.
    """
    for rec in records:
        log_event(
            "moment",
            metadata={
                "moment_kind": "redaction_applied",
                "redaction_kind": rec.redaction_kind,
                "source": rec.source,
                "original_length": rec.original_length,
                "redactor_version": REDACTOR_VERSION,
            },
        )


def redact_text(
    s: str,
    *,
    source: str = "transcript",
    emit_audit: bool = True,
) -> tuple[str, list[RedactionRecord]]:
    """Run the regex scrub layer over ``s`` and return (redacted, records).

    ``source`` is stamped on every emitted ``RedactionRecord`` and the
    operator-internal audit event. Caller passes the surface name
    (``transcript`` / ``moment_title`` / ``moment_body`` / ``moment_meta``)
    so operators can cluster redactions by where they're showing up.

    HTML-escape is NOT performed here — that's render-time concern of
    Units 6/7. The redacted text uses ``<redacted:KIND>`` markers which
    are returned verbatim and escaped downstream alongside the rest of
    the body.

    ``emit_audit`` defaults True. Callers chaining multiple redact_text
    calls into one logical redaction event (e.g. ``redact_metadata`` walking
    a dict) may pass ``False`` and emit once at the outer boundary.
    """
    if not isinstance(s, str) or not s:
        return s, []
    redacted, scrub_records = scrub_with_records(s)
    records = [
        RedactionRecord(
            redaction_kind=sr.kind,
            source=source,
            original_length=sr.original_length,
        )
        for sr in scrub_records
    ]
    if emit_audit and records:
        _emit_audit(records)
    return redacted, records


def redact_metadata(
    d: dict[str, Any],
    *,
    source: str = "moment_meta",
    emit_audit: bool = True,
) -> tuple[dict[str, Any], list[RedactionRecord]]:
    """Walk ``d`` and apply ``redact_text`` to every string leaf.

    Returns a new dict (does not mutate the input) plus the aggregated
    record list. Recurses into nested dicts and lists; non-string leaves
    pass through unchanged.

    Used for moment metadata (title, body, action, args_summary,
    reviewer_note, reason_text, etc.). Audit emission is batched at the
    outer call — internal ``redact_text`` calls pass ``emit_audit=False``.
    """
    all_records: list[RedactionRecord] = []

    def _walk(value: Any) -> Any:
        if isinstance(value, str):
            redacted, records = redact_text(value, source=source, emit_audit=False)
            all_records.extend(records)
            return redacted
        if isinstance(value, dict):
            return {k: _walk(v) for k, v in value.items()}
        if isinstance(value, list):
            return [_walk(v) for v in value]
        if isinstance(value, tuple):
            return tuple(_walk(v) for v in value)
        return value

    new_d = _walk(d)
    if emit_audit and all_records:
        _emit_audit(all_records)
    return new_d, all_records


def _expand_path(s: str) -> str:
    """Expand ``$HOME`` and ``~`` server-side for denylist evasion checks.

    Operator-side expansion of agent-provided strings — we do NOT want the
    agent's ``$HOME`` value, we want ours (the server's). ``os.path.expanduser``
    + ``os.path.expandvars`` both honour server-side env.
    """
    return os.path.expandvars(os.path.expanduser(s))


def _scan_for_secret_file(value: str) -> str | None:
    """Return the matched token if ``value`` (or its expanded form) names a
    secret-file shape, else None.

    Checks the raw value AND the ``$HOME``/``~``-expanded form to catch
    evasions like ``cat $HOME/.env``.
    """
    if not isinstance(value, str) or not value:
        return None
    candidates = [value]
    expanded = _expand_path(value)
    if expanded != value:
        candidates.append(expanded)
    for candidate in candidates:
        match = _SECRET_FILE_PATTERN.search(candidate)
        if match:
            return match.group(1)
    return None


def _summarize_redacted_result(file_path: str | None, original_result: Any) -> str:
    """One-line summary that replaces a denylisted tool result.

    Mentions the path (path is not the secret, contents are) and an
    approximate size measure if the original result was a string with
    newlines. Avoids leaking any actual content.
    """
    if isinstance(original_result, str):
        line_count = original_result.count("\n") + (1 if original_result else 0)
        suffix = f"{line_count} lines"
    else:
        suffix = "contents withheld"
    label = file_path or "secret-file"
    return f"{label} ({suffix} — contents redacted)"


def redact_transcript_event(
    ev: dict[str, Any],
    *,
    allow_secret_file: bool = False,
    emit_audit: bool = True,
) -> tuple[dict[str, Any], list[RedactionRecord]]:
    """Layered redaction for one transcript event.

    Layer 1: file-pattern denylist on tool args. If any arg names a secret
    file (``.env``, ``id_rsa``, ``*.pem``, etc.) the tool's ``result`` is
    replaced with a one-line summary and a ``RedactionRecord`` of kind
    ``file_denylist`` is recorded. Args remain visible.

    Layer 2: ``redact_text`` over every remaining string leaf (always runs).

    ``allow_secret_file=True`` skips layer 1 — reserved for operator UI
    in a future plan, never True in v1 callers (kept in the signature so
    the boolean exists from day one).

    Returns ``(new_event, records)``. Input is not mutated.
    """
    all_records: list[RedactionRecord] = []
    new_ev: dict[str, Any] = dict(ev)

    # --- Layer 1: file-pattern denylist on tool args ---
    if not allow_secret_file:
        tool_name = new_ev.get("tool_name") or new_ev.get("tool") or ""
        args = new_ev.get("args")
        if tool_name in _FILE_TOOLS and isinstance(args, dict):
            matched_token: str | None = None
            for field in _PATH_ARG_FIELDS:
                value = args.get(field)
                if not isinstance(value, str):
                    continue
                token = _scan_for_secret_file(value)
                if token:
                    matched_token = token
                    break
            if matched_token is not None:
                # Replace the result with a summary; preserve args.
                original_result = new_ev.get("result")
                # Choose a path field for the summary message (prefer
                # file_path / path / notebook_path; fall back to the
                # matched token).
                summary_path = None
                for field in ("file_path", "path", "notebook_path"):
                    val = args.get(field)
                    if isinstance(val, str) and val:
                        summary_path = val
                        break
                if summary_path is None:
                    summary_path = matched_token
                summary = _summarize_redacted_result(summary_path, original_result)
                new_ev["result"] = summary
                original_length = (
                    len(original_result) if isinstance(original_result, str) else 0
                )
                all_records.append(
                    RedactionRecord(
                        redaction_kind="file_denylist",
                        source="transcript",
                        original_length=original_length,
                    )
                )

    # --- Layer 2: regex scrub over remaining strings (always runs) ---
    def _walk(value: Any) -> Any:
        if isinstance(value, str):
            redacted, records = redact_text(
                value, source="transcript", emit_audit=False
            )
            all_records.extend(records)
            return redacted
        if isinstance(value, dict):
            return {k: _walk(v) for k, v in value.items()}
        if isinstance(value, list):
            return [_walk(v) for v in value]
        if isinstance(value, tuple):
            return tuple(_walk(v) for v in value)
        return value

    new_ev = _walk(new_ev)

    if emit_audit and all_records:
        _emit_audit(all_records)

    return new_ev, all_records
