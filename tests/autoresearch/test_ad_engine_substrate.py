"""U15 — ad_engine substrate (workflow + session_eval + structural gate).

Mirrors test_article/image_engine_substrate.py in module-loading shape.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from types import ModuleType

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_WORKFLOWS_DIR = (
    _REPO_ROOT / "autoresearch" / "archive" / "v007-curated" / "workflows"
)


def _load(name: str) -> ModuleType:
    parent_pkg_name = "_ad_test_workflows"
    if parent_pkg_name not in sys.modules:
        parent_pkg = ModuleType(parent_pkg_name)
        parent_pkg.__path__ = [str(_WORKFLOWS_DIR)]  # type: ignore[attr-defined]
        sys.modules[parent_pkg_name] = parent_pkg

    module_name = f"{parent_pkg_name}.{name}_under_test"
    spec = importlib.util.spec_from_file_location(
        module_name, _WORKFLOWS_DIR / f"{name}.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load spec for {name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def ad_engine() -> ModuleType:
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    return _load("ad_engine")


@pytest.fixture
def session_eval_ad() -> ModuleType:
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    return _load("session_eval_ad_engine")


@pytest.fixture(autouse=True)
def _reset_ad_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "AD_ENGINE_VOICE_PERSONA_REF",
        "AD_ENGINE_CAMPAIGN_GOAL",
        "AD_ENGINE_OFFER",
        "AD_ENGINE_TARGET_AUDIENCE",
        "AD_ENGINE_PLATFORM_TARGET",
        "AD_ENGINE_AD_FORMAT_PER_PLATFORM",
        "AD_ENGINE_CAMPAIGN_ID",
        "AD_ENGINE_SESSION_DIR",
        "AUTORESEARCH_CONTEXT",
        "AUTORESEARCH_SESSION_DIR",
    ):
        monkeypatch.delenv(key, raising=False)


# ---------------------------------------------------------------------------
# configure_env validation
# ---------------------------------------------------------------------------


def test_configure_env_fails_loud_missing_persona(ad_engine: ModuleType) -> None:
    with pytest.raises(RuntimeError) as exc:
        ad_engine.configure_env("test-client")
    assert "AD_ENGINE_VOICE_PERSONA_REF" in str(exc.value)


def test_configure_env_rejects_google_platform(
    ad_engine: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """v1 scope: meta + linkedin only; google deferred to v1.5."""
    fake = tmp_path / "v_test"
    fake.mkdir()
    monkeypatch.setattr(ad_engine, "_VARIANT_ROOT", fake)
    monkeypatch.setenv("AD_ENGINE_VOICE_PERSONA_REF", "jr")
    monkeypatch.setenv("AD_ENGINE_CAMPAIGN_GOAL", "demos")
    monkeypatch.setenv("AD_ENGINE_OFFER", "free trial")
    monkeypatch.setenv("AD_ENGINE_TARGET_AUDIENCE", "marketers")
    monkeypatch.setenv("AD_ENGINE_PLATFORM_TARGET", "google,meta")
    monkeypatch.setenv("AD_ENGINE_AD_FORMAT_PER_PLATFORM", '{"meta": "meta_image"}')
    with pytest.raises(RuntimeError) as exc:
        ad_engine.configure_env("test-client")
    assert "google" in str(exc.value).lower()
    assert "v1.5" in str(exc.value)


def test_configure_env_happy_path(
    ad_engine: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    fake = tmp_path / "v_test"
    fake.mkdir()
    monkeypatch.setattr(ad_engine, "_VARIANT_ROOT", fake)
    monkeypatch.setenv("AD_ENGINE_VOICE_PERSONA_REF", "jr")
    monkeypatch.setenv("AD_ENGINE_CAMPAIGN_GOAL", "demos")
    monkeypatch.setenv("AD_ENGINE_OFFER", "free 15-min consultation")
    monkeypatch.setenv("AD_ENGINE_TARGET_AUDIENCE", "marketing operators")
    monkeypatch.setenv("AD_ENGINE_PLATFORM_TARGET", "meta,linkedin")
    monkeypatch.setenv(
        "AD_ENGINE_AD_FORMAT_PER_PLATFORM",
        '{"meta": "meta_image", "linkedin": "linkedin_sponsored"}',
    )

    ad_engine.configure_env("test-client")

    runtime_voice = (
        fake.parent / "current_runtime"
        / "programs" / "references" / "voice.md"
    )
    assert runtime_voice.is_file()


def test_configure_env_allowed_platforms_meta_linkedin_only(
    ad_engine: ModuleType,
) -> None:
    """Plan §scope: v1 supports meta + linkedin; tiktok/google deferred."""
    assert ad_engine.ALLOWED_PLATFORMS == frozenset({"meta", "linkedin"})


# ---------------------------------------------------------------------------
# structural_gate
# ---------------------------------------------------------------------------


def _well_formed_variant(format: str = "meta_image") -> dict:
    """Build a well-formed variant artifact dict. Hook + headline
    share enough tokens to satisfy the AD-8 Jaccard ≥0.4 gate."""
    return {
        "variant_id": "v1",
        "format": format,
        "platform": "meta" if format.startswith("meta_") else "linkedin",
        "hook_archetype": "statistic",
        "ad_creative": {
            "hook": "Ship campaigns 3x faster with proven tooling",
            "body": "We help marketing teams ship campaigns 3x faster.",
            "cta": {"verb": "Book", "text": "Book demo"},
            "image_brief": "Brand-anchored composition; no stock photo.",
            "proof_noun": "campaigns",
        },
        "lp_hero": {
            "headline": "Ship campaigns 3x faster with proven tooling",
            "subhead": "Built for enterprise marketing teams.",
            "primary_cta": {"verb": "Book", "text": "Book a 15-min demo"},
            "proof_point": "Our 50 enterprise clients ship campaigns 3x faster on average.",
        },
    }


def test_structural_gate_passes_well_formed_meta_image(
    session_eval_ad: ModuleType, tmp_path: Path,
) -> None:
    artifact = tmp_path / "drafts" / "v1.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(json.dumps(_well_formed_variant("meta_image")))
    failures = session_eval_ad.structural_gate("full", artifact, tmp_path)
    assert failures == [], f"unexpected: {failures}"


def test_structural_gate_rejects_invalid_json(
    session_eval_ad: ModuleType, tmp_path: Path,
) -> None:
    artifact = tmp_path / "drafts" / "v1.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("{not valid json")
    failures = session_eval_ad.structural_gate("full", artifact, tmp_path)
    assert any("not valid JSON" in f for f in failures)


def test_structural_gate_rejects_missing_lp_hero(
    session_eval_ad: ModuleType, tmp_path: Path,
) -> None:
    variant = _well_formed_variant()
    del variant["lp_hero"]
    artifact = tmp_path / "drafts" / "v1.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(json.dumps(variant))
    failures = session_eval_ad.structural_gate("full", artifact, tmp_path)
    assert any("lp_hero" in f for f in failures)


def test_structural_gate_fails_message_match_jaccard(
    session_eval_ad: ModuleType, tmp_path: Path,
) -> None:
    """AD-8 hard structural: jaccard(ad.hook, lp.headline) ≥ 0.4."""
    variant = _well_formed_variant()
    variant["lp_hero"]["headline"] = "Totally unrelated landing page about other things"
    artifact = tmp_path / "drafts" / "v1.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(json.dumps(variant))
    failures = session_eval_ad.structural_gate("full", artifact, tmp_path)
    assert any("AD-8" in f and "message-match" in f for f in failures)


def test_structural_gate_fails_cta_verb_mismatch(
    session_eval_ad: ModuleType, tmp_path: Path,
) -> None:
    variant = _well_formed_variant()
    variant["ad_creative"]["cta"] = {"verb": "Book", "text": "Book demo"}
    variant["lp_hero"]["primary_cta"] = {"verb": "Apply", "text": "Apply now"}
    artifact = tmp_path / "drafts" / "v1.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(json.dumps(variant))
    failures = session_eval_ad.structural_gate("full", artifact, tmp_path)
    assert any("CTA verb mismatch" in f for f in failures)


def test_structural_gate_fails_meta_health_banned_terms(
    session_eval_ad: ModuleType, tmp_path: Path,
) -> None:
    """Meta health-vertical banned words → structural fail for meta_*."""
    variant = _well_formed_variant("meta_image")
    variant["ad_creative"]["body"] = (
        "We cure your symptoms and heal your skin with our treatment."
    )
    # Align LP to keep jaccard high
    variant["lp_hero"]["headline"] = (
        "We cure symptoms and heal skin with our treatment."
    )
    artifact = tmp_path / "drafts" / "v1.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(json.dumps(variant))
    failures = session_eval_ad.structural_gate("full", artifact, tmp_path)
    assert any("Meta health-vertical" in f for f in failures)


def test_structural_gate_fails_linkedin_aggressive_phrases(
    session_eval_ad: ModuleType, tmp_path: Path,
) -> None:
    """LinkedIn aggressive-promotional phrases → fail for linkedin_*."""
    variant = _well_formed_variant("linkedin_sponsored")
    variant["ad_creative"]["body"] = (
        "Get guaranteed ROI in 30 days with our secret hack."
    )
    variant["lp_hero"]["headline"] = "Get guaranteed ROI in 30 days"
    artifact = tmp_path / "drafts" / "v1.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(json.dumps(variant))
    failures = session_eval_ad.structural_gate("full", artifact, tmp_path)
    assert any("LinkedIn aggressive" in f for f in failures)


def test_structural_gate_fails_meta_character_limits(
    session_eval_ad: ModuleType, tmp_path: Path,
) -> None:
    """Meta primary text >125 chars hard-fails."""
    variant = _well_formed_variant("meta_image")
    variant["ad_creative"]["body"] = "x" * 200  # >125 chars
    artifact = tmp_path / "drafts" / "v1.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(json.dumps(variant))
    failures = session_eval_ad.structural_gate("full", artifact, tmp_path)
    assert any("char cap" in f for f in failures)


def test_structural_gate_flags_anti_patterns(
    session_eval_ad: ModuleType, tmp_path: Path,
) -> None:
    """Anti-pattern hits surface as structural-gate notes (cap rubric
    score; don't auto-reject)."""
    variant = _well_formed_variant("meta_image")
    variant["ad_creative"]["hook"] = "Tired of broken workflows? Meet our platform."
    # Align LP
    variant["lp_hero"]["headline"] = "Tired of broken workflows? Meet our platform."
    artifact = tmp_path / "drafts" / "v1.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(json.dumps(variant))
    failures = session_eval_ad.structural_gate("full", artifact, tmp_path)
    assert any("Anti-pattern" in f for f in failures)


# ---------------------------------------------------------------------------
# LaneSpec wiring
# ---------------------------------------------------------------------------


def test_lane_registry_ad_engine_inner_pinned_to_claude_sonnet() -> None:
    """U15 plan §judge wiring: inner statically pinned to claude/sonnet
    (NOT codex — healthcare/legal vocabulary trips codex cyber filter)."""
    from autoresearch.lane_registry import LANES
    spec = LANES["ad_engine"]
    assert spec.inner_backend == "claude"
    assert spec.inner_model == "sonnet"


def test_lane_registry_ad_engine_has_11_rubric_ids() -> None:
    """8 AD + 3 compliance per U15."""
    from autoresearch.lane_registry import LANES
    spec = LANES["ad_engine"]
    assert len(spec.rubric_ids) == 11
    assert all(rid.startswith("AD-") for rid in spec.rubric_ids[:8])
    assert "gdpr_eu_ad_engine_compliance" in spec.rubric_ids
    assert "medical_pl_ad_engine_compliance" in spec.rubric_ids
    assert "legal_pl_ad_engine_compliance" in spec.rubric_ids


def test_lane_registry_ad_engine_deliverables_are_json() -> None:
    """U15 variants are JSON artifacts (not .md drafts) per TD-42."""
    from autoresearch.lane_registry import LANES
    spec = LANES["ad_engine"]
    assert "drafts/*.json" in spec.deliverables
