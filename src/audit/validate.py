"""marketing_audit lane manifest validation — L1 stub.

Wired into ``autoresearch/lane_registry.py:LANES["marketing_audit"]``
as ``custom_validate``. Substrate's ``compute_expected_hashes()``
(``autoresearch/critique_manifest.py``) is symbol-based, not
file-based — adding marketing_audit's stage/judge/rubric file paths
would be a structural substrate redesign. Lane-side custom_validate
using the shared ``lane_registry.verify_manifest()`` is self-contained
and proven (master plan §6.2).

L1 stub returns ``(True, [])`` — pass. Full implementation lands in
L3 once MA-1..MA-8 rubric + judge + stage prompt files exist on
disk and ``marketing_audit_manifest.json`` is frozen via the
operator script ``autoresearch/scripts/regen_marketing_audit_manifest.py``.

Full L3 contract (master plan §6.6):
    1. Read marketing_audit_manifest.json from variant_dir.
    2. Re-hash each entry against the variant's actual file bytes.
    3. Return (False, [diffs]) on drift; reject the variant.
"""
from __future__ import annotations

from typing import Any


def marketing_audit_validate(
    variant_dir: Any,
    parent: Any | None = None,
) -> tuple[bool, list[str]]:
    """L1 stub. Returns (True, []) so variants pass through; L3
    implements the SHA256 manifest check via
    ``lane_registry.verify_manifest`` per master plan §6.6.

    Signature returns the same shape as ``lane_registry.verify_manifest``:
    ``(passed: bool, failures: list[str])``.
    """
    return True, []


__all__ = ["marketing_audit_validate"]
