"""Tests for ``src/portal/redaction.py`` — Unit 5 of the portal-moments redesign.

Covers every scenario listed in the plan's Unit 5 §"Test scenarios":

- Happy paths (Anthropic key, JWT, OPENAI_API_KEY=, password=, DATABASE_URL=,
  Supabase service_role).
- Edge cases (no secrets; R-Sec-2 Bash/Read denylist + wildcard + negatives;
  R-Sec-2 evasions: $HOME / `head .env` / `python -c`; broader tools
  Write/Grep; R-Sec-5 HTML render-time).
- Integration (R-Sec-3 audit log emits operator-internal moment per record;
  R-Sec-4 redactor_version stamping).

Audit-log integration tests monkeypatch ``log_event`` at the module
boundary so we never write to the operator's real ``events.jsonl``.
"""
from __future__ import annotations

from typing import Any

import pytest

from src.portal import redaction
from src.portal.redaction import (
    REDACTOR_VERSION,
    RedactionRecord,
    redact_metadata,
    redact_text,
    redact_transcript_event,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def captured_audit_events(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """Capture all ``log_event`` calls made by the redaction layer.

    Replaces the imported ``log_event`` reference inside ``redaction`` so we
    never touch the operator's real events.jsonl during tests.
    """
    events: list[dict[str, Any]] = []

    def fake_log_event(kind: str, *, path: Any = None, **data: Any) -> None:
        events.append({"kind": kind, "path": path, **data})

    monkeypatch.setattr(redaction, "log_event", fake_log_event)
    return events


# ---------------------------------------------------------------------------
# redact_text — happy paths (R-Sec-1)
# ---------------------------------------------------------------------------

def test_redact_text_anthropic_key(captured_audit_events) -> None:
    text = "Here is my key: " + "sk-ant-" + ("api03-" + "a" * 40)
    out, records = redact_text(text, source="transcript")
    assert "<redacted:anthropic_key>" in out
    assert any(r.redaction_kind == "anthropic_key" for r in records)
    rec = next(r for r in records if r.redaction_kind == "anthropic_key")
    assert rec.source == "transcript"
    assert rec.original_length > 0


def test_redact_text_jwt(captured_audit_events) -> None:
    text = "eyJ" + "abc" * 8 + ".eyJ" + "def" * 8 + ".sig" + "a" * 20
    out, records = redact_text(text)
    assert "<redacted:jwt>" in out
    assert any(r.redaction_kind == "jwt" for r in records)


def test_redact_text_env_var_api_key(captured_audit_events) -> None:
    text = "OPENAI_API_KEY=" + "sk-proj-" + "abc12345"
    out, records = redact_text(text)
    assert "<redacted:env_var_key>" in out
    kinds = {r.redaction_kind for r in records}
    assert "env_var_key" in kinds


def test_redact_text_password_literal(captured_audit_events) -> None:
    text = "password=hunter2"
    out, records = redact_text(text)
    assert "<redacted:password>" in out
    assert any(r.redaction_kind == "password" for r in records)


def test_redact_text_database_url(captured_audit_events) -> None:
    text = "DATABASE_URL=postgresql://" + "myuser:" + "myp4ss@" + "db.host:5432/mydb"
    out, records = redact_text(text)
    assert "<redacted:" in out
    kinds = {r.redaction_kind for r in records}
    # db_url should fire on the postgresql://user:pass@host part
    assert "db_url" in kinds, f"expected db_url, got kinds={kinds}"


def test_redact_text_supabase_service_role_via_jwt() -> None:
    # Supabase service_role keys ARE JWTs (eyJ. eyJ. sig). Verifies the
    # existing JWT pattern covers them — no new pattern required.
    header = "eyJ" + "alg" * 8 + "_X"
    payload = "eyJ" + "role_service_role" * 3
    sig = "sig" + "a" * 32
    fake_jwt = f"{header}.{payload}.{sig}"
    out, records = redact_text(fake_jwt)
    assert "<redacted:jwt>" in out
    assert any(r.redaction_kind == "jwt" for r in records)


# ---------------------------------------------------------------------------
# redact_text — edge cases
# ---------------------------------------------------------------------------

def test_redact_text_no_secrets_returns_verbatim() -> None:
    text = "Just plain prose, nothing to redact here."
    out, records = redact_text(text)
    assert out == text
    assert records == []


def test_redact_text_empty_string() -> None:
    out, records = redact_text("")
    assert out == ""
    assert records == []


def test_redact_text_source_passed_through(captured_audit_events) -> None:
    text = "OPENAI_API_KEY=" + "sk-proj-" + "abc12345"
    _, records = redact_text(text, source="moment_title")
    assert records
    assert all(r.source == "moment_title" for r in records)


# ---------------------------------------------------------------------------
# R-Sec-5: HTML-escape is NOT a redaction concern
# ---------------------------------------------------------------------------

def test_redact_text_does_not_html_escape() -> None:
    # HTML escape happens at render time (Unit 6/7). redact_text returns
    # raw text, so <script> stays literal.
    text = "<script>alert('x')</script>"
    out, records = redact_text(text)
    assert out == text
    assert records == []


def test_redact_text_marker_is_literal_not_escaped() -> None:
    # The redaction marker itself is literal text — Jinja autoescape at
    # render time will convert < and > to &lt; / &gt;. We verify here that
    # redact_text returns the marker unescaped.
    text = "secret OPENAI_API_KEY=" + ("x" * 16)
    out, _ = redact_text(text)
    assert "<redacted:env_var_key>" in out
    assert "&lt;redacted" not in out


# ---------------------------------------------------------------------------
# redact_metadata — walks dicts + lists
# ---------------------------------------------------------------------------

def test_redact_metadata_walks_string_leaves(captured_audit_events) -> None:
    meta = {
        "title": "OPENAI_API_KEY=" + ("x" * 16),
        "body": "no secrets here",
        "tokens": 42,
        "nested": {
            "args_summary": "password=hunter2",
            "list_field": ["clean text", "AKIA" + "IOSFODNN7EXAMPLE"],
        },
    }
    out, records = redact_metadata(meta)
    assert "<redacted:env_var_key>" in out["title"]
    assert out["body"] == "no secrets here"
    assert out["tokens"] == 42  # non-string preserved
    assert "<redacted:password>" in out["nested"]["args_summary"]
    assert "<redacted:aws_access_key>" in out["nested"]["list_field"][1]
    # Original not mutated
    assert meta["title"] == "OPENAI_API_KEY=" + ("x" * 16)
    kinds = {r.redaction_kind for r in records}
    assert {"env_var_key", "password", "aws_access_key"} <= kinds


def test_redact_metadata_source_defaults_to_moment_meta(captured_audit_events) -> None:
    meta = {"title": "password=hunter2"}
    _, records = redact_metadata(meta)
    assert all(r.source == "moment_meta" for r in records)


def test_redact_metadata_explicit_source(captured_audit_events) -> None:
    meta = {"title": "password=hunter2"}
    _, records = redact_metadata(meta, source="moment_title")
    assert all(r.source == "moment_title" for r in records)


def test_redact_metadata_preserves_non_string_types() -> None:
    meta = {"count": 42, "flag": True, "rate": 1.5, "nothing": None}
    out, records = redact_metadata(meta)
    assert out == meta
    assert records == []


# ---------------------------------------------------------------------------
# redact_transcript_event — Layer 1 (file denylist) HAPPY PATHS
# ---------------------------------------------------------------------------

def test_bash_cat_env_redacts_result(captured_audit_events) -> None:
    ev = {
        "tool_name": "Bash",
        "args": {"command": "cat .env"},
        "result": "API_KEY=supersecret\nDB_PASSWORD=hunter2",
    }
    out, records = redact_transcript_event(ev)
    # Args preserved (path is not the secret)
    assert out["args"]["command"] == "cat .env"
    # Result replaced with summary
    assert "contents redacted" in out["result"]
    assert "API_KEY=supersecret" not in out["result"]
    assert "hunter2" not in out["result"]
    # file_denylist record present
    assert any(r.redaction_kind == "file_denylist" for r in records)


def test_read_dot_env_file_redacts(captured_audit_events) -> None:
    ev = {
        "tool_name": "Read",
        "args": {"file_path": "/home/user/.env"},
        "result": "SUPABASE_KEY=" + ("x" * 24),
    }
    out, records = redact_transcript_event(ev)
    assert "contents redacted" in out["result"]
    assert any(r.redaction_kind == "file_denylist" for r in records)
    # Path remains visible in args + summary
    assert "/home/user/.env" in out["args"]["file_path"]


def test_read_id_rsa_redacts(captured_audit_events) -> None:
    ev = {
        "tool_name": "Read",
        "args": {"file_path": "/home/user/secrets/id_rsa"},
        "result": "-----BEGIN RSA PRIVATE KEY-----\nXXX\n-----END RSA PRIVATE KEY-----",
    }
    out, records = redact_transcript_event(ev)
    assert "contents redacted" in out["result"]
    assert any(r.redaction_kind == "file_denylist" for r in records)


def test_read_pem_file_redacts(captured_audit_events) -> None:
    ev = {
        "tool_name": "Read",
        "args": {"file_path": "/opt/certs/server.pem"},
        "result": "-----BEGIN PRIVATE KEY-----\nMII...\n-----END PRIVATE KEY-----",
    }
    out, records = redact_transcript_event(ev)
    assert "contents redacted" in out["result"]
    assert any(r.redaction_kind == "file_denylist" for r in records)


# ---------------------------------------------------------------------------
# redact_transcript_event — Layer 1 NEGATIVES (no false denylist trigger)
# ---------------------------------------------------------------------------

def test_read_notes_md_passes_through() -> None:
    ev = {
        "tool_name": "Read",
        "args": {"file_path": "/home/user/notes.md"},
        "result": "Just some markdown notes. No secrets.",
    }
    out, records = redact_transcript_event(ev)
    # Result NOT replaced with summary
    assert out["result"] == "Just some markdown notes. No secrets."
    # No file_denylist record (regex may still find inline secrets, but
    # there are none in this innocent string).
    assert not any(r.redaction_kind == "file_denylist" for r in records)


def test_bash_ls_passes_through() -> None:
    ev = {
        "tool_name": "Bash",
        "args": {"command": "ls -la"},
        "result": "total 0\ndrwxr-xr-x  4 user user 128 Jan  1 .\n",
    }
    out, records = redact_transcript_event(ev)
    assert out["result"] == ev["result"]
    assert not any(r.redaction_kind == "file_denylist" for r in records)


# ---------------------------------------------------------------------------
# redact_transcript_event — Layer 1 EVASION SCENARIOS
# ---------------------------------------------------------------------------

def test_evasion_home_dollar_expansion(
    monkeypatch: pytest.MonkeyPatch, captured_audit_events
) -> None:
    # $HOME-prefixed path should be caught after server-side expansion.
    monkeypatch.setenv("HOME", "/Users/operator")
    ev = {
        "tool_name": "Bash",
        "args": {"command": "cat $HOME/.env"},
        "result": "SECRET=xxx",
    }
    out, records = redact_transcript_event(ev)
    # Should be caught — `.env` substring is in the command directly anyway,
    # AND the $HOME expansion is a defense-in-depth path.
    assert "contents redacted" in out["result"]
    assert any(r.redaction_kind == "file_denylist" for r in records)


def test_evasion_head_dot_env(captured_audit_events) -> None:
    # `head .env` — alternate reader, still names .env in command
    ev = {
        "tool_name": "Bash",
        "args": {"command": "head .env"},
        "result": "SECRET_VALUE=abc123\n",
    }
    out, records = redact_transcript_event(ev)
    assert "contents redacted" in out["result"]
    assert any(r.redaction_kind == "file_denylist" for r in records)


def test_evasion_python_open_dot_env(captured_audit_events) -> None:
    # `python -c '...open(".env").read()...'` — token match on `.env`
    ev = {
        "tool_name": "Bash",
        "args": {"command": "python -c 'print(open(\".env\").read())'"},
        "result": "SUPER_SECRET=topsecret",
    }
    out, records = redact_transcript_event(ev)
    assert "contents redacted" in out["result"]
    assert any(r.redaction_kind == "file_denylist" for r in records)


def test_envrc_caught(captured_audit_events) -> None:
    ev = {
        "tool_name": "Read",
        "args": {"file_path": "/home/user/.envrc"},
        "result": "export API_KEY=xxx",
    }
    out, records = redact_transcript_event(ev)
    assert "contents redacted" in out["result"]
    assert any(r.redaction_kind == "file_denylist" for r in records)


def test_git_credentials_caught(captured_audit_events) -> None:
    ev = {
        "tool_name": "Read",
        "args": {"file_path": "/home/user/.git/credentials"},
        "result": "https://user:token@github.com",
    }
    out, records = redact_transcript_event(ev)
    assert "contents redacted" in out["result"]
    assert any(r.redaction_kind == "file_denylist" for r in records)


# ---------------------------------------------------------------------------
# redact_transcript_event — Layer 1 BROADER TOOLS
# ---------------------------------------------------------------------------

def test_write_tool_dot_env_caught(captured_audit_events) -> None:
    ev = {
        "tool_name": "Write",
        "args": {"file_path": "/home/user/.env", "content": "API_KEY=newvalue"},
        "result": "wrote 1 line",
    }
    out, records = redact_transcript_event(ev)
    assert any(r.redaction_kind == "file_denylist" for r in records)


def test_edit_tool_dot_env_caught(captured_audit_events) -> None:
    ev = {
        "tool_name": "Edit",
        "args": {"file_path": "/home/user/.env", "old_string": "x", "new_string": "y"},
        "result": "edit applied",
    }
    out, records = redact_transcript_event(ev)
    assert any(r.redaction_kind == "file_denylist" for r in records)


def test_grep_tool_path_dot_env_caught(captured_audit_events) -> None:
    # Grep searching `.env` — path field triggers redaction even though
    # `pattern=API_KEY` itself is not a secret.
    ev = {
        "tool_name": "Grep",
        "args": {"pattern": "API_KEY", "path": "/home/user/.env"},
        "result": "API_KEY=topsecret",
    }
    out, records = redact_transcript_event(ev)
    assert any(r.redaction_kind == "file_denylist" for r in records)


def test_notebook_edit_secret_file_caught(captured_audit_events) -> None:
    ev = {
        "tool_name": "NotebookEdit",
        "args": {"notebook_path": "/home/user/secrets/id_rsa"},
        "result": "edit applied",
    }
    out, records = redact_transcript_event(ev)
    assert any(r.redaction_kind == "file_denylist" for r in records)


# ---------------------------------------------------------------------------
# redact_transcript_event — Layer 2 (regex scrub) runs even when Layer 1 misses
# ---------------------------------------------------------------------------

def test_layer_2_catches_inline_secret_in_tool_result(captured_audit_events) -> None:
    # Bash `echo $OPENAI_API_KEY` — `.env`-style file is not named, so
    # Layer 1 doesn't fire. Layer 2 should catch the env-var output.
    ev = {
        "tool_name": "Bash",
        "args": {"command": "env | grep API"},
        "result": "OPENAI_API_KEY=" + ("x" * 16),
    }
    out, records = redact_transcript_event(ev)
    assert "<redacted:env_var_key>" in out["result"]
    kinds = {r.redaction_kind for r in records}
    assert "env_var_key" in kinds


def test_layer_2_catches_jwt_in_agent_text(captured_audit_events) -> None:
    # Non-tool event (e.g. agent_text) — only Layer 2 runs.
    ev = {
        "kind": "agent_text",
        "body": "I see a token: " + "eyJ" + "abc" * 8 + ".eyJ" + "def" * 8 + ".sig" + "x" * 20,
    }
    out, records = redact_transcript_event(ev)
    assert "<redacted:jwt>" in out["body"]
    assert any(r.redaction_kind == "jwt" for r in records)


def test_allow_secret_file_skips_layer_1(captured_audit_events) -> None:
    # v1 flag is present in signature but never True in v1 callers.
    # Verifying it short-circuits Layer 1 when explicitly enabled.
    ev = {
        "tool_name": "Bash",
        "args": {"command": "cat .env"},
        "result": "no_secrets_here",  # innocent value, no regex match
    }
    out, records = redact_transcript_event(ev, allow_secret_file=True)
    # Layer 1 skipped — result preserved
    assert out["result"] == "no_secrets_here"
    assert not any(r.redaction_kind == "file_denylist" for r in records)


def test_redact_transcript_event_does_not_mutate_input(captured_audit_events) -> None:
    original_args = {"command": "cat .env"}
    original_result = "SECRET=xxx"
    ev = {
        "tool_name": "Bash",
        "args": original_args,
        "result": original_result,
    }
    redact_transcript_event(ev)
    # Original dict + nested dict references unchanged
    assert ev["result"] == original_result
    assert ev["args"]["command"] == "cat .env"


# ---------------------------------------------------------------------------
# R-Sec-3: operator-internal audit log
# ---------------------------------------------------------------------------

def test_audit_log_emits_one_event_per_record(
    captured_audit_events: list[dict[str, Any]],
) -> None:
    text = "OPENAI_API_KEY=" + ("x" * 16) + " and password=hunter2"
    _, records = redact_text(text, source="transcript")
    assert len(records) == len(captured_audit_events)
    for ev in captured_audit_events:
        assert ev["kind"] == "moment"
        md = ev["metadata"]
        assert md["moment_kind"] == "redaction_applied"
        assert md["redactor_version"] == REDACTOR_VERSION
        assert "redaction_kind" in md
        assert "source" in md
        assert isinstance(md["original_length"], int)


def test_audit_log_never_stores_original_value(
    captured_audit_events: list[dict[str, Any]],
) -> None:
    # The whole point of R-Sec-3: original secret value MUST NOT appear in
    # the audit log payload.
    secret = "sk-proj-" + "abc12345xxxxxxxxxxxxxxxx"
    text = "OPENAI_API_KEY=" + secret
    redact_text(text)
    for ev in captured_audit_events:
        serialized = repr(ev)
        assert secret not in serialized, f"audit log leaked secret: {serialized}"
        # Also check the secret prefix doesn't show up
        assert "sk-proj-" not in serialized


def test_audit_log_no_client_id_no_path(
    captured_audit_events: list[dict[str, Any]],
) -> None:
    # Operator-internal: no client_id key, no path override.
    text = "password=hunter2"
    redact_text(text)
    assert captured_audit_events
    for ev in captured_audit_events:
        assert ev.get("client_id") is None
        assert ev.get("path") is None


def test_audit_log_emit_audit_false_suppresses(
    captured_audit_events: list[dict[str, Any]],
) -> None:
    text = "password=hunter2"
    redact_text(text, emit_audit=False)
    assert captured_audit_events == []


def test_audit_log_no_secrets_no_events(
    captured_audit_events: list[dict[str, Any]],
) -> None:
    text = "Plain prose, no secrets."
    redact_text(text)
    assert captured_audit_events == []


# ---------------------------------------------------------------------------
# R-Sec-4: versioning
# ---------------------------------------------------------------------------

def test_redactor_version_constant() -> None:
    assert REDACTOR_VERSION == "v1"


def test_audit_records_stamp_redactor_version(
    captured_audit_events: list[dict[str, Any]],
) -> None:
    redact_text("password=hunter2")
    assert captured_audit_events
    for ev in captured_audit_events:
        assert ev["metadata"]["redactor_version"] == REDACTOR_VERSION


# ---------------------------------------------------------------------------
# Integration: redact_transcript_event emits both layer records to audit
# ---------------------------------------------------------------------------

def test_transcript_event_audit_includes_both_layers(
    captured_audit_events: list[dict[str, Any]],
) -> None:
    ev = {
        "tool_name": "Bash",
        "args": {"command": "cat .env && echo password=hunter2"},
        "result": "API_KEY=" + ("x" * 16),
    }
    _, records = redact_transcript_event(ev)
    # Should have file_denylist (layer 1) + at least one regex hit (layer 2)
    kinds = {r.redaction_kind for r in records}
    assert "file_denylist" in kinds
    # Each record → one audit event
    assert len(captured_audit_events) == len(records)
    audit_kinds = {ev["metadata"]["redaction_kind"] for ev in captured_audit_events}
    assert "file_denylist" in audit_kinds


# ---------------------------------------------------------------------------
# RedactionRecord shape invariants
# ---------------------------------------------------------------------------

def test_redaction_record_does_not_store_original_value() -> None:
    rec = RedactionRecord(
        redaction_kind="anthropic_key", source="transcript", original_length=64
    )
    # Dataclass fields: only kind, source, length — no `value` / `original`
    fields = rec.__dataclass_fields__  # type: ignore[attr-defined]
    assert set(fields.keys()) == {"redaction_kind", "source", "original_length"}
