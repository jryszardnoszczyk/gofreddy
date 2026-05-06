"""Deterministic slop detection. Banned phrases + n-gram dedup vs exemplars."""
from __future__ import annotations

import re
from pathlib import Path

# Tier-1: hard-banned phrases (must reject)
BANNED_PHRASES = [
    # Opening tells
    r"\bmost people don'?t realize\b",
    r"\bhere'?s the thing\b",
    r"\bhere'?s why\b",
    r"\bit turns out\b",
    r"\bin a world where\b",
    r"\bif you'?re not (?:\w+ )?already behind\b",
    r"\bdid you know\b",
    r"\bhave you ever wondered\b",
    r"\blet me tell you about\b",
    r"\bimagine this:",
    r"\bpicture this:",
    # Hot-take telegraphs
    r"\bhot take:",
    r"\bunpopular opinion:",
    r"\bpsa:",
    r"\bpro tip:",
    r"🚨\s*breaking:",
    r"\bicymi:",
    # Engagement bait
    r"\bbookmark this\b",
    r"\bsave this (?:thread|post|for later)\b",
    r"\blike (?:and|\+) (?:rt|retweet)\b",
    r"\bfollow for more\b",
    r"\btag a friend\b",
    r"\bdrop your thoughts below\b",
    # Mid-sentence slop
    r"\bdives into\b",
    r"\bdelves into\b",
    r"\bnavigates the (?:landscape|realm|ecosystem) of\b",
    r"\bin the realm of\b",
    r"\bat the intersection of\b",
    r"\bever-evolving landscape\b",
    r"\brapidly changing\b",
    r"\bcutting-edge\b",
    r"\bgame-chang(?:er|ing)\b",
    r"\brevolutionary\b",
    r"\bgroundbreaking\b",
    r"\btapestry\b",
    r"\bembark on a journey\b",
    r"\bharness the power of\b",
    r"\bsupercharge\b",
    r"\bneedle-mover\b",
    # Hedge filler
    r"\bit'?s important to note that\b",
    r"\bit'?s worth noting that\b",
    r"\bit'?s worth mentioning that\b",
    r"\bit should be noted that\b",
    # Conclusions
    r"\bin conclusion,\b",
    r"\bto summarize,\b",
    r"\bto wrap up,\b",
    r"\bat the end of the day,\b",
    r"\bwhen all is said and done,\b",
]

# Tier-1.5: characters
EM_DASH_PATTERN = re.compile(r"[—–]")  # em-dash and en-dash

# Tier-2: parallel-structure formulas
PARALLEL_PATTERNS = [
    re.compile(r"\bNot \w{3,15}\. \w{3,30}\.", re.IGNORECASE),
    re.compile(r"\bIt'?s not \w[\w\s]{2,30}\.\s+It'?s \w[\w\s]{2,30}\.", re.IGNORECASE),
]


def _compile_banned() -> list[re.Pattern]:
    return [re.compile(p, re.IGNORECASE) for p in BANNED_PHRASES]


_compiled_banned = _compile_banned()


def check_text(text: str) -> tuple[bool, list[str]]:
    """Check text for slop. Returns (passed, flags)."""
    flags: list[str] = []
    for pat in _compiled_banned:
        if pat.search(text):
            flags.append(f"banned_phrase:{pat.pattern}")

    if EM_DASH_PATTERN.search(text):
        flags.append("em_dash")

    for pat in PARALLEL_PATTERNS:
        if pat.search(text):
            flags.append(f"parallel_structure:{pat.pattern[:40]}")

    return len(flags) == 0, flags


def ngram_overlap(text: str, corpus_text: str, n: int = 5) -> float:
    """Fraction of n-grams in `text` that also appear in `corpus_text`. 0..1."""
    def ngrams(s: str, n: int) -> set[str]:
        words = s.lower().split()
        return {" ".join(words[i : i + n]) for i in range(len(words) - n + 1)}

    text_ngrams = ngrams(text, n)
    if not text_ngrams:
        return 0.0
    corpus_ngrams = ngrams(corpus_text, n)
    overlap = text_ngrams & corpus_ngrams
    return len(overlap) / len(text_ngrams)


def check_against_exemplars(text: str, exemplars_path: Path, threshold: float = 0.20) -> tuple[bool, float]:
    """Reject text if too many 5-grams overlap with voice/exemplars.md."""
    if not exemplars_path.exists():
        return True, 0.0
    corpus = exemplars_path.read_text()
    overlap = ngram_overlap(text, corpus, n=5)
    return overlap < threshold, overlap


def check_full(text: str, exemplars_path: Path | None = None) -> dict:
    """Run all checks. Returns dict with all flags."""
    passed_phrases, phrase_flags = check_text(text)
    overlap = 0.0
    passed_ngram = True
    if exemplars_path:
        passed_ngram, overlap = check_against_exemplars(text, exemplars_path)
    return {
        "passed": passed_phrases and passed_ngram,
        "phrase_flags": phrase_flags,
        "ngram_overlap": overlap,
        "ngram_blocked": not passed_ngram,
    }
