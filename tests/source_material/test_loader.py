"""U13 source material loader — markdown + PDF + HTML extraction.

Per the U13 plan-drift resolution: HTML loader ships in v1 (JR's
2026-05-19 decision). TD-56 cut applies only to voice corpora; source
material is operator-curated handoff content where HTML is a frequent
arrival format.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from src.source_material.loader import (
    SUPPORTED_SOURCE_MATERIAL_EXTENSIONS,
    SourceMaterialFile,
    UnsupportedSourceMaterialFormatError,
    load_source_material,
)


# ---------------------------------------------------------------------------
# Empty + missing-path handling
# ---------------------------------------------------------------------------


def test_load_source_material_empty_list_returns_empty() -> None:
    """No source material configured → empty result, no error. Lanes
    that hard-require source material check the length themselves."""
    assert load_source_material([]) == []


def test_load_source_material_missing_path_fails_loud(tmp_path: Path) -> None:
    """Operator-curated paths reference real handoff content; missing
    files are a curation error, not a soft skip. Per the plan, the
    loader surfaces ALL configured content."""
    with pytest.raises(FileNotFoundError) as exc:
        load_source_material([tmp_path / "does_not_exist.md"])
    assert "does_not_exist.md" in str(exc.value)


# ---------------------------------------------------------------------------
# Markdown — passthrough
# ---------------------------------------------------------------------------


def test_load_markdown_file(tmp_path: Path) -> None:
    md = tmp_path / "topic.md"
    md.write_text("# Topic\n\nMarkdown body content.\n")
    files = load_source_material([md])
    assert len(files) == 1
    assert files[0].format == "markdown"
    assert "Markdown body content" in files[0].text


def test_load_markdown_extension_variant_markdown_suffix(tmp_path: Path) -> None:
    """Both `.md` and `.markdown` are accepted."""
    md = tmp_path / "topic.markdown"
    md.write_text("hello\n")
    files = load_source_material([md])
    assert len(files) == 1
    assert files[0].format == "markdown"


# ---------------------------------------------------------------------------
# HTML — BeautifulSoup extraction
# ---------------------------------------------------------------------------


def test_load_html_strips_scripts_and_styles(tmp_path: Path) -> None:
    """HTML extraction must remove <script>, <style>, <noscript> — they
    pollute the LLM prompt with code/css and can inject prompt-
    injection payloads."""
    html = tmp_path / "blog_post.html"
    html.write_text(
        "<html><head>"
        "<style>body { color: red; }</style>"
        "<script>alert('xss')</script>"
        "</head><body>"
        "<noscript>JS off</noscript>"
        "<h1>Headline</h1><p>Visible body.</p>"
        "</body></html>"
    )
    files = load_source_material([html])
    assert len(files) == 1
    assert files[0].format == "html"
    assert "Visible body" in files[0].text
    assert "Headline" in files[0].text
    assert "alert" not in files[0].text  # script body stripped
    assert "color: red" not in files[0].text  # style body stripped
    assert "JS off" not in files[0].text  # noscript stripped


def test_load_html_extension_variant_htm_suffix(tmp_path: Path) -> None:
    """Both `.html` and `.htm` are accepted."""
    html = tmp_path / "post.htm"
    html.write_text("<html><body><p>hi</p></body></html>")
    files = load_source_material([html])
    assert len(files) == 1
    assert files[0].format == "html"


def test_load_malformed_html_falls_back_to_html_parser(tmp_path: Path) -> None:
    """Malformed HTML must not crash the loader; bs4 falls back through
    parsers and recovers what it can."""
    html = tmp_path / "broken.html"
    html.write_text("<html><body><p>orphan text<div>unclosed")
    files = load_source_material([html])
    assert len(files) == 1
    assert "orphan text" in files[0].text


# ---------------------------------------------------------------------------
# PDF — PyMuPDF extraction
# ---------------------------------------------------------------------------


def test_load_pdf_file(tmp_path: Path) -> None:
    """PDF extraction via PyMuPDF round-trips visible text."""
    import fitz  # type: ignore[import-untyped]

    pdf_path = tmp_path / "source.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Source material body text.")
    doc.save(pdf_path)
    doc.close()

    files = load_source_material([pdf_path])
    assert len(files) == 1
    assert files[0].format == "pdf"
    assert "Source material body text" in files[0].text


# ---------------------------------------------------------------------------
# Unsupported formats — fail loud
# ---------------------------------------------------------------------------


def test_unsupported_extension_raises(tmp_path: Path) -> None:
    """JSON, CSV, DOCX etc. are not supported in v1. Loader fails loud
    so operators see the curation problem instead of silent skips."""
    txt = tmp_path / "notes.docx"
    txt.write_text("plain text masquerading as docx")
    with pytest.raises(UnsupportedSourceMaterialFormatError) as exc:
        load_source_material([txt])
    assert ".docx" in str(exc.value)


def test_unsupported_extensions_include_csv_and_json() -> None:
    """Sanity: SUPPORTED_SOURCE_MATERIAL_EXTENSIONS only covers the
    documented v1 set."""
    assert ".csv" not in SUPPORTED_SOURCE_MATERIAL_EXTENSIONS
    assert ".json" not in SUPPORTED_SOURCE_MATERIAL_EXTENSIONS
    assert ".txt" not in SUPPORTED_SOURCE_MATERIAL_EXTENSIONS


# ---------------------------------------------------------------------------
# Directory walk
# ---------------------------------------------------------------------------


def test_directory_walk_recurses_and_sorts(tmp_path: Path) -> None:
    """Passing a directory walks all supported files inside, sorted by
    path for deterministic prompt construction."""
    (tmp_path / "subdir").mkdir()
    (tmp_path / "a.md").write_text("A body")
    (tmp_path / "b.md").write_text("B body")
    (tmp_path / "subdir" / "c.md").write_text("C body")

    files = load_source_material([tmp_path])
    assert len(files) == 3
    paths = [str(f.path).split(str(tmp_path))[1] for f in files]
    # Sorted: a.md < b.md < subdir/c.md
    assert paths == sorted(paths)


def test_directory_walk_skips_dotfiles(tmp_path: Path) -> None:
    """Hidden files (.DS_Store, .gitkeep, .gitignore) are not source
    material; skip them silently like the persona corpus loader."""
    (tmp_path / "real.md").write_text("real content")
    (tmp_path / ".gitkeep").write_text("")
    (tmp_path / ".DS_Store").write_text("mac noise")
    files = load_source_material([tmp_path])
    assert len(files) == 1
    assert "real content" in files[0].text


def test_directory_walk_raises_on_unsupported_descendant(tmp_path: Path) -> None:
    """Bad-curation state inside a directory still surfaces — operator
    fix-up beats silent skip."""
    (tmp_path / "good.md").write_text("ok")
    (tmp_path / "bad.docx").write_text("bad")
    with pytest.raises(UnsupportedSourceMaterialFormatError):
        load_source_material([tmp_path])


# ---------------------------------------------------------------------------
# Mixed input (file + directory)
# ---------------------------------------------------------------------------


def test_mixed_file_and_dir_paths(tmp_path: Path) -> None:
    """ClientConfig.source_material_paths may mix individual files
    (handoff doc) and directories (a curated folder of sources)."""
    single = tmp_path / "single.md"
    single.write_text("single body")
    dir_with_files = tmp_path / "dir"
    dir_with_files.mkdir()
    (dir_with_files / "inside.md").write_text("inside body")

    files = load_source_material([single, dir_with_files])
    assert len(files) == 2
    texts = " ".join(f.text for f in files)
    assert "single body" in texts
    assert "inside body" in texts


# ---------------------------------------------------------------------------
# Symlink escape (mirrors persona corpus defense)
# ---------------------------------------------------------------------------


def test_symlink_escape_outside_dir_is_skipped(tmp_path: Path) -> None:
    """Source material directories may sync from external sources
    (Dropbox / SharePoint) where an attacker-placed symlink → /etc/
    passwd would fold into the LLM prompt. Resolve + check
    containment; skip + warn on escape."""
    source_dir = tmp_path / "sources"
    source_dir.mkdir()
    (source_dir / "real.md").write_text("real content")

    outside = tmp_path / "outside.md"
    outside.write_text("attacker content")
    # Symlink inside source_dir pointing to outside.
    (source_dir / "evil.md").symlink_to(outside)

    files = load_source_material([source_dir])
    texts = " ".join(f.text for f in files)
    assert "real content" in texts
    assert "attacker content" not in texts


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_load_order_is_stable_across_calls(tmp_path: Path) -> None:
    """Repeated loads of the same input return the same order. Lane
    prompt construction depends on this for variant reproducibility."""
    for name in ("z.md", "a.md", "m.md"):
        (tmp_path / name).write_text(name)
    first = [f.path.name for f in load_source_material([tmp_path])]
    second = [f.path.name for f in load_source_material([tmp_path])]
    assert first == second
