"""Regenerate the ``## Structural Validator Requirements`` section in each
``programs/<domain>-session.md`` from ``STRUCTURAL_DOC_FACTS`` in
``src/evaluation/structural.py``.

Single source of truth for structural-validator docs. Called on every
variant clone from ``autoresearch/evolve.py`` so the program docs can
never drift from the validator code — the live 5x drift bug this
module exists to fix.

Usage (one-time bootstrap, fixes today's drifted docs):
    python3 -m autoresearch.regen_program_docs <programs-dir>

The runtime call site wraps this in the clone sequence so the meta
agent's session programs are always in sync with the validator.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running as a module from a checkout where src/ is not on sys.path.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.evaluation.structural import STRUCTURAL_DOC_FACTS  # noqa: E402

START_MARKER = "<!-- AUTOGEN:STRUCTURAL:START -->"
END_MARKER = "<!-- AUTOGEN:STRUCTURAL:END -->"

SECTION_HEADING = "## Structural Validator Requirements"

PREAMBLE = (
    "*Do not edit content between `<!-- AUTOGEN:STRUCTURAL:START -->` "
    "and `<!-- AUTOGEN:STRUCTURAL:END -->` — it is regenerated from "
    "`structural.py` on every variant clone; hand-edits are overwritten.*"
)

DOMAIN_FILENAMES: dict[str, str] = {
    "competitive": "competitive-session.md",
    "monitoring": "monitoring-session.md",
    "geo": "geo-session.md",
    "storyboard": "storyboard-session.md",
}


def _build_block(domain: str) -> str:
    """Render the AUTOGEN block body for a domain."""
    bullets = STRUCTURAL_DOC_FACTS.get(domain, [])
    if not bullets:
        return (
            f"{START_MARKER}\n"
            f"_No structural gates defined for `{domain}`._\n"
            f"{END_MARKER}\n"
        )
    lines = [
        START_MARKER,
        f"The structural validator for **{domain}** enforces these gates — "
        "all must pass:",
        "",
    ]
    lines.extend(f"- {bullet}" for bullet in bullets)
    lines.append(END_MARKER)
    return "\n".join(lines) + "\n"


def _replace_existing_section(text: str, block: str) -> str | None:
    """If ``## Structural Validator Requirements`` is present, rewrite it.

    Returns the updated text, or None if the section header isn't found.
    The AUTOGEN block replaces everything from the heading through the
    next ``## ``-level heading (exclusive) — the heading itself is kept.
    """
    lines = text.splitlines(keepends=True)
    start_idx: int | None = None
    for i, line in enumerate(lines):
        if line.strip() == SECTION_HEADING:
            start_idx = i
            break
    if start_idx is None:
        return None

    # Find the next H2 heading after start_idx (exclusive).
    end_idx = len(lines)
    for j in range(start_idx + 1, len(lines)):
        stripped = lines[j].lstrip()
        if stripped.startswith("## ") and not stripped.startswith("### "):
            end_idx = j
            break

    new_section = f"{SECTION_HEADING}\n\n{PREAMBLE}\n\n{block}"
    if end_idx < len(lines):
        # Preserve a single blank line separator before the next heading.
        new_section = new_section.rstrip("\n") + "\n\n"
    replaced = "".join(lines[:start_idx]) + new_section + "".join(lines[end_idx:])
    return replaced


def _insert_new_section(text: str, block: str) -> str:
    """Insert a new section before ``## Notes`` if present, else append."""
    lines = text.splitlines(keepends=True)
    section = f"{SECTION_HEADING}\n\n{PREAMBLE}\n\n{block}"

    # Look for "## Notes" insertion point.
    for i, line in enumerate(lines):
        if line.strip() == "## Notes":
            insert = section.rstrip("\n") + "\n\n"
            return "".join(lines[:i]) + insert + "".join(lines[i:])

    # Otherwise append to end-of-file with a leading blank line.
    trailing = "" if text.endswith("\n") else "\n"
    return text + trailing + "\n" + section


def regen_one(path: Path, domain: str) -> bool:
    """Regenerate the AUTOGEN block in a single program file.

    Returns True if the file was modified.
    """
    original = path.read_text(encoding="utf-8")
    block = _build_block(domain)

    updated = _replace_existing_section(original, block)
    if updated is None:
        updated = _insert_new_section(original, block)

    if updated == original:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def regen(programs_dir: Path | str) -> dict[str, bool]:
    """Regenerate all known ``*-session.md`` files under a programs dir.

    Returns ``{filename: was_modified}`` — missing files are skipped with
    a warning.
    """
    programs_path = Path(programs_dir)
    if not programs_path.is_dir():
        print(
            f"regen_program_docs: programs dir not found: {programs_path}",
            file=sys.stderr,
        )
        return {}

    results: dict[str, bool] = {}
    for domain, filename in DOMAIN_FILENAMES.items():
        target = programs_path / filename
        if not target.is_file():
            print(
                f"regen_program_docs: skip (missing): {target}",
                file=sys.stderr,
            )
            continue
        try:
            results[filename] = regen_one(target, domain)
        except OSError as exc:
            print(
                f"regen_program_docs: failed to update {target}: {exc}",
                file=sys.stderr,
            )
            results[filename] = False

    # Sanity check: every declared domain in STRUCTURAL_DOC_FACTS must map
    # to a known filename. Drop-through here means someone added a domain
    # without wiring it up.
    missing = set(STRUCTURAL_DOC_FACTS) - set(DOMAIN_FILENAMES)
    if missing:
        print(
            f"regen_program_docs: WARNING — STRUCTURAL_DOC_FACTS has "
            f"domains with no filename mapping: {sorted(missing)}",
            file=sys.stderr,
        )

    return results


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(
            "Usage: python3 -m autoresearch.regen_program_docs <programs-dir>",
            file=sys.stderr,
        )
        return 2
    results = regen(argv[1])
    updated = sum(1 for changed in results.values() if changed)
    print(
        f"regen_program_docs: {updated} of {len(results)} files updated",
        file=sys.stderr,
    )
    for filename, changed in results.items():
        print(f"  {'UPDATED' if changed else 'unchanged'}  {filename}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
