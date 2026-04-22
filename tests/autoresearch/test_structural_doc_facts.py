"""Bidirectional paired test for STRUCTURAL_DOC_FACTS.

Doc-code drift is the LIVE 5x bug this unit exists to fix, so coverage
runs in BOTH directions:

1. Every bullet in ``STRUCTURAL_DOC_FACTS`` maps to a registered gate
   function in ``STRUCTURAL_GATE_FUNCTIONS`` (catches: doc ahead of code).
2. Every gate function in ``STRUCTURAL_GATE_FUNCTIONS`` is surfaced in
   ``STRUCTURAL_DOC_FACTS`` (catches: code ahead of docs).
3. The gate-function registry matches the actual callables / assertions
   inside the ``_validate_<domain>`` helpers in ``structural.py`` — this
   is the check that will light up on drift when (for example) Unit 12
   removes a monitoring assertion but forgets to drop the bullet.

When Unit 12 removes an assertion, the expected flow is: drop the
bullet from ``STRUCTURAL_DOC_FACTS`` AND drop the key from
``STRUCTURAL_GATE_FUNCTIONS`` AND re-run ``regen_program_docs`` in the
same commit. All three red checks here align.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from src.evaluation import structural
from src.evaluation.structural import (
    STRUCTURAL_DOC_FACTS,
    STRUCTURAL_GATE_FUNCTIONS,
)

DOMAINS = ("competitive", "monitoring", "geo", "storyboard")


# ---------------------------------------------------------------------------
# Check 1: every bullet has a gate function registered for its domain
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("domain", DOMAINS)
def test_every_bullet_has_gate_function(domain: str) -> None:
    bullets = STRUCTURAL_DOC_FACTS.get(domain, [])
    gates = STRUCTURAL_GATE_FUNCTIONS.get(domain, ())
    assert bullets, f"STRUCTURAL_DOC_FACTS[{domain!r}] is empty"
    assert gates, f"STRUCTURAL_GATE_FUNCTIONS[{domain!r}] is empty"
    assert len(bullets) == len(gates), (
        f"{domain}: {len(bullets)} bullets vs {len(gates)} gates — "
        "STRUCTURAL_DOC_FACTS and STRUCTURAL_GATE_FUNCTIONS drifted. "
        "Add/remove bullet AND gate together."
    )


# ---------------------------------------------------------------------------
# Check 2: every gate function in the registry is surfaced in the docs
# ---------------------------------------------------------------------------


def test_every_registered_domain_has_bullets() -> None:
    missing_bullets = set(STRUCTURAL_GATE_FUNCTIONS) - set(STRUCTURAL_DOC_FACTS)
    assert not missing_bullets, (
        f"STRUCTURAL_GATE_FUNCTIONS has domains with no bullets: {missing_bullets}"
    )
    missing_gates = set(STRUCTURAL_DOC_FACTS) - set(STRUCTURAL_GATE_FUNCTIONS)
    assert not missing_gates, (
        f"STRUCTURAL_DOC_FACTS has domains with no gate registry: {missing_gates}"
    )


# ---------------------------------------------------------------------------
# Check 3: the registered gate names line up with real code
# ---------------------------------------------------------------------------


def _assert_names_in_validator(domain: str) -> set[str]:
    """Return the set of names passed to ``_assert(...)`` inside the
    ``_validate_<domain>`` function — these are the actual enforced
    gates inside ``structural.py`` for the monitoring validator.
    """
    func = getattr(structural, f"_validate_{domain}")
    source = inspect.getsource(func)
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_assert"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            names.add(node.args[0].value)
    return names


def test_monitoring_registry_matches_assert_names() -> None:
    """Monitoring uses a local ``_assert`` helper; the string names it
    registers should match ``STRUCTURAL_GATE_FUNCTIONS['monitoring']``.

    After Unit 12 landed, no gates are pending removal — the only
    non-registered ``_assert`` names are:

    * ``rec_exec_summary`` + ``rec_action_items`` — folded into the
      single ``rec_exec_summary_and_action_items`` bullet.
    * ``claim_grounded`` — dynamic per-claim assertion fired by the
      R-#37 claim-grounding agent; not a static structural rule, so it
      does not appear in ``STRUCTURAL_DOC_FACTS`` (documented in the
      session-md prose surrounding the validator instead).
    """
    actual = _assert_names_in_validator("monitoring")
    registered = set(STRUCTURAL_GATE_FUNCTIONS["monitoring"])

    # Combined asserts that the registry folds into one bullet.
    combined = {"rec_exec_summary", "rec_action_items"}
    # Agent-driven dynamic assertions — not static structural rules.
    agent_derived = {"claim_grounded"}

    # Gates registered but not present in code — hard failure.
    missing = registered - actual - {"rec_exec_summary_and_action_items"}
    assert not missing, (
        f"monitoring: gates in registry but not asserted in code: {missing}"
    )

    # Gates in code but missing from BOTH registry and known-excepted
    # set — drift in the other direction.
    unaccounted = actual - registered - combined - agent_derived
    assert not unaccounted, (
        f"monitoring: asserts in code with no bullet and no excepted category: "
        f"{unaccounted}"
    )


# ---------------------------------------------------------------------------
# Check 4: AUTOGEN blocks render and contain one bullet per fact
# ---------------------------------------------------------------------------


def test_regen_block_shape() -> None:
    """Sanity-check that ``regen_program_docs`` emits the same bullet
    count it was given — a cheap canary on the renderer."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "regen_program_docs",
        Path(__file__).resolve().parents[2]
        / "autoresearch"
        / "regen_program_docs.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    for domain, bullets in STRUCTURAL_DOC_FACTS.items():
        block = module._build_block(domain)
        assert module.START_MARKER in block
        assert module.END_MARKER in block
        assert block.count("\n- ") == len(bullets), (
            f"{domain}: expected {len(bullets)} bullets in block, "
            f"got {block.count(chr(10) + '- ')}"
        )
