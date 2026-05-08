"""Isolated subprocess entrypoint for ``build_critique_prompt`` (R-#24).

Runs as ``python3 -I -m autoresearch.harness.prompt_builder_entrypoint``
(typically via the ``-c`` bootstrap that does ``sys.path.insert(0, REPO_ROOT)``
+ ``runpy.run_module(...)``). The ``-I`` flag makes Python ignore
``PYTHONPATH`` / user site-packages / ``PYTHON*`` env vars — only the
caller-injected ``REPO_ROOT`` on ``sys.path`` is visible.

Protocol
--------
stdin  (JSON): ``{"criteria": [{"domain_name", "criterion_id",
                                "criterion_definition",
                                "cross_item_context"}, ...]}``
stdout (JSON): ``{"prompts": [{"criterion_id", "prompt"}, ...]}``
Non-zero exit on a rogue-package check failure, import error, or
missing/invalid input. Error text goes to stderr so the caller can
surface it.

Threat model and defense
------------------------
The threat: a rogue package on ``PYTHONPATH`` (planted by a malicious
variant under its own worktree, or smuggled via a ``.pth`` file) that
redefines ``autoresearch.harness.session_evaluator.build_critique_prompt``
to return a softer prompt. ``python3 -I`` already drops PYTHONPATH; the
residual risk is a same-named ``autoresearch/`` package smuggled in via
the ``-c`` bootstrap's explicit ``sys.path.insert(0, REPO_ROOT)`` — i.e.,
``REPO_ROOT`` itself was tampered with.

The defense: the caller passes ``AUTORESEARCH_EXPECTED_REPO_ROOT`` in the
subprocess environment (one of the few env vars Python's ``-I`` lets
through, since it's not a ``PYTHON*`` name). After importing the target
symbol, we verify ``autoresearch.__file__`` resolves under that path. If
the rogue package on ``REPO_ROOT`` won the import race, this check
catches it and exits 2.

Replaces a previous 80-prefix ``sys.modules`` allowlist (commit
``c120815``, 2026-05-07) that coupled to CPython's stdlib import graph
and false-positived an entire validation run when 3.13's ``runpy``
started loading ``urllib`` / ``ipaddress``.
"""

from __future__ import annotations

import json
import os
import sys


# Import the target symbol before the rogue-package check so that, if a
# rogue ``autoresearch/`` package on ``sys.path[0]`` shadows the real
# one, ``autoresearch.__file__`` reflects the path that was actually
# resolved — not what we hoped to resolve.
from autoresearch.harness.session_evaluator import build_critique_prompt


def _enforce_no_rogue_autoresearch() -> None:
    """Verify the loaded ``autoresearch`` package resolves under REPO_ROOT.

    The bootstrap's ``-c`` snippet does ``sys.path.insert(0, REPO_ROOT)``
    — so the only way ``autoresearch.harness.session_evaluator`` could
    resolve to anything other than the canonical file is a same-named
    package on REPO_ROOT itself. This check verifies that didn't happen.

    No-op when the caller hasn't pinned a path (back-compat for any
    direct invocations without env-var setup).
    """
    import autoresearch

    expected = os.environ.get("AUTORESEARCH_EXPECTED_REPO_ROOT")
    if not expected:
        return  # backward compat — caller didn't pin a path
    autoresearch_path = os.path.realpath(autoresearch.__file__)
    expected_real = os.path.realpath(expected)
    if not autoresearch_path.startswith(expected_real):
        sys.stderr.write(
            f"prompt_builder_entrypoint: autoresearch resolved to "
            f"{autoresearch_path}, expected under {expected_real}\n"
        )
        raise SystemExit(2)


def main() -> int:
    _enforce_no_rogue_autoresearch()

    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"prompt_builder_entrypoint: invalid JSON on stdin: {exc}\n")
        return 3

    criteria = payload.get("criteria")
    if not isinstance(criteria, list):
        sys.stderr.write(
            "prompt_builder_entrypoint: payload missing 'criteria' list\n"
        )
        return 3

    prompts: list[dict[str, str]] = []
    for entry in criteria:
        if not isinstance(entry, dict):
            sys.stderr.write(
                "prompt_builder_entrypoint: criterion entry is not a dict\n"
            )
            return 3
        try:
            prompt = build_critique_prompt(
                domain_name=str(entry["domain_name"]),
                criterion_id=str(entry["criterion_id"]),
                criterion_definition=str(entry["criterion_definition"]),
                cross_item_context=(
                    None
                    if entry.get("cross_item_context") is None
                    else str(entry["cross_item_context"])
                ),
            )
        except KeyError as exc:
            sys.stderr.write(
                f"prompt_builder_entrypoint: criterion missing field {exc}\n"
            )
            return 3
        prompts.append(
            {
                "criterion_id": str(entry["criterion_id"]),
                "prompt": prompt,
            }
        )

    json.dump({"prompts": prompts}, sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
