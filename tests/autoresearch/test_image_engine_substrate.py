"""U14 — image_engine substrate (workflow + session_eval + structural gate).

Mirrors test_article_engine_substrate.py in module-loading shape — the
canonical workflow files live under `autoresearch/archive/v007-curated/...`
whose hyphen blocks normal imports. We load via importlib + synthetic
parent package.

Test scope:
- configure_env validation (topic / format / persona / brand_tokens_path)
- configure_env compiles voice substrate (mirrors U11/U12/U13)
- structural_gate per format (frontmatter, dimensions, slide count, anti-patterns load)
- LaneSpec wiring (inner=codex/gpt-5.5, 11 rubric_ids, structural_doc_facts)
- fal_image semaphore exists + sized from env
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


def _load_workflow_module(name: str) -> ModuleType:
    parent_pkg_name = "_ie_test_workflows"
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
def image_engine() -> ModuleType:
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    return _load_workflow_module("image_engine")


@pytest.fixture
def session_eval_image() -> ModuleType:
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    return _load_workflow_module("session_eval_image_engine")


@pytest.fixture(autouse=True)
def _reset_image_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "IMAGE_ENGINE_VOICE_PERSONA_REF",
        "IMAGE_ENGINE_TOPIC",
        "IMAGE_ENGINE_FORMAT",
        "IMAGE_ENGINE_BRAND_TOKENS_PATH",
        "IMAGE_ENGINE_BRIEFS_PATH",
        "IMAGE_ENGINE_ANGLE_ID",
        "IMAGE_ENGINE_SESSION_DIR",
        "AUTORESEARCH_CONTEXT",
        "AUTORESEARCH_SESSION_DIR",
        "FAL_IMAGE_MAX_CONCURRENCY",
    ):
        monkeypatch.delenv(key, raising=False)


# ---------------------------------------------------------------------------
# configure_env validation
# ---------------------------------------------------------------------------


def test_configure_env_fails_loud_missing_persona(image_engine: ModuleType) -> None:
    with pytest.raises(RuntimeError) as exc:
        image_engine.configure_env("test-client")
    assert "IMAGE_ENGINE_VOICE_PERSONA_REF" in str(exc.value)


def test_configure_env_fails_loud_missing_topic(
    image_engine: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    fake = tmp_path / "v_test"
    fake.mkdir()
    monkeypatch.setattr(image_engine, "_VARIANT_ROOT", fake)
    monkeypatch.setenv("IMAGE_ENGINE_VOICE_PERSONA_REF", "jr")
    with pytest.raises(RuntimeError) as exc:
        image_engine.configure_env("test-client")
    assert "IMAGE_ENGINE_TOPIC" in str(exc.value)


def test_configure_env_fails_loud_missing_format(
    image_engine: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    fake = tmp_path / "v_test"
    fake.mkdir()
    monkeypatch.setattr(image_engine, "_VARIANT_ROOT", fake)
    monkeypatch.setenv("IMAGE_ENGINE_VOICE_PERSONA_REF", "jr")
    monkeypatch.setenv("IMAGE_ENGINE_TOPIC", "t")
    with pytest.raises(RuntimeError) as exc:
        image_engine.configure_env("test-client")
    assert "IMAGE_ENGINE_FORMAT" in str(exc.value)


def test_configure_env_rejects_unknown_format(
    image_engine: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    fake = tmp_path / "v_test"
    fake.mkdir()
    monkeypatch.setattr(image_engine, "_VARIANT_ROOT", fake)
    monkeypatch.setenv("IMAGE_ENGINE_VOICE_PERSONA_REF", "jr")
    monkeypatch.setenv("IMAGE_ENGINE_TOPIC", "t")
    monkeypatch.setenv("IMAGE_ENGINE_FORMAT", "tiktok_video")
    with pytest.raises(RuntimeError) as exc:
        image_engine.configure_env("test-client")
    assert "tiktok_video" in str(exc.value)


def test_configure_env_fails_loud_missing_brand_tokens(
    image_engine: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    fake = tmp_path / "v_test"
    fake.mkdir()
    monkeypatch.setattr(image_engine, "_VARIANT_ROOT", fake)
    monkeypatch.setenv("IMAGE_ENGINE_VOICE_PERSONA_REF", "jr")
    monkeypatch.setenv("IMAGE_ENGINE_TOPIC", "t")
    monkeypatch.setenv("IMAGE_ENGINE_FORMAT", "ig_single")
    with pytest.raises(RuntimeError) as exc:
        image_engine.configure_env("test-client")
    assert "IMAGE_ENGINE_BRAND_TOKENS_PATH" in str(exc.value)


def test_configure_env_happy_path_writes_substrate(
    image_engine: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    fake = tmp_path / "v_test"
    fake.mkdir()
    monkeypatch.setattr(image_engine, "_VARIANT_ROOT", fake)
    monkeypatch.setenv("IMAGE_ENGINE_VOICE_PERSONA_REF", "jr")
    monkeypatch.setenv("IMAGE_ENGINE_TOPIC", "Botox aftercare")
    monkeypatch.setenv("IMAGE_ENGINE_FORMAT", "ig_carousel")
    monkeypatch.setenv(
        "IMAGE_ENGINE_BRAND_TOKENS_PATH",
        "clients/klinika-melitus/brand/palette.json",
    )

    image_engine.configure_env("test-client")

    runtime_voice = (
        fake.parent / "current_runtime"
        / "programs" / "references" / "voice.md"
    )
    assert runtime_voice.is_file()


def test_configure_env_allowed_formats_complete(image_engine: ModuleType) -> None:
    """All 6 formats per JR's 2026-05-19 U14 decision (full v1 scope)."""
    assert image_engine.ALLOWED_FORMATS == frozenset({
        "ig_single", "ig_carousel", "ig_story",
        "li_doc_carousel", "hero_banner", "ad_static",
    })


# ---------------------------------------------------------------------------
# structural_gate
# ---------------------------------------------------------------------------


def _write_single_image_with_meta(
    tmp_path: Path, format: str, dimensions: tuple[int, int],
) -> Path:
    """Build a single-image artifact + meta.json sibling."""
    from PIL import Image  # type: ignore[import-untyped]
    drafts = tmp_path / "drafts"
    drafts.mkdir(parents=True, exist_ok=True)
    artifact = drafts / "draft-001.png"
    img = Image.new("RGB", dimensions, color=(255, 255, 255))
    img.save(artifact)

    meta = drafts / "draft-001.meta.json"
    meta.write_text(json.dumps({
        "draft_id": "draft-001",
        "topic": "test topic",
        "format": format,
        "voice_persona": "jr",
        "brand_tokens_path": "clients/_stub_b2b_tech/brand/palette.json",
    }))
    return artifact


def test_structural_gate_passes_well_formed_ig_single(
    session_eval_image: ModuleType, tmp_path: Path,
) -> None:
    artifact = _write_single_image_with_meta(tmp_path, "ig_single", (1080, 1080))
    failures = session_eval_image.structural_gate("full", artifact, tmp_path)
    # Note: anti_patterns.yml load failure is expected here (variant
    # root not discoverable in tmp_path). Filter that out.
    real_failures = [f for f in failures if "anti_patterns.yml" not in f]
    assert real_failures == [], f"unexpected failures: {real_failures}"


def test_structural_gate_rejects_missing_meta(
    session_eval_image: ModuleType, tmp_path: Path,
) -> None:
    from PIL import Image  # type: ignore[import-untyped]
    drafts = tmp_path / "drafts"
    drafts.mkdir(parents=True)
    artifact = drafts / "draft-001.png"
    Image.new("RGB", (1080, 1080)).save(artifact)
    # No meta.json sidecar
    failures = session_eval_image.structural_gate("full", artifact, tmp_path)
    assert any("meta.json" in f for f in failures)


def test_structural_gate_rejects_unknown_format(
    session_eval_image: ModuleType, tmp_path: Path,
) -> None:
    artifact = _write_single_image_with_meta(tmp_path, "tiktok_video", (1080, 1080))
    failures = session_eval_image.structural_gate("full", artifact, tmp_path)
    assert any("format=" in f for f in failures)


def test_structural_gate_rejects_wrong_single_image_dimensions(
    session_eval_image: ModuleType, tmp_path: Path,
) -> None:
    """ig_single must be 1080x1080. Off-size = structural fail."""
    artifact = _write_single_image_with_meta(tmp_path, "ig_single", (800, 800))
    failures = session_eval_image.structural_gate("full", artifact, tmp_path)
    assert any("dimensions" in f for f in failures)


def test_structural_gate_rejects_carousel_as_single_file(
    session_eval_image: ModuleType, tmp_path: Path,
) -> None:
    """ig_carousel must be a directory, not a single file."""
    artifact = _write_single_image_with_meta(tmp_path, "ig_carousel", (1080, 1080))
    failures = session_eval_image.structural_gate("full", artifact, tmp_path)
    assert any("carousel" in f.lower() for f in failures)


def test_structural_gate_rejects_carousel_with_too_few_slides(
    session_eval_image: ModuleType, tmp_path: Path,
) -> None:
    """ig_carousel hard-fails outside [5, 10]."""
    from PIL import Image  # type: ignore[import-untyped]
    drafts = tmp_path / "drafts" / "carousel-001"
    drafts.mkdir(parents=True)
    for i in range(3):  # only 3 slides
        Image.new("RGB", (1080, 1080)).save(drafts / f"slide_{i:02d}.png")
    (drafts / "meta.json").write_text(json.dumps({
        "draft_id": "carousel-001",
        "topic": "t",
        "format": "ig_carousel",
        "voice_persona": "jr",
        "brand_tokens_path": "tokens.json",
    }))
    failures = session_eval_image.structural_gate("full", drafts, tmp_path)
    assert any("slide count" in f.lower() for f in failures)


def test_structural_gate_passes_well_formed_carousel(
    session_eval_image: ModuleType, tmp_path: Path,
) -> None:
    """ig_carousel with 5 slides at 1080×1080 passes."""
    from PIL import Image  # type: ignore[import-untyped]
    drafts = tmp_path / "drafts" / "carousel-001"
    drafts.mkdir(parents=True)
    for i in range(5):
        Image.new("RGB", (1080, 1080)).save(drafts / f"slide_{i:02d}.png")
    (drafts / "meta.json").write_text(json.dumps({
        "draft_id": "carousel-001",
        "topic": "t",
        "format": "ig_carousel",
        "voice_persona": "jr",
        "brand_tokens_path": "tokens.json",
    }))
    failures = session_eval_image.structural_gate("full", drafts, tmp_path)
    real_failures = [f for f in failures if "anti_patterns.yml" not in f]
    assert real_failures == [], f"unexpected: {real_failures}"


# ---------------------------------------------------------------------------
# Lane registry wiring
# ---------------------------------------------------------------------------


def test_lane_registry_image_engine_inner_pinned_to_codex() -> None:
    from autoresearch.lane_registry import LANES
    spec = LANES["image_engine"]
    assert spec.inner_backend == "codex"
    assert spec.inner_model == "gpt-5.5"


def test_lane_registry_image_engine_has_11_rubric_ids() -> None:
    """8 IE + 3 compliance per U14."""
    from autoresearch.lane_registry import LANES
    spec = LANES["image_engine"]
    assert len(spec.rubric_ids) == 11
    assert all(rid.startswith("IE-") for rid in spec.rubric_ids[:8])
    assert "gdpr_eu_image_engine_compliance" in spec.rubric_ids
    assert "medical_pl_image_engine_compliance" in spec.rubric_ids
    assert "legal_pl_image_engine_compliance" in spec.rubric_ids


# ---------------------------------------------------------------------------
# fal_image semaphore (D23)
# ---------------------------------------------------------------------------


def test_fal_image_semaphore_default() -> None:
    """Default cap is 2 (matches fal free-tier shape per concurrency.py)."""
    from autoresearch import concurrency
    concurrency._reset_for_test()
    sem = concurrency.fal_image_semaphore()
    # Default cap = 2; can acquire twice without blocking.
    acquired = []
    for _ in range(2):
        if sem.acquire(blocking=False):
            acquired.append(True)
        else:
            acquired.append(False)
    assert acquired == [True, True]
    # Third immediate acquire fails (already at cap).
    assert sem.acquire(blocking=False) is False
    for _ in range(2):
        sem.release()


def test_fal_image_semaphore_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """FAL_IMAGE_MAX_CONCURRENCY env var sizes the semaphore."""
    from autoresearch import concurrency
    concurrency._reset_for_test()
    monkeypatch.setenv("FAL_IMAGE_MAX_CONCURRENCY", "4")
    sem = concurrency.fal_image_semaphore()
    acquired = sum(1 for _ in range(4) if sem.acquire(blocking=False))
    assert acquired == 4
    for _ in range(4):
        sem.release()
