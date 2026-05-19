"""Unit 6 portal transcript drill-down tests.

Coverage matches the plan's §"Unit 6: Transcript drill-down route + renderer"
test scenarios:

  Happy paths       CC + Codex transcripts render, reasoning collapsed,
                    redaction footer absent on clean transcripts.
  Edge cases        IDOR registry-miss → 404 not 403, cross-tenant 404,
                    reasoning class collapsed, Codex task_aborted row.
  Error paths       Registry file_path vanished mid-request → 404, JSONL
                    parse error mid-file → truncation footer present.
  Security (T8)     Path traversal: /etc/passwd, dot-dot, symlink-target,
                    symlink-in-parent — all 404 transcript_unavailable.
  Security (T4)     <script> escaped; CSP header present; img onerror escaped.
  Redaction (T3)    .env file_path → result replaced with the Unit 5 summary.

Requires local Supabase + Postgres (conftest auto-skips when down).
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Iterator
from unittest.mock import patch

import httpx
import pytest

from src.portal.transcript_tailer import session_registry_path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def _seed_registry(slug: str, rows: list[dict]) -> Path:
    """Write rows into clients/<slug>/audit/sessions.jsonl relative to CWD.

    Tests chdir into a tmp dir before calling this so the relative
    ``clients/...`` path lives inside the per-test sandbox.
    """
    reg_path = session_registry_path(slug)
    reg_path.parent.mkdir(parents=True, exist_ok=True)
    with reg_path.open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    return reg_path


def _cc_transcript_rows() -> list[dict]:
    """A minimal but realistic CC session: user prompt + assistant reasoning +
    assistant tool_use + tool_result."""
    return [
        {
            "type": "user",
            "uuid": "u1",
            "timestamp": "2026-05-18T10:00:00.000Z",
            "message": {"role": "user", "content": "Please list /tmp"},
        },
        {
            "type": "assistant",
            "uuid": "a1",
            "timestamp": "2026-05-18T10:00:05.000Z",
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "thinking", "thinking": "User wants ls /tmp"},
                    {
                        "type": "tool_use",
                        "id": "toolu_1",
                        "name": "Bash",
                        "input": {"command": "ls /tmp"},
                    },
                ],
            },
        },
        {
            "type": "user",
            "uuid": "u2",
            "timestamp": "2026-05-18T10:00:06.000Z",
            "message": {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_1",
                        "content": "file_a\nfile_b\n",
                    }
                ],
            },
        },
    ]


def _codex_transcript_rows() -> list[dict]:
    """Codex rollout with user_message + agent_message + task_aborted end."""
    return [
        {
            "type": "event_msg",
            "timestamp": "2026-05-18T11:00:00Z",
            "payload": {"type": "user_message", "message": "hello codex"},
        },
        {
            "type": "event_msg",
            "timestamp": "2026-05-18T11:00:01Z",
            "payload": {"type": "agent_message", "message": "hello back"},
        },
        {
            "type": "event_msg",
            "timestamp": "2026-05-18T11:00:02Z",
            "payload": {"type": "task_aborted", "reason": "user_cancelled"},
        },
    ]


# ---------------------------------------------------------------------------
# Happy path — CC
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_transcript_cc_happy_path_renders_html(
    api_client: httpx.AsyncClient, test_tenant: dict, tmp_path: Path
) -> None:
    """CC transcript renders 200 HTML with reasoning collapsed + tool call row."""
    slug = test_tenant["client_slug"]
    sid = "sid_cc_happy"

    # Place the JSONL inside a fake CC root we redirect cc_root() to.
    cc_root_dir = tmp_path / ".claude" / "projects" / "-tmp-acme"
    cc_root_dir.mkdir(parents=True)
    transcript_file = cc_root_dir / f"{sid}.jsonl"
    _write_jsonl(transcript_file, _cc_transcript_rows())

    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        _seed_registry(slug, [
            {
                "session_id": sid,
                "client_id": slug,
                "source": "cc",
                "file_path": str(transcript_file),
                "started_at": "2026-05-18T10:00:00Z",
            }
        ])

        with patch("src.api.routers.portal.cc_root",
                   return_value=tmp_path / ".claude" / "projects"):
            r = await api_client.get(
                f"/portal/{slug}/transcript/{sid}",
                headers={"Authorization": f"Bearer {test_tenant['token']}"},
            )
        assert r.status_code == 200, r.text
        body = r.text
        # Reasoning row carries collapsed marker class.
        assert "agent-reasoning collapsed" in body
        # Tool call row + summary one-liner are present.
        assert "Bash · ls /tmp" in body
        # User prompt visible.
        assert "Please list /tmp" in body
        # CSP header present.
        csp = r.headers.get("Content-Security-Policy") or ""
        assert "default-src 'self'" in csp
        assert "script-src 'self'" in csp
        assert "object-src 'none'" in csp
    finally:
        os.chdir(old_cwd)


# ---------------------------------------------------------------------------
# Happy path — Codex
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_transcript_codex_task_aborted_renders_session_end(
    api_client: httpx.AsyncClient, test_tenant: dict, tmp_path: Path
) -> None:
    """Codex rollout with task_aborted → 200 + session-end row visible."""
    slug = test_tenant["client_slug"]
    sid = "sid_codex_abort"

    codex_root_dir = tmp_path / ".codex" / "sessions" / "2026" / "05" / "18"
    codex_root_dir.mkdir(parents=True)
    transcript_file = codex_root_dir / f"rollout-2026-05-18T11-00-00-{sid}.jsonl"
    _write_jsonl(transcript_file, _codex_transcript_rows())

    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        _seed_registry(slug, [
            {
                "session_id": sid,
                "client_id": slug,
                "source": "codex",
                "file_path": str(transcript_file),
                "started_at": "2026-05-18T11:00:00Z",
            }
        ])

        with patch("src.api.routers.portal.codex_root",
                   return_value=tmp_path / ".codex" / "sessions"):
            r = await api_client.get(
                f"/portal/{slug}/transcript/{sid}",
                headers={"Authorization": f"Bearer {test_tenant['token']}"},
            )
        assert r.status_code == 200, r.text
        body = r.text
        assert "task_aborted" in body
        assert "user_cancelled" in body
        # Both messages rendered.
        assert "hello codex" in body
        assert "hello back" in body
    finally:
        os.chdir(old_cwd)


# ---------------------------------------------------------------------------
# IDOR — registry miss returns 404
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_transcript_unknown_session_id_returns_404(
    api_client: httpx.AsyncClient, test_tenant: dict, tmp_path: Path
) -> None:
    """No registry row for session_id → 404 transcript_unavailable.

    The session may exist for another tenant; the route MUST NOT 403 here.
    """
    slug = test_tenant["client_slug"]

    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        # Registry exists but is empty.
        _seed_registry(slug, [])
        r = await api_client.get(
            f"/portal/{slug}/transcript/sid_ghost",
            headers={"Authorization": f"Bearer {test_tenant['token']}"},
        )
        assert r.status_code == 404
        assert r.headers.get("X-Error-Code") == "transcript_unavailable"
    finally:
        os.chdir(old_cwd)


@pytest.mark.asyncio
async def test_transcript_cross_tenant_registry_still_404(
    api_client: httpx.AsyncClient, test_tenant: dict, tmp_path: Path
) -> None:
    """A session_id present in another tenant's registry but not in this one → 404."""
    slug = test_tenant["client_slug"]

    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        # Plant a row in a different tenant's registry.
        cc_root_dir = tmp_path / ".claude" / "projects" / "-tmp-other"
        cc_root_dir.mkdir(parents=True)
        other_tx = cc_root_dir / "sid_other.jsonl"
        _write_jsonl(other_tx, _cc_transcript_rows())
        _seed_registry("other-tenant", [
            {
                "session_id": "sid_other",
                "client_id": "other-tenant",
                "source": "cc",
                "file_path": str(other_tx),
                "started_at": "...",
            }
        ])
        # Authenticated user's tenant has no such row.
        _seed_registry(slug, [])

        r = await api_client.get(
            f"/portal/{slug}/transcript/sid_other",
            headers={"Authorization": f"Bearer {test_tenant['token']}"},
        )
        assert r.status_code == 404
        assert r.headers.get("X-Error-Code") == "transcript_unavailable"
    finally:
        os.chdir(old_cwd)


@pytest.mark.asyncio
async def test_transcript_no_membership_returns_403(
    api_client: httpx.AsyncClient, outsider: dict, test_tenant: dict
) -> None:
    """Outsider JWT with no membership on the slug → 403 no_membership."""
    slug = test_tenant["client_slug"]
    r = await api_client.get(
        f"/portal/{slug}/transcript/whatever",
        headers={"Authorization": f"Bearer {outsider['token']}"},
    )
    assert r.status_code == 403
    assert r.headers.get("X-Error-Code") == "no_membership"


# ---------------------------------------------------------------------------
# Path safety (T8)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_transcript_path_traversal_etc_passwd_returns_404(
    api_client: httpx.AsyncClient, test_tenant: dict, tmp_path: Path
) -> None:
    """A registry row pointing to /etc/passwd → 404 (NOT 500, NOT a file read)."""
    slug = test_tenant["client_slug"]
    sid = "sid_evil"

    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        _seed_registry(slug, [
            {
                "session_id": sid,
                "client_id": slug,
                "source": "cc",
                "file_path": "/etc/passwd",
                "started_at": "...",
            }
        ])
        with patch("src.api.routers.portal.cc_root",
                   return_value=tmp_path / ".claude" / "projects"):
            r = await api_client.get(
                f"/portal/{slug}/transcript/{sid}",
                headers={"Authorization": f"Bearer {test_tenant['token']}"},
            )
        assert r.status_code == 404
        assert r.headers.get("X-Error-Code") == "transcript_unavailable"
    finally:
        os.chdir(old_cwd)


@pytest.mark.asyncio
async def test_transcript_dotdot_escape_returns_404(
    api_client: httpx.AsyncClient, test_tenant: dict, tmp_path: Path
) -> None:
    """A registry row with ../../etc/shadow.jsonl → resolved outside roots → 404."""
    slug = test_tenant["client_slug"]
    sid = "sid_dotdot"

    # Build a path WITH literal `..` segments that would resolve outside roots.
    cc_root_dir = tmp_path / ".claude" / "projects" / "-tmp"
    cc_root_dir.mkdir(parents=True)
    real_target = tmp_path / "secrets.txt"
    real_target.write_text("nope")
    poisoned = cc_root_dir / ".." / ".." / ".." / "secrets.txt"

    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        _seed_registry(slug, [
            {
                "session_id": sid,
                "client_id": slug,
                "source": "cc",
                "file_path": str(poisoned),
                "started_at": "...",
            }
        ])
        with patch("src.api.routers.portal.cc_root",
                   return_value=tmp_path / ".claude" / "projects"):
            r = await api_client.get(
                f"/portal/{slug}/transcript/{sid}",
                headers={"Authorization": f"Bearer {test_tenant['token']}"},
            )
        assert r.status_code == 404
        assert r.headers.get("X-Error-Code") == "transcript_unavailable"
    finally:
        os.chdir(old_cwd)


@pytest.mark.asyncio
async def test_transcript_symlink_target_outside_roots_returns_404(
    api_client: httpx.AsyncClient, test_tenant: dict, tmp_path: Path
) -> None:
    """A symlink whose target is outside the watched roots → 404."""
    slug = test_tenant["client_slug"]
    sid = "sid_symlink"

    cc_root_dir = tmp_path / ".claude" / "projects" / "-tmp"
    cc_root_dir.mkdir(parents=True)
    outside_target = tmp_path / "outside-roots.jsonl"
    outside_target.write_text(json.dumps({"type": "user"}) + "\n")
    sym = cc_root_dir / "sid_symlink.jsonl"
    sym.symlink_to(outside_target)

    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        _seed_registry(slug, [
            {
                "session_id": sid,
                "client_id": slug,
                "source": "cc",
                "file_path": str(sym),
                "started_at": "...",
            }
        ])
        with patch("src.api.routers.portal.cc_root",
                   return_value=tmp_path / ".claude" / "projects"):
            r = await api_client.get(
                f"/portal/{slug}/transcript/{sid}",
                headers={"Authorization": f"Bearer {test_tenant['token']}"},
            )
        assert r.status_code == 404
        assert r.headers.get("X-Error-Code") == "transcript_unavailable"
    finally:
        os.chdir(old_cwd)


@pytest.mark.asyncio
async def test_transcript_symlink_in_parent_returns_404(
    api_client: httpx.AsyncClient, test_tenant: dict, tmp_path: Path
) -> None:
    """A parent directory that is itself a symlink → 404 (defense-in-depth)."""
    slug = test_tenant["client_slug"]
    sid = "sid_symparent"

    # Set up a real CC project directory.
    real_dir = tmp_path / "real-projects" / "-tmp"
    real_dir.mkdir(parents=True)
    target_file = real_dir / "sid_symparent.jsonl"
    _write_jsonl(target_file, _cc_transcript_rows())

    # Symlink projects/-tmp inside the watched root to the real_dir parent.
    proj_link_parent = tmp_path / ".claude" / "projects"
    proj_link_parent.mkdir(parents=True)
    symdir = proj_link_parent / "-tmp"
    symdir.symlink_to(real_dir)

    poisoned_path = symdir / "sid_symparent.jsonl"

    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        _seed_registry(slug, [
            {
                "session_id": sid,
                "client_id": slug,
                "source": "cc",
                "file_path": str(poisoned_path),
                "started_at": "...",
            }
        ])
        with patch("src.api.routers.portal.cc_root",
                   return_value=tmp_path / ".claude" / "projects"):
            r = await api_client.get(
                f"/portal/{slug}/transcript/{sid}",
                headers={"Authorization": f"Bearer {test_tenant['token']}"},
            )
        # The parent segment is a symlink → _safe_transcript_path rejects.
        assert r.status_code == 404
        assert r.headers.get("X-Error-Code") == "transcript_unavailable"
    finally:
        os.chdir(old_cwd)


# ---------------------------------------------------------------------------
# Disk race — file vanished between registry write and request
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_transcript_registry_filepath_missing_returns_404(
    api_client: httpx.AsyncClient, test_tenant: dict, tmp_path: Path
) -> None:
    """Tailer recorded the path; operator deleted the file → 404."""
    slug = test_tenant["client_slug"]
    sid = "sid_gone"

    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        _seed_registry(slug, [
            {
                "session_id": sid,
                "client_id": slug,
                "source": "cc",
                "file_path": str(tmp_path / ".claude" / "projects" / "-x" / "sid_gone.jsonl"),
                "started_at": "...",
            }
        ])
        with patch("src.api.routers.portal.cc_root",
                   return_value=tmp_path / ".claude" / "projects"):
            r = await api_client.get(
                f"/portal/{slug}/transcript/{sid}",
                headers={"Authorization": f"Bearer {test_tenant['token']}"},
            )
        assert r.status_code == 404
        assert r.headers.get("X-Error-Code") == "transcript_unavailable"
    finally:
        os.chdir(old_cwd)


# ---------------------------------------------------------------------------
# Parse error mid-file → truncation footer
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_transcript_parse_error_renders_truncation_footer(
    api_client: httpx.AsyncClient, test_tenant: dict, tmp_path: Path
) -> None:
    """Bad JSON in line 3 of N → first 2 events render + truncation footer."""
    slug = test_tenant["client_slug"]
    sid = "sid_truncated"

    cc_root_dir = tmp_path / ".claude" / "projects" / "-tmp"
    cc_root_dir.mkdir(parents=True)
    transcript_file = cc_root_dir / f"{sid}.jsonl"
    transcript_file.write_text(
        json.dumps({
            "type": "user", "uuid": "u1",
            "timestamp": "2026-05-18T10:00:00Z",
            "message": {"role": "user", "content": "first valid"},
        }) + "\n"
        + "not json at all\n"
        + json.dumps({
            "type": "user", "uuid": "u2",
            "timestamp": "...",
            "message": {"role": "user", "content": "never reached"},
        }) + "\n"
    )

    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        _seed_registry(slug, [
            {
                "session_id": sid,
                "client_id": slug,
                "source": "cc",
                "file_path": str(transcript_file),
                "started_at": "...",
            }
        ])
        with patch("src.api.routers.portal.cc_root",
                   return_value=tmp_path / ".claude" / "projects"):
            r = await api_client.get(
                f"/portal/{slug}/transcript/{sid}",
                headers={"Authorization": f"Bearer {test_tenant['token']}"},
            )
        assert r.status_code == 200
        assert "first valid" in r.text
        assert "never reached" not in r.text
        assert "Transcript truncated" in r.text
    finally:
        os.chdir(old_cwd)


# ---------------------------------------------------------------------------
# Redaction integration (T3)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_transcript_dotenv_bash_result_is_redacted(
    api_client: httpx.AsyncClient, test_tenant: dict, tmp_path: Path
) -> None:
    """A Bash event whose command names .env → result replaced with one-line summary.

    The tool args remain visible (path is not the secret); the result body
    is replaced. We assert the literal env contents do NOT appear in the
    rendered page.
    """
    slug = test_tenant["client_slug"]
    sid = "sid_env"

    cc_root_dir = tmp_path / ".claude" / "projects" / "-tmp"
    cc_root_dir.mkdir(parents=True)
    transcript_file = cc_root_dir / f"{sid}.jsonl"
    _write_jsonl(transcript_file, [
        {
            "type": "assistant",
            "uuid": "a1",
            "timestamp": "2026-05-18T10:00:00Z",
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_env",
                        "name": "Bash",
                        "input": {"command": "cat .env"},
                    }
                ],
            },
        },
        {
            "type": "user",
            "uuid": "u_env",
            "timestamp": "2026-05-18T10:00:01Z",
            "message": {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_env",
                        "content": "STRIPE_SECRET=sk_test_DEADBEEFSHOULDNOTAPPEAR12345\nDATABASE_URL=postgres://shouldnotappear",
                    }
                ],
            },
        },
    ])

    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        _seed_registry(slug, [
            {
                "session_id": sid,
                "client_id": slug,
                "source": "cc",
                "file_path": str(transcript_file),
                "started_at": "...",
            }
        ])
        with patch("src.api.routers.portal.cc_root",
                   return_value=tmp_path / ".claude" / "projects"):
            r = await api_client.get(
                f"/portal/{slug}/transcript/{sid}",
                headers={"Authorization": f"Bearer {test_tenant['token']}"},
            )
        assert r.status_code == 200
        body = r.text
        # The secret value MUST NOT appear.
        assert "DEADBEEFSHOULDNOTAPPEAR12345" not in body
        # The command path remains visible.
        assert "cat .env" in body
        # Redaction footer indicates count > 0.
        assert "redacted · portal-redactor" in body
    finally:
        os.chdir(old_cwd)


@pytest.mark.asyncio
async def test_transcript_no_redactions_omits_footer(
    api_client: httpx.AsyncClient, test_tenant: dict, tmp_path: Path
) -> None:
    """Clean transcript → redaction footer is NOT in the rendered HTML."""
    slug = test_tenant["client_slug"]
    sid = "sid_clean"

    cc_root_dir = tmp_path / ".claude" / "projects" / "-tmp"
    cc_root_dir.mkdir(parents=True)
    transcript_file = cc_root_dir / f"{sid}.jsonl"
    _write_jsonl(transcript_file, _cc_transcript_rows())

    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        _seed_registry(slug, [
            {
                "session_id": sid,
                "client_id": slug,
                "source": "cc",
                "file_path": str(transcript_file),
                "started_at": "...",
            }
        ])
        with patch("src.api.routers.portal.cc_root",
                   return_value=tmp_path / ".claude" / "projects"):
            r = await api_client.get(
                f"/portal/{slug}/transcript/{sid}",
                headers={"Authorization": f"Bearer {test_tenant['token']}"},
            )
        assert r.status_code == 200
        assert "redacted · portal-redactor" not in r.text
    finally:
        os.chdir(old_cwd)


# ---------------------------------------------------------------------------
# XSS / CSP (T4)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_transcript_xss_in_agent_text_is_escaped(
    api_client: httpx.AsyncClient, test_tenant: dict, tmp_path: Path
) -> None:
    """Agent text with <script>alert(1)</script> renders escaped — no literal tag."""
    slug = test_tenant["client_slug"]
    sid = "sid_xss"

    cc_root_dir = tmp_path / ".claude" / "projects" / "-tmp"
    cc_root_dir.mkdir(parents=True)
    transcript_file = cc_root_dir / f"{sid}.jsonl"
    _write_jsonl(transcript_file, [
        {
            "type": "assistant",
            "uuid": "a1",
            "timestamp": "2026-05-18T10:00:00Z",
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "<script>alert(1)</script>"},
                    {"type": "text", "text": "<img src=x onerror=alert(2)>"},
                ],
            },
        }
    ])

    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        _seed_registry(slug, [
            {
                "session_id": sid,
                "client_id": slug,
                "source": "cc",
                "file_path": str(transcript_file),
                "started_at": "...",
            }
        ])
        with patch("src.api.routers.portal.cc_root",
                   return_value=tmp_path / ".claude" / "projects"):
            r = await api_client.get(
                f"/portal/{slug}/transcript/{sid}",
                headers={"Authorization": f"Bearer {test_tenant['token']}"},
            )
        assert r.status_code == 200
        body = r.text
        # Literal <script> tag MUST NOT appear; escaped form may.
        assert "<script>alert(1)</script>" not in body
        # The escaped form should appear.
        assert "&lt;script&gt;alert(1)" in body or "&lt;script&gt;" in body
        # img onerror — same check.
        assert "<img src=x onerror=" not in body
    finally:
        os.chdir(old_cwd)
