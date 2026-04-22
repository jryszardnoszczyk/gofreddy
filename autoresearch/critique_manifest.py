"""SHA256 manifest for the five frozen critique-prompt symbols (R-#13).

Autoresearch is a self-modifying meta-loop: variants rewrite their own
`programs/*.md`. A variant that tampered with `build_critique_prompt` or
its threshold constants could score itself higher in Layer 2 and escape
the evaluator silently. The honor-system note in
`archive/current_runtime/meta.md` is social, not enforced.

This module converts that note into a gated invariant. It hashes the
canonical source of each frozen symbol from the running interpreter via
``inspect.getsource`` and returns a deterministic ``{name: sha256}``
mapping. Evolve writes the manifest at clone time; Layer 1 validation
re-computes hashes inside a ``python3 -I`` subprocess and refuses to run
variants whose bundled manifest disagrees with what the freshly imported
symbols produce.

Canonical source: ``autoresearch/harness/session_evaluator.py``.
"""

from __future__ import annotations

import hashlib
import inspect

from autoresearch.harness import session_evaluator

# The five frozen symbols. Order is stable across invocations; callers
# that want a subset should filter from the returned dict rather than
# reorder the source of truth.
FROZEN_SYMBOLS: tuple[str, ...] = (
    "DEFAULT_PASS_THRESHOLD",
    "HARD_FAIL_THRESHOLD",
    "GRADIENT_CRITIQUE_TEMPLATE",
    "build_critique_prompt",
    "compute_decision_threshold",
)


def _symbol_source(name: str) -> str:
    """Return the exact source text that defines *name*.

    For module-level constants ``inspect.getsource`` doesn't work — it
    expects a class/function/module. Fall back to finding the exact
    assignment line(s) in the module source.
    """
    obj = getattr(session_evaluator, name)
    try:
        return inspect.getsource(obj)
    except TypeError:
        # Module-level constant (int/float/str). Locate its assignment
        # block in the module source. This handles single-line
        # constants and multi-line string literals equally well
        # because a bare name cannot appear on the LHS of ``=``
        # anywhere else in well-formed Python.
        module_src = inspect.getsource(session_evaluator)
        lines = module_src.splitlines(keepends=True)
        prefix = f"{name} ="
        collected: list[str] = []
        in_block = False
        for line in lines:
            if not in_block and line.startswith(prefix):
                in_block = True
                collected.append(line)
                # Single-line assignment? Detect by closing a bare
                # literal on this line — a rough heuristic: the line
                # ends with a quote/digit/closing bracket and the
                # open-quote count is even.
                stripped = line.rstrip("\n").rstrip()
                if stripped.count('"""') % 2 == 0 and not stripped.endswith(("(", "[", "{", "\\")):
                    break
                continue
            if in_block:
                collected.append(line)
                if line.rstrip().endswith('"""'):
                    break
                if line.strip() and not line.startswith((" ", "\t")) and not line.startswith('"""'):
                    # Hit next top-level statement, stop before it.
                    collected.pop()
                    break
        if not collected:
            raise RuntimeError(
                f"critique_manifest: could not locate source of {name!r} "
                f"in {session_evaluator.__file__}"
            )
        return "".join(collected)


def compute_expected_hashes() -> dict[str, str]:
    """Return ``{symbol_name: sha256_hex}`` for all frozen symbols.

    Deterministic: ``inspect.getsource`` reads the `.py` file from disk
    on each call, so two calls within the same process return identical
    hashes as long as the source hasn't been edited between them.
    """
    result: dict[str, str] = {}
    for name in FROZEN_SYMBOLS:
        src = _symbol_source(name)
        result[name] = hashlib.sha256(src.encode("utf-8")).hexdigest()
    return result


if __name__ == "__main__":
    import json

    print(json.dumps(compute_expected_hashes(), indent=2, sort_keys=True))
