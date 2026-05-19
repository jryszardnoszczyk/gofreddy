"""resolve_prose: TD-11 hybrid rubric resolution (U5).

Per TD-56: the resolver lives INLINE in src/evaluation/rubrics.py as a
~50-LOC function rather than a separate src/evaluation/rubric_resolver.py
module. This test file pins the function's existence + the no-separate-
module invariant so future refactors stay inline.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from src.evaluation.rubrics import RUBRICS, RubricTemplate, resolve_prose


# ---------------------------------------------------------------------------
# No-separate-module pin (TD-56)
# ---------------------------------------------------------------------------


def test_resolve_prose_lives_in_rubrics_module() -> None:
    """Per TD-56 cut: the resolver is inlined in rubrics.py, NOT its own
    rubric_resolver.py module. Drift pin so a future refactor doesn't
    silently split it out."""
    import src.evaluation.rubrics as rubrics_mod
    assert hasattr(rubrics_mod, "resolve_prose")

    # And no separate module exists.
    with pytest.raises(ModuleNotFoundError):
        __import__("src.evaluation.rubric_resolver")


# ---------------------------------------------------------------------------
# Fallback: prose_ref=None → inline prompt
# ---------------------------------------------------------------------------


def test_resolve_prose_returns_inline_prompt_when_prose_ref_none() -> None:
    template = RubricTemplate(
        criterion_id="TEST-1",
        domain="test",
        scoring_type="gradient",
        prompt="Inline prompt content goes here.",
    )
    assert resolve_prose(template) == "Inline prompt content goes here."


# ---------------------------------------------------------------------------
# YAML resolution: reviewer_assist/checklists/<name>.yaml#<rule_id>
# ---------------------------------------------------------------------------


def test_resolve_prose_loads_yaml_rule_prose() -> None:
    """Real-data integration: resolve a prose_ref against the shipped
    gdpr_eu reviewer-assist YAML."""
    template = RubricTemplate(
        criterion_id="gdpr_eu_article_engine_compliance",
        domain="article_engine",
        scoring_type="gradient",
        prompt="",  # placeholder; not used when prose_ref resolves
        prose_ref="reviewer_assist/checklists/gdpr_eu.yaml#gdpr_safe_harbor_invalid",
    )
    prose = resolve_prose(template)
    assert "Safe Harbor" in prose
    assert "Schrems" in prose


def test_resolve_prose_raises_on_missing_yaml_rule() -> None:
    template = RubricTemplate(
        criterion_id="TEST-1", domain="test", scoring_type="gradient",
        prompt="",
        prose_ref="reviewer_assist/checklists/gdpr_eu.yaml#does_not_exist",
    )
    with pytest.raises(KeyError) as exc:
        resolve_prose(template)
    assert "does_not_exist" in str(exc.value)


def test_resolve_prose_raises_when_anchor_missing_from_ref() -> None:
    template = RubricTemplate(
        criterion_id="TEST-1", domain="test", scoring_type="gradient",
        prompt="",
        prose_ref="reviewer_assist/checklists/gdpr_eu.yaml",  # no #<id>
    )
    with pytest.raises(ValueError) as exc:
        resolve_prose(template)
    assert "anchor" in str(exc.value).lower() or "#" in str(exc.value)


# ---------------------------------------------------------------------------
# Markdown resolution: docs/rubrics/<file>.md#<anchor>
# ---------------------------------------------------------------------------


def test_resolve_prose_loads_markdown_section(tmp_path: Path) -> None:
    md_root = tmp_path / "docs" / "rubrics"
    md_root.mkdir(parents=True)
    md_file = md_root / "site-quality.md"
    md_file.write_text(
        "# Site Quality Rubric\n\n"
        "Some intro text.\n\n"
        "## SE-1: visual hierarchy\n\n"
        "Hierarchy prose lives here.\n\n"
        "## SE-2: copy clarity\n\n"
        "Different prose for SE-2.\n"
    )

    template = RubricTemplate(
        criterion_id="SE-1", domain="site_engine", scoring_type="gradient",
        prompt="",
        prose_ref="docs/rubrics/site-quality.md#SE-1",
    )
    prose = resolve_prose(template, registry_root=tmp_path)
    assert "Hierarchy prose lives here" in prose
    assert "Different prose for SE-2" not in prose


def test_resolve_prose_markdown_anchor_match_is_case_insensitive(tmp_path: Path) -> None:
    md_root = tmp_path / "docs" / "rubrics"
    md_root.mkdir(parents=True)
    (md_root / "site-quality.md").write_text(
        "## SE-1: visual hierarchy\n\nProse body.\n"
    )
    template = RubricTemplate(
        criterion_id="SE-1", domain="site_engine", scoring_type="gradient",
        prompt="",
        prose_ref="docs/rubrics/site-quality.md#se-1",  # lowercase anchor
    )
    prose = resolve_prose(template, registry_root=tmp_path)
    assert "Prose body" in prose


def test_resolve_prose_raises_on_missing_markdown_anchor(tmp_path: Path) -> None:
    md_root = tmp_path / "docs" / "rubrics"
    md_root.mkdir(parents=True)
    (md_root / "site-quality.md").write_text("## SE-1: x\n\nBody.\n")
    template = RubricTemplate(
        criterion_id="SE-99", domain="site_engine", scoring_type="gradient",
        prompt="",
        prose_ref="docs/rubrics/site-quality.md#SE-99",
    )
    with pytest.raises(KeyError):
        resolve_prose(template, registry_root=tmp_path)


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------


def test_resolve_prose_raises_when_file_missing(tmp_path: Path) -> None:
    template = RubricTemplate(
        criterion_id="TEST-1", domain="test", scoring_type="gradient",
        prompt="",
        prose_ref="reviewer_assist/checklists/missing.yaml#fixture_rule",
    )
    with pytest.raises(FileNotFoundError):
        resolve_prose(template, registry_root=tmp_path)


def test_resolve_prose_raises_on_unsupported_extension(tmp_path: Path) -> None:
    weird = tmp_path / "rules.txt"
    weird.write_text("not yaml or markdown")
    template = RubricTemplate(
        criterion_id="TEST-1", domain="test", scoring_type="gradient",
        prompt="",
        prose_ref="rules.txt#anchor",
    )
    with pytest.raises(ValueError) as exc:
        resolve_prose(template, registry_root=tmp_path)
    assert "unsupported file extension" in str(exc.value)


def test_resolve_prose_rejects_path_traversal_outside_root(tmp_path: Path) -> None:
    """Per the 4-agent review (sec-5): prose_ref like
    `../../../../etc/passwd.yaml#anything` cannot escape the registry
    root, even if such a file exists on disk."""
    # Create the registry root + a sibling "secrets" directory outside it.
    root = tmp_path / "registry"
    root.mkdir()
    outside = tmp_path / "secrets.yaml"
    outside.write_text("rules:\n  - id: leaked\n    prose: SHOULD_NOT_LOAD\n")

    template = RubricTemplate(
        criterion_id="TEST-1", domain="test", scoring_type="gradient",
        prompt="",
        prose_ref="../secrets.yaml#leaked",
    )
    with pytest.raises(ValueError) as exc:
        resolve_prose(template, registry_root=root)
    assert "outside the registry root" in str(exc.value)


# ---------------------------------------------------------------------------
# CE-review C-11: every registered prose_ref must resolve
# ---------------------------------------------------------------------------


def test_every_registered_prose_ref_resolves() -> None:
    """Drift pin (CE-review C-11): for every RubricTemplate in RUBRICS
    with `prose_ref` set, `resolve_prose(t)` must succeed.

    Earlier iterations of `rubrics.py` minted compliance rubric prose_ref
    entries pointing at `<lane>_compliance` anchors that didn't exist in
    any YAML — `resolve_prose` would KeyError on first call. This test
    catches that class of bug at substrate-load time, not at evaluation
    time. The compliance rubrics now correctly use prose_ref=None
    because their verdict is computed by evaluate_compliance (regex)
    not by an LLM judge consuming resolved prose."""
    failures: list[tuple[str, str, str]] = []
    for criterion_id, template in RUBRICS.items():
        if template.prose_ref is None:
            continue
        try:
            prose = resolve_prose(template)
            assert prose, f"{criterion_id}: prose_ref resolved to empty"
        except Exception as exc:  # KeyError, FileNotFoundError, ValueError
            failures.append((criterion_id, template.prose_ref, str(exc)[:160]))
    assert not failures, (
        f"{len(failures)} prose_ref entries failed to resolve:\n  "
        + "\n  ".join(f"{cid}: {ref!r} -> {err}" for cid, ref, err in failures)
    )


def test_compliance_rubrics_use_prose_ref_none() -> None:
    """Pin: auto-generated `<rule_set>_<lane>_compliance` rubrics MUST
    NOT have prose_ref set. They are scored by evaluate_compliance
    (deterministic regex), not by an LLM judge consuming resolved
    prose. Setting prose_ref on them would either KeyError (no matching
    rule id in the YAML) or load arbitrary unrelated rule prose."""
    compliance_ids = [cid for cid in RUBRICS if cid.endswith("_compliance")]
    assert len(compliance_ids) > 0, "no compliance rubrics in RUBRICS"
    for cid in compliance_ids:
        assert RUBRICS[cid].prose_ref is None, (
            f"compliance rubric {cid!r} has prose_ref={RUBRICS[cid].prose_ref!r}; "
            f"must be None (verdict via evaluate_compliance, not resolve_prose)"
        )
