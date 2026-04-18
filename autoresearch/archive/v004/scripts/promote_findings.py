#!/usr/bin/env python3
"""Promote per-session findings into per-domain global findings."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

from workflows import WORKFLOW_SPECS

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class DomainConfig:
    session_dir: Path
    global_file: Path
    title: str
    confirmed_threshold: int
    repeated_threshold: int


DOMAIN_CONFIGS: dict[str, DomainConfig] = {
    domain: DomainConfig(
        session_dir=ROOT / "sessions" / domain,
        global_file=ROOT / f"{domain}-findings.md",
        title=spec.findings_promotion.title,
        confirmed_threshold=spec.findings_promotion.confirmed_threshold,
        repeated_threshold=spec.findings_promotion.repeated_threshold,
    )
    for domain, spec in WORKFLOW_SPECS.items()
}

GLOBAL_SECTIONS = ("Always Apply", "Watch For", "Disproved", "Never Do", "Raw / Unprocessed")
PLACEHOLDER_SNIPPETS = (
    "example:",
    "title here",
    "description of what was confirmed",
    "description of why this was disproved",
    "neutral observation for future reference",
)


@dataclass
class Finding:
    section: str
    category: str
    title: str
    evidence: str
    detail: str


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", text.lower())).strip()


def _extract_detail_sentence(text: str) -> str:
    cleaned = " ".join(text.split())
    if not cleaned:
        return ""
    sentence = re.split(r"(?<=[.!?])\s+", cleaned, maxsplit=1)[0]
    return sentence[:220].rstrip(". ")


def _is_placeholder(finding: Finding) -> bool:
    text = " ".join(
        part for part in (finding.title, finding.evidence, finding.detail) if part
    ).lower()
    return any(snippet in text for snippet in PLACEHOLDER_SNIPPETS)


def parse_findings(text: str) -> list[Finding]:
    findings: list[Finding] = []
    current_section: str | None = None
    current: Finding | None = None

    def flush() -> None:
        nonlocal current
        if current and current.title and not _is_placeholder(current):
            findings.append(current)
        current = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        section_match = re.match(r"^##\s+(.+)$", line)
        if section_match:
            flush()
            current_section = section_match.group(1).strip()
            continue

        heading = re.match(r"^###\s+\[(.+?)\]\s+(.+)$", line)
        if heading:
            flush()
            current = Finding(
                section=current_section or "",
                category=heading.group(1).strip(),
                title=heading.group(2).strip(),
                evidence="",
                detail="",
            )
            continue

        if current is None:
            continue

        evidence = re.match(r"^\s*[-*]\s+\*\*Evidence:\*\*\s*(.+)$", line)
        if evidence:
            current.evidence = evidence.group(1).strip()
            continue

        detail = re.match(r"^\s*[-*]\s+\*\*Detail:\*\*\s*(.+)$", line)
        if detail:
            current.detail = detail.group(1).strip()
            continue

    flush()
    return findings


def _render_summary(finding: Finding, clients: set[str], label: str) -> str:
    title = finding.title
    if finding.category:
        title = f"[{finding.category}] {title}"
    detail = _extract_detail_sentence(finding.detail)
    suffix = f" ({label}: {', '.join(sorted(clients))})"
    return f"{title} — {detail}{suffix}" if detail else f"{title}{suffix}"


def _parse_global_sections(text: str) -> tuple[str, dict[str, list[str]]]:
    header_match = re.match(r"^(.*?)(?=^## )", text, re.DOTALL | re.MULTILINE)
    header = header_match.group(1) if header_match else ""
    sections: dict[str, list[str]] = {}
    current: str | None = None

    for line in text.splitlines():
        section_match = re.match(r"^##\s+(.+)$", line)
        if section_match:
            current = section_match.group(1).strip()
            sections.setdefault(current, [])
            continue
        if current is not None:
            sections[current].append(line)

    return header, sections


def _existing_normalized(sections: dict[str, list[str]]) -> set[str]:
    norms: set[str] = set()
    for lines in sections.values():
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(("- ", "* ")):
                stripped = stripped[2:].strip()
            normalized = _normalize(stripped)
            if normalized:
                norms.add(normalized)
    return norms


def _load_all_findings(config: DomainConfig) -> dict[str, list[Finding]]:
    findings_by_client: dict[str, list[Finding]] = {}
    if not config.session_dir.exists():
        return findings_by_client

    for client_dir in sorted(config.session_dir.iterdir()):
        if not client_dir.is_dir():
            continue
        findings_file = client_dir / "findings.md"
        if not findings_file.exists():
            continue
        parsed = parse_findings(findings_file.read_text())
        if parsed:
            findings_by_client[client_dir.name] = parsed
    return findings_by_client


def promote_domain(domain: str, dry_run: bool = False) -> None:
    config = DOMAIN_CONFIGS[domain]
    findings_by_client = _load_all_findings(config)

    if not findings_by_client:
        print(f"{domain}: no client findings found")
        return

    confirmed: dict[str, tuple[Finding, set[str]]] = {}
    repeated: dict[str, tuple[Finding, set[str]]] = {}

    for client, findings in findings_by_client.items():
        for finding in findings:
            key = _normalize(f"[{finding.category}] {finding.title}")
            if not key:
                continue
            bucket = confirmed if finding.section == "Confirmed" else repeated
            if key not in bucket:
                bucket[key] = (finding, set())
            bucket[key][1].add(client)

    promoted_lines: list[str] = []

    for finding, clients in (
        item for item in confirmed.values() if len(item[1]) >= config.confirmed_threshold
    ):
        promoted_lines.append(_render_summary(finding, clients, "confirmed by"))

    for finding, clients in (
        item for item in repeated.values() if len(item[1]) >= config.repeated_threshold
    ):
        promoted_lines.append(_render_summary(finding, clients, "seen in"))

    if config.global_file.exists():
        existing_text = config.global_file.read_text()
    else:
        existing_text = (
            f"# {config.title}\n\n"
            "## Always Apply\n\n"
            "## Watch For\n\n"
            "## Disproved\n\n"
            "## Never Do\n\n"
            "## Raw / Unprocessed\n"
        )

    header, sections = _parse_global_sections(existing_text)
    existing_norms = _existing_normalized(sections)
    new_lines = [
        f"- {line}" for line in promoted_lines if _normalize(line) not in existing_norms
    ]

    if not new_lines:
        print(f"{domain}: no new findings to append")
        return

    if dry_run:
        print(f"{domain}: would append {len(new_lines)} finding(s)")
        for line in new_lines:
            print(f"  {line}")
        return

    sections.setdefault("Raw / Unprocessed", [])
    sections["Raw / Unprocessed"].extend(new_lines)

    out_parts = [header.rstrip("\n") or f"# {config.title}"]
    for section_name in GLOBAL_SECTIONS:
        if section_name in sections:
            out_parts.append(f"\n\n## {section_name}")
            body = "\n".join(sections[section_name]).strip()
            if body:
                out_parts.append(body)
    for section_name, lines in sections.items():
        if section_name in GLOBAL_SECTIONS:
            continue
        out_parts.append(f"\n\n## {section_name}")
        body = "\n".join(lines).strip()
        if body:
            out_parts.append(body)
    out_parts.append("")

    config.global_file.write_text("\n".join(out_parts))
    print(f"{domain}: appended {len(new_lines)} finding(s) to {config.global_file}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("domain", nargs="?", choices=sorted(DOMAIN_CONFIGS))
    parser.add_argument("--all", action="store_true", dest="all_domains")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    domains = sorted(DOMAIN_CONFIGS) if args.all_domains or not args.domain else [args.domain]
    for domain in domains:
        promote_domain(domain, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
