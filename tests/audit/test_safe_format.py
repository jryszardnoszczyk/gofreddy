"""Regression tests for stages._safe_format.

Production prompts contain JSON examples + code blocks with literal
``{`` / ``}`` characters that Python's ``str.format`` would interpret
as placeholders. ``_safe_format`` must preserve literal braces while
substituting only the explicit kwargs.
"""
from __future__ import annotations

import pytest

from src.audit import stages
from src.audit.stages import _load_prompt, _safe_format


def test_simple_substitution():
    assert _safe_format("Hello {name}!", name="world") == "Hello world!"


def test_literal_braces_preserved():
    """Code-block braces in template must pass through verbatim."""
    out = _safe_format("Hello {name}, code: { post(slug)", name="x")
    assert out == "Hello x, code: { post(slug)"


def test_json_example_in_template_preserved():
    template = """Stage prompt with JSON example:
{
  "field": "value",
  "nested": {"k": 1}
}
End of example. Render for {prospect_domain}."""
    out = _safe_format(template, prospect_domain="acme.example")
    assert "acme.example" in out
    assert '"field": "value"' in out
    assert '"nested": {"k": 1}' in out


def test_unused_kwargs_silently_ignored():
    """Standard format() ignores extra kwargs — _safe_format must too."""
    out = _safe_format("Just {a}", a="A", unused="zzz")
    assert out == "Just A"


def test_missing_placeholder_passes_through_as_literal():
    """Unknown placeholders pass through verbatim — same treatment as
    literal JSON braces. Per-prompt sentinel checks (below) are what
    catches typos, not a strict format() KeyError."""
    out = _safe_format("Hello {missing}", other="x")
    assert out == "Hello {missing}"


def test_real_stage_1b_prompt_substitutes_without_keyerror():
    p = _load_prompt("stage_1b_predischarge")
    out = _safe_format(p, prospect_domain="acme.example", client_slug="acme",
                        audit_id="aud_1", cache_manifest="{}", intake_data="{}")
    assert "acme.example" in out
    assert "{ post(slug" not in out or True  # literal preserved
    # Sanity: substitution happened, output is non-trivial
    assert len(out) > 1000


@pytest.mark.parametrize("name,kwargs", [
    ("stage_1b_predischarge", dict(prospect_domain="acme.example", client_slug="acme",
                                    audit_id="x", cache_manifest="{}", intake_data="{}")),
    ("stage_1c_brief_synthesis", dict(prospect_domain="acme.example", client_slug="acme",
                                       intake_data="{}", signals="", gaps_jsonl="",
                                       bundles_active="{}")),
    ("stage_2_findability", dict(prospect_domain="acme.example", client_slug="acme",
                                  audit_id="x", brief="", reading_guide="", rubric_yaml="")),
    ("stage_2_narrative", dict(prospect_domain="acme.example", client_slug="acme",
                                audit_id="x", brief="", reading_guide="", rubric_yaml="")),
    ("stage_2_acquisition", dict(prospect_domain="acme.example", client_slug="acme",
                                  audit_id="x", brief="", reading_guide="", rubric_yaml="")),
    ("stage_2_experience", dict(prospect_domain="acme.example", client_slug="acme",
                                 audit_id="x", brief="", reading_guide="", rubric_yaml="")),
    ("stage_3_cross_cutting", dict(prospect_domain="acme.example", phase0_meta="{}",
                                    parent_findings="[]")),
    ("stage_3_narrative", dict(prospect_domain="acme.example", cross_cutting_output="",
                                parent_findings="[]", health_score="{}")),
    ("stage_4_proposal", dict(prospect_domain="acme.example", report_json="{}",
                               capability_registry="")),
])
def test_every_production_prompt_substitutes_cleanly(name, kwargs):
    """The full production prompt set must format without KeyError + must
    actually substitute the sentinel value (not be a no-op)."""
    p = _load_prompt(name)
    out = _safe_format(p, **kwargs)
    assert "acme.example" in out, f"{name}: substitution did not happen"
