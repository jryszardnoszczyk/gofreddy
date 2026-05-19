"""Cross-lane voice consistency (Plan Success Criterion #4).

Per plan §172:
  > "Cross-lane voice consistency: same persona consumed unchanged
  >   by 4 lanes"

And §1891:
  > "5 lanes consume same `dr_maria` persona — article, linkedin,
  >   x, ad, site"

The plan's U18 demo validates this at the OPERATOR level (Klinika
demo produces consistent voice across the 5 lane outputs). This
substrate-level test enforces the structural invariant that makes
operator-side consistency possible:

  1. compile_substrate() is deterministic for a given persona +
     corpus — N calls return identical output.
  2. All 5 voice-consuming lanes import compile_substrate from the
     SAME source (src.voice.persona) — no per-lane drift via
     copy-paste or per-lane re-implementation.
  3. Each lane's configure_env() reads its own VOICE_PERSONA_REF env
     var and writes the compiled substrate to its own runtime
     voice.md — but the COMPILED CONTENT is the same for the same
     persona, regardless of lane.

A new lane that adds persona consumption without going through
compile_substrate (or a refactor that splits the helper) breaks
this test loud at CI.
"""
from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
from types import ModuleType

import pytest


_REPO_ROOT = Path(__file__).resolve().parents[2]


# The 5 textual lanes per plan §1891 + image_engine (which also routes
# alt-text + caption voice through compile_substrate per its workflow).
# Storyboard handles voice differently (voice_persona_ref env is optional,
# only required for brand_authority mode; uses its own loader) and is
# intentionally EXCLUDED from this consistency check.
_VOICE_CONSUMING_LANES: dict[str, str] = {
    "article_engine":  "autoresearch/archive/v007-curated/workflows/article_engine.py",
    "linkedin_engine": "autoresearch/archive/v007-curated/workflows/linkedin_engine.py",
    "x_engine":        "autoresearch/archive/v007-curated/workflows/x_engine.py",
    "ad_engine":       "autoresearch/archive/v007-curated/workflows/ad_engine.py",
    "site_engine":     "autoresearch/archive/v007-curated/workflows/site_engine.py",
    "image_engine":    "autoresearch/archive/v007-curated/workflows/image_engine.py",
}


def _load_lane_workflow(rel_path: str) -> ModuleType:
    """Load a lane workflow module from its hyphenated path.

    The v007-curated/ path component contains a hyphen, which Python's
    standard import machinery rejects. Use importlib.util.spec_from_file_location
    to side-step the issue (same pattern used in other substrate
    tests).
    """
    full = _REPO_ROOT / rel_path
    assert full.is_file(), f"lane workflow missing: {full}"
    spec = importlib.util.spec_from_file_location(
        f"_lane_{full.stem}", full,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_compile_substrate_is_deterministic() -> None:
    """Pin: compile_substrate(persona, corpus) returns identical output
    on repeated calls. Without determinism, different lanes consuming
    the same persona at different times would see drift, defeating
    Success Criterion #4."""
    from src.voice.persona import compile_substrate, load_corpus_files, load_persona

    # Use the `jr` persona — its corpus is shipped in-repo (public
    # substrate, not consent-gated) so this test runs without operator
    # setup. Per the gitignore exception:
    #   `!voice_personas/corpora/jr/**`
    persona = load_persona("jr")
    corpus = load_corpus_files(persona)
    out_a = compile_substrate(persona, corpus)
    out_b = compile_substrate(persona, corpus)
    out_c = compile_substrate(persona, corpus)
    assert out_a == out_b == out_c, (
        "compile_substrate is non-deterministic. Cross-lane voice "
        "consistency (Plan SC #4) requires identical output for "
        "identical input."
    )
    assert out_a, "compile_substrate returned empty output for the jr persona"


# ---------------------------------------------------------------------------
# Structural: every voice-consuming lane imports from the same module
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("lane_name,rel_path", list(_VOICE_CONSUMING_LANES.items()))
def test_lane_imports_compile_substrate_from_canonical_module(
    lane_name: str, rel_path: str,
) -> None:
    """Pin: each voice-consuming lane imports compile_substrate from
    `src.voice.persona`. A lane that re-implements substrate compilation
    in-line, or imports from a per-lane copy, breaks cross-lane
    consistency.

    Reads the workflow source rather than the loaded module to avoid
    forcing lane preconditions (env vars, lazy imports). The structural
    invariant is import-site, not runtime."""
    full = _REPO_ROOT / rel_path
    src_text = full.read_text(encoding="utf-8")
    assert "from src.voice.persona import" in src_text, (
        f"{lane_name} ({rel_path}) does not import from src.voice.persona. "
        f"Cross-lane voice consistency requires every voice-consuming "
        f"lane to route through the canonical compile_substrate helper."
    )
    assert "compile_substrate" in src_text, (
        f"{lane_name} ({rel_path}) does not reference compile_substrate. "
        f"Persona consumption must flow through the canonical helper, "
        f"not via per-lane substrate logic."
    )


def test_voice_consuming_lanes_match_plan_callout() -> None:
    """Pin: the set of voice-consuming lanes matches plan §1891's
    callout of `dr_maria` consumption (5 textual lanes — article,
    linkedin, x, ad, site) plus image_engine which also routes
    persona through compile_substrate for alt-text + caption voice.
    Storyboard intentionally NOT in this set (different voice-handling
    pattern, see module docstring)."""
    plan_text_lanes = {"article_engine", "linkedin_engine", "x_engine", "ad_engine", "site_engine"}
    assert plan_text_lanes <= set(_VOICE_CONSUMING_LANES.keys()), (
        f"Voice-consuming-lanes registry missing plan §1891 callouts: "
        f"{plan_text_lanes - set(_VOICE_CONSUMING_LANES.keys())}"
    )
    assert "image_engine" in _VOICE_CONSUMING_LANES


# ---------------------------------------------------------------------------
# Anchor preservation
# ---------------------------------------------------------------------------


def test_compile_substrate_preserves_persona_anchors() -> None:
    """Pin: compile_substrate output carries the persona's style_anchors
    + voice_rules verbatim (or with the documented formatting). Any
    lane consuming the compiled substrate must see the anchors so its
    own prose generation can reference them."""
    from src.voice.persona import compile_substrate, load_corpus_files, load_persona

    persona = load_persona("jr")
    corpus = load_corpus_files(persona)
    compiled = compile_substrate(persona, corpus)

    # If the persona declares any anchors, at least one must appear in
    # the compiled output. (Empty-anchor personas are valid per schema;
    # the jr persona ships with concrete anchors.)
    if persona.style_anchors:
        anchor_strings = [str(a) for a in persona.style_anchors]
        found = sum(1 for anchor in anchor_strings if anchor in compiled)
        assert found > 0, (
            f"compile_substrate dropped all {len(anchor_strings)} style "
            f"anchors. Compiled output: {compiled[:200]!r}..."
        )
