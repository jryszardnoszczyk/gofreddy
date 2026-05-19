"""Unit tests for src/portal/transcript_tailer.py.

Test strategy:
- Internal helpers (glob, attribution, dedup, boundary detection) run
  directly against ``tmp_path`` JSONLs.
- ``Path.home()`` is monkeypatched so CC/Codex roots live under tmp.
- Slug validation seam is overridden per-test (no real asyncpg pool).
- Time source on :class:`SessionRegistry` is overridden so idle-timeout
  scenarios complete in microseconds, not minutes.
- The asyncio task itself is tested via a tight loop with manual cancel.
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

import pytest

from src.portal.transcript_tailer import (
    Attribution,
    RegistryRow,
    SessionRegistry,
    attribute_session,
    canonicalize_under_roots,
    cc_root,
    codex_root,
    decode_cc_dirname,
    detect_codex_terminal_event,
    encode_cwd_for_cc,
    extract_slug_from_cwd,
    is_session_already_started,
    iter_cc_jsonl_files,
    iter_codex_jsonl_files,
    operator_internal_path,
    rebuild_registry_from_disk,
    run_tailer,
    sanity_parse_jsonl,
    session_id_from_cc_path,
    session_id_from_codex_path,
    session_registry_path,
    _resolve_poll_interval,
)


# ---------------------------------------------------------------------------
# Fixtures.
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect ``Path.home()`` (everywhere) to a tmp dir + chdir into it.

    Chdir matters because the production code resolves
    ``clients/<slug>/audit/...`` as a relative path from the cwd. Also
    monkeypatches ``autoresearch.events.EVENTS_LOG`` so any ``log_event``
    call with no explicit ``path=`` (and any call that resolves
    ``client_events_path(None)``) lands under ``home``, not the real
    operator log.
    """
    import autoresearch.events as ev_module
    home = tmp_path / "home"
    home.mkdir()
    # Patch Path.home at the pathlib level so every helper picks it up.
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    # Redirect the operator-internal events.jsonl to the fake home.
    monkeypatch.setattr(
        ev_module,
        "EVENTS_LOG",
        home / ".local" / "share" / "gofreddy" / "events.jsonl",
    )
    # The registry lays out ``clients/<slug>/audit/sessions.jsonl`` relative
    # to cwd; run tests in tmp_path so we don't pollute the repo.
    monkeypatch.chdir(tmp_path)
    return home


async def _always_valid(slug: str) -> bool:
    return True


async def _always_invalid(slug: str) -> bool:
    return False


def _write_cc_session(
    home: Path, encoded_dir: str, sid: str, *, lines: list[dict[str, Any]] | None = None
) -> Path:
    cc_dir = home / ".claude" / "projects" / encoded_dir
    cc_dir.mkdir(parents=True, exist_ok=True)
    path = cc_dir / f"{sid}.jsonl"
    if lines is None:
        lines = [{"type": "user", "message": "hi"}]
    path.write_text("".join(json.dumps(L) + "\n" for L in lines))
    return path


def _write_codex_session(
    home: Path, sid: str, *, cwd: str | None, extra: list[dict[str, Any]] | None = None
) -> Path:
    rollout_dir = home / ".codex" / "sessions" / "2026" / "05" / "18"
    rollout_dir.mkdir(parents=True, exist_ok=True)
    path = rollout_dir / f"rollout-2026-05-18T12-00-00-{sid}.jsonl"
    lines: list[dict[str, Any]] = []
    if cwd is not None:
        lines.append({"type": "session_meta", "cwd": cwd})
    if extra:
        lines.extend(extra)
    if not lines:
        lines = [{"type": "session_meta"}]  # session without cwd
    path.write_text("".join(json.dumps(L) + "\n" for L in lines))
    return path


# ---------------------------------------------------------------------------
# Path / encoding helpers.
# ---------------------------------------------------------------------------


class TestEncoding:
    def test_encode_and_decode_round_trip_simple_path(self) -> None:
        cwd = Path("/tmp/clients/acme/foo")
        encoded = encode_cwd_for_cc(cwd)
        assert encoded == "-tmp-clients-acme-foo"
        decoded = decode_cc_dirname(encoded)
        assert decoded == Path("/tmp/clients/acme/foo")

    def test_decode_handles_missing_leading_marker(self) -> None:
        decoded = decode_cc_dirname("relative-path-no-marker")
        assert decoded == Path("relative/path/no/marker")

    def test_decode_paths_with_legitimate_dashes_are_ambiguous(self) -> None:
        # Path with `-` in a real segment becomes ambiguous after encode/decode.
        encoded = encode_cwd_for_cc(Path("/Users/jr/foo-bar"))
        # Without disk-existence anchoring the decoded path will mistakenly
        # split foo-bar into foo/bar. This documents the limitation.
        decoded = decode_cc_dirname(encoded)
        assert decoded == Path("/Users/jr/foo/bar")
        assert decoded != Path("/Users/jr/foo-bar")


class TestSlugExtraction:
    def test_extract_slug_from_cwd_simple(self) -> None:
        assert extract_slug_from_cwd(Path("/tmp/clients/acme/foo")) == "acme"

    def test_extract_slug_from_cwd_no_segment(self) -> None:
        assert extract_slug_from_cwd(Path("/tmp/random/path")) is None

    def test_extract_slug_from_cwd_trailing_clients(self) -> None:
        # `clients` as last segment has no slug after it.
        assert extract_slug_from_cwd(Path("/tmp/foo/clients")) is None


# ---------------------------------------------------------------------------
# Attribution.
# ---------------------------------------------------------------------------


class TestAttribution:
    @pytest.mark.asyncio
    async def test_attribute_to_valid_slug(self, fake_home: Path) -> None:
        result = await attribute_session(
            Path("/tmp/clients/acme/foo"), is_slug_valid=_always_valid
        )
        assert result == Attribution(client_id="acme", reason=None)

    @pytest.mark.asyncio
    async def test_attribute_no_segment_is_operator_internal(
        self, fake_home: Path
    ) -> None:
        result = await attribute_session(
            Path("/tmp/foo/bar"), is_slug_valid=_always_valid
        )
        assert result.client_id is None
        assert result.reason is None  # not a conflict — just operator-internal

    @pytest.mark.asyncio
    async def test_attribute_invalid_slug_pattern_emits_conflict(
        self, fake_home: Path
    ) -> None:
        result = await attribute_session(
            Path("/tmp/clients/Invalid Slug!/foo"),
            is_slug_valid=_always_valid,
        )
        assert result.client_id is None
        assert result.reason == "slug_invalid"
        op_log = operator_internal_path()
        assert op_log.is_file()
        lines = [json.loads(L) for L in op_log.read_text().splitlines() if L.strip()]
        moments = [
            L for L in lines
            if L["kind"] == "moment"
            and L["metadata"]["moment_kind"] == "attribution_conflict"
        ]
        assert len(moments) == 1
        assert moments[0]["metadata"]["reason"] == "slug_invalid"

    @pytest.mark.asyncio
    async def test_attribute_unknown_slug_emits_conflict(self, fake_home: Path) -> None:
        result = await attribute_session(
            Path("/tmp/clients/ghost/foo"),
            is_slug_valid=_always_invalid,
        )
        assert result.client_id is None
        assert result.reason == "slug_unknown"
        op_log = operator_internal_path()
        lines = [json.loads(L) for L in op_log.read_text().splitlines() if L.strip()]
        moments = [
            L for L in lines
            if L["kind"] == "moment"
            and L["metadata"]["moment_kind"] == "attribution_conflict"
        ]
        assert len(moments) == 1
        assert moments[0]["metadata"]["reason"] == "slug_unknown"


# ---------------------------------------------------------------------------
# Sanity-parse helpers.
# ---------------------------------------------------------------------------


class TestSanityParse:
    def test_cc_with_type_line_is_session(self, tmp_path: Path) -> None:
        p = tmp_path / "a.jsonl"
        p.write_text(json.dumps({"type": "user", "message": "hi"}) + "\n")
        assert sanity_parse_jsonl(p, source="cc").is_session is True

    def test_cc_empty_file_is_not_session(self, tmp_path: Path) -> None:
        p = tmp_path / "a.jsonl"
        p.write_text("")
        assert sanity_parse_jsonl(p, source="cc").is_session is False

    def test_cc_garbage_first_lines_is_not_session(self, tmp_path: Path) -> None:
        p = tmp_path / "a.jsonl"
        p.write_text("not json\nstill not json\n")
        assert sanity_parse_jsonl(p, source="cc").is_session is False

    def test_codex_session_meta_extracts_cwd(self, tmp_path: Path) -> None:
        p = tmp_path / "rollout-x.jsonl"
        p.write_text(json.dumps({"type": "session_meta", "cwd": "/foo/bar"}) + "\n")
        result = sanity_parse_jsonl(p, source="codex")
        assert result.is_session is True
        assert result.codex_cwd == Path("/foo/bar")

    def test_codex_nested_payload_form(self, tmp_path: Path) -> None:
        p = tmp_path / "rollout-x.jsonl"
        p.write_text(
            json.dumps(
                {"payload": {"type": "session_meta", "cwd": "/quux"}, "ts": 0}
            )
            + "\n"
        )
        result = sanity_parse_jsonl(p, source="codex")
        assert result.is_session is True
        assert result.codex_cwd == Path("/quux")


# ---------------------------------------------------------------------------
# Session-id parsers + terminal-event detection.
# ---------------------------------------------------------------------------


class TestSessionIdParsers:
    def test_cc_session_id_is_stem(self) -> None:
        assert session_id_from_cc_path(Path("/foo/abc-123.jsonl")) == "abc-123"

    def test_codex_session_id_match(self) -> None:
        sid = session_id_from_codex_path(
            Path("/x/rollout-2026-05-18T12-00-00-019e1c79.jsonl")
        )
        assert sid == "019e1c79"

    def test_codex_session_id_non_match(self) -> None:
        assert session_id_from_codex_path(Path("/x/not-a-rollout.jsonl")) is None


class TestTerminalEvent:
    def test_detect_task_completed(self, tmp_path: Path) -> None:
        p = tmp_path / "r.jsonl"
        p.write_text(
            json.dumps({"type": "session_meta", "cwd": "/x"}) + "\n"
            + json.dumps({"type": "task_completed"}) + "\n"
        )
        assert detect_codex_terminal_event(p) == "task_completed"

    def test_detect_task_aborted_in_payload(self, tmp_path: Path) -> None:
        p = tmp_path / "r.jsonl"
        p.write_text(
            json.dumps({"payload": {"type": "task_aborted"}}) + "\n"
        )
        assert detect_codex_terminal_event(p) == "task_aborted"

    def test_no_terminal_event_returns_none(self, tmp_path: Path) -> None:
        p = tmp_path / "r.jsonl"
        p.write_text(json.dumps({"type": "session_meta"}) + "\n")
        assert detect_codex_terminal_event(p) is None


# ---------------------------------------------------------------------------
# Dedup (R8.3).
# ---------------------------------------------------------------------------


class TestDedup:
    def test_no_log_means_not_started(self, tmp_path: Path) -> None:
        assert is_session_already_started(
            log_path=tmp_path / "absent.jsonl", session_id="x"
        ) is False

    def test_existing_session_start_is_detected(self, tmp_path: Path) -> None:
        log = tmp_path / "events.jsonl"
        log.write_text(
            json.dumps({
                "kind": "session_start",
                "metadata": {"session_id": "sidX"},
            }) + "\n"
        )
        assert is_session_already_started(log_path=log, session_id="sidX") is True

    def test_other_kind_is_ignored(self, tmp_path: Path) -> None:
        log = tmp_path / "events.jsonl"
        log.write_text(
            json.dumps({"kind": "tool_call", "metadata": {"session_id": "sidX"}}) + "\n"
        )
        assert is_session_already_started(log_path=log, session_id="sidX") is False


# ---------------------------------------------------------------------------
# Registry rebuild from disk.
# ---------------------------------------------------------------------------


class TestRegistryRebuild:
    def test_latest_row_per_session_id(self, tmp_path: Path) -> None:
        reg = tmp_path / "sessions.jsonl"
        reg.write_text(
            json.dumps({
                "session_id": "sidA",
                "client_id": "acme",
                "source": "cc",
                "file_path": "/abs/a.jsonl",
                "started_at": "2026-05-18T00:00:00Z",
                "hook_emitted": False,
            }) + "\n"
            + json.dumps({
                "session_id": "sidB",
                "client_id": None,
                "source": "codex",
                "file_path": "/abs/b.jsonl",
                "started_at": "2026-05-18T00:00:01Z",
                "hook_emitted": False,
            }) + "\n"
            + json.dumps({
                "session_id": "sidA",
                "ended_at": "2026-05-18T00:01:00Z",
                "reason": "idle_timeout",
            }) + "\n"
        )
        state = rebuild_registry_from_disk([reg])
        assert set(state) == {"sidA", "sidB"}
        assert state["sidA"].ended_at == "2026-05-18T00:01:00Z"
        assert state["sidA"].end_reason == "idle_timeout"
        assert state["sidB"].ended_at is None

    def test_stray_end_row_creates_stub(self, tmp_path: Path) -> None:
        reg = tmp_path / "sessions.jsonl"
        reg.write_text(
            json.dumps({
                "session_id": "sidOrphan",
                "ended_at": "2026-05-18T00:00:00Z",
                "reason": "task_completed",
            }) + "\n"
        )
        state = rebuild_registry_from_disk([reg])
        assert "sidOrphan" in state
        assert state["sidOrphan"].ended_at == "2026-05-18T00:00:00Z"


# ---------------------------------------------------------------------------
# Glob helpers.
# ---------------------------------------------------------------------------


class TestGlob:
    def test_iter_cc_jsonl_files_lists_all_sessions(self, fake_home: Path) -> None:
        _write_cc_session(fake_home, "-tmp-clients-acme-foo", "sid1")
        _write_cc_session(fake_home, "-tmp-other", "sid2")
        files = iter_cc_jsonl_files()
        assert len(files) == 2

    def test_iter_codex_jsonl_files_recursive(self, fake_home: Path) -> None:
        _write_codex_session(fake_home, "sidcodex1", cwd="/tmp/clients/acme/foo")
        _write_codex_session(fake_home, "sidcodex2", cwd=None)
        files = iter_codex_jsonl_files()
        assert len(files) == 2

    def test_iter_handles_missing_roots(self, tmp_path: Path, monkeypatch) -> None:
        empty_home = tmp_path / "empty"
        empty_home.mkdir()
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: empty_home))
        assert iter_cc_jsonl_files() == []
        assert iter_codex_jsonl_files() == []


# ---------------------------------------------------------------------------
# canonicalize_under_roots — symlink/path-escape guard.
# ---------------------------------------------------------------------------


class TestCanonicalize:
    def test_path_under_cc_root_is_accepted(self, fake_home: Path) -> None:
        path = _write_cc_session(fake_home, "-tmp-x", "sid")
        result = canonicalize_under_roots(path)
        assert result is not None
        assert result == path.resolve(strict=True)

    def test_path_outside_roots_is_rejected_and_alerts(
        self, fake_home: Path, tmp_path: Path
    ) -> None:
        # File lives outside both roots → should be dropped + alert emitted.
        outside = tmp_path / "elsewhere.jsonl"
        outside.write_text("{}\n")
        result = canonicalize_under_roots(outside)
        assert result is None
        op_log = operator_internal_path()
        lines = [json.loads(L) for L in op_log.read_text().splitlines() if L.strip()]
        alerts = [
            L for L in lines
            if L["kind"] == "alert"
            and L["metadata"]["reason"] == "path_outside_roots"
        ]
        assert len(alerts) == 1


# ---------------------------------------------------------------------------
# Full tick happy/edge paths via SessionRegistry.tick().
# ---------------------------------------------------------------------------


def _registry(fake_home: Path, *, is_slug_valid=_always_valid, now: float = 1_000_000.0,
              idle_timeout_s: float = 5.0) -> SessionRegistry:
    """Build a SessionRegistry whose time source is a fixed float — tests
    advance it manually via ``registry.now = lambda: <new value>``.
    """
    reg = SessionRegistry(
        is_slug_valid=is_slug_valid,
        idle_timeout_s=idle_timeout_s,
        now=lambda: now,
    )
    reg.bootstrap()
    return reg


def _set_mtime(path: Path, ts: float) -> None:
    os.utime(path, (ts, ts))


@pytest.mark.asyncio
class TestTickHappyPaths:
    async def test_cc_happy_path_attributes_to_client(self, fake_home: Path) -> None:
        path = _write_cc_session(fake_home, "-tmp-clients-acme-foo", "sid123")
        # Make the cwd resolvable on disk so decode_cc_dirname round-trips.
        (Path("/tmp/clients/acme/foo")).mkdir(parents=True, exist_ok=True)
        _set_mtime(path, 999_999.0)
        reg = _registry(fake_home, now=1_000_000.0)
        await reg.tick()

        # Wide log under clients/acme/audit/events.jsonl gets session_start.
        wide_log = Path("clients/acme/audit/events.jsonl")
        assert wide_log.is_file(), "expected per-client wide log"
        events = [json.loads(L) for L in wide_log.read_text().splitlines() if L.strip()]
        starts = [e for e in events if e["kind"] == "session_start"]
        assert len(starts) == 1
        assert starts[0]["metadata"]["session_id"] == "sid123"
        assert starts[0]["metadata"]["source"] == "cc"

        # Registry row written.
        registry_file = Path("clients/acme/audit/sessions.jsonl")
        assert registry_file.is_file()
        rows = [json.loads(L) for L in registry_file.read_text().splitlines() if L.strip()]
        assert any(r["session_id"] == "sid123" and r["client_id"] == "acme" for r in rows)

    async def test_codex_happy_path_attributes_to_client(self, fake_home: Path) -> None:
        path = _write_codex_session(
            fake_home, "sidcodex", cwd="/tmp/clients/acme/foo"
        )
        _set_mtime(path, 999_999.0)
        reg = _registry(fake_home, now=1_000_000.0)
        await reg.tick()

        wide_log = Path("clients/acme/audit/events.jsonl")
        events = [json.loads(L) for L in wide_log.read_text().splitlines() if L.strip()]
        starts = [e for e in events if e["kind"] == "session_start"]
        assert len(starts) == 1
        assert starts[0]["metadata"]["source"] == "codex"
        assert starts[0]["metadata"]["session_id"] == "sidcodex"

    async def test_operator_internal_when_no_clients_segment(
        self, fake_home: Path
    ) -> None:
        path = _write_cc_session(fake_home, "-tmp-random-path", "sidop")
        (Path("/tmp/random/path")).mkdir(parents=True, exist_ok=True)
        _set_mtime(path, 999_999.0)
        reg = _registry(fake_home, now=1_000_000.0)
        await reg.tick()

        op_log = operator_internal_path()
        events = [json.loads(L) for L in op_log.read_text().splitlines() if L.strip()]
        starts = [e for e in events if e["kind"] == "session_start"]
        assert len(starts) == 1
        # No per-client log should exist.
        assert not Path("clients").exists() or not any(
            Path("clients").rglob("events.jsonl")
        )


@pytest.mark.asyncio
class TestTickEdgeCases:
    async def test_sanity_parse_fail_retries_next_tick(self, fake_home: Path) -> None:
        cc_dir = fake_home / ".claude" / "projects" / "-tmp-clients-acme-foo"
        cc_dir.mkdir(parents=True, exist_ok=True)
        path = cc_dir / "sid-midwrite.jsonl"
        path.write_text("")  # empty — not a session yet
        _set_mtime(path, 999_999.0)

        reg = _registry(fake_home, now=1_000_000.0)
        await reg.tick()
        # No emission.
        wide_log = Path("clients/acme/audit/events.jsonl")
        assert not wide_log.exists()

        # Now write a real line and retry.
        (Path("/tmp/clients/acme/foo")).mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"type": "user"}) + "\n")
        _set_mtime(path, 999_999.5)
        await reg.tick()
        assert wide_log.is_file()
        events = [json.loads(L) for L in wide_log.read_text().splitlines() if L.strip()]
        assert any(e["kind"] == "session_start" for e in events)

    async def test_idle_timeout_emits_session_end(self, fake_home: Path) -> None:
        path = _write_cc_session(fake_home, "-tmp-clients-acme-foo", "sididle")
        (Path("/tmp/clients/acme/foo")).mkdir(parents=True, exist_ok=True)
        _set_mtime(path, 999_999.0)
        reg = _registry(fake_home, now=1_000_000.0, idle_timeout_s=5.0)
        await reg.tick()
        # 3 consecutive ticks with no growth + mtime stale = end.
        reg.now = lambda: 1_000_010.0  # 10s past mtime → exceeds 5s idle
        for _ in range(3):
            await reg.tick()

        wide_log = Path("clients/acme/audit/events.jsonl")
        events = [json.loads(L) for L in wide_log.read_text().splitlines() if L.strip()]
        ends = [e for e in events if e["kind"] == "session_end"]
        assert len(ends) == 1
        assert ends[0]["metadata"]["reason"] == "idle_timeout"

    async def test_codex_task_completed_emits_session_end(
        self, fake_home: Path
    ) -> None:
        path = _write_codex_session(
            fake_home,
            "sidcompletes",
            cwd="/tmp/clients/acme/foo",
            extra=[{"type": "task_completed"}],
        )
        _set_mtime(path, 999_999.0)
        reg = _registry(fake_home, now=1_000_000.0)
        await reg.tick()

        wide_log = Path("clients/acme/audit/events.jsonl")
        events = [json.loads(L) for L in wide_log.read_text().splitlines() if L.strip()]
        ends = [e for e in events if e["kind"] == "session_end"]
        assert len(ends) == 1
        assert ends[0]["metadata"]["reason"] == "task_completed"

    async def test_codex_task_aborted_emits_session_end(self, fake_home: Path) -> None:
        path = _write_codex_session(
            fake_home,
            "sidaborts",
            cwd="/tmp/clients/acme/foo",
            extra=[{"type": "task_aborted"}],
        )
        _set_mtime(path, 999_999.0)
        reg = _registry(fake_home, now=1_000_000.0)
        await reg.tick()
        wide_log = Path("clients/acme/audit/events.jsonl")
        events = [json.loads(L) for L in wide_log.read_text().splitlines() if L.strip()]
        ends = [e for e in events if e["kind"] == "session_end"]
        assert len(ends) == 1
        assert ends[0]["metadata"]["reason"] == "task_aborted"

    async def test_old_session_is_register_only_not_emitted(
        self, fake_home: Path
    ) -> None:
        path = _write_cc_session(fake_home, "-tmp-clients-acme-foo", "sidold")
        (Path("/tmp/clients/acme/foo")).mkdir(parents=True, exist_ok=True)
        # mtime far past the active window.
        _set_mtime(path, 100.0)
        reg = _registry(fake_home, now=1_000_000.0)
        await reg.tick()
        wide_log = Path("clients/acme/audit/events.jsonl")
        # Stale session — NO session_start emitted to wide log.
        assert not wide_log.exists()
        # But registry row IS written so IDOR guard can resolve.
        registry_file = Path("clients/acme/audit/sessions.jsonl")
        assert registry_file.is_file()
        rows = [json.loads(L) for L in registry_file.read_text().splitlines() if L.strip()]
        assert any(r["session_id"] == "sidold" for r in rows)


@pytest.mark.asyncio
class TestIntegration:
    async def test_dedup_against_pre_existing_session_start(
        self, fake_home: Path
    ) -> None:
        # Pre-write a session_start to clients/acme/audit/events.jsonl
        # (simulating a CC hook beating the tailer).
        wide_log = Path("clients/acme/audit/events.jsonl")
        wide_log.parent.mkdir(parents=True, exist_ok=True)
        wide_log.write_text(
            json.dumps({
                "kind": "session_start",
                "metadata": {"session_id": "sidcc"},
            }) + "\n"
        )
        path = _write_cc_session(fake_home, "-tmp-clients-acme-foo", "sidcc")
        (Path("/tmp/clients/acme/foo")).mkdir(parents=True, exist_ok=True)
        _set_mtime(path, 999_999.0)

        reg = _registry(fake_home, now=1_000_000.0)
        await reg.tick()

        events = [json.loads(L) for L in wide_log.read_text().splitlines() if L.strip()]
        starts = [e for e in events if e["kind"] == "session_start"]
        # Tailer didn't double-write.
        assert len(starts) == 1

        # Registry row marks hook_emitted=true.
        registry_file = Path("clients/acme/audit/sessions.jsonl")
        rows = [json.loads(L) for L in registry_file.read_text().splitlines() if L.strip()]
        match = [r for r in rows if r.get("session_id") == "sidcc"]
        assert match and match[0]["hook_emitted"] is True

    async def test_restart_safety_rebuild_state(self, fake_home: Path) -> None:
        registry_file = Path("clients/acme/audit/sessions.jsonl")
        registry_file.parent.mkdir(parents=True, exist_ok=True)
        registry_file.write_text(
            json.dumps({
                "session_id": "sidresume",
                "client_id": "acme",
                "source": "cc",
                "file_path": "/abs/x.jsonl",
                "started_at": "2026-05-18T00:00:00Z",
                "hook_emitted": False,
            }) + "\n"
        )
        # The CC dir exists for this session — but bootstrap should NOT
        # re-emit session_start because the registry already lists it.
        path = _write_cc_session(fake_home, "-tmp-clients-acme-foo", "sidresume")
        (Path("/tmp/clients/acme/foo")).mkdir(parents=True, exist_ok=True)
        _set_mtime(path, 999_999.0)

        reg = _registry(fake_home, now=1_000_000.0)
        # After bootstrap the row is already in memory; tick won't re-emit.
        assert "sidresume" in reg.rows
        await reg.tick()
        wide_log = Path("clients/acme/audit/events.jsonl")
        # No new session_start since we already knew about it.
        if wide_log.exists():
            events = [json.loads(L) for L in wide_log.read_text().splitlines() if L.strip()]
            starts = [e for e in events if e["kind"] == "session_start"]
            assert len(starts) == 0

    async def test_cross_tenant_r7_sub_case_i_unknown_slug(
        self, fake_home: Path
    ) -> None:
        path = _write_cc_session(fake_home, "-tmp-clients-ghost-foo", "sidghost")
        (Path("/tmp/clients/ghost/foo")).mkdir(parents=True, exist_ok=True)
        _set_mtime(path, 999_999.0)
        reg = _registry(fake_home, is_slug_valid=_always_invalid, now=1_000_000.0)
        await reg.tick()

        # No clients/ghost/audit/events.jsonl exists — went operator-internal.
        assert not Path("clients/ghost/audit/events.jsonl").exists()
        op_log = operator_internal_path()
        events = [json.loads(L) for L in op_log.read_text().splitlines() if L.strip()]
        # Both the conflict moment AND the session_start should be there.
        assert any(
            e["kind"] == "moment"
            and e["metadata"]["moment_kind"] == "attribution_conflict"
            and e["metadata"]["reason"] == "slug_unknown"
            for e in events
        )
        assert any(e["kind"] == "session_start" for e in events)


@pytest.mark.asyncio
class TestErrorPath:
    async def test_permission_error_during_tick_emits_alert(
        self, fake_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _write_cc_session(fake_home, "-tmp-clients-acme-foo", "sidpe")
        (Path("/tmp/clients/acme/foo")).mkdir(parents=True, exist_ok=True)
        reg = _registry(fake_home, now=1_000_000.0)

        # Inject a synthetic crash inside _handle_cc_file.
        async def boom(path: Path, *, now: float) -> None:
            raise PermissionError("simulated")

        monkeypatch.setattr(reg, "_handle_cc_file", boom)
        await reg.tick()
        op_log = operator_internal_path()
        events = [json.loads(L) for L in op_log.read_text().splitlines() if L.strip()]
        alerts = [
            e for e in events
            if e["kind"] == "alert"
            and e["metadata"]["reason"] == "tailer_tick_error"
        ]
        assert len(alerts) >= 1


# ---------------------------------------------------------------------------
# Poll-interval clamping.
# ---------------------------------------------------------------------------


class TestPollInterval:
    def test_default_when_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("GOFREDDY_TAILER_INTERVAL_S", raising=False)
        assert _resolve_poll_interval() == 1.5

    def test_clamp_to_min(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GOFREDDY_TAILER_INTERVAL_S", "0.01")
        assert _resolve_poll_interval() == 0.25

    def test_clamp_to_max(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GOFREDDY_TAILER_INTERVAL_S", "9999")
        assert _resolve_poll_interval() == 60.0

    def test_invalid_falls_back_to_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("GOFREDDY_TAILER_INTERVAL_S", "not-a-float")
        assert _resolve_poll_interval() == 1.5


# ---------------------------------------------------------------------------
# Lifespan integration smoke — `run_tailer` cancels cleanly.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestLifespanIntegration:
    async def test_run_tailer_cancels_cleanly(self, fake_home: Path) -> None:
        # No sessions on disk; tailer should idle then cancel without leaking.
        task = asyncio.create_task(
            run_tailer(
                is_slug_valid=_always_valid,
                pool_is_ready=lambda: True,
                poll_interval_s=0.01,
            )
        )
        await asyncio.sleep(0.05)  # let it tick a few times
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    async def test_run_tailer_skips_tick_when_pool_not_ready(
        self, fake_home: Path
    ) -> None:
        # If the pool isn't ready yet, tick() is never called — tailer
        # just sleeps. Verified by injecting a registry whose tick()
        # would raise if invoked.
        from src.portal.transcript_tailer import SessionRegistry

        ticks_seen = 0

        async def fake_tick() -> None:
            nonlocal ticks_seen
            ticks_seen += 1

        reg = SessionRegistry(is_slug_valid=_always_valid)
        reg.tick = fake_tick  # type: ignore[assignment]

        task = asyncio.create_task(
            run_tailer(
                is_slug_valid=_always_valid,
                pool_is_ready=lambda: False,
                poll_interval_s=0.01,
                registry=reg,
            )
        )
        await asyncio.sleep(0.05)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert ticks_seen == 0
