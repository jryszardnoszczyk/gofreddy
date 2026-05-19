"""Voice persona framework (R20).

A `VoicePersona` is the shared substrate that storyboard / article_engine /
linkedin_engine / x_engine consume to produce on-brand content for a
client. The persona carries:

- `name`           — slug-shaped identifier (e.g., "dr_maria", "partner_jamka")
- `corpus_path`    — directory of markdown + PDF source files the lane reads
                     for tone calibration + factual grounding
- `voice_rules`    — list of plain-language style rules ("never use exclamation
                     points," "open with a question," "avoid 'we'")
- `style_anchors`  — named anchor descriptions ("argumentative-medical-pedagogic")
                     referenced by name in lane prompts

The persona file lives at `voice_personas/<persona_ref>.yaml`. Multiple
clients MAY share a persona (no uniqueness constraint) — `ClientConfig`'s
`voice_persona_ref` field resolves to a persona by name.

Per TD-56 binary-cuts pass (2026-05-18):
- NO `corpus_checksum` field on VoicePersona. Re-add when ≥3 personas
  are active and corpus drift becomes a real concern (currently a 2-persona
  setup with operator-curated corpora; file mtime + git diff are enough
  signal until then).
- Corpus loaders cover markdown + PDF ONLY. HTML + JSON loaders deferred
  to the first SaaS-shaped client whose corpus needs them (deferring
  BeautifulSoup vendor surface + JSON-export schema discovery until then).
- No voice extractor CLI — operator authors `voice_rules` + `style_anchors`
  by hand from the corpus.

Per the plan §Compliance Posture: a persona's `corpus_path` may not yet
exist or may be empty pre-consent (parallel-track risk #1 for Klinika +
DWF). `load_persona` validates the path exists (even if empty); lanes
that read corpus content fail loud when content is missing — keeping
the load step graceful while preserving fail-loud at usage time.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger(__name__)


_REPO_ROOT = Path(__file__).resolve().parents[2]


SUPPORTED_CORPUS_EXTENSIONS: frozenset[str] = frozenset({".md", ".pdf"})
"""File extensions the corpus loader recognises. Per TD-56: markdown +
PDF only in v1. HTML + JSON deferred."""


class VoicePersonaNotFoundError(FileNotFoundError):
    """Raised when `voice_personas/<persona_ref>.yaml` does not exist."""


class UnsupportedCorpusFormatError(ValueError):
    """Raised when a corpus file has an extension outside
    `SUPPORTED_CORPUS_EXTENSIONS`."""


class VoicePersona(BaseModel):
    """The shared voice substrate consumed by content lanes."""

    model_config = ConfigDict(frozen=True, extra="allow", populate_by_name=True)

    persona_slug: str = Field(
        ...,
        alias="name",
        description=(
            "Slug-shaped persona identifier; matches the YAML filename. "
            "YAML keys use `name` for operator-friendliness; the model "
            "field is renamed `persona_slug` to avoid the field-name "
            "collision with ComplianceRuleSet.rule_set_name + ClientConfig"
            ".display_name that lanes will compose in prompts."
        ),
    )
    corpus_path: Path = Field(
        ...,
        description=(
            "Directory of markdown + PDF source files. May be empty pre-consent; "
            "lanes verify content at read time, not at persona load time."
        ),
    )
    voice_rules: list[str] = Field(
        default_factory=list,
        description="Plain-language style rules referenced verbatim by lane prompts.",
    )
    style_anchors: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Named anchor → prose mapping. Lane prompts reference by name: "
            'e.g., "use the style_anchors.argumentative-medical-pedagogic voice".'
        ),
    )

    @field_validator("persona_slug")
    @classmethod
    def _persona_slug_is_slug_shaped(cls, v: str) -> str:
        if not v or any(c.isspace() for c in v):
            raise ValueError(f"persona_slug must be non-empty with no whitespace; got {v!r}")
        return v


@dataclass(frozen=True)
class CorpusFile:
    """One corpus file's extracted text content + source path provenance."""

    path: Path
    text: str
    format: str  # "markdown" | "pdf"


def _persona_yaml_path(persona_ref: str) -> Path:
    return _REPO_ROOT / "voice_personas" / f"{persona_ref}.yaml"


def _resolve_corpus_path(raw: Path) -> Path:
    """Resolve a corpus_path entry from the YAML against the repo root.

    Repo-relative paths are anchored to the repo root; absolute paths
    pass through. Symlinks resolve before existence check.
    """
    if raw.is_absolute():
        return raw.resolve()
    return (_REPO_ROOT / raw).resolve()


def load_persona(persona_ref: str) -> VoicePersona:
    """Load + validate `voice_personas/<persona_ref>.yaml` into a frozen
    `VoicePersona`.

    Raises:
        VoicePersonaNotFoundError: when the YAML file is missing.
        FileNotFoundError: when `corpus_path` resolves to a path that
            does not exist on disk (empty directory is fine; missing
            directory fails loud).
        pydantic.ValidationError: when the YAML fails schema validation.
        yaml.YAMLError: when the YAML is malformed.
    """
    yaml_path = _persona_yaml_path(persona_ref)
    if not yaml_path.is_file():
        raise VoicePersonaNotFoundError(
            f"voice_personas/{persona_ref}.yaml not found at {yaml_path}. "
            f"Verify the persona ref or author a new persona YAML."
        )

    raw = yaml.safe_load(yaml_path.read_text())
    if not isinstance(raw, dict):
        raise ValueError(
            f"voice_personas/{persona_ref}.yaml must contain a mapping at the "
            f"top level (got {type(raw).__name__})."
        )

    persona = VoicePersona.model_validate(raw)

    resolved = _resolve_corpus_path(persona.corpus_path)
    if not resolved.exists():
        raise FileNotFoundError(
            f"voice_personas/{persona_ref}.yaml corpus_path resolves to "
            f"{resolved} which does not exist. Create the directory (it "
            f"may be empty pre-consent — see §Compliance Posture parallel-"
            f"track risk #1)."
        )
    return persona


def load_corpus_files(persona: VoicePersona) -> list[CorpusFile]:
    """Walk `persona.corpus_path` and return extracted text content per file.

    Per TD-56 cuts:
    - `.md` files are read as UTF-8 text.
    - `.pdf` files are extracted via PyMuPDF (fitz).
    - Any other extension raises `UnsupportedCorpusFormatError`. HTML +
      JSON loaders are deferred to the first SaaS-shaped corpus that
      needs them.

    The returned list is sorted by path for determinism. An empty
    corpus directory returns an empty list — lanes that depend on
    content fail loud at usage time, not here, so pre-consent personas
    remain loadable.
    """
    resolved = _resolve_corpus_path(persona.corpus_path)
    if not resolved.is_dir():
        raise NotADirectoryError(
            f"persona {persona.persona_slug!r} corpus_path {resolved} is not a directory."
        )

    files: list[CorpusFile] = []
    for entry in sorted(resolved.rglob("*")):
        if not entry.is_file():
            continue
        # Filesystem metadata (.gitkeep, .DS_Store, .gitignore) is not
        # corpus content; skip silently so empty consent-gated corpora
        # remain loadable.
        if entry.name.startswith("."):
            continue
        # Per the 4-agent review (sec-6): defend against symlink escape.
        # Klinika/DWF corpora may sync from external sources (Dropbox /
        # SharePoint) where an attacker-placed symlink → /etc/passwd
        # would otherwise fold into the persona corpus and ultimately
        # into LLM prompts. Resolve + check containment.
        try:
            entry_real = entry.resolve()
            entry_real.relative_to(resolved)
        except ValueError:
            logger.warning(
                "persona %r: skipping %s which symlinks outside corpus_path %s",
                persona.persona_slug, entry, resolved,
            )
            continue
        suffix = entry.suffix.lower()
        if suffix not in SUPPORTED_CORPUS_EXTENSIONS:
            raise UnsupportedCorpusFormatError(
                f"corpus file {entry} has extension {suffix!r}; supported "
                f"extensions are {sorted(SUPPORTED_CORPUS_EXTENSIONS)}. "
                f"HTML + JSON loaders are deferred to the first SaaS-shaped "
                f"client per TD-56."
            )
        if suffix == ".md":
            text = entry.read_text(encoding="utf-8")
            files.append(CorpusFile(path=entry, text=text, format="markdown"))
        elif suffix == ".pdf":
            text = _extract_pdf_text(entry)
            files.append(CorpusFile(path=entry, text=text, format="pdf"))
    return files


def _extract_pdf_text(pdf_path: Path) -> str:
    """Extract plain text from a PDF via PyMuPDF.

    Isolated as a separate helper so callers can mock the PyMuPDF
    dependency in tests; the import is deferred so test environments
    without PyMuPDF installed can still exercise the markdown path.
    """
    try:
        import fitz  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover — pymupdf is in main deps
        raise ImportError(
            "PyMuPDF (fitz) is required for PDF corpus extraction. "
            "Verify it's installed via the project's main dependencies."
        ) from exc

    chunks: list[str] = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            chunks.append(page.get_text())
    return "\n".join(chunks)


def compile_substrate(
    persona: VoicePersona, corpus_files: list[CorpusFile],
) -> str:
    """Concatenate persona corpus + optional rules/anchors into a single
    markdown substrate string.

    Used by lane `configure_env` hooks (linkedin_engine, x_engine, and
    future content lanes) to materialize the persona's compiled voice
    substrate into the runtime read path. Lifted out of linkedin_engine
    in U12 to avoid duplication across migrations.

    Shape contract:
    - Single corpus file + empty `voice_rules` + empty `style_anchors`
      → output is the corpus body verbatim. This is the structural-
      zero-regression guarantee the `jr` persona relies on (compiled
      substrate == pre-U11 voice.md byte-for-byte).
    - Multi-file corpus → bodies joined by ``\\n\\n---\\n\\n``.
    - Non-empty `voice_rules` → appended as a ``## Voice Rules`` bullet
      section.
    - Non-empty `style_anchors` → appended as ``## Style Anchors`` with
      each anchor under a ``### <name>`` heading.
    """
    parts = [cf.text for cf in corpus_files]
    body = "\n\n---\n\n".join(parts) if len(parts) > 1 else parts[0]

    suffix = ""
    if persona.voice_rules:
        bullets = "\n".join(f"- {rule}" for rule in persona.voice_rules)
        suffix += f"\n\n## Voice Rules\n\n{bullets}\n"
    if persona.style_anchors:
        chunks = [
            f"### {name}\n\n{prose.rstrip()}"
            for name, prose in persona.style_anchors.items()
        ]
        suffix += "\n\n## Style Anchors\n\n" + "\n\n".join(chunks) + "\n"
    return body + suffix


__all__ = [
    "SUPPORTED_CORPUS_EXTENSIONS",
    "CorpusFile",
    "UnsupportedCorpusFormatError",
    "VoicePersona",
    "VoicePersonaNotFoundError",
    "compile_substrate",
    "load_corpus_files",
    "load_persona",
]
