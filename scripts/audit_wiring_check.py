#!/usr/bin/env python3
"""Deep wiring check — imports every provider/scraper/check the audit
pipeline depends on, verifies expected methods exist + can instantiate
where safe.

Run BEFORE the §7.7 dry run to catch import errors, missing methods,
or stale class signatures that would explode mid-pipeline. Companion
to scripts/audit_provider_check.py (which only verifies env vars).

Output:
  WIRED            → import ok + expected callable present
  WIRED-NEEDS-CFG  → import ok + expected callable present, but needs
                     env/config to actually call (not exercised here)
  IMPORT-ERROR     → module won't import
  MISSING-METHOD   → module imports but expected method absent
  STAGE-CONTRACT-OK → src/audit/stages.py + cli/freddy.commands.audit
                     boot cleanly

Exit code = number of IMPORT-ERROR + MISSING-METHOD.

Usage:
  python scripts/audit_wiring_check.py            # JSON output
  python scripts/audit_wiring_check.py --human    # table output
"""
from __future__ import annotations

import importlib
import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


def _load_env_file() -> None:
    """Same logic as audit_provider_check.py — walk parents, load .env."""
    for ancestor in Path(__file__).resolve().parents[:5]:
        env_path = ancestor / ".env"
        if env_path.is_file():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
            return


_load_env_file()


def _prepend_worktree_to_syspath() -> None:
    """The venv was installed via `pip install -e .` from the main repo,
    so `import src.audit.stages` resolves to main-repo source — which
    doesn't have the marketing-audit additions. Prepend the worktree's
    repo root so worktree modules win."""
    worktree_root = Path(__file__).resolve().parent.parent
    if str(worktree_root) not in sys.path:
        sys.path.insert(0, str(worktree_root))


_prepend_worktree_to_syspath()


@dataclass
class WireResult:
    name: str
    category: str           # "T1-owned" / "T3-local" / "preflight" / "audit-core" / "stage-contract"
    status: str             # WIRED / WIRED-NEEDS-CFG / IMPORT-ERROR / MISSING-METHOD / STAGE-CONTRACT-OK
    detail: str = ""


def _check_module(
    name: str,
    category: str,
    module_path: str,
    expected_attrs: list[str],
) -> WireResult:
    try:
        mod = importlib.import_module(module_path)
    except Exception as exc:
        return WireResult(name, category, "IMPORT-ERROR",
                          detail=f"{type(exc).__name__}: {exc}")
    missing = [a for a in expected_attrs if not hasattr(mod, a)]
    if missing:
        return WireResult(name, category, "MISSING-METHOD",
                          detail=f"{module_path} missing: {', '.join(missing)}")
    return WireResult(name, category, "WIRED",
                      detail=f"{module_path}: {', '.join(expected_attrs)}")


# ─── Provider catalog ──────────────────────────────────────────────────────
# Tuple format: (display_name, category, module, [expected_attrs])

CHECKS: list[tuple[str, str, str, list[str]]] = [
    # SEO + Performance
    ("DataForSEO",       "T1-owned", "src.seo.providers.dataforseo",
     ["DataForSeoProvider"]),
    ("PageSpeed",        "T1-owned", "src.seo.providers.pagespeed",
     ["check_performance"]),
    ("GSC",              "T1-owned", "src.seo.providers.gsc",
     ["GSCClient"]),

    # GEO / AI
    ("Cloro",            "T1-owned", "src.geo.providers.cloro",
     ["CloroClient"]),

    # Competitive
    ("Foreplay",         "T1-owned", "src.competitive.providers.foreplay",
     ["ForeplayProvider"]),
    ("Adyntel",          "T1-owned", "src.competitive.providers.adyntel",
     ["AdyntelProvider"]),
    ("Vision (Gemini)",  "T1-owned", "src.competitive.vision",
     []),

    # Monitoring adapters
    ("Xpoz",             "T1-owned", "src.monitoring.adapters.xpoz",
     ["XpozAdapter"]),
    ("Reviews (3 sub)",  "T1-owned", "src.monitoring.adapters.reviews",
     ["TrustpilotAdapter", "AppStoreAdapter", "PlayStoreAdapter"]),
    ("IC Content",       "T1-owned", "src.monitoring.adapters.ic_content",
     ["ICContentAdapter"]),
    ("TikTok",           "T1-owned", "src.monitoring.adapters.tiktok",
     ["TikTokAdapter"]),
    ("NewsData",         "T1-owned", "src.monitoring.adapters.news",
     ["NewsDataAdapter"]),
    ("Bluesky",          "T1-owned", "src.monitoring.adapters.bluesky",
     ["BlueskyMentionFetcher"]),
    ("Facebook",         "T1-owned", "src.monitoring.adapters.facebook",
     ["FacebookMentionFetcher"]),
    ("Pod Engine",       "T1-owned", "src.monitoring.adapters.podcasts",
     ["PodEngineAdapter"]),
    ("LinkedIn",         "T1-owned", "src.monitoring.adapters.linkedin",
     ["LinkedInMentionFetcher"]),
    ("GoogleTrends",     "T1-owned", "src.monitoring.adapters.google_trends",
     ["GoogleTrendsAdapter"]),
    ("AiSearch",         "T1-owned", "src.monitoring.adapters.ai_search",
     ["AiSearchAdapter"]),

    # Audit-specific tools (Phase-1.5 net-new)
    ("Apify-SimilarWeb", "T1-owned", "src.audit.tools.apify_similarweb",
     []),
    ("Brave Search",     "T1-owned", "src.audit.tools.brave_search",
     []),
    ("SerpAPI Ads",      "T1-owned", "src.audit.tools.serpapi_ads",
     []),
    ("MarTech (Wappa)",  "T3-local", "src.audit.tools.martech",
     []),
    ("RenderedFetcher",  "T3-local", "src.audit.tools.rendered_fetcher",
     []),

    # X-engine fetchers (reused per master plan §4.2)
    ("Fetcher: Instagram", "T1-owned", "src.fetcher.instagram", []),
    ("Fetcher: TikTok",    "T1-owned", "src.fetcher.tiktok",    []),
    ("Fetcher: YouTube",   "T1-owned", "src.fetcher.youtube",   []),

    # Audit pipeline core
    ("agent_models",     "audit-core", "src.audit.agent_models",
     ["AgentOutput", "ParentFinding", "SubSignal", "HealthScore",
      "compute_health_score"]),
    ("stages",           "audit-core", "src.audit.stages",
     ["stage_0_intake", "stage_1_warmup", "stage_1b_predischarge",
      "stage_1c_brief_synthesis", "stage_2_agents", "stage_3_synthesis",
      "stage_4_proposal", "stage_5_deliverable", "_safe_format",
      "is_stage_complete", "mark_stage_complete"]),
    ("agent_runner",     "audit-core", "src.audit.agent_runner",
     ["AgentRunner"]),
    ("cost_observability", "audit-core", "src.audit.cost_observability",
     ["record_stage_cost", "COST_THRESHOLDS_USD"]),
    ("state",            "audit-core", "src.audit.state",
     ["AuditState", "AuditStateFile"]),
    ("r2_publish",       "audit-core", "src.audit.r2_publish",
     ["upload_audit_dir"]),
    ("email_delivery",   "audit-core", "src.audit.email_delivery",
     ["send_email"]),
    ("validate (custom_validate)", "audit-core", "src.audit.validate", []),

    # Preflight checks (8 — wired into stage_1_warmup)
    ("preflight: dns",       "preflight", "src.audit.preflight.checks.dns",       ["check"]),
    ("preflight: wellknown", "preflight", "src.audit.preflight.checks.wellknown", ["check"]),
    ("preflight: schema",    "preflight", "src.audit.preflight.checks.schema",    ["check"]),
    ("preflight: badges",    "preflight", "src.audit.preflight.checks.badges",    ["check"]),
    ("preflight: headers",   "preflight", "src.audit.preflight.checks.headers",   ["check"]),
    ("preflight: social",    "preflight", "src.audit.preflight.checks.social",    ["check"]),
    ("preflight: assets",    "preflight", "src.audit.preflight.checks.assets",    ["check"]),
    ("preflight: tooling",   "preflight", "src.audit.preflight.checks.tooling",   ["check"]),
    ("preflight: runner",    "preflight", "src.audit.preflight.runner",
     ["run", "PreflightConfig", "PreflightResult"]),

    # API routers (commerce/funnel)
    ("router: stripe",    "audit-core", "src.api.routers.stripe",    ["router"]),
    ("router: scan",      "audit-core", "src.api.routers.scan",      ["router"]),
    ("router: fireflies", "audit-core", "src.api.routers.fireflies", ["router"]),

    # Cache layer
    ("tools.cache",        "audit-core", "src.audit.tools.cache", []),
    ("tools.cached_tool",  "audit-core", "src.audit.tools.cached_tool", []),
]


def _check_stage_contract() -> WireResult:
    """Boot the FastAPI app with stub env — verifies the lane registry +
    RUBRICS + 5 new endpoints all import cleanly."""
    os.environ.setdefault("SUPABASE_URL", "http://x")
    os.environ.setdefault("SUPABASE_ANON_KEY", "x")
    os.environ.setdefault("SUPABASE_JWT_SECRET", "x")
    os.environ.setdefault("DATABASE_URL", "postgresql://x:x@127.0.0.1:1/x")
    try:
        from src.api.main import app
    except Exception as exc:
        return WireResult("FastAPI app boot", "stage-contract", "IMPORT-ERROR",
                          detail=f"{type(exc).__name__}: {exc}")
    routes = sorted({r.path for r in app.routes if hasattr(r, "path")})
    expected = {"/v1/audit/stripe/webhook", "/v1/scan/request", "/v1/scan/{scan_id}",
                "/v1/audit/sales-call-transcript",
                "/v1/audit/walkthrough-call-transcript"}
    missing = expected - set(routes)
    if missing:
        return WireResult("FastAPI app boot", "stage-contract", "MISSING-METHOD",
                          detail=f"missing routes: {sorted(missing)}")
    return WireResult("FastAPI app boot", "stage-contract", "STAGE-CONTRACT-OK",
                      detail=f"{len(routes)} routes; all 5 audit endpoints present")


def _check_freddy_cli_contract() -> WireResult:
    """Verify the freddy audit verbs JR will invoke during the dry run."""
    try:
        from cli.freddy.commands import audit as audit_cli
    except Exception as exc:
        return WireResult("freddy audit CLI", "stage-contract", "IMPORT-ERROR",
                          detail=f"{type(exc).__name__}: {exc}")
    expected_cmds = {"init", "run", "confirm-brief", "mark-paid",
                     "publish", "close-engagement", "attach"}
    registered = set()
    for cmd in audit_cli.app.registered_commands:
        registered.add(cmd.name)
    missing = expected_cmds - registered
    if missing:
        return WireResult("freddy audit CLI", "stage-contract", "MISSING-METHOD",
                          detail=f"missing verbs: {sorted(missing)}")
    return WireResult("freddy audit CLI", "stage-contract", "STAGE-CONTRACT-OK",
                      detail=f"all 7 marketing-audit verbs registered")


def _check_lane_registry() -> WireResult:
    """Verify marketing_audit lane is registered with expected fields."""
    try:
        from autoresearch.lane_registry import LANES
        from src.evaluation.rubrics import RUBRICS
    except Exception as exc:
        return WireResult("lane registry", "stage-contract", "IMPORT-ERROR",
                          detail=f"{type(exc).__name__}: {exc}")
    if "marketing_audit" not in LANES:
        return WireResult("lane registry", "stage-contract", "MISSING-METHOD",
                          detail="marketing_audit lane not in LANES")
    spec = LANES["marketing_audit"]
    if len(spec.rubric_ids) != 8:
        return WireResult("lane registry", "stage-contract", "MISSING-METHOD",
                          detail=f"expected 8 rubric_ids, got {len(spec.rubric_ids)}")
    missing_rubrics = [r for r in spec.rubric_ids if r not in RUBRICS]
    if missing_rubrics:
        return WireResult("lane registry", "stage-contract", "MISSING-METHOD",
                          detail=f"rubric_ids not in RUBRICS: {missing_rubrics}")
    return WireResult("lane registry", "stage-contract", "STAGE-CONTRACT-OK",
                      detail=f"marketing_audit lane: 8 rubrics MA-1..MA-8 all in RUBRICS dict")


def _check_data_files() -> WireResult:
    """The audit pipeline reads from rubric YAMLs + capability registry +
    Stage-5 template at runtime. If any are missing, mid-stage crash."""
    repo_root = Path(__file__).resolve().parents[1]
    # Walk up to main repo if we're in a worktree
    for ancestor in [repo_root] + list(repo_root.parents)[:4]:
        if (ancestor / "data" / "capability_registry.yaml").exists():
            repo_root = ancestor
            break
    expected = [
        "data/capability_registry.yaml",
        "data/rubrics_findability.yaml",
        "data/rubrics_narrative.yaml",
        "data/rubrics_acquisition.yaml",
        "data/rubrics_experience.yaml",
        "data/martech_rules.yaml",
        "templates/audit_report.html.j2",
        "programs/marketing_audit-session.md",
        "programs/marketing_audit/prompts/stage_1b_predischarge.md",
        "programs/marketing_audit/prompts/stage_1c_brief_synthesis.md",
        "programs/marketing_audit/prompts/stage_2_findability.md",
        "programs/marketing_audit/prompts/stage_2_narrative.md",
        "programs/marketing_audit/prompts/stage_2_acquisition.md",
        "programs/marketing_audit/prompts/stage_2_experience.md",
        "programs/marketing_audit/prompts/stage_3_cross_cutting.md",
        "programs/marketing_audit/prompts/stage_3_narrative.md",
        "programs/marketing_audit/prompts/stage_4_proposal.md",
    ]
    # 8 MA-N judge prompts (loaded by RUBRICS at module import)
    expected += [f"programs/marketing_audit/prompts/judges/MA-{i}-judge.md"
                 for i in range(1, 9)]
    missing = [p for p in expected if not (repo_root / p).is_file()]
    if missing:
        return WireResult("runtime data files", "stage-contract", "MISSING-METHOD",
                          detail=f"missing under {repo_root}: {missing}")
    return WireResult("runtime data files", "stage-contract", "STAGE-CONTRACT-OK",
                      detail=f"{len(expected)} files present under {repo_root.name}")


def main() -> int:
    human = "--human" in sys.argv
    results: list[WireResult] = []
    for name, category, module, attrs in CHECKS:
        results.append(_check_module(name, category, module, attrs))
    results.append(_check_stage_contract())
    results.append(_check_freddy_cli_contract())
    results.append(_check_lane_registry())
    results.append(_check_data_files())

    bad = sum(1 for r in results if r.status in {"IMPORT-ERROR", "MISSING-METHOD"})

    if human:
        col = lambda s, w: s.ljust(w)
        print(f"{col('TARGET', 32)} {col('CATEGORY', 14)} {col('STATUS', 22)} DETAIL")
        print("─" * 130)
        for r in results:
            print(f"{col(r.name, 32)} {col(r.category, 14)} {col(r.status, 22)} {r.detail[:60]}")
        print()
        print(f"IMPORT-ERROR + MISSING-METHOD: {bad}")
        wired = sum(1 for r in results if r.status == "WIRED")
        contract_ok = sum(1 for r in results if r.status == "STAGE-CONTRACT-OK")
        print(f"WIRED: {wired} / STAGE-CONTRACT-OK: {contract_ok} / total: {len(results)}")
    else:
        print(json.dumps([asdict(r) for r in results], indent=2))

    return bad


if __name__ == "__main__":
    sys.exit(main())
