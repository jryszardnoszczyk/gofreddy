"""DNS-layer email-auth + transport hardening.

Covers preflight lenses 01 (SPF/DKIM/DMARC/BIMI/MTA-STS). No HTTP I/O — all
lookups go through the resolver directly.

Expected signal shape:

    {
        "spf":     {"present": bool, "record": str | None, "policy": "-all"|"~all"|"?all"|None, "lookups": int},
        "dkim":    {"selectors_probed": [str], "present_selectors": [str]},
        "dmarc":   {"present": bool, "policy": "none"|"quarantine"|"reject"|None, "rua": str | None, "pct": int | None},
        "bimi":    {"present": bool, "svg_url": str | None, "vmc": str | None},
        "mta_sts": {"policy_present": bool, "mode": "enforce"|"testing"|"none"|None, "tlsrpt_present": bool},
    }

Implementation note (v1): `dnspython` async resolver. Retry once on transient
NXDOMAIN-during-serve. Common DKIM selectors to probe: default, google, selector1,
selector2, k1, mandrill, mxvault, mail, s1, dkim.
"""
from __future__ import annotations


async def check(domain: str) -> dict:
    # TODO(v1-step-C): implement via dnspython async resolver.
    return {"implemented": False}
