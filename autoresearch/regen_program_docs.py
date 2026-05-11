"""Regenerate the ``## Structural Validator Requirements`` section in each
``programs/<domain>-session.md`` from the lane registry's structural-doc-facts.

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

from lane_registry import (  # noqa: E402
    DOMAIN_FILENAMES,
    STRUCTURAL_DOC_FACTS,
)

START_MARKER = "<!-- AUTOGEN:STRUCTURAL:START -->"
END_MARKER = "<!-- AUTOGEN:STRUCTURAL:END -->"

SECTION_HEADING = "## Structural Validator Requirements"

PREAMBLE = (
    "*Do not edit content between `<!-- AUTOGEN:STRUCTURAL:START -->` "
    "and `<!-- AUTOGEN:STRUCTURAL:END -->` — it is regenerated from the "
    "lane registry on every variant clone; hand-edits are overwritten.*"
)


def _read_variant_doc_facts(programs_dir: Path | None, domain: str) -> tuple[str, ...] | None:
    """Look for ``STRUCTURAL_DOC_FACTS`` in the variant's session_eval module.

    The variant lives at ``<programs_dir>/../workflows/session_eval_<domain>.py``.
    A meta-agent that mutates the gate function should also update this
    constant; doing so makes the variant's doc bullets the source of
    truth for *its* prompt, and a drift-detection test catches divergence
    from the live registry.

    Reads via AST instead of importing — variant modules use relative
    imports (``from .session_eval_common import ...``) that fail without
    a package parent, and we don't need to execute their code, only read
    a literal tuple-of-strings constant. AST parse is safer and faster.

    Returns None when no programs_dir is provided, the workflow file is
    missing, the parse fails, or the constant isn't a tuple-of-string-
    literals. Falling back to the live registry preserves backward compat.
    """
    if programs_dir is None:
        return None
    workflow_path = (Path(programs_dir).resolve().parent
                     / "workflows" / f"session_eval_{domain}.py")
    if not workflow_path.is_file():
        return None
    try:
        import ast
        tree = ast.parse(workflow_path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError) as exc:
        print(
            f"regen_program_docs: variant workflow parse failed for "
            f"{workflow_path} ({exc!r}); falling back to live registry.",
            file=sys.stderr,
        )
        return None
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        target_names: list[str] = []
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name):
                    target_names.append(tgt.id)
        elif isinstance(node.target, ast.Name):
            target_names.append(node.target.id)
        if "STRUCTURAL_DOC_FACTS" not in target_names:
            continue
        value = node.value
        if not isinstance(value, ast.Tuple):
            return None
        bullets: list[str] = []
        for elt in value.elts:
            # Accept a string literal OR a concatenation of string literals
            # (the marketing_audit constant uses implicit string concat).
            literal = _extract_str_literal(elt)
            if literal is None:
                return None
            bullets.append(literal)
        return tuple(bullets)
    return None


def _extract_str_literal(node: object) -> str | None:
    """Return a string when ``node`` is a string literal or a concatenation of them."""
    import ast as _ast
    if isinstance(node, _ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, _ast.BinOp) and isinstance(node.op, _ast.Add):
        left = _extract_str_literal(node.left)
        right = _extract_str_literal(node.right)
        if left is None or right is None:
            return None
        return left + right
    return None


def _build_block(domain: str, programs_dir: Path | None = None) -> str:
    """Render the AUTOGEN block body for a domain.

    Reads the variant's ``workflows/session_eval_<domain>.py`` first when
    ``programs_dir`` is provided — that file lives next to the prompt and
    is the source of truth for *that variant's* gates. Falls back to the
    live ``lane_registry.STRUCTURAL_DOC_FACTS`` for variants that don't
    expose the constant (backward compat).
    """
    variant_bullets = _read_variant_doc_facts(programs_dir, domain)
    bullets = list(variant_bullets) if variant_bullets is not None else STRUCTURAL_DOC_FACTS.get(domain, [])
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


def regen_one(path: Path, domain: str, programs_dir: Path | None = None) -> bool:
    """Regenerate the AUTOGEN block in a single program file.

    Returns True if the file was modified.
    """
    original = path.read_text(encoding="utf-8")
    block = _build_block(domain, programs_dir=programs_dir)

    updated = _replace_existing_section(original, block)
    if updated is None:
        updated = _insert_new_section(original, block)

    if updated == original:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def regen(
    programs_dir: Path | str, lane: str | None = None,
) -> dict[str, bool]:
    """Regenerate ``*-session.md`` files under a programs dir.

    With ``lane=None`` (default), regenerates every known session-md file —
    used by the live ``run.py`` bootstrap before any session, where every
    domain may run.

    With ``lane="<name>"``, regenerates only that lane's session-md file
    (e.g. lane=``x_engine`` → only ``programs/x_engine-session.md``).
    Used by the evolve clone path so an x_engine variant doesn't surface
    cross-lane edits to ``programs/geo-session.md`` from drift between
    parent's AUTOGEN block and what ``_build_block`` currently produces
    — cf. Finding #115 / lineage of v014 + v020.

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

    if lane is not None and lane in DOMAIN_FILENAMES:
        targets: dict[str, str] = {lane: DOMAIN_FILENAMES[lane]}
    else:
        targets = dict(DOMAIN_FILENAMES)

    results: dict[str, bool] = {}
    for domain, filename in targets.items():
        target = programs_path / filename
        if not target.is_file():
            print(
                f"regen_program_docs: skip (missing): {target}",
                file=sys.stderr,
            )
            continue
        try:
            results[filename] = regen_one(target, domain, programs_dir=programs_path)
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
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m autoresearch.regen_program_docs",
        description=(
            "Regenerate the AUTOGEN structural-validator block in each "
            "programs/<domain>-session.md from STRUCTURAL_DOC_FACTS."
        ),
    )
    parser.add_argument(
        "programs_dir",
        help="Path to the programs directory containing *-session.md files.",
    )
    args = parser.parse_args(argv[1:])

    results = regen(args.programs_dir)
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
