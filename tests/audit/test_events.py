"""Tests for src/audit/events + the autoresearch.events.log_event path= extension."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from autoresearch.events import EVENTS_LOG, log_event
from src.audit.events import log_global, log_to_audit


def test_log_event_with_path_writes_to_custom_destination(tmp_path: Path):
    target = tmp_path / "custom" / "events.jsonl"
    log_event("test_kind", path=target, foo="bar", n=42)
    assert target.is_file()
    rows = target.read_text(encoding="utf-8").strip().splitlines()
    assert len(rows) == 1
    record = json.loads(rows[0])
    assert record["kind"] == "test_kind"
    assert record["foo"] == "bar"
    assert record["n"] == 42
    assert "timestamp" in record


def test_log_event_without_path_uses_default(monkeypatch, tmp_path: Path):
    """Default destination is autoresearch.events.EVENTS_LOG; redirect via
    monkeypatch so the test doesn't write to the real user dir."""
    fake_default = tmp_path / "default.jsonl"
    monkeypatch.setattr("autoresearch.events.EVENTS_LOG", fake_default)
    log_event("global_kind", marker="default-path")
    assert fake_default.is_file()
    record = json.loads(fake_default.read_text(encoding="utf-8").strip())
    assert record["kind"] == "global_kind"
    assert record["marker"] == "default-path"


def test_log_to_audit_writes_under_audit_dir(tmp_path: Path):
    audit_dir = tmp_path / "audit-001"
    audit_dir.mkdir()
    log_to_audit(audit_dir, "stage_start", stage="stage_1b")
    assert (audit_dir / "events.jsonl").is_file()
    record = json.loads((audit_dir / "events.jsonl").read_text(encoding="utf-8").strip())
    assert record["kind"] == "stage_start"
    assert record["stage"] == "stage_1b"


def test_log_global_writes_to_default(monkeypatch, tmp_path: Path):
    fake_default = tmp_path / "global.jsonl"
    monkeypatch.setattr("autoresearch.events.EVENTS_LOG", fake_default)
    log_global("audit_start", audit_id="a-001")
    assert fake_default.is_file()
    record = json.loads(fake_default.read_text(encoding="utf-8").strip())
    assert record["kind"] == "audit_start"
    assert record["audit_id"] == "a-001"


def test_log_to_audit_appends_multiple_events(tmp_path: Path):
    audit_dir = tmp_path
    log_to_audit(audit_dir, "k1", n=1)
    log_to_audit(audit_dir, "k2", n=2)
    log_to_audit(audit_dir, "k3", n=3)
    rows = (audit_dir / "events.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(rows) == 3
    assert [json.loads(r)["kind"] for r in rows] == ["k1", "k2", "k3"]


# ---------------------------------------------------------------------------
# Wide-log mirror (portal visibility — added 2026-05-15 for portal v1.0)
#
# When `audit_dir` is shaped `clients/<slug>/audit/<audit_id>/`, audit events
# also land in `clients/<slug>/audit/events.jsonl` (the wide log the portal
# SSE tails). Without this mirror, audit-pipeline events would be visible
# only to operator post-mortem tooling, not to portal subscribers.
# ---------------------------------------------------------------------------


def _read_jsonl(p: Path) -> list[dict]:
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


def test_log_to_audit_mirrors_to_wide_log_when_under_clients_tree(tmp_path: Path, monkeypatch):
    """Per-client audit dir → event mirrors to clients/<slug>/audit/events.jsonl."""
    monkeypatch.chdir(tmp_path)
    audit_dir = tmp_path / "clients" / "klinika-melitus" / "audit" / "audit-001"
    audit_dir.mkdir(parents=True)

    log_to_audit(audit_dir, "stage_start", stage="stage_1b")

    # Source-of-truth write
    per_audit = _read_jsonl(audit_dir / "events.jsonl")
    assert len(per_audit) == 1
    assert per_audit[0]["kind"] == "stage_start"

    # Wide-log mirror
    wide = _read_jsonl(tmp_path / "clients" / "klinika-melitus" / "audit" / "events.jsonl")
    assert len(wide) == 1
    assert wide[0]["kind"] == "stage_start"
    assert wide[0]["stage"] == "stage_1b"
    # Mirror enriches with slug + audit_id so the portal can disambiguate
    assert wide[0]["client_id"] == "klinika-melitus"
    assert wide[0]["audit_id"] == "audit-001"


def test_log_to_audit_does_not_mirror_for_paths_outside_clients_tree(tmp_path: Path, monkeypatch):
    """Test fixture / ad-hoc audit dirs → no wide-log mirror."""
    monkeypatch.chdir(tmp_path)
    audit_dir = tmp_path / "scratch" / "audit-001"
    audit_dir.mkdir(parents=True)

    log_to_audit(audit_dir, "stage_start", stage="stage_1b")

    assert _read_jsonl(audit_dir / "events.jsonl") != []
    # No clients/ tree at all — no mirror
    assert not (tmp_path / "clients").exists()


def test_log_to_audit_skips_mirror_when_audit_dir_is_the_wide_log(tmp_path: Path, monkeypatch):
    """If a caller passes `clients/<slug>/audit/` itself (no audit_id segment),
    don't double-write — that path IS the wide log."""
    monkeypatch.chdir(tmp_path)
    wide_dir = tmp_path / "clients" / "klinika-melitus" / "audit"
    wide_dir.mkdir(parents=True)

    log_to_audit(wide_dir, "audit_start", note="missing audit_id segment")

    rows = _read_jsonl(wide_dir / "events.jsonl")
    # Exactly one line, not duplicated by a mirror loop
    assert len(rows) == 1
    assert rows[0]["kind"] == "audit_start"
    assert "client_id" not in rows[0]  # mirror didn't run, so no enrichment


def test_log_to_audit_mirror_failure_does_not_break_per_audit_write(
    tmp_path: Path, monkeypatch
):
    """If the wide-log write blows up, the per-audit write still succeeds.
    The audit pipeline must be resilient to portal-visibility regressions."""
    audit_dir = tmp_path / "clients" / "klinika-melitus" / "audit" / "audit-001"
    audit_dir.mkdir(parents=True)

    # Force the wide-log helper to return a path under a root we can't write
    # to (root-owned, no perms). The source-of-truth write to audit_dir stays
    # under tmp_path and must still succeed.
    from src.audit import events as audit_events_mod

    def _exploding(_audit_dir: Path):
        return ("klinika-melitus", Path("/nonexistent-root/forbidden/events.jsonl"))

    monkeypatch.setattr(audit_events_mod, "_wide_log_for", _exploding)

    # Should not raise — mirror failure is swallowed.
    log_to_audit(audit_dir, "stage_start", stage="stage_1b")

    per_audit = _read_jsonl(audit_dir / "events.jsonl")
    assert len(per_audit) == 1
    assert per_audit[0]["kind"] == "stage_start"


def test_log_to_audit_mirror_resolves_relative_to_audit_dir_not_cwd(
    tmp_path: Path, monkeypatch
):
    """Wide-log path must derive from audit_dir's root, NOT from cwd.

    Regression — the audit pipeline can be launched from any working
    directory; the mirror must not silently write to cwd-relative
    `clients/...` and leak across tenants.
    """
    # Deliberately cd somewhere ELSE than the tmp_path root so a cwd-
    # dependent mirror would write to the wrong place.
    elsewhere = tmp_path / "cwd-elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    audit_dir = tmp_path / "clients" / "klinika-melitus" / "audit" / "audit-001"
    audit_dir.mkdir(parents=True)

    log_to_audit(audit_dir, "stage_start", stage="stage_1b")

    # Wide log lands under the audit_dir's root, NOT under cwd
    expected_wide = tmp_path / "clients" / "klinika-melitus" / "audit" / "events.jsonl"
    assert expected_wide.exists()
    # And NOT under the wrong root
    cwd_wide = elsewhere / "clients" / "klinika-melitus" / "audit" / "events.jsonl"
    assert not cwd_wide.exists()


def test_slug_from_audit_dir_handles_absolute_paths(tmp_path: Path):
    """Absolute paths to clients/<slug>/audit/<id>/ also extract the slug
    (operators commonly cd into a worktree and pass absolute audit dirs)."""
    from src.audit.events import _slug_from_audit_dir

    rel = Path("clients/klinika-melitus/audit/audit-001")
    assert _slug_from_audit_dir(rel) == "klinika-melitus"

    abs_path = Path("/Users/foo/repo/clients/dwf-poland/audit/abc-123")
    assert _slug_from_audit_dir(abs_path) == "dwf-poland"

    # Nested under a worktree
    nested = Path("/repo/.worktrees/branch-name/clients/acme/audit/run-9")
    assert _slug_from_audit_dir(nested) == "acme"

    # Negative cases
    assert _slug_from_audit_dir(Path("scratch/audit-001")) is None
    assert _slug_from_audit_dir(Path("clients/acme/audit")) is None  # no audit_id
    assert _slug_from_audit_dir(Path("clients/acme")) is None         # no audit segment
