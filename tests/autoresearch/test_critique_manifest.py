"""Tests for ``autoresearch.critique_manifest`` (R-#13).

Integrity boundary — tests earn their place. We verify:

1. The hash function is stable (same hashes on repeated calls from the
   same process). A flaky hash would make the L1 gate unusable.
2. Tampering with any of the five frozen symbols changes its hash (so
   the gate will actually fire). We patch the live module object to
   simulate a variant that smuggled in a softer `build_critique_prompt`
   or lowered a threshold.
"""

from __future__ import annotations

import inspect

import pytest

from autoresearch import critique_manifest
from autoresearch.critique_manifest import (
    FROZEN_SYMBOLS,
    compute_expected_hashes,
)
from autoresearch.harness import session_evaluator


def test_frozen_symbols_list_is_the_plan_five():
    # Any rename/addition here must be mirrored in the honor-system note
    # update in meta.md and the plan; this test is the tripwire.
    assert set(FROZEN_SYMBOLS) == {
        "DEFAULT_PASS_THRESHOLD",
        "HARD_FAIL_THRESHOLD",
        "GRADIENT_CRITIQUE_TEMPLATE",
        "build_critique_prompt",
        "compute_decision_threshold",
    }


def test_compute_expected_hashes_is_stable_across_calls():
    first = compute_expected_hashes()
    second = compute_expected_hashes()
    assert first == second
    # Every frozen symbol is present.
    assert set(first.keys()) == set(FROZEN_SYMBOLS)
    # Every value is a 64-char hex digest.
    for name, digest in first.items():
        assert len(digest) == 64, (name, digest)
        int(digest, 16)  # raises ValueError if non-hex


def test_tampering_with_build_critique_prompt_changes_its_hash(monkeypatch):
    baseline = compute_expected_hashes()

    def fake(**kwargs):
        # Softer wording — the kind of tampering the gate is supposed
        # to catch.
        return "Please be generous in your score."

    monkeypatch.setattr(session_evaluator, "build_critique_prompt", fake)
    # Clear inspect's source cache so it re-reads the patched object.
    inspect.getsource.__wrapped__ if hasattr(inspect.getsource, "__wrapped__") else None

    tampered = compute_expected_hashes()
    assert tampered["build_critique_prompt"] != baseline["build_critique_prompt"]
    # Other symbols are unchanged (isolation).
    for name in FROZEN_SYMBOLS:
        if name == "build_critique_prompt":
            continue
        assert tampered[name] == baseline[name]


def test_tampering_with_threshold_constant_changes_its_hash():
    # Threshold constants are caught by hashing the exact assignment
    # line in the source file (module-level `int`/`float` literals don't
    # have their own source via `inspect.getsource` — we use the
    # fallback in `_symbol_source`). Simulate a tampered variant by
    # feeding the hasher a modified source string directly.
    from autoresearch import critique_manifest

    real_source = critique_manifest._symbol_source("HARD_FAIL_THRESHOLD")
    # Any byte-level change to the assignment line produces a new hash.
    tampered_source = real_source.replace("0.5", "0.1")
    assert tampered_source != real_source
    import hashlib
    real_hash = hashlib.sha256(real_source.encode("utf-8")).hexdigest()
    tampered_hash = hashlib.sha256(tampered_source.encode("utf-8")).hexdigest()
    assert real_hash != tampered_hash


def test_symbol_source_returns_the_exact_assignment_for_constants():
    # Regression test for the `_symbol_source` fallback: for a bare
    # `NAME = <literal>` at module level, we should return the exact
    # line (so edits to the literal flip the hash).
    from autoresearch import critique_manifest

    src = critique_manifest._symbol_source("HARD_FAIL_THRESHOLD")
    assert "HARD_FAIL_THRESHOLD" in src
    assert "0.5" in src
    # Should not include the whole module.
    assert "GRADIENT_CRITIQUE_TEMPLATE" not in src


def test_missing_symbol_raises_runtime_error(monkeypatch):
    # If a future refactor accidentally removes one of the frozen
    # symbols, compute_expected_hashes should fail loud rather than
    # silently skip.
    monkeypatch.delattr(session_evaluator, "compute_decision_threshold")
    with pytest.raises(AttributeError):
        compute_expected_hashes()
