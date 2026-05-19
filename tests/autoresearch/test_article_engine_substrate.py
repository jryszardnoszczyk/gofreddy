"""U13 — article_engine substrate (workflow + session_eval + structural gate).

Mirrors test_linkedin_engine_voice_migration / test_x_engine_voice_migration
in module-loading shape — the canonical workflow files live under
`autoresearch/archive/v007-curated/...` whose hyphen blocks normal
imports. We load via importlib + a synthetic parent package.

Test scope:
- configure_env env-var validation (topic / persona / platforms)
- configure_env compiles voice substrate (same pattern as U11/U12)
- structural_gate accepts well-formed blog + linkedin_article drafts
- structural_gate rejects wrong platform / wrong length bracket /
  hard-cap violations / missing schema.org / LinkedIn fold violations
- citation anti-patterns flagged ("studies show" without [N])
- anti_patterns.yml regex pre-check fires
- AE-8 cross-cohort criterion glob configured correctly
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_WORKFLOWS_DIR = (
    _REPO_ROOT / "autoresearch" / "archive" / "v007-curated" / "workflows"
)


def _load_workflow_module(name: str) -> ModuleType:
    """Load a v007-curated workflow module by file path.

    Works around the v007-curated hyphen blocking normal imports.
    Registers a parent package whose __path__ points at the
    workflows dir so the lane module's relative imports resolve.
    """
    parent_pkg_name = "_ae_test_workflows"
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
def article_engine() -> ModuleType:
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    return _load_workflow_module("article_engine")


@pytest.fixture
def session_eval_article() -> ModuleType:
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    return _load_workflow_module("session_eval_article_engine")


@pytest.fixture(autouse=True)
def _reset_article_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clear article_engine env vars between tests."""
    for key in (
        "ARTICLE_ENGINE_VOICE_PERSONA_REF",
        "ARTICLE_ENGINE_TOPIC",
        "ARTICLE_ENGINE_TARGET_PLATFORMS",
        "ARTICLE_ENGINE_SOURCE_MATERIAL_PATHS",
        "ARTICLE_ENGINE_BRIEFS_PATH",
        "ARTICLE_ENGINE_ANGLE_ID",
        "ARTICLE_ENGINE_SESSION_DIR",
        "AUTORESEARCH_CONTEXT",
        "AUTORESEARCH_SESSION_DIR",
    ):
        monkeypatch.delenv(key, raising=False)


# ---------------------------------------------------------------------------
# configure_env validation
# ---------------------------------------------------------------------------


def test_configure_env_fails_loud_missing_persona_ref(
    article_engine: ModuleType,
) -> None:
    with pytest.raises(RuntimeError) as exc:
        article_engine.configure_env("test-client")
    assert "ARTICLE_ENGINE_VOICE_PERSONA_REF" in str(exc.value)
    assert "U13" in str(exc.value)


def test_configure_env_fails_loud_missing_topic(
    article_engine: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    fake_variant = tmp_path / "v_test"
    fake_variant.mkdir()
    monkeypatch.setattr(article_engine, "_VARIANT_ROOT", fake_variant)
    monkeypatch.setenv("ARTICLE_ENGINE_VOICE_PERSONA_REF", "jr")
    with pytest.raises(RuntimeError) as exc:
        article_engine.configure_env("test-client")
    assert "ARTICLE_ENGINE_TOPIC" in str(exc.value)


def test_configure_env_fails_loud_missing_platforms(
    article_engine: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    fake_variant = tmp_path / "v_test"
    fake_variant.mkdir()
    monkeypatch.setattr(article_engine, "_VARIANT_ROOT", fake_variant)
    monkeypatch.setenv("ARTICLE_ENGINE_VOICE_PERSONA_REF", "jr")
    monkeypatch.setenv("ARTICLE_ENGINE_TOPIC", "test topic")
    with pytest.raises(RuntimeError) as exc:
        article_engine.configure_env("test-client")
    assert "ARTICLE_ENGINE_TARGET_PLATFORMS" in str(exc.value)


def test_configure_env_rejects_unsupported_platform(
    article_engine: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    fake_variant = tmp_path / "v_test"
    fake_variant.mkdir()
    monkeypatch.setattr(article_engine, "_VARIANT_ROOT", fake_variant)
    monkeypatch.setenv("ARTICLE_ENGINE_VOICE_PERSONA_REF", "jr")
    monkeypatch.setenv("ARTICLE_ENGINE_TOPIC", "test topic")
    monkeypatch.setenv("ARTICLE_ENGINE_TARGET_PLATFORMS", "medium,substack")
    with pytest.raises(RuntimeError) as exc:
        article_engine.configure_env("test-client")
    assert "medium" in str(exc.value) or "substack" in str(exc.value)


def test_configure_env_happy_path_writes_substrate(
    article_engine: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """U13 happy path: all required env vars set → persona compiled +
    written to current_runtime + ANGLE_ID propagated."""
    fake_variant = tmp_path / "v_test"
    fake_variant.mkdir()
    monkeypatch.setattr(article_engine, "_VARIANT_ROOT", fake_variant)
    monkeypatch.setenv("ARTICLE_ENGINE_VOICE_PERSONA_REF", "jr")
    monkeypatch.setenv("ARTICLE_ENGINE_TOPIC", "KSeF e-invoicing")
    monkeypatch.setenv("ARTICLE_ENGINE_TARGET_PLATFORMS", "blog,linkedin_article")
    monkeypatch.setenv("AUTORESEARCH_CONTEXT", "121")

    article_engine.configure_env("test-client")

    runtime_voice = (
        fake_variant.parent / "current_runtime"
        / "programs" / "references" / "voice.md"
    )
    assert runtime_voice.is_file()
    assert "gofreddy" in runtime_voice.read_text(encoding="utf-8")
    assert os.environ.get("ARTICLE_ENGINE_ANGLE_ID") == "121"


# ---------------------------------------------------------------------------
# structural_gate — blog
# ---------------------------------------------------------------------------


def _well_formed_blog(word_count: int = 1800) -> str:
    """Build a minimum-passable blog draft. Word count tuneable."""
    body_words = " ".join(["test"] * word_count)
    return (
        "---\n"
        "draft_id: blog-001\n"
        "topic: KSeF e-invoicing for Polish SMBs\n"
        "platform: blog\n"
        "length_bracket: standard\n"
        "voice_persona: jr\n"
        f"word_count: {word_count}\n"
        "meta_description: A specific 140-to-160 character description that explains the article's thesis precisely to the reader landing from search engines and adds the right clarity.\n"
        "---\n\n"
        "# A specific testable claim about KSeF implementation\n\n"
        "## Context\n\n"
        f"{body_words}\n\n"
        "## Mechanism\n\n"
        "> **Hero image brief:** Architecture diagram showing KSeF flow.\n\n"
        "> **Inline image brief:** Spreadsheet screenshot.\n\n"
        "Some prose [1] backing the claim with a citation.\n\n"
        "## References\n\n"
        "[1] Polish Ministry of Finance, https://www.gov.pl/web/finanse/ksef\n\n"
        "```json\n"
        '{"@context":"https://schema.org","@type":"Article","headline":"A specific testable claim about KSeF implementation","author":"JR","datePublished":"2026-05-19","image":"https://example.com/hero.jpg"}\n'
        "```\n"
    )


def test_structural_gate_passes_well_formed_blog(
    session_eval_article: ModuleType, tmp_path: Path,
) -> None:
    artifact = tmp_path / "drafts" / "blog-001.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(_well_formed_blog())
    failures = session_eval_article.structural_gate(
        "full", artifact, tmp_path,
    )
    assert failures == [], f"unexpected failures: {failures}"


def test_structural_gate_rejects_missing_frontmatter(
    session_eval_article: ModuleType, tmp_path: Path,
) -> None:
    artifact = tmp_path / "drafts" / "bad.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("# headline\nbody body body")
    failures = session_eval_article.structural_gate(
        "full", artifact, tmp_path,
    )
    assert any("frontmatter" in f.lower() for f in failures)


def test_structural_gate_rejects_wrong_platform(
    session_eval_article: ModuleType, tmp_path: Path,
) -> None:
    artifact = tmp_path / "drafts" / "bad.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(
        "---\n"
        "draft_id: x\n"
        "topic: t\n"
        "platform: medium\n"
        "length_bracket: standard\n"
        "voice_persona: jr\n"
        "word_count: 1800\n"
        "---\n\n# h\n\nbody\n"
    )
    failures = session_eval_article.structural_gate(
        "full", artifact, tmp_path,
    )
    assert any("platform=" in f for f in failures)


def test_structural_gate_rejects_wrong_length_bracket_for_platform(
    session_eval_article: ModuleType, tmp_path: Path,
) -> None:
    """A blog draft with a linkedin_article-only bracket like `short`
    must fail."""
    artifact = tmp_path / "drafts" / "bad.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(
        "---\n"
        "draft_id: x\n"
        "topic: t\n"
        "platform: blog\n"
        "length_bracket: short\n"  # blog has no `short` bracket
        "voice_persona: jr\n"
        "word_count: 1800\n"
        "---\n\n# h\n\nbody\n"
    )
    failures = session_eval_article.structural_gate(
        "full", artifact, tmp_path,
    )
    assert any("length_bracket" in f for f in failures)


def test_structural_gate_rejects_word_count_outside_hard_caps(
    session_eval_article: ModuleType, tmp_path: Path,
) -> None:
    """Blog draft well below blog 800 min → structural fail."""
    artifact = tmp_path / "drafts" / "bad.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(
        "---\n"
        "draft_id: x\n"
        "topic: t\n"
        "platform: blog\n"
        "length_bracket: standard\n"
        "voice_persona: jr\n"
        "word_count: 200\n"
        "---\n\n# h\n\ntoo short body\n"
    )
    failures = session_eval_article.structural_gate(
        "full", artifact, tmp_path,
    )
    assert any("hard caps" in f for f in failures)


def test_structural_gate_rejects_blog_missing_h1(
    session_eval_article: ModuleType, tmp_path: Path,
) -> None:
    """Blog without an `# H1` line fails."""
    body = _well_formed_blog().replace(
        "# A specific testable claim about KSeF implementation",
        "(no h1 here)",
    )
    artifact = tmp_path / "drafts" / "bad.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(body)
    failures = session_eval_article.structural_gate(
        "full", artifact, tmp_path,
    )
    assert any("H1" in f for f in failures)


def test_structural_gate_rejects_blog_missing_schema_org(
    session_eval_article: ModuleType, tmp_path: Path,
) -> None:
    """Blog without schema.org Article JSON fails."""
    body = _well_formed_blog().replace("```json", "```yaml")
    artifact = tmp_path / "drafts" / "bad.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(body)
    failures = session_eval_article.structural_gate(
        "full", artifact, tmp_path,
    )
    assert any("schema.org" in f for f in failures)


# ---------------------------------------------------------------------------
# structural_gate — linkedin_article
# ---------------------------------------------------------------------------


def _well_formed_linkedin(word_count: int = 1400) -> str:
    """Build a passable LinkedIn Article draft."""
    body_words = " ".join(["test"] * word_count)
    return (
        "---\n"
        "draft_id: li-001\n"
        "topic: KSeF e-invoicing\n"
        "platform: linkedin_article\n"
        "length_bracket: short\n"
        "voice_persona: jr\n"
        f"word_count: {word_count}\n"
        "---\n\n"
        "A specific testable claim that holds in the first 210 characters of "
        "the body. Story-led, named entity from voice.md, falsifiable.\n\n"
        "**A bold pseudo-subhead**\n\n"
        f"{body_words}\n\n"
        "#KSeF #PolishTax #SMB #Compliance\n"
    )


def test_structural_gate_passes_well_formed_linkedin(
    session_eval_article: ModuleType, tmp_path: Path,
) -> None:
    artifact = tmp_path / "drafts" / "li-001.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(_well_formed_linkedin())
    failures = session_eval_article.structural_gate(
        "full", artifact, tmp_path,
    )
    assert failures == [], f"unexpected failures: {failures}"


def test_structural_gate_rejects_linkedin_with_markdown_header(
    session_eval_article: ModuleType, tmp_path: Path,
) -> None:
    """LinkedIn Article with `# Headline` on line 1 → structural fail
    (LI strips it)."""
    body = _well_formed_linkedin().replace(
        "A specific testable claim that holds",
        "# A markdown header here\n\nA specific testable claim that holds",
    )
    artifact = tmp_path / "drafts" / "bad.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(body)
    failures = session_eval_article.structural_gate(
        "full", artifact, tmp_path,
    )
    assert any("markdown" in f.lower() for f in failures)


def test_structural_gate_rejects_linkedin_wrong_hashtag_count(
    session_eval_article: ModuleType, tmp_path: Path,
) -> None:
    """LinkedIn Article with 1 hashtag or 7 hashtags → structural fail."""
    body = _well_formed_linkedin().replace(
        "#KSeF #PolishTax #SMB #Compliance", "#OnlyOne",
    )
    artifact = tmp_path / "drafts" / "bad.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(body)
    failures = session_eval_article.structural_gate(
        "full", artifact, tmp_path,
    )
    assert any("hashtag" in f.lower() for f in failures)


# ---------------------------------------------------------------------------
# Citation anti-patterns + anti_patterns.yml pre-check
# ---------------------------------------------------------------------------


def test_structural_gate_flags_studies_show_without_citation(
    session_eval_article: ModuleType, tmp_path: Path,
) -> None:
    """'studies show' without an inline [N] → AE-3 anti-pattern flagged."""
    body = _well_formed_blog().replace(
        "Some prose [1] backing the claim with a citation.",
        "Studies show that this approach works.",
    )
    artifact = tmp_path / "drafts" / "bad.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(body)
    failures = session_eval_article.structural_gate(
        "full", artifact, tmp_path,
    )
    assert any("AE-3" in f for f in failures)


def test_structural_gate_flags_anti_pattern_today_fast_paced(
    session_eval_article: ModuleType, tmp_path: Path,
) -> None:
    """Anti_patterns.yml regex match → flagged via the gate."""
    # The test must run from a context where the variant root is
    # discoverable. We simulate by creating a session_dir 3 levels
    # deep so session_dir.parents[2] = variant root.
    variant_root = tmp_path / "v007-curated"
    variant_root.mkdir()
    # Materialize anti_patterns.yml so the gate's anti-pattern check fires
    (variant_root / "templates" / "article_engine").mkdir(parents=True)
    (variant_root / "templates" / "article_engine" / "anti_patterns.yml").write_text(
        "patterns:\n"
        "  - name: today_fast_paced\n"
        "    regex: 'in today.?s fast-?paced world'\n"
        "    why: AI tell\n"
    )
    session_dir = variant_root / "sessions" / "article_engine" / "test-client"
    session_dir.mkdir(parents=True)
    artifact_body = _well_formed_blog().replace(
        "## Context",
        "## Context\n\nIn today's fast-paced world, things change quickly.",
    )
    artifact = session_dir / "drafts" / "blog.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(artifact_body)
    failures = session_eval_article.structural_gate(
        "full", artifact, session_dir,
    )
    assert any("anti_patterns" in f.lower() for f in failures)


# ---------------------------------------------------------------------------
# AE-8 cross-cohort criterion + LaneSpec integration
# ---------------------------------------------------------------------------


def test_session_eval_spec_has_cross_item_ae8(
    session_eval_article: ModuleType,
) -> None:
    spec = session_eval_article.SPEC
    assert "AE-8" in spec.cross_item_criteria
    assert spec.cross_item_criteria["AE-8"].glob == "drafts/*.md"


def test_lane_registry_article_engine_inner_pinned_to_codex() -> None:
    """U13 §judge wiring: inner statically pinned to codex/gpt-5.5
    per priority chain. CLI/env can still override per-invocation."""
    from autoresearch.lane_registry import LANES
    spec = LANES["article_engine"]
    assert spec.inner_backend == "codex"
    assert spec.inner_model == "gpt-5.5"


def test_lane_registry_article_engine_has_11_rubric_ids() -> None:
    """8 AE + 3 compliance rubric IDs."""
    from autoresearch.lane_registry import LANES
    spec = LANES["article_engine"]
    assert len(spec.rubric_ids) == 11
    assert all(rid.startswith("AE-") for rid in spec.rubric_ids[:8])
    assert spec.rubric_ids[8] == "gdpr_eu_article_engine_compliance"
    assert spec.rubric_ids[9] == "medical_pl_article_engine_compliance"
    assert spec.rubric_ids[10] == "legal_pl_article_engine_compliance"
