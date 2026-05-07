#!/usr/bin/env python3
"""Pre-flight provider connection check for marketing audit v1.

Reports which env vars are set + makes a tiny probe call per Tier-1 owned
provider to confirm credentials work. Run BEFORE the §7.7 acceptance dry
run so JR knows exactly which providers will actually deliver data.

Output:
  REQUIRED-MISSING  → audit will halt at Stage 1a (or fall to gap_flag)
  REQUIRED-SET      → env var present; probe attempted
  REQUIRED-OK       → env var present + probe call succeeded
  REQUIRED-FAIL     → env var present but probe failed (likely bad creds)
  OPTIONAL-MISSING  → audit continues but lens(es) gap_flag
  OPTIONAL-OK       → env var present + probe ok

Exit code = number of REQUIRED-MISSING + REQUIRED-FAIL.

Usage:
  python scripts/audit_provider_check.py            # JSON output
  python scripts/audit_provider_check.py --human    # table output
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass
from typing import Callable

import httpx

TIMEOUT = 8.0


@dataclass
class ProbeResult:
    name: str
    tier: str               # "T1-owned" / "T2-free" / "commerce"
    criticality: str        # "REQUIRED" / "OPTIONAL"
    env_vars: list[str]
    status: str             # one of the buckets above
    detail: str = ""


def _all_set(vars: list[str]) -> bool:
    return all(os.environ.get(v, "").strip() for v in vars)


def _probe(
    name: str, tier: str, criticality: str, env_vars: list[str],
    probe: Callable[[], tuple[bool, str]] | None = None,
) -> ProbeResult:
    if not _all_set(env_vars):
        miss_status = f"{criticality}-MISSING"
        missing = [v for v in env_vars if not os.environ.get(v, "").strip()]
        return ProbeResult(name, tier, criticality, env_vars, miss_status,
                           detail=f"missing env: {', '.join(missing)}")
    if probe is None:
        return ProbeResult(name, tier, criticality, env_vars, f"{criticality}-SET",
                           detail="env present; no probe defined")
    try:
        ok, msg = probe()
    except Exception as exc:
        return ProbeResult(name, tier, criticality, env_vars, f"{criticality}-FAIL",
                           detail=f"probe raised: {type(exc).__name__}: {exc}")
    return ProbeResult(name, tier, criticality, env_vars,
                       f"{criticality}-OK" if ok else f"{criticality}-FAIL",
                       detail=msg)


# ─── Probe implementations ─────────────────────────────────────────────────


def _probe_apify() -> tuple[bool, str]:
    r = httpx.get("https://api.apify.com/v2/users/me",
                  headers={"Authorization": f"Bearer {os.environ['APIFY_TOKEN']}"},
                  timeout=TIMEOUT)
    return (r.status_code == 200, f"apify users/me {r.status_code}")


def _probe_brave() -> tuple[bool, str]:
    r = httpx.get("https://api.search.brave.com/res/v1/web/search?q=ping&count=1",
                  headers={"X-Subscription-Token": os.environ["BRAVE_API_KEY"]},
                  timeout=TIMEOUT)
    return (r.status_code in (200, 429), f"brave search {r.status_code}")


def _probe_serpapi() -> tuple[bool, str]:
    r = httpx.get(f"https://serpapi.com/account?api_key={os.environ['SERPAPI_KEY']}",
                  timeout=TIMEOUT)
    return (r.status_code == 200, f"serpapi account {r.status_code}")


def _probe_dataforseo() -> tuple[bool, str]:
    login = os.environ["DATAFORSEO_LOGIN"]
    password = os.environ["DATAFORSEO_PASSWORD"]
    r = httpx.get("https://api.dataforseo.com/v3/appendix/user_data",
                  auth=(login, password), timeout=TIMEOUT)
    return (r.status_code == 200, f"dataforseo user_data {r.status_code}")


def _probe_pagespeed() -> tuple[bool, str]:
    key = os.environ["GOOGLE_PAGESPEED_KEY"]
    r = httpx.get(
        f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=https://example.com&key={key}",
        timeout=TIMEOUT,
    )
    return (r.status_code == 200, f"pagespeed {r.status_code}")


def _probe_github() -> tuple[bool, str]:
    r = httpx.get("https://api.github.com/user",
                  headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"},
                  timeout=TIMEOUT)
    return (r.status_code == 200, f"github user {r.status_code}")


def _probe_reddit() -> tuple[bool, str]:
    r = httpx.post("https://www.reddit.com/api/v1/access_token",
                   auth=(os.environ["REDDIT_CLIENT_ID"], os.environ["REDDIT_CLIENT_SECRET"]),
                   data={"grant_type": "client_credentials"},
                   headers={"User-Agent": "gofreddy-audit-precheck/0.1"},
                   timeout=TIMEOUT)
    return (r.status_code == 200, f"reddit oauth {r.status_code}")


def _probe_huggingface() -> tuple[bool, str]:
    r = httpx.get("https://huggingface.co/api/whoami-v2",
                  headers={"Authorization": f"Bearer {os.environ['HUGGINGFACE_TOKEN']}"},
                  timeout=TIMEOUT)
    return (r.status_code == 200, f"hf whoami {r.status_code}")


def _probe_resend() -> tuple[bool, str]:
    # Resend has no whoami endpoint — `/domains` returns 200 with valid key
    r = httpx.get("https://api.resend.com/domains",
                  headers={"Authorization": f"Bearer {os.environ['RESEND_API_KEY']}"},
                  timeout=TIMEOUT)
    return (r.status_code == 200, f"resend domains {r.status_code}")


# ─── Provider catalog ──────────────────────────────────────────────────────


PROVIDERS: list[ProbeResult | tuple] = [
    # Tier-1 owned (paid) — required for full-signal audit; missing → gap_flags
    ("DataForSEO",        "T1-owned", "REQUIRED",
     ["DATAFORSEO_LOGIN", "DATAFORSEO_PASSWORD"], _probe_dataforseo),
    ("PageSpeed",         "T1-owned", "REQUIRED",
     ["GOOGLE_PAGESPEED_KEY"], _probe_pagespeed),
    ("Cloro (AI search)", "T1-owned", "REQUIRED",
     ["CLORO_API_KEY", "MONITORING_CLORO_API_KEY"], None),  # accept either
    ("Apify (multi)",     "T1-owned", "REQUIRED",
     ["APIFY_TOKEN"], _probe_apify),
    ("Xpoz (Twitter/IG)", "T1-owned", "REQUIRED",
     ["XPOZ_API_KEY", "MONITORING_XPOZ_API_KEY"], None),
    ("Foreplay (ads)",    "T1-owned", "OPTIONAL",
     ["COMPETITIVE_FOREPLAY_API_KEY"], None),
    ("Adyntel (ads)",     "T1-owned", "OPTIONAL",
     ["COMPETITIVE_ADYNTEL_API_KEY", "COMPETITIVE_ADYNTEL_EMAIL"], None),
    ("Brave Search",      "T1-owned", "OPTIONAL",
     ["BRAVE_API_KEY"], _probe_brave),
    ("SerpAPI (Google ads)", "T1-owned", "OPTIONAL",
     ["SERPAPI_KEY"], _probe_serpapi),
    ("NewsData",          "T1-owned", "OPTIONAL",
     ["MONITORING_NEWSDATA_API_KEY"], None),
    ("Pod Engine",        "T1-owned", "OPTIONAL",
     ["MONITORING_POD_ENGINE_API_KEY"], None),
    ("GSC",               "T1-owned", "OPTIONAL",
     ["GSC_SERVICE_ACCOUNT_PATH"], None),

    # Tier-2 free public — agent-side fetched; gap_flag if unset
    ("GitHub",            "T2-free",  "OPTIONAL",
     ["GITHUB_TOKEN"], _probe_github),
    ("Reddit",            "T2-free",  "OPTIONAL",
     ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET"], _probe_reddit),
    ("HuggingFace",       "T2-free",  "OPTIONAL",
     ["HUGGINGFACE_TOKEN"], _probe_huggingface),
    ("Wikimedia",         "T2-free",  "OPTIONAL",
     ["WIKIMEDIA_API_KEY"], None),
    ("Mailinator",        "T2-free",  "OPTIONAL",
     ["MAILINATOR_API_TOKEN"], None),
    ("Product Hunt",      "T2-free",  "OPTIONAL",
     ["PRODUCT_HUNT_DEVELOPER_TOKEN"], None),
    ("Podchaser",         "T2-free",  "OPTIONAL",
     ["PODCHASER_TOKEN"], None),

    # Commerce surface — fully optional for a code-only dry run
    ("Resend (email)",    "commerce", "OPTIONAL",
     ["RESEND_API_KEY"], _probe_resend),
    ("Stripe webhook",    "commerce", "OPTIONAL",
     ["STRIPE_WEBHOOK_SECRET"], None),
    ("Fireflies webhook", "commerce", "OPTIONAL",
     ["FIREFLIES_WEBHOOK_SECRET"], None),
    ("Slack leads",       "commerce", "OPTIONAL",
     ["SLACK_WEBHOOK_LEADS"], None),
    ("Slack paid",        "commerce", "OPTIONAL",
     ["SLACK_WEBHOOK_PAID"], None),
    ("Slack calls",       "commerce", "OPTIONAL",
     ["SLACK_WEBHOOK_CALLS"], None),
    ("Slack cost",        "commerce", "OPTIONAL",
     ["SLACK_WEBHOOK_COST"], None),
    ("R2 publish",        "commerce", "OPTIONAL",
     ["R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_ACCOUNT_ID"], None),
]


def main() -> int:
    human = "--human" in sys.argv
    results: list[ProbeResult] = []
    for spec in PROVIDERS:
        name, tier, criticality, env_vars, probe = spec
        results.append(_probe(name, tier, criticality, env_vars, probe))

    bad = sum(1 for r in results if r.status in {"REQUIRED-MISSING", "REQUIRED-FAIL"})

    if human:
        col = lambda s, w: s.ljust(w)
        print(f"{col('PROVIDER', 22)} {col('TIER', 10)} {col('STATUS', 18)} DETAIL")
        print("─" * 90)
        for r in results:
            print(f"{col(r.name, 22)} {col(r.tier, 10)} {col(r.status, 18)} {r.detail}")
        print()
        print(f"REQUIRED-MISSING + REQUIRED-FAIL: {bad}")
    else:
        print(json.dumps([asdict(r) for r in results], indent=2))

    return bad


if __name__ == "__main__":
    sys.exit(main())
