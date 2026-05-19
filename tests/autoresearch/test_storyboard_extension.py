"""Storyboard lane extension (U8): platform_target + format_mode +
voice persona + content_denylist.

Test scope:
- configure_env env-var validation (platform + mode + voice + denylist)
- D17 fail-loud on impossible denylist+mode intersection
- custom_score format-mode reweighting (narrative no-op; educational
  + brand_authority apply tier weights)
- LaneSpec.rubric_ids extension (3 compliance rubric IDs)
- RUBRICS registers the new compliance entries
- Eval-suite fixtures referenced from search-v1.json
"""
from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT / "autoresearch") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "autoresearch"))


# Per CE-review testing finding test-4: prior imports targeted
# `autoresearch.archive.current_runtime.workflows.storyboard` — a
# gitignored ephemeral copy materialized by `ensure_materialized_runtime()`.
# Tests passed/failed based on whether the operator had run that
# materialization, not on the canonical U8 v007-curated source. Load
# directly from v007-curated via the synthetic-package loader pattern
# (mirrors test_linkedin_engine_substrate.py + test_x_engine_substrate.py).
_LANE_WORKFLOWS = _REPO_ROOT / "autoresearch" / "archive" / "v007-curated" / "workflows"
_TEMPLATES_ROOT = _REPO_ROOT / "autoresearch" / "archive" / "v007-curated" / "templates"
_PKG_NAME = "_test_v007_workflows_sb"


def _load_storyboard_workflow():
    """Load v007-curated/workflows/storyboard.py as a member of a
    synthetic parent package so its `from .eval_cache import …` +
    `from .specs import …` relative imports resolve."""
    if f"{_PKG_NAME}.storyboard" in sys.modules:
        return sys.modules[f"{_PKG_NAME}.storyboard"]
    pkg = types.ModuleType(_PKG_NAME)
    pkg.__path__ = [str(_LANE_WORKFLOWS)]
    sys.modules[_PKG_NAME] = pkg
    spec = importlib.util.spec_from_file_location(
        f"{_PKG_NAME}.storyboard",
        _LANE_WORKFLOWS / "storyboard.py",
        submodule_search_locations=None,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"{_PKG_NAME}.storyboard"] = module
    spec.loader.exec_module(module)
    return module


# Pre-load at module-import time so subsequent `from
# _test_v007_workflows_sb.storyboard import X` statements inside test
# functions resolve.
_load_storyboard_workflow()


# ---------------------------------------------------------------------------
# configure_env validation
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_storyboard_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clear all U8 env vars between tests so previous test state can't
    bleed into the next test's setdefault calls."""
    for key in (
        "CREATOR_HANDLE", "STORYBOARD_COUNT",
        "STORYBOARD_PLATFORM_TARGET", "STORYBOARD_FORMAT_MODE",
        "STORYBOARD_VOICE_PERSONA_REF", "STORYBOARD_CONTENT_DENYLIST",
    ):
        monkeypatch.delenv(key, raising=False)


def _configure_env(client: str = "test-client") -> None:
    """Re-import the storyboard workflow each call so module-level
    state doesn't leak between tests."""
    from _test_v007_workflows_sb.storyboard import (
        configure_env,
    )
    configure_env(client)


def test_configure_env_sets_defaults() -> None:
    """Per U8: env defaults are platform_target=youtube_long +
    format_mode=narrative + STORYBOARD_COUNT=5."""
    import os
    _configure_env("test-client")
    assert os.environ["STORYBOARD_PLATFORM_TARGET"] == "youtube_long"
    assert os.environ["STORYBOARD_FORMAT_MODE"] == "narrative"
    assert os.environ["STORYBOARD_COUNT"] == "5"
    assert os.environ["CREATOR_HANDLE"] == "test-client"


def test_configure_env_accepts_all_platform_targets(monkeypatch) -> None:
    from _test_v007_workflows_sb.storyboard import (
        ALLOWED_PLATFORM_TARGETS,
    )
    for platform in ALLOWED_PLATFORM_TARGETS:
        monkeypatch.delenv("STORYBOARD_PLATFORM_TARGET", raising=False)
        monkeypatch.setenv("STORYBOARD_PLATFORM_TARGET", platform)
        _configure_env("test")  # should not raise


def test_configure_env_rejects_unknown_platform(monkeypatch) -> None:
    monkeypatch.setenv("STORYBOARD_PLATFORM_TARGET", "x_video")
    with pytest.raises(ValueError) as exc:
        _configure_env("test")
    assert "STORYBOARD_PLATFORM_TARGET" in str(exc.value)


def test_configure_env_accepts_all_format_modes(monkeypatch) -> None:
    """Narrative + educational + brand_authority all valid. Brand_authority
    requires the voice persona ref."""
    from _test_v007_workflows_sb.storyboard import (
        ALLOWED_FORMAT_MODES,
    )
    for mode in ALLOWED_FORMAT_MODES:
        monkeypatch.delenv("STORYBOARD_FORMAT_MODE", raising=False)
        monkeypatch.delenv("STORYBOARD_VOICE_PERSONA_REF", raising=False)
        monkeypatch.setenv("STORYBOARD_FORMAT_MODE", mode)
        if mode == "brand_authority":
            monkeypatch.setenv("STORYBOARD_VOICE_PERSONA_REF", "dr_maria")
        _configure_env("test")  # should not raise


def test_configure_env_rejects_unknown_format_mode(monkeypatch) -> None:
    monkeypatch.setenv("STORYBOARD_FORMAT_MODE", "documentary")
    with pytest.raises(ValueError):
        _configure_env("test")


def test_brand_authority_requires_voice_persona_ref(monkeypatch) -> None:
    """Per U8: brand_authority is the only mode that hard-requires the
    voice persona ref. Narrative + educational soft-degrade."""
    monkeypatch.setenv("STORYBOARD_FORMAT_MODE", "brand_authority")
    monkeypatch.delenv("STORYBOARD_VOICE_PERSONA_REF", raising=False)
    with pytest.raises(ValueError) as exc:
        _configure_env("test")
    assert "STORYBOARD_VOICE_PERSONA_REF" in str(exc.value)


def test_d17_fail_loud_when_denylist_blocks_all_required(monkeypatch) -> None:
    """Per D17: lane refuses to start when format_mode + content_denylist
    intersection is empty. Educational mode requires at least one of
    informational_visuals / diagrams / screen_captures / data_visualization
    — denylist that includes ALL four trips D17."""
    monkeypatch.setenv("STORYBOARD_FORMAT_MODE", "educational")
    monkeypatch.setenv(
        "STORYBOARD_CONTENT_DENYLIST",
        "informational_visuals,diagrams,screen_captures,data_visualization",
    )
    with pytest.raises(ValueError) as exc:
        _configure_env("test")
    assert "D17" in str(exc.value) or "cannot produce" in str(exc.value)


def test_klinika_partial_denylist_does_not_trip_d17(monkeypatch) -> None:
    """Klinika's denylist (clinical_visuals + before_after_imagery) does
    NOT trip D17 for any mode: narrative still has depicted_scenes;
    educational still has informational_visuals; brand_authority still
    has voice_corpus_quotes."""
    for mode in ("narrative", "educational", "brand_authority"):
        monkeypatch.delenv("STORYBOARD_PLATFORM_TARGET", raising=False)
        monkeypatch.delenv("STORYBOARD_FORMAT_MODE", raising=False)
        monkeypatch.delenv("STORYBOARD_VOICE_PERSONA_REF", raising=False)
        monkeypatch.setenv("STORYBOARD_FORMAT_MODE", mode)
        monkeypatch.setenv(
            "STORYBOARD_CONTENT_DENYLIST",
            "clinical_visuals,before_after_imagery",
        )
        if mode == "brand_authority":
            monkeypatch.setenv("STORYBOARD_VOICE_PERSONA_REF", "dr_maria")
        _configure_env("klinika-melitus")  # should not raise


# ---------------------------------------------------------------------------
# custom_score reweighting
# ---------------------------------------------------------------------------


def test_format_mode_weights_pinned() -> None:
    """Pin the per-mode weight tables so a silent change is caught.
    Narrative is empty (no-op); educational + brand_authority have
    documented tilts."""
    from _test_v007_workflows_sb.storyboard import (
        _FORMAT_MODE_WEIGHTS,
    )
    assert _FORMAT_MODE_WEIGHTS["narrative"] == {}
    # Educational relaxes SB-3 + SB-4, upweights SB-6.
    assert _FORMAT_MODE_WEIGHTS["educational"]["SB-3"] < 1.0
    assert _FORMAT_MODE_WEIGHTS["educational"]["SB-4"] < 1.0
    assert _FORMAT_MODE_WEIGHTS["educational"]["SB-6"] > 1.0
    # Brand_authority upweights SB-1 + SB-5, softens SB-7.
    assert _FORMAT_MODE_WEIGHTS["brand_authority"]["SB-1"] > 1.0
    assert _FORMAT_MODE_WEIGHTS["brand_authority"]["SB-5"] > 1.0
    assert _FORMAT_MODE_WEIGHTS["brand_authority"]["SB-7"] < 1.0


# ---------------------------------------------------------------------------
# LaneSpec wiring
# ---------------------------------------------------------------------------


def test_storyboard_lanespec_has_compliance_rubric_ids() -> None:
    """Per U8 + plan §New-lane Substrate Wiring Checklist Item 5: the
    storyboard LaneSpec carries 3 compliance rubric IDs (one per v1
    rule set) alongside SB-1..SB-8."""
    from autoresearch.lane_registry import LANES
    spec = LANES["storyboard"]
    assert "gdpr_eu_storyboard_compliance" in spec.rubric_ids
    assert "medical_pl_storyboard_compliance" in spec.rubric_ids
    assert "legal_pl_storyboard_compliance" in spec.rubric_ids
    # Pre-U8 SB-1..SB-8 preserved
    for i in range(1, 9):
        assert f"SB-{i}" in spec.rubric_ids


def test_storyboard_lanespec_custom_score_wired() -> None:
    """Per U8: _wire_storyboard_callables binds custom_score to the
    LaneSpec at module load."""
    from autoresearch.lane_registry import LANES
    spec = LANES["storyboard"]
    assert spec.custom_score is not None


# ---------------------------------------------------------------------------
# RUBRICS registry
# ---------------------------------------------------------------------------


def test_compliance_rubrics_registered() -> None:
    """Per D12-hybrid + TD-11: each compliance rubric is registered for
    the storyboard lane.

    Per CE-review correctness C-11: compliance rubrics have prose_ref=
    None (verdict is computed by src.compliance.judge.evaluate_compliance
    against the reviewer-assist YAML, NOT by an LLM judge consuming
    resolved prose). Earlier iterations of this test asserted prose_ref
    is set — that was correct under the original (broken) prose_ref
    minting that pointed at `<lane>_compliance` anchors with no
    matching YAML rule. After C-11 fix, prose_ref MUST be None on
    these auto-generated rubrics; the test_resolve_prose suite pins
    the invariant programmatically.
    """
    from src.evaluation.rubrics import RUBRICS
    for rs in ("gdpr_eu", "medical_pl", "legal_pl"):
        rubric_id = f"{rs}_storyboard_compliance"
        assert rubric_id in RUBRICS, f"missing rubric {rubric_id}"
        template = RUBRICS[rubric_id]
        # Per C-11 fix: compliance rubrics use prose_ref=None.
        assert template.prose_ref is None, (
            f"{rubric_id} has prose_ref={template.prose_ref!r}; "
            f"compliance rubrics must use prose_ref=None per C-11"
        )
        assert template.domain == "storyboard"
        assert template.tier == "essential"
        # The inline prompt names the YAML so operators inspecting a
        # rubric template can find the rule set.
        assert f"reviewer_assist/checklists/{rs}.yaml" in template.prompt


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def test_klinika_and_dwf_fixtures_in_search_v1() -> None:
    """Per U8: the 2 Content Engine v1 fixtures appear in
    autoresearch/eval_suites/search-v1.json under the storyboard
    domain block."""
    suite_path = _REPO_ROOT / "autoresearch" / "eval_suites" / "search-v1.json"
    data = json.loads(suite_path.read_text())
    storyboard_fixtures = data["domains"]["storyboard"]
    fixture_ids = {f["fixture_id"] for f in storyboard_fixtures}
    assert "storyboard-klinika-short-form-educational" in fixture_ids
    assert "storyboard-dwf-long-form-brand-authority" in fixture_ids

    # Per D11: real-client provenance flag set.
    for fid in (
        "storyboard-klinika-short-form-educational",
        "storyboard-dwf-long-form-brand-authority",
    ):
        fixture = next(f for f in storyboard_fixtures if f["fixture_id"] == fid)
        assert fixture.get("data_provenance") == "real_client"
        # Per U8 contract: env carries the new STORYBOARD_* vars
        assert "STORYBOARD_PLATFORM_TARGET" in fixture["env"]
        assert "STORYBOARD_FORMAT_MODE" in fixture["env"]


def test_skeleton_templates_exist() -> None:
    """Per U8: 3 cold-start skeleton templates ship for the 3 format modes.
    Templates live under v007-curated/templates/ (the canonical source);
    earlier iteration of this test pointed at current_runtime/ which is
    gitignored ephemeral state."""
    templates_dir = _TEMPLATES_ROOT / "storyboard"
    for mode in ("narrative", "educational", "brand_authority"):
        path = templates_dir / f"skeleton-{mode}.md"
        assert path.is_file(), f"missing skeleton: {path}"
        content = path.read_text()
        # Each skeleton must reference its own mode + the JSON shape
        assert mode in content
        assert "story_id" in content
        assert "scenes" in content


# ---------------------------------------------------------------------------
# Drift pin — allowed sets
# ---------------------------------------------------------------------------


def test_allowed_platform_targets_pin() -> None:
    """The 5 platform_target values are fixed per U8 R1. Drift pin so a
    silent rename is caught."""
    from _test_v007_workflows_sb.storyboard import (
        ALLOWED_PLATFORM_TARGETS,
    )
    assert ALLOWED_PLATFORM_TARGETS == frozenset({
        "ig_reels", "tiktok", "ig_story", "ig_carousel", "youtube_long",
    })


def test_allowed_format_modes_pin() -> None:
    """The 3 format_mode values are fixed per U8 R2."""
    from _test_v007_workflows_sb.storyboard import (
        ALLOWED_FORMAT_MODES,
    )
    assert ALLOWED_FORMAT_MODES == frozenset({
        "narrative", "educational", "brand_authority",
    })
