"""Tests for Stream C C1 — novelty rejection (Jaccard + codex tie-breaker).

Exercises:
- ``_shingles`` + ``_jaccard_similarity`` math
- ``_gather_variant_text`` (sort stability, skip-list compliance)
- ``_resolve_recent_siblings`` (lane-filtering, K-cap, most-recent-first)
- ``_parse_novelty_verdict`` (codex output parsing)
- ``check_novelty`` end-to-end with ``invoke_codex`` monkey-patched so
  tests stay offline. Verifies the auto-accept path (low Jaccard, no
  codex call), the tie-breaker path (high Jaccard → codex), and the
  accept-by-default failure modes.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from autoresearch import novelty_check as nc


# --- shingles + Jaccard ----------------------------------------------------


def test_shingles_basic():
    text = "the quick brown fox jumps over the lazy dog"
    shingles = nc._shingles(text, k=5)
    assert "the quick brown fox jumps" in shingles
    assert "quick brown fox jumps over" in shingles


def test_shingles_short_text_collapses_to_single_bucket():
    """Texts shorter than k words map to one shingle so they can still
    participate in similarity against another short text."""
    assert nc._shingles("hi there", k=5) == {"hi there"}


def test_shingles_empty_text_returns_empty_set():
    assert nc._shingles("", k=5) == set()


def test_jaccard_identical_sets():
    a = {"a b c", "b c d"}
    assert nc._jaccard_similarity(a, a) == 1.0


def test_jaccard_disjoint_sets():
    assert nc._jaccard_similarity({"a"}, {"b"}) == 0.0


def test_jaccard_partial_overlap():
    a = {"x", "y", "z"}
    b = {"y", "z", "w"}
    # intersection = {y, z}, union = {x, y, z, w}, jaccard = 2/4
    assert nc._jaccard_similarity(a, b) == 0.5


def test_jaccard_empty_set_returns_zero():
    assert nc._jaccard_similarity(set(), {"a"}) == 0.0


# --- text gathering --------------------------------------------------------


def test_gather_variant_text_picks_up_md_and_yaml(tmp_path: Path):
    (tmp_path / "a.md").write_text("alpha")
    (tmp_path / "b.yaml").write_text("key: val")
    (tmp_path / "ignore.png").write_bytes(b"\x89PNG")
    out = nc._gather_variant_text(tmp_path)
    assert "alpha" in out
    assert "key: val" in out
    assert "PNG" not in out


def test_gather_variant_text_skips_session_artifacts(tmp_path: Path):
    """Session output drifts with scoring noise — must not be included,
    or sibling similarity would track score noise instead of mutation."""
    (tmp_path / "lane.md").write_text("real content")
    (tmp_path / "sessions").mkdir()
    (tmp_path / "sessions" / "output.md").write_text("noisy run output")
    out = nc._gather_variant_text(tmp_path)
    assert "real content" in out
    assert "noisy run output" not in out


def test_gather_variant_text_is_sort_stable(tmp_path: Path):
    (tmp_path / "z.md").write_text("ZZZ")
    (tmp_path / "a.md").write_text("AAA")
    out1 = nc._gather_variant_text(tmp_path)
    out2 = nc._gather_variant_text(tmp_path)
    assert out1 == out2
    assert out1.index("AAA") < out1.index("ZZZ")


def test_gather_variant_text_missing_dir_returns_empty(tmp_path: Path):
    assert nc._gather_variant_text(tmp_path / "no_such") == ""


# --- _resolve_recent_siblings ----------------------------------------------


def test_resolve_recent_siblings_returns_most_recent_first(tmp_path, monkeypatch):
    """Lineage is chronological; reversed iteration gives most-recent first."""
    archive = tmp_path / "archive"
    archive.mkdir()
    for vid in ("v001", "v002", "v003"):
        (archive / vid).mkdir()

    monkeypatch.setattr(
        "autoresearch.archive_index.load_lineage_history",
        lambda *a, **k: [
            {"id": "v001", "lane": "geo"},
            {"id": "v002", "lane": "geo"},
            {"id": "v003", "lane": "geo"},
        ],
    )
    siblings = nc._resolve_recent_siblings(archive, "geo", exclude_id="v999", k=5)
    # Most-recent first → v003, v002, v001
    assert [sid for sid, _ in siblings] == ["v003", "v002", "v001"]


def test_resolve_recent_siblings_caps_at_k(tmp_path, monkeypatch):
    archive = tmp_path / "archive"
    archive.mkdir()
    for i in range(10):
        (archive / f"v{i:03d}").mkdir()
    monkeypatch.setattr(
        "autoresearch.archive_index.load_lineage_history",
        lambda *a, **k: [{"id": f"v{i:03d}", "lane": "geo"} for i in range(10)],
    )
    siblings = nc._resolve_recent_siblings(archive, "geo", exclude_id="x", k=3)
    assert len(siblings) == 3


def test_resolve_recent_siblings_filters_other_lanes(tmp_path, monkeypatch):
    archive = tmp_path / "archive"
    archive.mkdir()
    for vid in ("v001", "v002", "v003"):
        (archive / vid).mkdir()
    monkeypatch.setattr(
        "autoresearch.archive_index.load_lineage_history",
        lambda *a, **k: [
            {"id": "v001", "lane": "geo"},
            {"id": "v002", "lane": "competitive"},
            {"id": "v003", "lane": "geo"},
        ],
    )
    siblings = nc._resolve_recent_siblings(archive, "geo", exclude_id="x", k=5)
    assert [sid for sid, _ in siblings] == ["v003", "v001"]


def test_resolve_recent_siblings_excludes_self(tmp_path, monkeypatch):
    archive = tmp_path / "archive"
    archive.mkdir()
    for vid in ("v001", "v002"):
        (archive / vid).mkdir()
    monkeypatch.setattr(
        "autoresearch.archive_index.load_lineage_history",
        lambda *a, **k: [
            {"id": "v001", "lane": "geo"},
            {"id": "v002", "lane": "geo"},
        ],
    )
    siblings = nc._resolve_recent_siblings(archive, "geo", exclude_id="v002", k=5)
    assert [sid for sid, _ in siblings] == ["v001"]


def test_resolve_recent_siblings_deduplicates_by_id(tmp_path, monkeypatch):
    """If lineage has multiple entries per variant_id (rescoring), each
    sibling appears once in the result."""
    archive = tmp_path / "archive"
    archive.mkdir()
    for vid in ("v001",):
        (archive / vid).mkdir()
    monkeypatch.setattr(
        "autoresearch.archive_index.load_lineage_history",
        lambda *a, **k: [
            {"id": "v001", "lane": "geo"},
            {"id": "v001", "lane": "geo"},  # rescored
            {"id": "v001", "lane": "geo"},  # rescored again
        ],
    )
    siblings = nc._resolve_recent_siblings(archive, "geo", exclude_id="x", k=5)
    assert [sid for sid, _ in siblings] == ["v001"]


# --- _parse_novelty_verdict ------------------------------------------------


def test_parse_verdict_novel_simple():
    assert nc._parse_novelty_verdict("NOVEL") is True


def test_parse_verdict_duplicate_simple():
    assert nc._parse_novelty_verdict("DUPLICATE") is False


def test_parse_verdict_with_rationale_then_word():
    """Real codex output: paragraph of reasoning followed by the verdict."""
    text = "Variant B introduces a new instruction set for handling edge cases. The strategy is meaningfully different.\n\nNOVEL"
    assert nc._parse_novelty_verdict(text) is True


def test_parse_verdict_mentions_both_terms_in_rationale():
    """Codex talks about 'novel' and 'duplicate' definitions in its
    rationale; only the final standalone token is the verdict."""
    text = "We define NOVEL as substantively different, and DUPLICATE as the same intent. Here, the candidate is essentially a paraphrase.\n\nDUPLICATE"
    assert nc._parse_novelty_verdict(text) is False


def test_parse_verdict_markdown_bold():
    """LLMs love bolding their verdict."""
    assert nc._parse_novelty_verdict("**DUPLICATE**") is False
    assert nc._parse_novelty_verdict("**NOVEL**") is True


def test_parse_verdict_empty_returns_none():
    assert nc._parse_novelty_verdict("") is None


def test_parse_verdict_no_verdict_word_returns_none():
    assert nc._parse_novelty_verdict("I cannot decide.") is None


# --- check_novelty end-to-end ----------------------------------------------


@pytest.fixture
def stub_archive(tmp_path, monkeypatch):
    """Build a stub archive with 2 siblings + 1 candidate on lane=geo."""
    archive = tmp_path / "archive"
    archive.mkdir()
    (archive / "v001").mkdir()
    (archive / "v001" / "lane.md").write_text("parent prose content baseline")
    (archive / "v002").mkdir()
    (archive / "v002" / "lane.md").write_text("sibling prose content variant")
    (archive / "v003").mkdir()
    (archive / "v003" / "lane.md").write_text("candidate prose content here")

    monkeypatch.setattr(
        "autoresearch.archive_index.load_lineage_history",
        lambda *a, **k: [
            {"id": "v001", "lane": "geo"},
            {"id": "v002", "lane": "geo"},
            {"id": "v999", "lane": "competitive"},  # other lane, filtered out
        ],
    )
    return archive


def test_check_novelty_no_siblings_returns_novel(tmp_path, monkeypatch):
    archive = tmp_path / "archive"
    archive.mkdir()
    (archive / "v001").mkdir()
    (archive / "v001" / "lane.md").write_text("first variant of the lane")
    monkeypatch.setattr(
        "autoresearch.archive_index.load_lineage_history",
        lambda *a, **k: [{"id": "v001", "lane": "geo"}],
    )
    is_novel, meta = nc.check_novelty(
        variant_dir=archive / "v001",
        parent_id="",
        lane="geo",
        archive_dir=archive,
    )
    assert is_novel is True
    assert meta["sibling_count"] == 0


def test_check_novelty_empty_candidate_text_is_novel(tmp_path, monkeypatch):
    archive = tmp_path / "archive"
    archive.mkdir()
    (archive / "v001").mkdir()
    (archive / "v001" / "binary.png").write_bytes(b"\x89PNG")
    monkeypatch.setattr(
        "autoresearch.archive_index.load_lineage_history",
        lambda *a, **k: [{"id": "v001", "lane": "geo"}],
    )
    is_novel, meta = nc.check_novelty(
        variant_dir=archive / "v001",
        parent_id="v000",
        lane="geo",
        archive_dir=archive,
    )
    assert is_novel is True
    assert "error" in meta


def test_check_novelty_low_jaccard_auto_accepts_without_codex(stub_archive, monkeypatch):
    """When candidate is clearly different (Jaccard < threshold), we
    auto-accept and do NOT call codex."""
    codex_called = {"n": 0}

    def fake_codex(a, b):
        codex_called["n"] += 1
        return True, "NOVEL"

    monkeypatch.setattr(nc, "_codex_novelty_judge", fake_codex)

    # Rewrite candidate so it has near-zero shingle overlap with siblings.
    (stub_archive / "v003" / "lane.md").write_text(
        "completely orthogonal text with totally different vocabulary and structure"
    )
    is_novel, meta = nc.check_novelty(
        variant_dir=stub_archive / "v003",
        parent_id="v001",
        lane="geo",
        archive_dir=stub_archive,
        similarity_threshold=0.3,
    )
    assert is_novel is True
    assert codex_called["n"] == 0
    assert meta["codex_invoked"] is False


def test_check_novelty_high_jaccard_invokes_codex_and_respects_verdict(
    stub_archive, monkeypatch,
):
    """When Jaccard >= threshold, codex decides; we reject on DUPLICATE
    and accept on NOVEL."""
    # Make candidate nearly identical to v002 → high Jaccard
    (stub_archive / "v003" / "lane.md").write_text(
        "sibling prose content variant"
    )
    codex_calls = {"a_text": None, "b_text": None}

    def fake_codex_says_duplicate(a, b):
        codex_calls["a_text"] = a
        codex_calls["b_text"] = b
        return False, "DUPLICATE"

    monkeypatch.setattr(nc, "_codex_novelty_judge", fake_codex_says_duplicate)
    is_novel, meta = nc.check_novelty(
        variant_dir=stub_archive / "v003",
        parent_id="v001",
        lane="geo",
        archive_dir=stub_archive,
        similarity_threshold=0.3,
    )
    assert is_novel is False
    assert meta["codex_invoked"] is True
    assert meta["codex_verdict"] == "DUPLICATE"
    # Codex was given the most-similar sibling, not just any
    assert "sibling prose content variant" in codex_calls["a_text"]


def test_check_novelty_high_jaccard_codex_says_novel_accepts(stub_archive, monkeypatch):
    (stub_archive / "v003" / "lane.md").write_text(
        "sibling prose content variant"
    )
    monkeypatch.setattr(nc, "_codex_novelty_judge", lambda a, b: (True, "NOVEL"))
    is_novel, meta = nc.check_novelty(
        variant_dir=stub_archive / "v003",
        parent_id="v001",
        lane="geo",
        archive_dir=stub_archive,
        similarity_threshold=0.3,
    )
    assert is_novel is True
    assert meta["codex_invoked"] is True
    assert meta["codex_verdict"] == "NOVEL"


def test_check_novelty_codex_ambiguous_accepts_by_default(stub_archive, monkeypatch):
    """If codex returns garbage / ambiguous output, the judge defaults
    to NOVEL (accept). The evolve loop must not be blocked by codex
    flakiness on a check that's just an optimization."""
    (stub_archive / "v003" / "lane.md").write_text(
        "sibling prose content variant"
    )
    monkeypatch.setattr(nc, "_codex_novelty_judge", lambda a, b: (True, "AMBIGUOUS-ACCEPT"))
    is_novel, meta = nc.check_novelty(
        variant_dir=stub_archive / "v003",
        parent_id="v001",
        lane="geo",
        archive_dir=stub_archive,
        similarity_threshold=0.3,
    )
    assert is_novel is True
    assert meta["codex_verdict"] == "AMBIGUOUS-ACCEPT"


def test_check_novelty_compares_only_recent_siblings(tmp_path, monkeypatch):
    """k_most_recent caps how far back we look. Old duplicates beyond
    the window are ignored (a deliberate scoping choice)."""
    archive = tmp_path / "archive"
    archive.mkdir()
    # 5 historical variants, candidate is variant 6
    for i in range(1, 7):
        (archive / f"v{i:03d}").mkdir()
        (archive / f"v{i:03d}" / "lane.md").write_text(f"distinct content {i}")
    # Make v001 (oldest) identical to v006 (candidate)
    (archive / "v006" / "lane.md").write_text("distinct content 1")
    monkeypatch.setattr(
        "autoresearch.archive_index.load_lineage_history",
        lambda *a, **k: [{"id": f"v{i:03d}", "lane": "geo"} for i in range(1, 7)],
    )

    codex_called = {"n": 0}
    monkeypatch.setattr(
        nc, "_codex_novelty_judge",
        lambda a, b: (codex_called.update(n=codex_called["n"] + 1) or (False, "DUPLICATE")),
    )
    # k_most_recent=3 → only compares against v005, v004, v003 (not v001)
    is_novel, meta = nc.check_novelty(
        variant_dir=archive / "v006",
        parent_id="v005",
        lane="geo",
        archive_dir=archive,
        similarity_threshold=0.3,
        k_most_recent=3,
    )
    assert meta["sibling_count"] == 3
    # Candidate is identical to v001 but v001 isn't in the recent window,
    # so Jaccard against v003/v004/v005 should be low → auto-accept.
    assert is_novel is True
    assert codex_called["n"] == 0


def test_check_novelty_env_override_threshold(stub_archive, monkeypatch):
    """AUTORESEARCH_NOVELTY_THRESHOLD env var tunes the auto-accept threshold."""
    (stub_archive / "v003" / "lane.md").write_text("sibling prose content variant")
    monkeypatch.setenv("AUTORESEARCH_NOVELTY_THRESHOLD", "0.99")
    monkeypatch.setattr(nc, "_codex_novelty_judge", lambda a, b: (False, "DUPLICATE"))
    # Even with similar text, threshold 0.99 means we auto-accept anything
    # below near-identical match.
    is_novel, meta = nc.check_novelty(
        variant_dir=stub_archive / "v003",
        parent_id="v001",
        lane="geo",
        archive_dir=stub_archive,
    )
    # The candidate IS identical to v002, so Jaccard = 1.0 >= 0.99 → codex fires.
    # Codex says DUPLICATE → reject.
    assert is_novel is False
