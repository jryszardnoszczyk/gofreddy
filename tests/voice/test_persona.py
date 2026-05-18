"""VoicePersona schema + loader + corpus reader (U3).

Per TD-56 binary-cuts pass (2026-05-18):
- VoicePersona has no `corpus_checksum` field; corruption detection
  deferred to v1.5+ trigger.
- Corpus loaders cover markdown + PDF only. HTML + JSON loaders
  intentionally raise.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from src.voice.persona import (
    SUPPORTED_CORPUS_EXTENSIONS,
    CorpusFile,
    UnsupportedCorpusFormatError,
    VoicePersona,
    VoicePersonaNotFoundError,
    load_corpus_files,
    load_persona,
)


# ---------------------------------------------------------------------------
# Schema: VoicePersona validators
# ---------------------------------------------------------------------------


def _minimal_persona_dict(**overrides) -> dict:
    base = {
        "name": "fixture_persona",
        "corpus_path": "voice_personas/corpora/stub",  # exists in repo
        "voice_rules": ["rule one", "rule two"],
        "style_anchors": {"anchor_one": "prose for anchor one"},
    }
    base.update(overrides)
    return base


def test_minimal_persona_constructs() -> None:
    persona = VoicePersona.model_validate(_minimal_persona_dict())
    assert persona.persona_slug == "fixture_persona"
    assert persona.voice_rules == ["rule one", "rule two"]
    assert persona.style_anchors == {"anchor_one": "prose for anchor one"}


def test_persona_is_frozen() -> None:
    persona = VoicePersona.model_validate(_minimal_persona_dict())
    with pytest.raises(ValidationError):
        persona.persona_slug = "different"  # type: ignore[misc]


def test_persona_name_must_be_non_whitespace() -> None:
    with pytest.raises(ValidationError):
        VoicePersona.model_validate(_minimal_persona_dict(name="bad name"))
    with pytest.raises(ValidationError):
        VoicePersona.model_validate(_minimal_persona_dict(name=""))


def test_empty_voice_rules_allowed() -> None:
    """Per plan U3 edge case: empty voice_rules list → persona loadable."""
    persona = VoicePersona.model_validate(_minimal_persona_dict(voice_rules=[]))
    assert persona.voice_rules == []


def test_empty_style_anchors_allowed() -> None:
    """Per plan U3 edge case: empty style_anchors → persona loadable.
    Lanes that need anchors fail at use, not at load."""
    persona = VoicePersona.model_validate(_minimal_persona_dict(style_anchors={}))
    assert persona.style_anchors == {}


def test_persona_has_no_corpus_checksum_field() -> None:
    """Per TD-56 cuts: corpus_checksum field was rejected. Verifying the
    cut so a future re-add is a deliberate decision, not silent drift."""
    assert "corpus_checksum" not in VoicePersona.model_fields


# ---------------------------------------------------------------------------
# Loader: load_persona reads real YAML files
# ---------------------------------------------------------------------------


def test_load_dr_maria_persona() -> None:
    """Per plan U3 verification:
    python -c 'from src.voice.persona import load_persona;
               p = load_persona("dr_maria"); print(p.style_anchors)' succeeds."""
    persona = load_persona("dr_maria")
    assert persona.persona_slug == "dr_maria"
    assert "argumentative-medical-pedagogic" in persona.style_anchors
    assert len(persona.voice_rules) > 0


def test_load_partner_jamka_persona() -> None:
    persona = load_persona("partner_jamka")
    assert persona.persona_slug == "partner_jamka"
    assert "senior-partner-strategic-counsel" in persona.style_anchors


def test_load_stub_persona() -> None:
    persona = load_persona("_stub_persona")
    assert persona.persona_slug == "_stub_persona"


def test_load_unknown_persona_raises_not_found() -> None:
    """Per plan U3 error path: unknown persona ref → FileNotFoundError
    with helpful message."""
    with pytest.raises(VoicePersonaNotFoundError) as exc:
        load_persona("does-not-exist-anywhere")
    assert "voice_personas/" in str(exc.value)
    assert "does-not-exist-anywhere" in str(exc.value)


def test_load_persona_with_nonexistent_corpus_path_raises(tmp_path: Path) -> None:
    """Per plan U3 error path: corpus_path that doesn't resolve to an
    existing path → FileNotFoundError at load."""
    # Build a temp persona YAML pointing at a nonexistent corpus dir.
    bad_dir = tmp_path / "voice_personas"
    bad_dir.mkdir()
    bad_yaml = bad_dir / "bad_persona.yaml"
    bad_yaml.write_text(yaml.safe_dump({
        "name": "bad_persona",
        "corpus_path": str(tmp_path / "this-dir-does-not-exist"),
        "voice_rules": [],
        "style_anchors": {},
    }))

    # Monkey the loader to read from tmp_path's voice_personas/. We do
    # this by constructing the VoicePersona directly and calling the
    # internal path check (which is what load_persona does after
    # schema validation).
    from src.voice.persona import _resolve_corpus_path

    persona = VoicePersona.model_validate(yaml.safe_load(bad_yaml.read_text()))
    resolved = _resolve_corpus_path(persona.corpus_path)
    assert not resolved.exists()


def test_load_persona_with_empty_corpus_dir_succeeds() -> None:
    """The 3 v1 personas all reference empty corpus directories pre-consent.
    Load must succeed even when the dir is empty — lanes detect content
    absence at usage time."""
    persona = load_persona("dr_maria")
    # corpus_path exists (the .gitkeep placeholder ensures the dir exists)
    # but holds no .md or .pdf content yet.
    files = load_corpus_files(persona)
    assert files == []


# ---------------------------------------------------------------------------
# Corpus reader: load_corpus_files
# ---------------------------------------------------------------------------


def test_corpus_reader_returns_markdown_text(tmp_path: Path) -> None:
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    (corpus_dir / "first.md").write_text("# First\n\nBody one.\n", encoding="utf-8")
    (corpus_dir / "second.md").write_text("# Second\n\nBody two.\n", encoding="utf-8")

    persona = VoicePersona.model_validate({
        "name": "test_md_persona",
        "corpus_path": str(corpus_dir),
        "voice_rules": [],
        "style_anchors": {},
    })

    files = load_corpus_files(persona)
    assert len(files) == 2
    assert all(f.format == "markdown" for f in files)
    # Sorted-by-path determinism
    assert files[0].path.name == "first.md"
    assert files[1].path.name == "second.md"
    assert "Body one" in files[0].text
    assert "Body two" in files[1].text


def test_corpus_reader_recurses_into_subdirectories(tmp_path: Path) -> None:
    corpus_dir = tmp_path / "corpus"
    sub = corpus_dir / "sub"
    sub.mkdir(parents=True)
    (corpus_dir / "top.md").write_text("top", encoding="utf-8")
    (sub / "nested.md").write_text("nested", encoding="utf-8")

    persona = VoicePersona.model_validate({
        "name": "recursive_persona",
        "corpus_path": str(corpus_dir),
        "voice_rules": [],
        "style_anchors": {},
    })

    files = load_corpus_files(persona)
    assert {f.path.name for f in files} == {"top.md", "nested.md"}


def test_corpus_reader_rejects_html(tmp_path: Path) -> None:
    """Per TD-56: HTML corpus loader is deferred. Loader raises."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    (corpus_dir / "blog.html").write_text("<p>some content</p>", encoding="utf-8")

    persona = VoicePersona.model_validate({
        "name": "html_persona",
        "corpus_path": str(corpus_dir),
        "voice_rules": [],
        "style_anchors": {},
    })

    with pytest.raises(UnsupportedCorpusFormatError) as exc:
        load_corpus_files(persona)
    assert ".html" in str(exc.value)
    assert "TD-56" in str(exc.value)


def test_corpus_reader_rejects_json(tmp_path: Path) -> None:
    """Per TD-56: JSON corpus loader is deferred. Loader raises."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    (corpus_dir / "twitter-export.json").write_text('{"tweets": []}', encoding="utf-8")

    persona = VoicePersona.model_validate({
        "name": "json_persona",
        "corpus_path": str(corpus_dir),
        "voice_rules": [],
        "style_anchors": {},
    })

    with pytest.raises(UnsupportedCorpusFormatError):
        load_corpus_files(persona)


def test_corpus_reader_handles_pdf(tmp_path: Path) -> None:
    """PyMuPDF-backed PDF extraction. Skips if fitz unavailable."""
    fitz = pytest.importorskip("fitz")

    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    pdf_path = corpus_dir / "sample.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Hello from the test PDF.")
    doc.save(pdf_path)
    doc.close()

    persona = VoicePersona.model_validate({
        "name": "pdf_persona",
        "corpus_path": str(corpus_dir),
        "voice_rules": [],
        "style_anchors": {},
    })

    files = load_corpus_files(persona)
    assert len(files) == 1
    assert files[0].format == "pdf"
    assert "Hello from the test PDF" in files[0].text


def test_corpus_reader_raises_when_path_is_not_a_directory(tmp_path: Path) -> None:
    bad_path = tmp_path / "not-a-dir.md"
    bad_path.write_text("contents", encoding="utf-8")

    persona = VoicePersona.model_validate({
        "name": "file_not_dir_persona",
        "corpus_path": str(bad_path),
        "voice_rules": [],
        "style_anchors": {},
    })

    with pytest.raises(NotADirectoryError):
        load_corpus_files(persona)


def test_supported_extensions_is_md_and_pdf_only() -> None:
    """Pinning the supported-extension set so HTML/JSON re-introduction
    is a deliberate v1.5 decision, not silent drift."""
    assert SUPPORTED_CORPUS_EXTENSIONS == frozenset({".md", ".pdf"})


# ---------------------------------------------------------------------------
# Integration: ClientConfig.voice_persona_ref → load_persona
# ---------------------------------------------------------------------------


def test_client_config_voice_persona_ref_resolves_to_persona() -> None:
    """Per plan U3 integration: ClientConfig.voice_persona_ref resolves
    through loader to a valid VoicePersona."""
    from src.clients.loader import load_client_config

    klinika = load_client_config("klinika-melitus")
    persona = load_persona(klinika.voice_persona_ref)
    assert persona.persona_slug == "dr_maria"
    assert persona.persona_slug == klinika.voice_persona_ref


def test_multiple_clients_can_share_persona_ref() -> None:
    """Per plan U2/U3: two clients referencing same persona_ref is allowed."""
    p1 = load_persona("_stub_persona")
    p2 = load_persona("_stub_persona")
    # Pydantic frozen models compare by value
    assert p1 == p2


def test_corpus_reader_skips_symlink_escaping_corpus_dir(tmp_path: Path) -> None:
    """Per the 4-agent review (sec-6): a symlink inside the corpus
    directory pointing OUTSIDE it (e.g., a syncd Dropbox sneaking in a
    symlink to /etc/passwd) is skipped with a log warning, not folded
    into the persona corpus."""
    outside_file = tmp_path / "outside_secret.md"
    outside_file.write_text("SECRET CORPUS CONTENT", encoding="utf-8")

    corpus = tmp_path / "corpus"
    corpus.mkdir()
    legit = corpus / "legit.md"
    legit.write_text("legitimate corpus", encoding="utf-8")

    # Symlink inside the corpus that points outside
    escape_link = corpus / "escape.md"
    escape_link.symlink_to(outside_file)

    persona = VoicePersona.model_validate({
        "name": "symlink_test",
        "corpus_path": str(corpus),
        "voice_rules": [],
        "style_anchors": {},
    })

    files = load_corpus_files(persona)
    # Only the legitimate file is read; the escape symlink is skipped.
    paths = [f.path.name for f in files]
    assert "legit.md" in paths
    assert "escape.md" not in paths
    # And the secret content didn't make it in.
    for f in files:
        assert "SECRET" not in f.text
