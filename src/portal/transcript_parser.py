"""Pure JSONL parsers for the transcript drill-down route (Unit 6).

Normalizes Claude Code and Codex session transcripts into a common
``TranscriptEvent`` shape the drill-down template renders against. Kept
side-effect-free so tests can exercise the shape independently of the
FastAPI route.

Both parsers tolerate JSONL parse errors mid-file: parsing returns the
list of events successfully decoded up to (but not including) the broken
line, and ``partial`` is set so the route can render the truncation
footer. A parse-error never raises out of the parser.

Plan: docs/plans/2026-05-18-001-feat-portal-moments-redesign-plan.md
Spec: §"Unit 6: Transcript drill-down route + renderer".
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Normalised event shape — single contract the renderer consumes.
# ---------------------------------------------------------------------------


@dataclass
class TranscriptEvent:
    """One row in the rendered transcript.

    ``role`` collapses CC's ``user``/``assistant`` + Codex's ``user_message``/
    ``agent_message`` into the two-value vocabulary the template uses.

    ``kind`` is the rendered row variant:
      * ``msg``         — plain user/agent text
      * ``reasoning``   — agent reasoning (collapsed by default)
      * ``tool_call``   — agent invoking a tool / function
      * ``tool_result`` — output of a tool/function call
      * ``session_end`` — Codex ``task_complete`` / ``task_aborted``

    Empty/missing fields default to safe sentinels so the Jinja template
    can render any event without conditionals on missing keys.
    """

    event_id: str
    role: str  # "user" | "agent"
    kind: str  # "msg" | "reasoning" | "tool_call" | "tool_result" | "session_end"
    body: str
    ts: str
    tool_name: str | None = None
    args: dict[str, Any] | None = None
    args_summary: str | None = None
    result: str | None = None
    token_counts: dict[str, Any] | None = None


@dataclass
class ParseResult:
    """Wraps the list of events with a ``partial`` flag.

    ``partial=True`` means at least one JSONL line failed to decode and
    we stopped at that line — the route renders a truncation footer.
    """

    events: list[TranscriptEvent] = field(default_factory=list)
    partial: bool = False


# ---------------------------------------------------------------------------
# Claude Code parser.
#
# CC JSONL shape (verified against ~/.claude/projects/<dir>/<sid>.jsonl):
#   {"type": "user" | "assistant" | "attachment" | "queue-operation"
#            | "last-prompt" | ...,
#    "uuid": "<event-uuid>",
#    "timestamp": "...Z",
#    "message": {
#       "role": "user" | "assistant",
#       "content": str | list[ {type:"text"|"thinking"|"tool_use"|"tool_result", ...} ]
#    },
#    "toolUseResult": dict | None
#   }
#
# We surface only the rows a human would want to see:
#   * type=user with message.content as text → role=user, kind=msg
#   * type=assistant with content.type=text  → role=agent, kind=msg
#   * type=assistant with content.type=thinking → role=agent, kind=reasoning
#   * type=assistant with content.type=tool_use → role=agent, kind=tool_call
#   * type=user with content.type=tool_result (or toolUseResult on row) →
#       role=agent, kind=tool_result  (the tool *output*, attributed to agent
#       for renderer symmetry — the row is "what the tool said back")
# ---------------------------------------------------------------------------


_CC_DISPLAY_TYPES: frozenset[str] = frozenset({"user", "assistant"})


def _safe_str(v: Any) -> str:
    """String coercion that never raises and never returns None."""
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    try:
        return str(v)
    except Exception:  # noqa: BLE001
        return ""


def _summarize_args(tool_name: str, args: Any) -> str:
    """One-line ``<tool> · <hint>`` summary for the collapsed row.

    Picks a sensible field per common tool. Falls back to JSON-shortening
    when no preferred field is present. The summary is plain text — Jinja
    autoescape handles HTML safety at render time.
    """
    if not isinstance(args, dict):
        return tool_name
    # Prefer well-known shapes
    for field_name in ("command", "file_path", "path", "pattern", "url", "query"):
        v = args.get(field_name)
        if isinstance(v, str) and v:
            return f"{tool_name} · {v}"
    # Fallback: short JSON blob
    try:
        blob = json.dumps(args, separators=(",", ":"))
    except (TypeError, ValueError):
        blob = repr(args)
    if len(blob) > 80:
        blob = blob[:77] + "..."
    return f"{tool_name} · {blob}"


def _coerce_tool_result_content(content: Any) -> str:
    """Tool-result content can be str or list[ {type:"text", text:...} ]."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(_safe_str(item.get("text")))
                else:
                    # Other content blocks (image refs, etc.) — render a
                    # type tag instead of dumping opaque dict structure.
                    parts.append(f"[{_safe_str(item.get('type', '?'))}]")
            else:
                parts.append(_safe_str(item))
        return "\n".join(parts)
    return _safe_str(content)


def _parse_cc_row(obj: dict[str, Any]) -> list[TranscriptEvent]:
    """Convert one CC JSONL row to zero-or-more TranscriptEvents.

    A single assistant row can contain multiple content blocks (text +
    thinking + tool_use) — each becomes its own renderer row so the
    template can collapse/expand independently.
    """
    row_type = obj.get("type")
    if row_type not in _CC_DISPLAY_TYPES:
        return []  # attachments, queue-operation, last-prompt are not displayed

    base_uuid = _safe_str(obj.get("uuid"))
    ts = _safe_str(obj.get("timestamp"))
    msg = obj.get("message") or {}
    if not isinstance(msg, dict):
        return []

    role_raw = msg.get("role")
    content = msg.get("content")

    # Plain user text — message.content is a string.
    if row_type == "user" and isinstance(content, str):
        text = content
        if not text:
            return []
        return [
            TranscriptEvent(
                event_id=base_uuid,
                role="user",
                kind="msg",
                body=text,
                ts=ts,
            )
        ]

    # Tool result (under user row) — message.content is a list of tool_result.
    if row_type == "user" and isinstance(content, list):
        out: list[TranscriptEvent] = []
        for i, block in enumerate(content):
            if not isinstance(block, dict):
                continue
            btype = block.get("type")
            if btype == "tool_result":
                body = _coerce_tool_result_content(block.get("content"))
                out.append(
                    TranscriptEvent(
                        event_id=f"{base_uuid}-{i}" if base_uuid else f"r{i}",
                        role="agent",
                        kind="tool_result",
                        body=body,
                        ts=ts,
                        result=body,
                    )
                )
            elif btype == "text":
                text = _safe_str(block.get("text"))
                if text:
                    out.append(
                        TranscriptEvent(
                            event_id=f"{base_uuid}-{i}" if base_uuid else f"t{i}",
                            role="user",
                            kind="msg",
                            body=text,
                            ts=ts,
                        )
                    )
        return out

    # Assistant — message.content is a list of (text | thinking | tool_use).
    if row_type == "assistant" and isinstance(content, list):
        out = []
        for i, block in enumerate(content):
            if not isinstance(block, dict):
                continue
            btype = block.get("type")
            ev_id = f"{base_uuid}-{i}" if base_uuid else f"a{i}"
            if btype == "text":
                text = _safe_str(block.get("text"))
                if text:
                    out.append(
                        TranscriptEvent(
                            event_id=ev_id,
                            role="agent",
                            kind="msg",
                            body=text,
                            ts=ts,
                        )
                    )
            elif btype == "thinking":
                body = _safe_str(block.get("thinking"))
                out.append(
                    TranscriptEvent(
                        event_id=ev_id,
                        role="agent",
                        kind="reasoning",
                        body=body,
                        ts=ts,
                    )
                )
            elif btype == "tool_use":
                name = _safe_str(block.get("name")) or "tool"
                args = block.get("input")
                if not isinstance(args, dict):
                    args = None
                out.append(
                    TranscriptEvent(
                        event_id=ev_id,
                        role="agent",
                        kind="tool_call",
                        body="",
                        ts=ts,
                        tool_name=name,
                        args=args,
                        args_summary=_summarize_args(name, args),
                    )
                )
        return out

    # Assistant single-string message (rare; older CC versions).
    if row_type == "assistant" and isinstance(content, str) and content:
        return [
            TranscriptEvent(
                event_id=base_uuid,
                role="agent",
                kind="msg",
                body=content,
                ts=ts,
            )
        ]

    return []


def parse_cc_jsonl(path: Path) -> ParseResult:
    """Parse a Claude Code session JSONL into a list of TranscriptEvents.

    Reads up to a permissive line cap (no per-line size limit — CC rows
    can legitimately carry multi-KB prompts). Stops on the first JSON
    decode error and sets ``partial=True``.
    """
    result = ParseResult()
    try:
        with path.open("r", encoding="utf-8") as handle:
            for raw in handle:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError:
                    result.partial = True
                    return result
                if not isinstance(obj, dict):
                    continue
                result.events.extend(_parse_cc_row(obj))
    except (OSError, UnicodeDecodeError):
        # File deleted/unreadable mid-parse — return what we have plus
        # the partial flag so the caller can render the truncation footer.
        result.partial = True
    return result


# ---------------------------------------------------------------------------
# Codex parser.
#
# Codex JSONL shape (verified against ~/.codex/sessions/.../rollout-*.jsonl):
#   {"type": "session_meta" | "event_msg" | "response_item" | "turn_context",
#    "timestamp": "...Z",
#    "payload": { "type": "<inner-type>", ... }
#   }
#
# Inner-type renderer mapping:
#   event_msg / user_message   → role=user, kind=msg, body=payload.message
#   event_msg / agent_message  → role=agent, kind=msg, body=payload.message
#   event_msg / task_complete  → kind=session_end, body="task_complete"
#   event_msg / task_aborted   → kind=session_end, body="task_aborted: <reason>"
#   event_msg / token_count    → carried on the next msg as token_counts
#   response_item / reasoning  → role=agent, kind=reasoning,
#                                body = summary[0].text or "(reasoning unavailable)"
#   response_item / function_call → role=agent, kind=tool_call,
#                                args parsed from JSON-encoded "arguments"
#   response_item / function_call_output → kind=tool_result, body=output
#   response_item / message    → skipped if role=developer (system bootstrap);
#                                emitted otherwise as role=agent, kind=msg
# ---------------------------------------------------------------------------


def _maybe_load_json_args(raw: str) -> dict[str, Any] | None:
    """Codex stores tool args as a JSON-encoded string under ``arguments``."""
    if not isinstance(raw, str) or not raw:
        return None
    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if isinstance(decoded, dict):
        return decoded
    return None


def _codex_message_text(content: Any) -> str:
    """A Codex response_item/message payload has content=list[{type,text}]."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if not isinstance(item, dict):
                continue
            itype = item.get("type")
            if itype in ("input_text", "output_text", "text"):
                parts.append(_safe_str(item.get("text")))
        return "\n".join(p for p in parts if p)
    return _safe_str(content)


def _parse_codex_row(obj: dict[str, Any], index: int) -> list[TranscriptEvent]:
    """Convert one Codex JSONL row to TranscriptEvents.

    ``index`` is the line index, used to seed event_ids when the payload
    doesn't carry a stable id of its own.
    """
    outer_type = obj.get("type")
    ts = _safe_str(obj.get("timestamp"))
    payload = obj.get("payload")
    if not isinstance(payload, dict):
        return []
    inner_type = payload.get("type")

    # ---- event_msg variants ----
    if outer_type == "event_msg":
        if inner_type == "user_message":
            text = _safe_str(payload.get("message"))
            if not text:
                return []
            return [
                TranscriptEvent(
                    event_id=f"cdx-{index}",
                    role="user",
                    kind="msg",
                    body=text,
                    ts=ts,
                )
            ]
        if inner_type == "agent_message":
            text = _safe_str(payload.get("message"))
            if not text:
                return []
            return [
                TranscriptEvent(
                    event_id=f"cdx-{index}",
                    role="agent",
                    kind="msg",
                    body=text,
                    ts=ts,
                )
            ]
        if inner_type in ("task_complete", "task_completed", "task_aborted"):
            reason = _safe_str(payload.get("reason") or payload.get("message") or "")
            body = inner_type if not reason else f"{inner_type}: {reason}"
            return [
                TranscriptEvent(
                    event_id=f"cdx-{index}",
                    role="agent",
                    kind="session_end",
                    body=body,
                    ts=ts,
                )
            ]
        # token_count etc. are not displayed in v1 — could be threaded onto
        # the preceding turn in a future iteration.
        return []

    # ---- response_item variants ----
    if outer_type == "response_item":
        if inner_type == "reasoning":
            # Codex encrypts reasoning content by default; surface the
            # human-readable summary if present, else a placeholder.
            summary = payload.get("summary")
            body = ""
            if isinstance(summary, list) and summary:
                first = summary[0]
                if isinstance(first, dict):
                    body = _safe_str(first.get("text"))
            if not body:
                body = "(reasoning unavailable — encrypted by Codex)"
            return [
                TranscriptEvent(
                    event_id=f"cdx-{index}",
                    role="agent",
                    kind="reasoning",
                    body=body,
                    ts=ts,
                )
            ]
        if inner_type == "function_call":
            name = _safe_str(payload.get("name")) or "function"
            args = _maybe_load_json_args(_safe_str(payload.get("arguments")))
            call_id = _safe_str(payload.get("call_id"))
            ev_id = call_id or f"cdx-{index}"
            return [
                TranscriptEvent(
                    event_id=ev_id,
                    role="agent",
                    kind="tool_call",
                    body="",
                    ts=ts,
                    tool_name=name,
                    args=args,
                    args_summary=_summarize_args(name, args),
                )
            ]
        if inner_type == "function_call_output":
            call_id = _safe_str(payload.get("call_id"))
            output = _safe_str(payload.get("output"))
            return [
                TranscriptEvent(
                    event_id=f"{call_id}-out" if call_id else f"cdx-{index}-out",
                    role="agent",
                    kind="tool_result",
                    body=output,
                    ts=ts,
                    result=output,
                )
            ]
        if inner_type == "message":
            role = _safe_str(payload.get("role"))
            if role == "developer":
                # Skip the system/developer bootstrap payload — it's not
                # user-facing content (it's the agent's own system prompt).
                return []
            text = _codex_message_text(payload.get("content"))
            if not text:
                return []
            mapped_role = "user" if role == "user" else "agent"
            return [
                TranscriptEvent(
                    event_id=f"cdx-{index}",
                    role=mapped_role,
                    kind="msg",
                    body=text,
                    ts=ts,
                )
            ]
        return []

    return []


def parse_codex_jsonl(path: Path) -> ParseResult:
    """Parse a Codex rollout JSONL into a list of TranscriptEvents.

    Mirrors ``parse_cc_jsonl`` semantics: stops on the first JSON decode
    error and sets ``partial=True``.
    """
    result = ParseResult()
    try:
        with path.open("r", encoding="utf-8") as handle:
            for idx, raw in enumerate(handle):
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError:
                    result.partial = True
                    return result
                if not isinstance(obj, dict):
                    continue
                result.events.extend(_parse_codex_row(obj, idx))
    except (OSError, UnicodeDecodeError):
        result.partial = True
    return result


# ---------------------------------------------------------------------------
# Registry lookup — used by the drill-down route's IDOR guard.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RegistryLookup:
    """Resolved (source, file_path) for a session_id within a client's registry.

    Mirrors the start-row shape persisted by ``SessionRegistry``. ``ended_at``
    is included so the renderer can optionally show a "session ended" tag,
    but is not load-bearing for the IDOR guard.
    """

    session_id: str
    source: str  # "cc" | "codex"
    file_path: str
    started_at: str
    ended_at: str | None = None


def lookup_session_in_registry(
    registry_path: Path, session_id: str
) -> RegistryLookup | None:
    """Scan ``clients/<slug>/audit/sessions.jsonl`` for a row matching session_id.

    Latest-row-per-session-id wins — same rule SessionRegistry's
    rebuild_registry_from_disk applies. A trailing start row replaces an
    earlier start; an end row overlays ended_at on the existing start.

    Returns ``None`` if the registry file is missing OR no row matches.
    The caller treats both as 404 ``transcript_unavailable`` (R9.1 IDOR).

    Reads the whole file linearly — registries are append-only and small
    (one row per session, ~150 bytes each). At 10k sessions that's still
    <2MB, well inside one-tick I/O budget.
    """
    if not registry_path.is_file():
        return None

    start_row: dict[str, Any] | None = None
    end_row: dict[str, Any] | None = None
    try:
        with registry_path.open("r", encoding="utf-8") as handle:
            for raw in handle:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError:
                    # Skip the corrupt line — same posture as the moments
                    # endpoint takes for the wide log.
                    continue
                if not isinstance(obj, dict):
                    continue
                if obj.get("session_id") != session_id:
                    continue
                if "started_at" in obj:
                    start_row = obj
                    # Latest-row-wins: a subsequent start replaces.
                elif "ended_at" in obj:
                    end_row = obj
    except OSError:
        return None

    if start_row is None:
        return None

    return RegistryLookup(
        session_id=session_id,
        source=_safe_str(start_row.get("source")) or "cc",
        file_path=_safe_str(start_row.get("file_path")),
        started_at=_safe_str(start_row.get("started_at")),
        ended_at=_safe_str(end_row.get("ended_at")) if end_row else None,
    )
