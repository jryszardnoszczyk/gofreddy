"""Source material loader for article_engine (R5–R10 / U13).

Loads operator-curated handoff content referenced from
`ClientConfig.source_material_paths`. Each path may be a single file
or a directory; the loader walks directories recursively, extracts
text per extension, and returns a deterministic list of
`SourceMaterialFile` records the lane concatenates into the session
prompt context.

Supported formats (v1):
- `.md` / `.markdown` — UTF-8 text passthrough.
- `.pdf` — PyMuPDF (fitz) page-by-page text extraction.
- `.html` / `.htm` — BeautifulSoup main-content extraction (script/
  style tags stripped; visible-text only). `lxml` parser preferred,
  with `html.parser` fallback.

Per JR's U13 decision (2026-05-19, "Build now"): HTML loader ships
in v1. TD-56 cut HTML for VOICE corpora (operator-curated lived-work
references, where structure leaks into rubric scoring); source
material is a different concern — handoff content frequently arrives
as HTML (Notion exports, blog posts, scraped landing pages) and
fail-loud on HTML inputs would push the operator into manual
conversion for every onboarding.

Per the persona-loader precedent: corpus-loading defends against
symlink escape (an attacker-placed symlink → `/etc/passwd` would
otherwise fold into the LLM prompt). Source material runs the same
defense at directory walk time. Path traversal at the file-list
level (`paths` argument) is the caller's responsibility — the
canonical caller (article_engine `configure_env`) reads
`ClientConfig.source_material_paths` which is schema-validated at
config load time.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


SUPPORTED_SOURCE_MATERIAL_EXTENSIONS: frozenset[str] = frozenset(
    {".md", ".markdown", ".pdf", ".html", ".htm"}
)
"""Extensions the source-material loader recognises. URL-list ingestion
is deferred — operators pre-fetch URLs into local files for v1."""


class UnsupportedSourceMaterialFormatError(ValueError):
    """Raised when a source-material file has an extension outside
    `SUPPORTED_SOURCE_MATERIAL_EXTENSIONS`."""


@dataclass(frozen=True)
class SourceMaterialFile:
    """One source-material file's extracted text + provenance.

    Mirrors `src.voice.persona.CorpusFile`'s shape so consumers can
    treat the two streams interchangeably (e.g., a generic concat
    helper in the lane prompt builder). The `format` field tags the
    extraction method so downstream prompts can include provenance
    hints ("This source was extracted from a PDF; pagination may be
    lost.")."""

    path: Path
    text: str
    format: str  # "markdown" | "pdf" | "html"


def load_source_material(paths: list[Path]) -> list[SourceMaterialFile]:
    """Load + extract text from all source-material file references.

    `paths` may include both individual file paths and directory
    paths. Directories are walked recursively (matching the persona
    corpus loader pattern). Order of the returned list is determined
    by `Path.rglob`'s sort, then by input-list order; the loader
    guarantees stable output for a given input.

    Raises:
        FileNotFoundError: any path in `paths` does not exist on disk.
        UnsupportedSourceMaterialFormatError: a discovered file has
            an extension outside the supported set. Directory walks
            do NOT swallow this (fail loud) — operators should curate
            source material directories cleanly. Single-file inputs
            with unsupported extensions also fail loud.
        NotADirectoryError: a path resolves to neither a file nor a
            directory (e.g., broken symlink).

    Per the plan §source material acquisition: the lane's session
    prompt expects the loader to surface ALL operator-curated
    content. Silent skips would hide bad-curation states the
    operator needs to fix.
    """
    if not paths:
        return []

    files: list[SourceMaterialFile] = []
    seen_paths: set[Path] = set()
    for entry_path in paths:
        if not entry_path.exists():
            raise FileNotFoundError(
                f"source material path {entry_path} does not exist. "
                f"Verify ClientConfig.source_material_paths references "
                f"reachable operator-curated content."
            )
        if entry_path.is_file():
            file_record = _extract_file(entry_path, root_for_symlink_check=None)
            if file_record is not None and file_record.path not in seen_paths:
                files.append(file_record)
                seen_paths.add(file_record.path)
        elif entry_path.is_dir():
            resolved_root = entry_path.resolve()
            for descendant in sorted(resolved_root.rglob("*")):
                if not descendant.is_file():
                    continue
                if descendant.name.startswith("."):
                    continue
                file_record = _extract_file(
                    descendant, root_for_symlink_check=resolved_root,
                )
                if file_record is not None and file_record.path not in seen_paths:
                    files.append(file_record)
                    seen_paths.add(file_record.path)
        else:
            raise NotADirectoryError(
                f"source material path {entry_path} is neither a file "
                f"nor a directory (broken symlink?)."
            )
    return files


def _extract_file(
    path: Path, root_for_symlink_check: Path | None,
) -> SourceMaterialFile | None:
    """Extract text from a single file. Returns None for files that
    fail the symlink-containment check (logged + skipped); raises for
    unsupported extensions (fail loud)."""
    if root_for_symlink_check is not None:
        try:
            resolved = path.resolve()
            resolved.relative_to(root_for_symlink_check)
        except ValueError:
            logger.warning(
                "skipping %s which symlinks outside source material root %s",
                path, root_for_symlink_check,
            )
            return None

    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_SOURCE_MATERIAL_EXTENSIONS:
        raise UnsupportedSourceMaterialFormatError(
            f"source material file {path} has extension {suffix!r}; "
            f"supported extensions are "
            f"{sorted(SUPPORTED_SOURCE_MATERIAL_EXTENSIONS)}. URL "
            f"ingestion is deferred — operators pre-fetch URLs into "
            f"local files for v1."
        )

    if suffix in {".md", ".markdown"}:
        return SourceMaterialFile(
            path=path, text=path.read_text(encoding="utf-8"), format="markdown",
        )
    if suffix == ".pdf":
        return SourceMaterialFile(
            path=path, text=_extract_pdf_text(path), format="pdf",
        )
    if suffix in {".html", ".htm"}:
        return SourceMaterialFile(
            path=path, text=_extract_html_text(path), format="html",
        )
    # Unreachable — the suffix check above guards every case.
    raise UnsupportedSourceMaterialFormatError(  # pragma: no cover
        f"unhandled suffix {suffix!r} for {path}"
    )


def _extract_pdf_text(pdf_path: Path) -> str:
    """Extract plain text from a PDF via PyMuPDF.

    Mirrors `src.voice.persona._extract_pdf_text` (intentional
    duplication — two consumers + a 10-LOC helper; factor into a
    shared module when a third consumer needs it, per the rule of
    three).
    """
    try:
        import fitz  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover — pymupdf is in main deps
        raise ImportError(
            "PyMuPDF (fitz) is required for PDF source-material extraction. "
            "Verify it's installed via the project's main dependencies."
        ) from exc

    chunks: list[str] = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            chunks.append(page.get_text())
    return "\n".join(chunks)


def _extract_html_text(html_path: Path) -> str:
    """Extract visible text from an HTML file via BeautifulSoup.

    Strips `<script>`, `<style>`, and `<noscript>` tags to avoid
    injecting JavaScript or CSS into the LLM prompt. Preserves
    structural newlines via `get_text(separator='\\n')`. Prefers
    `lxml` parser (faster, better recovery) with a stdlib
    `html.parser` fallback.
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError as exc:  # pragma: no cover — beautifulsoup4 is in main deps
        raise ImportError(
            "beautifulsoup4 is required for HTML source-material extraction. "
            "Verify it's installed via the project's main dependencies."
        ) from exc

    raw = html_path.read_text(encoding="utf-8", errors="replace")
    try:
        soup = BeautifulSoup(raw, "lxml")
    except Exception:
        # lxml may be missing or fail on malformed HTML; fall back to
        # stdlib parser. Fail-loud on the FALLBACK only — bs4's
        # html.parser is always available with the stdlib.
        soup = BeautifulSoup(raw, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return soup.get_text(separator="\n").strip()
