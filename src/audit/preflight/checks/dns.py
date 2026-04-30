"""DNS-layer email-auth + transport hardening.

Covers preflight lenses 01 (SPF/DKIM/DMARC/BIMI/MTA-STS). No HTTP I/O — all
lookups go through the resolver directly.

Signal shape: see `_SIGNAL_SHAPE` below and the module return-type of check().

Implementation notes:

- Uses dnspython's async resolver. Transient NXDOMAIN / Timeout on a single
  record type is recorded as `{"present": False}`; the run as a whole still
  succeeds so Stage-2 agents see "unknown", not "absent-with-certainty".
- DKIM requires selector probing since there's no discovery mechanism. We
  probe the 8 most-common selectors; absence across all 8 is reported, but
  is not a hard-negative — the prospect may use a rare selector.
- BIMI and MTA-STS TXT records follow standard `_{name}._domainkey` /
  `_mta-sts.<domain>` / `_dmarc.<domain>` / `default._bimi.<domain>` subdomain
  conventions (RFC 8463, RFC 8461, RFC 7489, BIMI Group draft).
"""
from __future__ import annotations

import re
from typing import Any

import dns.asyncresolver
import dns.exception

_COMMON_DKIM_SELECTORS = (
    "default", "google", "selector1", "selector2",
    "k1", "mandrill", "mail", "s1",
)


async def _txt_records(name: str, timeout_s: float = 5.0) -> list[str]:
    """Return list of TXT strings at `name`. Returns [] on NXDOMAIN/timeout."""
    resolver = dns.asyncresolver.Resolver()
    resolver.timeout = timeout_s
    resolver.lifetime = timeout_s
    try:
        answer = await resolver.resolve(name, "TXT")
    except (dns.exception.DNSException,):
        return []
    # Each answer may be a multi-string TXT; join chunks per RFC 7208.
    return [b"".join(rdata.strings).decode("utf-8", errors="replace") for rdata in answer]


def _parse_spf(records: list[str]) -> dict[str, Any]:
    """First record starting `v=spf1` wins. Count `include:` + `a` + `mx` for lookup count."""
    spf = next((r for r in records if r.lower().startswith("v=spf1")), None)
    if not spf:
        return {"present": False, "record": None, "policy": None, "lookups": 0}
    # Terminator: -all (reject), ~all (softfail), ?all (neutral), +all (none — insecure).
    policy_match = re.search(r"([-~?+])all\b", spf)
    policy = policy_match.group(0) if policy_match else None
    # SPF 10-lookup limit mechanisms: include, a, mx, ptr, exists, redirect.
    lookups = sum(1 for tok in spf.lower().split() if tok.startswith(("include:", "a:", "mx:", "ptr", "exists:", "redirect=")) or tok in ("a", "mx"))
    return {"present": True, "record": spf, "policy": policy, "lookups": lookups}


def _parse_dmarc(records: list[str]) -> dict[str, Any]:
    dmarc = next((r for r in records if r.lower().startswith("v=dmarc1")), None)
    if not dmarc:
        return {"present": False, "policy": None, "rua": None, "pct": None}
    tags = dict(
        re.findall(r"(\w+)\s*=\s*([^;]+)", dmarc)
    )
    p = tags.get("p", "").strip().lower() or None
    rua = tags.get("rua", "").strip() or None
    pct_s = tags.get("pct", "100").strip()
    try:
        pct = int(pct_s)
    except ValueError:
        pct = None
    return {"present": True, "policy": p, "rua": rua, "pct": pct}


def _parse_bimi(records: list[str]) -> dict[str, Any]:
    bimi = next((r for r in records if r.lower().startswith("v=bimi1")), None)
    if not bimi:
        return {"present": False, "svg_url": None, "vmc": None}
    tags = dict(re.findall(r"(\w+)\s*=\s*([^;]+)", bimi))
    return {
        "present": True,
        "svg_url": tags.get("l", "").strip() or None,
        "vmc": tags.get("a", "").strip() or None,
    }


def _parse_mta_sts(records: list[str]) -> dict[str, Any]:
    """TXT at `_mta-sts.<domain>` confirms policy intent; mode requires fetching
    the HTTPS policy file — out of scope for DNS-only module, left to wellknown.py
    if we later add it."""
    if not records:
        return {"policy_present": False, "mode": None, "tlsrpt_present": False}
    sts = next((r for r in records if r.lower().startswith("v=stsv1")), None)
    return {
        "policy_present": bool(sts),
        "mode": None,  # determined by policy file fetch, not TXT
        "tlsrpt_present": False,  # checked separately below
    }


async def check(domain: str) -> dict:
    domain = domain.strip().lower().rstrip(".")

    spf_records = await _txt_records(domain)
    dmarc_records = await _txt_records(f"_dmarc.{domain}")
    bimi_records = await _txt_records(f"default._bimi.{domain}")
    mtasts_records = await _txt_records(f"_mta-sts.{domain}")
    tlsrpt_records = await _txt_records(f"_smtp._tls.{domain}")

    dkim_results = {}
    for selector in _COMMON_DKIM_SELECTORS:
        dkim_results[selector] = bool(await _txt_records(f"{selector}._domainkey.{domain}"))

    return {
        "spf":    _parse_spf(spf_records),
        "dmarc":  _parse_dmarc(dmarc_records),
        "bimi":   _parse_bimi(bimi_records),
        "dkim": {
            "selectors_probed": list(_COMMON_DKIM_SELECTORS),
            "present_selectors": [s for s, present in dkim_results.items() if present],
        },
        "mta_sts": {
            **_parse_mta_sts(mtasts_records),
            "tlsrpt_present": bool(tlsrpt_records),
        },
    }
