"""Holdout loader rejects `is_redacted_example: true` (SCHEMA.md sentinel).

The repo-level conftest stubs autoresearch's `load_json` to return `{}`, so
we exercise the sentinel at the `_reject_redacted_example` seam and wire-
check `_load_holdout_manifest` by monkey-patching `_load_manifest_from_path`
to return a real payload.
"""
import json
from pathlib import Path

import pytest

import autoresearch.evaluate_variant as ev


def test_reject_raises_when_sentinel_true():
    with pytest.raises(RuntimeError, match="is_redacted_example"):
        ev._reject_redacted_example({"is_redacted_example": True}, source="t")


def test_reject_allows_false_and_absent():
    ev._reject_redacted_example({"is_redacted_example": False}, source="t")
    ev._reject_redacted_example({"other": "data"}, source="t")
    ev._reject_redacted_example({}, source="t")


def test_load_holdout_manifest_trips_sentinel(monkeypatch):
    def _fake_load(path):
        return {
            "is_redacted_example": True,
            "suite_id": "holdout-v1",
            "version": "1.0",
            "domains": {},
        }
    monkeypatch.setattr(ev, "_load_manifest_from_path", _fake_load)
    with pytest.raises(RuntimeError, match="is_redacted_example"):
        ev._load_holdout_manifest({"EVOLUTION_HOLDOUT_MANIFEST": "/path/to/example"})


def test_load_holdout_manifest_passes_past_guard_when_sentinel_absent(monkeypatch):
    """No sentinel → execution proceeds past _reject_redacted_example.

    Downstream validators (normalize / project) are exercised by their own
    tests; here we only need to prove the guard doesn't fire when sentinel
    is absent.
    """
    guard_calls = []
    monkeypatch.setattr(
        ev, "_reject_redacted_example",
        lambda payload, source: guard_calls.append((payload.get("is_redacted_example"), source)),
    )
    monkeypatch.setattr(
        ev, "_load_manifest_from_path",
        lambda p: {"suite_id": "holdout-v1", "version": "1.0", "domains": {}},
    )
    # Further downstream failure is irrelevant — we prove the guard was called
    # with the non-sentinel payload and did not raise.
    try:
        ev._load_holdout_manifest({"EVOLUTION_HOLDOUT_MANIFEST": "/path/real"})
    except RuntimeError:
        pass  # downstream normalization errors are unrelated to the sentinel
    assert len(guard_calls) == 1
    sentinel_value, _ = guard_calls[0]
    assert sentinel_value is None


def test_shipped_example_file_carries_sentinel():
    """The committed holdout-v1.json.example must have the sentinel set."""
    repo_root = Path(__file__).resolve().parents[2]
    example = repo_root / "autoresearch" / "eval_suites" / "holdout-v1.json.example"
    assert example.exists(), "holdout-v1.json.example must exist in the repo"
    payload = json.loads(example.read_text())
    assert payload.get("is_redacted_example") is True, (
        "the shipped example file must set is_redacted_example=true so a "
        "loader accidentally pointed at it fails-loud"
    )
