"""Pure-function tests for src.portal.transcript_parser (Unit 6).

Synthetic CC + Codex JSONL fixtures. Real CC/Codex shapes are documented
verbatim in module docstrings of transcript_parser.py — the minimal samples
here just exercise the renderer-visible fields (role, kind, body, tool_name,
args/result, partial flag).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.portal.transcript_parser import (
    RegistryLookup,
    TranscriptEvent,
    lookup_session_in_registry,
    parse_cc_jsonl,
    parse_codex_jsonl,
)


# ---------------------------------------------------------------------------
# CC JSONL fixtures
# ---------------------------------------------------------------------------


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def test_parse_cc_jsonl_user_message_string_content(tmp_path: Path) -> None:
    """Plain string user prompt → one TranscriptEvent(role=user, kind=msg)."""
    fp = tmp_path / "sid1.jsonl"
    _write_jsonl(fp, [
        {
            "type": "user",
            "uuid": "u1",
            "timestamp": "2026-05-18T10:00:00.000Z",
            "message": {"role": "user", "content": "hello world"},
        }
    ])
    result = parse_cc_jsonl(fp)
    assert result.partial is False
    assert len(result.events) == 1
    ev = result.events[0]
    assert ev.role == "user"
    assert ev.kind == "msg"
    assert ev.body == "hello world"
    assert ev.event_id == "u1"


def test_parse_cc_jsonl_assistant_thinking_and_tool_use(tmp_path: Path) -> None:
    """Assistant row with thinking + tool_use → two events with kinds reasoning, tool_call."""
    fp = tmp_path / "sid2.jsonl"
    _write_jsonl(fp, [
        {
            "type": "assistant",
            "uuid": "a1",
            "timestamp": "2026-05-18T10:01:00.000Z",
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "thinking", "thinking": "I'll list the files"},
                    {
                        "type": "tool_use",
                        "id": "toolu_1",
                        "name": "Bash",
                        "input": {"command": "ls /tmp"},
                    },
                ],
            },
        }
    ])
    result = parse_cc_jsonl(fp)
    assert [e.kind for e in result.events] == ["reasoning", "tool_call"]
    assert result.events[0].body == "I'll list the files"
    tc = result.events[1]
    assert tc.tool_name == "Bash"
    assert tc.args == {"command": "ls /tmp"}
    assert tc.args_summary == "Bash · ls /tmp"


def test_parse_cc_jsonl_tool_result_under_user_row(tmp_path: Path) -> None:
    """A user row with content=[tool_result] becomes one kind=tool_result event."""
    fp = tmp_path / "sid3.jsonl"
    _write_jsonl(fp, [
        {
            "type": "user",
            "uuid": "u2",
            "timestamp": "2026-05-18T10:02:00.000Z",
            "message": {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_1",
                        "is_error": False,
                        "content": "file1\nfile2\n",
                    }
                ],
            },
        }
    ])
    result = parse_cc_jsonl(fp)
    assert len(result.events) == 1
    ev = result.events[0]
    assert ev.kind == "tool_result"
    assert ev.body == "file1\nfile2\n"
    assert ev.result == "file1\nfile2\n"


def test_parse_cc_jsonl_skips_non_display_types(tmp_path: Path) -> None:
    """attachment / queue-operation / last-prompt produce no events."""
    fp = tmp_path / "sid4.jsonl"
    _write_jsonl(fp, [
        {"type": "queue-operation", "operation": "enqueue", "timestamp": "..."},
        {"type": "attachment", "attachment": {}, "timestamp": "..."},
        {"type": "last-prompt", "lastPrompt": "x", "sessionId": "s"},
    ])
    result = parse_cc_jsonl(fp)
    assert result.events == []


def test_parse_cc_jsonl_partial_on_decode_error(tmp_path: Path) -> None:
    """Mid-file JSON decode error → events up to that line + partial=True."""
    fp = tmp_path / "sid5.jsonl"
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(
        json.dumps({
            "type": "user", "uuid": "u1",
            "timestamp": "...",
            "message": {"role": "user", "content": "valid"},
        }) + "\n"
        + "{not valid json\n"
        + json.dumps({
            "type": "user", "uuid": "u2",
            "timestamp": "...",
            "message": {"role": "user", "content": "after broken line"},
        }) + "\n"
    )
    result = parse_cc_jsonl(fp)
    assert result.partial is True
    assert len(result.events) == 1
    assert result.events[0].body == "valid"


def test_parse_cc_jsonl_missing_file_returns_partial(tmp_path: Path) -> None:
    """Vanished file → empty events + partial=True (no exception leaks)."""
    fp = tmp_path / "nope.jsonl"
    result = parse_cc_jsonl(fp)
    assert result.partial is True
    assert result.events == []


# ---------------------------------------------------------------------------
# Codex JSONL fixtures
# ---------------------------------------------------------------------------


def test_parse_codex_jsonl_user_and_agent_messages(tmp_path: Path) -> None:
    """user_message → role=user; agent_message → role=agent."""
    fp = tmp_path / "rollout-2026-05-18T10-00-00-abc.jsonl"
    _write_jsonl(fp, [
        {
            "type": "event_msg",
            "timestamp": "2026-05-18T10:00:00Z",
            "payload": {"type": "user_message", "message": "hi codex"},
        },
        {
            "type": "event_msg",
            "timestamp": "2026-05-18T10:00:01Z",
            "payload": {"type": "agent_message", "message": "hi back"},
        },
    ])
    result = parse_codex_jsonl(fp)
    roles = [e.role for e in result.events]
    bodies = [e.body for e in result.events]
    assert roles == ["user", "agent"]
    assert bodies == ["hi codex", "hi back"]


def test_parse_codex_jsonl_function_call_and_output(tmp_path: Path) -> None:
    """function_call → tool_call with parsed args; function_call_output → tool_result."""
    fp = tmp_path / "rollout-x.jsonl"
    _write_jsonl(fp, [
        {
            "type": "response_item",
            "timestamp": "2026-05-18T10:00:00Z",
            "payload": {
                "type": "function_call",
                "name": "exec_command",
                "call_id": "call_42",
                "arguments": json.dumps({"cmd": "ls /tmp"}),
            },
        },
        {
            "type": "response_item",
            "timestamp": "2026-05-18T10:00:01Z",
            "payload": {
                "type": "function_call_output",
                "call_id": "call_42",
                "output": "file1\nfile2\n",
            },
        },
    ])
    result = parse_codex_jsonl(fp)
    assert [e.kind for e in result.events] == ["tool_call", "tool_result"]
    tc = result.events[0]
    assert tc.tool_name == "exec_command"
    assert tc.args == {"cmd": "ls /tmp"}
    tr = result.events[1]
    assert tr.body == "file1\nfile2\n"


def test_parse_codex_jsonl_task_aborted_becomes_session_end(tmp_path: Path) -> None:
    """Codex task_aborted → kind=session_end row carries reason in body."""
    fp = tmp_path / "rollout-y.jsonl"
    _write_jsonl(fp, [
        {
            "type": "event_msg",
            "timestamp": "2026-05-18T10:00:00Z",
            "payload": {"type": "task_aborted", "reason": "user_cancelled"},
        }
    ])
    result = parse_codex_jsonl(fp)
    assert len(result.events) == 1
    ev = result.events[0]
    assert ev.kind == "session_end"
    assert "task_aborted" in ev.body
    assert "user_cancelled" in ev.body


def test_parse_codex_jsonl_reasoning_encrypted_falls_back_to_placeholder(
    tmp_path: Path,
) -> None:
    """Encrypted reasoning (no summary) renders the placeholder text."""
    fp = tmp_path / "rollout-z.jsonl"
    _write_jsonl(fp, [
        {
            "type": "response_item",
            "timestamp": "2026-05-18T10:00:00Z",
            "payload": {
                "type": "reasoning",
                "summary": [],
                "encrypted_content": "gAAAAAB...",
            },
        }
    ])
    result = parse_codex_jsonl(fp)
    assert len(result.events) == 1
    ev = result.events[0]
    assert ev.kind == "reasoning"
    assert "encrypted" in ev.body.lower() or "unavailable" in ev.body.lower()


def test_parse_codex_jsonl_skips_developer_message(tmp_path: Path) -> None:
    """response_item / message with role=developer (system bootstrap) is skipped."""
    fp = tmp_path / "rollout-w.jsonl"
    _write_jsonl(fp, [
        {
            "type": "response_item",
            "timestamp": "2026-05-18T10:00:00Z",
            "payload": {
                "type": "message",
                "role": "developer",
                "content": [{"type": "input_text", "text": "system prompt"}],
            },
        },
        {
            "type": "event_msg",
            "timestamp": "2026-05-18T10:00:01Z",
            "payload": {"type": "user_message", "message": "real user"},
        },
    ])
    result = parse_codex_jsonl(fp)
    bodies = [e.body for e in result.events]
    assert bodies == ["real user"]


def test_parse_codex_jsonl_partial_on_decode_error(tmp_path: Path) -> None:
    """Mid-file decode error → partial=True, events up to broken line only."""
    fp = tmp_path / "rollout-broken.jsonl"
    fp.write_text(
        json.dumps({
            "type": "event_msg",
            "timestamp": "...",
            "payload": {"type": "user_message", "message": "hi"},
        }) + "\nnot json\n"
    )
    result = parse_codex_jsonl(fp)
    assert result.partial is True
    assert len(result.events) == 1


# ---------------------------------------------------------------------------
# Registry lookup
# ---------------------------------------------------------------------------


def test_lookup_session_in_registry_finds_start_row(tmp_path: Path) -> None:
    """Latest-row-wins: a start row resolves (source, file_path)."""
    reg = tmp_path / "sessions.jsonl"
    _write_jsonl(reg, [
        {
            "session_id": "sid_known",
            "client_id": "acme",
            "source": "cc",
            "file_path": "/abs/path/to/sid_known.jsonl",
            "started_at": "2026-05-18T10:00:00Z",
            "hook_emitted": False,
        }
    ])
    lookup = lookup_session_in_registry(reg, "sid_known")
    assert lookup is not None
    assert lookup.source == "cc"
    assert lookup.file_path == "/abs/path/to/sid_known.jsonl"
    assert lookup.ended_at is None


def test_lookup_session_in_registry_overlays_end_row(tmp_path: Path) -> None:
    """A start row + an end row → ended_at populated on the lookup."""
    reg = tmp_path / "sessions.jsonl"
    _write_jsonl(reg, [
        {
            "session_id": "sid_done",
            "client_id": "acme",
            "source": "codex",
            "file_path": "/abs/p.jsonl",
            "started_at": "2026-05-18T10:00:00Z",
        },
        {
            "session_id": "sid_done",
            "ended_at": "2026-05-18T11:00:00Z",
            "reason": "task_completed",
        },
    ])
    lookup = lookup_session_in_registry(reg, "sid_done")
    assert lookup is not None
    assert lookup.ended_at == "2026-05-18T11:00:00Z"


def test_lookup_session_in_registry_unknown_returns_none(tmp_path: Path) -> None:
    """A session_id not in the registry → None (caller emits 404)."""
    reg = tmp_path / "sessions.jsonl"
    _write_jsonl(reg, [
        {
            "session_id": "sid_a",
            "source": "cc",
            "file_path": "/x.jsonl",
            "started_at": "...",
        }
    ])
    assert lookup_session_in_registry(reg, "sid_unknown") is None


def test_lookup_session_in_registry_missing_file_returns_none(tmp_path: Path) -> None:
    """Registry file doesn't exist (tenant has had zero sessions) → None."""
    assert lookup_session_in_registry(tmp_path / "nope.jsonl", "sid") is None


def test_lookup_session_in_registry_tolerates_bad_lines(tmp_path: Path) -> None:
    """A garbled JSON line in the middle does not crash the scan."""
    reg = tmp_path / "sessions.jsonl"
    reg.parent.mkdir(parents=True, exist_ok=True)
    reg.write_text(
        "this is not json\n"
        + json.dumps({
            "session_id": "sid_real",
            "source": "cc",
            "file_path": "/x.jsonl",
            "started_at": "...",
        }) + "\n"
    )
    lookup = lookup_session_in_registry(reg, "sid_real")
    assert lookup is not None
    assert lookup.source == "cc"


def test_transcript_event_dataclass_carries_expected_fields() -> None:
    """Smoke test: dataclass instantiates with the documented field set.

    Locks the public contract so the route's template doesn't drift if
    we add fields in a future iteration.
    """
    ev = TranscriptEvent(
        event_id="x",
        role="user",
        kind="msg",
        body="b",
        ts="2026-05-18T10:00:00Z",
    )
    assert ev.tool_name is None
    assert ev.args is None
    assert ev.result is None
    assert ev.token_counts is None
