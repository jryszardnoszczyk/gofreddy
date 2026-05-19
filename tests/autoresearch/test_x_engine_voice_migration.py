"""U12 — x_engine voice persona migration (R20 / TD-19).

Mirror of U11 for the x_engine lane. Direct cutover from per-lane
`programs/references/voice.md` to the shared `VoicePersona` spec
resolved via `X_ENGINE_VOICE_PERSONA_REF`. The compile helper now lives
at `src.voice.persona.compile_substrate` (factored out of
linkedin_engine in this commit).

Test scope:
- configure_env fail-loud when env var missing (no toggle per TD-19)
- configure_env fail-loud when persona resolves to empty corpus
- configure_env fail-loud when persona YAML is missing
- configure_env compiles persona corpus + writes to runtime voice.md
- Compile produces bit-identical output to pre-U12 voice.md for the
  default `jr` persona — D10 regression bar is structurally satisfied
- Re-write works when prior runtime voice.md was locked 0444

Imports use importlib because the canonical source path
`autoresearch/archive/v007-curated/workflows/x_engine.py` contains a
hyphen that blocks normal `import` syntax.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_X_ENGINE_PATH = (
    _REPO_ROOT
    / "autoresearch"
    / "archive"
    / "v007-curated"
    / "workflows"
    / "x_engine.py"
)


# ---------------------------------------------------------------------------
# Module loader — works around the v007-curated hyphen
# ---------------------------------------------------------------------------


def _load_x_engine() -> ModuleType:
    """Load the canonical x_engine workflow module by file path.

    Same workaround as test_linkedin_engine_voice_migration: the
    package path's hyphen blocks normal imports, and the lane's
    relative imports (`.eval_cache`, `.specs`) require a parent
    package whose __path__ points at the workflows directory.
    """
    workflows_dir = _X_ENGINE_PATH.parent
    parent_pkg_name = "_xe_v12_test_workflows"
    if parent_pkg_name not in sys.modules:
        parent_pkg = ModuleType(parent_pkg_name)
        parent_pkg.__path__ = [str(workflows_dir)]  # type: ignore[attr-defined]
        sys.modules[parent_pkg_name] = parent_pkg

    module_name = f"{parent_pkg_name}.x_engine_under_test"
    spec = importlib.util.spec_from_file_location(
        module_name, _X_ENGINE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load spec for {_X_ENGINE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def x_engine() -> ModuleType:
    """Fresh x_engine module + ensure src/ is on sys.path so the
    lazy import of src.voice.persona resolves inside configure_env."""
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    return _load_x_engine()


@pytest.fixture(autouse=True)
def _reset_x_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clear x_engine env vars between tests."""
    for key in (
        "X_ENGINE_VOICE_PERSONA_REF",
        "X_ENGINE_ANGLE_ID",
        "X_ENGINE_SESSION_DIR",
        "AUTORESEARCH_CONTEXT",
        "AUTORESEARCH_SESSION_DIR",
    ):
        monkeypatch.delenv(key, raising=False)


# ---------------------------------------------------------------------------
# configure_env fail-loud paths (TD-19 — no toggle)
# ---------------------------------------------------------------------------


def test_configure_env_fails_loud_when_persona_ref_missing(
    x_engine: ModuleType,
) -> None:
    """Per TD-19: no toggle, no silent fallback."""
    with pytest.raises(RuntimeError) as exc:
        x_engine.configure_env("test-client")
    msg = str(exc.value)
    assert "X_ENGINE_VOICE_PERSONA_REF" in msg
    assert "U12" in msg or "TD-19" in msg


def test_configure_env_fails_loud_when_persona_yaml_missing(
    x_engine: ModuleType, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Nonexistent persona slug → VoicePersonaNotFoundError surfaces."""
    from src.voice.persona import VoicePersonaNotFoundError
    monkeypatch.setenv(
        "X_ENGINE_VOICE_PERSONA_REF", "_definitely_not_a_persona_slug",
    )
    with pytest.raises(VoicePersonaNotFoundError) as exc:
        x_engine.configure_env("test-client")
    assert "_definitely_not_a_persona_slug" in str(exc.value)


def test_configure_env_fails_loud_when_corpus_empty(
    x_engine: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Empty corpus → fail loud naming the persona + corpus path."""
    corpus_dir = tmp_path / "empty_corpus"
    corpus_dir.mkdir()
    yaml_text = (
        "name: _u12_empty_test\n"
        f"corpus_path: {corpus_dir}\n"
        "voice_rules: []\n"
        "style_anchors: {}\n"
    )
    yaml_path = _REPO_ROOT / "voice_personas" / "_u12_empty_test.yaml"
    yaml_path.write_text(yaml_text)
    try:
        monkeypatch.setenv("X_ENGINE_VOICE_PERSONA_REF", "_u12_empty_test")
        with pytest.raises(RuntimeError) as exc:
            x_engine.configure_env("test-client")
        msg = str(exc.value)
        assert "_u12_empty_test" in msg
        assert "empty corpus" in msg
    finally:
        yaml_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Happy path — jr persona produces voice.md substrate
# ---------------------------------------------------------------------------


def test_configure_env_writes_runtime_voice_for_jr_persona(
    x_engine: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Happy path: jr persona resolves, corpus loads, compiled substrate
    lands at the expected runtime path."""
    fake_variant = tmp_path / "v_test"
    fake_variant.mkdir()
    monkeypatch.setattr(x_engine, "_VARIANT_ROOT", fake_variant)
    monkeypatch.setenv("X_ENGINE_VOICE_PERSONA_REF", "jr")

    x_engine.configure_env("test-client")

    runtime_voice = (
        fake_variant.parent
        / "current_runtime"
        / "programs"
        / "references"
        / "voice.md"
    )
    assert runtime_voice.is_file()
    text = runtime_voice.read_text(encoding="utf-8")
    assert "Named lived-work entities" in text
    assert "gofreddy" in text


def test_configure_env_writes_are_bit_identical_to_legacy_voice_md(
    x_engine: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """D10 regression bar: jr persona's compiled output must equal the
    pre-U12 static voice.md content (single corpus file, empty rules,
    empty anchors → corpus body verbatim)."""
    fake_variant = tmp_path / "v_test"
    fake_variant.mkdir()
    monkeypatch.setattr(x_engine, "_VARIANT_ROOT", fake_variant)
    monkeypatch.setenv("X_ENGINE_VOICE_PERSONA_REF", "jr")

    x_engine.configure_env("test-client")

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
    x_engine: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Pre-U12 behavior preserved: AUTORESEARCH_CONTEXT bridges to
    X_ENGINE_ANGLE_ID for downstream consumers."""
    fake_variant = tmp_path / "v_test"
    fake_variant.mkdir()
    monkeypatch.setattr(x_engine, "_VARIANT_ROOT", fake_variant)
    monkeypatch.setenv("X_ENGINE_VOICE_PERSONA_REF", "jr")
    monkeypatch.setenv("AUTORESEARCH_CONTEXT", "122")

    x_engine.configure_env("test-client")

    assert os.environ["X_ENGINE_ANGLE_ID"] == "122"


def test_runtime_voice_is_writable_when_prior_file_was_locked(
    x_engine: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Edge: prior session locked the runtime voice.md to 0444 — next
    session must still be able to overwrite (unlink-then-write)."""
    fake_variant = tmp_path / "v_test"
    fake_variant.mkdir()
    monkeypatch.setattr(x_engine, "_VARIANT_ROOT", fake_variant)

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

    monkeypatch.setenv("X_ENGINE_VOICE_PERSONA_REF", "jr")
    x_engine.configure_env("test-client")

    text = runtime_voice.read_text(encoding="utf-8")
    assert "stale legacy" not in text
    assert "gofreddy" in text


# ---------------------------------------------------------------------------
# Symmetry: linkedin + x land at the SAME runtime voice.md (commute, since
# both compile from the same persona to the same path)
# ---------------------------------------------------------------------------


def test_x_engine_and_linkedin_engine_write_to_same_runtime_voice(
    x_engine: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Both lanes write the compiled substrate to the same runtime
    voice.md path. With the SAME persona slug the write commutes
    (last-writer-wins with identical content). The original pre-U11
    code relied on this commute; U11+U12 preserve it because the
    compile output for a given persona is deterministic.
    """
    from tests.autoresearch.test_linkedin_engine_voice_migration import (
        _load_linkedin_engine,
    )

    fake_variant = tmp_path / "v_test"
    fake_variant.mkdir()

    linkedin_engine = _load_linkedin_engine()
    monkeypatch.setattr(x_engine, "_VARIANT_ROOT", fake_variant)
    monkeypatch.setattr(linkedin_engine, "_VARIANT_ROOT", fake_variant)

    monkeypatch.setenv("X_ENGINE_VOICE_PERSONA_REF", "jr")
    monkeypatch.setenv("LINKEDIN_ENGINE_VOICE_PERSONA_REF", "jr")

    x_engine.configure_env("test-client")
    x_text = (
        fake_variant.parent / "current_runtime"
        / "programs" / "references" / "voice.md"
    ).read_text(encoding="utf-8")

    linkedin_engine.configure_env("test-client")
    li_text = (
        fake_variant.parent / "current_runtime"
        / "programs" / "references" / "voice.md"
    ).read_text(encoding="utf-8")

    assert x_text == li_text, "x+linkedin compile must agree for shared persona"
