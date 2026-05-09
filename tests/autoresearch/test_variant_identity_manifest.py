"""Regression tests for Finding #114: variant_manifest.json corruption.

Variant clones used to inherit the parent's ``variant_manifest.json`` via
copytree without refreshing it, so every promoted variant carried v001's
identity (variant_id="v001", lane="geo", parent=null) regardless of its
actual provenance. The fix stamps a fresh manifest at clone time via the
``_write_variant_identity_manifest`` helper.
"""
from __future__ import annotations

import json
from pathlib import Path

import evolve


def test_writes_correct_identity(tmp_path: Path) -> None:
    """Helper writes variant_id, lane, parent matching the args."""
    variant_dir = tmp_path / "v042"
    variant_dir.mkdir()
    evolve._write_variant_identity_manifest(
        variant_dir, "v042", "geo", "v007",
    )
    payload = json.loads((variant_dir / "variant_manifest.json").read_text())
    assert payload["variant_id"] == "v042"
    assert payload["lane"] == "geo"
    assert payload["parent"] == "v007"
    assert "created_at" in payload
    # Sanity: timestamp parses as ISO-8601.
    from datetime import datetime
    datetime.fromisoformat(payload["created_at"])


def test_overwrites_inherited_stale_manifest(tmp_path: Path) -> None:
    """Helper must replace, not merge: stale parent identity is wiped."""
    variant_dir = tmp_path / "v176"
    variant_dir.mkdir()
    # Simulate the corrupted inheritance pattern: parent's v001 manifest
    # got copytree'd into the child's directory.
    stale = {
        "variant_id": "v001",
        "lane": "geo",
        "parent": None,
        "search_summary": {"composite": 0.0},
    }
    (variant_dir / "variant_manifest.json").write_text(json.dumps(stale))

    evolve._write_variant_identity_manifest(
        variant_dir, "v176", "competitive", "v074",
    )

    payload = json.loads((variant_dir / "variant_manifest.json").read_text())
    assert payload["variant_id"] == "v176"
    assert payload["lane"] == "competitive"
    assert payload["parent"] == "v074"
    # Stale fields must be gone — we overwrite, not merge.
    assert "search_summary" not in payload


def test_first_of_lane_has_no_parent(tmp_path: Path) -> None:
    """parent=None is preserved (first-of-lane / cold-start case)."""
    variant_dir = tmp_path / "v001"
    variant_dir.mkdir()
    evolve._write_variant_identity_manifest(
        variant_dir, "v001", "geo", None,
    )
    payload = json.loads((variant_dir / "variant_manifest.json").read_text())
    assert payload["parent"] is None
