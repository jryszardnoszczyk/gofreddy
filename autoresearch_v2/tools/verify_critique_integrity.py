"""autoresearch_v2/tools/verify_critique_integrity.py — Pi v007 defense as a tool.

Autoresearch is a self-modifying meta-loop: variants edit `lanes/<lane>.md`.
A variant that tampered with `judges/session/prompts/critique.md` could lower
the inner-critique bar and escape detection. v1 defended this with a chmod
0444 + Python source hash check inside session_evaluator. v2 reframes it as
an explicit tool the agent (and operators) call.

Manifest format: JSON object mapping repo-relative path → SHA256 hex digest.
Default location: `autoresearch_v2/.critique-manifest.json`. Override via
`CRITIQUE_MANIFEST_PATH` env var.

CLI:
    verify_critique_integrity            # check live files against manifest
    verify_critique_integrity --init     # write manifest from current files

Exit codes:
    0 — INTEGRITY OK
    2 — mismatch / missing manifest / missing defended file
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

# The defended set: the critique + review prompts the inner-critique
# subprocess reads. If you add new critique-prompt files, append them here
# and re-run `--init`.
DEFENDED_PATHS: tuple[str, ...] = (
    "judges/session/prompts/critique.md",
    "judges/session/prompts/review.md",
)

DEFAULT_MANIFEST_RELPATH = "autoresearch_v2/.critique-manifest.json"


def _repo_root() -> Path:
    override = os.environ.get("AUTORESEARCH_V2_ROOT")
    if override:
        return Path(override).resolve()
    return Path(__file__).resolve().parent.parent.parent


def _manifest_path() -> Path:
    override = os.environ.get("CRITIQUE_MANIFEST_PATH")
    if override:
        return Path(override).resolve()
    return _repo_root() / DEFAULT_MANIFEST_RELPATH


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compute_live_hashes(*, defended_paths=DEFENDED_PATHS) -> dict[str, str]:
    """Hash each defended file from its live on-disk content. Raises
    FileNotFoundError for missing files (no silent skipping)."""
    root = _repo_root()
    out: dict[str, str] = {}
    for rel in defended_paths:
        path = root / rel
        if not path.is_file():
            raise FileNotFoundError(f"defended file missing: {rel}")
        out[rel] = _hash_file(path)
    return out


def load_manifest(path: Path | None = None) -> dict[str, str]:
    p = path or _manifest_path()
    if not p.is_file():
        raise FileNotFoundError(f"manifest missing: {p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"manifest must be a JSON object, got {type(data).__name__}")
    if data.get("__grace_mode__"):
        raise ValueError(
            "grace-mode manifest detected (v1 legacy). v2 has no grace mode; "
            "regenerate with `verify_critique_integrity --init`."
        )
    return {k: v for k, v in data.items() if not k.startswith("__")}


def write_manifest(path: Path | None = None, *, defended_paths=DEFENDED_PATHS) -> Path:
    p = path or _manifest_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = compute_live_hashes(defended_paths=defended_paths)
    p.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return p


def diff_hashes(expected: dict[str, str], live: dict[str, str]) -> list[str]:
    """Return a list of human-readable mismatch lines. Empty list = match."""
    issues: list[str] = []
    expected_paths = set(expected)
    live_paths = set(live)
    for missing in sorted(expected_paths - live_paths):
        issues.append(f"  missing live file: {missing}")
    for extra in sorted(live_paths - expected_paths):
        issues.append(f"  unmanifested live file: {extra}")
    for shared in sorted(expected_paths & live_paths):
        if expected[shared] != live[shared]:
            issues.append(
                f"  hash mismatch: {shared}\n"
                f"    manifest: {expected[shared][:16]}…\n"
                f"    live:     {live[shared][:16]}…"
            )
    return issues


def verify(*, manifest_path: Path | None = None, defended_paths=DEFENDED_PATHS) -> tuple[int, str]:
    try:
        expected = load_manifest(manifest_path)
    except FileNotFoundError as e:
        return 2, (
            f"MANIFEST MISSING\n  {e}\n"
            f"  remediation: run `verify_critique_integrity --init` "
            f"to bless the current prompts."
        )
    except ValueError as e:
        return 2, f"MANIFEST INVALID\n  {e}"

    try:
        live = compute_live_hashes(defended_paths=defended_paths)
    except FileNotFoundError as e:
        return 2, f"DEFENDED FILE MISSING\n  {e}"

    issues = diff_hashes(expected, live)
    if issues:
        return 2, "INTEGRITY MISMATCH\n" + "\n".join(issues)
    return 0, "INTEGRITY OK"


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        description="Verify critique-prompt integrity via SHA256 manifest.",
    )
    p.add_argument(
        "--init",
        action="store_true",
        help="Write a fresh manifest from current on-disk prompts (blesses current state).",
    )
    args = p.parse_args(argv)

    if args.init:
        try:
            written = write_manifest()
        except FileNotFoundError as e:
            sys.stderr.write(f"verify_critique_integrity: {e}\n")
            return 2
        print(f"manifest written: {written}")
        return 0

    rc, message = verify()
    print(message)
    return rc


if __name__ == "__main__":
    sys.exit(main())
