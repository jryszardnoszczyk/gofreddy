from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class CrossItemCriterion:
    glob: str
    max_items: int
    words_per_item: int | None = None


@dataclass(frozen=True)
class SessionEvalSpec:
    domain: str
    domain_name: str
    criteria: dict[str, str]
    structural_gate: Callable[[str, Path, Path], list[str]]
    load_source_data: Callable[[str, Path, Path], str]
    per_story_criteria: tuple[str, ...] = ()
    cross_item_criteria: dict[str, CrossItemCriterion] = field(default_factory=dict)


def criteria_for_mode(spec: SessionEvalSpec, mode: str) -> dict[str, str]:
    if mode == "per-story" and spec.per_story_criteria:
        return {key: value for key, value in spec.criteria.items() if key in spec.per_story_criteria}
    return spec.criteria


def truncate(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + f"\n\n[... truncated at {max_words} words]"


def count_regex(text: str, pattern: str) -> int:
    """Used by competitive's structural_gate (CI banned-phrase / SOV checks)."""
    return len(re.findall(pattern, text, re.IGNORECASE | re.MULTILINE))


def load_results_entries(session_dir: Path) -> list[dict]:
    results_file = session_dir / "results.jsonl"
    entries: list[dict] = []
    if not results_file.exists():
        return entries
    for line in results_file.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            entries.append(payload)
    return entries
