"""Capability cost definitions — single source of truth for per-tool credit billing."""

from dataclasses import dataclass

from .tiers import Tier


@dataclass(frozen=True, slots=True)
class CapabilityCost:
    credits: int
    min_tier: Tier


CAPABILITY_COSTS: dict[str, CapabilityCost] = {
    # ── Core analysis ──────────────────────────────────────────
    "analyze_video": CapabilityCost(credits=5, min_tier=Tier.FREE),
    # analyze_brands, infer_demographics, analyze_creative_patterns — bundled into analyze_video
    # get_analysis_report — absorbed into analyze_video
    # detect_deepfake — absorbed into analyze_video
    # ── Trust & safety ─────────────────────────────────────────
    "detect_fraud": CapabilityCost(credits=2, min_tier=Tier.FREE),
    # ── Discovery ──────────────────────────────────────────────
    "search": CapabilityCost(credits=0, min_tier=Tier.FREE),
    # get_trends — absorbed into search
    "discover_creators": CapabilityCost(credits=0, min_tier=Tier.FREE),
    "creator_profile": CapabilityCost(credits=1, min_tier=Tier.FREE),
    # capture_stories — absorbed into creator_profile
    "evaluate_creators": CapabilityCost(credits=1, min_tier=Tier.FREE),
    # ── Monitoring ─────────────────────────────────────────────
    "manage_monitor": CapabilityCost(credits=2, min_tier=Tier.PRO),
    "query_monitor": CapabilityCost(credits=0, min_tier=Tier.PRO),
    # draft_action_packet — absorbed into query_monitor
    # ── Creative ───────────────────────────────────────────────
    "analyze_content": CapabilityCost(credits=3, min_tier=Tier.FREE),
    "generate_content": CapabilityCost(credits=2, min_tier=Tier.PRO),
    # ── Generation ─────────────────────────────────────────────
    "video_generate": CapabilityCost(credits=0, min_tier=Tier.PRO),
    "video_generation_480p": CapabilityCost(credits=6, min_tier=Tier.PRO),
    "video_generation_720p": CapabilityCost(credits=9, min_tier=Tier.PRO),
    "video_project": CapabilityCost(credits=2, min_tier=Tier.PRO),
    # ── Workspace ──────────────────────────────────────────────
    "workspace": CapabilityCost(credits=0, min_tier=Tier.FREE),
    # delete_collection, analyze_batch — absorbed into workspace
    # ── SEO & competitive ─────────────────────────────────────
    "seo_audit": CapabilityCost(credits=0, min_tier=Tier.PRO),
    "competitor_ads": CapabilityCost(credits=0, min_tier=Tier.PRO),
    # ── GEO ────────────────────────────────────────────────────
    "geo_check_visibility": CapabilityCost(credits=2, min_tier=Tier.PRO),
    # ── Policy ─────────────────────────────────────────────────
    "manage_policy": CapabilityCost(credits=1, min_tier=Tier.FREE),
    # ── Retrieval (free) ───────────────────────────────────────
    "get_analysis": CapabilityCost(credits=0, min_tier=Tier.FREE),
    # ── Free utilities ─────────────────────────────────────────
    "check_usage": CapabilityCost(credits=0, min_tier=Tier.FREE),
    "think": CapabilityCost(credits=0, min_tier=Tier.FREE),
    # ── Avatar & media (stubs for future PRs) ────────────────
    "avatar_standard": CapabilityCost(credits=5, min_tier=Tier.PRO),
    "avatar_pro": CapabilityCost(credits=12, min_tier=Tier.PRO),
    "avatar_ultra": CapabilityCost(credits=16, min_tier=Tier.PRO),
    "tts_generation": CapabilityCost(credits=1, min_tier=Tier.PRO),
    "article_generation": CapabilityCost(credits=1, min_tier=Tier.PRO),
    "image_generation": CapabilityCost(credits=1, min_tier=Tier.PRO),
    "face_swap": CapabilityCost(credits=1, min_tier=Tier.PRO),
    "bg_removal": CapabilityCost(credits=1, min_tier=Tier.PRO),
}


def get_capability_cost(name: str) -> CapabilityCost:
    """Get cost for a capability. Raises KeyError if not found."""
    return CAPABILITY_COSTS[name]
