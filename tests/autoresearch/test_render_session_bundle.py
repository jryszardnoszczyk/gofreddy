"""Tests for make_session_bundle + build_session_bundle_section.

Verifies:
- bundle.tar.gz contains every session_dir file *except* the rendered
  artefacts themselves (no recursion on report.html / .pdf / .png /
  bundle.tar.gz on re-render).
- HTML report renders the file tree with a relative <a download> for
  every file.
- Inline preview <details> appear for small text/JSON files.
- PDF-side stub stays present so the slim PDF still mentions the bundle.
- @media print CSS rule hides the inline tree in PDF.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tarfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
RENDER_REPORT_PATH = (
    REPO_ROOT
    / "autoresearch"
    / "archive"
    / "v006"
    / "scripts"
    / "render_report.py"
)


@pytest.fixture(scope="module")
def render_report_module():
    spec = importlib.util.spec_from_file_location(
        "render_report_bundle_test", RENDER_REPORT_PATH
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["render_report_bundle_test"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def populated_session(tmp_path: Path) -> Path:
    sd = tmp_path / "sd"
    (sd / "logs").mkdir(parents=True)
    (sd / "drafts").mkdir()
    (sd / "session.md").write_text("# Session\n\n## Status: COMPLETE\n")
    (sd / "results.jsonl").write_text(
        json.dumps({"iteration": 1, "type": "x", "status": "ok"}) + "\n"
    )
    (sd / "findings.md").write_text("## Observations\n\n- [TAG] hi\n")
    (sd / "session_summary.json").write_text(json.dumps({"status": "COMPLETE"}))
    (sd / "logs" / "iteration_001.log.err").write_text(
        "codex\nI'll start.\nexec\n/bin/zsh -lc \"ls\"\n"
    )
    (sd / "drafts" / "draft-001.md").write_text("---\nx: y\n---\n[BODY]\nhi\n[/BODY]\n")
    # A binary-ish file (no preview)
    (sd / "drafts" / "preview.bin").write_bytes(b"\x00\x01\x02BIN")
    # An empty placeholder file (skipped from inline preview)
    (sd / "logs" / "iteration_002.log.err").write_text("")
    return sd


def test_make_session_bundle_excludes_rendered_artefacts(
    render_report_module, populated_session
):
    # Pretend a prior render already wrote these
    (populated_session / "report.html").write_text("<html></html>")
    (populated_session / "report.pdf").write_bytes(b"%PDF")
    (populated_session / "report-screenshot.png").write_bytes(b"\x89PNG")

    bundle = render_report_module.make_session_bundle(populated_session)
    assert bundle is not None
    assert bundle.name == "bundle.tar.gz"

    with tarfile.open(bundle, "r:gz") as tf:
        members = sorted(m.name for m in tf.getmembers() if m.isfile())

    # Rendered artefacts NOT in the bundle (no recursion)
    assert "report.html" not in members
    assert "report.pdf" not in members
    assert "report-screenshot.png" not in members
    assert "bundle.tar.gz" not in members

    # Real session files ARE in the bundle
    assert "session.md" in members
    assert "logs/iteration_001.log.err" in members
    assert "drafts/draft-001.md" in members
    assert "drafts/preview.bin" in members


def test_make_session_bundle_returns_none_on_empty(
    render_report_module, tmp_path
):
    empty = tmp_path / "empty"
    empty.mkdir()
    assert render_report_module.make_session_bundle(empty) is None
    assert not (empty / "bundle.tar.gz").exists()


def test_build_session_bundle_section_renders_tree(
    render_report_module, populated_session
):
    bundle = render_report_module.make_session_bundle(populated_session)
    html = render_report_module.build_session_bundle_section(
        populated_session, bundle
    )

    # Top-level section header + bundle download
    assert "Session bundle" in html
    assert 'href="bundle.tar.gz"' in html
    assert "Download all" in html

    # File tree groups present
    assert "(root)" in html
    assert "<code>logs/</code>" in html
    assert "<code>drafts/</code>" in html

    # Relative download links for actual files
    assert 'href="logs/iteration_001.log.err"' in html
    assert 'href="drafts/draft-001.md"' in html
    assert 'href="drafts/preview.bin"' in html

    # Inline preview <details> appears for text/JSON, not for binaries
    # 4 text files (session.md, results.jsonl, findings.md, session_summary.json,
    # logs/iteration_001.log.err, drafts/draft-001.md) + the 0-byte log.err is
    # skipped. preview.bin (binary) has NO show-inline.
    assert html.count("show inline") >= 4
    # The binary file doesn't get a preview details block: search for its row
    bin_row = html.split('href="drafts/preview.bin"')[1].split("</li>")[0]
    assert "show inline" not in bin_row


def test_build_session_bundle_section_pdf_stub(
    render_report_module, populated_session
):
    bundle = render_report_module.make_session_bundle(populated_session)
    html = render_report_module.build_session_bundle_section(
        populated_session, bundle
    )
    # @media print CSS rule must hide the inline tree
    assert "@media print" in html
    assert ".rprt-bundle-tree { display:none }" in html
    # PDF-only stub is present (default-hidden via .rprt-bundle-print { display:none })
    assert "rprt-bundle-print" in html
    assert "the printable PDF omits" in html


def test_build_session_bundle_section_no_bundle(
    render_report_module, populated_session
):
    """When bundle generation failed (returns None), the section still
    renders but the download link reports the absence."""
    html = render_report_module.build_session_bundle_section(
        populated_session, None
    )
    assert "Session bundle" in html
    # No download anchor, but a graceful fallback message
    assert "bundle.tar.gz not generated" in html


def test_inline_preview_truncates_huge_text_files(
    render_report_module, tmp_path
):
    sd = tmp_path / "sd"
    sd.mkdir()
    big = sd / "big.log.err"
    # 200 KB > the 128 KB inline cap → should NOT inline
    big.write_text("x" * (200 * 1024))
    bundle = render_report_module.make_session_bundle(sd)
    html = render_report_module.build_session_bundle_section(sd, bundle)
    # File appears as a download link
    assert 'href="big.log.err"' in html
    # But no inline preview because it's over the 128 KB cap
    big_row = html.split('href="big.log.err"')[1].split("</li>")[0]
    assert "show inline" not in big_row


def test_full_render_creates_bundle_and_slim_pdf_stub(
    render_report_module, populated_session, monkeypatch
):
    # Patch html_to_pdf + html_to_screenshot to avoid Chrome dependency in
    # CI. We're only verifying that render() wires the bundle into the HTML.
    monkeypatch.setattr(render_report_module, "html_to_pdf", lambda *a, **k: True)
    monkeypatch.setattr(
        render_report_module, "html_to_screenshot", lambda *a, **k: True
    )
    # Need a domain that maps to a composer
    out = render_report_module.render(populated_session, "x_engine", "jr")

    html = (populated_session / "report.html").read_text()

    # Bundle generated
    bundle = populated_session / "bundle.tar.gz"
    assert bundle.is_file()
    assert bundle.stat().st_size > 0

    # Bundle section landed in the HTML
    assert "Session bundle · every file" in html
    assert 'href="bundle.tar.gz"' in html

    # The bundle.tar.gz is now in session_dir, but a re-render must NOT
    # include it in the new bundle. Re-render and check.
    out2 = render_report_module.render(populated_session, "x_engine", "jr")
    with tarfile.open(populated_session / "bundle.tar.gz", "r:gz") as tf:
        members = {m.name for m in tf.getmembers() if m.isfile()}
    assert "bundle.tar.gz" not in members
    assert "report.html" not in members
