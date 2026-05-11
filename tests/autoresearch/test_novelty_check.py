"""Tests for Stream C C1 — novelty rejection.

Exercises:
- ``_cosine_similarity`` math (identical / orthogonal / zero / mismatched-dim)
- ``_gather_variant_text`` (sort stability, skip-list compliance)
- ``_ArchiveAdapter`` (compute_similarity + get_most_similar_program)
- ``check_novelty`` end-to-end with ``embed_text`` and lineage loader
  monkey-patched so tests stay offline.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from autoresearch import novelty_check as nc


# --- math helpers -----------------------------------------------------------


def test_cosine_similarity_identical_vectors():
    assert nc._cosine_similarity([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == pytest.approx(1.0)


def test_cosine_similarity_orthogonal_vectors():
    assert nc._cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0


def test_cosine_similarity_zero_vector_returns_zero():
    assert nc._cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0


def test_cosine_similarity_dimension_mismatch_returns_zero():
    assert nc._cosine_similarity([1.0, 2.0], [1.0, 2.0, 3.0]) == 0.0


def test_cosine_similarity_clipped_to_unit_range():
    """Antiparallel vectors yield -1; novelty use clips to [0,1] so
    negatives become 0 (treat-as-different) rather than confusing the
    downstream max()."""
    assert nc._cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == 0.0


# --- text gathering ---------------------------------------------------------


def test_gather_variant_text_picks_up_md_and_yaml(tmp_path: Path):
    (tmp_path / "a.md").write_text("alpha")
    (tmp_path / "b.yaml").write_text("key: val")
    (tmp_path / "ignore.png").write_bytes(b"\x89PNG")
    out = nc._gather_variant_text(tmp_path)
    assert "alpha" in out
    assert "key: val" in out
    assert "PNG" not in out


def test_gather_variant_text_skips_session_artifacts(tmp_path: Path):
    """Session output drifts with scoring noise — it must not be embedded,
    or sibling embeddings would track score noise rather than mutation."""
    (tmp_path / "lane.md").write_text("real content")
    (tmp_path / "sessions").mkdir()
    (tmp_path / "sessions" / "output.md").write_text("noisy run output")
    out = nc._gather_variant_text(tmp_path)
    assert "real content" in out
    assert "noisy run output" not in out


def test_gather_variant_text_is_sort_stable(tmp_path: Path):
    """Same source files in different filesystem-walk order must produce
    the same string (so the embedding cache key is stable)."""
    (tmp_path / "z.md").write_text("ZZZ")
    (tmp_path / "a.md").write_text("AAA")
    out1 = nc._gather_variant_text(tmp_path)
    out2 = nc._gather_variant_text(tmp_path)
    assert out1 == out2
    # alpha-sorted: a.md content appears before z.md content
    assert out1.index("AAA") < out1.index("ZZZ")


def test_gather_variant_text_missing_dir_returns_empty(tmp_path: Path):
    assert nc._gather_variant_text(tmp_path / "no_such") == ""


# --- adapter ----------------------------------------------------------------


def test_archive_adapter_returns_per_sibling_similarity():
    siblings = [
        ("v001", [1.0, 0.0, 0.0]),
        ("v002", [0.0, 1.0, 0.0]),
    ]
    adapter = nc._ArchiveAdapter(siblings)
    sims = adapter.compute_similarity([1.0, 0.0, 0.0])
    assert sims[0] == pytest.approx(1.0)
    assert sims[1] == 0.0


def test_archive_adapter_get_most_similar_picks_highest():
    siblings = [
        ("v001", [0.1, 0.9, 0.0]),
        ("v002", [1.0, 0.0, 0.0]),
    ]
    adapter = nc._ArchiveAdapter(siblings)
    best = adapter.get_most_similar_program([1.0, 0.0, 0.0])
    assert best is not None
    assert best.variant_id == "v002"


def test_archive_adapter_empty_siblings():
    adapter = nc._ArchiveAdapter([])
    assert adapter.compute_similarity([1.0, 0.0]) == []
    assert adapter.get_most_similar_program([1.0, 0.0]) is None


# --- check_novelty end-to-end ----------------------------------------------


@pytest.fixture
def stub_archive(tmp_path: Path, monkeypatch):
    """Build a stub archive with one parent and one sibling on lane=geo."""
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()
    # Parent
    (archive_dir / "v001").mkdir()
    (archive_dir / "v001" / "lane.md").write_text("parent prose")
    # Sibling
    (archive_dir / "v002").mkdir()
    (archive_dir / "v002" / "lane.md").write_text("sibling prose")
    # Candidate (under evaluation)
    (archive_dir / "v003").mkdir()
    (archive_dir / "v003" / "lane.md").write_text("candidate prose")

    fake_lineage = {
        "v001": {"id": "v001", "lane": "geo"},
        "v002": {"id": "v002", "lane": "geo"},
        "v003": {"id": "v003", "lane": "geo"},  # the candidate itself
        "v999": {"id": "v999", "lane": "competitive"},  # wrong lane, filtered out
    }
    monkeypatch.setattr(
        "autoresearch.archive_index.load_latest_lineage",
        lambda *a, **k: fake_lineage,
    )
    return archive_dir


def test_check_novelty_no_siblings_returns_novel(tmp_path: Path, monkeypatch):
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()
    (archive_dir / "v001").mkdir()
    (archive_dir / "v001" / "lane.md").write_text("first variant")
    monkeypatch.setattr(
        "autoresearch.archive_index.load_latest_lineage",
        lambda *a, **k: {"v001": {"id": "v001", "lane": "geo"}},
    )
    is_novel, meta = nc.check_novelty(
        variant_dir=archive_dir / "v001",
        parent_id="",
        lane="geo",
        archive_dir=archive_dir,
    )
    assert is_novel is True
    assert meta["sibling_count"] == 0


def test_check_novelty_empty_candidate_text_is_novel(tmp_path: Path, monkeypatch):
    """A variant with no embeddable source files (only binaries / sessions)
    can't be embedded; we accept-by-default rather than crash."""
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()
    (archive_dir / "v001").mkdir()
    (archive_dir / "v001" / "binary.png").write_bytes(b"\x89PNG")
    monkeypatch.setattr(
        "autoresearch.archive_index.load_latest_lineage",
        lambda *a, **k: {"v001": {"id": "v001", "lane": "geo"}},
    )
    is_novel, meta = nc.check_novelty(
        variant_dir=archive_dir / "v001",
        parent_id="v000",
        lane="geo",
        archive_dir=archive_dir,
    )
    assert is_novel is True
    assert "error" in meta


def test_check_novelty_identical_to_sibling_is_rejected(stub_archive, monkeypatch):
    """Headline behavior: candidate embedding == sibling embedding → reject."""
    # Same embedding for parent + sibling + candidate (all identical)
    monkeypatch.setattr(
        "autoresearch.novelty_check.embed_text",
        lambda text, **kwargs: [1.0, 0.0, 0.0],
    )
    is_novel, meta = nc.check_novelty(
        variant_dir=stub_archive / "v003",
        parent_id="v001",
        lane="geo",
        archive_dir=stub_archive,
        similarity_threshold=0.95,
    )
    assert is_novel is False
    assert meta["sibling_count"] == 2
    assert meta["max_similarity"] == pytest.approx(1.0)


def test_check_novelty_distinct_from_siblings_is_novel(stub_archive, monkeypatch):
    """Orthogonal embeddings → max similarity < threshold → accept."""
    def fake_embed(text: str, **kwargs) -> list[float]:
        # Return a different unit vector per text so siblings ≠ candidate.
        if "candidate" in text:
            return [1.0, 0.0, 0.0]
        if "sibling" in text:
            return [0.0, 1.0, 0.0]
        return [0.0, 0.0, 1.0]
    monkeypatch.setattr("autoresearch.novelty_check.embed_text", fake_embed)
    is_novel, meta = nc.check_novelty(
        variant_dir=stub_archive / "v003",
        parent_id="v001",
        lane="geo",
        archive_dir=stub_archive,
        similarity_threshold=0.95,
    )
    assert is_novel is True
    assert meta["sibling_count"] == 2
    assert meta["max_similarity"] == 0.0


def test_check_novelty_lane_filtering_excludes_other_lanes(stub_archive, monkeypatch):
    """v999 is on a different lane and must not contribute to similarity."""
    seen_paths: list[str] = []

    def tracking_embed(text: str, **kwargs) -> list[float]:
        seen_paths.append(text[:50])
        return [1.0, 0.0, 0.0]

    monkeypatch.setattr("autoresearch.novelty_check.embed_text", tracking_embed)
    nc.check_novelty(
        variant_dir=stub_archive / "v003",
        parent_id="v001",
        lane="geo",
        archive_dir=stub_archive,
    )
    # We embedded the candidate + the 2 same-lane siblings; v999 (other lane) skipped.
    assert len(seen_paths) == 3


def test_check_novelty_embedding_error_accepts_by_default(stub_archive, monkeypatch):
    """If OpenAI is unreachable, the evolve loop must not crash — accept."""
    def fail_embed(text: str, **kwargs) -> list[float]:
        raise nc.EmbeddingUnavailable("simulated outage")
    monkeypatch.setattr("autoresearch.novelty_check.embed_text", fail_embed)
    is_novel, meta = nc.check_novelty(
        variant_dir=stub_archive / "v003",
        parent_id="v001",
        lane="geo",
        archive_dir=stub_archive,
    )
    assert is_novel is True
    assert "error" in meta
