"""Voice persona framework (R20) — shared across content lanes."""

from src.voice.persona import (
    SUPPORTED_CORPUS_EXTENSIONS,
    CorpusFile,
    UnsupportedCorpusFormatError,
    VoicePersona,
    VoicePersonaNotFoundError,
    load_corpus_files,
    load_persona,
)

__all__ = [
    "SUPPORTED_CORPUS_EXTENSIONS",
    "CorpusFile",
    "UnsupportedCorpusFormatError",
    "VoicePersona",
    "VoicePersonaNotFoundError",
    "load_corpus_files",
    "load_persona",
]
