"""Trust-mark badge detection + staleness flags.

Covers preflight lenses 10-11 (Trust-mark badge detection, Stale-trust-page
red-flag detection).

Expected signal shape:

    {
        "detected": [
            {"vendor": "soc2",       "location": "footer"|"security-page", "evidence_url": str},
            {"vendor": "iso_27001",  ...},
            {"vendor": "bbb",        ...},
            {"vendor": "dpf_privacy_shield", ...},
            {"vendor": "norton",     "stale": bool, "evidence_url": str},   # deprecated vendor
            {"vendor": "mcafee",     "stale": bool, "evidence_url": str},   # deprecated vendor
            {"vendor": "truste_original", "stale": bool, "evidence_url": str}, # now TrustArc
        ],
        "stale_vendors_present": [str],
    }

Implementation note (v1): scan homepage + /security + /trust + footer of each
for badge image alt-text regex + dst-link domain regex (e.g. `/soc-?2/i`,
`norton|symantec` in src). Norton/McAfee/TRUSTe-original are stale markers —
a real trust program would have migrated to the current brand.
"""
from __future__ import annotations


async def check(domain: str) -> dict:
    # TODO(v1-step-C): implement via httpx + BeautifulSoup + regex.
    return {"implemented": False}
