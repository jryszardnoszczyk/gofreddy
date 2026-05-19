"""U11 — linkedin_engine voice persona migration (R20 / TD-19).

Direct cutover from per-lane `programs/references/voice.md` to the shared
`VoicePersona` spec resolved via `LINKEDIN_ENGINE_VOICE_PERSONA_REF`.

Test scope:
- configure_env fail-loud when env var missing (no toggle per TD-19)
- configure_env fail-loud when persona resolves to empty corpus
- configure_env compiles persona corpus + writes to runtime voice.md
- Compile produces bit-identical output to pre-U11 voice.md for the
  default `jr` persona (single corpus file, no rules/anchors) → D10
  regression bar is structurally satisfied for the JR-default case
- Compile concatenates multi-corpus + appends rules + anchors for the
  multi-file persona case (Klinika / DWF shape)
- jr persona YAML loads + has corpus pointing at tracked substrate
- LaneSpec readonly_subprefixes still covers the legacy voice.md path
  (x_engine pre-U12 still reads it; meta-agent shouldn't mutate)

Imports use importlib because the canonical source path
`autoresearch/archive/v007-curated/workflows/linkedin_engine.py`
contains a hyphen that blocks normal `import` syntax.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_LINKEDIN_ENGINE_PATH = (
    _REPO_ROOT
    / "autoresearch"
    / "archive"
    / "v007-curated"
    / "workflows"
    / "linkedin_engine.py"
)


# ---------------------------------------------------------------------------
# Module loader — works around the v007-curated hyphen
# ---------------------------------------------------------------------------


def _load_linkedin_engine() -> ModuleType:
    """Load the canonical linkedin_engine workflow module by file path.

    The package path contains a hyphen (`v007-curated`) which blocks
    `import autoresearch.archive.v007-curated...`. We bypass that by
    loading directly via `importlib.util.spec_from_file_location` with
    the file's relative imports temporarily resolved by registering the
    parent package in sys.modules.

    Returns a freshly loaded module so prior-test env state cannot leak
    into module-level state.
    """
    # The lane module uses `from .eval_cache import ...` and
    # `from .specs import ...`. Register a parent package whose
    # __path__ points at the v007-curated/workflows dir so the relative
    # imports resolve.
    workflows_dir = _LINKEDIN_ENGINE_PATH.parent
    parent_pkg_name = "_le_v11_test_workflows"
    if parent_pkg_name not in sys.modules:
        parent_pkg = ModuleType(parent_pkg_name)
        parent_pkg.__path__ = [str(workflows_dir)]  # type: ignore[attr-defined]
        sys.modules[parent_pkg_name] = parent_pkg

    module_name = f"{parent_pkg_name}.linkedin_engine_under_test"
    spec = importlib.util.spec_from_file_location(
        module_name, _LINKEDIN_ENGINE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load spec for {_LINKEDIN_ENGINE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def linkedin_engine() -> ModuleType:
    """Fresh linkedin_engine module + ensure src/ is on sys.path so the
    lazy import of src.voice.persona resolves inside configure_env."""
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    return _load_linkedin_engine()


@pytest.fixture(autouse=True)
def _reset_linkedin_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clear linkedin env vars between tests."""
    for key in (
        "LINKEDIN_ENGINE_VOICE_PERSONA_REF",
        "LINKEDIN_ENGINE_ANGLE_ID",
        "LINKEDIN_ENGINE_SESSION_DIR",
        "AUTORESEARCH_CONTEXT",
        "AUTORESEARCH_SESSION_DIR",
    ):
        monkeypatch.delenv(key, raising=False)


# ---------------------------------------------------------------------------
# configure_env fail-loud paths (TD-19 — no toggle)
# ---------------------------------------------------------------------------


def test_configure_env_fails_loud_when_persona_ref_missing(
    linkedin_engine: ModuleType,
) -> None:
    """Per TD-19: no toggle, no silent fallback. Missing env var must
    raise so the operator can't accidentally run the lane without an
    assigned persona."""
    with pytest.raises(RuntimeError) as exc:
        linkedin_engine.configure_env("test-client")
    msg = str(exc.value)
    assert "LINKEDIN_ENGINE_VOICE_PERSONA_REF" in msg
    assert "U11" in msg or "TD-19" in msg


def test_configure_env_fails_loud_when_persona_yaml_missing(
    linkedin_engine: ModuleType, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Per U11 error path: nonexistent persona slug → fail loud naming
    the missing file (delegated to load_persona's
    VoicePersonaNotFoundError)."""
    from src.voice.persona import VoicePersonaNotFoundError
    monkeypatch.setenv(
        "LINKEDIN_ENGINE_VOICE_PERSONA_REF", "_definitely_not_a_persona_slug",
    )
    with pytest.raises(VoicePersonaNotFoundError) as exc:
        linkedin_engine.configure_env("test-client")
    assert "_definitely_not_a_persona_slug" in str(exc.value)


def test_configure_env_fails_loud_when_corpus_empty(
    linkedin_engine: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Per U11 error path: persona resolves but corpus is empty (e.g.,
    pre-consent state for regulated personas) → fail loud naming the
    persona + corpus path."""
    # Build a throwaway persona YAML pointing at an empty dir.
    corpus_dir = tmp_path / "empty_corpus"
    corpus_dir.mkdir()
    yaml_text = (
        "name: _u11_empty_test\n"
        f"corpus_path: {corpus_dir}\n"
        "voice_rules: []\n"
        "style_anchors: {}\n"
    )
    yaml_path = _REPO_ROOT / "voice_personas" / "_u11_empty_test.yaml"
    yaml_path.write_text(yaml_text)
    try:
        monkeypatch.setenv(
            "LINKEDIN_ENGINE_VOICE_PERSONA_REF", "_u11_empty_test",
        )
        with pytest.raises(RuntimeError) as exc:
            linkedin_engine.configure_env("test-client")
        msg = str(exc.value)
        assert "_u11_empty_test" in msg
        assert "empty corpus" in msg
    finally:
        yaml_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Happy path — jr persona produces voice.md substrate
# ---------------------------------------------------------------------------


def test_configure_env_writes_runtime_voice_for_jr_persona(
    linkedin_engine: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Happy path: jr persona resolves, corpus loads, compiled substrate
    lands at `<variant_root>/../current_runtime/programs/references/voice.md`."""
    # Redirect the variant root so the test writes into tmp_path, not
    # into the real archive tree.
    fake_variant = tmp_path / "v_test"
    fake_variant.mkdir()
    monkeypatch.setattr(linkedin_engine, "_VARIANT_ROOT", fake_variant)
    monkeypatch.setenv("LINKEDIN_ENGINE_VOICE_PERSONA_REF", "jr")

    linkedin_engine.configure_env("test-client")

    runtime_voice = (
        fake_variant.parent
        / "current_runtime"
        / "programs"
        / "references"
        / "voice.md"
    )
    assert runtime_voice.is_file(), "compiled substrate should land at runtime path"
    text = runtime_voice.read_text(encoding="utf-8")
    # The jr corpus's hard-floor section header must survive — it's the
    # X-2 / LI-2 rubric allowlist source.
    assert "Named lived-work entities" in text
    assert "gofreddy" in text


def test_configure_env_writes_are_bit_identical_to_legacy_voice_md(
    linkedin_engine: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """D10 regression bar: jr persona's compiled output must equal the
    pre-U11 static voice.md content (single corpus file, empty rules,
    empty anchors → corpus body verbatim).

    This is the structural-zero-regression guarantee — any non-default
    persona could regress fixtures, but the jr default cannot, because
    its compiled substrate IS the legacy file."""
    fake_variant = tmp_path / "v_test"
    fake_variant.mkdir()
    monkeypatch.setattr(linkedin_engine, "_VARIANT_ROOT", fake_variant)
    monkeypatch.setenv("LINKEDIN_ENGINE_VOICE_PERSONA_REF", "jr")

    linkedin_engine.configure_env("test-client")

    runtime_voice = (
        fake_variant.parent
        / "current_runtime"
        / "programs"
        / "references"
        / "voice.md"
    )
    compiled = runtime_voice.read_text(encoding="utf-8")
    legacy = (
        _REPO_ROOT
        / "autoresearch"
        / "archive"
        / "v007-curated"
        / "programs"
        / "references"
        / "voice.md"
    ).read_text(encoding="utf-8")
    assert compiled == legacy


def test_configure_env_propagates_angle_id(
    linkedin_engine: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Pre-U11 behavior preserved: AUTORESEARCH_CONTEXT bridges to
    LINKEDIN_ENGINE_ANGLE_ID for downstream consumers."""
    fake_variant = tmp_path / "v_test"
    fake_variant.mkdir()
    monkeypatch.setattr(linkedin_engine, "_VARIANT_ROOT", fake_variant)
    monkeypatch.setenv("LINKEDIN_ENGINE_VOICE_PERSONA_REF", "jr")
    monkeypatch.setenv("AUTORESEARCH_CONTEXT", "121")

    linkedin_engine.configure_env("test-client")

    assert os.environ["LINKEDIN_ENGINE_ANGLE_ID"] == "121"


def test_runtime_voice_is_writable_when_prior_file_was_locked(
    linkedin_engine: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Edge: prior session re-chmodded the runtime voice.md to 0444.
    Next session must still be able to overwrite it (the substrate
    re-compiles every session). Unlink-then-write covers this."""
    fake_variant = tmp_path / "v_test"
    fake_variant.mkdir()
    monkeypatch.setattr(linkedin_engine, "_VARIANT_ROOT", fake_variant)

    runtime_voice = (
        fake_variant.parent
        / "current_runtime"
        / "programs"
        / "references"
        / "voice.md"
    )
    runtime_voice.parent.mkdir(parents=True, exist_ok=True)
    runtime_voice.write_text("stale legacy content\n")
    import stat as _stat
    os.chmod(runtime_voice, _stat.S_IRUSR | _stat.S_IRGRP | _stat.S_IROTH)

    monkeypatch.setenv("LINKEDIN_ENGINE_VOICE_PERSONA_REF", "jr")
    linkedin_engine.configure_env("test-client")

    assert "stale legacy" not in runtime_voice.read_text(encoding="utf-8")
    assert "gofreddy" in runtime_voice.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# _compile_voice_substrate — multi-corpus + rules + anchors shape
# ---------------------------------------------------------------------------


def test_compile_substrate_single_file_no_rules_no_anchors_passes_through(
    linkedin_engine: ModuleType,
) -> None:
    """Single corpus file + empty rules + empty anchors → output is the
    corpus body verbatim. This is the contract that gives the jr
    default case bit-identical output."""
    from src.voice.persona import CorpusFile, VoicePersona

    persona = VoicePersona(
        persona_slug="t",
        corpus_path=Path("/tmp"),
        voice_rules=[],
        style_anchors={},
    )
    corpus = [CorpusFile(path=Path("/tmp/a.md"), text="just the body\n", format="markdown")]
    from src.voice.persona import compile_substrate
    out = compile_substrate(persona, corpus)
    assert out == "just the body\n"


def test_compile_substrate_concatenates_multiple_corpus_files(
    linkedin_engine: ModuleType,
) -> None:
    """Multi-file corpus → separator-joined body. Klinika / DWF shape."""
    from src.voice.persona import CorpusFile, VoicePersona

    persona = VoicePersona(
        persona_slug="t",
        corpus_path=Path("/tmp"),
        voice_rules=[],
        style_anchors={},
    )
    corpus = [
        CorpusFile(path=Path("/tmp/a.md"), text="first file body", format="markdown"),
        CorpusFile(path=Path("/tmp/b.md"), text="second file body", format="markdown"),
    ]
    from src.voice.persona import compile_substrate
    out = compile_substrate(persona, corpus)
    assert "first file body" in out
    assert "second file body" in out
    assert "---" in out  # separator


def test_compile_substrate_appends_rules_and_anchors(
    linkedin_engine: ModuleType,
) -> None:
    """Multi-attribute persona → corpus body + Voice Rules + Style
    Anchors sections concatenated in that order. Klinika / DWF case."""
    from src.voice.persona import CorpusFile, VoicePersona

    persona = VoicePersona(
        persona_slug="t",
        corpus_path=Path("/tmp"),
        voice_rules=["never claim a cure", "lead with mechanism"],
        style_anchors={"warmth": "warm but not effusive"},
    )
    corpus = [CorpusFile(path=Path("/tmp/a.md"), text="corpus body", format="markdown")]
    from src.voice.persona import compile_substrate
    out = compile_substrate(persona, corpus)
    assert out.startswith("corpus body")
    assert "## Voice Rules" in out
    assert "- never claim a cure" in out
    assert "- lead with mechanism" in out
    assert "## Style Anchors" in out
    assert "### warmth" in out
    assert "warm but not effusive" in out


# ---------------------------------------------------------------------------
# Persona YAML + substrate corpus shipped
# ---------------------------------------------------------------------------


def test_jr_persona_yaml_loads() -> None:
    """The shipped jr.yaml is valid + resolves to a non-empty corpus."""
    from src.voice.persona import load_corpus_files, load_persona

    persona = load_persona("jr")
    assert persona.persona_slug == "jr"
    corpus = load_corpus_files(persona)
    # At least one corpus file (the substrate copied from voice.md).
    assert len(corpus) >= 1
    assert any("gofreddy" in cf.text for cf in corpus), (
        "jr persona corpus should carry the gofreddy substrate prose"
    )


def test_jr_persona_corpus_matches_legacy_voice_md_byte_for_byte() -> None:
    """The jr persona corpus carries the exact pre-U11 voice.md content.
    This is the structural guarantee behind the D10 regression bar.

    If this test fails, the jr substrate has drifted from the legacy
    file — either edit the legacy file to match (preferred, single
    source of truth) or accept the drift and re-baseline the
    noise-floor doc (`docs/plans/2026-05-13-002-noise-floor-baselines.md`).
    """
    from src.voice.persona import load_corpus_files, load_persona

    persona = load_persona("jr")
    corpus = load_corpus_files(persona)
    assert len(corpus) == 1, (
        "jr persona should have exactly one corpus file pre-U12. "
        "If you've added a second file, the structural-zero-regression "
        "guarantee is broken — see noise-floor-baselines.md."
    )
    legacy = (
        _REPO_ROOT
        / "autoresearch"
        / "archive"
        / "v007-curated"
        / "programs"
        / "references"
        / "voice.md"
    ).read_text(encoding="utf-8")
    assert corpus[0].text == legacy


# ---------------------------------------------------------------------------
# LaneSpec wiring (readonly_subprefixes unchanged for U11)
# ---------------------------------------------------------------------------


def test_linkedin_lane_spec_unchanged_in_u11() -> None:
    """U11 deliberately does NOT modify linkedin_engine's
    path_prefixes or readonly_subprefixes — the legacy voice.md is
    still locked for x_engine consumption (x_engine migrates in U12).
    Verifies the lane's surface area didn't drift."""
    from autoresearch.lane_registry import LANES

    spec = LANES["linkedin_engine"]
    assert "programs/references/voice.md" in spec.readonly_subprefixes, (
        "voice.md must stay locked: x_engine still reads it pre-U12"
    )
    assert "programs/references/voice.md" in spec.path_prefixes
