"""Finding dataclass + YAML-front-matter markdown parser + routing.

Evaluator writes one YAML-front-matter block per finding. parse() reads them back.
route() partitions into (actionable, review) — actionable is high-confidence defects.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

DEFECT_CATEGORIES: tuple[str, ...] = (
    "crash",
    "5xx",
    "console-error",
    "self-inconsistency",
    "dead-reference",
)
ALL_CATEGORIES: tuple[str, ...] = DEFECT_CATEGORIES + ("doc-drift", "low-confidence")
CONFIDENCES: tuple[str, ...] = ("high", "medium", "low")
TRACKS: tuple[str, ...] = ("a", "b", "c")

_BLOCK_RE = re.compile(r"^---\s*$\n(.*?)\n^---\s*$\n(.*?)(?=\n^---\s*$\n|\Z)", re.MULTILINE | re.DOTALL)


@dataclass(frozen=True)
class Finding:
    id: str
    track: str
    category: str
    confidence: str
    summary: str
    evidence: str = ""
    reproduction: str = ""
    files: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_block(cls, front: dict, body: str) -> "Finding":
        category = str(front.get("category", "")).strip()
        confidence = str(front.get("confidence", "")).strip()
        track = str(front.get("track", "")).strip()
        if category not in ALL_CATEGORIES:
            raise ValueError(f"unknown category: {category!r}")
        if confidence not in CONFIDENCES:
            raise ValueError(f"unknown confidence: {confidence!r}")
        if track not in TRACKS:
            raise ValueError(f"unknown track: {track!r}")
        files = front.get("files") or []
        if isinstance(files, str):
            files = [files]
        return cls(
            id=str(front.get("id", "")).strip(),
            track=track,
            category=category,
            confidence=confidence,
            summary=str(front.get("summary", "")).strip(),
            evidence=body.strip(),
            reproduction=str(front.get("reproduction", "")).strip(),
            files=tuple(str(f) for f in files),
        )


def parse(path: Path) -> list[Finding]:
    """Read a findings markdown file; return one Finding per YAML block. Empty -> []."""
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return []
    findings: list[Finding] = []
    for match in _BLOCK_RE.finditer(text):
        front_text, body = match.group(1), match.group(2)
        try:
            front = yaml.safe_load(front_text) or {}
        except yaml.YAMLError as exc:
            raise ValueError(f"malformed YAML in {path.name}: {exc}") from exc
        if not isinstance(front, dict):
            raise ValueError(f"YAML front-matter must be a mapping in {path.name}")
        findings.append(Finding.from_block(front, body))
    return findings


def route(findings: list[Finding]) -> tuple[list[Finding], list[Finding]]:
    """Partition findings into (actionable, review).

    Actionable = category in DEFECT_CATEGORIES AND confidence == "high".
    Everything else — doc-drift, low-confidence, medium-confidence defects — goes to review.
    """
    actionable: list[Finding] = []
    review: list[Finding] = []
    for f in findings:
        if f.category in DEFECT_CATEGORIES and f.confidence == "high":
            actionable.append(f)
        else:
            review.append(f)
    return actionable, review
