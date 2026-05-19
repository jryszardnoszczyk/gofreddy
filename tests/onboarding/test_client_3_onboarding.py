"""U19 — architectural CI diff assertion for config-only onboarding.

Per Success Criteria: "Per-client onboarding works config-only for
client #3". The test validates the D11 + D20 architectural invariants:
a new archetype + new client onboards via YAML edits ONLY — no code
changes to lane internals, rubrics, or shared infra.

Per Pass-5 right-sized scope: this test is the diff assertion only.
The full end-to-end pipeline run against the stub was deleted per
the U19 plan — synthetic-data-through-synthetic-code validates
nothing real. The architectural invariant is structural; this test
makes it falsifiable.

The `_stub_b2b_tech` client demonstrates the invariant by existing:
it shipped in U2 with `archetype: b2b_tech` + `archetype_stub_allowed:
true` and is loaded by the ClientConfig loader without any code
under `src/{clients,voice,briefs,compliance,review,ads,generation}/`
needing to change for THAT specific load. The test asserts this is
still true.
"""
from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from src.clients.config import (
    Archetype,
    ArticleBriefConsumptionMode,
    ClientConfig,
)
from src.clients.loader import load_client_config


_REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Happy path: stub client loads as config-only
# ---------------------------------------------------------------------------


def test_stub_b2b_tech_loads_via_config_loader() -> None:
    """`ClientConfig.load("_stub_b2b_tech")` returns a frozen model
    without raising. This is the foundational D11 invariant — adding a
    new archetype's example client is a YAML-only operation."""
    config = load_client_config("_stub_b2b_tech")
    assert isinstance(config, ClientConfig)
    assert config.slug == "_stub_b2b_tech"
    assert config.archetype == "b2b_tech"
    assert config.archetype_stub_allowed is True


def test_stub_b2b_tech_is_frozen() -> None:
    """ClientConfig is frozen — mutation must raise."""
    config = load_client_config("_stub_b2b_tech")
    with pytest.raises(Exception):  # FrozenInstanceError / ValidationError
        config.slug = "mutated"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Architectural surface: _stub_b2b_tech depends ONLY on tracked YAML
# ---------------------------------------------------------------------------


# Files that the architectural invariant FORBIDS modifying when
# onboarding a new client of an EXISTING archetype. (Adding a brand-
# new archetype requires a 1-line edit to the Archetype Literal in
# src/clients/config.py + 1 line in src/evaluation/models.py + an
# entry in archetype-defaults runbook — that's tracked separately.)
_ARCHITECTURAL_SURFACE = (
    # Lane substrate
    "autoresearch/lane_registry.py",
    "autoresearch/archive/v007-curated/workflows/__init__.py",
    # Shared primitives
    "src/clients/loader.py",
    "src/voice/persona.py",
    "src/briefs/schema.py",
    "src/briefs/emitter.py",
    "src/briefs/reader.py",
    "src/compliance/schema.py",
    "src/compliance/judge.py",
    "src/review/service.py",
    "src/ads/signal_aggregator/aggregator.py",
    "src/ads/signal_aggregator/merger.py",
    "src/ads/compliance/anti_patterns.py",
    "src/generation/image_composer.py",
    "src/site_engine/sanitizer.py",
    "src/evaluation/vision_judge.py",
    "src/verification/citation_verifier.py",
)


def test_stub_b2b_tech_has_yaml_only_footprint() -> None:
    """The _stub_b2b_tech archetype's footprint should be a YAML file
    + (optionally) eval suite fixtures + (optionally) a reviewer-assist
    checklist. NOT any of the architectural surface files above.

    This test is a structural assertion — it doesn't run a git diff
    (which depends on a baseline commit unavailable in arbitrary CI
    contexts), but instead asserts that the stub's `clients/_stub_b2b_tech/`
    directory is the only client-specific surface.
    """
    stub_dir = _REPO_ROOT / "clients" / "_stub_b2b_tech"
    assert stub_dir.is_dir(), (
        f"_stub_b2b_tech client directory missing at {stub_dir}; "
        f"D11 archetype-coverage assertion would fail."
    )
    yaml_path = stub_dir / "client.yaml"
    assert yaml_path.is_file(), (
        f"_stub_b2b_tech/client.yaml missing; YAML is the architectural "
        f"contract surface."
    )

    # The architectural surface files must NOT mention _stub_b2b_tech
    # by name (the stub must be discovered via the generic loader,
    # not hardcoded in lane internals).
    for surface_path in _ARCHITECTURAL_SURFACE:
        target = _REPO_ROOT / surface_path
        if not target.is_file():
            # Surface file may not exist at all yet (Compose-time list
            # includes future units' files); skip.
            continue
        text = target.read_text(encoding="utf-8", errors="replace")
        assert "_stub_b2b_tech" not in text, (
            f"{surface_path} mentions _stub_b2b_tech by name; the "
            f"architectural invariant forbids client-specific code in "
            f"lane internals. New clients onboard via YAML only."
        )


def test_archetype_literal_carries_b2b_tech() -> None:
    """Adding a new archetype is a 1-line Literal edit; b2b_tech is
    already in the Literal so the stub loads. This documents the
    architectural invariant: the Literal IS the registry."""
    # Get the Literal's args via typing introspection.
    import typing
    args = typing.get_args(Archetype)
    assert "b2b_tech" in args
    assert "b2c_aesthetics" in args
    assert "b2b_regulated" in args
    assert "b2b_saas" in args


def test_evaluation_domain_literal_does_not_carry_archetype_names() -> None:
    """The evaluation/models.py domain Literal is over LANE names, not
    archetypes. Adding a new archetype doesn't require touching it;
    adding a new LANE does. Documenting the invariant."""
    from src.evaluation.models import EvaluateRequest
    import typing
    # Inspect the `domain` field's type.
    fields = EvaluateRequest.model_fields
    domain_field = fields["domain"]
    # Pydantic v2 exposes annotation directly.
    annotation = domain_field.annotation
    args = typing.get_args(annotation)
    # No archetype names should leak into the domain Literal.
    for archetype_name in ("b2b_saas", "b2c_aesthetics", "b2b_regulated", "b2b_tech"):
        assert archetype_name not in args, (
            f"evaluation.models domain Literal mentions archetype "
            f"{archetype_name!r}; this is a separation-of-concerns "
            f"violation. Domains are LANE names; archetypes are "
            f"CLIENT classifications."
        )


# ---------------------------------------------------------------------------
# Reviewer-assist checklist independence
# ---------------------------------------------------------------------------


def test_adding_reviewer_assist_checklist_is_yaml_only() -> None:
    """Per D20: adding a new reviewer-assist checklist requires only
    the YAML file under reviewer_assist/checklists/ — no Python code.

    Validates the invariant by walking the reviewer_assist/ directory
    and confirming no `.py` files exist (the registry is YAML-driven).
    """
    checklists_dir = _REPO_ROOT / "reviewer_assist" / "checklists"
    if not checklists_dir.is_dir():
        pytest.skip("reviewer_assist/checklists not yet materialized")
    py_files = list(checklists_dir.rglob("*.py"))
    assert py_files == [], (
        f"reviewer_assist/checklists contains Python files: {py_files}. "
        f"D20 architectural invariant: checklists are YAML-driven; "
        f"any Python code belongs in src/compliance/."
    )


def test_archetype_brief_consumption_mode_literal_defaults_via_validator() -> None:
    """U13 ClientConfig.article_brief_consumption_mode has archetype-
    derived defaults via the before-validator. Adding a NEW archetype
    requires updating that validator's default rule — but the existing
    archetypes' defaults remain stable. Documents the invariant."""
    import typing
    args = typing.get_args(ArticleBriefConsumptionMode)
    assert "hybrid" in args
    assert "primary_only" in args
    # The stub (b2b_tech) defaults to 'hybrid' per the U13 validator.
    config = load_client_config("_stub_b2b_tech")
    assert config.article_brief_consumption_mode == "hybrid"
