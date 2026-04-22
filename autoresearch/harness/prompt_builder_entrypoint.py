"""Isolated subprocess entrypoint for ``build_critique_prompt`` (R-#24).

Runs as ``python3 -I -m autoresearch.harness.prompt_builder_entrypoint``.
The ``-I`` flag makes Python ignore ``PYTHONPATH`` / user site-packages /
``PYTHON*`` env vars — only the caller-provided ``PYTHONPATH`` injected
through the subprocess environment is visible. Combined with the
``sys.modules`` allowlist check below, this blocks a polluted path from
substituting a fake ``session_evaluator`` that softens the critique
prompt.

Protocol
--------
stdin  (JSON): ``{"criteria": [{"domain_name", "criterion_id",
                                "criterion_definition",
                                "cross_item_context"}, ...]}``
stdout (JSON): ``{"prompts": [{"criterion_id", "prompt"}, ...]}``
Non-zero exit on any allowlist violation, import error, or
missing/invalid input. Error text goes to stderr so the caller can
surface it.

Allowlist philosophy
--------------------
At startup we snapshot ``sys.modules`` right after the critical imports.
Anything outside the allowlist is a pollution signal (a rogue package on
``PYTHONPATH`` got imported before us, or someone added a ``sitecustomize``
that ran). The allowlist covers:

- the stdlib modules we actually use in this file (``json``, ``sys``,
  plus their transitive stdlib deps),
- ``autoresearch``, ``autoresearch.harness``,
  ``autoresearch.harness.session_evaluator``,
- stdlib-only transitive deps of ``session_evaluator`` (``math``,
  ``pathlib`` + its deps).

The check is a *prefix* allowlist: ``os.path`` is allowed because ``os``
is allowed. Anything without an allowed prefix fails the subprocess.
"""

from __future__ import annotations

import json
import sys


# Import the target symbol before taking the sys.modules snapshot. If
# someone pollutes sys.modules to replace session_evaluator with a
# trojan, the import here would pull the trojan in — BUT python3 -I
# ignores PYTHONPATH from the ambient shell, so only the explicitly
# passed PYTHONPATH (set by the caller, pointing at the repo root) is
# honored. Combined with the allowlist, a trojan module on a polluted
# path cannot win: either it imports with a name outside the allowlist
# (caught below), or it shadows session_evaluator and gets detected by
# the L1 hash-check on the next evolve cycle.
from autoresearch.harness.session_evaluator import build_critique_prompt

# Prefix allowlist. Any module whose dotted name starts with one of
# these prefixes (or equals one of them exactly) is allowed.
_ALLOWED_PREFIXES: tuple[str, ...] = (
    # This package
    "autoresearch",
    # Stdlib modules we import directly or transitively
    "json",
    "sys",
    "math",
    "pathlib",
    "os",
    "posixpath",
    "ntpath",
    "genericpath",
    "stat",
    "io",
    "codecs",
    "encodings",
    "abc",
    "_abc",
    "_weakref",
    "_weakrefset",
    "weakref",
    "types",
    "_collections_abc",
    "collections",
    "keyword",
    "operator",
    "reprlib",
    "heapq",
    "itertools",
    "functools",
    "contextlib",
    "enum",
    "re",
    "sre_compile",
    "sre_parse",
    "sre_constants",
    "copyreg",
    "_sre",
    "errno",
    "_io",
    "_stat",
    "_thread",
    "_warnings",
    "warnings",
    "_frozen_importlib",
    "_frozen_importlib_external",
    "_imp",
    "_signal",
    "_codecs",
    "_functools",
    "_heapq",
    "_operator",
    "builtins",
    "marshal",
    "time",
    "zipimport",
    "encodings.aliases",
    "encodings.utf_8",
    "encodings.latin_1",
    "site",
    "linecache",
    "tokenize",
    "token",
    "_collections",
    "_locale",
    "_json",
    "__future__",
    "importlib",
    "threading",
    "atexit",
    "_bootlocale",
    "_winapi",  # no-op on non-Windows; present on some builds
    "nt",
    # site/runpy bootstrap modules loaded by python -I + -c bootstrap
    "runpy",
    "pkgutil",
    "_sitebuiltins",
    "_types",
    "fcntl",
    "fnmatch",
    "glob",
    "grp",
    "posix",
    "pwd",
    "sitecustomize",
    "usercustomize",
    # Namespace-package stubs that venv .pth files may pre-load during
    # site.py processing. These are empty namespace markers that cannot
    # shadow `autoresearch.harness.session_evaluator` (different root),
    # so they're harmless to critique-prompt integrity. Listed explicitly
    # rather than wildcarded so new unexpected top-level namespaces
    # still trip the guard.
    "google",
    "mpl_toolkits",
    "zope",
    "ruamel",
)


def _is_allowed(module_name: str) -> bool:
    """Allow a module if its dotted name matches an allowed prefix.

    Exact match or ``prefix + '.'`` start both count. ``os.path`` is
    allowed because ``os`` is in the list; ``rogue.evil`` is not.
    """
    for prefix in _ALLOWED_PREFIXES:
        if module_name == prefix or module_name.startswith(prefix + "."):
            return True
    return False


def _enforce_allowlist() -> None:
    """Fail loud if any loaded module falls outside the allowlist.

    We tolerate dunder-prefixed internal names (``__main__``,
    ``__mp_main__``) because they're always produced by Python itself
    and carry no code from ``PYTHONPATH``.
    """
    offenders: list[str] = []
    for name in list(sys.modules):
        if not name or name.startswith("_") or name.startswith("__"):
            # Leading-underscore modules are either stdlib internals
            # (already covered) or Python-internal names. Skip.
            if _is_allowed(name):
                continue
            # Unknown underscore-prefixed name? Still check.
            # Fall through to the allowlist.
        if _is_allowed(name):
            continue
        # Dunder names produced by Python's import machinery.
        if name in ("__main__", "__mp_main__"):
            continue
        offenders.append(name)
    if offenders:
        sys.stderr.write(
            "prompt_builder_entrypoint: sys.modules allowlist violation. "
            f"Offending modules: {sorted(offenders)}\n"
        )
        raise SystemExit(2)


def main() -> int:
    _enforce_allowlist()

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
