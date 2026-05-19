"""U15b — reviewer_diff_capture (TD-43 v1.3 scaffolding)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.site_engine.reviewer_diff_capture import (
    EditCategory,
    ReviewerDiffEntry,
    capture_diff,
    categorize_edit,
)


def test_categorize_edit_no_change_returns_empty() -> None:
    assert categorize_edit("<h1>x</h1>", "<h1>x</h1>") == []


def test_categorize_edit_copy_change() -> None:
    """Same structure, different text → copy_change."""
    cats = categorize_edit("<h1>old</h1>", "<h1>new</h1>")
    assert "copy_change" in cats


def test_categorize_edit_sub_element_added() -> None:
    """More tags in approved → reviewer added sub-elements."""
    cats = categorize_edit(
        "<h1>x</h1><p>a</p><p>b</p><p>c</p><p>d</p>",
        "<h1>x</h1>",
    )
    assert "sub_element_added" in cats


def test_categorize_edit_sub_element_removed() -> None:
    """Fewer tags in approved → reviewer removed sub-elements."""
    cats = categorize_edit(
        "<h1>x</h1>",
        "<h1>x</h1><p>a</p><p>b</p><p>c</p><p>d</p>",
    )
    assert "sub_element_removed" in cats


def test_categorize_edit_layout_swap() -> None:
    """Different grid-cols class → layout_swap."""
    cats = categorize_edit(
        '<div class="grid-cols-2">x</div>',
        '<div class="grid-cols-3">x</div>',
    )
    assert "layout_swap" in cats


def test_capture_diff_persists_jsonl(tmp_path: Path) -> None:
    """Capture writes a JSONL entry under reviewer_diffs/<client>/<YYYY-MM>/."""
    entry = capture_diff(
        client_slug="klinika-melitus",
        section_type="hero",
        variant_id="hero_v1",
        approved_html='<h1>Approved</h1>',
        lane_output_html='<h1>Lane</h1>',
        reviewer_note="Adjusted headline for clarity.",
        output_root=tmp_path,
    )
    assert isinstance(entry, ReviewerDiffEntry)
    # File should exist under tmp_path/klinika-melitus/<YYYY-MM>/diffs.jsonl
    yyyy_mm = entry.captured_at[:7]
    out_path = tmp_path / "klinika-melitus" / yyyy_mm / "diffs.jsonl"
    assert out_path.is_file()
    line = out_path.read_text(encoding="utf-8").splitlines()[0]
    parsed = json.loads(line)
    assert parsed["client_slug"] == "klinika-melitus"
    assert parsed["reviewer_note"] == "Adjusted headline for clarity."
    assert "copy_change" in parsed["edit_categories"]


def test_capture_diff_empty_note_logs_warning(
    tmp_path: Path, caplog,
) -> None:
    """TD-43: empty reviewer_note logs CI warning but doesn't block."""
    import logging
    caplog.set_level(logging.WARNING)
    capture_diff(
        client_slug="dwf-poland",
        section_type="value_prop",
        variant_id="vp_v1",
        approved_html='<h1>x</h1>',
        lane_output_html='<h1>y</h1>',
        reviewer_note="",  # empty
        output_root=tmp_path,
    )
    assert any("empty reviewer_note" in rec.message for rec in caplog.records)


def test_capture_diff_truncates_large_diffs(tmp_path: Path) -> None:
    """Textual diffs cap at ~5KB to keep JSONL manageable."""
    huge = "<p>" + "x" * 10_000 + "</p>"
    entry = capture_diff(
        client_slug="c1",
        section_type="hero",
        variant_id="x",
        approved_html=huge,
        lane_output_html="<p>different</p>",
        reviewer_note="changed all the things",
        output_root=tmp_path,
    )
    assert len(entry.textual_diff) <= 5100  # cap + truncation marker
