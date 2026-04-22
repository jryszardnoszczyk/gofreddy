"""Tests for the critique-manifest gate in ``evaluate_variant.layer1_validate``
(R-#13 / R-#24).

Integrity boundary. We're not testing the other Layer 1 checks
(``py_compile`` / ``bash -n`` / session programs) here — those are
orthogonal and already covered elsewhere. We test *only* the manifest
gate, and we isolate it by building a minimal fake variant directory
that would otherwise pass L1.

The tests drive ``_check_critique_manifest`` directly because that's
the unit that encodes the gate. ``layer1_validate`` just calls it
first; once the gate is satisfied, the rest of L1 is the same code
that ran before R-#13.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import evaluate_variant
from autoresearch.critique_manifest import compute_expected_hashes


def _write_manifest(variant_dir: Path, content: dict) -> None:
    (variant_dir / "critique_manifest.json").write_text(
        json.dumps(content, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def test_missing_manifest_fails(tmp_path, capsys):
    assert evaluate_variant._check_critique_manifest(tmp_path) is False
    err = capsys.readouterr().err
    assert "L1 FAIL" in err
    assert "critique_manifest.json missing" in err


def test_correct_manifest_passes(tmp_path):
    _write_manifest(tmp_path, compute_expected_hashes())
    assert evaluate_variant._check_critique_manifest(tmp_path) is True


def test_tampered_manifest_fails(tmp_path, capsys):
    bad = compute_expected_hashes()
    # Flip one bit in the build_critique_prompt hash — simulates a
    # variant that tampered with the prompt and updated its manifest
    # to match the tampered source. The subprocess introspection
    # recomputes hashes from the untampered canonical module, so the
    # comparison still mismatches.
    bad["build_critique_prompt"] = "0" * 64
    _write_manifest(tmp_path, bad)

    assert evaluate_variant._check_critique_manifest(tmp_path) is False
    err = capsys.readouterr().err
    assert "L1 FAIL" in err
    assert "build_critique_prompt" in err
    assert "hash mismatch" in err


def test_grace_manifest_bypasses_check(tmp_path):
    # Pre-R-#13 variants carry a grace manifest written by
    # rebuild_manifests.py. L1 must accept them even if the recorded
    # hashes drift from today's canonical hashes.
    fake = {
        "grace": True,
        "build_critique_prompt": "0" * 64,  # intentionally wrong
        "GRADIENT_CRITIQUE_TEMPLATE": "0" * 64,
        "HARD_FAIL_THRESHOLD": "0" * 64,
        "DEFAULT_PASS_THRESHOLD": "0" * 64,
        "compute_decision_threshold": "0" * 64,
    }
    _write_manifest(tmp_path, fake)
    assert evaluate_variant._check_critique_manifest(tmp_path) is True


def test_malformed_json_fails(tmp_path, capsys):
    (tmp_path / "critique_manifest.json").write_text(
        "not-json{", encoding="utf-8"
    )
    assert evaluate_variant._check_critique_manifest(tmp_path) is False
    err = capsys.readouterr().err
    assert "L1 FAIL" in err
    assert "unreadable" in err


def test_non_object_manifest_fails(tmp_path, capsys):
    (tmp_path / "critique_manifest.json").write_text("[]", encoding="utf-8")
    assert evaluate_variant._check_critique_manifest(tmp_path) is False
    err = capsys.readouterr().err
    assert "must be a JSON object" in err


def test_key_mismatch_fails(tmp_path, capsys):
    truncated = compute_expected_hashes()
    truncated.pop("build_critique_prompt")
    truncated["rogue_symbol"] = "0" * 64
    _write_manifest(tmp_path, truncated)

    assert evaluate_variant._check_critique_manifest(tmp_path) is False
    err = capsys.readouterr().err
    assert "key mismatch" in err
    assert "build_critique_prompt" in err  # in the missing list
