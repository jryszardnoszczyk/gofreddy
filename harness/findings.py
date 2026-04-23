"""Finding dataclass + YAML-front-matter markdown parser + routing.

Evaluator writes one YAML-front-matter block per finding. parse() reads them back.
route() partitions into (actionable, review) — actionable is high-confidence defects.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

log = logging.getLogger("harness.findings")

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
    cycle: int = 1
    evidence: str = ""
    reproduction: str = ""
    files: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_block(cls, front: dict, body: str, *, cycle: int = 1) -> "Finding":
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
            cycle=cycle,
            evidence=body.strip(),
            reproduction=str(front.get("reproduction", "")).strip(),
            files=tuple(str(f) for f in files),
        )


def parse(path: Path, *, cycle: int = 1) -> list[Finding]:
    """Read a findings markdown file; return one Finding per YAML block. Empty -> [].

    Malformed blocks are logged and skipped — one bad YAML value must not
    cause the caller to lose every other finding in the file.

    `cycle` scopes each finding to its evaluator cycle. Evaluators start
    numbering from 1 each cycle, so `F-c-1-5` in cycle 1 and `F-c-1-5` in
    cycle 2 are different findings. The cycle stamp disambiguates them
    in commit subjects and resume-skip checks.
    """
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return []
    findings: list[Finding] = []
    for idx, match in enumerate(_BLOCK_RE.finditer(text), start=1):
        front_text, body = match.group(1), match.group(2)
        try:
            front = yaml.safe_load(front_text) or {}
            if not isinstance(front, dict):
                raise ValueError("YAML front-matter must be a mapping")
            findings.append(Finding.from_block(front, body, cycle=cycle))
        except (yaml.YAMLError, ValueError) as exc:
            log.warning("skipping malformed finding block #%d in %s: %s", idx, path.name, exc)
            continue
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
