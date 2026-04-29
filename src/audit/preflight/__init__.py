"""Stage-1a deterministic pre-pass.

Runs the 25 cheap deterministic checks specified in `data/preflight_lenses.yaml`
before any Stage-2 agent fires. Each check returns a structured signal that
becomes a context key downstream agents read — saves ~$10/audit vs routing
these through Sonnet.

Architecture (per LHR design doc v1):

    runner.run(domain: str, *, config: PreflightConfig) -> PreflightResult
      ↓ fan out in parallel via asyncio.gather
    ┌──────────────────────────────────────────────────────┐
    │ 8 check modules (each: `async def check(ctx) -> dict`) │
    │   dns       — SPF/DKIM/DMARC/BIMI/MTA-STS              │
    │   wellknown — /.well-known/{security,agent-card,mcp,   │
    │                apple-app-site-association,             │
    │                assetlinks.json,ucp-manifest}           │
    │   schema    — JSON-LD @types + @graph parsing          │
    │   badges    — trust-mark badge detection + staleness   │
    │   headers   — HSTS/CSP/COOP/COEP/X-Frame/Referrer      │
    │   social    — OpenGraph + Twitter Card validation      │
    │   assets    — logo hash + color extraction + robots    │
    │   tooling   — CMP/tag-manager/CDP/analytics/CRO/       │
    │               session-replay/ESP fingerprints          │
    └──────────────────────────────────────────────────────┘
      ↓ aggregate
    PreflightResult (stored in state.enrichments.preflight)

None of the check modules have implementations yet — they are typed stubs so
the runner orchestration is reviewable. Fill in check bodies during v1 Step C
implementation proper.
"""
from __future__ import annotations

from .runner import PreflightConfig, PreflightResult, run

__all__ = ["PreflightConfig", "PreflightResult", "run"]
