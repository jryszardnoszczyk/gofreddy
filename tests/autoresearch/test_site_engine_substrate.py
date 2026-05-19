"""U15b — site_engine substrate (workflow + session_eval + 2-pass gate).

Mirrors test_article/image/ad_engine_substrate.py in module-loading shape.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_WORKFLOWS_DIR = (
    _REPO_ROOT / "autoresearch" / "archive" / "v007-curated" / "workflows"
)


def _load(name: str) -> ModuleType:
    parent_pkg_name = "_se_test_workflows"
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
def site_engine() -> ModuleType:
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    return _load("site_engine")


@pytest.fixture
def session_eval_site() -> ModuleType:
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    return _load("session_eval_site_engine")


@pytest.fixture(autouse=True)
def _reset_site_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "SITE_ENGINE_VOICE_PERSONA_REF",
        "SITE_ENGINE_TARGET_URL",
        "SITE_ENGINE_SECTION",
        "SITE_ENGINE_BRAND_TOKENS_PATH",
        "SITE_ENGINE_BRIEFS_PATH",
        "SITE_ENGINE_AUDIENCE",
        "SITE_ENGINE_CONTEXT_ID",
        "SITE_ENGINE_SESSION_DIR",
        "AUTORESEARCH_CONTEXT",
        "AUTORESEARCH_SESSION_DIR",
    ):
        monkeypatch.delenv(key, raising=False)


# ---------------------------------------------------------------------------
# configure_env validation
# ---------------------------------------------------------------------------


def test_configure_env_fails_missing_persona(site_engine: ModuleType) -> None:
    with pytest.raises(RuntimeError) as exc:
        site_engine.configure_env("test-client")
    assert "SITE_ENGINE_VOICE_PERSONA_REF" in str(exc.value)


def test_configure_env_fails_missing_target_url(
    site_engine: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    fake = tmp_path / "v_test"
    fake.mkdir()
    monkeypatch.setattr(site_engine, "_VARIANT_ROOT", fake)
    monkeypatch.setenv("SITE_ENGINE_VOICE_PERSONA_REF", "jr")
    with pytest.raises(RuntimeError) as exc:
        site_engine.configure_env("test-client")
    assert "SITE_ENGINE_TARGET_URL" in str(exc.value)


def test_configure_env_fails_invalid_section(
    site_engine: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    fake = tmp_path / "v_test"
    fake.mkdir()
    monkeypatch.setattr(site_engine, "_VARIANT_ROOT", fake)
    monkeypatch.setenv("SITE_ENGINE_VOICE_PERSONA_REF", "jr")
    monkeypatch.setenv("SITE_ENGINE_TARGET_URL", "https://example.com")
    monkeypatch.setenv("SITE_ENGINE_SECTION", "full_page")
    monkeypatch.setenv("SITE_ENGINE_BRAND_TOKENS_PATH", "x.json")
    with pytest.raises(RuntimeError) as exc:
        site_engine.configure_env("test-client")
    assert "full_page" in str(exc.value)
    assert "section-level only" in str(exc.value)


def test_configure_env_allowed_sections_six(site_engine: ModuleType) -> None:
    """v1 scope per TD-28: 6 section types."""
    assert site_engine.ALLOWED_SECTIONS == frozenset({
        "hero", "value_prop", "social_proof", "faq", "cta", "pricing",
    })


def test_configure_env_happy_path(
    site_engine: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    fake = tmp_path / "v_test"
    fake.mkdir()
    monkeypatch.setattr(site_engine, "_VARIANT_ROOT", fake)
    monkeypatch.setenv("SITE_ENGINE_VOICE_PERSONA_REF", "jr")
    monkeypatch.setenv("SITE_ENGINE_TARGET_URL", "https://example.com")
    monkeypatch.setenv("SITE_ENGINE_SECTION", "hero")
    monkeypatch.setenv("SITE_ENGINE_BRAND_TOKENS_PATH", "clients/_stub_b2b_tech/brand/palette.json")
    site_engine.configure_env("test-client")
    runtime_voice = (
        fake.parent / "current_runtime"
        / "programs" / "references" / "voice.md"
    )
    assert runtime_voice.is_file()


# ---------------------------------------------------------------------------
# structural_gate
# ---------------------------------------------------------------------------


_WELL_FORMED_HERO = """<!-- frontmatter:
variant_id: hero_v1
section: hero
voice_persona: jr
brand_tokens_path: x.json
mutation_strategy: copy_rewrite
layout_recipe: left_text_right_image
-->
<section data-section="hero">
  <h1 data-element="h1">Ship campaigns 3x faster with proven tooling</h1>
  <p data-element="subhead">Built for enterprise marketing teams.</p>
  <a href="https://example.com/demo" data-element="primary_cta" class="primary-cta">Book demo</a>
</section>
"""


def test_structural_gate_passes_well_formed_hero(
    session_eval_site: ModuleType, tmp_path: Path,
) -> None:
    artifact = tmp_path / "drafts" / "hero_v1.html"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(_WELL_FORMED_HERO)
    failures = session_eval_site.structural_gate("full", artifact, tmp_path)
    assert failures == [], f"unexpected: {failures}"


def test_structural_gate_rejects_missing_frontmatter(
    session_eval_site: ModuleType, tmp_path: Path,
) -> None:
    artifact = tmp_path / "drafts" / "bad.html"
    artifact.parent.mkdir(parents=True)
    artifact.write_text('<section><h1>Title</h1></section>')
    failures = session_eval_site.structural_gate("full", artifact, tmp_path)
    assert any("frontmatter" in f.lower() for f in failures)


def test_structural_gate_rejects_unknown_section(
    session_eval_site: ModuleType, tmp_path: Path,
) -> None:
    body = _WELL_FORMED_HERO.replace("section: hero", "section: full_page")
    artifact = tmp_path / "drafts" / "bad.html"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(body)
    failures = session_eval_site.structural_gate("full", artifact, tmp_path)
    assert any("section=" in f for f in failures)


def test_structural_gate_rejects_full_page_rewrite(
    session_eval_site: ModuleType, tmp_path: Path,
) -> None:
    """v1 scope: section-level only. Multiple <section> tags fail."""
    body = (
        '<!-- frontmatter:\nvariant_id: x\nsection: hero\n'
        'voice_persona: jr\nbrand_tokens_path: x\n-->\n'
        '<section><h1>H1a</h1></section>\n'
        '<section><h1>H1b</h1></section>\n'
    )
    artifact = tmp_path / "drafts" / "bad.html"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(body)
    failures = session_eval_site.structural_gate("full", artifact, tmp_path)
    assert any("full-page" in f.lower() for f in failures)


def test_structural_gate_rejects_script_tag(
    session_eval_site: ModuleType, tmp_path: Path,
) -> None:
    """Pass-1 sanitizer strips <script>; structural gate fails."""
    body = _WELL_FORMED_HERO.replace(
        '<a href=', '<script>alert(1)</script><a href=',
    )
    artifact = tmp_path / "drafts" / "bad.html"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(body)
    failures = session_eval_site.structural_gate("full", artifact, tmp_path)
    assert any("sanitizer" in f.lower() for f in failures)


def test_structural_gate_rejects_missing_h1_in_hero(
    session_eval_site: ModuleType, tmp_path: Path,
) -> None:
    body = _WELL_FORMED_HERO.replace(
        '<h1 data-element="h1">Ship campaigns 3x faster with proven tooling</h1>', "",
    )
    artifact = tmp_path / "drafts" / "bad.html"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(body)
    failures = session_eval_site.structural_gate("full", artifact, tmp_path)
    assert any("h1" in f.lower() and "missing" in f.lower() for f in failures)


def test_structural_gate_rejects_missing_primary_cta(
    session_eval_site: ModuleType, tmp_path: Path,
) -> None:
    body = _WELL_FORMED_HERO.replace(
        'data-element="primary_cta" class="primary-cta"', '',
    )
    artifact = tmp_path / "drafts" / "bad.html"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(body)
    failures = session_eval_site.structural_gate("full", artifact, tmp_path)
    assert any("primary_cta" in f for f in failures)


# ---------------------------------------------------------------------------
# Lane registry wiring
# ---------------------------------------------------------------------------


def test_lane_registry_site_engine_has_11_rubric_ids() -> None:
    """8 SE + 3 compliance per U15b."""
    from autoresearch.lane_registry import LANES
    spec = LANES["site_engine"]
    assert len(spec.rubric_ids) == 11
    assert all(rid.startswith("SE-") for rid in spec.rubric_ids[:8])
    assert "gdpr_eu_site_engine_compliance" in spec.rubric_ids
    assert "medical_pl_site_engine_compliance" in spec.rubric_ids
    assert "legal_pl_site_engine_compliance" in spec.rubric_ids


def test_lane_registry_site_engine_inner_codex_default() -> None:
    """Plan §judge wiring: default inner = codex/gpt-5.5 (codex_fallback
    flips to claude/sonnet at config-time for clients that need it)."""
    from autoresearch.lane_registry import LANES
    spec = LANES["site_engine"]
    assert spec.inner_backend == "codex"
    assert spec.inner_model == "gpt-5.5"


# ---------------------------------------------------------------------------
# Rubric prose resolution
# ---------------------------------------------------------------------------


def test_se_rubrics_resolve_prose_from_site_quality_md() -> None:
    """SE-1..SE-8 prose_ref points to docs/rubrics/site-quality.md
    anchors; resolve_prose loads from there at eval time."""
    from src.evaluation.rubrics import RUBRICS, resolve_prose
    for n in range(1, 9):
        rid = f"SE-{n}"
        template = RUBRICS[rid]
        assert template.prose_ref is not None
        assert "site-quality.md" in template.prose_ref
        resolved = resolve_prose(template)
        # The resolved prose should be substantial (not the stub) and
        # mention the rubric.
        assert len(resolved) > 100, f"{rid} prose resolved to <100 chars"


def test_vision_judge_handles_se_rubrics() -> None:
    """vision_judge accepts SE-1, SE-5, SE-8 as visual rubrics."""
    from src.evaluation.vision_judge import VISUAL_RUBRIC_IDS
    assert "SE-1" in VISUAL_RUBRIC_IDS
    assert "SE-5" in VISUAL_RUBRIC_IDS
    assert "SE-8" in VISUAL_RUBRIC_IDS
